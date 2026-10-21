# bd2-stage · BD2 立绘舞台

Brown Dust 2 的 Live2D 壁纸：素材全本地 + 收藏 / 随机 / 定时轮播。

这个目录**既是壁纸包，也是本项目的 git 仓库**：xwallpaper 直接加载它，
`make` 在这里改代码、同步素材、验证状态。

```
index.html                  由 templates/index.html 生成，?v= 为内容哈希
project.json                壁纸属性（已移除 logoScale）
assets/                     素材 517MB（绝大多数被 gitignore）
  spines/ audios/           234 角色 / 1956 文件，可由 make sync 拉回
  index-Dsqno3tX.js         上游 bundle，被 make patch 打两处补丁
  bd2-data.js               角色表（gen_characters.py 生成，stamp.py 安装）
  bd2-fav-random.js         收藏 / 随机 / 定时随机外挂
custom/                     外挂源码（唯一手改的运行时文件）
templates/                  index.html 与 project.json 模板
tools/                      同步、补丁、校验、冒烟
tests/                      测试
tasks/                      manifest.json（期望 hash）、bundle 原始底稿、角色顺序
```

## 命令

```
make sync      # 上游素材同步到 assets/（HEAD 比对；--refresh 强制）+ 生成角色表
make patch     # bundle 打补丁（幂等）+ 刷新 index.html 版本号
make verify    # 校验 manifest hash / 补丁 / 版本号
make check     # 静态检查 + 测试
make smoke     # 无头 Chromium 冒烟（抓未捕获异常、确认 UI 挂载）
make all       # 全流程
```

## bundle 补丁（字符串级，指纹不符会中止）

| 原文 | 改为 | 目的 |
|---|---|---|
| `function T_(e){return w_.has(e)}` | `return!0` | 全部角色按本地素材处理（缺失仍回退在线） |
| `logoVisible:!0` | `!1` | Logo 默认关闭 |

## 外挂功能

- 角色条目右侧心形：收藏（只收藏，不切换角色），存 `localStorage`。
- 属性行末尾的收藏图标：进入独立收藏列表（自带分页，只有收藏项）。
- `🎲`：从当前候选集随机；洗牌袋保证一轮内不重复。
- `⏱`：定时随机，档位 5 分 / 15 分 / 1 小时；面板打开时暂停并显示“面板关闭后计时”。
  换人直接写 Pinia `characterStore`，所以面板关闭也能换；取不到 store 才回退点列表。

## 已知限制

- xwallpaper 会摘除页面键盘事件（`src/web.c` `web_drop_key_mask`），面板内的输入框
  无法键入；因此间隔控件是点击循环，而不是输入框。
- 素材不入库：`git clone` 后需 `make sync` 才能恢复 517MB 素材（或直接从 Steam 重下）。

## 素材与仓库的边界

| 入库 | 不入库（可重建） |
|---|---|
| `custom/`、`templates/`、`tools/`、`tests/`、`Makefile`、`index.html`、`project.json` | `assets/spines/`、`assets/audios/`、`assets/index-*.js/.css`、`assets/bd2-*.js`、`preview.gif` |

`tasks/manifest.json` 入库：它记录每个素材的 sha256，`make verify` 据此判断
“本地是否仍与上游一致”。
