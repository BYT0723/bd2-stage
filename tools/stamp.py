"""把 custom/ 的外挂装进 assets/，并给 index.html 写内容哈希版本号。

用法: python3 tools/stamp.py
"""
import hashlib, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
CUSTOM = ROOT / "custom"
TEMPLATE = ROOT / "templates" / "index.html"

ASSETS = ["bd2-data.js", "bd2-bg-theme.js", "bd2-fav-random.js"]

def main():
    for name in ASSETS:
        src = CUSTOM / name
        if src.exists():
            shutil.copyfile(src, ROOT / "assets" / name)
    html = TEMPLATE.read_text()
    for name in ASSETS:
        f = ROOT / "assets" / name
        ver = hashlib.sha256(f.read_bytes()).hexdigest()[:10]
        html = html.replace(f"{name}?v=DEV", f"{name}?v={ver}")
    (ROOT / "index.html").write_text(html)
    vers = re.findall(r"(bd2-[\w.-]+\.js)\?v=([0-9a-f]{10})", html)
    print("stamped " + ", ".join(f"{n}@{v}" for n, v in vers))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
