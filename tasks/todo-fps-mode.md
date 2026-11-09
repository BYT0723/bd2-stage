## Task 1: RED — 测试先行

**Description:** 新增 `tests/test_fps_mode.py`，覆盖四组契约：调度器、双属性、面板两行、集成
（carousel boost / stamp / verify / curLang 排除）。注册到 `tools/test.py`，并把 `bd2-fps.js`
加入 `tests/test_fav_random.py::test_versions_stamped` 与 `tools/verify.py` 的版本号清单。

**Acceptance criteria:**
- [x] `python3 tools/test.py` 因新测试失败（RED），旧测试仍 PASS
- [x] 断言覆盖：默认 refresh/refresh、30/60/refresh 选项、5 秒常量、队列不丢弃、
      `cancelAnimationFrame`、`bd2-fps-seg`、carousel boost、stamp 清单

**Verification:**
- [x] `python3 tools/test.py` 输出新 FAIL + 旧 PASS

**Dependencies:** None

**Files likely touched:**
- `tests/test_fps_mode.py`（新增）
- `tools/test.py`
- `tests/test_fav_random.py`
- `tools/verify.py`

**Estimated scope:** M（4 文件，纯测试）

## Task 2: 调度器核心（Slice A）

**Description:** 新建 `custom/bd2-fps.js`：常量、值归一化、共享时间片 rAF 调度器（保留循环、
逻辑 id 取消、异常隔离、累积配速）、交互监听、面板可见性缓存、`window.__bd2Fps` API。

**Acceptance criteria:**
- [x] 默认 target=0 时逐帧放行，行为与未包装一致
- [x] 未到点的回调留在队列、下次到点执行，不丢弃
- [x] `cancelAnimationFrame` 能取消排队回调
- [x] `window.__bd2Fps.{set,get,target,boost}` 可用

**Verification:**
- [x] `node --check custom/bd2-fps.js`
- [x] `python3 tools/test.py` 的 scheduler 断言 GREEN
- [x] 无头页面默认加载 draw/s ≈60，Spine 不停摆

**Dependencies:** Task 1

**Files likely touched:**
- `custom/bd2-fps.js`

**Estimated scope:** M（1 文件，核心逻辑）

## Task 3: 双属性接线（Slice B）

**Description:** 挂 `wallpaperPropertyListener` 读 `fps` / `fpsIdle`；`project.json` 增加两个 combo
（30/60/refresh，默认 refresh，index 20/21，order 120/121）；idle>active 执行时按 active。

**Acceptance criteria:**
- [x] 属性变更即时生效（无需刷新）
- [x] 非法值/缺省回退 refresh
- [x] idle>active 执行时按 active（不覆盖用户设置值）

**Verification:**
- [x] `python3 tools/test.py` 的 props 断言 GREEN
- [x] 模拟 `applyUserProperties` 下发 30/30、60/30、refresh，`__bd2Fps.get()` 与 target 正确

**Dependencies:** Task 2

**Files likely touched:**
- `custom/bd2-fps.js`
- `project.json`

**Estimated scope:** S（2 文件）

## Task 4: 面板两行（Slice C）

**Description:** 面板出现后注入两行 seg（活动/静止 × 30/60/跟随），复制 scoped 样式属性，
与属性状态互同步；`bd2-fav-random.js` 的 `curLang()` 两处查询排除 `.bd2-fps-seg`。

**Acceptance criteria:**
- [x] 两行出现于语音行之后、随机/收藏工具行之前
- [x] 点击立即生效，高亮与 WE 属性值同步
- [x] 名字语言判定不受影响（curLang 不选中新 seg）

**Verification:**
- [x] `python3 tools/test.py` 的 panel 断言 GREEN
- [x] 面板打开截图/目检；切换名字语言后收藏红心与随机定位仍正确

**Dependencies:** Task 3

**Files likely touched:**
- `custom/bd2-fps.js`
- `custom/bd2-fav-random.js`

**Estimated scope:** M（2 文件）

## Task 5: 集成（Slice D）

**Description:** `bd2-carousel.js` swap 首行调用 `__bd2FpsBoost()`；`templates/index.html` 加脚本引用；
`tools/stamp.py` ASSETS 加入；README 功能列表补一条。

**Acceptance criteria:**
- [x] 所有换人（含定时轮播）都会 boost
- [x] `index.html`/`templates` 均引用 `bd2-fps.js?v=<hash>`，stamp 幂等
- [x] README 写明两档默认 refresh、可设 30/60 省电

**Verification:**
- [x] `python3 tools/stamp.py && python3 tools/verify.py`
- [x] `make smoke` 无异常

**Dependencies:** Task 4

**Files likely touched:**
- `custom/bd2-carousel.js`
- `templates/index.html`
- `tools/stamp.py`
- `README.md`

**Estimated scope:** S（4 文件，均为接线）

## Task 6: 运行时探针

**Description:** 新增 `tools/fps_check.py`（复用 smoke 的 chromium 启动方式，真实 GPU；
SwiftShader 或无 chromium 时 SKIP），断言 60/60≈60、30/30≈30、60/30 静置→30、boost→60、
30fps 下 draws>0；`Makefile` 加 `fpscheck`。

**Acceptance criteria:**
- [x] `python3 tools/fps_check.py` 本机 PASS 并打印 draws/s
- [x] 软件渲染环境返回 SKIP（退出码 0）

**Verification:**
- [x] 本机运行输出 PASS；对比 30/60 的 draws/s 与 CPU

**Dependencies:** Task 5

**Files likely touched:**
- `tools/fps_check.py`（新增）
- `Makefile`

**Estimated scope:** M（2 文件）

## Checkpoint: 完成

- [x] `make check` + `python3 tools/verify.py` + `make smoke` + `python3 tools/fps_check.py` 全过
- [x] `git diff --stat` 仅 SPEC / tasks / custom / project.json / tools / tests / README
- [x] 默认 refresh/refresh 与改动前行为一致（draws/s 与 CPU 在噪声内）

## 实测（tools/fps_check.py，Radeon 780M / 1280×720）

| 模式 | draws/s | 总 CPU（核） |
|---|---|---|
| refresh / refresh（默认） | 59.8 | 0.50 |
| 60 / 60 | 58.8 | 0.41 |
| 30 / 30 | 30.2 | 0.24 |
| 60 / 30 静置 | 29.9 | 0.22 |
| 60 / 30 boost | 59.6 | 0.37 |

30fps 相对默认约省 52% CPU；换人/输入/面板打开会立即回到活动档。
