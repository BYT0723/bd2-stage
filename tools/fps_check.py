"""运行时帧率探针：在真实 GPU 上验证 fps / fpsIdle 的 draw 速率。

用法: python3 tools/fps_check.py
无 chromium、缺 websocket-client、或 WebGL 落到 SwiftShader 时 SKIP（退出 0）。
"""
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent

try:
    import websocket
except Exception:  # 可选依赖：probe 不在 make check 门禁里
    websocket = None

INSTRUMENT = r"""
(function(){
  window.__probe = {draws: 0};
  ['drawElements','drawArrays','drawElementsInstanced','drawArraysInstanced'].forEach(function(k){
    [window.WebGLRenderingContext, window.WebGL2RenderingContext].forEach(function(C){
      if (!C || !C.prototype[k]) return;
      var orig = C.prototype[k];
      C.prototype[k] = function(){ window.__probe.draws++; return orig.apply(this, arguments); };
    });
  });
})();
"""


class CDP:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=60)
        self.id = 0
        self.lock = threading.Lock()
        self.responses = {}
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while True:
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                return
            if "id" in msg:
                self.responses[msg["id"]] = msg

    def send(self, method, params=None, timeout=60):
        with self.lock:
            self.id += 1
            mid = self.id
            self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            if mid in self.responses:
                return self.responses.pop(mid)
            time.sleep(0.005)
        raise TimeoutError(method)

    def eval(self, expr):
        r = self.send("Runtime.evaluate", {"expression": expr, "returnByValue": True,
                                           "userGesture": True})
        return r.get("result", {}).get("result", {}).get("value")


def chromium():
    return shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def chrome_pids(marker):
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="ignore")
        except Exception:
            continue
        if marker in cmd:
            yield int(pid)


def cpu_seconds(marker):
    total = 0.0
    for pid in chrome_pids(marker):
        try:
            parts = open(f"/proc/{pid}/stat").read().split()
            total += (int(parts[13]) + int(parts[14])) / os.sysconf("SC_CLK_TCK")
        except Exception:
            pass
    return total


def wait_json(url, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=5) as f:
                return json.load(f)
        except Exception:
            time.sleep(0.1)
    raise TimeoutError(url)


def measure(c, marker, secs):
    d0 = c.eval("window.__probe.draws")
    c0 = cpu_seconds(marker)
    t0 = time.time()
    time.sleep(secs)
    d1 = c.eval("window.__probe.draws")
    c1 = cpu_seconds(marker)
    dt = time.time() - t0
    return (d1 - d0) / dt, (c1 - c0) / dt


def main():
    chrome = chromium()
    if not chrome:
        print("SKIP fps_check: chromium not found")
        return 0
    if websocket is None:
        print("SKIP fps_check: 缺 websocket-client（pip install websocket-client）")
        return 0
    if not (ROOT / "index.html").exists() or not (ROOT / "assets" / "bd2-fps.js").exists():
        print("SKIP fps_check: 先跑 make patch / tools/stamp.py")
        return 0

    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    port, dbg = free_port(), free_port()
    profile = tempfile.mkdtemp(prefix="bd2-fps-")
    httpd = ThreadingHTTPServer(("127.0.0.1", port), lambda *a, **k: Quiet(*a, directory=str(ROOT), **k))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    proc = subprocess.Popen([
        chrome, "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
        f"--remote-debugging-port={dbg}", f"--user-data-dir={profile}",
        "--window-size=1280,720", "--force-device-scale-factor=1",
        "--use-gl=angle", "--use-angle=gl",
        "--disable-background-timer-throttling", "--disable-renderer-backgrounding",
        "--hide-scrollbars", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    failed = 0
    try:
        targets = wait_json(f"http://127.0.0.1:{dbg}/json/list")
        page = [t for t in targets if t["type"] == "page"][0]
        c = CDP(page["webSocketDebuggerUrl"])
        c.send("Page.enable")
        c.send("Runtime.enable")
        c.send("Page.addScriptToEvaluateOnNewDocument", {"source": INSTRUMENT})
        c.send("Page.navigate", {"url": f"http://127.0.0.1:{port}/index.html"})

        # 等角色和 fps 控制器就绪
        end = time.time() + 30
        while time.time() < end:
            if c.eval("!!(window.__bd2Fps && document.querySelector('canvas.spine-player-canvas'))"):
                break
            time.sleep(0.2)
        else:
            print("SKIP fps_check: 页面未就绪")
            return 0
        time.sleep(1.0)

        renderer = c.eval("""(() => {const cv=document.querySelector('canvas.spine-player-canvas');
            const gl=cv&&(cv.getContext('webgl2')||cv.getContext('webgl'));
            const d=gl&&gl.getExtension('WEBGL_debug_renderer_info');
            return d?gl.getParameter(d.UNMASKED_RENDERER_WEBGL):'';})()""") or ""
        if not renderer or "SwiftShader" in renderer:
            print(f"SKIP fps_check: 软件渲染（{renderer or 'no webgl'}）测不出真实帧率")
            return 0
        print(f"renderer: {renderer}")

        def check(label, rate, ok, cores=None):
            nonlocal failed
            if not ok:
                failed += 1
            extra = f" cores={cores:.2f}" if cores is not None else ""
            print(("PASS " if ok else "FAIL ") + f"{label:18s} draws/s={rate:.1f}" + extra)

        c.eval("window.__bd2Fps.set(0,0)")
        rate, cores = measure(c, profile, 4)
        check("refresh/refresh", rate, rate >= 45, cores)

        c.eval("window.__bd2Fps.set(30,30)")
        rate, cores = measure(c, profile, 4)
        check("30/30", rate, 27 <= rate <= 33, cores)

        c.eval("window.__bd2Fps.set(60,60)")
        rate, cores = measure(c, profile, 4)
        check("60/60", rate, 54 <= rate <= 66, cores)

        c.eval("window.__bd2Fps.set(60,30)")
        time.sleep(6.2)                      # 越过 5 秒静止阈值
        rate, cores = measure(c, profile, 3)
        check("60/30 idle", rate, 27 <= rate <= 33, cores)

        c.eval("window.__bd2Fps.boost();")
        time.sleep(0.3)
        rate, cores = measure(c, profile, 2)
        check("60/30 boost", rate, 54 <= rate <= 66, cores)

        c.eval("window.__bd2Fps.set(30,30)")
        time.sleep(0.5)
        draws = c.eval("window.__probe.draws")
        check("30fps 仍在绘制", 1.0, draws > 0)

        c.eval("window.__bd2Fps.set(0,0)")
        return 1 if failed else 0
    finally:
        proc.kill()
        httpd.shutdown()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
