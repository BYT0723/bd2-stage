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
    # 语音元素复用 + 不预加载：上游每次换人都 new 3 个 Audio 并 load()，
    # xwallpaper 的音频 shim 会强引用所有 detached 元素，长会话里换人越多
    # 留得越多（换壁纸时还要成批销毁 GStreamer pipeline）。这里固定复用 3 个
    # 元素、preload=none，点击时才加载；监听器改为属性赋值，避免复用时叠加。
    (
        "function Vn(){let e=Ln();if(e&&I?.key===e.key||(Bn(),!e))return;"
        "let t=e.urls.map(e=>{let t=new Audio;return t.preload=`auto`,t.src=e,"
        "t.volume=Wn(h.volume),t.addEventListener(`ended`,()=>{L===t&&(L=null)}),"
        "t.addEventListener(`error`,()=>{let n=t.error?t.error.code:`unknown`;"
        "console.warn(`[wallpaper] 语音加载失败（code=${n}）：${e}`)}),t.load(),t});"
        "I={key:e.key,clips:t}}",
        "var bd2AudioPool=[];function Vn(){let e=Ln();"
        "if(e&&I?.key===e.key||(Bn(),!e))return;"
        "let t=e.urls.map((e,i)=>{let t=bd2AudioPool[i]||(bd2AudioPool[i]=new Audio);"
        "return t.onended=()=>{L===t&&(L=null)},"
        "t.onerror=()=>{let n=t.error?t.error.code:`unknown`;"
        "console.warn(`[wallpaper] 语音加载失败（code=${n}）：${e}`)},"
        "t.preload=`none`,t.src=e,t.volume=Wn(h.volume),t});"
        "I={key:e.key,clips:t}}",
        "语音池/不预加载",
    ),
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
