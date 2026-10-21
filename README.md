# bd2-stage · BD2 立绘舞台

Brown Dust 2 Live2D 壁纸：234 个角色全本地加载，支持收藏 / 随机 / 定时轮播。

> EN: A Brown Dust 2 Live2D wallpaper with 234 local characters, favorites, shuffle and timer autoplay. Viewer core by [Jelosus2/BD2-L2D-Viewer](https://github.com/Jelosus2/BD2-L2D-Viewer).

<!-- 预览图：本地 preview.gif 是 Steam 资源（不入库），公开展示时请自行截图放到 docs/ 下并在此引用 -->

## 功能

- 234 角色，点击人物会做动作、说语音（中 / 日 / 英三语）
- 按火 / 水 / 风 / 光 / 暗属性筛选
- ❤ 收藏：列表项右侧点心只收藏不切换；属性行末图标进独立收藏列表（自带分页）
- 🎲 随机：洗牌袋保证一轮内不重复，随机后自动跳到该角色所在页
- ⏱ 定时：5 分 / 15 分 / 1 小时三档，面板打开时暂停，关闭后继续
- 悬浮球选人 + 右键属性调位置 / 缩放 / 背景 / 音量 / 主题色
- 语音按需加载 + 3 路复用，不再换人堆积 Audio 元素

## 用法

### 直接预览

```sh
python3 -m http.server
# 打开 http://localhost:8000
```

### Wallpaper Engine（Windows）

把本目录作为壁纸包导入即可，`project.json` 已配好属性面板。

### xwallpaper（Linux）

```sh
xwallpaper --output all /path/to/bd2-stage/index.html
```

> xwallpaper 会摘除页面键盘事件，间隔用点击循环档位代替输入框。

## 素材说明

素材不入库，`git clone` 后恢复：

```sh
make sync    # 同步上游素材到 assets/（约 517MB）+ 生成角色表
make patch   # bundle 打补丁 + 刷新版本号
make verify  # 校验 manifest / 补丁 / 版本号
```

| 入库 | 不入库（可重建） |
| ---- | ---------------- |
| `custom/` `templates/` `tools/` `tests/` `Makefile` `index.html` `project.json` | `assets/spines/` `assets/audios/` `assets/index-*.js/.css` `assets/bd2-*.js` `preview.gif` `favicon.ico` |

## 开发

```sh
make check   # 静态检查 + 测试
make smoke   # 无头 Chromium 冒烟
make all     # sync -> patch -> verify -> check -> smoke
```

bundle 补丁是字符串级（指纹不符中止）：全角色按本地素材处理、Logo 默认关闭、语音元素池化。

## 版权

- 角色立绘 / 语音版权归 NEOWIZ / GAMFS 所有，本仓库不含游戏资源
- 网页 Viewer 部分 © Jelosus2（开源），壁纸外挂与工程部分由本仓库作者维护
