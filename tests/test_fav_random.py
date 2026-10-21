"""收藏+随机：静态测试（DOM 行为靠手动清单验证）。"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CUSTOM = ROOT / "custom"
LIVE = pathlib.Path(__file__).resolve().parent.parent
DIST = LIVE

def _db():
    src = (LIVE / "assets" / "bd2-data.js").read_text()
    return json.loads(src.split("=", 1)[1].rstrip().rstrip(";"))

def test_characters_data():
    db = _db()
    order = json.load(open(ROOT / "tasks" / "char_order.json"))
    assert db["order"] == order, "顺序必须=bundle 顺序"
    assert {v for v in db["elem"].values()} <= {"fire", "water", "wind", "light", "dark", "none"}
    assert len(db["names"]) == len(order), "每个角色都要有三语言名"

def test_npc_names_zh():
    names = _db()["names"]
    assert names["400070"]["zh"].startswith("内肯"), names["400070"]["zh"]
    assert names["000001"]["zh"].startswith("罗什")

def test_inject_script():
    s = (CUSTOM / "bd2-fav-random.js").read_text()
    for sel in [".wc-list__item", ".wc-listnav", "bd2-wallpaper-favs", "MutationObserver"]:
        assert sel in s, f"缺 {sel}"
    assert "T_(" not in s, "外挂不得碰 bundle 内部函数"
    m = s.replace("http://www.w3.org/2000/svg", "")
    assert "http://" not in m and "https://" not in m, "外挂不得有远程请求（SVG命名空间除外）"
    assert "fetch(" not in s, "file协议下fetch会被拦，数据必须内联"
    assert "__bd2fav" in s, "缺启动标记"
    assert ":scope > .bd2-bar" not in s, "bar存在性检查不能用:scope限定"
    assert "idFromButton" in s and "cleanText" in s, "必须文本→id映射"
    assert "wc-elems" in s, "收藏开关必须并入属性行"
    assert "buildIndex" in s, "名字映射必须走预建索引（避免每帧 O(n)）"
    assert "pendingClear" in s, "清属性过滤不得用时间窗猜测"
    assert "lastFavKey" in s, "自建列表渲染必须有key守卫"
    assert "renderFavList" in s, "收藏必须是自建独立列表（自有分页）"
    assert "positionTools" in s, "工具行须按当前模式摆到分页行之前"
    assert ".bd2-tools{display:flex" in s, "三个随机控件必须在同一行"
    assert "批量连点" in s, "翻页必须批量连点"
    assert "heartSvg" in s, "图标须用SVG+填充色"
    assert ".wc-list__item>.wc-list__name" in s, "长名字必须可压缩"
    assert "nextPick" in s and "bagKey" in s, "随机必须用洗牌袋，一轮内不重复"
    assert "timerFire" in s and "startTimer" in s, "定时随机缺失"
    assert "getClientRects" in s, "定时暂停必须按面板可见性判断（不能用 document.hidden）"
    assert "timerNextAt = 0" in s and "timerUi = null" in s, "定时器状态变量必须声明（严格模式下未声明会中断整脚本）"
    assert "piniaCharStore" in s and "__vue_app__" in s, "换人不得依赖面板列表（面板关闭时列表不存在）"
    assert "setCharacter" in s, "随机/收藏/定时必须走 setCharacter"
    assert "TIMER_STEPS = [300, 900, 3600]" in s, "间隔档位必须是 5 分/15 分/1 小时"
    assert "secsLabel" in s, "间隔必须带单位"
    assert ".wp-logo{display:none!important}" in s, "Logo 渲染必须被移除"
    assert ".wc-foldrow{display:none!important}" in s, "Logo 配置分组必须被移除"
    assert "listIds" in s and "st.characters" in s, "页码必须按列表真实顺序（store.characters）算，不能用 DB.order"
    assert "filteredIds" not in s, "旧的有序表算页逻辑必须删除"
    assert "pageNums" in s and r"(\d+)\D+(\d+)" in s, "页码解析必须兼容 第a/b页 · a/b ページ · Page a of b"
    assert "syncListTo" in s, "随机后必须定位到该角色所在页"
    assert "scrollIntoView" in s, "跳页后列表必须滚进可视区"

def test_logo_removed():
    import json
    props = json.loads((LIVE / "project.json").read_text())["general"]["properties"]
    assert "logoScale" not in props, "project.json 不应再有 logoScale 配置"
    bundle = (ROOT / "tasks" / "bundle-reference.js.txt").read_text()
    assert "logoVisible:!0" in bundle, "原始 bundle 指纹变化，需复核 Logo 补丁点"

def test_versions_stamped():
    html = (LIVE / "index.html").read_text()
    assert "?v=DEV" not in html, "线上版本号未被 deploy.py 替换"
    for name in ["bd2-data.js", "bd2-fav-random.js"]:
        m = re.search(re.escape(name) + r"\?v=([0-9a-f]{10})", html)
        assert m, f"{name} 缺内容哈希版本号"
        import hashlib
        h = hashlib.sha256((LIVE / "assets" / name).read_bytes()).hexdigest()[:10]
        assert m.group(1) == h, f"{name} 版本号与内容不一致（缓存不会刷新）"

def test_dist_matches_live():
    import hashlib
    for rel in ["assets/bd2-fav-random.js", "assets/bd2-data.js"]:
        a, b = DIST / rel, LIVE / rel
        assert a.exists() and b.exists(), f"缺 {rel}"
        assert hashlib.sha256(a.read_bytes()).hexdigest() == \
               hashlib.sha256(b.read_bytes()).hexdigest(), f"dist 与线上不一致: {rel}（回滚点过期）"
