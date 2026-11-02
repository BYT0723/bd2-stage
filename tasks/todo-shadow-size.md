## Task 1: 测试先行（RED）

**Description:** 在 `tests/test_full.py` 接地影断言区追加 `shadowScale` 接线断言，跑出 RED，锁定实现契约。

**Acceptance criteria:**
- [ ] props 断言：`shadowScale` 为 slider，min 0 max 200 value 100
- [ ] bundle 断言：`shadowScale:[`shadowScale`,!1]`、`h.shadowScale`、`st.shadowScale` 三标记
- [ ] `python3 tools/test.py` 在 Task 1 后失败（RED），报错指向 `shadowScale`

**Verification:**
- [ ] Tests pass: `python3 tools/test.py`（预期 RED）
- [ ] Build succeeds: `python3 tools/verify.py`（bundle 未改前仍 PASS，不阻塞）
- [ ] Manual check: 断言名与实现标记一一对应

**Dependencies:** None

**Files likely touched:**
- `tests/test_full.py`

**Estimated scope:** S (1 文件)

## Task 2: 属性 + 补丁实现（GREEN）

**Description:** `project.json` 新增滑块；`tools/patch.py` 加 tb 映射 + store 默认 + `bd2Shadow` 系数 + watcher，跑 patch 后 GREEN。

**Acceptance criteria:**
- [ ] `project.json` 有 `shadowScale`（index 19 / order 119 / 0-200 / 默认 100）
- [ ] `patch.py` 四处生效：store 默认 `shadowScale:100`、tb `!1`、几何读 `st.shadowScale` 并钳制、watcher 含 `h.shadowScale`
- [ ] 默认 100 时 `bw/bh` 与旧版等价；mask 洞仍用同一 `bw/bh`
- [ ] `python3 tools/test.py` 全 PASS（GREEN）

**Verification:**
- [ ] Tests pass: `python3 tools/test.py`
- [ ] Build succeeds: `python3 tools/patch.py && python3 tools/patch.py`（第二次 already patched，字节一致）+ `python3 tools/verify.py`
- [ ] Manual check: `git diff --stat` 仅 3 文件（project.json / patch.py / test_full.py）+ bundle 产物

**Dependencies:** Task 1

**Files likely touched:**
- `project.json`
- `tools/patch.py`
- `assets/index-Dsqno3tX.js`（补丁产物）

**Estimated scope:** M (2-3 文件)

## Checkpoint: 接线

- [ ] All tests pass
- [ ] patch 幂等 + verify 通过
- [ ] Review with human before proceeding（如有几何疑问）

## Task 3: 文档 + 烟测回归

**Description:** 更新 `SPEC-ground-shadow.md` 几何章节（追加 `*sc` 系数），跑 `smoke.py`，确认默认视觉不变。

**Acceptance criteria:**
- [ ] `SPEC-ground-shadow.md` 宽高公式含 `*sc` 且注明 `sc=shadowScale/100`
- [ ] `python3 tools/smoke.py` 通过，无未捕获异常
- [ ] `make check` 通过

**Verification:**
- [ ] Tests pass: `make check`
- [ ] Build succeeds: `python3 tools/verify.py`
- [ ] Manual check: `git diff --stat` 无无关改动、无调试残留

**Dependencies:** Task 2

**Files likely touched:**
- `SPEC-ground-shadow.md`
- `SPEC-shadow-size.md`（如有实现偏离则同步）

**Estimated scope:** S (1-2 文件)

## Checkpoint: 完成

- [ ] All acceptance criteria met（SPEC Success Criteria 5 条）
- [ ] Ready for review（等用户选 /ship 或 /publish）
