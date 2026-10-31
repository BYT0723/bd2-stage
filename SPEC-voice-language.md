# Spec: 控制面板语音语言切换 (voice-panel)

## Objective

语音已有 JP/KR 双语（`assets/audios/<id>/{JP,KR}/`，209 个角色齐全），但切换入口只在齿轮
SettingsModal 里（`data-tutorial="audio-language"`），用户记不住、找不着。

把 JP/KR 切换加进悬浮球控制面板（WallpaperControls，和音量滑块放一起），点一下就能切，
不需要进 SettingsModal，也不需要 Wallpaper Engine 属性面板。

用户故事：作为壁纸用户，我打开悬浮球面板就能看到当前语音是 JP 还是 KR，点一下切换，
下一次点击角色播的就是对应语言；选择自动保存，下次打开还是上次选的。

## Tech Stack

- `tools/patch.py` bundle 补丁：在 WallpaperControls 里加语音行（日本語/한국어 seg），走现有
  `settingsStore.setAudioLanguage()`（自动持久化到 localStorage，现有 watcher
  `Oi(()=>g.audioLanguage,()=>{Vn()})` 自动重载语音）
- `project.json` 加 `audioLanguage` combo（JP/KR），右键属性可切
- `tools/patch.py` bundle 补丁：`fb()` 里接 `audioLanguage` 属性 → 复用 `bd2Voice()` 写同一 store
- 不动 `assets/audios/`（只读输入），不动 `tools/mirror.py` / `gen_characters.py`
- 默认语言不变：JP（`Bs` 默认 + WE combo 默认首项 JP 一致）

> 范围变更 2026-11-01：用户要求 WE 右键属性里也要能切（之前决议只做面板）。
> 双入口写同一 store（last-writer-wins）；已知限制：壁纸改不了 WE 属性面板的显示值，
> 且 WE 每次加载会下发它记住的值（WE-wins on load，与音量等现有属性一致）。

## Commands

```sh
python3 tools/patch.py
python3 tools/test.py
python3 tools/verify.py
make check   # check_fav_random + test.py
```

## Project Structure

```text
SPEC-voice-language.md → 本文件
tasks/plan-voice-panel.md   → 实现计划（Phase 2 定）
tasks/todo-voice-panel.md   → 任务清单（Phase 3 定）
tools/patch.py              → 新增补丁：控制面板语音行 + settingsStore 接线
tests/test_full.py          → 新增断言（RED→GREEN）
tools/verify.py             → 如有必要加补丁在位校验
```

## Code Style

沿用面板现有 seg 风格（`nameLang` 语言三段 `zh/ja/en` 那组 `wc-seg`）：

```html
<!-- 示意：音量行下方新增一行，复用 wc-row / wc-seg 类 -->
<div class="wc-row">
  <div class="wc-row__label"><span>语音 (Voice)</span></div>
  <div class="wc-seg" role="group" aria-label="voice language">
    <button>JP</button><button>KR</button>
  </div>
</div>
```

补丁写法沿用 `tools/patch.py` 现有惯例：只认 pristine（`.orig`）指纹、幂等、
一个补丁只改一处，label 中文（如 `"控制面板语音切换"`）。锚点从
`assets/index-Dsqno3tX.js.orig` 里找（音量行 `Zv/Qv/$v/ey` 附近、SettingsModal 的
`[{value:'JP',label:'Japanese'},{value:'KR',label:'Korean'}]` 数组可复用文案）。

状态接线：WallpaperControls 的 setup 目前只拿 `Es()`（壁纸 store `t`）；
语音状态在 `settingsStore`（`Us()`，bundle 里 `g.audioLanguage` / `setAudioLanguage`）。
补丁需在面板 setup 里取一份 settingsStore 实例并绑定 seg，复用现有 watcher 重载语音，
不要自己另起 localStorage 键。

## Testing Strategy

- TDD：先在 `tests/test_full.py` 加断言跑 RED（新标记缺失），实现后 GREEN。
  断言方向：bundle 里控制面板出现语音标记（如 `bd2Voice` / `audio-language` 进面板，
  具体标记实现时定）、`setAudioLanguage` 在面板接线处被引用、`verify.py` 仍全过。
- `python3 tools/patch.py` 幂等：跑两次，第二遍输出 `already patched`。
- `node --check assets/index-Dsqno3tX.js` 语法通过（verify.py 已含）。
- 手工：悬浮球面板出现 JP/KR；默认高亮 JP；点 KR 后点角色播韩语；
  刷新页面仍是 KR（localStorage `bd2-l2d-viewer-settings`）；切回 JP 同理。

## Boundaries

- Always: 先读 `.orig` 定指纹再写补丁；补丁幂等；测试先 RED 后 GREEN；
  跑 `make check` + `verify.py`；`git diff --stat` 自查无无关文件。
- Ask first: ~~改动 `project.json`（本次不需要，加 WE 属性才问）；~~
  加新音频语言目录；动 `Bd2-data.js` / manifest。
  - 2026-11-01 用户已批准加 WE `audioLanguage` combo（本 spec 范围内）。
- Never: 在 worktree 里跑 `make sync`（素材是只读输入）；直改 bundle 不经
  `patch.py`；提交 `.orig` 以外的构建产物；把 secrets/私钥带进仓库。

## Success Criteria

1. 悬浮球控制面板音量行下方有 日本語/한국어 切换，当前语言高亮。
2. 点击切换立即生效（下次点角色播新语言），且刷新后保持（localStorage）。
3. WE 右键属性有语音语言 combo（日本語/한국어），切换后面板高亮同步、下次点角色播新语言。
4. 默认仍是 JP（Bs 默认 + WE combo 默认一致）；SettingsModal 齿轮页与面板同步（同一 store）。
5. `make patch && make check && python3 tools/verify.py` 全过；`patch.py` 二次运行字节幂等。
6. `git diff --stat` 只有 SPEC / `project.json` / `tools/patch.py` / `tests`（+计划/todo 文档）改动。

## Open Questions（已决议 2026-11-01）

1. 位置：~~放音量行正下方（推荐，语音相关归拢），还是角色选择区旁边？默认按音量下方做。~~
   → 决议：音量行正下方。
2. 文案：~~按钮 `JP` / `KR` + 行标签 `语音 (Voice)`（推荐，沿用面板中英双语惯例），~~
   ~~还是 `日本語` / `한국어`？默认按前者做。~~
   → 决议：按钮文案用 `日本語` / `한국어`，行标签 `语音 (Voice)` 不变。
3. 高亮色：~~沿用 `wc-seg__btn--active` 现有主题色（推荐，不引入新色）。~~
   → 决议：沿用 `wc-seg__btn--active` 现有主题色。
