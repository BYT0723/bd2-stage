/* bd2-carousel.js v1 — 换人转盘动画（定格快照，不碰 bundle 内部）。
 *
 * bundle 换人时会先 dispose 旧 SpinePlayer、再清空容器，旧画面无法继续播放，
 * 所以这里在 dispose 之前把 WebGL canvas 同步拷到一张 2D canvas 上当作定格贴片：
 * 旧人物朝一侧 3D 转出，新人物从另一侧转入，形成左右转盘换人的感觉。
 * 方向每次随机；资源没加载完就等，最长 3 秒兜底显示，避免卡成隐形。
 * 系统开启“减少动效”时完全跳过。
 */
(function () {
  'use strict';

  var OUT_MS = 420;
  var IN_MS = 560;
  var HOLD_MS = 3000;
  var PERSPECTIVE = 1600;
  var ANGLE = 62;          // 绕 Y 轴最大角度
  var SHIFT = 26;          // 横向位移（元素自身宽度百分比）
  var SCALE = 0.82;
  var ORIGIN = '52% 58%';  // 以人物身体中心为转轴

  var state = {
    pending: false,
    dir: 1,
    wrapper: null,
    container: null,
    overlay: null,
    outAnim: null,
    inAnim: null,
    revealTimer: null,
    hitLayer: null,
    hitPointer: ''
  };

  function reduced() {
    try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
    catch (e) { return false; }
  }

  function canAnimate() {
    try { return typeof Element !== 'undefined' && !!Element.prototype.animate; }
    catch (e) { return false; }
  }

  function wrapper() {
    var bg = document.querySelector('.bd2-bg-layer');
    return bg ? bg.parentElement : null;
  }

  function findCanvas(w) {
    var c = w && w.querySelector('canvas.spine-player-canvas');
    return c && c.width > 0 && c.height > 0 ? c : null;
  }

  function findContainer(w, canvas) {
    var sp = canvas && canvas.parentElement;
    if (sp && sp.parentElement && sp.parentElement !== w) return sp.parentElement;
    // 加载失败/空容器时按 z-10 找人物层
    var kids = w ? w.children : [];
    for (var i = 0; i < kids.length; i++) {
      var cls = String(kids[i].className || '');
      if (/(^|\s)z-10(\s|$)/.test(cls)) return kids[i];
    }
    return null;
  }

  function animate(el, frames, opts) {
    if (!el) return null;
    try { return el.animate(frames, opts); } catch (e) { return null; }
  }

  function cancelAnim(a) {
    if (!a) return;
    try { a.cancel(); } catch (e) {}
  }

  function removeOverlay() {
    if (!state.overlay) return;
    try { state.overlay.remove(); } catch (e) {}
    state.overlay = null;
  }

  function restoreHit() {
    var h = state.hitLayer;
    if (!h) return;
    h.style.pointerEvents = state.hitPointer || '';
    state.hitLayer = null;
    state.hitPointer = '';
  }

  function restoreContainer() {
    var c = state.container;
    if (!c) return;
    c.style.opacity = '';
    c.style.transform = '';
    c.style.transformOrigin = '';
    c.style.backfaceVisibility = '';
    c.style.willChange = '';
    c.style.filter = '';
  }

  function lockHit() {
    var w = state.wrapper;
    var h = w && w.querySelector('.character-hit-layer');
    if (!h) return;
    state.hitLayer = h;
    state.hitPointer = h.style.pointerEvents;
    h.style.pointerEvents = 'none';
  }

  /* 同一套位姿：sign=+1 右侧、-1 左侧；edge=0 正位、1 最外侧 */
  function pose(sign, edge) {
    return 'perspective(' + PERSPECTIVE + 'px)' +
      ' translateX(' + (sign * SHIFT * edge) + '%)' +
      ' rotateY(' + (-sign * ANGLE * edge) + 'deg)' +
      ' scale(' + (1 - (1 - SCALE) * edge) + ')';
  }

  function outFrames() {
    var s = -state.dir;   // 旧人物去新人物来的反方向
    return [
      { offset: 0, transform: pose(s, 0), opacity: 1, filter: 'brightness(1)' },
      { offset: 0.55, opacity: 1 },
      { offset: 1, transform: pose(s, 1), opacity: 0, filter: 'brightness(.55)' }
    ];
  }

  function inFrames() {
    var s = state.dir;
    return [
      { offset: 0, transform: pose(s, 1), opacity: 0.6, filter: 'brightness(.65)' },
      { offset: 0.18, opacity: 1 },
      { offset: 1, transform: pose(s, 0), opacity: 1, filter: 'brightness(1)' }
    ];
  }

  function snapshot(canvas) {
    var cv = document.createElement('canvas');
    cv.width = canvas.width;
    cv.height = canvas.height;
    var ctx = null;
    try { ctx = cv.getContext('2d'); } catch (e) {}
    if (!ctx) return null;
    try { ctx.drawImage(canvas, 0, 0); } catch (e) { return null; }
    cv.setAttribute('aria-hidden', 'true');
    cv.style.cssText = 'display:block;width:100%;height:100%';
    var box = document.createElement('div');
    box.className = 'bd2-carousel-out';
    box.setAttribute('aria-hidden', 'true');
    box.style.cssText = 'position:absolute;inset:0;z-index:10;pointer-events:none;' +
      'transform-origin:' + ORIGIN + ';will-change:transform,opacity;backface-visibility:hidden';
    box.appendChild(cv);
    return box;
  }

  function playOut(box) {
    var a = animate(box, outFrames(), {
      duration: OUT_MS,
      easing: 'cubic-bezier(.45,0,.55,1)',
      fill: 'forwards'
    });
    state.outAnim = a;
    if (!a) { removeOverlay(); return; }
    a.onfinish = a.oncancel = function () {
      a.onfinish = a.oncancel = null;
      if (state.overlay === box) removeOverlay();
      if (state.outAnim === a) state.outAnim = null;
      try { a.cancel(); } catch (e) {}
    };
  }

  function reveal() {
    state.pending = false;
    if (state.revealTimer) { clearTimeout(state.revealTimer); state.revealTimer = null; }
    cancelAnim(state.inAnim);
    state.inAnim = null;
    removeOverlay();
    restoreContainer();
    restoreHit();
  }

  function reset() {
    state.pending = false;
    if (state.revealTimer) { clearTimeout(state.revealTimer); state.revealTimer = null; }
    cancelAnim(state.outAnim);
    state.outAnim = null;
    cancelAnim(state.inAnim);
    state.inAnim = null;
    removeOverlay();
    restoreContainer();
    restoreHit();
  }

  /* 换人 watcher 最开头调用：此时旧 player 还活着，可以同步取画面 */
  function swap() {
    reset();
    state.wrapper = wrapper();
    if (!state.wrapper) return;

    var canvas = findCanvas(state.wrapper);
    var container = findContainer(state.wrapper, canvas);
    if (!container) return;

    // “减少动效”或没有 WAAPI：直接走原来的瞬间切换
    if (reduced() || !canAnimate()) return;

    state.pending = true;
    state.container = container;
    state.dir = Math.random() < 0.5 ? -1 : 1;
    lockHit();

    var box = canvas ? snapshot(canvas) : null;
    if (box) {
      state.overlay = box;
      container.parentNode.insertBefore(box, container.nextSibling);
      playOut(box);
    }

    // 新人物先藏起来，等 success 再入场，避免加载空帧闪一下
    container.style.transformOrigin = ORIGIN;
    container.style.backfaceVisibility = 'hidden';
    container.style.willChange = 'transform,opacity';
    container.style.transform = pose(state.dir, 1);
    container.style.opacity = '0';

    state.revealTimer = setTimeout(function () {
      state.revealTimer = null;
      if (state.pending) reveal();
    }, HOLD_MS);
  }

  /* Spine success 回调最开头调用：新骨架已就绪，等两帧让它先画出来 */
  function enter() {
    var container = state.container;
    if (!state.pending || !container) return;
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        if (!state.pending || state.container !== container) return;
        state.pending = false;
        if (state.revealTimer) { clearTimeout(state.revealTimer); state.revealTimer = null; }
        var a = animate(container, inFrames(), {
          duration: IN_MS,
          easing: 'cubic-bezier(.42,0,.28,1)',
          fill: 'forwards'
        });
        state.inAnim = a;
        if (!a) { reveal(); return; }
        a.onfinish = a.oncancel = function () {
          a.onfinish = a.oncancel = null;
          if (state.container !== container) return;
          state.inAnim = null;
          removeOverlay();
          restoreContainer();
          restoreHit();
          try { a.cancel(); } catch (e) {}
        };
      });
    });
  }

  window.__bd2CarouselSwap = swap;
  window.__bd2CarouselEnter = enter;
  window.__bd2Carousel = {
    version: 1,
    build: 'turntable-1',
    durations: { out: OUT_MS, in: IN_MS }
  };
})();
