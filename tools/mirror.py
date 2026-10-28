"""全量镜像：spines+audios。

默认与上游做轻量比对（HEAD 的 Content-Length），大小变化即重新下载，
因此重复运行能把上游更新同步下来；--refresh 强制全部重下。
并发提速：默认 4 线程（保守值，防上游限流），可用 --jobs N 调整（1-8）。
用法: python3 tools/mirror.py [--refresh] [--limit N] [--jobs N]
"""
import concurrent.futures as futures
import json, pathlib, re, sys, hashlib, threading, urllib.request, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "tasks" / "bundle-reference.js.txt"
MIRROR = ROOT / "assets"
TASKS = ROOT / "tasks" / "upstream.json"
BASES = [
    "https://cdn.jsdelivr.net/gh/Jelosus2/BD2-L2D-Viewer@main/src/assets",
    "https://jelosus2.github.io/BD2-L2D-Viewer/assets",
]

def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "bd2-mirror/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def upstream_size(url, timeout=15):
    """HEAD 拿 Content-Length；拿不到返回 None（视为未知，保留本地）。"""
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "bd2-mirror/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            n = r.headers.get("Content-Length")
            return int(n) if n and n.isdigit() else None
    except Exception:
        return None

def fetch(cands, timeout=30):
    last = None
    for url in cands:
        for attempt in range(3):
            try:
                return get(url, timeout), url
            except Exception as e:
                last = e
                time.sleep(1 + attempt)
    raise IOError(f"all failed {cands[0]}: {last}")

def sha256_file(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def load_old_manifest():
    """读旧 manifest 的 path -> (size, sha256)，命中则免读文件。"""
    mp = ROOT / "tasks" / "manifest.json"
    try:
        m = json.loads(mp.read_text())
    except Exception:
        return {}
    out = {}
    for f in m.get("files", []):
        try:
            out[f["path"]] = (f["size"], f["sha256"])
        except KeyError:
            continue
    return out


def process_one(job, refresh, old):
    """单个文件：复用或下载，返回 (idx, rel, size, sha256, changed, missing)。"""
    idx, rel, dest, cands = job
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        local = dest.stat().st_size
        remote = None
        for url in cands:
            remote = upstream_size(url)
            if remote is not None:
                break
        if remote is None or remote == local:
            o = old.get(rel)
            if o and o[0] == local:
                return idx, rel, local, o[1], False, None
            return idx, rel, local, sha256_file(dest), False, None
    try:
        data, _ = fetch(cands)
    except IOError:
        return idx, rel, 0, "", False, rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return idx, rel, len(data), hashlib.sha256(data).hexdigest(), True, None

def main():
    refresh = "--refresh" in sys.argv
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
    jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
    jobs = max(1, min(8, jobs))
    js = BUNDLE.read_text()
    spine_map, audio_map = {}, {}
    for m in re.finditer(r'"?([A-Za-z0-9_]+)"?:\{charName:[^}]*?spine:`([^`]*)`[^}]*?audio:`([^`]*)`', js):
        spine_map[m.group(1)] = m.group(2); audio_map[m.group(1)] = m.group(3)
    ids = json.loads(TASKS.read_text())
    if limit: ids = ids[:limit]
    old = load_old_manifest() if not refresh else {}
    tasks = []
    for cid in ids:
        spine = spine_map.get(cid, f"char{cid}")
        audio = audio_map.get(cid, "")
        for ext in ["skel", "atlas", "png"]:
            fn = f"{spine}.{ext}"
            tasks.append((len(tasks), f"spines/{cid}/{fn}",
                          MIRROR / "spines" / cid / fn,
                          [f"{b}/spines/{cid}/{fn}" for b in BASES]))
        if audio:
            for lang in ["JP", "KR"]:
                for n in [1, 2, 3]:
                    fn = f"{audio}_{n}.webm"
                    tasks.append((len(tasks), f"audios/{cid}/{lang}/{fn}",
                                  MIRROR / "audios" / cid / lang / fn,
                                  [f"{b}/audios/{cid}/{lang}/{fn}" for b in BASES]))
    results = [None] * len(tasks)
    missing, total, changed = [], 0, 0
    done = 0
    lock = threading.Lock()
    def on_done(fut):
        nonlocal done, total, changed
        idx, rel, size, sha, was, miss = fut.result()
        results[idx] = (rel, size, sha, was, miss)
        with lock:
            done += 1
            if miss:
                missing.append(miss)
            else:
                total += size
                changed += 1 if was else 0
            if done % 100 == 0 or done == len(tasks):
                print(f"[{done}/{len(tasks)}] total={total/1e6:.1f}MB "
                      f"updated={changed} missing={len(missing)}", flush=True)
    with futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = [ex.submit(process_one, t, refresh, old) for t in tasks]
        for f in futs:
            f.add_done_callback(on_done)
        for f in futures.as_completed(futs):
            f.result()
    files = []
    for rel, size, sha, _was, miss in results:
        if miss:
            continue
        files.append({"path": rel, "size": size, "sha256": sha})
    missing.sort()
    (ROOT / "tasks" / "manifest.json").write_text(json.dumps(
        {"characters": len(ids), "file_count": len(files), "files": files,
         "total_bytes": total,
         "missing": missing, "upstream": "Jelosus2/BD2-L2D-Viewer@main",
         "spine_audio_maps": {"spine": spine_map, "audio": audio_map}}, indent=1))
    print(f"DONE files={len(files)} total={total/1e6:.1f}MB updated={changed} missing={len(missing)}")
    if missing:
        print("MISSING:", missing[:20])
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
