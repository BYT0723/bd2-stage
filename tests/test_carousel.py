"""换人转盘动画：静态契约测试（真实动效靠浏览器手动验收）。"""
import hashlib, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CUSTOM = ROOT / "custom"
ASSETS = ROOT / "assets"


def test_script_contract():
    s = (CUSTOM / "bd2-carousel.js").read_text()
    for key in ["__bd2CarouselSwap", "__bd2CarouselEnter", "window.__bd2Carousel", "use strict"]:
        assert key in s, f"缺 {key}"
    assert "drawImage" in s, "旧人物必须同步拷贝 canvas（定格快照）"
    assert "spine-player-canvas" in s, "必须定位真实 spine canvas"
    assert "requestAnimationFrame" in s, "入场必须等新骨架渲染后再动"
    assert "prefers-reduced-motion" in s, "必须尊重系统减少动效"
    assert "clearTimeout" in s and "setTimeout" in s, "加载失败必须有兜底显示"
    assert "Math.random" in s and "dir" in s, "方向必须每次随机"
    assert "rotateY" in s and "perspective(" in s, "转盘必须是 3D 旋转"
    assert ".remove()" in s or "removeChild" in s, "动画结束必须清理快照"
    assert "fetch(" not in s, "外挂不得联网"
    assert "http://" not in s and "https://" not in s, "外挂不得有远程请求"


def test_bundle_hooks_present():
    js = (ASSETS / "index-Dsqno3tX.js").read_text()
    assert "window.__bd2CarouselSwap" in js, "换人 watcher 未挂钩子（make patch）"
    assert "window.__bd2CarouselEnter" in js, "Spine success 未挂钩子（make patch）"
    assert "try{window.__bd2CarouselSwap&&window.__bd2CarouselSwap()}catch" in js, \
        "swap 钩子必须容错，不能拖垮换人"
    assert "try{window.__bd2CarouselEnter&&window.__bd2CarouselEnter()}catch" in js, \
        "enter 钩子必须容错"


def test_patch_points_declared():
    p = (ROOT / "tools" / "patch.py").read_text()
    assert "window.__bd2CarouselSwap" in p and "window.__bd2CarouselEnter" in p, \
        "patch.py 必须登记两个转盘钩子"
    assert "转盘" in p or "carousel" in p.lower(), "补丁缺少转盘说明"


def test_index_and_stamp():
    html = (ROOT / "templates" / "index.html").read_text()
    assert "bd2-carousel.js?v=DEV" in html, "模板必须挂载转盘脚本"
    st = (ROOT / "tools" / "stamp.py").read_text()
    assert '"bd2-carousel.js"' in st, "stamp 必须把转盘脚本装进 assets"
    live = (ROOT / "index.html").read_text()
    m = re.search(r"bd2-carousel\.js\?v=([0-9a-f]{10})", live)
    assert m, "线上 index.html 缺转盘脚本版本号"
    h = hashlib.sha256((ASSETS / "bd2-carousel.js").read_bytes()).hexdigest()[:10]
    assert m.group(1) == h, "转盘脚本版本号与内容不一致"


def test_verify_gate():
    v = (ROOT / "tools" / "verify.py").read_text()
    assert "window.__bd2CarouselSwap" in v and "bd2-carousel.js" in v, \
        "verify.py 必须校验转盘钩子与脚本版本"
