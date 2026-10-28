# Spec: 透明聚光灯前景层 (light-overlay)

## Objective

把聚光灯从“烤进背景”拆成两层：背景保留暗底+ scrim，后续光锥/尘埃做成黑底前景层，
`mix-blend-mode:screen` 盖在人物和背景之上。氛围更裹人，灯光可在多背景间复用。
用户选择 B 方案（黑底+screen，不用真 alpha）+ 独立前景属性。

## Tech Stack

- Python 3 + numpy + PIL（复用 `tools/gen_background.py` 管线）
- 输出 `backgrounds/bd2-light-{warm,frost,fest}-2560x1440.jpg`（黑底，screen 用）+ 预览图
- 接线：`project.json` 只留 `background` + `foreground`（图片视频都吃，前景默认空=关闭，不分 light/dark）；
  `tools/patch.py` 新增 `bd2Fg` 槽位 + `bd2FgApply` + `bd2Light(host,img,vid)` 前景渲染
  （`z-index:20;pointer-events:none;mix-blend-mode:screen`，挂在 `viewerWrapper` 内，
  位于角色容器 `z-10` 之上、点击层 `z-30` 之下）
- custom 外挂不碰 DOM（禁 `document.`），前景元素只走 bundle 补丁

## Commands

```sh
python3 tools/gen_light_overlay.py --only warm
python3 tools/gen_light_overlay.py --size 2560x1440 --only warm,frost,fest
make check   # check_fav_random + test.py
python3 tools/verify.py
python3 tools/patch.py
```

## Project Structure

```text
tools/gen_light_overlay.py → 新增：黑底前景生成器（warm/frost/fest）
backgrounds/bd2-light-*-2560x1440.jpg + preview-light-*.jpg → 新增前景图
project.json → 新增 foreground/foreground_dark
tools/patch.py → 新增 bd2Fg/bd2Light/bd2FgApply 补丁
tests/test_full.py → 新增前景断言
SPEC-light-overlay.md → 本文件
```

## Code Style

复用 `gen_background.py` 函数式风格：`grid/radial/smoothstep/over/_cone/dust` 直接 import 复用。

```python
def light_warm(w, h, rng):
    img = np.zeros((h, w, 3), np.float32)  # 黑底，screen 下=透明
    img = gb.over(img, WARM, cone_mask(...) * 0.55)
    return img
```

- 黑底，不做暗角/scrim/grain（screen 下黑=透明，加暗角会压暗人物）
- 内容压中央 80%，超宽屏裁切安全

## Testing Strategy

- 生成器可重复跑：`rng = default_rng(3000 + STYLES.index(style))`，与 `--only` 顺序无关，
  两次输出字节一致（`--only fest` 与全量跑出的 fest 必须同 md5）
- 文件检查：JPG×3 存在、2560x1440、单张 < 1MB
- 像素断言：中心亮、四角接近黑（screen 下透明）、全图均值 < 背景版
- 补丁：`node --check` 通过；bundle 含 `bd2Fg`、`bd2Light`、`foreground_dark`
- `make check` + `verify.py` 回归

## Boundaries

- Always: 只加 `tools/gen_light_overlay.py` + 前景 JPG + `project.json` 前景双属性 + `patch.py` 前景补丁 + 测试
- Ask first: 是否把某前景设为默认、是否跟随系统
- Never: 不改 `index.html` 默认背景；不提交 `assets/spines|audios`；不提交 >5MB；
  不在 `main` 上开发；custom 外挂不碰 DOM

## Success Criteria

1. 三张前景 JPG 存在（warm/frost/fest），2560x1440，<1MB，黑底中央亮四角黑；
   头肩区（HEAD）光量≈6%，光束只在 y>0.34 成形，脸不糊、不蒙雾
2. `project.json` 有 `foreground`/`foreground_dark`，`bundle` 含接线且 `node --check` 过
3. 前景层样式含 `mix-blend-mode:screen`、`pointer-events:none`、`z-index:20`
4. `make check` + `verify.py` 通过，无关改动无
5. 目检：人物被光裹住、尘埃在身前、右侧面板可读

## Open Questions

- 前景默认空（关闭），用户在 WE 里手选 —— 已确认
- 视频前景（webm 黑底循环）本次先做图片，视频按需再起 —— 待确认
