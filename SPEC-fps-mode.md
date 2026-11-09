# Spec: 帧率属性 (fps)

## Objective

壁纸长时间静止运行，但渲染循环始终按显示器刷新率跑帧（60Hz 实测 0.5–0.9 核；120/144Hz 同比更高）。
调研已证实：**帧率是唯一有效杠杆**（60→30fps 省约 40–50% CPU），分辨率、背景/灯光图层、
`preserveDrawingBuffer`/`antialias`、自研外挂脚本都不是瓶颈（隐藏图层 ≤7%，在噪声内）。

用**两个正交属性**取代"模式"枚举：

| 属性 | 含义 | 选项 | 默认 |
|---|---|---|---|
| `fps` | 活动帧率（有输入 / 面板打开时） | 30 / 60 / 跟随刷新率 | **跟随刷新率** |
| `fpsIdle` | 静止帧率（5 秒无输入） | 30 / 60 / 跟随刷新率 | **跟随刷新率** |

组合等价关系：60/30 = 原"自动"，60/60 = 原"性能"，30/30 = 原"省电"，跟随/跟随 = 完全跟随显示器（现状）。
任意组合都合法（例如 30/60 表示"交互时省电、静置时顺滑"）。

**默认跟随/跟随 = 与现状完全一致**：不改变任何现有用户的观感与耗电，省电能力由用户显式开启
（xwallpaper 用户可在 WE 属性里设成 60/30 或 30/30）。

用户故事：作为壁纸用户，我可以右键 Wallpaper Engine 属性或打开悬浮球面板，分别设置
活动/静止帧率；想省电就设 60/30 或 30/30；想完全流畅就保持默认或两档都设 60；想最省电就都设 30。

## Tech Stack

- 新增 `custom/bd2-fps.js`（经典脚本，在 bundle 的 deferred module 之前执行）：
  - 单例 rAF 调度器（共享时间片、保留循环、支持 `cancelAnimationFrame`、按目标帧率累积配速）
  - 监听 `window.wallpaperPropertyListener.applyUserProperties` 读取 `fps` / `fpsIdle`
    （bundle 会链式调用我们的回调）
  - 悬浮球面板注入两行 `.wc-row`（复用 `wc-row` / `wc-seg` / `wc-seg__btn--active`，
    复制 `data-v-*` 使 scoped 样式生效）
  - 交互检测 + `window.__bd2FpsBoost()` 对外提速入口
- `project.json`：新增 `fps` / `fpsIdle` 两个 combo（30 / 60 / refresh，默认 refresh / refresh）
- `custom/bd2-carousel.js`：换人 `swap()` 开头调用 `__bd2FpsBoost()`（覆盖定时轮播等无输入换人）
- `templates/index.html` + `tools/stamp.py`：加入 `bd2-fps.js` 的引用与内容哈希
- **不改 bundle、不加 patch**：属性读取和面板 UI 都走外挂，避免 bundle 指纹与新补丁链式冲突
- 不改素材、不改 `tools/mirror.py` / `gen_characters.py`

## Commands

```sh
python3 tools/stamp.py          # custom → assets + index.html 版本号
python3 tools/test.py           # 全部静态测试
python3 tools/verify.py         # manifest / bundle / 版本号
make check                      # check_fav_random + test.py
make smoke                      # 无头冒烟（异常 + 挂载）
python3 tools/fps_check.py      # 运行时帧率探针（无 chromium / 软件渲染时 SKIP）
```

## Project Structure

```text
SPEC-fps-mode.md            → 本文件
tasks/plan-fps-mode.md      → 实现计划（Phase 2）
tasks/todo-fps-mode.md      → 任务清单（Phase 3）
custom/bd2-fps.js           → 新增：调度器 + 双属性 + 面板两行
custom/bd2-carousel.js      → 换人时 boost（1 行）
templates/index.html        → 新增 <script> 引用
tools/stamp.py              → ASSETS 增加 bd2-fps.js
project.json                → fps / fpsIdle 两个 combo
tests/test_fps_mode.py      → 新增静态/契约测试
tools/test.py               → 注册新测试
tools/fps_check.py          → 新增运行时探针（非门禁）
Makefile                    → 可选 fpscheck 目标
tests/test_fav_random.py    → 版本号脚本清单加入 bd2-fps.js
```

## Code Style

沿用现有外挂风格（ES5、IIFE、`'use strict'`、无箭头函数、无 fetch、无远程 URL）：

```js
(function () {
  'use strict';
  var FPS_ACTIVE = 0, FPS_IDLE = 0, IDLE_MS = 5000;   // 0 = 跟随刷新率（默认）
  var targets = { active: FPS_ACTIVE, idle: FPS_IDLE };  // 数字，0 = 跟随刷新率
  function targetFor(active, panelOpen) {
    var idleNow = !active && !panelOpen;
    var t = idleNow ? targets.idle : targets.active;
    return t === 0 ? 0 : t;                              // 0 表示不封顶
  }
  // ...
  window.__bd2Fps = {
    version: 1,
    set: setTargets, get: function () { return { fps: targets.active, idle: targets.idle }; },
    target: function () { return targetFor(isActive(), panelVisible()); },
    boost: boost
  };
})();
```

约束：面板按钮/高亮沿用 `wc-seg__btn--active`（与语音行一致），不引入新色；
行标签 `活动帧率 (FPS)` / `静止帧率 (Idle FPS)`，按钮 `30 / 60 / 跟随`；
WE 属性文案写清"跟随显示器（高刷更耗电）"。

## 行为契约

### 属性解析

- `fps` / `fpsIdle` 接受 `30` / `60` / `refresh`（字符串或数字，大小写/别名归一化：
  `auto|monitor|display|跟随` → `refresh`）；非法值回退默认（两档都是 refresh）。
- 数值 30/60 直接作为目标帧率；`refresh`（内部存 0）表示不节流、跟随显示器。
- 保护规则：两者都是数值且 `idle > active` 时，**执行时**按 `active`，不覆盖用户设置值
  （之后把活动档调高，静止档仍保留原值；避免"一停下反而更快"）。
- 默认 `refresh / refresh`；不做 localStorage 持久化（用户确认 xwallpaper 兼容 WE 属性，属性是唯一持久来源）。
- 属性在启动时和变更时都立即生效；面板点击与属性写同一份内存状态，界面高亮同步。

### `active` 判定（决定用哪一档）

- `active` = 最近一次输入在 5 秒内：`pointerdown` / `pointermove` / `pointerup` / `wheel` /
  `keydown` / `touchstart`（window 捕获、passive），以及 `visibilitychange` 变可见。
- “活动”还包括 `.wc-panel` 存在且 `getClientRects().length > 0`（面板打开期间用活动帧率）。
- `window.__bd2FpsBoost()` 显式提速 5 秒；`bd2-carousel.js` 的 `swap()` 调用它。

### rAF 调度器

- 在 bundle 执行前安装，统一接管 `requestAnimationFrame` / `cancelAnimationFrame`。
- 共享时间片：每帧最多执行一批回调；未到时间的注册保留在队列中，下一次到点执行——**绝不丢弃回调**
  （调研中错误写法会让 Spine 循环永久停摆，`draws/s = 0`）。
- 配速用**累积截止时间**（`next += 1000/fps`），使 60fps 目标在 144Hz 屏上平均 60（允许 13.9/20.8ms 抖动），
  落后超过一帧时从当前时间重新起算，避免长任务后突发补帧。
- 返回稳定的逻辑 id；`cancelAnimationFrame(id)` 必须真正取消排队中的回调。
- 回调异常被隔离（`try/catch`），不能中断其它回调；只记录一次告警。
- `refresh`（0）时不做节流，逐帧执行；两档都是 `refresh` 时行为与现状一致。
- 切换属性后一帧内生效。
- 不影响 WAAPI / CSS 动画（转盘、面板过渡仍由合成器按刷新率播放）。

### 面板入口

- 悬浮球面板出现后注入两行，位置在语音行之后、随机/收藏工具行之前（找不到语音行则退回 `.wc-list` 之前）。
- 行 1：`活动帧率 (FPS)` + `30 / 60 / 跟随`；行 2：`静止帧率 (Idle FPS)` + `30 / 60 / 跟随`。
- 当前值高亮；点击立即切换调度器，并与 WE 属性来的值互相同步（同写一份内存状态）。
- 不破坏 `bd2-fav-random.js` 的 `curLang()`（新增 seg 均为 3 个按钮且不加语音标记；
  注意它的 `curLang` 只认"3 段 + 非 bd2-voice-seg"的组，新增组不能用 `wc-seg` 以外的结构导致误判——
  实现时加 `bd2-fps-seg` 标记并在必要时排除）。

## Testing Strategy

- **TDD**：先写 `tests/test_fps_mode.py`（RED：文件/属性/标记不存在），再实现到 GREEN。
- 静态/契约测试：
  - `project.json` 有 `fps` / `fpsIdle`，`type=combo`，默认 `60` / `30`，选项含 `30/60/refresh`，
    index/order 唯一。
  - `templates/index.html` 与 `index.html` 都引用 `bd2-fps.js?v=<hash>`，且 `stamp.py` 会刷新它。
  - `custom/bd2-fps.js`：含两档常量、5 秒、`refresh` 归一化、`__bd2Fps`、`wallpaperPropertyListener`、
    `MutationObserver`、`cancelAnimationFrame`、累积配速、无 `http(s)://`、无 `fetch(`、
    不出现 `T_(` 等 bundle 内部符号。
  - `custom/bd2-carousel.js`：`swap()` 内调用 `__bd2FpsBoost`。
  - `tests/test_fav_random.py::test_versions_stamped` 清单加入 `bd2-fps.js`。
- 运行时探针 `tools/fps_check.py`（手动/按需，不进 `make check`）：
  - 无 chromium 或 WebGL renderer 为 SwiftShader → SKIP（软件渲染跑不到 60fps）。
  - 断言：`fps=60,idle=60` draw/s 60±10%；`30/30` 30±10%；`60/30` 静置 6 秒后 30±10%，
    `__bd2FpsBoost()` 后 200ms 内回到 60；30fps 下仍持续 draw（>0）。
- 手工验证：WE 两个属性三档切换、面板两行切换与高亮、语音/收藏/随机/定时/转盘/背景灯光无回归；
  1 分钟静置无长任务堆积、无内存增长。
- 门禁：`make check`、`python3 tools/verify.py`、`make smoke` 全过。

## Boundaries

- **Always**：先写失败测试；外挂不碰 bundle 内部；无远程请求；保持 ES5 风格；
  更新 `stamp.py` + 版本号测试；跑 `make check` / `verify.py` / `smoke`；`git diff --stat` 自查。
- **Ask first**：改默认值；增加 45fps / 自定义数值档；做 localStorage 持久化；改成 bundle 补丁实现。
- **Never**：在 worktree 跑 `make sync`；提交 `assets/spines|audios` 等只读素材；
  丢弃/停摆 rAF 回调；为了通过测试而放宽阈值或删测试；引入依赖。

## Success Criteria

1. WE 右键属性出现「帧率 (FPS)」与「静止帧率 (Idle FPS)」两个 combo，默认 refresh / refresh
   （与现状一致）；切换立即生效，`refresh` 表示跟随显示器。
2. 悬浮球面板出现两行三档按钮，高亮与当前值一致；点击立即生效，且与 WE 属性值同步。
3. 运行时：`60/60` ≈60 draws/s，`30/30` ≈30 draws/s，`60/30` 静置降到 30、输入/面板/换人回到 60；
   `idle > active` 执行时按 `active`（不覆盖用户设置值）。
4. 30fps 下动画持续推进（draws/s > 0），Spine 循环不停摆；换人就绪时间与现状同级（≤300ms），
   转盘动画仍完整播放。
5. 现有功能无回归：语音 JP/KR、收藏、随机、定时、换人转盘、背景/前景/接地影、缓存版本号。
6. `make check` + `python3 tools/verify.py` + `make smoke` 全过；`git diff --stat` 仅本 spec 列出的文件。

## Assumptions（请确认）

1. 属性键 `fps` / `fpsIdle`，WE 文案「帧率 (FPS)」「静止帧率 (Idle FPS)」，默认 **refresh / refresh**。
2. 静置阈值与提速保持时间都取 **5 秒**（常量可调，不加第三个属性）。
3. 面板入口用外挂 DOM 注入（与收藏/随机/定时一致），**不改 bundle 补丁**；两行，每行 `30/60/跟随`。
4. 不做持久化：浏览器直接预览时每次回到默认；WE 会下发记住的属性值。
5. "跟随刷新率"允许两档都选；两档都是 refresh 时不安装包装，切回 refresh 后新回调直接走原生
   （零排队开销），行为等于现状。

## Open Questions

- 已决议：面板不加"自动/性能/省电"快捷预设；两个属性已覆盖该功能。
