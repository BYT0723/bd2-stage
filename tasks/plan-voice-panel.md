# Implementation Plan: 控制面板语音语言切换

## Overview

在悬浮球控制面板（WallpaperControls）音量行下方加一行 JP/KR… 不，
按已决议文案：`日本語` / `한국어` 两段切换，复用 `wc-seg` 样式与主题高亮，
走现有 `settingsStore.setAudioLanguage()`（持久化 + 语音重载 watcher 全是现成的，
补丁只负责 UI 接线）。实现载体是 `tools/patch.py` 新增幂等补丁 + `tests/test_full.py`
断言，全程 TDD（RED→GREEN）。

## Architecture Decisions

- 不新增 Wallpaper Engine 属性（用户明确不要放 property 里），`project.json` 不动。
- 不自建状态：面板 setup 里取 `Us()`（settingsStore，与 `g.audioLanguage` 同一实例），
  点击调 `setAudioLanguage()`；SettingsModal 与面板自动同步；现有 watcher
  `Oi(()=>g.audioLanguage,()=>{Vn()})` 负责重载语音，不另起逻辑。
- 补丁锚点（只认 pristine 指纹，`patch.py` 惯例）：
  1. setup 头 `setup(e){let t=Es(),n=`full`` —— 注入 settingsStore 引用；
  2. 音量行 const `Zv/Qv/$v/ey` 区 —— 加语音行 const；
  3. 音量行 render 块之后 —— 插入语音 seg 行（仿 `nameLang` 的 `wc-seg` /
     `wc-seg__btn` + `wc-seg__btn--active` 写法，文案 `日本語`/`한국어`）。
- 标记：补丁注入可断言的 markers（如 `bd2Voice` helper / `audio-language` 进面板），
  供 `tests/test_full.py` 与 `verify.py` 校验。
- 风险：bundle 是 minified，锚点字符串必须从 pristine 精确拷贝；
  缓解——实现前用脚本在 normalize 后的 bundle 上验证每个 `old` 恰出现 1 次，
  `patch.py` 本身也会对不上指纹就 FAIL 停下。

## Task List

### Phase 1: 测试先行（RED）

- [ ] Task 1: `tests/test_full.py` 加语音面板断言，跑出 RED（见 tasks/todo-voice-panel.md）
- [ ] Task 2: 锚点指纹确认脚本（pristine 上每个 old 唯一命中）

### Checkpoint: RED 确认

- [ ] `python3 tools/test.py` 明确失败在新增断言（且只失败在新增断言）
- [ ] 锚点全部唯一命中，无需改方案

### Phase 2: 补丁实现（GREEN）

- [ ] Task 3: `tools/patch.py` 新增补丁（setup 接线 + 语音行 const + render 插入）
- [ ] Task 4: `make patch && make check && verify.py` 全过 + 幂等（二次 patch 无变化）

### Checkpoint: GREEN + 手工

- [ ] `node --check` 通过（verify.py 内含）
- [ ] 手工：面板音量下方出现 日本語/한국어；默认 日本語 高亮；点 한국어 后点角色播韩语；
      刷新保持；切回亦然；SettingsModal 齿轮页同步
- [ ] `git diff --stat` 只有 SPEC / patch.py / tests / plan-todo 文档

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| minified 锚点在 pristine 对不上/多命中 | 中 | Task 2 先验证唯一命中；`patch.py` 指纹 FAIL 即停 |
| 面板 setup 作用域拿不到 `Us()` | 中 | 退路：顶层注入 `bd2Voice()` helper 直调 store；Task 2 确认 |
| 与现有 watcher 冲突（切语言不重载） | 低 | 复用同一 store + 现有 watcher，不自建；手工验证覆盖 |
| 改坏面板渲染（Vue render 括号错位） | 高 | `node --check` + verify + 手工冒烟；小步提交便于回滚 |

## Open Questions

- 无（spec 决议已定：音量行下方 / 日本語・한국어 / 沿用主题高亮）。实现中若锚点迫使换位，
  先停下汇报再定，不擅自换方案。

### Phase 3: WE 属性入口（2026-11-01 范围追加）

- [ ] Task 5: `project.json` 加 `audioLanguage` combo + `patch.py` 接 `fb()`（见 tasks/todo-voice-panel.md）
- [ ] Task 6: CDP 模拟 WE 下发验证双入口同步 + 全量验证

### Checkpoint: WE 双入口

- [ ] WE 下发 KR → 面板高亮同步；面板切回 JP → store 同步
- [ ] `make check` + `verify.py` 全过，diff 干净
