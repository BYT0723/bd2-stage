# Spec: overlay 灯光强度滑块 (foreground-opacity)

## Objective

用户觉得前景灯光层（`bd2-fg-light`，`mix-blend-mode:screen`）偏亮。
把写死的 `opacity:.6` 降到默认 `0.45`，并加一个 Wallpaper Engine 属性滑块实时调整。

用户故事：作为壁纸用户，我想在属性面板拖一个滑块实时调灯光强度，默认比现在暗一档；
foreground 为空时灯光层照样关闭。

## Tech Stack

- `project.json` general.properties 新增 slider（0-100，默认 45）
- `tools/patch.py` bundle 补丁：tb 映射 + store 默认 + `bd2LightOp()` + watcher
- 不动 `tools/gen_light_overlay.py`，不重烤 JPG

## Commands

```sh
python3 tools/patch.py
python3 tools/test.py
python3 tools/verify.py
make check   # check_fav_random + test.py
```

## Project Structure

```text
SPEC-foreground-opacity.md → 本文件
tasks/plan-fg-opacity.md   → 实现计划
tasks/todo-fg-opacity.md   → 任务清单
project.json               → 新增 foregroundOpacity slider
tools/patch.py             → tb 映射 + store 默认 + bd2LightOp + watcher + 默认 opacity .45
tests/test_full.py         → 更新断言（RED→GREEN）
```

## Code Style

沿用现有 slider 风格（`volume` / `shadowOffsetX`）：

```json
"foregroundOpacity": {
  "fraction": false, "index": 17, "max": 100, "min": 0,
  "order": 117, "text": "灯光强度 % (Foreground opacity)",
  "type": "slider", "value": 45
}
```

bundle 侧走 `volume` 同款 `!0` 映射（0-100 → 0-1），store 默认 `.45`：

```js
function bd2LightOp(){try{var l=document.querySelector(`.bd2-fg-light`);
if(!l)return;var v=sb&&sb.foregroundOpacity;
v=Number(v);if(!Number.isFinite(v))v=.45;
v=Math.max(0,Math.min(1,v));l.style.opacity=v.toFixed(2)}catch(e){}}
```

## Testing Strategy

- 先改测试跑 RED（断言新标记缺失），实现后 GREEN
- `node --check`（经由 `verify.py`）拦 bundle 语法
- `make check` + `verify.py` 回归
- 手测：默认 45 目检比 60 暗；拖到 0≈无光、100≈更亮；foreground 空→层消失

## Boundaries

- Always：最小 diff，只动 project.json + patch.py + 测试 + spec/plan/todo；本分支内开发提交
- Ask first：默认值偏离 45、范围改动、重烤底图
- Never：改默认背景；提交 `assets/spines|audios`；提交 >5MB；custom 外挂碰 DOM；直推 main

## Success Criteria

1. `project.json` 有 `foregroundOpacity` slider（0-100，默认 45）
2. 前景层 opacity 默认 0.45，滑块实时生效，无需重载
3. foreground 为空时灯光层关闭；非空时 opacity 生效
4. `make check` + `verify.py` 通过，无关改动无

## Open Questions

无（已确认：默认 45、范围 0-100、只做透明度滑块不重生成底图）。
