# Spec: 聚光灯舞台背景原型 (spotlight-stage)

## Objective

给 bd2-stage 加聚光灯舞台系列静态原型 + 1080p 循环视频原型。
静态三款：d 暖金单束（主推，同暗金 UI）、e 冷色单束、f 多向舞台束（暖金中央 + 两侧冷束）。
视频先只做 1080p 30fps（2k/4k/60fps 搁置）。

用户故事：作为壁纸用户，我想要“人物在舞台中央、头顶聚光灯”的深色背景，
立绘被托起来，边缘不抢戏，右侧属性面板依然可读；动态版光束有呼吸/尘埃漂浮，可循环播放。

## Tech Stack

- Python 3 + numpy + PIL（沿用现有 `tools/gen_background.py`）
- 输出 JPG 三款：`bd2-spotlight-stage`（d 暖单束 2560x1440 主力）、`bd2-spotlight-frost`（e 冷单束）、`bd2-spotlight-fest`（f 多向舞台束），各 + 小预览图
- 视频：`tools/gen_spotlight_loop.py` 程序化生成 + ffmpeg 编码，**webm（VP9）优先**，
  1080p 30fps、10~12s 整数周期无缝循环（`--style warm|frost|fest --format webm`，`--format mp4` 仍可用）。
  webm 实测 104~138KB（同内容 mp4 约 600KB），直接入库 `backgrounds/`。
  策略：静态底图算一次，逐帧只算轻量调制层（呼吸增益 + 光锥摇摆 + 尘埃位移），再合成编码
- 接线：`project.json` 只有两个背景属性——`background`（通用）/`background_dark`（深色），
  图片视频都吃（按扩展名分支）；`tools/patch.py` 补丁：`customBackgroundVideo` 独立状态位 +
  `bd2Bg {img,dark}` 槽位 + 统一解析（深色留空跟通用、通用留空跟内置；视频优先于图片；
  面板手选外来图保持不动）+ `ib()` 内按扩展名挂 `<video>`（autoplay/muted/loop/playsinline，
  cover 铺满，出错摘掉回落 JPG）；JPG 逻辑不动
- 不碰 bundle 上游语义 / Live2D 前景 / 外挂约束（custom 脚本禁 `document.`，视频 DOM 只走 bundle 补丁）

## Commands

```sh
python3 tools/gen_background.py --only def
python3 tools/gen_spotlight_loop.py --seconds 12 --fps 30 --size 1920x1080 --style warm --format webm --out backgrounds/bd2-spotlight-loop-warm-1080p30.webm
python3 tools/gen_spotlight_loop.py --seconds 12 --fps 30 --size 1920x1080 --style frost --format webm --out backgrounds/bd2-spotlight-loop-frost-1080p30.webm
python3 tools/gen_spotlight_loop.py --seconds 12 --fps 30 --size 1920x1080 --style fest --format webm --out backgrounds/bd2-spotlight-loop-fest-1080p30.webm
make bg   # 全量 + 新增三款（如保留）
python3 tools/check_fav_random.py && python3 tools/test.py  # 回归
python3 tools/verify.py  # 含 node --check bundle 语法
```

## Project Structure

```text
tools/gen_background.py      → 新增 scene_spotlight/frost/fest() + SCENES["d"/"e"/"f"]
tools/gen_spotlight_loop.py  → 新增：程序化循环视频生成器（新文件，--style warm|frost|fest）
backgrounds/                 → 新增 bd2-spotlight-stage/frost/fest-2560x1440.jpg + preview 三张
                               + 1080p30 mp4×3（原型放 /tmp，不入库）
SPEC-spotlight.md            → 本文件
```

## Code Style

沿用现有函数式风格示例：

```python
def scene_spotlight(w, h, rng):
    img = vertical([...], h, w)
    img = over(img, WARM, radial(h, w, 0.47, 0.42, 0.28, 0.30, 2.0) * 0.45)
    return img
```

- 颜色从暗金 UI 取色，不引入新高饱和色
- 光锥用 `smoothstep` + 指数衰减，不硬边；内容压在画面中央 80%，超宽屏裁切安全
- 不画边框线（背景是 `object-cover` 可拖动）

## Testing Strategy

- 生成脚本可重复跑：`--only def` 两次输出字节一致（固定 `rng = default_rng(2000+ord(key))`）
- 文件检查：JPG×3 存在、尺寸 2560x1440、单张 < 1MB、无异常抛错
- 目检：中央亮/四周暗、顶部光锥可见、地面有光池、右侧有 scrim 留白、浅色立绘/深色立绘都不糊
- 视频：ffprobe 确认 1080p/30fps/时长，首尾帧差 < 阈值
- 不跑 `make smoke`（无头 Chromium 与静态图无关），跑 `check + test` 回归即可

## Boundaries

- Always: 只改 `tools/gen_background.py` + 新增图片/视频脚本 + `project.json` 视频属性 + `tools/patch.py` 视频补丁；
  右侧 scrim 保留；seed 固定；视频动画用整数周期保证首尾无缝（呼吸 N 整周期、尘埃位移整周回绕）
- Ask first: 是否把 webm 设为 WE 深色默认、是否接入跟随系统
- Never: 不改 `index.html` 默认背景（原型阶段）；不提交 `assets/spines|audios`；
  不提交 >5MB 文件进 git（webm 单个 ~140KB 可入库）；不在 `main` 上直接开发；
  custom 外挂不碰 DOM（禁 `document.`，视频元素只走 bundle 补丁）

## Success Criteria

1. 三张 JPG 存在（stage/frost/fest），2560x1440，质量 93，单张 < 1MB
2. 中央（0.47,0.45）亮度明显高于四角（目检 + 可选直方图断言）
3. 右侧 x>0.66 有压暗（面板可读），超宽屏裁掉上下 17% 后主体仍完整
4. 循环视频 webm×3（warm/frost/fest，1080p30，10~12s）ffprobe 可读，首尾帧差 < 阈值；
   单个 < 200KB，入库 `backgrounds/`
5. `make check` + `tools/verify.py`（含 `node --check`）通过；bundle 含视频补丁标记；
   WE 属性面板只有 `background`/`background_dark`，选 webm 后 `<video>` 层播放、JPG 兜底
6. `git status` 无无关改动（只有背景文件 + `gen_background.py` + `gen_spotlight_loop.py --format` + `patch.py` + `project.json` + 测试）

## Open Questions（已确认）

1. 深/浅 → 只深色。
2. 光色 → 暖金主光 d（`#FFD9A8` 系 + 冷紫对冲）+ 冷色 e（冰蓝 `#BFD9FF` 系）+ 多向舞台 f（暖中央 + 两侧冷束）。
3. 范围 → webm 优先入库（小文件）；mp4 仅 /tmp 预览保留；WE 接线已做（`<video>` 层 + JPG 兜底）；
   属性合并为 `background`/`background_dark`（旧 6 属性移除，含 bgImage 手动覆盖）；
   2k/4k/60fps 搁置；两者默认都空（跟内置/通用）；旧存档背景选择升级后重置一次。
