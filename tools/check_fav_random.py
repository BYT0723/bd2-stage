"""静态自检：数据、外挂脚本约定、bundle 指纹。用法: python3 tools/check_fav_random.py"""
import hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = pathlib.Path(__file__).resolve().parent.parent
ok = True

def check(name, cond, detail=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + (f" ({detail})" if detail and not cond else ""))
    if not cond:
        ok = False

db = json.loads((LIVE / "assets" / "bd2-data.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
order = json.load(open(ROOT / "tasks" / "char_order.json"))
check("角色表顺序=bundle", db["order"] == order, f"{len(db['order'])} vs {len(order)}")
check("elem合法", {v for v in db["elem"].values()} <= {"fire", "water", "wind", "light", "dark", "none"})
check("三语言名齐", all(set(v) == {"en", "zh", "ja"} for v in db["names"].values()))
check("NPC中文名已抓到", db["names"]["400070"]["zh"].startswith("内肯"))

s = (ROOT / "custom" / "bd2-fav-random.js").read_text()
check("含 .wc-list__item", ".wc-list__item" in s)
check("含 .wc-listnav__btn", ".wc-listnav__btn" in s)
check("含 bd2-wallpaper-favs", "bd2-wallpaper-favs" in s)
check("含 MutationObserver", "MutationObserver" in s)
check("不碰bundle内部", "T_(" not in s)
m = s.replace("http://www.w3.org/2000/svg", "")
check("无远程请求", "http://" not in m and "https://" not in m)
check("无fetch", "fetch(" not in s)
check("名字映射走索引", "buildIndex" in s and "IDX[" in s)
check("清过滤用显式状态", "pendingClear" in s and "favEnterAt" not in s)
check("无死代码tick", "function tick()" not in s)
check("收藏自建列表", "renderFavList" in s and "bd2-fitem" in s and "favPage" in s)
check("渲染守卫", "lastFavKey" in s)
check("类目按钮自绘样式", "aspect-ratio:1/1" in s)
check("随机在列表下分页上", "positionTools" in s)
check("三控件同一行", ".bd2-tools{display:flex" in s and "bd2-timer-secs" in s)
check("翻页批量连点", "批量连点" in s)
check("心形用SVG填充色", "heartSvg" in s and "fill:none" in s)
check("名字可压缩", ".wc-list__item>.wc-list__name" in s)
check("随机不重复(洗牌袋)", "nextPick" in s and "bagKey" in s)
check("定时随机", "timerFire" in s and "startTimer" in s)
check("定时按面板可见性暂停", "getClientRects" in s and "panelVisible" in s)
check("定时状态已声明", "timerNextAt = 0" in s and "timerUi = null" in s)
check("严格模式无隐式全局", "use strict" in s)
check("换人不依赖面板", "piniaCharStore" in s and "setCharacter" in s)
check("间隔免键盘+带单位", "TIMER_STEPS" in s and "secsLabel" in s)
check("间隔档位5m/15m/1h", "TIMER_STEPS = [300, 900, 3600]" in s)
check("Logo渲染已移除", ".wp-logo{display:none!important}" in s)
check("Logo配置分组已移除", ".wc-foldrow{display:none!important}" in s)
check("页码按列表真实顺序", "listIds" in s and "st.characters" in s and "filteredIds" not in s)
check("页码多语言解析", "pageNums" in s and r"(\d+)\D+(\d+)" in s)
check("随机后定位到所在页", "syncListTo" in s and "scrollIntoView" in s)
_live_props = json.loads((LIVE / "project.json").read_text())["general"]["properties"]
check("project.json无logoScale", "logoScale" not in _live_props)

bundle = (ROOT / "tasks" / "bundle-reference.js.txt").read_text()
for sel in ["wc-list__item", "wc-listnav__btn", "wc-elem--active", "wc-listnav__page"]:
    check(f"bundle指纹 {sel}", sel in bundle)

html = (ROOT / "templates" / "index.html").read_text()
check("模板挂载", "bd2-fav-random.js?v=DEV" in html and "bd2-data.js?v=DEV" in html)

live_html = (LIVE / "index.html").read_text()
check("线上版本号已哈希化", "?v=DEV" not in live_html)
for name in ["bd2-data.js", "bd2-fav-random.js"]:
    mm = re.search(re.escape(name) + r"\?v=([0-9a-f]{10})", live_html)
    f = LIVE / "assets" / name
    good = bool(mm) and f.exists() and \
        mm.group(1) == hashlib.sha256(f.read_bytes()).hexdigest()[:10]
    check(f"{name} 缓存版本一致", good)

check("运行时不再分发冗余json", not (LIVE / "assets" / "bd2-characters.json").exists())

sys.exit(0 if ok else 1)
