"""从磁盘重建 mirror/manifest.json（含每文件 sha256），不重新下载。

用法: python3 tools/manifest.py
"""
import hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIRROR = ROOT / "assets"
TASKS = ROOT / "tasks" / "upstream.json"

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    old = json.loads((ROOT / "tasks" / "manifest.json").read_text())
    ids = json.loads(TASKS.read_text())
    files, total = [], 0
    for sub in ["spines", "audios"]:
        for p in sorted((MIRROR / sub).rglob("*")):
            if not p.is_file():
                continue
            size = p.stat().st_size
            total += size
            files.append({"path": str(p.relative_to(MIRROR)), "size": size, "sha256": sha256(p)})
    m = {
        "characters": len(ids),
        "file_count": len(files),
        "files": files,
        "total_bytes": total,
        "missing": [],
        "upstream": old.get("upstream", "Jelosus2/BD2-L2D-Viewer@main"),
        "spine_audio_maps": old.get("spine_audio_maps", {"spine": {}, "audio": {}}),
    }
    (ROOT / "tasks" / "manifest.json").write_text(json.dumps(m, indent=1))
    print(f"manifest rebuilt files={len(files)} total={total/1e6:.1f}MB")
    return 0

if __name__ == "__main__":
    sys.exit(main())
