## Task 1: 转盘外挂

**Description:** 新增 `custom/bd2-carousel.js`：同步快照旧 canvas，随机方向，
旧人反向 3D 转出，新人从另一侧转入；连点清理、3 秒兜底、reduced-motion 跳过。

**Acceptance criteria:**
- [x] 暴露 `window.__bd2CarouselSwap` / `__bd2CarouselEnter` / `__bd2Carousel`
- [x] 快照用 `drawImage`，不用 `toDataURL`，不联网
- [x] 方向每次独立随机，新旧方向相反
- [x] 入场等 2 帧；3 秒兜底显示
- [x] 结束时移除快照、恢复容器样式和 hit layer

**Verification:**
- [x] `node --check custom/bd2-carousel.js`
- [x] `python3 tools/test.py` 中 `test_script_contract` PASS

**Dependencies:** None

**Files likely touched:**
- `custom/bd2-carousel.js`

**Estimated scope:** M (1 文件)

## Task 2: bundle 钩子与挂载

**Description:** `tools/patch.py` 在换人 watcher 和 Spine success 回调各插一个
try/catch 钩子；`templates/index.html` 挂载脚本；`tools/stamp.py` 加入 ASSETS。

**Acceptance criteria:**
- [x] `python3 tools/patch.py` 幂等，反复跑字节一致
- [x] bundle 含 `__bd2CarouselSwap` / `__bd2CarouselEnter`
- [x] `index.html` 引用带内容哈希的 `bd2-carousel.js`

**Verification:**
- [x] `python3 tools/patch.py && python3 tools/verify.py`
- [x] `node --check assets/index-Dsqno3tX.js`

**Dependencies:** Task 1

**Files likely touched:**
- `tools/patch.py`
- `templates/index.html`
- `tools/stamp.py`

**Estimated scope:** S

## Task 3: 静态校验

**Description:** 新增 `tests/test_carousel.py`，并让 `verify.py`、`check_fav_random.py`、
`tests/test_full.py`、`tests/test_fav_random.py` 覆盖钩子、脚本和版本号。

**Acceptance criteria:**
- [x] 新测试先 RED（文件/钩子缺失），实现后 GREEN
- [x] `tools/test.py` 全 PASS
- [x] `verify.py` 校验 bundle 两个钩子
- [x] `make check` 通过

**Verification:**
- [x] `python3 tools/test.py`
- [x] `python3 tools/verify.py`
- [x] `make check`

**Dependencies:** Task 2

**Files likely touched:**
- `tests/test_carousel.py`
- `tests/test_full.py`
- `tests/test_fav_random.py`
- `tools/verify.py`
- `tools/check_fav_random.py`
- `tools/test.py`

**Estimated scope:** M

## Task 4: 文档与冒烟

**Description:** README 功能列表补一行，新增 SPEC / 计划 / 本 todo；
`make smoke` 确认页面无未捕获异常。

**Acceptance criteria:**
- [x] README 有转盘动画说明
- [x] `SPEC-character-carousel.md`、`tasks/plan-character-carousel.md` 存在
- [x] 不覆盖现有 `tasks/plan.md` / `tasks/todo.md`
- [x] smoke 无新异常

**Verification:**
- [x] `make smoke`
- [x] `git diff --stat` 检查无无关文件

**Dependencies:** Task 3

**Files likely touched:**
- `README.md`
- `SPEC-character-carousel.md`
- `tasks/plan-character-carousel.md`
- `tasks/todo-character-carousel.md`

**Estimated scope:** S

## Checkpoint: 完成

- [x] 手动目检四种入口的转盘动效
- [x] 连点 / 加载失败 / reduced-motion 边界确认
- [x] `python3 tools/test.py`、`python3 tools/verify.py`、`make smoke` 通过
