"""全量镜像：spines+audios。

默认与上游做轻量比对（HEAD 的 Content-Length），大小变化即重新下载，
因此重复运行能把上游更新同步下来；--refresh 强制全部重下。
用法: python3 tools/mirror.py [--refresh] [--limit N]
"""
import json, pathlib, re, sys, hashlib, urllib.request, time

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

def resolve(cands, dest, refresh):
    """返回 (data, changed)。本地已存在且与上游同大小则复用。"""
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        local = dest.stat().st_size
        remote = None
        for url in cands:
            remote = upstream_size(url)
            if remote is not None:
                break
        if remote is None or remote == local:
            return dest.read_bytes(), False
    data, _ = fetch(cands)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data, True

def main():
    refresh = "--refresh" in sys.argv
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 0
    js = BUNDLE.read_text()
    spine_map, audio_map = {}, {}
    for m in re.finditer(r'"?([A-Za-z0-9_]+)"?:\{charName:[^}]*?spine:`([^`]*)`[^}]*?audio:`([^`]*)`', js):
        spine_map[m.group(1)] = m.group(2); audio_map[m.group(1)] = m.group(3)
    ids = json.loads(TASKS.read_text())
    if limit: ids = ids[:limit]
    files, missing, total, changed = [], [], 0, 0
    for idx, cid in enumerate(ids, 1):
        spine = spine_map.get(cid, f"char{cid}")
        audio = audio_map.get(cid, "")
        for ext in ["skel", "atlas", "png"]:
            fn = f"{spine}.{ext}"
            dest = MIRROR / "spines" / cid / fn
            try:
                data, was = resolve([f"{b}/spines/{cid}/{fn}" for b in BASES], dest, refresh)
            except IOError:
                missing.append(f"spines/{cid}/{fn}"); continue
            changed += 1 if was else 0
            total += len(data)
            files.append({"path": f"spines/{cid}/{fn}", "size": len(data),
                          "sha256": hashlib.sha256(data).hexdigest()})
        if audio:
            for lang in ["JP", "KR"]:
                for n in [1, 2, 3]:
                    fn = f"{audio}_{n}.webm"
                    dest = MIRROR / "audios" / cid / lang / fn
                    try:
                        data, was = resolve([f"{b}/audios/{cid}/{lang}/{fn}" for b in BASES], dest, refresh)
                    except IOError:
                        missing.append(f"audios/{cid}/{lang}/{fn}"); continue
                    changed += 1 if was else 0
                    total += len(data)
                    files.append({"path": f"audios/{cid}/{lang}/{fn}", "size": len(data),
                                  "sha256": hashlib.sha256(data).hexdigest()})
        print(f"[{idx}/{len(ids)}] {cid} total={total/1e6:.1f}MB "
              f"updated={changed} missing={len(missing)}", flush=True)
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
