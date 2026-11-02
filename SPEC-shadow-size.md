# Spec: 阴影大小滑块 (shadow-size)

## Objective

人物接地影（`.bd2-fg-shadow`）当前宽高写死为 `宽 0.235*scale、高 0.062*scale`，
不同角色体型/用户审美下无法调。新增一个 Wallpaper Engine 属性滑块，
让用户按百分比缩放阴影大小，默认保持现有视觉不变。

用户故事：作为壁纸用户，我想在属性面板拖一个滑块放大/缩小脚下椭圆影，
默认 100% 就是现在的大小；拖到 0 时影子消失（等于隐藏）。

## Tech Stack

- `project.json` general.properties 新增 slider `shadowScale`
- `tools/patch.py` bundle 补丁：tb 映射 + store 默认 + `bd2Shadow()` 几何 + watcher
- 纯补丁方案，不新增图片、不重烤背景；灯光层挖洞半径自动跟随（已用同一 `bw/bh` 变量）

## Commands

```sh
python3 tools/patch.py      # 幂等；先归一化再打补丁
python3 tools/test.py
python3 tools/verify.py
python3 tools/smoke.py      # 真实浏览器，抓未捕获异常
```

## Project Structure

```text
SPEC-shadow-size.md   → 本文件
project.json          → 新增 shadowScale slider
tools/patch.py        → tb 映射 + store 默认 shadowScale:100 + bd2Shadow() 乘系数 + watcher 加 h.shadowScale
tests/test_full.py    → 接地影尺寸接线断言
SPEC-ground-shadow.md → 几何章节追加系数说明（实现时同步改）
```

## Code Style

沿用现有 slider 风格（`shadowOffsetX` / `volume`）：

```json
"shadowScale": {
  "fraction": false, "index": 19, "max": 200, "min": 0,
  "order": 119, "text": "阴影大小 % (Shadow size)",
  "type": "slider", "value": 100
}
```

bundle 侧走 `shadowOffsetX` 同款 `!1` 映射（原值，不做 /100）：

```js
shadowOffsetX:[`shadowOffsetX`,!1],
shadowOffsetY:[`shadowOffsetY`,!1],
shadowScale:[`shadowScale`,!1],
```

`bd2Shadow()` 内换算（示意，保持压成一行风格）：

```js
var sc=Number(st.shadowScale);if(!Number.isFinite(sc))sc=100;
sc=Math.max(0,Math.min(2,sc/100));
bw=0.235*s*sc*100; bh=0.062*s*sc*100;
```

几何常量带注释写清来源，不留魔法数；mask 洞继续用同一 `bw/bh`，保证洞与影子同尺寸。

## Testing Strategy

- 先改测试跑 RED（断言新标记缺失），实现后 GREEN（TDD）
- `patch.py` 幂等：连跑两次 bundle 字节一致
- bundle 断言：`shadowScale:[`shadowScale`,!1]`、`h.shadowScale`（watcher）、
  `st.shadowScale`（几何读取）都在，且 `node --check` 通过（经由 `verify.py`）
- `smoke.py`：页面无未捕获异常、控件挂载
- 目检：默认 100 目视与旧版一致；拖到 0 影子消失；200 约两倍大且灯光洞同步（无双轮廓）

## Boundaries

- Always: 最小 diff，只动 `project.json` + `tools/patch.py` + `tests/test_full.py` + SPEC；
  本分支 `feat/shadow-size` 内开发提交，不直推 main
- Ask first: 属性改名、范围偏离 0-200、默认值偏离 100、拆宽高两个滑块
- Never: 不碰 `assets/spines|audios`、不提交 >5MB、不动已烤底图、不改无关属性

## Success Criteria

1. `project.json` 有 `shadowScale` slider（0-200，默认 100）
2. 默认 100 时影子几何与旧版像素一致（`bw=0.235*s`、`bh=0.062*s`）
3. 拖滑块影子即时缩放（DOM `width/height` 百分比随之变化），灯光层 mask 洞同步（无小黑盘+大黑圈）
4. 拖到 0 时影子不可见（宽高为 0）
5. `test.py`、`verify.py`、`smoke.py` 通过，`patch.py` 两次运行字节一致

## Open Questions

无（已确认：单滑块等比、`shadowScale`、0-200/默认100）。
