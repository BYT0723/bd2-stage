"""全量素材与补丁的校验（配合 tools/verify.py）。"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MANIFEST = ROOT / "tasks" / "manifest.json"

def test_manifest_complete():
    assert MANIFEST.exists(), "缺 tasks/manifest.json（先跑 make sync）"
    m = json.loads(MANIFEST.read_text())
    assert m["characters"] == 234, f"角色数 {m['characters']}"
    assert m["missing"] == [], f"缺失: {m['missing'][:5]}"

def test_bundle_patched():
    js = (ASSETS / "index-Dsqno3tX.js").read_text()
    assert "function T_(e){return!0}" in js, "补丁未应用"
    assert "logoVisible:!1" in js, "Logo 未关闭"
    assert "cdn.jsdelivr.net" in js, "兜底不应被删"
    assert "bd2AudioPool" in js, "语音元素未复用（换人次数一多会堆积 Audio）"
    assert "t.preload=`none`" in js, "语音应在点击时才加载"
    assert "t.onerror=()=>" in js, "复用元素必须覆盖监听器，不能 addEventListener 叠加"
    assert "bd2Bg.img=rb(String(t??``))" in js, "背景属性未接线"
    assert "bd2Fg.img=rb(String(t??``))" in js, "前景属性未接线"
    assert "bd2Apply(1)" in js, "属性下发必须 force（否则被旧手选值拦死）"
    props = json.loads((ROOT / "project.json").read_text())["general"]["properties"]
    for name, p in props.items():
        if p.get("type") == "file" and name.startswith("background"):
            assert name in js, f"背景属性 {name} 在 bundle 里没接线（改名必死）"
    assert "BD2_BG_AUTO" in js, "背景默认值未注入"
    assert "var BD2_BG_AUTO" in js, "BD2_BG_AUTO 必须用 var 声明（漏写会在模块严格模式下 ReferenceError 白屏）"
    assert "bgImageLight" not in js, "旧图片属性未移除"
    assert "bgVideo" not in js, "旧视频属性未移除（customBackgroundVideo 除外）"
    assert "customBackgroundVideo" in js, "视频背景状态位未注入"
    assert "bd2Video(" in js, "视频背景 applier 未注入"
    assert "background_dark" not in js, "旧深色背景属性未移除"
    assert "foreground_dark" not in js, "旧深色前景属性未移除"
    assert "bd2Dark" not in js, "深色跟随逻辑未移除"
    assert "bd2Fg" in js, "前景槽位未注入"
    assert "bd2Light(" in js, "前景渲染未注入"
    assert "bd2FgApply" in js, "前景 applier 未注入"
    assert "mix-blend-mode:screen" in js, "前景必须 screen 混合"
    assert "opacity:.45" in js, "前景默认必须 0.45（过曝修复后降档）"
    assert "opacity:.6" not in js, "前景写死 0.6 已移除（改走滑块）"
    assert "bd2LightOp(" in js, "前景透明度 applier 未注入"
    assert "foregroundOpacity:[`foregroundOpacity`,!0]" in js, "前景透明度 tb 映射未注入"
    assert "h.foregroundOpacity" in js, "前景透明度没进 watcher（拖滑块不实时）"
    assert "customForegroundVideo" in js, "前景视频状态位未注入"
    assert "foreground" in props and props["foreground"].get("type") == "file", "前景属性缺失"
    assert "foreground" in js, "前景属性在 bundle 里没接线"
    assert "foregroundOpacity" in props and props["foregroundOpacity"].get("type") == "slider", "灯光强度属性缺失"
    assert props["foregroundOpacity"].get("value") == 45, "灯光强度默认必须是 45"
    assert props["foregroundOpacity"].get("min") == 0 and props["foregroundOpacity"].get("max") == 100, "灯光强度范围必须是 0-100"
    assert "foregroundOpacity" in js, "灯光强度在 bundle 里没接线"
    assert "background_dark" not in props, "旧 background_dark 未移除"
    assert "foreground_dark" not in props, "旧 foreground_dark 未移除"
    for p in sorted((ROOT / "backgrounds").glob("bd2-light-*-2560x1440.jpg")):
        assert p.stat().st_size < 1024 * 1024, f"{p.name} 超 1MB"
    assert "bd2-fg-shadow" in js, "接地影层未注入"
    assert "bd2Shadow(" in js, "接地影函数未注入"
    assert "h.shadowOffsetX,h.shadowOffsetY,h.shadowScale" in js, "接地影没跟随位移/大小属性"
    assert "st.shadowScale" in js, "接地影没读 shadowScale（尺寸系数未接线）"
    assert "shadowScale:[`shadowScale`,!1]" in js, "阴影大小 tb 映射未注入"
    assert "bd2Shadow(),bd2LightOp()})" in js, "接地影/灯光强度没跟上 watcher"
    assert "z-index:5" in js, "接地影必须在背景之上、人物之下（z-index:5）"
    assert "radial-gradient(closest-side,rgba(0,0,0,.75)" in js, "接地影渐变未注入"
    assert "maskImage=m" in js, "灯光层没挖洞，影子会被 screen 洗掉"
    for name in ("shadowOffsetX", "shadowOffsetY"):
        assert name in props and props[name].get("type") == "slider", f"{name} 属性缺失"
        assert name in js, f"{name} 在 bundle 里没接线"
    assert "shadowScale" in props and props["shadowScale"].get("type") == "slider", "shadowScale 属性缺失"
    assert props["shadowScale"].get("value") == 100, "阴影大小默认必须是 100"
    assert props["shadowScale"].get("min") == 0 and props["shadowScale"].get("max") == 200, "阴影大小范围必须是 0-200"
    assert "window.__bd2CarouselSwap" in js, "换人转盘出场钩子未注入（make patch）"
    assert "window.__bd2CarouselEnter" in js, "换人转盘入场钩子未注入（make patch）"

def test_voice_panel():
    js = (ASSETS / "index-Dsqno3tX.js").read_text()
    assert "bd2Voice" in js, "控制面板语音接线未注入（make patch）"
    assert "日本語" in js and "한국어" in js, "面板语音文案缺失（make patch）"
    assert js.count("bd2Voice(") >= 2, "面板 JP/KR 两档都没接上 setAudioLanguage"
    # 回归：语音按钮文本必须是 Se(...) 直传 + 11,oy（nameLang 同款），
    # 数组包裸字符串（},[Se(...)]）在 block 收集路径下渲染为空按钮（2026-11-01 实测）。
    assert "},[Se(e.l)]" not in js, "语音按钮用了数组包裸字符串，渲染为空（改走 Se 直传）"
    assert "Se(e.l),11,oy" in js, "语音按钮没走 Se 直传 + 11,oy 形态"
    # 回归：语音 seg 与角色名语言 seg 同类名，外挂 curLang 靠全局索引判语言会错位
    # （语音 KR→误判 ja）。语音 seg 必须带可排除标记。
    assert "bd2-voice-seg" in js, "语音 seg 缺 bd2-voice-seg 标记（make patch）"


def test_voice_property():
    import json
    props = json.loads((ROOT / "project.json").read_text())["general"]["properties"]
    assert "audioLanguage" in props, "WE 语音属性缺失（project.json）"
    p = props["audioLanguage"]
    assert p.get("type") == "combo", "语音属性必须是 combo 下拉"
    vals = [o.get("value") for o in p.get("options", [])]
    assert "JP" in vals and "KR" in vals, "combo 选项必须含 JP/KR"
    assert p.get("value") in ("JP", "0"), "combo 默认必须是 JP（首项）"
    js = (ASSETS / "index-Dsqno3tX.js").read_text()
    assert "n==`audioLanguage`" in js, "fb() 没接 audioLanguage 属性（make patch）"
    assert "bd2Voice(`JP`)" in js and "bd2Voice(`KR`)" in js, "fb() 归一化没调 bd2Voice"


def test_audio_patch_fingerprint():
    ref = (ROOT / "tasks" / "bundle-reference.js.txt").read_text()
    assert "t.preload=`auto`" in ref, "原始 bundle 指纹变化，需复核语音补丁点"
    assert "function Vn(){let e=Ln()" in ref, "原始 Vn 指纹变化，需复核语音补丁点"

def test_webgl_context_reuse():
    """换人必须复用同一个 canvas/context：每次新建 context 会永久占 4 个 dmabuf
    （实测 loseContext + canvas 缩 0 都不归还，只有整页销毁才收回）。"""
    js = (ASSETS / "index-Dsqno3tX.js").read_text()
    assert "window.__bd2SpineCanvas" in js, "SpinePlayer 未复用 canvas（make patch）"
    assert js.count("window.__bd2SpineCanvas") == 2, "缓存读写应各一处"
    assert "_c.parentNode.replaceChild(_g,_c)" in js, "复用时必须把缓存 canvas 换进新容器"
    assert "WEBGL_lose_context" not in js, "loseContext 实测不归还（WebKit），不要再用"
    car = (ASSETS / "bd2-carousel.js").read_text()
    assert "releaseSnapshot" in car, "转盘快照画布未释放（每次换人一张整屏 canvas）"
    assert "c.width = 0" in car and "c.height = 0" in car, "快照画布必须缩到 0 才立刻还缓冲"
    p = (ROOT / "tools" / "patch.py").read_text()
    assert "__bd2SpineCanvas" in p, "patch.py 未登记 context 复用补丁"

def test_memory_patches():
    """显存/内存瘦身：2D 渲染用不到 MSAA 和深度缓冲，图层高亮画布在壁纸模式
    下也每帧白清一整屏。实测（780M 核显）合计省 ~160MB GTT。"""
    js = (ASSETS / "index-Dsqno3tX.js").read_text()
    assert "antialias:!1,depth:!1" in js, "WebGL 没关掉无用的 MSAA/深度缓冲（make patch）"
    assert "function er(){var _r=h.selectedLayerName;" in js, "图层高亮画布未按需创建（make patch）"
    assert "_c.width=0;_c.height=0" in js, "未选中图层时必须把 overlay 画布缩到 0 还缓冲"
    # 守卫必须在 resize/clearRect 之前，否则每帧仍会清一整屏
    guard = js.index("function er(){var _r=h.selectedLayerName;")
    resize = js.index("e.width!==t.width", guard)
    assert guard < resize, "overlay 守卫必须在 resize/clear 之前"
    p = (ROOT / "tools" / "patch.py").read_text()
    assert "关闭无用 MSAA/深度缓冲" in p, "patch.py 未登记 MSAA/深度缓冲补丁"
    assert "图层高亮画布按需创建" in p, "patch.py 未登记 overlay 画布补丁"
