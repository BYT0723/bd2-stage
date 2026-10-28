"""生成黑底聚光灯前景层（screen 混合用）。

黑底在 mix-blend-mode:screen 下等价透明，光锥/尘埃直接加到人物和背景上。
复用 tools/gen_background.py 的 grid/radial/smoothstep/over/dust。

几条硬约束（screen 层的物理限制）：
  - screen 只能加亮，画不出阴影，所以这里不做接触阴影（那要烤进背景）；
  - 光束只在中下段成形（BEAM_TOP 以下）：头肩几乎不吃光，脸和头发永远干净；
  - 头肩挖椭圆洞（HEAD_KEEP），避免“整个人蒙雾 / 白裙过曝”；
  - 光束要有消失点、上窄下宽、底端收进地面光池，否则像贴在画面上的纸带。
注意：parchment 这类浅色底不要挂这层，会整体发灰。

用法:
  python3 tools/gen_light_overlay.py --only warm
  python3 tools/gen_light_overlay.py --size 2560x1440 --only warm,frost,fest
输出:
  backgrounds/bd2-light-<style>-<WxH>.jpg
"""

import argparse
import pathlib
import sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_background as gb  # noqa: E402

OUT = ROOT / "backgrounds"

STYLES = ("warm", "frost", "fest")

# 上半身保护区（头+肩+胸）：这里几乎不吃光，脸和头发永远干净
HEAD = dict(cx=0.470, cy=0.330, rx=0.150, ry=0.230)
HEAD_KEEP = 0.15
# 腰部以下放开，光束只在中下段成形（y > BEAM_TOP 才可见）
BEAM_TOP = 0.34


def head_mask(h, w):
    """1 = 头肩胸，0 = 其余，边缘平滑过渡。"""
    x, y = gb.grid(h, w)
    d = np.sqrt(
        ((x - HEAD["cx"]) / HEAD["rx"]) ** 2 + ((y - HEAD["cy"]) / HEAD["ry"]) ** 2
    )
    return 1.0 - gb.smoothstep(0.62, 1.10, d)


def cone(x, y, vp_x, vp_y, cx_bot, w_top, w_bot, top=BEAM_TOP, bot_fade=(0.90, 1.02)):
    """带消失点的锥形光：从 BEAM_TOP 起渐显，往下张开；底端收进光池不断开。"""
    t = np.clip((y - vp_y) / (1.0 - vp_y), 0.0, 1.0)
    cx = vp_x + (cx_bot - vp_x) * t
    sigma = w_top + (w_bot - w_top) * t
    m = np.exp(-(((x - cx) / np.maximum(sigma, 1e-3)) ** 2) * 2.0)
    m *= gb.smoothstep(top, top + 0.22, y)  # 上半身不给光
    m *= 1.0 - gb.smoothstep(bot_fade[0], bot_fade[1], y)
    return m


def add(img, mask, color, alpha=1.0):
    col = np.array(color, np.float32) / 255.0
    img += col[None, None, :] * (mask * alpha)[:, :, None]
    return img


def _warm_family(img, x, y, h, w, core, haze):
    img = add(img, gb.radial(h, w, 0.470, 0.760, 0.30, 0.26, 2.0), core, 0.26)
    img = add(img, cone(x, y, 0.47, -0.42, 0.47, 0.022, 0.150), core, 0.46)
    img = add(img, cone(x, y, 0.47, -0.42, 0.47, 0.070, 0.300), haze, 0.15)
    return img


def light_warm(w, h, rng):
    img = np.zeros((h, w, 3), np.float32)
    x, y = gb.grid(h, w)
    head = head_mask(h, w)
    img = _warm_family(img, x, y, h, w, core=(255, 224, 178), haze=(236, 206, 166))
    img = add(
        img, gb.radial(h, w, 0.47, 0.945, 0.30, 0.080, 2.0), (252, 222, 176), 0.32
    )
    img = add(
        img, gb.radial(h, w, 0.47, 0.915, 0.11, 0.040, 2.0), (255, 236, 205), 0.20
    )
    return _attenuate(img, head, y), x, y


def light_frost(w, h, rng):
    img = np.zeros((h, w, 3), np.float32)
    x, y = gb.grid(h, w)
    head = head_mask(h, w)
    core, haze = (198, 220, 255), (140, 170, 220)
    img = add(img, gb.radial(h, w, 0.470, 0.760, 0.30, 0.26, 2.0), core, 0.24)
    img = add(img, cone(x, y, 0.47, -0.42, 0.47, 0.022, 0.150), core, 0.44)
    img = add(img, cone(x, y, 0.47, -0.42, 0.47, 0.070, 0.300), haze, 0.15)
    img = add(
        img, gb.radial(h, w, 0.47, 0.945, 0.30, 0.080, 2.0), (170, 200, 240), 0.30
    )
    img = add(
        img, gb.radial(h, w, 0.47, 0.915, 0.11, 0.040, 2.0), (214, 232, 255), 0.19
    )
    return _attenuate(img, head, y), x, y


def light_fest(w, h, rng):
    img = np.zeros((h, w, 3), np.float32)
    x, y = gb.grid(h, w)
    head = head_mask(h, w)
    core, haze = (255, 224, 178), (236, 206, 166)
    img = add(img, gb.radial(h, w, 0.470, 0.760, 0.28, 0.25, 2.0), core, 0.24)
    img = add(img, cone(x, y, 0.47, -0.42, 0.47, 0.020, 0.145), core, 0.46)
    img = add(img, cone(x, y, 0.47, -0.42, 0.47, 0.062, 0.290), haze, 0.14)
    # 侧束对齐背景已有光束（0.30 / 0.64），只在中下段成形，右侧收进面板前
    img = add(img, cone(x, y, 0.30, -0.42, 0.285, 0.016, 0.090), (176, 198, 240), 0.30)
    img = add(img, cone(x, y, 0.64, -0.42, 0.610, 0.016, 0.090), (188, 188, 236), 0.26)
    img = add(
        img, gb.radial(h, w, 0.47, 0.945, 0.24, 0.075, 2.0), (252, 222, 176), 0.30
    )
    img = add(
        img, gb.radial(h, w, 0.47, 0.915, 0.10, 0.038, 2.0), (255, 236, 205), 0.19
    )
    img = add(
        img, gb.radial(h, w, 0.300, 0.948, 0.14, 0.060, 2.0), (176, 198, 240), 0.20
    )
    img = add(
        img, gb.radial(h, w, 0.628, 0.948, 0.14, 0.060, 2.0), (188, 188, 236), 0.17
    )
    return _attenuate(img, head, y), x, y


def _attenuate(img, head, y):
    """头肩保护：这一块只留 HEAD_KEEP，脸和头发永远干净；底部轻收。"""
    keep = 1.0 - (1.0 - HEAD_KEEP) * head
    keep *= 1.0 - 0.12 * gb.smoothstep(0.95, 1.0, y)
    return img * keep[:, :, None]


FNS = {"warm": light_warm, "frost": light_frost, "fest": light_fest}
DUST_TINT = {
    "warm": (1.00, 0.87, 0.64),
    "frost": (0.75, 0.82, 1.00),
    "fest": (1.00, 0.87, 0.64),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="2560x1440")
    ap.add_argument("--only", default="warm,frost,fest")
    ap.add_argument("--quality", type=int, default=93)
    args = ap.parse_args()
    w, h = (int(v) for v in args.size.lower().split("x"))
    OUT.mkdir(exist_ok=True)
    for style in [s.strip() for s in args.only.split(",") if s.strip()]:
        if style not in FNS:
            raise SystemExit(f"unknown style {style!r}")
        rng = np.random.default_rng(3000 + STYLES.index(style))
        img, x, y = FNS[style](w, h, rng)
        # 尘埃：头肩区再减七成，别把脸糊住；整体仍是中心多、边缘少
        keep = gb.radial(h, w, 0.47, 0.50, 0.55, 0.55, 1.2)[:, :, None]
        keep = keep * (1.0 - 0.7 * head_mask(h, w))[:, :, None]
        img += gb.dust(w, h, rng, int(w * h / 13000), DUST_TINT[style], keep)
        img = np.clip(img, 0.0, 1.0)
        path = OUT / f"bd2-light-{style}-{w}x{h}.jpg"
        Image.fromarray((img * 255.0 + 0.5).astype(np.uint8)).save(
            path, quality=args.quality, subsampling=1, optimize=True
        )
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
