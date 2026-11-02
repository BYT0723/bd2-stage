# Implementation Plan: 阴影大小滑块 (shadow-size)

## Overview

在 `feat/shadow-size` 内为接地影加 `shadowScale`（0-200，默认100）等比缩放。
`bd2Shadow()` 宽高乘 `sc=shadowScale/100`，mask 洞复用同一 `bw/bh` 自动同步。
垂直切片单任务即可，无并行。

## Architecture Decisions

- 单滑块等比，不拆宽高（避免属性膨胀，与 SPEC-ground-shadow 一致）。
- tb 映射走 `!1`（原值），与 `shadowOffsetX/Y` 同款；`foregroundOpacity` 的 `!0` 不适用。
- store 默认 `shadowScale:100`；`bd2Shadow` 内 `Number.isFinite` 兜底 100，钳制 0-2。
- watcher 在现有 `Oi(()=>[h.roleScale,...])` 数组追加 `h.shadowScale`，与位移同入口实时生效。
- 测试先 RED 后 GREEN（TDD）。

## Task List

### Phase 1: 接线（TDD RED）

- [ ] Task 1: `tests/test_full.py` 新增断言（props + tb + watcher + 几何读取）→ 跑出 RED
- [ ] Task 2: `project.json` + `tools/patch.py` 实现 → GREEN

### Checkpoint: 接线

- [ ] `python3 tools/test.py` 通过
- [ ] `python3 tools/patch.py` 两次运行字节一致
- [ ] `python3 tools/verify.py`（含 `node --check`）通过

### Phase 2: 回归

- [ ] Task 3: `SPEC-ground-shadow.md` 几何章节追加系数 + `python3 tools/smoke.py` + 目检说明

### Checkpoint: 完成

- [ ] `make check` 通过，`git diff --stat` 无无关改动

Tasks tracked in `tasks/todo-shadow-size.md`.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| bundle 指纹漂移导致 patch FAIL | Med | old 取当前精确字节；normalize 幂等；`new not in js` 才 FAIL |
| 默认值不一致导致旧版视觉偏移 | Med | 默认 100 → `sc=1`，几何与旧版逐字节等价；测试断言默认值 100 |
| mask 洞与影子不同步出双轮廓 | Low | 洞继续用同一 `bw/bh` 变量，不引入第二套尺寸 |

## Open Questions

无（Spec 已批准）。
