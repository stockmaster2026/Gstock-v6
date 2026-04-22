/*

- ═══════════════════════════════════════════════════════════
- decision-hook.js — 決策樹整合外掛
- ═══════════════════════════════════════════════════════════
- 作用:在 test-accum.html 的個股分析結果卡片上,
- ```
    自動加一顆「🎯 決策樹判斷」按鈕,
  ```
- ```
    點下去彈出視窗載入 decision.html,並自動帶入數據。
  ```
- 
- 使用方式:
- ```
    在 test-accum.html 的 </body> 前加一行:
  ```
- ```
    <script src="decision-hook.js"></script>
  ```
- 
- 依賴:test-accum.html 和 decision.html 放在同一層目錄
- ═══════════════════════════════════════════════════════════
  */

(function() {
‘use strict’;

// ═════════════════════════════════════════
// 1. 注入 CSS(Modal 樣式)
// ═════════════════════════════════════════
var css = `.dt-overlay { position: fixed; inset: 0; background: rgba(26, 26, 46, 0.6); z-index: 9999; display: none; align-items: flex-start; justify-content: center; padding: 20px 10px; overflow-y: auto; -webkit-backdrop-filter: blur(4px); backdrop-filter: blur(4px); } .dt-overlay.open { display: flex; } .dt-modal { background: #fffdf5; border-radius: 16px; width: 100%; max-width: 560px; max-height: calc(100vh - 40px); overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,.3); display: flex; flex-direction: column; position: relative; } .dt-modal-hdr { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: linear-gradient(135deg, #fffbec, #fff8e0); border-bottom: 1px solid #e8dfc0; } .dt-modal-title { font-size: 14px; font-weight: 700; color: #8a6e2f; letter-spacing: 1px; } .dt-modal-close { background: #f0e8d0; color: #8a6e2f; border: none; border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 700; cursor: pointer; -webkit-tap-highlight-color: transparent; } .dt-modal-close:active { background: #c8a84b; color: #fff; } .dt-modal-body { flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch; } .dt-iframe { width: 100%; min-height: 600px; border: none; display: block; } /* 決策樹按鈕(植入分析結果卡片) */ .dt-launch-btn { display: block; width: 100%; margin-top: 12px; padding: 14px; background: linear-gradient(135deg, #3a7bd5, #5b21b6); color: #fff; border: none; border-radius: 12px; font-size: 15px; font-weight: 700; cursor: pointer; box-shadow: 0 3px 10px rgba(58, 123, 213, .3); -webkit-tap-highlight-color: transparent; } .dt-launch-btn:active { transform: scale(.98); box-shadow: 0 1px 4px rgba(58, 123, 213, .3); } .dt-launch-hint { text-align: center; font-size: 11px; color: #888; margin-top: 6px; }`;
var styleEl = document.createElement(‘style’);
styleEl.textContent = css;
document.head.appendChild(styleEl);

// ═════════════════════════════════════════
// 2. 注入 Modal 結構
// ═════════════════════════════════════════
var overlay = document.createElement(‘div’);
overlay.className = ‘dt-overlay’;
overlay.id = ‘dtOverlay’;
overlay.innerHTML = `<div class="dt-modal" onclick="event.stopPropagation()"> <div class="dt-modal-hdr"> <span class="dt-modal-title">🎯 快速判斷決策樹</span> <button class="dt-modal-close" onclick="window.dtClose()">✕ 關閉</button> </div> <div class="dt-modal-body"> <iframe id="dtFrame" class="dt-iframe" src="about:blank"></iframe> </div> </div>`;
document.body.appendChild(overlay);

// 點擊 overlay 空白處關閉
overlay.addEventListener(‘click’, function(e) {
if (e.target === overlay) window.dtClose();
});

// ═════════════════════════════════════════
// 3. 開關 Modal 函數(掛到 window 方便調用)
// ═════════════════════════════════════════
window.dtOpen = function(params) {
var url = ‘decision.html’;
if (params) {
var qs = [];
Object.keys(params).forEach(function(k) {
var v = params[k];
if (v === null || v === undefined || v === ‘’) return;
qs.push(encodeURIComponent(k) + ‘=’ + encodeURIComponent(v));
});
if (qs.length) url += ‘?’ + qs.join(’&’);
}
var frame = document.getElementById(‘dtFrame’);
frame.src = url;
var ol = document.getElementById(‘dtOverlay’);
ol.classList.add(‘open’);
document.body.style.overflow = ‘hidden’;
};

window.dtClose = function() {
var ol = document.getElementById(‘dtOverlay’);
ol.classList.remove(‘open’);
document.body.style.overflow = ‘’;
// 延遲清空 iframe,避免關閉時閃現首頁
setTimeout(function() {
var frame = document.getElementById(‘dtFrame’);
if (!ol.classList.contains(‘open’)) frame.src = ‘about:blank’;
}, 300);
};

// ═════════════════════════════════════════
// 4. 從 test-accum.html 的分析結果抓數據
// ═════════════════════════════════════════
function extractDataFromPage(sym) {
var params = { sym: sym };
var root = document.getElementById(‘accumOut’);
if (!root) return params;

```
var txt = root.innerText || root.textContent || '';

// 漲幅:從「+XX%」或「突破後第 X 天 +XX%」抓
var gainMatch = txt.match(/\+(\d+)%/);
if (gainMatch) params.gain = parseInt(gainMatch[1]);

// 主力成本距離(保底)
if (!params.gain) {
  var distMatch = txt.match(/距主力成本\s*\+?(\-?\d+)%/);
  if (distMatch) params.gain = parseInt(distMatch[1]);
}

// RS Rating:從「RS 82」或「RS 82 領頭羊」抓
var rsMatch = txt.match(/RS\s+(\d+)/);
if (rsMatch) params.rs = parseInt(rsMatch[1]);

// 賣出訊號:看是否有「⚠️ 賣出」或「大單賣出」
var sellCount = (txt.match(/⚠️\s*賣出/g) || []).length;
if (sellCount >= 2) params.sell = 'heavy';
else if (sellCount === 1) params.sell = 'light';
else params.sell = 'no';

// RS 新高
if (/✨\s*RS\s*創/.test(txt) || /✨\s*新高/.test(txt) || /RS\s*創3月新高/.test(txt)) {
  params.newhigh = 1;
} else {
  params.newhigh = 0;
}

// RS 趨勢
if (/🔥\s*RS\s*上升/.test(txt) || /RS上升/.test(txt)) params.trend = 'up';
else if (/⚠️\s*RS\s*走弱/.test(txt) || /RS走弱/.test(txt)) params.trend = 'down';
else params.trend = 'stable';

// 突破狀態
var brkMatch = txt.match(/突破後第\s*(\d+)\s*天/);
if (brkMatch) {
  params.break = parseInt(brkMatch[1]);
} else if (/底部震盪中/.test(txt) || /🔄/.test(txt)) {
  params.break = 'pre';
}

// MACD 狀態
if (/MACD\s*強勢/.test(txt)) params.macd = 'strong';
else if (/MACD\s*柱縮/.test(txt) || /MACD\s*零軸上柱縮/.test(txt)) params.macd = 'weak';
else if (/MACD\s*零軸下/.test(txt)) params.macd = 'down';

return params;
```

}

// ═════════════════════════════════════════
// 5. 監測分析結果出現 → 自動加按鈕
// ═════════════════════════════════════════
function injectButton() {
var root = document.getElementById(‘accumOut’);
if (!root) return;

```
// 找每一張結果卡片裡的 .verdict-block(判決區塊是分析卡最底部)
var verdictBlocks = root.querySelectorAll('.verdict-block');
verdictBlocks.forEach(function(block) {
  // 避免重複加
  if (block.querySelector('.dt-launch-btn')) return;

  // 找這張卡所屬的股票代號
  var card = block.closest('.card');
  if (!card) return;
  var tkEl = card.querySelector('.tk');
  if (!tkEl) return;
  var sym = (tkEl.textContent || '').trim().toUpperCase();
  if (!sym) return;

  // 建立按鈕
  var btn = document.createElement('button');
  btn.className = 'dt-launch-btn';
  btn.innerHTML = '🎯 用決策樹快速判斷';
  btn.addEventListener('click', function() {
    var params = extractDataFromPage(sym);
    window.dtOpen(params);
  });

  var hint = document.createElement('div');
  hint.className = 'dt-launch-hint';
  hint.textContent = '自動帶入此頁數據,可手動修改';

  // 插在 verdict-inner 的最後
  var inner = block.querySelector('.verdict-inner');
  if (inner) {
    inner.appendChild(btn);
    inner.appendChild(hint);
  } else {
    block.appendChild(btn);
    block.appendChild(hint);
  }
});
```

}

// 用 MutationObserver 監測 accumOut 變化
function startObserver() {
var root = document.getElementById(‘accumOut’);
if (!root) {
// accumOut 還沒生成,稍後重試
setTimeout(startObserver, 500);
return;
}
var obs = new MutationObserver(function() {
// 延遲一下等 DOM 穩定
setTimeout(injectButton, 50);
});
obs.observe(root, { childList: true, subtree: true });
// 初次嘗試
injectButton();
}

// DOM 準備好就啟動
if (document.readyState === ‘loading’) {
document.addEventListener(‘DOMContentLoaded’, startObserver);
} else {
startObserver();
}

console.log(’[decision-hook] 已載入 ✓’);
})();
