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
    # 背景单属性：background，图片视频都吃；前景单属性：foreground。
    # 属性下发走 bd2Apply(1)（force）：必须压过 localStorage 里的旧手选值。
    # ai 追踪上次解析出的图片值，避免值变更后旧值被当生人。
    (
        "nb={};"
        "var bd2Bg={img:``,dark:``,ai:``},"
        "BD2_BG_AUTO=[`./backgrounds/bd2-parchment-2560x1440.jpg`,"
        "`./backgrounds/bd2-starlit-vault-2560x1440.jpg`];"
        "function bd2Dark(){try{return matchMedia(`(prefers-color-scheme: dark)`).matches}"
        "catch(e){return!1}}"
        "function bd2Apply(force){if(!sb)return;"
        "var c=String(sb.customBackgroundImage||``),v=String(sb.customBackgroundVideo||``);"
        "if(!force&&c&&BD2_BG_AUTO.indexOf(c)<0&&c!==bd2Bg.ai&&c!==bd2Bg.img&&c!==bd2Bg.dark)return;"
        "var d=bd2Dark(),"
        "w=d?(bd2Bg.dark||bd2Bg.img||BD2_BG_AUTO[1]):(bd2Bg.img||BD2_BG_AUTO[0]);"
        "if(/\\.(webm|mp4)(\\?.*)?$/i.test(w)){"
        "if(v!==w)sb.customBackgroundVideo=w;"
        "if(c)sb.customBackgroundImage=``}"
        "else{bd2Bg.ai=w;if(w!==c)sb.customBackgroundImage=w;"
        "if(v)sb.customBackgroundVideo=``}"
        "try{ib()}catch(e){}}"
        "try{matchMedia(`(prefers-color-scheme: dark)`).addEventListener(`change`,bd2Apply)}"
        "catch(e){}function rb(e){",
        "nb={};"
        "var bd2Bg={img:``,ai:``};var bd2Fg={img:``};"
        "var BD2_BG_AUTO=`./backgrounds/bd2-starlit-vault-2560x1440.jpg`;"
        "function bd2Apply(force){if(!sb)return;"
        "var c=String(sb.customBackgroundImage||``),v=String(sb.customBackgroundVideo||``);"
        "if(!force&&c&&c!==BD2_BG_AUTO&&c!==bd2Bg.ai&&c!==bd2Bg.img)return;"
        "var w=bd2Bg.img||BD2_BG_AUTO;"
        "if(/\\.(webm|mp4)(\\?.*)?$/i.test(w)){"
        "if(v!==w)sb.customBackgroundVideo=w;"
        "if(c)sb.customBackgroundImage=``}"
        "else{bd2Bg.ai=w;if(w!==c)sb.customBackgroundImage=w;"
        "if(v)sb.customBackgroundVideo=``}"
        "try{ib()}catch(e){}}"
        "function bd2FgApply(){if(!sb)return;"
        "var w=bd2Fg.img||``;"
        "var c=String(sb.customForegroundImage||``),"
        "v=String(sb.customForegroundVideo||``);"
        "if(/\\.(webm|mp4)(\\?.*)?$/i.test(w)){"
        "if(v!==w)sb.customForegroundVideo=w;"
        "if(c)sb.customForegroundImage=``}"
        "else{if(w!==c)sb.customForegroundImage=w;"
        "if(v)sb.customForegroundVideo=``}"
        "try{ib()}catch(e){}}"
        "function rb(e){",
        "单背景+前景槽位",
    ),
    (
        "if(n==`background`||n==`background_dark`){"
        "bd2Bg[n==`background`?`img`:`dark`]=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2Apply(1);continue}",
        "if(n==`background`){"
        "bd2Bg.img=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2Apply(1);continue}",
        "单背景属性",
    ),
    # 独立状态位 customBackgroundVideo（不复用图片位，避免 <img>
    # 误加载 webm 触发 onerror 把背景自清）。前景同理走 customForegroundVideo。
    (
        "customBackgroundImage:null,layerNames:[]",
        "customBackgroundImage:null,customBackgroundVideo:null,layerNames:[]",
        "视频背景状态位",
    ),
    (
        "}catch{}}var ab={",
        "}catch{}}function bd2Video(r,a){var m=r.querySelector(`video`),"
        "ok=/\\.(webm|mp4)(\\?.*)?$/i.test(a);"
        "if(!ok){if(m){try{m.pause()}catch(e){}m.remove()}return}"
        "if(!m){m=document.createElement(`video`);m.muted=!0;m.loop=!0;m.autoplay=!0;"
        "m.setAttribute(`playsinline`,``);"
        "m.onerror=function(){try{m.remove()}catch(e){}};"
        "m.style.cssText=`position:absolute;inset:0;width:100%;height:100%;"
        "object-fit:cover;pointer-events:none`;r.appendChild(m)}"
        "if(m.getAttribute(`src`)!==a){m.setAttribute(`src`,a);"
        "try{var p=m.play();p&&p.catch&&p.catch(function(){"
        "try{m.remove()}catch(e){}})}catch(e){}}}"
        "var ab={",
        "视频背景元素",
    ),
    (
        "let a=String(e.customBackgroundImage??``);",
        "let a=String(e.customBackgroundImage??``),"
        "v=String(e.customBackgroundVideo??``);bd2Video(r,v);",
        "视频背景应用",
    ),
    (
        "customBackgroundImage:null,customBackgroundVideo:null,layerNames:[]",
        "customBackgroundImage:null,customBackgroundVideo:null,"
        "customForegroundImage:null,customForegroundVideo:null,layerNames:[]",
        "前景状态位",
    ),
    (
        "if(n==`background`){"
        "bd2Bg.img=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2Apply(1);continue}",
        "if(n==`background`||n==`foreground`){"
        "if(n==`foreground`){"
        "bd2Fg.img=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2FgApply()}else{"
        "bd2Bg.img=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2Apply(1)}continue}",
        "前景属性接线",
    ),
    (
        "}catch(e){}}}var ab={",
        "}catch(e){}}}function bd2Light(h,img,vid){"
        "if(!h)return;"
        "var o=h.querySelector(`.bd2-fg-light`);"
        "if(!img&&!vid){if(o){try{var q=o.querySelector(`video`);q&&q.pause()}"
        "catch(e){}o.remove()}return}"
        "if(!o){o=document.createElement(`div`);o.className=`bd2-fg-light`;"
        "o.style.cssText=`position:absolute;inset:0;z-index:20;pointer-events:none;"
        "mix-blend-mode:screen;opacity:.6;overflow:hidden`;h.appendChild(o)}"
        "bd2Video(o,vid);"
        "var cur=o.getAttribute(`data-img`)||``;"
        "if((img||``)!==cur){if(img){"
        "o.style.backgroundImage=`url(\"${img}\")`;"
        "o.style.backgroundSize=`cover`;o.style.backgroundPosition=`center`;"
        "o.setAttribute(`data-img`,img)}"
        "else{o.style.backgroundImage=`none`;o.removeAttribute(`data-img`)}}}"
        "var ab={",
        "前景灯光元素",
    ),
    (
        "v=String(e.customBackgroundVideo??``);bd2Video(r,v);",
        "v=String(e.customBackgroundVideo??``);bd2Video(r,v);"
        "try{var _h=r.parentElement||r.parentNode,"
        "_fi=String(e.customForegroundImage??``),"
        "_fv=String(e.customForegroundVideo??``);bd2Light(_h,_fi,_fv)}catch(_e){}",
        "前景应用",
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
