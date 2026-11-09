# Implementation Plan: 帧率属性 (fps)

## Overview

在 `feat/fps-mode` worktree 内新增两个 WE 属性 `fps` / `fpsIdle`（30 / 60 / refresh，默认 refresh/refresh），
用外挂 `custom/bd2-fps.js` 接管 rAF 配速；悬浮球面板注入两行同款 seg；换人时自动提速。
不改 bundle、不改素材。默认与现状一致，省电由用户显式开启。

## Architecture Decisions

- **外挂实现，不加 bundle 补丁**：属性在 classic 脚本里挂 `wallpaperPropertyListener.applyUserProperties`，
  bundle 初始化时会链式调用；面板行走 DOM 注入（与收藏/随机/定时一致）。避免 bundle 指纹冲突与 `patch.py` 迁移。
- **调度器保留循环**：共享时间片批处理，未到点的回调排队而不是丢弃；`cancelAnimationFrame` 用
  逻辑 id + 节点标记实现。调研中错误写法会让 Spine 停摆（draws/s=0），验收必须含 draws>0。
- **默认 refresh=0 旁路**：两档都是 `refresh` 时 target=0，调度器逐帧放行（行为等于现状）；
  任一侧为 30/60 才真正节流。切换属性后一帧内生效。
- **配速用累积截止时间**：`next += 1000/fps`，144Hz 屏上 60fps 目标平均 60（13.9/20.8ms 抖动）；
  落后超过一帧则从当前时间重算，避免长任务后突发补帧。
- **活动判定**：输入事件（capture/passive）刷新 `activeUntil=now+5000`；面板可见 (`getClientRects`)
  也算活动，最多每 250ms 检查一次；`__bd2FpsBoost()` 供换人钩子调用。
- **夹取规则**：两档都是数值且 idle>active 时，执行时按 active（不覆盖用户设置值）。
- **面板 seg 必须加 `bd2-fps-seg` 标记**：`bd2-fav-random.curLang()` 会挑第一个"3 个按钮"的
  `.wc-seg` 当角色名语言组，新行必须有标记并被排除，否则名字→id 映射错位。
- 默认值 refresh/refresh：不改变现有用户观感与耗电；运行时探针必须显式 set 再断言。

## Task List

### Phase 1: RED（测试先行）
- [x] Task 1: 新增 `tests/test_fps_mode.py`（调度器/属性/面板/集成四组断言）+ 注册到 `tools/test.py`
      + `tests/test_fav_random.py` 版本号清单 + `tools/verify.py` 版本号清单；`python3 tools/test.py` 预期 FAIL。

### Checkpoint: RED
- [x] 新测试全部因"文件/标记不存在"失败，其余旧测试仍 PASS

### Phase 2: 调度器核心（Slice A）
- [x] Task 2: `custom/bd2-fps.js` 骨架：常量、归一化、调度器（队列/取消/累积配速/异常隔离）、
      活动监听、`__bd2Fps` API（set/get/target/boost）、面板可见性缓存。
- [x] Verify: `node --check`；`test_scheduler` 转 GREEN；默认 refresh 下页面正常（draws≈60）。

### Phase 3: 双属性（Slice B）
- [x] Task 3: `wallpaperPropertyListener` 接线 + `project.json` 两个 combo（默认 refresh）。
- [x] Verify: `test_props` GREEN；模拟 WE 下发 30/30、60/30、refresh 切换即时生效。

### Phase 4: 面板两行（Slice C）
- [x] Task 4: 面板注入 `活动帧率 (FPS)` / `静止帧率 (Idle FPS)` 两行（`bd2-fps-seg`，复制 `data-v-*`、
      与属性状态互同步）；`bd2-fav-random.curLang()` 排除新 seg 组。
- [x] Verify: `test_panel` GREEN；面板打开出现两行、高亮同步、语言/名字映射不回归。

### Phase 5: 集成（Slice D）
- [x] Task 5: `bd2-carousel.js` swap 调 `__bd2FpsBoost()`；`templates/index.html` + `tools/stamp.py`
      + 版本号；`README.md` 功能列表补一条。
- [x] Verify: `test_integration` GREEN；`python3 tools/stamp.py && python3 tools/verify.py`；`make smoke`。

### Phase 6: 运行时验证与收尾
- [x] Task 6: 新增 `tools/fps_check.py`（无 chromium 或 SwiftShader 时 SKIP）+ `Makefile` 目标；
      跑 60/60、30/30、60/30 静置→boost、refresh 旁路，记录 draws/s 与 CPU。
- [x] Task 7: `make check` + `verify.py` + `smoke` 全过；`git diff --stat` 自查；按切片提交 commit。

### Checkpoint: 完成
- [x] SPEC Success Criteria 6 条全满足，性能数字写进 commit message / 报告

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| rAF 包装让 Spine 停摆 | High | 队列不丢弃 + 逻辑 id 取消；运行时探针断言 30fps 下 draws>0 |
| 新 seg 被 `curLang()` 误认成语言组 | High | `bd2-fps-seg` 标记 + 两个查询点都排除 + 测试守卫 |
| 面板样式不生效 | Med | 复制现有 `.wc-row` / `.bd2-voice-seg` 的 `data-v-*` 属性 |
| 属性下发时机早于外挂 | Low | classic 脚本先于 deferred module 执行；bundle 链式调用 |
| 144Hz 上 60fps 配速偏差 | Med | 累积截止时间；探针在 60Hz 断言 ±10%，高刷只保证平均 |
| 默认 refresh 被误以为"优化没生效" | Low | 规格/README 写明默认与现状一致，需显式选 30/60 |
| headless 软件渲染跑不到 60fps | Med | 探针检测 SwiftShader 直接 SKIP，不进 `make check` |

## Open Questions

- 无（默认 refresh/refresh、双入口、不加预设、无持久化均已确认）。
