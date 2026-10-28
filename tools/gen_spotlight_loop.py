"""生成聚光灯循环视频（1080p30、webm/VP9 默认）。

复用 tools/gen_background.py 的管线与色板，底图只算一次，
逐帧只算轻量调制（呼吸增益 + 光锥摇摆 + 尘埃平移），全整数周期保证无缝。
编码经 ffmpeg stdin，默认 webm/VP9 直接产出到 backgrounds/（约 100~140KB），
--format mp4 走 H.264 供兼容性预览。

用法示例:
  python3 tools/gen_spotlight_loop.py --seconds 12 --fps 30 --size 1920x1080 \\
      --style warm --out backgrounds/bd2-spotlight-loop-warm-1080p30.webm
"""
import argparse
import pathlib
import subprocess
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gen_background as gb  # noqa: E402


STYLES = ("warm", "frost", "fest")


def base_vertical(style, h, w):
    if style == "frost":
        stops = [(0.00, (7, 10, 18)), (0.24, (13, 19, 35)),
                 (0.56, (17, 23, 39)), (0.80, (12, 14, 26)),
                 (1.00, (6, 7, 14))]
    elif style == "fest":
        stops = [(0.00, (11, 9, 8)), (0.24, (22, 18, 15)),
                 (0.56, (30, 24, 20)), (0.80, (19, 15, 13)),
                 (1.00, (8, 7, 6))]
    else:
        stops = [(0.00, (12, 9, 7)), (0.24, (24, 18, 13)),
                 (0.56, (34, 26, 18)), (0.80, (21, 16, 11)),
                 (1.00, (9, 7, 5))]
    return gb.vertical(stops, h, w)


def cone_mask(x, y, cx_top, cx_bot, w_top, w_bot):
    cx = cx_top + (cx_bot - cx_top) * y
    sigma = np.maximum(w_top + (w_bot - w_top) * y, 1e-3)
    m = np.exp(-(((x - cx) / sigma) ** 2) * 2.0)
    return m * (1.0 - gb.smoothstep(0.86, 1.0, y))


def render_frame(base, x, y, h, w, style, phase, dust_layers):
    """phase in [0,1). 全部调制均为整数周期正弦，phase=1 与 0 完全重合。"""
    breath = 1.0 + 0.030 * np.sin(2.0 * np.pi * 3 * phase)
    sway_c = 0.008 * np.sin(2.0 * np.pi * 2 * phase)
    sway_s = 0.006 * np.sin(2.0 * np.pi * 2 * phase + np.pi)
    img = base.copy()

    if style == "frost":
        glow_col, core_col, haze_col, pool_col = (
            (170, 200, 255), (198, 220, 255), (140, 170, 220), (170, 200, 240))
        fill = gb.radial(h, w, 0.78, 0.22, 0.34, 0.34, 1.8) * 0.12
        img = gb.over(img, np.array([70, 110, 130], np.float32) / 255, fill)
        img = gb.over(img, np.array(glow_col, np.float32) / 255,
                      gb.radial(h, w, 0.47 + sway_c, 0.45, 0.26, 0.28, 2.0)
                      * 0.38 * breath)
        img = gb.over(img, np.array(core_col, np.float32) / 255,
                      cone_mask(x, y, 0.47 + sway_c, 0.47 + sway_c, 0.028, 0.13)
                      * 0.55 * breath)
        img = gb.over(img, np.array(haze_col, np.float32) / 255,
                      cone_mask(x, y, 0.47 + sway_c, 0.47 + sway_c, 0.075, 0.27)
                      * 0.20 * breath)
    elif style == "fest":
        img = gb.over(img, np.array([255, 219, 168], np.float32) / 255,
                      gb.radial(h, w, 0.47 + sway_c, 0.45, 0.24, 0.26, 2.0)
                      * 0.38 * breath)
        img = gb.over(img, np.array([150, 175, 230], np.float32) / 255,
                      gb.radial(h, w, 0.36, 0.48, 0.20, 0.22, 2.0) * 0.16)
        img = gb.over(img, np.array([165, 165, 220], np.float32) / 255,
                      gb.radial(h, w, 0.58, 0.48, 0.20, 0.22, 2.0) * 0.16)
        img = gb.over(img, np.array([255, 224, 178], np.float32) / 255,
                      cone_mask(x, y, 0.47 + sway_c, 0.47 + sway_c, 0.026, 0.12)
                      * 0.55 * breath)
        img = gb.over(img, np.array([236, 206, 166], np.float32) / 255,
                      cone_mask(x, y, 0.47 + sway_c, 0.47 + sway_c, 0.070, 0.25)
                      * 0.18 * breath)
        img = gb.over(img, np.array([170, 200, 255], np.float32) / 255,
                      cone_mask(x, y, 0.30 + sway_s, 0.38 + sway_s, 0.020, 0.085)
                      * 0.38 * breath)
        img = gb.over(img, np.array([180, 180, 235], np.float32) / 255,
                      cone_mask(x, y, 0.64 - sway_s, 0.56 - sway_s, 0.020, 0.085)
                      * 0.34 * breath)
    else:
        img = gb.over(img, np.array([124, 112, 146], np.float32) / 255,
                      gb.radial(h, w, 0.80, 0.20, 0.34, 0.34, 1.8) * 0.12)
        img = gb.over(img, np.array([255, 219, 168], np.float32) / 255,
                      gb.radial(h, w, 0.47 + sway_c, 0.45, 0.26, 0.28, 2.0)
                      * 0.40 * breath)
        img = gb.over(img, np.array([255, 224, 178], np.float32) / 255,
                      cone_mask(x, y, 0.47 + sway_c, 0.47 + sway_c, 0.028, 0.13)
                      * 0.55 * breath)
        img = gb.over(img, np.array([236, 206, 166], np.float32) / 255,
                      cone_mask(x, y, 0.47 + sway_c, 0.47 + sway_c, 0.075, 0.27)
                      * 0.20 * breath)

    # 地面压暗 + 光池（光池随呼吸轻微起伏）
    img *= (1.0 - 0.20 * gb.smoothstep(0.74, 0.84, y))[:, :, None]
    if style == "frost":
        img = gb.over(img, np.array(pool_col, np.float32) / 255,
                      gb.radial(h, w, 0.47, 0.925, 0.32, 0.10, 2.0)
                      * 0.28 * (0.94 + 0.06 * breath))
    elif style == "fest":
        img = gb.over(img, np.array([252, 222, 176], np.float32) / 255,
                      gb.radial(h, w, 0.47, 0.925, 0.26, 0.09, 2.0)
                      * 0.28 * (0.94 + 0.06 * breath))
        img = gb.over(img, np.array([170, 200, 240], np.float32) / 255,
                      gb.radial(h, w, 0.375, 0.925, 0.15, 0.07, 2.0) * 0.20)
        img = gb.over(img, np.array([180, 180, 235], np.float32) / 255,
                      gb.radial(h, w, 0.565, 0.925, 0.15, 0.07, 2.0) * 0.18)
    else:
        img = gb.over(img, np.array([252, 222, 176], np.float32) / 255,
                      gb.radial(h, w, 0.47, 0.925, 0.32, 0.10, 2.0)
                      * 0.28 * (0.94 + 0.06 * breath))
    img *= (1.0 - 0.26 * gb.smoothstep(0.88, 1.0, y))[:, :, None]

    # 尘埃：两层整周回绕平移（正弦位移，首尾归零）
    for layer, amp_px, cyc, ph in dust_layers:
        dx = int(round(amp_px[0] * np.sin(2.0 * np.pi * cyc * phase + ph)))
        dy = int(round(amp_px[1] * np.sin(2.0 * np.pi * cyc * phase + ph * 1.7)))
        if dx or dy:
            layer_s = np.roll(layer, (dy, dx), axis=(0, 1))
        else:
            layer_s = layer
        img += layer_s * (0.85 + 0.15 * breath)
    return np.clip(img, 0.0, 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=12)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--style", default="warm", choices=STYLES)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", default="webm", choices=("webm", "mp4"),
                    help="webm=VP9（体积小，网页用）; mp4=H.264（兼容用）")
    ap.add_argument("--crf", type=int, default=None,
                    help="默认 webm=30 mp4=20")
    ap.add_argument("--preset", default="medium",
                    help="仅 mp4 有效（x264 preset）")
    ap.add_argument("--check-loop", action="store_true",
                    help="打印首尾帧 MSE 与最大相邻帧差")
    args = ap.parse_args()
    w, h = (int(v) for v in args.size.lower().split("x"))
    n = max(2, int(round(args.seconds * args.fps)))
    rng = np.random.default_rng(2000 + ord({"warm": "d", "frost": "e", "fest": "f"}[args.style]))

    x, y = gb.grid(h, w)
    base = base_vertical(args.style, h, w)

    # 静态后期乘子（暗角 + 右 scrim）只算一次
    r = np.sqrt(((x - 0.5) * 1.02) ** 2 + ((y - 0.5) * 1.06) ** 2) / 0.70
    vig = {"warm": 0.36, "frost": 0.34, "fest": 0.36}[args.style]
    post = ((1.0 - vig * np.clip(r, 0, 1) ** 2.3)
            * (1.0 - 0.26 * gb.smoothstep(0.66, 1.0, x))).astype(np.float32)

    tint = {"warm": (1.00, 0.87, 0.64), "frost": (0.75, 0.82, 1.00),
            "fest": (1.00, 0.87, 0.64)}[args.style]
    keep = gb.radial(h, w, 0.47, 0.46, 0.55, 0.55, 1.2)[:, :, None]
    dust_full = gb.dust(w, h, rng, int(w * h / 13000), tint, keep)
    dust1 = (dust_full * 0.7).astype(np.float32)
    dust2 = np.flip(dust_full, axis=1).astype(np.float32) * 0.5
    dust_layers = [(dust1, (min(14, w // 90), min(8, h // 90)), 2, 0.0),
                   (dust2, (min(9, w // 140), min(12, h // 70)), 3, 1.3)]

    cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-framerate", str(args.fps), "-i", "-"]
    crf = args.crf if args.crf is not None else (30 if args.format == "webm" else 20)
    if args.format == "webm":
        cmd += ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-crf", str(crf),
                "-b:v", "0", "-an", args.out]
    else:
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf),
                "-preset", args.preset, "-movflags", "+faststart", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    first = prev = None
    max_step = 0.0
    for i in range(n):
        img = render_frame(base, x, y, h, w, args.style, i / n, dust_layers)
        img *= post[:, :, None]
        frame = (np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8)
        proc.stdin.write(frame.tobytes())
        f32 = frame.astype(np.float32) / 255.0
        if first is None:
            first = f32
        if prev is not None:
            max_step = max(max_step, float(np.mean((f32 - prev) ** 2)))
        prev = f32
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg failed rc={proc.returncode}")
    if args.check_loop and first is not None and prev is not None:
        loop_mse = float(np.mean((prev - first) ** 2))
        print(f"frames={n} loop_mse(last,first)={loop_mse:.6f} max_step_mse={max_step:.6f}")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
