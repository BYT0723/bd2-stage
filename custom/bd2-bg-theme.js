/* bd2-bg-theme.js v1 — 背景跟随系统 light/dark（在 bundle 之前跑，只碰 localStorage）。
 *
 * 页面里执行不了 gsettings，但浏览器会把 org.gnome.desktop.interface
 * color-scheme 映射成 prefers-color-scheme，这里读的就是同一个开关。
 * bundle 里的 Vue 状态外挂无法访问，所以走它自己的持久化入口：
 * 启动前把 bd2-wallpaper-prefs.customBackgroundImage 填成对应那张，
 * 应用起来就直接是这张；没有 Wallpaper Engine 属性可实时切换时，
 * 系统切换后重载一次即可。
 *
 * 手动选的图（prefs 里既不是空白、也不是内置这两张）一律尊重，不再跟随系统。
 * Wallpaper Engine 里配了 background/background_dark 时，bundle 补丁会设
 * window.__bd2BgLive，此时交给补丁实时切，本脚本不再重载。
 */
(function () {
  'use strict';
  var KEY = 'bd2-wallpaper-prefs';
  var AUTO = ['./backgrounds/bd2-parchment-2560x1440.jpg',
              './backgrounds/bd2-starlit-vault-2560x1440.jpg'];

  function isDark() {
    try { return window.matchMedia('(prefers-color-scheme: dark)').matches; }
    catch (e) { return false; }
  }

  function readPrefs() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; }
    catch (e) { return {}; }
  }

  function isManual(prefs) {
    var cur = String(prefs.customBackgroundImage || '');
    return !!cur && AUTO.indexOf(cur) < 0;
  }

  /* 旧版本把视频塞进过图片位（bgImage=xxx.webm）：图片元素必然加载失败，
   * 失败回调会把 customBackgroundImage 置 null，连属性下发的值一起抹掉，
   * 表现为“怎么设背景都没反应”。启动前把视频值从图片位清掉，交给属性/默认值。 */
  function sanitize(prefs) {
    var cur = String(prefs.customBackgroundImage || '');
    if (/\.(webm|mp4)(\?.*)?$/i.test(cur)) {
      prefs.customBackgroundImage = '';
      return true;
    }
    return false;
  }

  /* 需要时写入对应背景，返回是否真的改了 */
  function apply() {
    var prefs = readPrefs();
    var dirty = sanitize(prefs);
    if (!isManual(prefs)) {
      var want = AUTO[isDark() ? 1 : 0];
      if (prefs.customBackgroundImage !== want) {
        prefs.customBackgroundImage = want;
        dirty = true;
      }
    }
    if (!dirty) return false;
    try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) {}
    return true;
  }

  apply();
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
      if (window.__bd2BgLive) return;
      if (apply()) { try { location.reload(); } catch (e) {} }
    });
  } catch (e) {}
})();
