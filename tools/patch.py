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
    # 背景跟随系统 light/dark：bgImageLight / bgImageDark 两个属性存两张图，
    # 按 prefers-color-scheme 选，系统切换时实时换（不重载）。
    # 手动选的图（既不是内置两张、也不是空）保持不动；bgImage 仍是最高的手动覆盖。
    (
        "nb={bgImage:`customBackgroundImage`};function rb(e){",
        "nb={bgImage:`customBackgroundImage`};"
        "var bd2Bg={light:``,dark:``,manual:``},"
        "BD2_BG_AUTO=[`./backgrounds/bd2-parchment-2560x1440.jpg`,"
        "`./backgrounds/bd2-starlit-vault-2560x1440.jpg`];"
        "function bd2Dark(){try{return matchMedia(`(prefers-color-scheme: dark)`).matches}"
        "catch(e){return!1}}"
        "function bd2Apply(){if(!sb)return;var c=String(sb.customBackgroundImage||``);"
        "if(!bd2Bg.manual&&c&&BD2_BG_AUTO.indexOf(c)<0&&c!==bd2Bg.light&&c!==bd2Bg.dark)return;"
        "var d=bd2Dark(),p=bd2Bg.manual||bd2Bg[d?`dark`:`light`]||BD2_BG_AUTO[d?1:0];"
        "if(!p||p===c)return;sb.customBackgroundImage=p;try{ib()}catch(e){}}"
        "try{matchMedia(`(prefers-color-scheme: dark)`).addEventListener(`change`,bd2Apply)}"
        "catch(e){}function rb(e){",
        "浅色/深色背景",
    ),
    (
        "if(nb[n]){e[nb[n]]=rb(String(t??``));continue}",
        "if(n==`bgImageLight`||n==`bgImageDark`){"
        "bd2Bg[n===`bgImageLight`?`light`:`dark`]=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2Apply();continue}"
        "if(nb[n]){e[nb[n]]=rb(String(t??``));"
        "if(n===`bgImage`){bd2Bg.manual=String(e[nb[n]]||``),bd2Apply()}continue}",
        "浅色/深色背景属性",
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
