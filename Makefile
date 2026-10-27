# bd2-stage · BD2 立绘舞台
PY ?= python3

.PHONY: help sync patch verify check smoke all manifest bg

help:
	@echo "make sync      同步上游素材到 assets/（HEAD 比对，必要时 --refresh）+ 生成角色表"
	@echo "make patch     给 bundle 打补丁并刷新 index.html 版本号（幂等）"
	@echo "make verify    校验 manifest hash / 补丁 / 版本号"
	@echo "make check     静态检查 + 全部测试"
	@echo "make smoke     无头浏览器冒烟（抓未捕获异常）"
	@echo "make bg        重新生成配套背景图（backgrounds/）"
	@echo "make all       sync -> patch -> verify -> check -> smoke"

sync:
	$(PY) tools/gen_characters.py
	$(PY) tools/mirror.py

manifest:
	$(PY) tools/manifest.py

patch:
	$(PY) tools/patch.py

verify:
	$(PY) tools/verify.py

check:
	$(PY) tools/check_fav_random.py
	$(PY) tools/test.py

smoke:
	$(PY) tools/smoke.py

bg:
	$(PY) tools/gen_background.py

all: sync patch verify check smoke
