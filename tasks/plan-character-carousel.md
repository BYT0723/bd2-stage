# Implementation Plan: 换人转盘动画

## Overview

在 `feat/character-carousel` worktree 内，用“同步快照旧画面 + Web Animations API”
实现换人转盘：旧人物向一侧 3D 转出并淡出，新人物从另一侧转入；方向每次随机。
外挂只在人物层做 transform，不碰背景/灯光/接地影，也不需要双 SpinePlayer。

## Architecture Decisions

- **快照而不是双实例**：bundle 换人时先 `dispose()` 旧 player，旧 canvas 会立刻失效；
  但 config 带了 `preserveDrawingBuffer:!0`，可以在 `dispose()` 前同步
  `drawImage` 到 2D canvas，作为旧人物的定格贴片。成本低、无内存泄漏。
- **两个 bundle 钩子**：
  1. `selectedCharacterId` watcher 最开头（旧 player 还在）→ `__bd2CarouselSwap`
  2. Spine `success` 回调最开头（新骨架已就绪）→ `__bd2CarouselEnter`
  钩子全部 try/catch，外挂异常不能拖垮换人。
- **进场等待两帧**：`success` 里骨架刚建好，等 2 个 rAF 再开始入场，避免第一帧空白。
- **缓动**：出场 `cubic-bezier(.45,0,.55,1)`（420ms），入场 `cubic-bezier(.42,0,.28,1)`
  （560ms）；不用 expo 型 ease-out，避免 0.1 秒就回正、看不出转盘。
- **兜底**：3 秒内没等到 `success` 就强制显示新人物，防止加载失败后隐形。
- **方向策略**：每次 `Math.random() < 0.5 ? -1 : 1`，独立随机（允许连续同向）。
- **降级**：`prefers-reduced-motion` 或没有 WAAPI 时直接跳过，等同旧行为。
- **清理**：连点先 cancel 上一轮动画 + 移除快照；入场结束恢复容器内联样式和 hit layer。

## Task List

### Phase 1: 外挂与钩子（垂直切片）

- [x] Task 1: `custom/bd2-carousel.js`（快照、随机方向、出入场、清理、兜底、reduced-motion）
- [x] Task 2: `tools/patch.py` 两个钩子 + `templates/index.html` + `tools/stamp.py`

### Checkpoint: 可运行

- [x] `node --check custom/bd2-carousel.js` / bundle 通过
- [x] `python3 tools/patch.py` 幂等，`python3 tools/verify.py` 通过

### Phase 2: 校验与文档

- [x] Task 3: `tests/test_carousel.py` + `tools/test.py` 注册 + `verify.py`/`check_fav_random.py` 断言
- [x] Task 4: README + SPEC + 本计划 + todo

### Checkpoint: 完成

- [x] `python3 tools/test.py` 全 PASS
- [x] `python3 tools/verify.py` PASS
- [x] `make smoke` 无新异常
- [x] 手动目检：列表 / 🎲 / ⏱ / URL 四种入口，方向随机、连点正常

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `drawImage` 读不到 WebGL 画面 | 旧人物没有转出，只剩新人入场 | 捕获异常并跳过出场；入场动画仍保留 |
| 在线素材 canvas taint | 无法 `toDataURL` | 不用 dataURL，只 `drawImage` 到 2D canvas 显示 |
| 快速连点 | 残留快照/容器被锁在透明 | 每轮先 `reset()`，cancel + remove；容器样式恢复 |
| 资源加载失败 | 新人物一直透明 | 3 秒兜底 `reveal()` |
| 全屏 3D 变换性能 | 掉帧 | 只转人物层（透明 canvas），0.4~0.5s；无模糊滤镜 |

## Open Questions

无。
