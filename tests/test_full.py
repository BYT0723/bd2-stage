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
    assert "h.shadowOffsetX,h.shadowOffsetY" in js, "接地影没跟随位移属性"
    assert "bd2Shadow(),bd2LightOp()})" in js, "接地影/灯光强度没跟上 watcher"
    assert "z-index:5" in js, "接地影必须在背景之上、人物之下（z-index:5）"
    assert "radial-gradient(closest-side,rgba(0,0,0,.75)" in js, "接地影渐变未注入"
    assert "maskImage=m" in js, "灯光层没挖洞，影子会被 screen 洗掉"
    for name in ("shadowOffsetX", "shadowOffsetY"):
        assert name in props and props[name].get("type") == "slider", f"{name} 属性缺失"
        assert name in js, f"{name} 在 bundle 里没接线"

def test_audio_patch_fingerprint():
    ref = (ROOT / "tasks" / "bundle-reference.js.txt").read_text()
    assert "t.preload=`auto`" in ref, "原始 bundle 指纹变化，需复核语音补丁点"
    assert "function Vn(){let e=Ln()" in ref, "原始 Vn 指纹变化，需复核语音补丁点"
