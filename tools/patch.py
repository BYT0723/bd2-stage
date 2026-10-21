"""就地给 bundle 打补丁（幂等），然后刷新 index.html 的缓存版本号。

用法: python3 tools/patch.py
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "assets" / "index-Dsqno3tX.js"

PATCHES = [
    # 所有角色按本地素材处理（缺失时 bundle 自身仍会回退在线）
    ("function T_(e){return w_.has(e)}", "function T_(e){return!0}", "本地素材"),
    # Logo 默认关闭
    ("logoVisible:!0", "logoVisible:!1", "关闭 Logo"),
]

def main():
    js = BUNDLE.read_text()
    changed = []
    for old, new, label in PATCHES:
        if old in js:
            js = js.replace(old, new)
            changed.append(label)
        elif new not in js:
            print(f"FAIL bundle 指纹变化（{label}），停下人工复核补丁点")
            return 1
    if changed:
        BUNDLE.write_text(js)
        print("patched: " + ", ".join(changed))
    else:
        print("already patched")

    import stamp
    stamp.main()
    return 0

if __name__ == "__main__":
    sys.exit(main())
