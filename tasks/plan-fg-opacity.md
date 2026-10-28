# Implementation Plan: overlay 灯光强度滑块 (foreground-opacity)

## Overview

把前景灯光层写死的 `opacity:.6` 换成 WE 属性滑块驱动（默认 0.45，范围 0-100→0-1）。
走 `volume` 同款 `tb !0` 映射 + store 默认 `.45`，新增 `bd2LightOp()` 做 opacity 的唯一写点，
创建/应用/watcher 三处调用，保证拖滑块实时生效。旧 `tasks/plan.md` 是已完工的历史，
本次用独立文件，不覆盖。

Tasks tracked in `tasks/todo-fg-opacity.md`.

## Architecture Decisions

- 映射选 `!0`（0-100→0-1）而非 `!1` raw：与 `volume`/`bgOpacity`/`panelOpacity` 一致，
  store 里直接是 0-1 的 opacity 值，`bd2LightOp` 无需再除 100。
- store 默认 `.45` + 创建时 cssText 默认 `opacity:.45`：首帧即正确，不依赖属性下发时序。
- `bd2LightOp()` 幂等且防御（NaN 回落 .45，clamp 0-1，不在时直接返回），避免白屏。
- watcher 复用现有 `Oi(...)` 位置位移 watcher，数组追加 `h.foregroundOpacity` 并加调
  `bd2LightOp()`；`bd2Light()` 内每次创建/更新后也调一次，覆盖属性面板外触发的重渲染路径。
- foreground 为空移除层的语义不动；`0` 只是近似不可见，不删除元素（与 screen 层语义一致）。

## Task List

### Phase 1: 测试先行（RED）

- [ ] Task 1: `tests/test_full.py` 新增/更新断言（见 todo-fg-opacity.md Task 1）

### Checkpoint: RED

- [ ] `python3 tools/test.py` 在 `test_bundle_patched` 失败（证明测试有效），其余通过

### Phase 2: 实现（GREEN）

- [ ] Task 2: `project.json` + `tools/patch.py` + 重新打补丁（见 todo-fg-opacity.md Task 2）

### Checkpoint: GREEN

- [ ] `python3 tools/test.py` 全 PASS
- [ ] `python3 tools/verify.py` PASS（含 `node --check`）
- [ ] `make check` PASS
- [ ] `git diff --stat` 无无关改动

### Checkpoint: Complete

- [ ] SPEC 4 条 Success Criteria 全满足
- [ ] 待用户目检：默认 45 更暗一档；0≈无光；100 更亮；foreground 空→层消失
- [ ] 收尾问用户 `/ship` 或 `/publish`

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| bundle 字符串补丁指纹漂移 | Med | old 取当前精确字节；幂等（`new not in js` 才 FAIL）；`verify.py node --check` 拦语法 |
| 属性名与 bundle 接线不一致（曾有 background_dark 教训） | Med | 测试加“project.json slider 属性必在 bundle 接线”守卫 |
| watcher 没覆盖导致拖滑块不实时 | Low | watcher 数组 + bd2Light 内双保险；手测拖动验证 |
| opacity 误用 raw 0-100 导致全白 | Low | 走 !0 映射 + clamp 0-1 + NaN 回落；断言 cssText 为 .45 |

## Open Questions

- 无。
