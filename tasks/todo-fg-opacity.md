## Task 1: 测试先行（RED）——前景透明度断言

**Description:** 在 `tests/test_full.py` 里把写死 `opacity:.6` 的断言换成 `.45` 默认，
并新增 `foregroundOpacity` 属性 + bundle 接线（tb 映射/store 默认/`bd2LightOp`/watcher）断言。
改完先跑一次，确认 RED（新断言失败），证明测试有效。

**Acceptance criteria:**
- [x] `opacity:.6` 断言已移除，改为 `opacity:.45`
- [x] 新增断言：`foregroundOpacity` 在 project.json（slider，0-100，默认 45）且在 bundle 接线
- [x] 新增断言：bundle 含 `bd2LightOp(`、`foregroundOpacity:[` 前景透明度映射、watcher 含 `h.foregroundOpacity`
- [x] `python3 tools/test.py` 在 `test_bundle_patched` 失败（RED），其余通过

**Verification:**
- [x] `python3 tools/test.py` → `test_bundle_patched` FAIL（RED 确认）

**Dependencies:** None

**Files likely touched:**
- `tests/test_full.py`

**Estimated scope:** S (1 文件)

## Checkpoint: RED

- [x] RED 已确认（测试失败且原因是新断言，不是环境问题）

## Task 2: 实现（GREEN）——属性 + 补丁 + 重打

**Description:** `project.json` 新增 `foregroundOpacity` slider（index 17 / order 117，
0-100，默认 45）；`tools/patch.py` 加 4 处补丁：tb 映射 `foregroundOpacity:[...,...]`（!0）、
store 默认 `foregroundOpacity:.45`、`bd2LightOp()` + `bd2Light` 内调用 + 默认 cssText `.45`、
watcher 数组追加；跑 `python3 tools/patch.py` 重打补丁。

**Acceptance criteria:**
- [x] `project.json` 有 `foregroundOpacity`（slider，min 0 max 100 value 45）
- [x] bundle 含 tb 映射、store 默认 `.45`、`bd2LightOp(`、watcher `h.foregroundOpacity`
- [x] 前景层默认 `opacity:.45`，不再含 `opacity:.6`
- [x] `python3 tools/patch.py` 幂等（第二次 `already patched` 或仅 stamp 变化）
- [x] foreground 为空移除层的逻辑未动

**Verification:**
- [x] `python3 tools/test.py` 全 PASS
- [x] `python3 tools/verify.py` PASS（含 `node --check`）
- [x] `make check` PASS
- [x] `git diff --stat` 仅含预期文件（project.json/patch.py/test_full.py/bundle/spec/plan/todo/index.html 版本号）

**Dependencies:** Task 1

**Files likely touched:**
- `project.json`
- `tools/patch.py`
- `assets/index-Dsqno3tX.js`（补丁产物）
- `index.html`（stamp 版本号）

**Estimated scope:** M (3-5 文件)

## Checkpoint: GREEN

- [x] 全套测试通过，无关改动无

## Checkpoint: Complete

- [x] SPEC 4 条 Success Criteria 全满足，待用户目检后问 `/ship` 或 `/publish`
