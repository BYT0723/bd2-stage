"""生成壁纸背景（立绘舞台的“景”）。

角色是主体，背景只做低对比的舞台：中间一团暖光把立绘托起来，
四周压暗、右侧留白给属性面板。所有颜色取自 custom/bd2-fav-random.js
的暗金配色，跟悬浮 UI 同源。

三种景：
  a 鎏金舞台 — 暗棕底 + 背后暖光 + 地面余晖，跟暗金 UI 同源
  b 深空夜穹 — 深靛星空 + 银河带，正好接住页面自带的星尘粒子
  c 素纸     — 干净暖白纸底，适合浅色立绘或白天用

背景是 object-cover 且可拖动，超宽屏会裁掉上下约 17%，
所以画面内容都压在中间，不画边框线。

用法: make bg
      python3 tools/gen_background.py [--size 2560x1440] [--only a|b|c]
输出: backgrounds/*.jpg
"""
import argparse
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "backgrounds"

# ---------------------------------------------------------------- 基础工具

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def grid(h, w):
    y, x = np.mgrid[0:h, 0:w]
    return x.astype(np.float32) / w, y.astype(np.float32) / h


def radial(h, w, cx, cy, rx, ry, power=2.0):
    """归一化椭圆衰减，1 在中心，0 在边缘外。"""
    x, y = grid(h, w)
    d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    return np.clip(1.0 - d, 0.0, 1.0) ** power


def vertical(stops, h, w):
    xs = np.array([s[0] for s in stops], dtype=np.float32)
    cols = np.array([s[1] for s in stops], dtype=np.float32) / 255.0
    t = np.linspace(0, 1, h, dtype=np.float32)
    img = np.empty((h, 3), dtype=np.float32)
    for c in range(3):
        img[:, c] = np.interp(t, xs, cols[:, c])
    return np.repeat(img[:, None, :], w, axis=1)


def over(base, layer, alpha):
    a = np.asarray(alpha, dtype=np.float32)
    if a.ndim == 2:
        a = a[:, :, None]
    return base * (1.0 - a) + layer * a


def blur_noise(h, w, rng, scale_px):
    """低频随机场，用来做“手绘”明暗不均，抵消纯渐变的塑料感。"""
    small_h, small_w = max(2, int(h / scale_px)), max(2, int(w / scale_px))
    n = rng.normal(0.0, 1.0, (small_h, small_w)).astype(np.float32)
    im = Image.fromarray(((n - n.min()) / max(1e-6, np.ptp(n)) * 255).astype(np.uint8))
    im = im.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale_px * 0.35))
    a = np.asarray(im, np.float32) / 255.0
    return a - a.mean()


def painterly(h, w, rng, amount=0.07):
    f = (blur_noise(h, w, rng, 220) * 0.6 + blur_noise(h, w, rng, 90) * 0.3
         + blur_noise(h, w, rng, 34) * 0.14)
    return 1.0 + amount * f


def canvas_texture(h, w, rng, amount=0.06):
    """纸/布纹：横向拉长的细噪声，比纯高斯颗粒更像画布。"""
    small = rng.normal(0.0, 1.0, (max(2, h // 6), max(2, w // 2))).astype(np.float32)
    im = Image.fromarray(((small - small.min()) / max(1e-6, np.ptp(small)) * 255)
                         .astype(np.uint8)).resize((w, h), Image.BICUBIC)
    a = np.asarray(im, np.float32) / 255.0
    a -= a.mean()
    return 1.0 + amount * a


def dust(w, h, rng, count, tint, keep):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.gamma(1.5, 1.1) + 0.5
        a = int(20 + 120 * rng.random() ** 2.6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=a)
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    a = np.asarray(im, np.float32)[:, :, None] / 255.0 * keep
    return np.array(tint, np.float32) * a


def stars(w, h, rng, count, y_band=None):
    """星点：幂律亮度，少数几颗带光晕。"""
    layer = np.zeros((h, w, 3), np.float32)
    for _ in range(count):
        if y_band is None:
            x, y = rng.uniform(0, w), rng.uniform(0, h)
        else:
            x = rng.uniform(0, w)
            y = rng.normal(y_band * h, h * 0.10)
            if not 0 <= y < h:
                continue
        mag = rng.random() ** 3.4
        size = 0.55 + 1.45 * mag
        bright = 0.12 + 1.05 * mag
        warm = rng.random()
        col = np.array([1.0, 0.94 - 0.10 * warm, 0.86 + 0.12 * warm], np.float32)
        r = int(np.ceil(size * 2.2)) + 1
        xi, yi = int(x), int(y)
        x0, x1 = max(0, xi - r), min(w, xi + r + 1)
        y0, y1 = max(0, yi - r), min(h, yi + r + 1)
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        g = np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (2.0 * size ** 2)))[:, :, None]
        layer[y0:y1, x0:x1] += g * col * bright
    return layer


# ---------------------------------------------------------------- 三种景

def scene_gilded(w, h, rng):
    """A · 鎏金舞台：暗棕底 + 人物背后一团暖光 + 落在地面的余晖。"""
    img = vertical([(0.00, (15, 11, 8)), (0.24, (26, 20, 14)),
                    (0.56, (36, 28, 19)), (0.80, (23, 17, 12)),
                    (1.00, (10, 8, 6))], h, w)
    x, y = grid(h, w)

    # 主光：人物背后，偏上，光心不在画面正中，画面才不像一次性渐变
    img = over(img, np.array([255, 219, 168], np.float32) / 255,
               radial(h, w, 0.462, 0.470, 0.28, 0.30, 2.0) * 0.42)
    img = over(img, np.array([214, 176, 132], np.float32) / 255,
               radial(h, w, 0.462, 0.470, 0.58, 0.56, 1.5) * 0.13)
    # 补光：右侧一点点冷紫，跟暖光对冲出层次
    img = over(img, np.array([124, 112, 146], np.float32) / 255,
               radial(h, w, 0.80, 0.20, 0.34, 0.34, 1.8) * 0.13)
    # 两道很宽的光柱，只是让画面下层“有空气”
    for cx, spread, a in ((0.42, 0.10, 0.10), (0.55, 0.16, 0.07)):
        sigma = spread + 0.30 * smoothstep(0.0, 0.8, y)
        img = over(img, np.array([236, 206, 166], np.float32) / 255,
                   np.exp(-(((x - cx) / sigma) ** 2) * 2.0)
                   * (1.0 - smoothstep(0.40, 1.0, y)) * a)

    # 地面：压低地平线以下，再在脚下抹一小块暖光，给立绘一个落脚点
    img *= (1.0 - 0.20 * smoothstep(0.74, 0.84, y))[:, :, None]
    img = over(img, np.array([252, 222, 176], np.float32) / 255,
               radial(h, w, 0.462, 0.925, 0.34, 0.105, 2.0) * 0.26)
    img *= (1.0 - 0.26 * smoothstep(0.88, 1.0, y))[:, :, None]
    return img


def scene_stars(w, h, rng):
    """B · 深空夜穹：深靛底 + 星云 + 星点，接住页面自带的星尘。"""
    img = vertical([(0.00, (7, 9, 20)), (0.34, (13, 16, 34)),
                    (0.66, (17, 19, 36)), (0.88, (12, 12, 24)),
                    (1.00, (6, 6, 13))], h, w)

    # 星云：几团大范围的低饱和冷色，越糊越好
    for cx, cy, r, col, a in ((0.30, 0.34, 0.42, (86, 78, 150), 0.20),
                              (0.68, 0.22, 0.34, (44, 96, 120), 0.16),
                              (0.52, 0.72, 0.46, (104, 74, 96), 0.13),
                              (0.14, 0.80, 0.30, (36, 54, 96), 0.14)):
        img = over(img, np.array(col, np.float32) / 255,
                   radial(h, w, cx, cy, r, r * 0.82, 1.6) * a)

    # 银河带：斜着一条，星星密度顺着它变化
    x, y = grid(h, w)
    band = np.exp(-(((x * 0.55 + y * 0.83) - 0.46) / 0.115) ** 2)
    img = over(img, np.array([130, 132, 186], np.float32) / 255, band * 0.07)
    img *= canvas_texture(h, w, rng, 0.10)[:, :, None]

    st = stars(w, h, rng, int(w * h / 2100)) + stars(w, h, rng, int(w * h / 11000), 0.28) * 1.5
    img += st * (0.35 + 0.65 * band)[:, :, None]

    # 地平线：很淡的一道暖边，给人物一个落脚处
    img = over(img, np.array([160, 140, 120], np.float32) / 255,
               radial(h, w, 0.47, 0.905, 0.40, 0.060, 2.0) * 0.16)
    return img


def scene_parchment(w, h, rng):
    """C · 素纸：干净暖白纸底，浅色立绘和白天用；只留纸纹，不做旧。"""
    img = vertical([(0.00, (243, 237, 226)), (0.42, (238, 231, 219)),
                    (0.78, (233, 225, 211)), (1.00, (226, 217, 202))], h, w)

    # 极淡的冷暖差，纸才不会像纯色块
    for _ in range(4):
        cx, cy = rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9)
        r = rng.uniform(0.30, 0.55)
        tint = (np.array([236, 226, 208], np.float32) if rng.random() < 0.6
                else np.array([248, 243, 232], np.float32)) / 255
        img = over(img, tint, radial(h, w, cx, cy, r, r * 0.85, 1.8) * 0.16)

    img = over(img, np.array([252, 248, 240], np.float32) / 255,
               radial(h, w, 0.47, 0.46, 0.42, 0.44, 2.0) * 0.30)
    img *= canvas_texture(h, w, rng, 0.10)[:, :, None]
    return img


SCENES = {
    "a": dict(name="gilded-stage", fn=scene_gilded,
              grain=0.006, vig=0.34, scrim=0.26, dust=(1.00, 0.87, 0.64)),
    "b": dict(name="starlit-vault", fn=scene_stars,
              grain=0.004, vig=0.30, scrim=0.26, dust=(0.80, 0.84, 1.00)),
    "c": dict(name="parchment", fn=scene_parchment,
              grain=0.012, vig=0.18, scrim=0.04, dust=(0.62, 0.52, 0.36),
              dust_scale=0.25),
}


# ---------------------------------------------------------------- 后期

def grade(img, w, h, rng, grain, vig, scrim):
    x, y = grid(h, w)
    img *= painterly(h, w, rng, 0.055)[:, :, None]
    r = np.sqrt(((x - 0.5) * 1.02) ** 2 + ((y - 0.5) * 1.06) ** 2) / 0.70
    img *= (1.0 - vig * np.clip(r, 0, 1) ** 2.3)[:, :, None]
    img *= (1.0 - scrim * smoothstep(0.66, 1.0, x))[:, :, None]   # 右侧留给面板
    img += rng.normal(0.0, grain, (h, w, 1)).astype(np.float32)
    img = np.clip(img, 0.0, 1.0)
    return img * img * (3.0 - 2.0 * img) * 0.30 + img * 0.70


def compose(img, w, h, rng, key, cfg):
    keep = (radial(h, w, 0.47, 0.46, 0.55, 0.55, 1.2)[:, :, None]
            if key != "c" else np.ones((h, w, 1), np.float32) * 0.45)
    img += dust(w, h, rng, int(w * h / 13000), cfg["dust"], keep) * cfg.get("dust_scale", 1.0)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="2560x1440")
    ap.add_argument("--only", default="abc")
    ap.add_argument("--quality", type=int, default=93)
    args = ap.parse_args()
    w, h = (int(v) for v in args.size.lower().split("x"))
    OUT.mkdir(exist_ok=True)

    for key in args.only:
        if key not in SCENES:
            raise SystemExit(f"unknown scene {key!r}")
        cfg = SCENES[key]
        rng = np.random.default_rng(2000 + ord(key))
        img = cfg["fn"](w, h, rng)
        img = grade(img, w, h, rng, cfg["grain"], cfg["vig"], cfg["scrim"])
        img = compose(img, w, h, rng, key, cfg)
        path = OUT / f"bd2-{cfg['name']}-{w}x{h}.jpg"
        Image.fromarray((np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)).save(
            path, quality=args.quality, subsampling=1, optimize=True)
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
