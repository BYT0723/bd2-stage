# Implementation Plan: 聚光灯舞台（三静态 + webm 循环 + WE 接线）

## Overview

在 `feat/spotlight` worktree 内：三张静态背景 d/e/f（已交付 b8ca23f）；视频改走 **webm（VP9）优先**
（同内容约 110~140KB，是 mp4 的 1/5，入库 `backgrounds/`）；`tools/patch.py` 新增视频补丁 +
`project.json` 只有 `background`/`background_dark`（图片视频都吃），bundle 内按扩展名挂 `<video>` 层，
JPG 留作 poster 兜底。2k/4k/60fps 搁置。

## Architecture Decisions

- 静态沿用 `tools/gen_background.py` 现有管线，只新增 `scene_spotlight/frost/fest()` + `SCENES["d"/"e"/"f"]`，seed=`2000+ord(key)` 保证可复现。
- d 暖单束：暗底 + 顶部锥形光（窄芯半角约 9° + 宽雾约 12°）+ 人物背后暖光 + 地面椭圆光池 + 右侧 scrim。
- e 冷单束：同构图，色板换冰蓝（`#BFD9FF` 系底 + 冷白芯），地面光池偏青，满足冷色偏好。
- f 多向舞台束：暖中央主束 + 左右两道冷侧束（对称 ±18° 偏角），地面三个光池，主次分明不抢人物。
- 超宽屏裁切安全，内容压中央 80%。
- 视频性能策略：静态底图算一次；逐帧只算轻量调制（全局呼吸增益 ±3%、光锥中心摇摆 ±1.5%、尘埃层整周回绕平移），全整数周期保证无缝；`--format webm` 走 `libvpx-vp9 -crf 30 -b:v 0`，`--format mp4` 走 `libx264 -crf 20`。
- 接线策略：视频走独立状态位 `customBackgroundVideo`（不复用图片位，避免 `<img>` 误加载 webm 触发 onerror 自清）；
  `bd2Bg {img,dark}` 双槽位 + 统一解析（深色留空跟通用、通用留空跟内置；视频优先于图片；面板手选外来图保持不动）；
  `ib()` 按 `/\.(webm|mp4)(\?.*)?$/i` 分支挂 `<video autoplay muted loop playsinline>`（cover 铺满，
  `pointer-events:none` 保拖拽，加载失败摘掉回落 JPG）；custom 外挂不碰 DOM。
- 验证：静态目检 + 中央/四角亮度断言；视频用 ffprobe（时长/分辨率/fps）+ 首尾帧差断言无缝；
  补丁用 `node --check`（verify.py 已有）+ 标记断言。

## Task List

### Phase 1: 三静态原型
- [ ] Task 1: `scene_spotlight/frost/fest` + SCENES["d"/"e"/"f"]（见 tasks/todo.md Task 1）
- [ ] Task 2: 生成 JPG×3 + 预览 + 亮度断言（Task 2）

### Checkpoint: 静态
- [ ] JPG×3 存在且单张 <1MB，中央亮于四角，右侧 scrim 生效，`make check` 通过

### Phase 2: 视频 webm（仅 1080p30）
- [x] Task 3: `tools/gen_spotlight_loop.py` 生成器 + ffmpeg 编码（c66f748；追加 `--format webm|mp4`，默认 webm）
- [ ] Task 4: webm×3 输出 + 校验（各 ~12s，单个 <200KB，入库 `backgrounds/`），首尾无缝（Task 4）

### Phase 3: WE 视频背景接线
- [ ] Task 5: `project.json`（background×2）+ `tools/patch.py`（统一解析/applier 分支）+ 测试标记（Task 5）

### Checkpoint: 完成
- [ ] 静态×3 + webm×3 + 接线都满足 SPEC Success Criteria，`make check` + `verify.py` 通过，
  `git status` 无无关改动

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 1080p×360 帧渲染耗时 | Med | 底图只算一次 + 逐帧轻量调制；numpy 向量化；先 4s 冒烟；转码 webm 与渲染分离 |
| 视频循环接缝可见 | Med | 全部动画整数周期 + 首尾帧差自动化断言 |
| bundle 字符串补丁指纹漂移 | Med | old 取当前精确字节；`patch.py` 幂等（`new not in js` 才 FAIL）；`verify.py node --check` 拦语法 |
| `<img>` 误吃 webm 触发 onerror 自清 | Med | 视频走独立 `customBackgroundVideo` 状态位，不复用图片位 |
| 三款风格割裂 | Low | 同构图同管线，只换色板/光束数；f 款主次分明 |
| 与现有三张风格割裂 | Low | 取色沿用 gilded 暗金 + 冷紫对冲（d/f），e 单独冰蓝 |

## Open Questions

- 已确认：只深色；d/e/f 三款；视频 webm 优先入库；WE 接线本次做；视频默认空（用户手选）；
  2k/4k/60fps 搁置
