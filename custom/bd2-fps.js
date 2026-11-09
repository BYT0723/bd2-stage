/* bd2-fps.js v1 — 活动/静止帧率（外挂，不碰 bundle）。
 *
 * 背景：壁纸持续 60fps 渲染约占 0.5–0.9 核（60Hz 实测），帧率是唯一有效杠杆。
 * 两个属性 fps / fpsIdle：30 / 60 / refresh，默认 refresh/refresh（与未安装时完全一致）。
 *
 * 调度器必须“保留循环”：未到点的 rAF 回调留在队列里等下一拍，绝不丢弃——
 * 丢弃会让 Spine 的自我重注册循环停摆（实测 draws/s 直接归零）。
 */
(function () {
  'use strict';

  var IDLE_MS = 5000;          // 无输入多久算静止
  var DEFAULT_ACTIVE = 0;      // 0 = 跟随刷新率（默认）
  var DEFAULT_IDLE = 0;

  var activeTarget = DEFAULT_ACTIVE;
  var idleTarget = DEFAULT_IDLE;
  var activeUntil = 0;
  var installed = false;

  var realRaf = window.requestAnimationFrame.bind(window);
  var realCaf = window.cancelAnimationFrame.bind(window);

  var queue = [];               // 待执行回调 [{id, cb, canceled}]
  var nodes = Object.create(null);
  var nextId = 1;
  var rafId = null;             // 真实 rAF id
  var nextAt = 0;               // 下一拍允许执行的时间戳
  var lastTarget = -1;
  var warned = false;

  function warnOnce(e) {
    if (warned) return;
    warned = true;
    try { console.warn('[bd2-fps] rAF callback error', e); } catch (err) {}
  }

  function runQueue(t) {
    var run = queue;
    queue = [];
    for (var i = 0; i < run.length; i++) {
      var n = run[i];
      delete nodes[n.id];
      if (n.canceled) continue;
      try { n.cb.call(window, t); } catch (e) { warnOnce(e); }
    }
  }

  function tick(t) {
    rafId = null;
    var step = budget();
    if (step <= 0 || nextAt === 0 || t >= nextAt) {
      if (step > 0) {
        // 累积配速：落后超过一帧就从当前时间重算，避免长任务后突发补帧
        nextAt = (nextAt && t - nextAt > step) ? t + step : (nextAt || t) + step;
      }
      runQueue(t);
    }
    if (queue.length) schedule();
  }

  function schedule() {
    if (rafId !== null || !installed) return;
    rafId = realRaf(tick);
  }

  function wrapRaf(cb) {
    // 两档都是跟随刷新率时直接旁路，零排队开销
    if (!activeTarget && !idleTarget) return realRaf(cb);
    var node = { id: nextId++, cb: cb, canceled: false };
    nodes[node.id] = node;
    queue.push(node);
    schedule();
    return node.id;
  }

  function wrapCaf(id) {
    var node = nodes[id];
    if (node) {
      node.canceled = true;
      delete nodes[id];
      return;
    }
    realCaf(id);                // 旁路期注册的回调走原生取消
  }

  function install() {
    if (installed) return;
    installed = true;
    window.requestAnimationFrame = wrapRaf;
    window.cancelAnimationFrame = wrapCaf;
    nextAt = 0;
  }

  function norm(v, fallback) {
    if (v === 0) return 0;      // 内部/面板传来的数值 0
    var s = String(v == null ? '' : v).trim().toLowerCase();
    if (s === '30') return 30;
    if (s === '60') return 60;
    if (s === 'refresh' || s === 'auto' || s === 'monitor' || s === 'display' ||
        s === '跟随' || s === '跟随刷新率') return 0;
    return fallback;
  }

  // 执行时夹取，不覆盖用户设置值：静止帧率高于活动帧率时按活动执行，
  // 避免“一停下来反而更快”；之后把活动档调高，静止档仍保留用户原值。
  function effectiveIdle() {
    if (idleTarget > 0 && activeTarget > 0 && idleTarget > activeTarget) {
      return activeTarget;
    }
    return idleTarget;
  }

  function set(active, idle) {
    if (typeof active !== 'undefined') activeTarget = norm(active, DEFAULT_ACTIVE);
    if (typeof idle !== 'undefined') idleTarget = norm(idle, DEFAULT_IDLE);
    nextAt = 0;
    if (activeTarget || idleTarget) install();
    paintRows();
  }

  function target() {
    if (Date.now() < activeUntil) return activeTarget;
    if (panelVisible()) return activeTarget;   // 面板打开时按活动档
    return effectiveIdle();
  }

  function budget() {
    var t = target();
    if (t !== lastTarget) { lastTarget = t; nextAt = 0; }
    return t > 0 ? 1000 / t : 0;
  }

  function boost() {
    var wasIdle = Date.now() >= activeUntil;
    activeUntil = Date.now() + IDLE_MS;
    if (wasIdle) nextAt = 0;
  }

  /* ---- WE 属性：fps / fpsIdle ---- */
  function readProp(props, name, fallback) {
    if (!props || !(name in props)) return fallback;
    var r = props[name];
    var v = (r && typeof r === 'object' && 'value' in r) ? r.value : r;
    return norm(v, fallback);
  }

  function applyProps(props) {
    if (!props) return;
    var hasFps = 'fps' in props;
    var hasIdle = 'fpsIdle' in props;
    if (!hasFps && !hasIdle) return;   // WE 会随任意属性变更下发整组，无关批次直接跳过
    set(readProp(props, 'fps', activeTarget), readProp(props, 'fpsIdle', idleTarget));
  }

  (function hookProps() {
    var l = window.wallpaperPropertyListener = window.wallpaperPropertyListener || {};
    var prev = l.applyUserProperties;
    l.applyUserProperties = function (props) {
      try { applyProps(props); } catch (e) {}
      if (typeof prev === 'function') return prev.apply(this, arguments);
    };
  })();

  /* ---- 面板可见性（活动档判定；节流查询，避免每帧 layout） ---- */
  var panelCheckAt = 0;
  var panelCached = false;
  function panelVisible() {
    var n = Date.now();
    if (n - panelCheckAt < 250) return panelCached;
    panelCheckAt = n;
    var el = document.querySelector('.wc-panel');
    panelCached = !!el && el.getClientRects().length > 0;
    return panelCached;
  }

  /* ---- 悬浮球面板两行：活动 / 静止 ---- */
  var ROW_LABEL = { active: '活动帧率 (FPS)', idle: '静止帧率 (Idle FPS)' };
  var SEG_CHOICES = [['30', 30], ['60', 60], ['跟随', 0]];

  function copyScope(dst, src) {
    if (!src || !dst) return;
    for (var i = 0; i < src.attributes.length; i++) {
      var a = src.attributes[i];
      if (/^data-v-/.test(a.name)) dst.setAttribute(a.name, a.value);
    }
  }

  function buildRow(kind, refRow, refSeg) {
    var row = document.createElement('div');
    row.className = 'wc-row bd2-fps-row';
    row.setAttribute('data-bd2-fps', kind);
    copyScope(row, refRow);

    var label = document.createElement('div');
    label.className = 'wc-row__label';
    copyScope(label, refRow && refRow.querySelector('.wc-row__label'));
    var span = document.createElement('span');
    span.textContent = ROW_LABEL[kind];
    label.appendChild(span);

    var seg = document.createElement('div');
    seg.className = 'wc-seg bd2-fps-seg';
    seg.setAttribute('role', 'group');
    seg.setAttribute('aria-label', 'fps ' + kind);
    copyScope(seg, refSeg);

    var refBtn = refSeg && refSeg.querySelector('.wc-seg__btn');
    for (var i = 0; i < SEG_CHOICES.length; i++) {
      (function (choice) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'wc-seg__btn';
        b.textContent = choice[0];
        b.setAttribute('data-fps', choice[1] === 0 ? 'refresh' : String(choice[1]));
        copyScope(b, refBtn);
        b.addEventListener('click', function () {
          if (kind === 'active') set(choice[1], idleTarget);
          else set(activeTarget, choice[1]);
        });
        seg.appendChild(b);
      })(SEG_CHOICES[i]);
    }

    row.appendChild(label);
    row.appendChild(seg);
    return row;
  }

  function paintRows() {
    var kinds = [['active', activeTarget], ['idle', idleTarget]];
    for (var k = 0; k < kinds.length; k++) {
      var row = document.querySelector('[data-bd2-fps="' + kinds[k][0] + '"]');
      if (!row) continue;
      var want = kinds[k][1];
      var btns = row.querySelectorAll('.wc-seg__btn');
      for (var i = 0; i < btns.length; i++) {
        var raw = btns[i].getAttribute('data-fps');
        var val = raw === 'refresh' ? 0 : Number(raw);
        var on = val === want;
        if (btns[i].classList.contains('wc-seg__btn--active') !== on) {
          btns[i].classList.toggle('wc-seg__btn--active', on);
        }
      }
    }
  }

  function ensurePanel() {
    var panel = document.querySelector('.wc-panel');
    if (!panel) return;
    if (panel.querySelector('[data-bd2-fps]')) { paintRows(); return; }

    var refSeg = panel.querySelector('.bd2-voice-seg');
    var refRow = refSeg && refSeg.closest ? refSeg.closest('.wc-row') : null;
    var activeRow = buildRow('active', refRow, refSeg);
    var idleRow = buildRow('idle', refRow, refSeg);

    if (refRow && refRow.parentNode) {
      refRow.parentNode.insertBefore(activeRow, refRow.nextSibling);
      refRow.parentNode.insertBefore(idleRow, activeRow.nextSibling);
    } else {
      var before = panel.querySelector('.bd2-tools') || panel.querySelector('.wc-list');
      if (before && before.parentNode) {
        before.parentNode.insertBefore(activeRow, before);
        before.parentNode.insertBefore(idleRow, before);
      } else {
        panel.appendChild(activeRow);
        panel.appendChild(idleRow);
      }
    }
    paintRows();
  }

  var ensureScheduled = false;
  function scheduleEnsure() {
    if (ensureScheduled) return;
    ensureScheduled = true;
    window.requestAnimationFrame(function () {
      ensureScheduled = false;
      try { ensurePanel(); } catch (e) {}
    });
  }
  new MutationObserver(scheduleEnsure).observe(document.documentElement, {
    childList: true, subtree: true
  });
  scheduleEnsure();

  var INPUT_EVENTS = ['pointerdown', 'pointermove', 'pointerup', 'wheel', 'keydown', 'touchstart'];
  for (var i = 0; i < INPUT_EVENTS.length; i++) {
    window.addEventListener(INPUT_EVENTS[i], boost, true);
  }
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) boost();
  });

  window.__bd2Fps = {
    version: 1,
    set: set,
    get: function () { return { fps: activeTarget, idle: idleTarget }; },
    target: target,
    boost: boost,
    installed: function () { return installed; }
  };
  window.__bd2FpsBoost = boost;
})();
