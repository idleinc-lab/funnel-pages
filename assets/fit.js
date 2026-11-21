/* 端末の文字拡大設定でも、手で区切った行が途中で折り返さないよう、文字サイズだけ自動で微調整する。
   JSが動かない環境では通常の折り返しになるだけで、表示は壊れない。 */
(function () {
  function fit() {
    var wrap = document.querySelector('.wrap');
    if (!wrap) return;
    wrap.style.removeProperty('--fs');
    var els = Array.prototype.slice.call(wrap.querySelectorAll('h1,h3,p')).filter(function (e) { return e.querySelector('br'); });
    els.forEach(function (e) { e.style.fontSize = ''; e.style.whiteSpace = 'nowrap'; });
    var body = 1, h1r = 1, h1 = wrap.querySelector('h1');
    els.forEach(function (e) {
      var r = e.clientWidth / e.scrollWidth;
      if (r < 1) { if (e === h1) h1r = r; else body = Math.min(body, r); }
    });
    if (body < 1) {
      var base = parseFloat(getComputedStyle(wrap).fontSize);
      wrap.style.setProperty('--fs', Math.max(12, Math.floor(base * body * 10) / 10) + 'px');
    }
    if (h1 && h1r < 1) {
      h1.style.fontSize = Math.max(16, Math.floor(parseFloat(getComputedStyle(h1).fontSize) * h1r * 10) / 10) + 'px';
    }
  }
  var t;
  function later() { clearTimeout(t); t = setTimeout(fit, 80); }
  if (document.readyState !== 'loading') fit(); else document.addEventListener('DOMContentLoaded', fit);
  window.addEventListener('load', fit);
  window.addEventListener('resize', later);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
})();
