"""冒烟测试：用无头 Chromium 真跑一次壁纸，抓未捕获异常。

用法: python3 tools/smoke.py
CI 里没有 chromium 时跳过（返回 0 并提示）。
"""
import pathlib, re, shutil, subprocess, sys, tempfile

LIVE = pathlib.Path(__file__).resolve().parent.parent
BAD = re.compile(r"Uncaught|ReferenceError|TypeError|SyntaxError", re.I)

def main():
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if not chrome:
        print("SKIP smoke: chromium not found")
        return 0
    if not (LIVE / "index.html").exists():
        print(f"FAIL smoke: 壁纸目录不存在 {LIVE}")
        return 1
    with tempfile.TemporaryDirectory() as td:
        err = pathlib.Path(td) / "console.log"
        dom = pathlib.Path(td) / "dom.html"
        with open(err, "wb") as f, open(dom, "wb") as g:
            subprocess.run([
                chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                "--allow-file-access-from-files", "--enable-logging=stderr", "--v=0",
                "--virtual-time-budget=9000", "--dump-dom",
                (LIVE / "index.html").as_uri(),
            ], stdout=g, stderr=f, timeout=180)
        text = err.read_text(errors="ignore")
        html = dom.read_text(errors="ignore")
    hits = [l for l in text.splitlines() if "CONSOLE" in l and BAD.search(l)]
    if hits:
        print("FAIL smoke: 页面有未捕获异常")
        for l in hits[:10]:
            print("  " + l.strip()[:300])
        return 1
    # 应用必须渲染出来（wallpaper-root），悬浮球控件必须挂载（.wc-btn）
    if 'class="wallpaper-root' not in html:
        print("FAIL smoke: 应用没有渲染出 wallpaper-root")
        return 1
    if 'class="wc-btn' not in html:
        print("FAIL smoke: 悬浮球控件没有挂载（.wc-btn 缺失）")
        return 1
    print("PASS smoke: 无未捕获异常，应用与控件已挂载")
    return 0

if __name__ == "__main__":
    sys.exit(main())
