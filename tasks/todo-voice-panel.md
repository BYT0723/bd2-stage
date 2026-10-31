## Task 1: 语音面板断言（RED）

**Description:** 在 `tests/test_full.py` 的 `test_bundle_patched()`（或新增
`test_voice_panel()`，二选一，实现时定）加断言：bundle 控制面板含语音切换标记、
`setAudioLanguage` 被面板引用。加完先跑，确认 RED。

**Acceptance criteria:**
- [x] 新增断言明确指向面板语音行（如 `bd2Voice` / 面板内 `audio-language` / 日本語文案标记）
- [x] `python3 tools/test.py` 失败且只失败在新增断言

**Verification:**
- [x] `python3 tools/test.py` 输出 FAIL 行是新增断言

**Dependencies:** None

**Files likely touched:**
- `tests/test_full.py`

**Estimated scope:** S (1 文件，数行断言)

## Task 2: 锚点指纹确认

**Description:** 只读验证：`patch.py` 计划用的每个 `old` 锚点（setup 头、音量行 const、
音量行 render 块）在 normalize 后的 bundle（pristine 视角）里恰出现 1 次；
同时确认 `Us`/`setAudioLanguage` 可达性。输出命中计数，不写实现代码。

**Acceptance criteria:**
- [x] 每个锚点恰命中 1 次（给出计数）
- [x] 若有锚点不唯一/缺失，输出替代锚点候选或升级方案（停下等确认，不硬写）

**Verification:**
- [x] 贴出各锚点 `js.count(old) == 1` 的检查输出

**Dependencies:** Task 1

**Files likely touched:**
- 临时检查脚本（`/tmp/opencode`，不入库）

**Estimated scope:** XS (只读脚本)

## Checkpoint: RED 确认

- [x] 测试明确 RED 在新增断言
- [x] 锚点全部唯一命中
- [x] 与人确认后进入 Phase 2（若锚点有问题，先修 plan）

## Task 3: patch.py 语音补丁

**Description:** `tools/patch.py` 的 `PATCHES` 追加补丁组：面板 setup 取 `Us()` settingsStore、
语音行 const、音量行下方 render 插入 日本語/한국어 seg（复用 `wc-seg` /
`wc-seg__btn--active`），点击调 `setAudioLanguage()`。`make patch` 应用。

**Acceptance criteria:**
- [x] `python3 tools/patch.py` 输出 patched 含新 label，且 `node --check` 通过
- [x] 面板出现 日本語/한국어 行（以 bundle 文本含文案 + 接线标记为准）
- [x] 不动 `project.json` / 音频素材 / `Bs` 默认 JP

**Verification:**
- [x] `python3 tools/patch.py && node --check assets/index-Dsqno3tX.js`
- [x] `python3 tools/test.py` 新增断言转 GREEN（整体全过）

**Dependencies:** Task 1, Task 2, Checkpoint RED

**Files likely touched:**
- `tools/patch.py`
- `assets/index-Dsqno3tX.js`（生成物，patch 产物）

**Estimated scope:** M (2-3 处补丁，仿现有 seg 写法)

## Task 4: 全量验证 + 幂等 + 手工

**Description:** `make check` + `verify.py` 全过；`patch.py` 跑第二遍幂等；
手工按 spec 成功标准走一遍面板切换；`git diff --stat` 自查。

**Acceptance criteria:**
- [x] `make check` 全 PASS，`python3 tools/verify.py` 输出 VERIFY OK
- [x] 第二遍 `make patch` 后 bundle sha256 不变，无重复标记（字节幂等）
- [ ] 手工：默认 日本語 高亮；切 한국어 点角色播韩语；刷新保持；切回亦然；
      SettingsModal 同步；`git diff --stat` 无无关文件

**Verification:**
- [x] `make check && python3 tools/verify.py`
- [x] `python3 tools/patch.py` 第二遍 bundle sha256 不变（normalize 后重打，字节幂等）
- [ ] 手工检查清单逐项打勾（需 Wallpaper Engine 实测）

**Dependencies:** Task 3

**Files likely touched:**
- `tools/verify.py`（仅如需加在位校验才动，否则不动）
- `SPEC-voice-language.md`（如实现偏离，同步更新）

**Estimated scope:** S (验证为主)

## Checkpoint: Complete

- [x] spec 成功标准 5 条全部满足
- [x] 人 review 通过，决定 `/ship`（main 内集成）还是继续打磨

## Task 5: WE 属性 combo + fb 接线（RED→GREEN）

**Description:** `project.json` 加 `audioLanguage` combo（日本語=JP / 한국어=KR，默认 JP，
index 18 / order 118，接在 foregroundOpacity 之后）；`tools/patch.py` 在 `fb()` 里加分支：
`audioLanguage` 下发值归一化（`JP`/`0`→JP，`KR`/`1`→KR，大小写不敏感）后调 `bd2Voice()`。
先加断言跑 RED，再实现跑 GREEN。

**Acceptance criteria:**
- [x] `project.json` 有 `audioLanguage` combo，options 含 JP/KR，默认 JP
- [x] bundle `fb()` 含 `audioLanguage` 分支，复用 `bd2Voice`
- [x] 非法值下发不炸、不切语言（归一化兜底，CDP 已验）

**Verification:**
- [x] `python3 tools/test.py` 新增断言 GREEN（12/12）
- [x] CDP 模拟 WE 下发：KR→store+面板同步；非法值不变；`0`→JP；无异常

**Dependencies:** Task 4（面板入口已 GREEN）

**Files likely touched:**
- `project.json`
- `tools/patch.py`
- `tests/test_full.py`

**Estimated scope:** S (2 文件 + 断言)

## Task 6: 全量验证 + 提交

**Description:** `make check` + `verify.py` + 二次 patch 字节幂等 + `git diff --stat` 自查；
已知限制（WE-wins on load、壁纸回写不了 WE 下拉显示）已记入 spec，不当 bug。

**Acceptance criteria:**
- [x] 全过；工作树只剩目标文件改动

**Verification:**
- [x] `make check && python3 tools/verify.py`
- [x] 二次 `make patch` sha256 不变

**Dependencies:** Task 5

**Files likely touched:**
- 无（验证为主）

**Estimated scope:** XS
