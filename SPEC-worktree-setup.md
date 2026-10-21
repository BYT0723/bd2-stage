# Spec: worktree 素材自举（`make worktree`）

## Objective

为仓库新增 `make worktree NAME=<desc> [TYPE=<type>] [MODE=link|copy]`，
一键建出“可直接加载验证”的隔离 slot，终结“新 worktree 缺 517MB 素材 →
xwallpaper/浏览器里无限 loading”反复出现的问题。

用户故事：开发者在 main 跑一条命令，得到
`~/Workspace/Worktrees/bd2-stage-<type>-<desc>` + `<type>/<desc>` 分支，
素材就绪、`index.html` 哈希已重打，可直接指向 xwallpaper 或浏览器打开验证。

## Tech Stack

- Python 3 标准库（`pathlib`/`shutil`/`subprocess`），与现有 `tools/*.py` 一致
- `git worktree`（底层调用，不重造轮子）
- 默认 `cp -al` 硬链接（coreutils），失败自动退回复制

## Commands

```sh
make worktree NAME=highlight-fix TYPE=fix   # 建 slot + 链素材 + stamp
make worktree NAME=demo MODE=copy           # 强制完整复制素材
make check                                   # 静态检查 + 全部测试（含新增单测）
python3 tools/verify.py                      # 新 slot 素材完整性确认（用户手动跑）
```

## Project Structure

```text
tools/worktree.py   → 新建：建 slot + 素材自举 + stamp 的实现（唯一手写逻辑）
Makefile            → 加 `worktree` target + help 行（薄封装，透传 NAME/TYPE/MODE）
tests/test_worktree.py → 新建：纯函数单测（命名校验、路径推导、素材清单）
tools/test.py       → CASES 追加新单测（只改 1 行附近）
README.md           → 命令表加 1 行（只改文档）
```

## Code Style

沿用现有 `tools/*.py` 风格：文件头 docstring 写用法，`main() -> int` +
`sys.exit(main())`，面向人类输出 Torture：

```python
"""一键建可验证的 worktree（含素材自举）。用法: make worktree NAME=xxx [TYPE=fix] [MODE=link|copy]"""
import pathlib, sys

def slot_dir(repo: str, typ: str, name: str) -> pathlib.Path:
    return pathlib.Path.home() / "Workspace" / "Worktrees" / f"{repo}-{typ}-{name}"
```

命名校验与仓库规范一致：`type ∈ feat|fix|perf|refactor|security|docs|test|chore|hotfix`，
`desc` 小写数字字母下划线/连字符。

## Testing Strategy

- 框架：沿用 `tools/test.py` 聚合（无 pytest 依赖），新 `tests/test_worktree.py`
  只测纯函数：命名合法/非法、slot 目录推导、素材清单完备（spines/audios/
  顶层图片/atlas/favicon），不碰 git、不碰大文件、不联网。
- 集成验证（手动一次）：在 main 跑 `make worktree NAME=smoke TYPE=chore`，
  进新 slot 跑 `make check` + `tools/verify.py`，再 `git worktree remove` 删掉。
- 覆盖率要求：新增分支（目录已存在/分支已存在/跨盘回退/非法名）每个至少一个单测。

## Boundaries

- Always：在 main 且工作区干净时才建 slot；先 `git worktree add` 再链素材再 stamp；
  任何前置失败（目录/分支已存在、素材缺失）直接报错退出，不做半截 slot（建出
  的空 worktree 要自动 `git worktree remove` 回滚）。
- Ask first：改 CI、加第三方依赖、动 `make sync`/`mirror` 的上游同步逻辑。
- Never：覆盖已存在目录/分支；删除用户文件；联网下载素材（只用本地
  `assets/` 硬链接/复制，不跑 sync）；碰 `main/master` 上的提交。

## Success Criteria

1. `make worktree NAME=demo TYPE=chore` 建出 `bd2-stage-chore-demo` + `chore/demo`，
   命令输出 PASS 且退出码 0。
2. 新 slot 内 `python3 tools/verify.py` → `VERIFY OK files=1956`。
3. 新 slot 内 `make check` 全过。
4. `MODE=copy` 在同盘强制完整复制（抽查文件 inode 与 main 不同）。
5. 同名目录或分支已存在时退出码非 0，且不修改任何已有文件，无残留新 worktree。
6. 非法 NAME/TYPE（如大写、空格、TYPE 不在白名单）直接报错，不调用 git。

## Open Questions

无（2026-10-22 已确认：硬链接默认+可退复制；含 stamp 不含 verify；不加清理命令）。

## 决议变更（2026-10-22）

用户反馈完整工具链过重，改用轻量方案：只在仓库根新增 `AGENTS.md` 提示词，
写死 worktree 素材自举步骤（agent 建 slot 时自动读到）。本 spec 的
`make worktree` 工具方案作废，不再进入 Plan/Implement。
