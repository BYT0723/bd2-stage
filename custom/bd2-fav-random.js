/* bd2-fav-random.js v13 — 收藏❤ 独立列表 + 随机🎲（DOM 外挂，不碰 bundle）。
 * 收藏是独立列表（自建 UI+分页），与属性平级；点心只收藏不选中。 */
(function () {
  'use strict';
  var LS_FAVS = 'bd2-wallpaper-favs';
  var LS_FAVONLY = 'bd2-wallpaper-favonly';
  var ELEMS = ['fire', 'water', 'wind', 'light', 'dark', 'none'];
  var LANGS = ['zh', 'ja', 'en'];
  var TAGS = ['（本地）', '（ローカル）', ' (local)'];
  var PAGE = 6;
  var SEL = {
    panel: '.wc-panel', list: '.wc-list', item: '.wc-list__item',
    elem: '.wc-elem:not(.bd2-fav)',
    seg: '.wc-seg__btn',
    page: '.wc-listnav__page', navBtn: '.wc-listnav__btn'
  };
  var DB = null;
  var IDX = { zh: {}, ja: {}, en: {} };   // 名字→id，启动时建一次
  var favs = new Set();
  var favOnly = false;
  var pendingClear = false;
  var favPage = 1;
  var navigating = false;
  var lastFavKey = '';
  var bag = [], bagKey = '', lastPick = '';   // 随机洗牌袋：一轮内不重复
  var LS_TIMER = 'bd2-wallpaper-timer';
  var LS_SECS = 'bd2-wallpaper-timer-secs';
  var timerOn = false, timerSecs = 60, timerHandle = null, timerBusy = false;
  var timerNextAt = 0, timerUi = null;
  var TIMER_STEPS = [300, 900, 3600];   // 5 分 / 15 分 / 1 小时（秒）
  try {
    favs = new Set(JSON.parse(localStorage.getItem(LS_FAVS) || '[]'));
    favOnly = localStorage.getItem(LS_FAVONLY) === '1';
    timerOn = localStorage.getItem(LS_TIMER) === '1';
    var sec = parseInt(localStorage.getItem(LS_SECS) || '', 10);
    timerSecs = TIMER_STEPS.indexOf(sec) >= 0 ? sec : TIMER_STEPS[0];   // 旧值归一到档位
  } catch (e) {}
  function save() {
    try {
      localStorage.setItem(LS_FAVS, JSON.stringify(Array.from(favs)));
      localStorage.setItem(LS_FAVONLY, favOnly ? '1' : '');
      localStorage.setItem(LS_TIMER, timerOn ? '1' : '');
      localStorage.setItem(LS_SECS, String(timerSecs));
    } catch (e) {}
  }
  function style() {
    if (document.getElementById('bd2-style')) return;
    var st = document.createElement('style');
    st.id = 'bd2-style';
    st.textContent = [
      '.bd2-heart{margin-left:auto;flex:0 0 auto;cursor:pointer;pointer-events:auto!important;',
      'position:relative;z-index:1;line-height:0;padding:2px 4px;',
      'background:none;border:none;color:inherit;opacity:.6}',
      '.bd2-heart:hover{opacity:1}',
      '.bd2-heart svg{width:15px;height:15px;display:block;fill:none;stroke:currentColor;stroke-width:2}',
      '.bd2-heart.on{opacity:1;color:#f43f5e}',
      '.bd2-heart.on svg{fill:#f43f5e;stroke:#9f1239}',
      '.wc-list__item>.wc-list__name{flex:1 1 auto;min-width:0}',
      '.bd2-fav{flex:1 1 0;min-width:0;aspect-ratio:1/1;padding:6px;cursor:pointer;',
      'display:flex;align-items:center;justify-content:center;',
      'background:#1c1710cc;border:1px solid #d9b26a61;border-radius:34%;color:#e6dcc4}',
      '.bd2-fav:hover{background:#3c301e}',
      '.bd2-fav.wc-elem--active,.bd2-fav.on{background:#d9b26a;border:2px solid #d9b26a;',
      'color:#1c1710;padding:5px}',
      '.bd2-fav svg{width:19px;height:19px;display:block;fill:none;stroke:currentColor;stroke-width:2}',
      '.bd2-fav.wc-elem--active svg,.bd2-fav.on svg{fill:#f43f5e;stroke:#9f1239}',
      '.bd2-fav.wc-elem{font-size:17px;line-height:1;color:inherit;cursor:pointer}',
      '.bd2-tools{display:flex;align-items:center;gap:6px;margin:0 0 8px}',
      '.bd2-tools .bd2-random{flex:0 0 auto;width:44px;cursor:pointer;',
      'border:1px solid #d9b26a66;border-radius:999px;background:#1c1710bf;',
      'color:#f2ead8;padding:8px 0;font-size:15px;line-height:1;white-space:nowrap}',
      '.bd2-tools .bd2-random:hover{background:#3c301e}',
      '.bd2-favlist{background:#1c171099;border:1px solid #d9b26a4d;border-radius:18px;color:#f2ead8;',
      'display:flex;flex-direction:column;gap:4px;margin-bottom:6px;padding:6px}',
      '.bd2-fitem{display:flex;align-items:center;gap:7px;width:100%;cursor:pointer;',
      'text-align:left;color:inherit;white-space:nowrap;overflow:hidden;',
      'background:0 0;border:1px solid transparent;border-radius:999px;padding:6px 9px;font-size:13px}',
      '.bd2-fitem:hover{background:#7f7f7f29}',
      '.bd2-fitem--active{background:#d9b26a;border-color:#d9b26a;color:#1c1710;font-weight:700}',
      '.bd2-fname{margin-left:2px;overflow:hidden;text-overflow:ellipsis}',
      '.bd2-fnav{display:flex;align-items:center;gap:6px;margin-bottom:6px}',
      '.bd2-fnav span{opacity:.75;font-size:11px;flex:none}',
      '.bd2-fnav button{cursor:pointer;flex:none;width:30px;height:30px;color:#f2ead8;',
      'display:flex;align-items:center;justify-content:center;',
      'background:#1c1710eb;border:1px solid #d9b26ae6;border-radius:50%;padding:0}',
      '.bd2-fnav button:hover{background:#3c301ef2}',
      '.bd2-fnav button:active{background:#d9b26a47}',
      '.bd2-tri{pointer-events:none;border-style:solid;width:0;height:0;display:block}',
      '.bd2-tri--left{border-width:6px 9px 6px 0;border-color:transparent #f2ead8 transparent transparent}',
      '.bd2-tri--right{border-width:6px 0 6px 9px;border-color:transparent transparent transparent #f2ead8}',
      '.bd2-empty{opacity:.7;font-size:12px;text-align:center;padding:8px 0}',
      '.wc-foldrow{display:none!important}',
      '.wp-logo{display:none!important}',
      '.bd2-tools .bd2-timer-toggle{flex:1 1 0;min-width:0;cursor:pointer;',
      'border:1px solid #d9b26a66;border-radius:999px;background:#1c1710bf;color:#f2ead8;',
      'padding:8px 6px;font-size:13px;white-space:nowrap}',
      '.bd2-tools .bd2-timer-toggle.on{border-color:#d9b26a;color:#1c1710;background:#d9b26a;font-weight:700}',
      '.bd2-tools .bd2-timer-toggle:hover{background:#3c301e}',
      '.bd2-tools .bd2-timer-toggle.on:hover{background:#d9b26a}',
      '.bd2-tools .bd2-timer-secs{flex:0 0 auto;cursor:pointer;white-space:nowrap;',
      'color:#f2ead8;background:#1c1710bf;border:1px solid #d9b26a80;border-radius:999px;',
      'padding:8px 10px;font-size:12px}',
      '.bd2-tools .bd2-timer-secs:hover{background:#3c301e}',
      '.bd2-toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:3000;',
      'background:#1c1710f2;color:#f6e3b4;border:1px solid #d9b26a;padding:8px 16px;',
      'border-radius:999px;font-size:13px;pointer-events:none}'
    ].join('');
    document.head.appendChild(st);
  }
  function heartSvg(on) {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    if (on) svg.setAttribute('data-fill', '1');
    var path = document.createElementNS(ns, 'path');
    path.setAttribute('d', 'M12 20.4 4.6 13a4.6 4.6 0 0 1 6.5-6.5l.9.9.9-.9A4.6 4.6 0 0 1 19.4 13z');
    svg.appendChild(path);
    return svg;
  }
  function setHeart(el, on) {
    var has = el.querySelector('svg');
    if (!has) { el.appendChild(heartSvg(on)); return; }
    var filled = has.getAttribute('data-fill') === '1';
    if (filled !== on) {
      if (on) has.setAttribute('data-fill', '1'); else has.removeAttribute('data-fill');
    }
  }
  function toast(msg) {
    var t = document.createElement('div');
    t.className = 'bd2-toast'; t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 1800);
  }
  function curLang() {
    var btns = Array.prototype.slice.call(document.querySelectorAll(SEL.seg));
    var i = btns.findIndex(function (b) { return b.classList.contains('wc-seg__btn--active'); });
    return LANGS[i] || 'zh';
  }
  function cleanText(btn) {
    var t = (btn.textContent || '').replace(/[❤️♡]/g, '').trim();
    TAGS.forEach(function (tag) { if (t.endsWith(tag)) t = t.slice(0, -tag.length).trim(); });
    return t;
  }
  function buildIndex() {
    IDX = { zh: {}, ja: {}, en: {} };
    Object.keys(DB.names).forEach(function (id) {
      var n = DB.names[id];
      if (n.zh && !IDX.zh[n.zh]) IDX.zh[n.zh] = id;
      if (n.ja && !IDX.ja[n.ja]) IDX.ja[n.ja] = id;
      if (n.en && !IDX.en[n.en]) IDX.en[n.en] = id;
    });
  }
  function idFromButton(btn) {
    if (!DB) return null;
    var t = cleanText(btn);
    if (t) {
      var langs = [curLang(), 'zh', 'ja', 'en'];
      for (var k = 0; k < langs.length; k++) {
        var hit = IDX[langs[k]][t];
        if (hit) return hit;
      }
    }
    // 兜底：按行位置映射（文本改名/截断时仍可用）
    var row = pageButtons().indexOf(btn);
    if (row < 0) return null;
    var ids = listIds();
    return ids[(curPage() - 1) * PAGE + row] || null;
  }
  function activeElem() {
    var btns = Array.prototype.slice.call(document.querySelectorAll(SEL.elem));
    var i = btns.findIndex(function (b) { return b.classList.contains('wc-elem--active'); });
    return i < 0 ? null : ELEMS[i] || null;
  }
  /* 列表真实顺序＝store.characters（DB.order 与之不同：NPC 在最前） */
  function listIds() {
    if (!DB) return [];
    var ids = null;
    var st = piniaCharStore();
    if (st && st.characters && st.characters.length) {
      ids = st.characters.map(function (c) { return c.id; });
    }
    if (!ids || !ids.length) ids = DB.order.slice();
    var el = activeElem();
    return el ? ids.filter(function (id) { return DB.elem[id] === el; }) : ids;
  }
  function favIds() {
    if (!DB) return [];
    return DB.order.filter(function (id) { return favs.has(id); });
  }
  function candidates() { return favOnly ? favIds() : listIds(); }
  /* 页码文案随语言变（第 a/b 页 · a/b ページ · Page a of b），按两个数字取 */
  function pageNums() {
    var el = document.querySelector(SEL.page);
    var m = el && /(\d+)\D+(\d+)/.exec(el.textContent || '');
    return m ? { cur: Math.max(1, parseInt(m[1], 10)), total: Math.max(1, parseInt(m[2], 10)) }
             : { cur: 1, total: 1 };
  }
  function totalPages() { return pageNums().total; }
  function curPage() { return pageNums().cur; }
  function pageButtons() { return Array.prototype.slice.call(document.querySelectorAll(SEL.item)); }
  function curChar() {
    var m = /[?&]char=([^&]*)/.exec(location.search || '');
    return m ? decodeURIComponent(m[1]) : '';
  }
  function displayOf(id) {
    if (!DB || !DB.names[id]) return null;
    var L = curLang();
    return DB.names[id][L] || DB.names[id].en;
  }
  function waitUntil(pred, timeout) {
    return new Promise(function (resolve) {
      var t0 = Date.now();
      (function poll() {
        var ok = false;
        try { ok = !!pred(); } catch (e) {}
        if (ok) return resolve(true);
        if (Date.now() - t0 > (timeout || 600)) return resolve(false);
        setTimeout(poll, 16);
      })();
    });
  }
  function navBtns() { return Array.prototype.slice.call(document.querySelectorAll(SEL.navBtn)); }
  async function gotoPage(target) {
    if (curPage() === target) return true;
    var bs0 = navBtns();
    if (bs0.length < 2) return false;
    var total = totalPages();
    var cur0 = curPage();
    var fwd = ((target - cur0) % total + total) % total;
    var back = total - fwd;
    var n = Math.min(fwd, back);
    if (n > 200) return false;
    var btn = fwd <= back ? bs0[1] : bs0[0];
    for (var i = 0; i < n; i++) btn.click();          // 先试批量连点（一次渲染）
    if (await waitUntil(function () { return curPage() === target; }, 1500)) return true;
    // 兜底：一步一页，每步都等到页码真的变了再继续（慢机器也稳）
    for (var g = 0; g < total + 3; g++) {
      var cur = curPage();
      if (cur === target) return true;
      var bs = navBtns();
      if (bs.length < 2) return false;
      var f2 = ((target - cur) % total + total) % total;
      (f2 <= total - f2 ? bs[1] : bs[0]).click();
      var prev = cur;
      if (!(await waitUntil(function () { return curPage() !== prev; }, 2000))) return false;
    }
    return curPage() === target;
  }

  function pageHas(id) {
    var want = displayOf(id);
    if (!want) return false;
    var btns = pageButtons();
    for (var i = 0; i < btns.length; i++) if (cleanText(btns[i]) === want) return true;
    return false;
  }

  function piniaCharStore() {
    try {
      var app = document.querySelector('#app').__vue_app__;
      var p = app && app._context && app._context.provides;
      if (!p) return null;
      var syms = Object.getOwnPropertySymbols(p);
      for (var i = 0; i < syms.length; i++) {
        var v = p[syms[i]];
        if (v && v.state && v.state.value && v.state.value.characterStore) {
          return v.state.value.characterStore;
        }
      }
    } catch (e) {}
    return null;
  }
  /* 优先直接改 store（无需面板/翻页）；拿不到再退回点列表 */
  async function setCharacter(id) {
    var st = piniaCharStore();
    if (st) {
      try {
        if (st.selectedCharacterId !== id) {
          st.selectedCharacterId = id;
          st.animationCategory = 'character';
          st.selectedAnimation = 'idle';
          st.selectedSkin = 'default';
        }
        if (await waitUntil(function () { return st.selectedCharacterId === id; }, 1500)) return true;
      } catch (e) {}
    }
    return selectId(id);
  }
  /* 旧路径：清属性过滤 → 翻到该角色所在页 → 点命中项（面板打开时兜底） */
  async function selectId(id) {
    navigating = true;
    try {
      var act = document.querySelector('.wc-elem:not(.bd2-fav).wc-elem--active');
      if (act) {
        act.click();
        await waitUntil(function () { return !document.querySelector('.wc-elem:not(.bd2-fav).wc-elem--active'); }, 400);
      }
      var idx = listIds().indexOf(id);
      if (idx < 0) return false;
      await gotoPage(Math.floor(idx / PAGE) + 1);
      var want = displayOf(id);
      for (var tries = 0; tries <= totalPages(); tries++) {
        if (pageHas(id)) {
          var bs = pageButtons();
          for (var i = 0; i < bs.length; i++) {
            if (want && cleanText(bs[i]) === want) { bs[i].click(); return true; }
          }
        }
        var before = curPage();
        var nav = navBtns();
        if (nav.length < 2) return false;
        nav[1].click();
        if (!(await waitUntil(function () { return curPage() !== before; }, 2000))) return false;
      }
      return false;
    } finally {
      navigating = false;
      lastFavKey = '';
      schedule();
    }
  }
  /* 随机后把列表翻到该角色所在页，方便直接点❤（不改选中，只翻页） */
  async function syncListTo(id) {
    try {
      if (favOnly) {
        var fi = favIds().indexOf(id);
        if (fi < 0) return false;
        favPage = Math.floor(fi / PAGE) + 1;
        lastFavKey = '';
        renderFavList();
        return true;
      }
      if (!panelVisible() || !document.querySelector(SEL.list)) return false;
      var list = document.querySelector(SEL.list);
      if (list.style.display === 'none') return false;
      if (!pageHas(id)) {
        var idx = listIds().indexOf(id);       // 保留当前属性过滤，按列表真实顺序算页
        if (idx >= 0) {
          var target = Math.floor(idx / PAGE) + 1;
          if (curPage() !== target) await gotoPage(target);
        }
        // 兜底：顺序/过滤与本地判断不一致时逐页找（最多一圈）
        for (var g = 0; g < totalPages() && !pageHas(id); g++) {
          var before = curPage();
          var nav = navBtns();
          if (nav.length < 2) return false;
          nav[1].click();
          if (!(await waitUntil(function () { return curPage() !== before; }, 1500))) return false;
        }
      }
      if (!pageHas(id)) return false;
      paintHearts();
      if (list.scrollIntoView) list.scrollIntoView({ block: 'nearest' });
      schedule();
      return true;
    } catch (e) { return false; }
  }
  /* 原列表条目右侧心形 */
  function paintHearts() {
    pageButtons().forEach(function (btn) {
      var id = idFromButton(btn);
      var h = btn.querySelector(':scope > .bd2-heart');
      if (!id) { if (h) h.remove(); return; }
      if (!h) {
        h = document.createElement('span');
        h.className = 'bd2-heart'; h.setAttribute('role', 'button');
        h.addEventListener('pointerdown', function (e) { e.stopPropagation(); });
        h.addEventListener('click', function (e) {
          e.stopPropagation(); e.preventDefault();
          try {
            var cid = idFromButton(btn); if (!cid) return;
            if (favs.has(cid)) favs.delete(cid); else favs.add(cid);
            save(); lastFavKey = ''; paintHearts(); paintFavTab(); applyMode();
          } catch (err) {}
        });
        btn.appendChild(h);
      }
      var on = favs.has(id);
      setHeart(h, on);
      if (h.classList.contains('on') !== on) h.classList.toggle('on', on);
    });
  }
  /* 收藏独立列表（自建分页，不受原列表 39 页影响） */
  function renderFavList() {
    var host = document.querySelector(SEL.list);
    if (!host) return;
    var box = document.querySelector('.bd2-favlist');
    var nav = document.querySelector('.bd2-fnav');
    if (!favOnly) {
      if (box && box.style.display !== 'none') box.style.display = 'none';
      if (nav && nav.style.display !== 'none') nav.style.display = 'none';
      lastFavKey = '';
      return;
    }
    var ids = favIds();
    var total = Math.max(1, Math.ceil(ids.length / PAGE));
    if (favPage > total) favPage = total;
    if (favPage < 1) favPage = 1;
    var slice = ids.slice((favPage - 1) * PAGE, favPage * PAGE);
    var key = curLang() + '|' + favPage + '|' + curChar() + '|' + slice.join(',');
    if (key === lastFavKey && box && nav) {
      if (box.style.display === 'none') box.style.display = '';
      if (nav.style.display === 'none') nav.style.display = '';
      return;
    }
    lastFavKey = key;
    if (!box) {
      box = document.createElement('div'); box.className = 'bd2-favlist';
      host.parentNode.insertBefore(box, host.nextSibling);
    }
    if (!nav) {
      nav = document.createElement('div'); nav.className = 'bd2-fnav';
      box.parentNode.insertBefore(nav, box.nextSibling);
    }
    box.style.display = ''; nav.style.display = '';
    box.textContent = '';
    nav.textContent = '';
    if (!slice.length) {
      var e = document.createElement('div');
      e.className = 'bd2-empty';
      e.textContent = '还没有收藏，给喜欢的角色点颗❤吧';
      box.appendChild(e);
    } else {
      slice.forEach(function (id) {
        var item = document.createElement('button');
        item.type = 'button';
        item.className = 'bd2-fitem' + (id === curChar() ? ' bd2-fitem--active' : '');
        var name = document.createElement('span');
        name.className = 'bd2-fname';
        name.textContent = displayOf(id) || id;
        var h = document.createElement('span');
        h.className = 'bd2-heart on';
        h.appendChild(heartSvg(true));
        h.addEventListener('pointerdown', function (e) { e.stopPropagation(); });
        h.addEventListener('click', function (e) {
          e.stopPropagation(); e.preventDefault();
          favs.delete(id); save(); lastFavKey = ''; paintFavTab(); renderFavList(); paintHearts();
        });
        item.appendChild(name); item.appendChild(h);
        item.addEventListener('click', function (e) {
          e.stopPropagation();
          try { if (id === curChar()) return; } catch (err) {}
          setCharacter(id);
        });
        box.appendChild(item);
      });
    }
    var prev = document.createElement('button');
    prev.type = 'button';
    var prevTri = document.createElement('span');
    prevTri.className = 'bd2-tri bd2-tri--left'; prev.appendChild(prevTri);
    prev.addEventListener('click', function () {
      favPage = favPage > 1 ? favPage - 1 : total; lastFavKey = ''; renderFavList();
    });
    var next = document.createElement('button');
    next.type = 'button';
    var nextTri = document.createElement('span');
    nextTri.className = 'bd2-tri bd2-tri--right'; next.appendChild(nextTri);
    next.addEventListener('click', function () {
      favPage = favPage < total ? favPage + 1 : 1; lastFavKey = ''; renderFavList();
    });
    var info = document.createElement('span');
    info.textContent = '第 ' + favPage + '/' + total + ' 页 · 共 ' + ids.length + ' 个';
    nav.appendChild(info); nav.appendChild(prev); nav.appendChild(next);
  }
  /* 属性行第 7 个图标：收藏类目 */
  function paintFavTab() {
    var row = document.querySelector('.wc-elems');
    if (!row) return;
    var t = row.querySelector('.bd2-fav');
    if (t) {
      setHeart(t, favOnly);
      if (t.classList.contains('on') !== favOnly) t.classList.toggle('on', favOnly);
      if (t.classList.contains('wc-elem--active') !== favOnly) t.classList.toggle('wc-elem--active', favOnly);
      return;
    }
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'wc-elem bd2-fav';
    // Vue scoped 样式需要 data-v-xxx 属性，否则 .wc-elem 的盒子样式不生效
    var ref = row.querySelector('.wc-elem');
    if (ref) {
      Array.prototype.forEach.call(ref.attributes, function (a) {
        if (/^data-v-/.test(a.name) && !b.hasAttribute(a.name)) b.setAttribute(a.name, '');
      });
    }
    b.addEventListener('click', function (e) {
      e.stopPropagation();
      try {
        if (!favOnly) {
          favOnly = true; favPage = 1; save();
          clearElemFilter();          // 清属性选择（异步，期间不自动退出）
        } else { favOnly = false; save(); }
        lastFavKey = ''; paintFavTab(); applyMode();
      } catch (err) {}
    });
    row.appendChild(b);
    paintFavTab();
  }
  function paintTools() {
    var panel = document.querySelector(SEL.panel);
    var list = document.querySelector(SEL.list);
    if (!panel || !list) return;
    var olds = panel.querySelectorAll('.bd2-tools');
    for (var k = 1; k < olds.length; k++) olds[k].remove();
    var row = panel.querySelector('.bd2-tools');
    if (!row) {
      row = document.createElement('div');
      row.className = 'bd2-tools';
      var r = document.createElement('button');
      r.type = 'button'; r.className = 'bd2-random';
      r.textContent = '🎲';
      r.addEventListener('click', function () { randomPick(); });
      row.appendChild(r);
      list.parentNode.insertBefore(row, list.nextSibling);
    }
    var rr = row.querySelector('.bd2-random');
    if (rr && rr.textContent !== '🎲') rr.textContent = '🎲';
  }
  function positionTools() {
    var r = document.querySelector('.bd2-tools');
    if (!r) return;
    var pager = favOnly ? document.querySelector('.bd2-fnav')
                        : document.querySelector('.wc-listnav');
    if (!pager || !pager.parentNode) return;
    if (r.nextSibling === pager && r.parentNode === pager.parentNode) return;
    pager.parentNode.insertBefore(r, pager);
  }
  /* 收藏模式：隐藏原列表，显示收藏列表 */
  function applyMode() {
    var list = document.querySelector(SEL.list);
    var navRow = document.querySelector('.wc-listnav');
    if (!list) return;
    if (favOnly) {
      if (list.style.display !== 'none') list.style.display = 'none';
      if (navRow && navRow.style.display !== 'none') navRow.style.display = 'none';
    } else {
      if (list.style.display !== '') list.style.display = '';
      if (navRow && navRow.style.display !== '') navRow.style.display = '';
    }
    renderFavList();
    positionTools();
  }
  function shuffled(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }
  function nextPick(ids) {
    var key = ids.join('|');
    if (key !== bagKey) {                 // 候选集变了 → 重开一轮
      bagKey = key; bag = shuffled(ids.slice()); lastPick = '';
    }
    if (!bag.length) {                    // 一轮用完 → 重新洗牌，且不与上次重复
      bag = shuffled(ids.slice());
      if (bag.length > 1 && bag[bag.length - 1] === lastPick) {
        var k = Math.floor(Math.random() * (bag.length - 1));
        var t = bag[bag.length - 1]; bag[bag.length - 1] = bag[k]; bag[k] = t;
      }
    }
    lastPick = bag.pop();
    return lastPick;
  }
  function secsLabel(n) {
    if (n < 60) return n + ' 秒';
    if (n % 60 === 0 && n < 3600) return (n / 60) + ' 分';
    if (n === 3600) return '1 小时';
    return Math.floor(n / 60) + ' 分 ' + (n % 60) + ' 秒';
  }
  function panelVisible() {
    var el = document.querySelector(SEL.panel);
    return !!el && el.getClientRects().length > 0;
  }
  function paintTimerLabel() {
    var row = document.querySelector('.bd2-tools');
    var b = row && row.querySelector('.bd2-timer-toggle');
    if (!b) return;
    var t;
    if (!timerOn) t = '⏱ 定时随机';
    else if (panelVisible()) t = '⏱ 面板关闭后计时';
    else t = '⏱ ' + Math.max(0, Math.ceil((timerNextAt - Date.now()) / 1000)) + ' 秒后换';
    if (b.textContent !== t) b.textContent = t;
    if (b.classList.contains('on') !== timerOn) b.classList.toggle('on', timerOn);
  }
  function stopTimer() {
    if (timerHandle) { clearTimeout(timerHandle); timerHandle = null; }
    if (timerUi) { clearInterval(timerUi); timerUi = null; }
    timerNextAt = 0;
  }
  function startTimer() {
    stopTimer();
    if (!timerOn) { paintTimerLabel(); return; }
    timerNextAt = Date.now() + timerSecs * 1000;
    timerHandle = setTimeout(timerFire, timerSecs * 1000);
    timerUi = setInterval(paintTimerLabel, 500);
    paintTimerLabel();
  }
  function timerFire() {
    timerHandle = null;
    if (!timerOn) return;
    if (panelVisible() || timerBusy) {           // 面板开着就先等着，不打断选人
      timerNextAt = Date.now() + 1000;
      timerHandle = setTimeout(timerFire, 1000);
      return;
    }
    timerBusy = true;
    Promise.resolve()
      .then(function () { return randomPick(true); })
      .catch(function () {})
      .then(function () { timerBusy = false; if (timerOn) startTimer(); });
  }
  function paintTimer() {
    var row = document.querySelector('.bd2-tools');
    if (!row) return;
    if (!row.querySelector('.bd2-timer-toggle')) {
      var btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'bd2-timer-toggle';
      btn.addEventListener('click', function () {
        timerOn = !timerOn; save(); paintTimer();
        if (timerOn) startTimer(); else stopTimer();
      });
      var step = document.createElement('button');
      step.type = 'button'; step.className = 'bd2-timer-secs';
      step.addEventListener('click', function () {
        var i = TIMER_STEPS.indexOf(timerSecs);
        timerSecs = TIMER_STEPS[(i + 1) % TIMER_STEPS.length];
        if (!timerOn) timerOn = true;            // 设间隔即视为启用
        save(); paintTimer(); startTimer();
      });
      row.appendChild(btn); row.appendChild(step);
    }
    var b = row.querySelector('.bd2-timer-toggle');
    paintTimerLabel();
    var i2 = row.querySelector('.bd2-timer-secs');
    var label = secsLabel(timerSecs);
    if (i2 && i2.textContent !== label) i2.textContent = label;
  }
  async function randomPick(quiet) {
    var ids = candidates();
    if (!ids.length) { toast(favOnly ? '收藏夹是空的' : '当前列表是空的'); return; }
    var id = nextPick(ids);
    if (ids.length > 1 && id === curChar()) id = nextPick(ids);   // 尽量别选中当前这个
    var ok = await setCharacter(id);
    var jumped = await syncListTo(id);   // 跳到该角色所在页，方便直接点❤
    var pageNow = favOnly ? favPage : curPage();
    var pageTotal = favOnly ? Math.max(1, Math.ceil(favIds().length / PAGE)) : totalPages();
    if (window.__bd2fav) window.__bd2fav.lastJump = { id: id, page: pageNow, jumped: jumped };
    if (quiet) return;   // 定时轮播不打扰：面板关着时弹 toast 是噪音
    var name = displayOf(id) || id;
    var where = '（第 ' + pageNow + '/' + pageTotal + ' 页）';
    toast(ok ? '随机：' + name + (jumped ? where : '') : '定位失败' + where);
  }
  async function clearElemFilter() {
    var act = document.querySelector('.wc-elem:not(.bd2-fav).wc-elem--active');
    if (!act) return;
    pendingClear = true;
    act.click();
    await waitUntil(function () {
      return !document.querySelector('.wc-elem:not(.bd2-fav).wc-elem--active');
    }, 600);
    pendingClear = false;
  }
  /* 全页 tooltip 禁用：连上游 bundle 的 title 也一起剥掉（只影响提示，不影响功能） */
  function stripTitles() {
    var els = document.querySelectorAll('[title]');
    for (var i = 0; i < els.length; i++) els[i].removeAttribute('title');
  }
  function ensure() {
    if (!DB) return;
    if (!document.querySelector(SEL.panel)) return;
    stripTitles();
    if (favOnly && !pendingClear && activeElem()) { favOnly = false; save(); }
    paintFavTab(); paintTools(); paintTimer(); paintHearts(); applyMode();
  }
  var scheduled = false;
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(function () { scheduled = false; ensure(); });
  }
  function boot() {
    style();
    if (window.__BD2_CHARACTERS && window.__BD2_CHARACTERS.order &&
        window.__BD2_CHARACTERS.order.length > 200) {
      DB = window.__BD2_CHARACTERS;
      buildIndex();
    } else {
      try { console.warn('[bd2-fav] no character data'); } catch (_) {}
      return;
    }
    window.__bd2fav = {
      version: 35,
      build: 'jump-2',
      lastJump: null,
      favCount: function () { return favs.size; },
      timer: function () { return { on: timerOn, secs: timerSecs }; }
    };
    startTimer();
    // 动态后加的 title 也要在显示前掐掉（捕获期，悬停 dwell 之前移除就不会弹）
    document.addEventListener('mouseover', function (e) {
      var t = e.target && e.target.closest ? e.target.closest('[title]') : null;
      if (t) t.removeAttribute('title');
    }, true);
    document.addEventListener('visibilitychange', function () {
      if (timerOn && !document.hidden) startTimer();
    });
    schedule();
  }
  boot();
  new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
})();
