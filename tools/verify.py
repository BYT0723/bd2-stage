"""校验：素材与 manifest 一致、bundle 补丁在位、index.html 版本号正确。

用法: python3 tools/verify.py
"""
import hashlib, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MANIFEST = ROOT / "tasks" / "manifest.json"

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def tree(root):
    files = [p for p in root.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)

def main():
    assert MANIFEST.exists(), "缺 tasks/manifest.json（先跑 make sync）"
    m = json.loads(MANIFEST.read_text())
    assert m["missing"] == [], f"缺失 {len(m['missing'])}: {m['missing'][:10]}"

    bad = []
    for f in m["files"]:
        p = ASSETS / f["path"]
        if not p.exists() or p.stat().st_size != f["size"] or sha256(p) != f["sha256"]:
            bad.append(f["path"])
    assert not bad, f"manifest 校验失败 {len(bad)} 个: {bad[:8]}"

    n_files = len([p for p in ASSETS.rglob("*") if p.is_file()
                   and p.parent.name != "." and (p.parent.parent.name in ("spines", "audios"))])
    print(f"assets: spines={tree(ASSETS / 'spines')[0]} audios={tree(ASSETS / 'audios')[0]} files={n_files}")

    js = (ASSETS / "index-Dsqno3tX.js").read_text()
    assert "function T_(e){return!0}" in js, "bundle 缺少本地素材补丁（make patch）"
    assert "logoVisible:!1" in js, "bundle 缺少 Logo 关闭补丁（make patch）"
    assert "bd2AudioPool" in js, "bundle 缺少语音池补丁（make patch）"
    assert "t.preload=`none`" in js, "bundle 语音仍会预加载（make patch）"
    assert "t.onerror=()=>" in js, "bundle 复用语音元素时监听器会叠加（make patch）"
    r = subprocess.run(["node", "--check", str(ASSETS / "index-Dsqno3tX.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    html = (ROOT / "index.html").read_text()
    assert "?v=DEV" not in html, "index.html 版本号未刷新（make patch）"
    for name in ["bd2-data.js", "bd2-fav-random.js"]:
        mm = re.search(re.escape(name) + r"\?v=([0-9a-f]{10})", html)
        assert mm, f"{name} 缺版本号"
        assert mm.group(1) == sha256(ASSETS / name)[:10], f"{name} 版本号与内容不一致"

    print(f"VERIFY OK files={m.get('file_count', len(m['files']))} "
          f"total={m['total_bytes']/1e6:.1f}MB")
    return 0

if __name__ == "__main__":
    sys.exit(main())
