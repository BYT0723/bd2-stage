"""就地给 bundle 打补丁（幂等），然后刷新 index.html 的缓存版本号。

用法: python3 tools/patch.py
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "assets" / "index-Dsqno3tX.js"
# 首次打补丁前手工留一份 pristine（.orig），之后从这里出发，产物怎么改都不怕
ORIG = BUNDLE.with_name(BUNDLE.name + ".orig")

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
    # 直接怼原始 bundle（不再链式改写），这样每条补丁只认 pristine 指纹，幂等好判断。
    (
        "nb={bgImage:`customBackgroundImage`};function rb(e){",
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
        "背景/前景槽位",
    ),
    (
        "if(nb[n]){e[nb[n]]=rb(String(t??``));continue}",
        "if(n==`background`||n==`foreground`){"
        "if(n==`foreground`){"
        "bd2Fg.img=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2FgApply()}else{"
        "bd2Bg.img=rb(String(t??``)),"
        "window.__bd2BgLive=!0,bd2Apply(1)}continue}",
        "背景/前景属性",
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
        "customForegroundImage:null,customForegroundVideo:null,"
        "shadowOffsetX:0,shadowOffsetY:0,layerNames:[]",
        "前景状态位",
    ),
    # 接地影的位移滑块：走 tb 映射（!1 = 原值，不做 /100）
    (
        "panelOpacity:[`panelOpacity`,!0]},nb={}",
        "panelOpacity:[`panelOpacity`,!0],"
        "shadowOffsetX:[`shadowOffsetX`,!1],"
        "shadowOffsetY:[`shadowOffsetY`,!1]},nb={}",
        "接地影位移属性",
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
        "_fv=String(e.customForegroundVideo??``);bd2Light(_h,_fi,_fv);"
        "bd2Shadow()}"
        "catch(_e){}",
        "前景应用",
    ),
    # 接地影：地面层，压在背景之上、人物之下（z-index:5，角色是 z-10）。
    # 灯光层是 screen 加亮、盖在最上面，会把影子洗掉——所以同时在同一位置
    # 给灯光层挖一个 mask 洞，等于“影子挡住了地面光”，物理上也对。
    # 几何：
    #   X 跟人物走（实测：缩放绕画面中心，0.02*scale 是人物中心的漂移）
    #   Y 锚地面线 0.945（背景光池那条线），不跟人物脚底走——
    #     不同角色脚高差很多（站姿 0.92、飘浮姿势更低），按脚估必然偏
    #   shadowOffsetX/Y 是属性面板里的相对微调，单位是画面百分比
    # offset 的符号与直觉相反：正的 roleOffsetX 让画面左移、正的 roleOffsetY 让画面下移。
    (
        "}catch(e){}}}function bd2Light(",
        "}catch(e){}}}function bd2Shadow(){"
        "var bg=document.querySelector(`.bd2-bg-layer`);if(!bg)return;"
        "var h=bg.parentElement;if(!h)return;"
        "var st=sb||{},s=Number(st.roleScale);"
        "if(!Number.isFinite(s)||s<=0)s=1;"
        "var dx=Number(st.roleOffsetX)||0,dy=Number(st.roleOffsetY)||0,"
        "sx=Number(st.shadowOffsetX)||0,sy=Number(st.shadowOffsetY)||0;"
        "var o=h.querySelector(`.bd2-fg-shadow`);"
        "if(!o){o=document.createElement(`div`);o.className=`bd2-fg-shadow`;"
        "o.style.cssText=`position:absolute;z-index:5;pointer-events:none;"
        "background:radial-gradient(closest-side,rgba(0,0,0,.75),"
        "rgba(0,0,0,.40) 40%,rgba(0,0,0,0) 86%)`;h.appendChild(o)}"
        "var cx=(0.5+0.02*s-dx/100+sx/100)*100,"
        "cy=(0.945+sy/100)*100,"
        "bw=0.235*s*100,bh=0.062*s*100;"
        "o.style.left=(cx-bw/2)+`%`;o.style.top=(cy-bh/2)+`%`;"
        "o.style.width=bw+`%`;o.style.height=bh+`%`;"
        "var l=h.querySelector(`.bd2-fg-light`);"
        "if(l){var m=`radial-gradient(ellipse `+(bw*1.0)+`% `+(bh*1.0)+`% at `"
        "+cx+`% `+cy+`%,rgba(0,0,0,0) 0%,rgba(0,0,0,.40) 40%,#000 86%)`;"
        "l.style.maskImage=m;l.style.webkitMaskImage=m}}"
        "function bd2Light(",
        "接地影",
    ),
    # 面板里拖缩放/位置不走属性下发，得挂在同一个 watcher 上
    (
        "Oi(()=>[h.roleScale,h.roleOffsetX,h.roleOffsetY],()=>{h.wallpaperMode&&(lr(),fr())})",
        "Oi(()=>[h.roleScale,h.roleOffsetX,h.roleOffsetY,"
        "h.shadowOffsetX,h.shadowOffsetY],()=>{"
        "h.wallpaperMode&&(lr(),fr()),bd2Shadow()})",
        "接地影跟随缩放",
    ),
]

def normalize(js):
    """先把本脚本打过的补丁按反序撤回，得到 pristine。

    bundle 是 gitignore 的构建产物，没有 pristine 副本可拿；如果不先归一化，
    链式补丁在“已打过补丁”的文件上会因为中间态被后续补丁改写而认不出指纹。
    撤回是幂等的：没打过就跳过。
    """
    for old, new, _label in reversed(PATCHES):
        if js.count(new) == 1:
            js = js.replace(new, old)
    return js


def main():
    js = (ORIG if ORIG.exists() else BUNDLE).read_text()
    js = normalize(js)
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
