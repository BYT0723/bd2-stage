# Spec: 换人转盘动画 (character-carousel)

## Objective

当前换人是硬切：bundle 在 `selectedCharacterId` 变化时先 `dispose()` 旧 SpinePlayer、
清空容器，再新建 player，旧画面来不及做任何过渡。

做成“转盘”效果：旧人物朝一侧 3D 转出，新人物从另一侧转回正位；方向每次随机。
覆盖列表点选、🎲 随机、⏱ 定时、URL 换人四种入口。初始加载不播。

用户故事：作为壁纸用户，我在换角色时希望旧人物旋转着退场、新人物从左边或右边
转进来，像转盘换人一样；如果系统开了“减少动效”，就保持原来的瞬间切换。

## Tech Stack

- 外挂 `custom/bd2-carousel.js`：2D canvas 定格快照 + Web Animations API
- `tools/patch.py`：bundle 两处钩子（换人 watcher / Spine success）
- 不新增依赖、不联网、不要求双 player

## Commands

```sh
python3 tools/patch.py      # 幂等；先归一化再打补丁
python3 tools/stamp.py      # custom → assets + index.html 版本号
python3 tools/test.py
python3 tools/verify.py
python3 tools/smoke.py
```

## Project Structure

```text
custom/bd2-carousel.js              → 转盘动效外挂（swap / enter / 快照 / 清理）
templates/index.html                → 挂载 bd2-carousel.js?v=DEV
tools/stamp.py                      → ASSETS 增加 bd2-carousel.js
tools/patch.py                      → 两个 try/catch 钩子
tools/verify.py                     → bundle 钩子 + 脚本版本断言
tests/test_carousel.py              → 静态契约测试
tests/test_fav_random.py            → 版本号列表加 bd2-carousel.js
tests/test_full.py                  → bundle 钩子断言
tools/check_fav_random.py           → 外挂静态自检
README.md                           → 功能列表补一行
```

## Code Style

外挂沿用现有 ES5 风格（`var` / `function` / `'use strict'`），常量集中在文件头：

```js
var OUT_MS = 420;
var IN_MS = 560;
var HOLD_MS = 3000;
var PERSPECTIVE = 1600;
var ANGLE = 62;
var SHIFT = 26;
var SCALE = 0.82;
var ORIGIN = '52% 58%';
```

位姿统一由一个函数生成，旧人出场和新人入场共用同一套左右规则：

```js
function pose(sign, edge) {
  return 'perspective(' + PERSPECTIVE + 'px)' +
    ' translateX(' + (sign * SHIFT * edge) + '%)' +
    ' rotateY(' + (-sign * ANGLE * edge) + 'deg)' +
    ' scale(' + (1 - (1 - SCALE) * edge) + ')';
}
```

bundle 钩子必须容错，外挂异常不能影响换人：

```js
try{window.__bd2CarouselSwap&&window.__bd2CarouselSwap()}catch(e){}
```

## Testing Strategy

- 先写静态契约测试并跑 RED（文件/钩子/版本号缺失），实现后 GREEN
- `node --check` 覆盖外挂与 bundle（verify.py 内已有 bundle 检查）
- `patch.py` 幂等：连跑两次 bundle 字节一致
- `smoke.py`：页面无未捕获异常、应用与控件挂载
- 手动验收：列表 / 🎲 / ⏱ / URL 四种入口换人；左右方向随机；旧人反方向转出；
  连点不残留；reduced-motion 下无动画

## Boundaries

- Always: 最小 diff；只在 `feat/character-carousel` worktree 内开发提交；动效只在人物层
- Ask first: 加 WE 开关、改方向策略（交替而不是独立随机）、覆盖大招/约会切换
- Never: 不碰 `assets/spines|audios`；不提交大文件；不改背景/灯光/接地影；不做双 player

## Success Criteria

1. 任意入口换人都有“旧人反向转出 + 新人随机左右转入”的转盘动画
2. 每次方向独立随机，新旧方向相反
3. 无闪白/闪黑/残影/残留 DOM；快速连点正常；加载失败 3 秒内兜底显示
4. 初始加载不播；`prefers-reduced-motion` 时不播
5. `tools/test.py`、`tools/verify.py`、`tools/smoke.py` 通过

## Open Questions

无（已确认：旧人定格快照、只覆盖换人、不加 WE 开关）。
