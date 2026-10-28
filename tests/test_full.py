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
    assert "background_dark" in js, "深浅背景属性未接线"
    assert "bd2Bg.ai" in js, "属性变更死锁守卫未注入"
    assert "bd2Apply(1)" in js, "属性下发必须 force（否则被旧手选值拦死）"
    props = json.loads((ROOT / "project.json").read_text())["general"]["properties"]
    for name, p in props.items():
        if p.get("type") == "file" and name.startswith("background"):
            assert name in js, f"背景属性 {name} 在 bundle 里没接线（改名必死）"
    assert "BD2_BG_AUTO" in js, "背景默认值未注入"
    assert "bgImageLight" not in js, "旧图片属性未移除"
    assert "bgVideo" not in js, "旧视频属性未移除（customBackgroundVideo 除外）"
    assert "customBackgroundVideo" in js, "视频背景状态位未注入"
    assert "prefers-color-scheme: dark" in js, "背景必须跟随系统配色"
    assert "bd2Video(" in js, "视频背景 applier 未注入"

def test_audio_patch_fingerprint():
    ref = (ROOT / "tasks" / "bundle-reference.js.txt").read_text()
    assert "t.preload=`auto`" in ref, "原始 bundle 指纹变化，需复核语音补丁点"
    assert "function Vn(){let e=Ln()" in ref, "原始 Vn 指纹变化，需复核语音补丁点"
