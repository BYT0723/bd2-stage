"""帧率属性：静态/契约测试（真实帧率由 tools/fps_check.py 在真实 GPU 上验证）。"""
import hashlib, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = ROOT
CUSTOM = ROOT / "custom"
PROPS = json.loads((ROOT / "project.json").read_text())["general"]["properties"]


def test_properties_shape():
    assert "fps" in PROPS, "缺活动帧率属性 fps"
    assert "fpsIdle" in PROPS, "缺静止帧率属性 fpsIdle"
    for name in ("fps", "fpsIdle"):
        p = PROPS[name]
        assert p["type"] == "combo", f"{name} 必须是 combo"
        assert p["value"] == "refresh", f"{name} 默认必须是 refresh（与现状一致）"
        assert [o["value"] for o in p["options"]] == ["30", "60", "refresh"], \
            f"{name} 选项必须是 30/60/refresh"
    assert "FPS" in PROPS["fps"]["text"], "活动帧率文案缺 FPS"
    assert "Idle" in PROPS["fpsIdle"]["text"], "静止帧率文案缺 Idle FPS"
    idx = [PROPS["fps"]["index"], PROPS["fpsIdle"]["index"]]
    assert len(set(idx)) == 2, "两个属性 index 不得重复"
    orders = [p.get("order") for p in PROPS.values()]
    assert len(orders) == len(set(orders)), "order 不得重复"
    s = (CUSTOM / "bd2-fps.js").read_text()
    assert "wallpaperPropertyListener" in s, "必须监听 WE 属性下发"
    assert "fpsIdle" in s, "属性接线必须读取 fpsIdle"


def test_scheduler_contract():
    s = (CUSTOM / "bd2-fps.js").read_text()
    for key in [
        "__bd2Fps", "__bd2FpsBoost",
        "IDLE_MS = 5000", "DEFAULT_ACTIVE = 0", "DEFAULT_IDLE = 0",
        "cancelAnimationFrame", "queue", "canceled", "nextAt", "refresh",
        "use strict",
    ]:
        assert key in s, f"缺 {key}"
    assert "installed" in s, "默认两档 refresh 时必须能旁路（不安装包装）"
    assert "fetch(" not in s, "外挂不得联网"
    m = s.replace("http://www.w3.org/2000/svg", "")
    assert "http://" not in m and "https://" not in m, "外挂不得有远程请求"
    assert "T_(" not in s, "外挂不得碰 bundle 内部函数"


def test_panel_rows():
    s = (CUSTOM / "bd2-fps.js").read_text()
    assert "活动帧率 (FPS)" in s, "面板缺活动帧率行"
    assert "静止帧率 (Idle FPS)" in s, "面板缺静止帧率行"
    assert "wc-seg__btn--active" in s, "高亮必须复用面板现有 active 样式"
    assert "data-v-" in s, "注入节点必须复制 Vue scoped 属性，否则样式不生效"
    assert "MutationObserver" in s and "getClientRects" in s, "面板注入必须等面板出现"
    assert "bd2-fps-seg" in s, "新增 seg 必须带可排除标记"
    fav = (CUSTOM / "bd2-fav-random.js").read_text()
    assert "bd2-fps-seg" in fav, "curLang 必须排除帧率 seg 组（否则 3 按钮组会被误认成语言组）"
    assert "curLang" in fav


def test_integration():
    carousel = (CUSTOM / "bd2-carousel.js").read_text()
    assert "__bd2FpsBoost" in carousel, "换人 swap 必须调用帧率提速"
    template = (ROOT / "templates" / "index.html").read_text()
    assert "bd2-fps.js?v=DEV" in template, "模板必须挂载帧率脚本"
    stamp = (ROOT / "tools" / "stamp.py").read_text()
    assert '"bd2-fps.js"' in stamp, "stamp 必须把帧率脚本装进 assets"
    live = (ROOT / "index.html").read_text()
    m = re.search(r"bd2-fps\.js\?v=([0-9a-f]{10})", live)
    assert m, "线上 index.html 缺帧率脚本版本号"
    f = LIVE / "assets" / "bd2-fps.js"
    assert f.exists(), "assets/bd2-fps.js 未生成（先跑 stamp.py）"
    assert m.group(1) == hashlib.sha256(f.read_bytes()).hexdigest()[:10], \
        "帧率脚本版本号与内容不一致"
    verify = (ROOT / "tools" / "verify.py").read_text()
    assert "bd2-fps.js" in verify, "verify.py 必须校验帧率脚本版本"
    makefile = (ROOT / "Makefile").read_text()
    assert "fpscheck" in makefile, "Makefile 缺 fpscheck 目标"
    probe = ROOT / "tools" / "fps_check.py"
    assert probe.exists(), "缺运行时探针 tools/fps_check.py"
    text = probe.read_text()
    assert "SwiftShader" in text, "探针必须识别软件渲染并 SKIP"
    assert "draws" in text, "探针必须统计真实 WebGL draw 次数"
    assert "帧率" in (ROOT / "README.md").read_text(), "README 功能列表缺帧率说明"
