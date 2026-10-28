# Spec: 人物接地影 (ground-shadow)

## Objective

聚光灯背景把人物托起来了，但脚下没有影子，人是“浮”在光池上的。
screen 灯光层只能加亮、画不出影子，所以单独加一层接地影，压在角色下面/光层上面，
让立绘有落地的接触感。用户选择方案 A（椭圆接地影），接受“不随动作变形”的近似。

## Tech Stack

- 纯 bundle 补丁（`tools/patch.py`），不新增属性、不加生成图
- 一个 DOM 层 `.bd2-fg-shadow`，`radial-gradient` 椭圆，`pointer-events:none`

## Commands

```sh
python3 tools/patch.py      # 幂等；先归一化再打补丁
python3 tools/test.py
python3 tools/verify.py
python3 tools/smoke.py      # 真实浏览器，抓未捕获异常
```

## 几何（1920x1080 实测标定）

缩放绕画面中心走、offset 的平移方向与直觉相反（正的 X 让画面左移、正的 Y 让画面下移）：

```text
中心 x = 0.5 + 0.02*scale - offsetX/100
脚底 y = 0.5 + 0.42*scale - offsetY/100
脚部宽 ≈ 0.145*scale
```

实测点：scale 0.75 → 脚底 0.815；1.00 → 0.920；1.50 起出画。影子椭圆取
`宽 0.190*scale`、`高 0.050*scale`、中心 `脚底 + 0.012*scale`（贴住脚底不糊脚面）。

## Project Structure

```text
tools/patch.py                    → normalize() + bd2Shadow() + 两处挂载
tests/test_full.py                → 接地影接线断言
SPEC-ground-shadow.md             → 本文件
```

## Code Style

沿 `patch.py` 现有风格：补丁 = (old, new, label) 三元的字面量替换，插进去的 JS 压成一行字符串。
几何常量带注释写清来源（实测），不留魔法数。

## Testing Strategy

- `patch.py` 幂等：连跑两次 bundle 字节一致（已加 `normalize()` 反序撤回）
- bundle 断言：`bd2-fg-shadow`、`z-index:21`、`radial-gradient(closest-side`、`bd2Shadow(`、
  `bd2Shadow(h.roleScale` 都在，且 `node --check` 通过
- `smoke.py`：页面无未捕获异常、控件挂载
- 目检：scale 0.75/1.0 截图，影子贴住脚底不悬空

## Boundaries

- Always: 只改 `tools/patch.py` + 测试 + 本 SPEC
- Ask first: 是否给影子加强度/开关属性
- Never: 不加属性、不碰 `project.json`、不在 `main` 上开发、不动 spines/audios

## Success Criteria

1. `bd2-fg-shadow` 层存在，几何随 `roleScale`/`roleOffset` 更新（属性下发与面板 watcher 两个入口）
2. 影子在角色之下、灯光层之上（`z-index:21`），不被 screen 光池洗掉、不盖住脚面
3. `test.py` 10/10、`verify.py`、`smoke.py` 通过，`patch.py` 两次运行字节一致
4. 目检：scale 0.75 与 1.0 下影子贴脚底

## Open Questions

- 是否要强度滑块（当前固定 72% 黑）？暂不加，避免属性膨胀。
