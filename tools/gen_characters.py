"""生成 custom/bd2-characters.json（bundle 顺序 id+elem）。用法: python3 tools/gen_characters.py"""
import pathlib, re, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
js = (ROOT / "tasks" / "bundle-reference.js.txt").read_text()
m = re.search(r'var Fv=\{([^}]+)\}', js)
fv = dict(re.findall(r'"?([A-Za-z0-9_]+)"?:`([a-z]+)`', m.group(1)))
order = json.load(open(ROOT / "tasks" / "char_order.json"))
data = [{"id": i, "elem": fv.get(i, "none")} for i in order]
# v4 数据：顺序+属性+三语言显示名（文本→id 映射用）
enm = {m.group(1): (m.group(2), m.group(3)) for m in
       re.finditer(r'"?([A-Za-z0-9_]+)"?:\{charName:`([^`]*)`,costumeName:`([^`]*)`', js)}
kvm = {}
for m in re.finditer(r'(?:\"([A-Za-z0-9_]+)\"|(?<![A-Za-z0-9_\"])([A-Za-z0-9_]+)):\{zh:\[([^\]]*)\],ja:\[([^\]]*)\]\}', js):
    cid = m.group(1) or m.group(2)
    zh = re.findall(r'`([^`]*)`', m.group(3)); ja = re.findall(r'`([^`]*)`', m.group(4))
    if cid and cid not in kvm and zh:
        kvm[cid] = (zh, ja)
names = {}
for i in order:
    a, b = enm.get(i, (i, ""))
    es = a + " · " + b
    z, j = kvm.get(i, ([], []))
    zs = (z[0] + " · " + z[1]) if len(z) >= 2 and z[0] else es
    js_ = (j[0] + " · " + j[1]) if len(j) >= 2 and j[0] else es
    names[i] = {"en": es, "zh": zs, "ja": js_}
db = {"order": order, "elem": {d["id"]: d["elem"] for d in data}, "names": names}
data_js = ROOT / "assets" / "bd2-data.js"
data_js.write_text("window.__BD2_CHARACTERS=" + json.dumps(db, ensure_ascii=False) + ";")
print(f"wrote {data_js.name} n={len(data)}")
