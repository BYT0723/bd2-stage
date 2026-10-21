# bd2-stage · 代理提示词

## 新 worktree 必做：素材自举（否则无限 loading）

`assets/spines`、`assets/audios`（约 517MB）被 gitignore，新 worktree 里没有；
bundle 是本地优先，spine 缺失就会卡 loading。建完 slot 后先跑：

```sh
MAIN=/home/walter/Workspace/Github/bd2-stage   # 建 worktree 的源仓库目录
WT=~/Workspace/Worktrees/<新 worktree 名>       # 新 worktree 目录
mkdir -p "$WT/assets"
cp -al "$MAIN"/assets/spines "$WT"/assets/spines
cp -al "$MAIN"/assets/audios "$WT"/assets/audios
cp "$MAIN"/assets/bd2-data.js "$MAIN"/assets/index-Dsqno3tX.js "$MAIN"/assets/index-CqczJBgX.css \
   "$MAIN"/assets/*.png "$MAIN"/assets/*.atlas "$WT"/assets/
cp "$MAIN"/favicon.ico "$MAIN"/preview.gif "$WT"/
cd "$WT" && python3 tools/stamp.py && python3 tools/verify.py
```

- 跨文件系统时 `cp -al` 会失败，改成 `cp -r`。
- 素材是只读输入，不要在 worktree 里跑 `make sync`。
