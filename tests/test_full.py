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
