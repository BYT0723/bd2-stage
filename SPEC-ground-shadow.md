# Spec: 人物接地影 (ground-shadow)

## Objective

聚光灯背景把人物托起来了，但脚下没有影子，人是“浮”在光池上的。
screen 灯光层只能加亮、画不出影子，所以单独加一层接地影，压在角色下面/光层上面，
让立绘有落地的接触感。用户选择方案 A（椭圆接地影），接受“不随动作变形”的近似。

## Tech Stack

- 纯 bundle 补丁（`tools/patch.py`），不新增属性、不加生成图
- 一个 DOM 层 `.bd2-fg-shadow`，`radial-gradient` 椭圆，`pointer-events:none`
- 层级：背景 < 影子(z-5) < 人物(z-10) < 灯光(z-20)。灯光是 screen 加亮、盖在最上面，
  会把影子洗掉，所以在灯光层同一位置用 `mask-image` 挖一个洞（等于“影子挡住地面光”）
- 两个滑块属性 `shadowOffsetX` / `shadowOffsetY`，相对人物微调影子位置

## Commands

```sh
python3 tools/patch.py      # 幂等；先归一化再打补丁
python3 tools/test.py
python3 tools/verify.py
python3 tools/smoke.py      # 真实浏览器，抓未捕获异常
```

## 几何

X 跟人物走，Y 锚地面线——不跟人物脚底走。原因：不同角色脚高差很多
（站姿约 0.92、飘浮姿势更低），按脚底估算必然在某个角色上浮空。

```text
中心 x = 0.5 + 0.02*scale - roleOffsetX/100 + shadowOffsetX/100
中心 y = 0.945 + shadowOffsetY/100        # 0.945 = 背景光池那条地面线
宽 0.190*scale，高 0.050*scale
```

实测：缩放绕画面中心（scale 0.75 → 人物中心 0.515，1.00 → 0.519）；
roleOffset 的平移方向与直觉相反，正的 X 让画面左移、正的 Y 让画面下移。

地面线锚定后不需要按角色重新标定，个体差异用 `shadowOffsetX/Y` 两个滑块微调
（范围 ±50，单位是画面百分比）。

## Project Structure

```text
tools/patch.py                    → normalize() + bd2Shadow() + 两处挂载 + 灯光挖洞
project.json                      → shadowOffsetX / shadowOffsetY 两个滑块
tests/test_full.py                → 接地影接线断言
SPEC-ground-shadow.md             → 本文件
```

## Code Style

沿 `patch.py` 现有风格：补丁 = (old, new, label) 三元的字面量替换，插进去的 JS 压成一行字符串。
几何常量带注释写清来源（实测），不留魔法数。

## Testing Strategy

- `patch.py` 幂等：连跑两次 bundle 字节一致（已加 `normalize()` 反序撤回）
- bundle 断言：`bd2-fg-shadow`、`z-index:5`、`radial-gradient(closest-side`、`bd2Shadow(`、
  `h.shadowOffsetX,h.shadowOffsetY`、`maskImage=m` 都在，且 `node --check` 通过
- `smoke.py`：页面无未捕获异常、控件挂载
- 目检：scale 0.75/1.0 截图，影子贴住脚底不悬空

## Boundaries

- Always: 只改 `tools/patch.py` + 测试 + 本 SPEC
- Ask first: 是否给影子加强度/开关属性
- Never: 不加属性、不碰 `project.json`、不在 `main` 上开发、不动 spines/audios

## Success Criteria

1. `bd2-fg-shadow` 层存在，几何随 `roleScale`/`roleOffset` 更新（属性下发与面板 watcher 两个入口）
2. 层级为背景 < 影子 < 人物 < 灯光；灯光层同位置挖洞，影子不被 screen 洗掉、不盖脚面
3. `shadowOffsetX/Y` 改动后影子即时跟着动（DOM 里 `left/top` 百分比随之变化）
4. `test.py` 10/10、`verify.py`、`smoke.py` 通过，`patch.py` 两次运行字节一致
5. 目检：默认位置落在光池地面线上，个体差异用两个滑块补

## Open Questions

- 是否要强度/尺寸滑块（当前固定 72% 黑、宽 0.19·scale）？暂不加，避免属性膨胀。
