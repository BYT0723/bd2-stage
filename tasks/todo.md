## Task 1: 三静态聚光灯 scene_d/e/f

**Description:** 在 `tools/gen_background.py` 新增 `scene_spotlight/frost/fest()` + `SCENES["d"/"e"/"f"]`：d 暖单束主推、e 冷单束、f 多向舞台束（暖中央+两侧冷束）。

**Acceptance criteria:**
- [x] `python3 tools/gen_background.py --only def` 成功输出三张 `bd2-spotlight-{stage,frost,fest}-2560x1440.jpg`
- [x] 两次运行字节一致（固定 seed）
- [x] 不改动现有 a/b/c 输出

**Verification:**
- [x] `python3 tools/gen_background.py --only def && ls -lh backgrounds/*spotlight* backgrounds/*frost* backgrounds/*fest*`
- [x] `make check` 通过（或至少 `check_fav_random + test`）

**Dependencies:** None

**Files likely touched:**
- `tools/gen_background.py`

**Estimated scope:** M (1 文件，三函数)

## Task 2: 静态验证 + 预览

**Description:** 生成小预览图并做亮度/scrim 断言，目检构图。

**Acceptance criteria:**
- [x] 中央区域亮度 > 四角均值（三张分别断言）
- [x] 右侧 x>0.66 有压暗
- [x] 预览图 `backgrounds/preview-spotlight-{stage,frost,fest}.jpg` 存在

**Verification:**
- [x] 运行亮度检查脚本输出 PASS
- [x] 人工目检截图确认

**Dependencies:** Task 1

**Files likely touched:**
- `backgrounds/preview-spotlight-*.jpg`（生成物）
- 临时检查脚本（/tmp，不入库）

**Estimated scope:** S (1 file)

## Checkpoint: 静态

- [x] JPG×3 单张 <1MB，构图符合 SPEC，原型经用户目检通过再做视频

## Task 3: 视频生成器脚本

**Description:** 新增 `tools/gen_spotlight_loop.py`（已交付 c66f748；追加 `--format webm|mp4`，默认 webm）。

**Acceptance criteria:**
- [x] `--help` 可用，参数含 `--seconds --fps --size --style --out`（已验证）
- [x] 首尾帧差可输出对比值（`--check-loop`，loop_mse~1e-06）（已验证）
- [x] 不依赖 imageio 等新重型依赖（numpy+PIL+ffmpeg stdin）（已验证）
- [x] `--format webm` 走 libvpx-vp9（`--format mp4` 仍走 libx264）

**Verification:**
- [x] 小尺寸 mp4 试跑 + ffprobe 通过
- [x] 小尺寸 webm 试跑 + ffprobe 通过 + 体积显著小于同内容 mp4

**Dependencies:** Task 1（复用色板/构图常量）

**Files likely touched:**
- `tools/gen_spotlight_loop.py`

**Estimated scope:** S（加一个 flag + 编码分支）

## Task 4: webm×3 输出 + 校验（warm/frost/fest，入库）

**Description:** 生成三款正式循环视频（webm，1080p30，~12s），入库 `backgrounds/`。

**Acceptance criteria:**
- [x] `backgrounds/bd2-spotlight-loop-warm-1080p30.webm` 存在可播，< 200KB
- [x] `backgrounds/bd2-spotlight-loop-frost-1080p30.webm` 同规格，< 200KB
- [x] `backgrounds/bd2-spotlight-loop-fest-1080p30.webm` 同规格，< 200KB
- [x] 首尾帧 MSE < 阈值（--check-loop），中间帧目检正常
- [x] mp4 仅留 /tmp 预览，不入库

**Verification:**
- [x] `ffprobe` 三款逐一通过（width/height/fps/duration）
- [x] 中间帧抽帧目检 + `ls -lh` 体积确认

**Dependencies:** Task 3（--format webm）

**Files likely touched:**
- `backgrounds/bd2-spotlight-loop-*.webm`（新增 3 个小文件）

**Estimated scope:** S（耗时在渲染，不在文件数）

## Task 5: WE 背景双属性接线（merge）

**Description:** `project.json` 只留 `background`（通用）/`background_dark`（深色），图片视频都吃；
`tools/patch.py` 统一解析（深色留空跟通用、通用留空跟内置；视频优先；外来手选不动）；
旧 6 属性（bgImage/bgImageLight/bgImageDark/bgVideo×3）全部移除；
`tests/test_full.py` 标记断言更新（含旧名 absence 守卫）。

**Acceptance criteria:**
- [x] `python3 tools/patch.py` 输出已含新补丁（或 already patched），幂等
- [x] bundle 含 `backgroundDark`、`customBackgroundVideo`、`bd2Video(` 标记，不含旧 6 属性名
- [x] `node --check`（经由 `verify.py`）通过
- [x] JPG 路径行为不变（无视频时无 `<video>` 元素）
- [x] 视频优先于图片；深色留空跟通用；外来手选保持不动（8 case 逻辑验证）

**Verification:**
- [x] `python3 tools/test.py` 全 PASS（含新增断言 RED→GREEN）
- [x] `python3 tools/verify.py` PASS
- [x] `make smoke` 无新异常
- [x] bd2Apply 8 case + bd2Video 6 case 用 bundle 原字节验证通过

**Dependencies:** Task 4（webm 文件就位）

**Files likely touched:**
- `tools/patch.py`、`project.json`、`tests/test_full.py`、`custom/bd2-bg-theme.js`（注释）、bundle（补丁产物）

**Estimated scope:** M

**修过的两个真 bug（repro 复现→修复→验证）：**
- 属性变更死锁：旧守卫把“刚换掉的旧值”当生人拦截，图片→视频等变更永远不生效；
  修：`bd2Bg.ai` 追踪上次解析值。repro：图片→视频→换图→清空，四步全 PASS。
- 深色属性名写错：handler 里是 `backgroundDark`，`project.json` 里是 `background_dark`，
  发来的深色值被静默丢弃；修：统一用 `background_dark`，测试加“project.json file 属性必在 bundle 接线”守卫。
  repro（`--force-dark-mode`）：深色 webm 挂载 + 清空跟通用，全 PASS。

## Checkpoint: 完成

- [x] SPEC 6 条 Success Criteria 全满足
- [x] `make check` + `verify.py` + `smoke` 通过
- [x] 待用户确认：旧 WE 存档的背景选择会重置（属性改名不可避免）；2k/4k/60fps 按需再起
