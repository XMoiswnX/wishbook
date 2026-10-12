"""The local progress page shown in the browser while wishbook_sync.exe runs (served from 127.0.0.1, polls /state)."""

PAGE = r"""<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wishbook | Sync</title>
<link rel="icon" href="{{ICON}}">
<style>
@font-face{font-family:"jf-openhuninn";src:local("jf-openhuninn-2.1"),local("jf open 粉圓 2.1"),url("https://cdn.jsdelivr.net/gh/justfont/open-huninn-font@v2.1/font/jf-openhuninn-2.1.ttf") format("truetype");font-display:swap}
:root{color-scheme:light;--bg:#e8eef6;--panel:#fff;--text:#2b3f58;--muted:#8193a8;--line:#d5e4f4;--head:#e3f1fe;--head-text:#1a6fc4;--bar:#1a8cf0;--card:#f2f6fb;--track:#dfe8f3}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;padding:20px;background:var(--bg);color:var(--text);font:16px/1.5 "jf-openhuninn","Microsoft JhengHei","Microsoft YaHei","Yu Gothic UI","Malgun Gothic",system-ui,sans-serif}
.dlg{width:100%;max-width:560px;background:var(--panel);border:3px solid var(--line);border-radius:34px;overflow:hidden;animation:rise .55s cubic-bezier(.22,1.2,.36,1) both}
.title{display:flex;align-items:center;gap:10px;padding:16px 28px;background:var(--head);color:var(--head-text);font-size:19px;transition:background .3s,color .3s}
.title i{width:10px;height:26px;border-radius:8px;background:var(--bar);animation:pop .5s .3s cubic-bezier(.22,1.2,.36,1) both;transition:background .3s}
.title #who{margin-left:auto;font-size:14px;opacity:.75}
.ib{flex:none;display:inline-flex;align-items:center;justify-content:center;gap:4px;height:32px;min-width:32px;padding:0;border:0;border-radius:999px;cursor:pointer;font:inherit;font-size:13px;background:#fff;color:var(--head-text);transition:filter .2s,transform .2s,background .2s}
.ib:hover{filter:brightness(.96);transform:translateY(-1px)}
.ib.new{height:34px;padding:0 8px 0 11px;gap:8px;color:var(--head-text)}
.ib.new b{display:inline-block;padding:1px 9px;border-radius:999px;background:#ff5d73;color:#fff;font-size:11px;font-weight:600;letter-spacing:.5px;line-height:18px;animation:blink 1.6s ease-in-out infinite}
@keyframes blink{50%{opacity:.55}}

/* dialogs: they spring in, and sink + fade out a little faster */
.ov{position:fixed;inset:0;display:grid;place-items:center;padding:20px;background:rgba(43,63,88,.38);opacity:0;visibility:hidden;pointer-events:none;transition:opacity .22s ease,visibility 0s .22s}
.ov.open{opacity:1;visibility:visible;pointer-events:auto;transition:opacity .22s ease,visibility 0s}
.set,.dlgc,.msg{position:relative;width:100%;background:var(--panel);border:3px solid var(--line);opacity:0;transform:translateY(18px) scale(.95);transition:transform .2s ease-in,opacity .18s ease-in}
.ov.open .set,.ov.open .dlgc,.ov.open .msg{opacity:1;transform:none;transition:transform .36s cubic-bezier(.22,1.2,.36,1),opacity .22s ease-out}
.set{display:grid;grid-template-columns:200px minmax(0,1fr);max-width:780px;height:min(580px,100%);border-radius:30px;overflow:hidden}
.snav{display:flex;flex-direction:column;gap:6px;padding:26px 14px;background:var(--card)}
.snav h3{margin:0 0 12px 12px;font-size:20px;font-weight:400}
.snav button{display:flex;align-items:center;justify-content:space-between;gap:8px;border:0;background:transparent;color:var(--text);font:inherit;font-size:15px;text-align:left;padding:11px 14px;border-radius:16px;cursor:pointer;transition:background .2s}
.snav button:hover{background:rgba(26,140,240,.08)}
.snav button.on{background:var(--head);color:var(--head-text)}
.snav .dot{flex:none;width:9px;height:9px;border-radius:50%;background:#ff5d73;animation:blink 1.6s ease-in-out infinite}
.spane{padding:26px 28px 28px;overflow:auto;min-width:0}
.spane[hidden]{display:none}
.spane h2{margin:0 0 16px;font-size:20px;font-weight:400;color:var(--text)}
.x{position:absolute;top:14px;right:14px;width:34px;height:34px;border:0;border-radius:50%;background:var(--card);color:var(--muted);cursor:pointer;font:inherit;font-size:18px;line-height:1;z-index:1;transition:filter .2s,transform .2s}
.x:hover{filter:brightness(.95);transform:rotate(90deg)}
.dlgc{max-width:660px;height:min(440px,100%);border-radius:30px;padding:24px 26px 22px;display:flex;flex-direction:column}
.dlgc h2,.msg h2{margin:0 0 16px;font-size:20px;font-weight:400}
.cl{flex:1;min-height:0;display:grid;grid-template-columns:190px minmax(0,1fr)}
.clv{overflow:auto;display:flex;flex-direction:column;gap:6px;padding-right:12px;border-right:1px solid var(--line)}
.clv button{display:flex;align-items:center;justify-content:space-between;gap:8px;border:0;background:transparent;color:var(--text);font:inherit;font-size:15px;text-align:left;padding:10px 14px;border-radius:14px;cursor:pointer;transition:background .2s}
.clv button:hover{background:rgba(26,140,240,.08)}
.clv button.on{background:var(--head);color:var(--head-text)}
.cld{overflow:auto;padding:0 6px 0 24px;min-width:0}
.cld h4{margin:0 0 .35rem;font-size:13.5px;font-weight:400;color:var(--muted)}
.cld p{margin:0 0 1.15rem;font-size:15px;line-height:1.65}
.msg{max-width:390px;border-radius:26px;padding:24px 26px 22px}
.msg.vup{max-width:440px}
.msg p{margin:0 0 22px;font-size:15px;line-height:1.65}
.vub{max-height:260px;overflow:auto;margin:0 0 20px;padding-right:8px}
.vub .vh{font-size:13.5px;color:var(--muted);margin:0 0 .15rem}
.vub p{margin:0 0 .9rem;font-size:15px;line-height:1.65}
.msg .btns{display:flex;justify-content:flex-end;gap:10px}
.btn{border:0;border-radius:999px;padding:8px 26px;font:inherit;font-size:15px;cursor:pointer;background:var(--bar);color:#fff;transition:filter .2s}
.btn:hover{filter:brightness(1.07)}
.btn.ghost{background:transparent;color:var(--text);box-shadow:inset 0 0 0 1.5px #b9c7d8}
.btn.ghost:hover{background:var(--head);filter:none}
@media(max-width:620px){.set{grid-template-columns:1fr;grid-template-rows:auto minmax(0,1fr)}.snav{flex-direction:row;align-items:center;padding:14px 60px 14px 14px;overflow:auto}.snav h3{display:none}.spane{padding:20px}}

/* settings content */
.app{display:flex;align-items:center;gap:14px;margin:2px 0 18px}
.app img{width:52px;height:52px;border-radius:16px;object-fit:cover;background:var(--track)}
.app b{font-weight:400;font-size:19px}
.app i{width:1.5px;height:18px;background:var(--line)}
.app span{font-size:16px;color:var(--muted)}
.grp{background:var(--card);border-radius:20px;overflow:hidden}
.grp.vis{overflow:visible}
.grp+.grp{margin-top:14px}
.rw{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 18px;font-size:15px;line-height:1.5}
.rw+.rw{border-top:1px solid var(--line)}
.rw small{display:block;font-size:13px;color:var(--muted);margin-top:1px}
.rw small.warn{color:#8a6200}
.rw b{font-weight:400}
.rw .n{flex:none;width:26px;height:26px;border-radius:50%;background:var(--head);color:var(--head-text);display:grid;place-items:center;font-size:13px;margin-right:2px}
.rw.step{justify-content:flex-start;align-items:flex-start;gap:12px}
.rw.lnk{width:100%;border:0;background:transparent;font:inherit;font-size:15px;color:inherit;text-align:left;cursor:pointer;transition:background .2s}
.rw.lnk:hover{background:rgba(26,140,240,.06)}
.rw.newv{flex-wrap:wrap}
.rw.newv .upbar{flex:1 0 100%;margin-top:2px}
.rw.newv .uerr{flex:1 0 100%;margin-top:0;font-size:13px;color:#c2447a}
.chev{flex:none;display:inline-flex;color:var(--muted)}
.chev svg{width:20px;height:20px;fill:currentColor}
.sec{margin:18px 4px 8px;font-size:14px;color:var(--muted)}
.sec:first-of-type{margin-top:0}
.ht{margin-left:6px;padding:1px 9px;border-radius:999px;background:var(--head);color:var(--head-text);font-size:11px;line-height:1.5;white-space:nowrap}
.ht.new{background:#ff5d73;color:#fff}
.rb{flex:none;display:inline-flex;align-items:center;gap:6px;border:1.5px solid #b9c7d8;background:transparent;color:var(--text);border-radius:999px;padding:5px 16px;font:inherit;font-size:14px;cursor:pointer;text-decoration:none;transition:background .2s,opacity .2s}
.rb:hover:not(:disabled){background:var(--head)}
.rb:disabled{opacity:.5;cursor:default}
.rb.on{background:var(--bar);border-color:var(--bar);color:#fff}
.rb svg{width:16px;height:16px}
.upbar{height:6px;border-radius:6px;background:var(--track);overflow:hidden;margin-top:12px}
.upbar i{display:block;height:100%;width:0;border-radius:6px;background:var(--bar);transition:width .3s}
.spin{animation:spin .9s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.sel{position:relative;flex:none}
.selb{display:inline-flex;align-items:center;gap:8px;border:0;background:#fff;color:var(--text);font:inherit;font-size:15px;cursor:pointer;padding:7px 12px 7px 16px;border-radius:12px;box-shadow:inset 0 0 0 1.5px var(--line);transition:box-shadow .2s}
.selb:hover{box-shadow:inset 0 0 0 1.5px #b9c7d8}
.selb .chv{width:18px;height:18px;fill:currentColor;color:var(--muted);transition:transform .3s cubic-bezier(.22,1,.36,1)}
.selb[aria-expanded=true] .chv{transform:rotate(180deg)}
.menu{position:absolute;right:0;top:calc(100% + 8px);width:230px;z-index:5;display:grid;grid-template-rows:0fr;visibility:hidden;transition:grid-template-rows .3s cubic-bezier(.22,1,.36,1),visibility 0s .3s}
.menu.open{grid-template-rows:1fr;visibility:visible;transition:grid-template-rows .3s cubic-bezier(.22,1,.36,1),visibility 0s}
.menui{overflow:hidden;min-height:0;background:var(--panel);border-radius:16px;box-shadow:0 0 0 1.5px var(--line),0 12px 30px rgba(43,63,88,.2)}
.mlist{padding:6px}
.menu button{display:flex;width:100%;align-items:center;justify-content:space-between;border:0;background:transparent;font:inherit;font-size:15px;color:var(--text);padding:12px 14px;border-radius:11px;cursor:pointer;text-align:left;transition:background .15s}
.menu button:hover{background:var(--card)}
.menu button .lb{flex:1;margin-left:12px}
.menu button .ck{width:18px;height:18px;fill:var(--bar);opacity:0;transform:scale(.6);transition:opacity .2s,transform .25s cubic-bezier(.22,1.4,.36,1)}
.menu button.on .ck{opacity:1;transform:none}
.fl{display:inline-flex;flex:none}
.fl svg{width:26px;height:17.5px;border-radius:3.4px;box-shadow:0 0 0 1px rgba(43,63,88,.16)}
.selb .fl{margin-right:-2px}
.sw{flex:none;position:relative;width:46px;height:26px;border:0;border-radius:999px;background:var(--track);cursor:pointer;transition:background .25s}
.sw i{position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.25);transition:transform .28s cubic-bezier(.22,1.2,.36,1)}
.sw[aria-checked=true]{background:var(--bar)}
.sw[aria-checked=true] i{transform:translateX(20px)}

/* main card */
.notice{margin:18px 22px 0;padding:14px 20px;border-radius:22px;background:#fff4d1;color:#8a6200;font-size:15px}
.notice.bad{background:#fde8f0;color:#c2447a}
.list{padding:4px 20px 2px}
.g{margin-top:10px;background:var(--card);border-radius:22px;padding:12px 18px;animation:fade .45s both}
.row{display:flex;align-items:center;gap:14px}
.ic{flex:none;width:44px;height:44px;border-radius:14px;object-fit:cover;background:var(--track);display:block}
.info{flex:1;min-width:0}
.name{font-size:18px;line-height:1.3}
.detail{font-size:14px;color:var(--muted);margin-top:3px;overflow-wrap:anywhere}
.pill{flex:none;font-size:14px;border-radius:999px;padding:5px 16px;transition:background .25s,color .25s}
.side{flex:none;display:flex;align-items:center;gap:8px}
.pill.wait,.pill.skip{background:#edf1f6;color:#8193a8}
.pill.run{background:#e3f1fe;color:#1a6fc4;animation:pulse 1.2s ease-in-out infinite}
.pill.ok{background:#e0f5ec;color:#168a5b}
.pill.bad{background:#fde8f0;color:#c2447a}
.upd{flex:none;border:0;cursor:pointer;font:inherit;font-size:14px;border-radius:999px;padding:6px 18px;background:var(--bar);color:#fff;transition:filter .2s,transform .2s,opacity .2s}
.upd:hover:not(:disabled){filter:brightness(1.07);transform:translateY(-1px)}
.upd:active:not(:disabled){transform:none}
.upd:disabled{opacity:.45;cursor:default}
.upd.again{background:var(--head);color:var(--head-text)}
.acts{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.go.alt{background:var(--head);color:var(--head-text);border:0;cursor:pointer;font:inherit;font-size:16px}
.go.alt:disabled{opacity:.45;cursor:default;transform:none;filter:none}
.bar{height:8px;border-radius:8px;background:var(--track);margin-top:12px;overflow:hidden;display:none}
.g.running .bar{display:block}
.bar b{display:block;height:100%;width:0;border-radius:8px;background:var(--bar);transition:width .4s ease}
.act{padding:16px 20px 22px;text-align:center;animation:fade .45s both}
.go{display:inline-flex;align-items:center;gap:8px;background:var(--bar);color:#fff;border-radius:999px;padding:9px 28px;font-size:16px;text-decoration:none;transition:filter .2s,transform .2s}
.go:hover{filter:brightness(1.07);transform:translateY(-1px)}
.go:active{transform:none}
.lgn{padding:6px 28px 8px;display:grid;gap:12px;text-align:center}
.lgn[hidden]{display:none}
.provs{display:grid;gap:10px;justify-items:center}
.provs .go{border:0;cursor:pointer;font:inherit;font-size:16px;min-width:240px;justify-content:center}
.lerr{color:#c2447a;font-size:14px}
.wait{padding:8px 28px 4px;text-align:center}
.wait[hidden]{display:none}
.wc{display:inline-block;font-size:34px;letter-spacing:.16em;padding:8px 26px;border-radius:22px;background:var(--gray);color:var(--head-text);user-select:all}
.wh{margin-top:10px;font-size:13px;color:var(--muted)}
.hint{padding:18px 28px 26px;text-align:center;font-size:15px;color:var(--muted)}
body.err .title{--head:#fde8f0;--head-text:#c2447a;--bar:#f06a9b;background:#fde8f0;color:#c2447a}
body.err .title i{background:#f06a9b}
@keyframes rise{from{opacity:0;transform:translateY(22px) scale(.96)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes pop{0%{transform:scaleY(0)}70%{transform:scaleY(1.25)}100%{transform:scaleY(1)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
<body>
<main class="dlg">
  <div class="title"><i></i><b id="ttl" style="font-weight:400">Getting ready</b><span id="who"></span><button class="ib" id="set" aria-label="Settings"><svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg></button></div>
  <div class="notice" id="notice" hidden></div>
  <div class="lgn" id="lgn" hidden>
    <div class="provs" id="provs"></div>
    <div class="lerr" id="lerr" hidden></div>
  </div>
  <div class="wait" id="wait" hidden><div class="wc" id="wcode"></div><div class="wh" data-t>The sign-in page will ask for this code. Do not enter it if you did not just open this program yourself.</div></div>
  <div class="list" id="list"></div>
  <div class="act" id="act" hidden><div class="acts"><button class="go alt" id="all" data-t>Update all</button><a class="go" id="go" target="_blank" rel="noopener"><span data-t>Open stats site</span><span>→</span></a></div></div>
  <div class="hint" id="hint">&nbsp;</div>
</main>

<div class="ov" id="ovs"><div class="set" role="dialog" aria-modal="true">
  <button class="x" data-close aria-label="close">✕</button>
  <nav class="snav">
    <h3 data-t>Settings</h3>
    <button data-tab="gen" class="on"><span data-t>General</span></button>
    <button data-tab="how"><span data-t>How to use</span></button>
    <button data-tab="about"><span data-t>About</span><i class="dot" id="dotAbout" hidden></i></button>
  </nav>
  <section class="spane" id="tab-gen">
    <h2 data-t>General</h2>
    <div class="sec" data-t>Language</div>
    <div class="grp vis">
      <div class="rw"><span data-t>Display language</span>
        <div class="sel"><button class="selb" id="langbtn" aria-haspopup="listbox" aria-expanded="false"><span class="fl" id="langflag"></span><span id="langcur">English</span><svg class="chv" viewBox="0 0 24 24" aria-hidden="true"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/></svg></button><div class="menu" id="langmenu" role="listbox"></div></div>
      </div>
    </div>
    <div class="sec" data-t>Updates</div>
    <div class="grp">
      <div class="rw"><div><span data-t>Allow automatic updates</span><small data-t>When a new version is found, download and install it automatically, then restart.</small></div><button class="sw" id="autoupd" role="switch" aria-checked="false"><i></i></button></div>
    </div>
  </section>
  <section class="spane" id="tab-how" hidden>
    <h2 data-t>How to use</h2>
    <div class="grp">
      <div class="rw step"><span class="n">1</span><span data-t>Open the in-game pull history once, so the program can find the latest history link.</span></div>
      <div class="rw step"><span class="n">2</span><span data-t>Come back here and press "Update" next to a game, or "Update all". Nothing runs automatically.</span></div>
      <div class="rw step"><span class="n">3</span><span data-t>The first time, choose how to sign in, sign in on the page that opens, then enter the code shown in this window. You will stay signed in afterwards.</span></div>
      <div class="rw step"><span class="n">4</span><span data-t>When it is done, open the stats site to see the result. Closing this tab ends the program.</span></div>
    </div>
    <div class="sec" data-t>Notes</div>
    <div class="grp">
      <div class="rw"><span data-t>If it says the history was never opened or the link has expired, open the in-game pull history again and then press Update.</span></div>
      <div class="rw"><span data-t>Your login is stored on this PC in %APPDATA%\wishbook. Do not share it.</span></div>
    </div>
  </section>
  <section class="spane" id="tab-about" hidden>
    <h2 data-t>About</h2>
    <div id="vabout"></div>
  </section>
</div></div>

<div class="ov" id="ovc"><div class="dlgc" role="dialog" aria-modal="true">
  <button class="x" data-close aria-label="close">✕</button>
  <h2 data-t>Changelog</h2>
  <div class="cl"><nav class="clv" id="clv"></nav><section class="cld" id="cld"></section></div>
</div></div>
<div class="ov" id="ovm"><div class="msg" role="alertdialog" aria-modal="true">
  <h2 id="msgt"></h2>
  <p id="msgp"></p>
  <div class="btns" id="msgb"></div>
</div></div>
<div class="ov" id="ovu"><div class="msg vup" role="alertdialog" aria-modal="true">
  <h2 id="vut"></h2>
  <div class="vub" id="vub"></div>
  <div class="btns" id="vubtn"></div>
</div></div>

<script>
// ---------------- languages: Traditional Chinese is the source text; the others are looked up by it ----------------
const LANGS = [['en', 'English'], ['zh-Hant', '繁體中文'], ['zh-Hans', '简体中文'], ['ja', '日本語'], ['ko', '한국어']];
// small vector flags (emoji flags show up as two letters on Windows)
const star = (cx, cy, r, rot = -90) => Array.from({ length: 10 }, (_, i) => { const a = (rot + i * 36) * Math.PI / 180, rr = i % 2 ? r * 0.4 : r; return (cx + rr * Math.cos(a)).toFixed(2) + ',' + (cy + rr * Math.sin(a)).toFixed(2); }).join(' ');
const flag = (id, inner) => '<svg viewBox="0 0 30 20" aria-hidden="true"><clipPath id="fc-' + id + '"><rect width="30" height="20" rx="3.4"/></clipPath><g clip-path="url(#fc-' + id + ')">' + inner + '</g></svg>';
const trig = (x, y, rot) => '<g transform="rotate(' + rot + ' ' + x + ' ' + y + ')"><rect x="' + (x - 2.2) + '" y="' + (y - 1.6) + '" width="4.4" height=".7" fill="#111"/><rect x="' + (x - 2.2) + '" y="' + (y - .35) + '" width="4.4" height=".7" fill="#111"/><rect x="' + (x - 2.2) + '" y="' + (y + .9) + '" width="4.4" height=".7" fill="#111"/></g>';
const FLAGS = {
  en: flag('en', '<rect width="30" height="20" fill="#fff"/>' + [0, 2, 4, 6, 8, 10, 12].map((i) => '<rect y="' + (i * 1.538).toFixed(2) + '" width="30" height="1.538" fill="#b22234"/>').join('') + '<rect width="12.4" height="10.77" fill="#3c3b6e"/>' + [1.6, 4.1, 6.6, 9.1].flatMap((x) => [1.7, 4.2, 6.7, 9.2].map((y) => '<circle cx="' + x + '" cy="' + (y - .2) + '" r=".55" fill="#fff"/>')).join('')),
  'zh-Hant': flag('zh-Hant', '<rect width="30" height="20" fill="#fe0000"/><rect width="15" height="10" fill="#000095"/><circle cx="7.5" cy="5" r="3.7" fill="#fff"/><circle cx="7.5" cy="5" r="3" fill="#000095"/><circle cx="7.5" cy="5" r="2.3" fill="#fff"/>'),
  'zh-Hans': flag('zh-Hans', '<rect width="30" height="20" fill="#de2910"/><polygon points="' + star(5.5, 5.2, 3.3) + '" fill="#ffde00"/>' + [[11, 1.8, -20], [13, 4, 10], [13, 7, -20], [11, 9.2, 5]].map((p) => '<polygon points="' + star(p[0], p[1], 1, p[2] - 90) + '" fill="#ffde00"/>').join('')),
  ja: flag('ja', '<rect width="30" height="20" fill="#fff"/><circle cx="15" cy="10" r="6" fill="#bc002d"/>'),
  ko: flag('ko', '<rect width="30" height="20" fill="#fff"/><path d="M10 10a5 5 0 0 1 10 0z" fill="#cd2e3a"/><path d="M10 10a5 5 0 0 0 10 0z" fill="#0047a0"/><circle cx="12.5" cy="10" r="2.5" fill="#0047a0"/><circle cx="17.5" cy="10" r="2.5" fill="#cd2e3a"/>' + trig(4.2, 4, -35) + trig(25.8, 16, -35) + trig(25.8, 4, 35) + trig(4.2, 16, 35)),
};
const I18N = {{I18N}};
let LANG = 'en';
const t = (zh, vars) => {
  let s = (LANG !== 'en' && I18N[LANG] && I18N[LANG][zh]) || zh;
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined ? vars[k] : m));
  return s;
};
const TITLE = { updating: 'Choose games to update', login: 'Waiting for login', idle: 'Choose games to update', running: 'Syncing pull history', done: 'Sync complete', error: 'Cannot sync' };
const HINT = { login: 'Finish logging in on the tab that just opened.', running: 'Syncing, please wait.', error: 'You can close this tab, fix the problem and run it again.' };
const LABEL = { wait: 'Not updated', run: 'Syncing', ok: 'Done', skip: 'Skipped', bad: 'Failed' };

const ICONS = {{GAME_ICONS}};
const cards = {};
const $ = (id) => document.getElementById(id);
let last = null, restarting = false;
const dlg = (id, on) => $(id).classList.toggle('open', on);
const mk = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
const cmpVer = (a, b) => { const x = String(a || 0).split('.').map(Number), y = String(b || 0).split('.').map(Number); for (let i = 0; i < Math.max(x.length, y.length); i++) { const d = (x[i] || 0) - (y[i] || 0); if (d) return d; } return 0; };
const IC_GEAR = '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>';
const IC_SEARCH = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>';
const IC_SYNC = '<svg class="spin" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg>';
const IC_CHEV = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>';

// static texts carry data-t; they are re-translated whenever the language changes
document.querySelectorAll('[data-t]').forEach((e) => { e.dataset.zh = e.textContent; });
function applyLang() {
  document.documentElement.lang = LANG;
  document.querySelectorAll('[data-t]').forEach((e) => { e.textContent = t(e.dataset.zh); });
  document.title = t('Wishbook | Sync');
  $('set').setAttribute('aria-label', t('Settings'));
  $('langcur').textContent = (LANGS.find((l) => l[0] === LANG) || LANGS[1])[1];
  $('langflag').innerHTML = FLAGS[LANG] || '';
  document.querySelectorAll('#langmenu button').forEach((b) => b.classList.toggle('on', b.dataset.lang === LANG));
  if (last) { $('set').dataset.key = ''; render(last); }
}

// ---------------- dialogs ----------------
document.querySelectorAll('.ov').forEach((o) => { o.onclick = (e) => { if (e.target === o || e.target.hasAttribute('data-close')) o.classList.remove('open'); }; });
document.addEventListener('keydown', (e) => { if (e.key !== 'Escape') return; const top = [...document.querySelectorAll('.ov.open')].pop(); if (top) top.classList.remove('open'); });  // nested dialogs close one at a time
function showMsg(title, text, buttons) {
  $('msgt').textContent = title; $('msgp').textContent = text;
  const row = $('msgb'); row.textContent = '';
  buttons.forEach(([label, cls, fn]) => { const e = mk('button', cls, label); e.onclick = () => { dlg('ovm', false); if (fn) fn(); }; row.append(e); });
  dlg('ovm', true);
}
function post(path, body) { return fetch(path, { method: 'POST', headers: { 'X-Wishbook': '1', 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }).catch(() => {}); }
const startUpdate = () => post('/update');
function checkNow() { return post('/check'); }
// "V1.2.3 Wishbook version update": what is new and two buttons (the dialog that pops up when a new version is found)
function versionDialog(v) {
  $('vut').textContent = t('V{v} Wishbook Version Update', { v: v.latest });
  const body = $('vub'); body.textContent = '';
  const fresh = (v.history || []).filter((h) => cmpVer(h.version, v.current) > 0 && h.note);
  if (fresh.length) fresh.forEach((h) => body.append(mk('div', 'vh', 'V' + h.version + (h.date ? '  ' + h.date : '')), mk('p', '', h.note)));
  else body.append(mk('p', '', v.note || t('A new version is available')));
  const row = $('vubtn'); row.textContent = '';
  [[t('Later'), 'btn ghost'], [t('Update now'), 'btn', startUpdate]].forEach(([label, cls, fn]) => { const e = mk('button', cls, label); e.onclick = () => { dlg('ovu', false); if (fn) fn(); }; row.append(e); });
  dlg('ovu', true);
}
let pendingCheck = 0, promptedStartup = false;  // pendingCheck: when the user pressed "Check"; the verdict opens once the answer is in
function verdictDialog(v) {
  if (!v.latest) return showMsg(t('Notice'), t('Cannot reach the site. Please try again later.'), [[t('OK'), 'btn']]);
  if (!v.newer) return showMsg(t('Notice'), t('You are on the latest version. No update needed.'), [[t('OK'), 'btn']]);
  if (!v.canUpdate) return showMsg(t('New version found'), t('New version V{v} found.', { v: v.latest }), [[t('OK'), 'btn']]);
  versionDialog(v);
}
function openChangelog(v) {
  const nav = $('clv'), det = $('cld'), items = v.history || [];
  nav.textContent = ''; det.textContent = '';
  const show = (h, b) => {
    nav.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
    det.textContent = '';
    det.append(mk('h4', '', t('Updated:')), mk('p', '', h.date || '—'), mk('h4', '', t('What\'s new:')), mk('p', '', h.note || t('(no description)')));
  };
  if (!items.length) det.append(mk('p', '', t('No changelog available (it cannot be loaded while offline).')));
  items.forEach((h, i) => {
    const b = mk('button'); b.append(mk('span', '', 'V' + h.version));
    if (h.version === v.current) b.append(mk('span', 'ht', t('Current')));
    else if (v.newer && cmpVer(h.version, v.current) > 0) b.append(mk('span', 'ht new', t('New')));
    b.onclick = () => show(h, b); nav.append(b);
    if (!i) show(h, b);
  });
  dlg('ovc', true);
}

// ---------------- settings window ----------------
let lastCheck = 0;
function autoCheck() {  // opening "About" asks the site (at most every 20s; straight away when there is no verdict yet)
  const v = last && last.version;
  if (Date.now() - lastCheck < 20000 && v && v.latest) return;
  lastCheck = Date.now(); checkNow();
}
function showTab(name) {
  if (name === 'about') autoCheck();
  document.querySelectorAll('.snav [data-tab]').forEach((b) => b.classList.toggle('on', b.dataset.tab === name));
  ['gen', 'how', 'about'].forEach((k) => { $('tab-' + k).hidden = k !== name; });
}
document.querySelectorAll('.snav [data-tab]').forEach((b) => { b.onclick = () => showTab(b.dataset.tab); });
$('set').onclick = () => { showTab(last && last.version && last.version.newer ? 'about' : 'gen'); dlg('ovs', true); };  // a new version opens straight on "About"
// language dropdown + auto-update switch
const langMenu = $('langmenu'), langBtn = $('langbtn');
const IC_CK = '<svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>';
const menuIn = mk('div', 'menui'), menuList = mk('div', 'mlist'); menuIn.append(menuList); langMenu.append(menuIn);  // the box grows downward from the button
LANGS.forEach(([code, label]) => { const b = mk('button'); b.dataset.lang = code; b.innerHTML = '<span class="fl">' + FLAGS[code] + '</span><span class="lb"></span>' + IC_CK; b.querySelector('.lb').textContent = label; b.onclick = () => { setLang(code); closeMenu(); }; menuList.append(b); });
function closeMenu() { langMenu.classList.remove('open'); langBtn.setAttribute('aria-expanded', 'false'); }
langBtn.onclick = (e) => { e.stopPropagation(); const on = !langMenu.classList.contains('open'); langMenu.classList.toggle('open', on); langBtn.setAttribute('aria-expanded', String(on)); };
document.addEventListener('click', closeMenu);
applyLang();  // flag + label of the current language (also marks the right menu row)
let localSettingsAt = 0;  // a change made here wins over a state that was fetched before the program has stored it
function changeSetting(patch) { localSettingsAt = Date.now(); if (last) last.settings = { ...(last.settings || {}), ...patch }; return post('/settings', patch); }
function setLang(code) { if (code === LANG) return; LANG = code; changeSetting({ lang: code }); applyLang(); }
$('autoupd').onclick = () => { const on = $('autoupd').getAttribute('aria-checked') !== 'true'; $('autoupd').setAttribute('aria-checked', String(on)); changeSetting({ autoUpdate: on }); };
function renderSettings(st) {
  if (!st || Date.now() - localSettingsAt < 1500) return;
  if (st.lang !== LANG && LANGS.some((l) => l[0] === st.lang)) { LANG = st.lang; applyLang(); }
  $('autoupd').setAttribute('aria-checked', String(!!st.autoUpdate));
}

function renderVersion(v, s) {
  const btn = $('set');
  if (!v) return;
  if (pendingCheck && !v.checking && Date.now() - pendingCheck > 900) { pendingCheck = 0; verdictDialog(v); }
  // opening the program: if a new version is waiting (and "allow automatic updates" is off) show the update dialog once
  if (!promptedStartup && v.newer && v.canUpdate && s.phase === 'idle' && s.settings && !s.settings.autoUpdate) { promptedStartup = true; versionDialog(v); }
  const key = JSON.stringify([v, s.phase, s.notice, !!pendingCheck, LANG]);
  if (btn.dataset.key === key) return;
  btn.dataset.key = key;
  btn.className = 'ib' + (v.newer ? ' new' : '');
  btn.innerHTML = v.newer ? IC_GEAR + '<span>' + t('New version') + '</span><b>NEW</b>' : IC_GEAR;  // the settings button itself carries the "new version" look
  btn.title = v.newer ? t('New version V{v} (open for details)', { v: v.latest }) : t('Settings');
  $('dotAbout').hidden = !v.newer;
  const box = $('vabout'); box.textContent = '';
  const app = mk('div', 'app'), img = mk('img'); img.src = document.querySelector('link[rel=icon]').href; img.alt = '';
  app.append(img, mk('b', '', 'Wishbook'), mk('i'), mk('span', '', 'V' + v.current)); box.append(app);
  if (v.newer) {  // the update is its own group, above the log / check group
    const upg = mk('div', 'grp'), busy = s.phase === 'updating', pct = (/(\d+)%/.exec(s.notice || '') || [])[1];
    const when = (v.history || []).find((h) => h.version === v.latest);
    const row = mk('div', 'rw newv'), left = mk('div');
    left.append(mk('b', '', t('New version V{v} found', { v: v.latest })), mk('small', 'warn', [v.size ? (v.size / 1048576).toFixed(1) + ' MB' : '', when && when.date].filter(Boolean).join('・') || t('A new version is available')));
    row.append(left);
    if (v.canUpdate) { const b = mk('button', 'rb on', busy ? (pct ? t('Downloading {p}%', { p: pct }) : t('Updating')) : t('Update now')); b.disabled = s.phase !== 'idle'; b.onclick = startUpdate; row.append(b); }
    if (busy) { const bar = mk('div', 'upbar'), fill = mk('i'); fill.style.width = (pct || 3) + '%'; bar.append(fill); row.append(bar); }
    if (v.error) row.append(mk('div', 'uerr', v.error));
    upg.append(row); box.append(upg);
  }
  const grp = mk('div', 'grp');
  const log = mk('button', 'rw lnk'), chev = mk('span', 'chev'); chev.innerHTML = IC_CHEV;
  log.append(mk('span', '', t('View changelog')), chev); log.onclick = () => openChangelog(v);
  const chk = mk('div', 'rw'), busyChk = v.checking || !!pendingCheck;
  const b = mk('button', 'rb'); b.innerHTML = (busyChk ? IC_SYNC : IC_SEARCH) + '<span>' + t('Check') + '</span>'; b.disabled = busyChk;
  b.onclick = () => { pendingCheck = Date.now(); lastCheck = pendingCheck; btn.dataset.key = ''; checkNow(); renderVersion(v, s); };
  chk.append(mk('span', '', t('Check for updates')), b);
  grp.append(log, chk); box.append(grp);
}

// ---------------- the main card ----------------
const ask = (games) => post('/sync', { games });
$('all').onclick = () => ask(Object.keys(cards));
const PNAME = { discord: 'Discord', google: 'Google' };
let loginKey = '';
function renderLogin(lg) {
  const key = JSON.stringify([lg.providers, LANG]);
  if (key !== loginKey) {  // rebuilt only when something changed
    loginKey = key;
    const box = $('provs'); box.textContent = '';
    if (!lg.providers.length) box.textContent = t('Sign-in is not open yet.');
    for (const p of lg.providers) {
      const b = document.createElement('button'); b.className = 'go';
      b.textContent = t('Sign in with {p}', { p: PNAME[p] || p });
      b.onclick = () => post('/login', { provider: p });
      box.append(b);
    }
  }
  $('lerr').textContent = lg.error || '';
  $('lerr').hidden = !lg.error;
}
function render(s) {
  renderSettings(s.settings);
  document.body.classList.toggle('err', s.phase === 'error');
  const lg = s.login || {};
  const signIn = !!lg.needed && !lg.waiting;  // the card is up: the games stay hidden until the account is signed in
  $('lgn').hidden = !signIn; $('list').hidden = !!lg.needed;
  if (signIn) renderLogin(lg);
  $('wait').hidden = !(lg.needed && lg.waiting && lg.code); $('wcode').textContent = lg.code || '';
  $('ttl').textContent = t(signIn ? 'Sign in' : (TITLE[s.phase] || 'Syncing pull history'));
  $('who').textContent = s.member || '';
  const hint = HINT[s.phase];
  $('hint').textContent = hint ? t(hint) : '';
  $('hint').hidden = !hint || !!(lg.waiting && lg.code);  // the yellow line above already says it while the code is on screen
  $('act').hidden = !['idle', 'running', 'updating', 'done'].includes(s.phase) || !s.site || !!lg.needed;
  $('all').hidden = s.phase === 'done';
  $('all').disabled = s.phase !== 'idle';
  if (s.site) $('go').href = s.site;
  renderVersion(s.version, s);
  const n = $('notice');
  n.hidden = !s.notice || s.phase === 'updating';  // the update progress is written inside the dialog only
  n.textContent = s.notice || '';
  n.className = 'notice' + (s.phase === 'error' ? ' bad' : '');
  s.games.forEach((g, i) => {
    let c = cards[g.key];
    if (!c) {
      const el = document.createElement('div');
      el.className = 'g';
      el.style.animationDelay = (0.15 + i * 0.08) + 's';
      el.innerHTML = '<div class="row"><img class="ic" alt=""><div class="info"><div class="name"></div><div class="detail"></div></div><div class="side"><span class="pill"></span><button class="upd"></button></div></div><div class="bar"><b></b></div>';
      $('list').append(el);
      el.querySelector('.ic').src = ICONS[g.key] || '';
      el.querySelector('.upd').onclick = () => ask([g.key]);
      c = cards[g.key] = { el, name: el.querySelector('.name'), detail: el.querySelector('.detail'), pill: el.querySelector('.pill'), btn: el.querySelector('.upd'), fill: el.querySelector('.bar b') };
    }
    c.name.textContent = t(g.name);
    c.detail.textContent = g.detail || '';
    c.detail.hidden = !g.detail;
    c.pill.textContent = g.queued ? t('Queued') : t(LABEL[g.status]);
    c.pill.className = 'pill ' + g.status;
    c.pill.hidden = g.status === 'wait' && !g.queued && s.phase === 'idle';  // nothing asked yet: just the button
    c.btn.hidden = !['idle', 'running', 'updating'].includes(s.phase) || g.status === 'run' || g.queued;
    c.btn.disabled = s.phase !== 'idle';
    c.btn.textContent = t(g.status === 'wait' ? 'Update' : 'Update again');
    c.btn.classList.toggle('again', g.status !== 'wait');
    c.el.classList.toggle('running', g.status === 'run' && g.progress != null);
    c.fill.style.width = Math.round((g.progress || 0) * 100) + '%';
  });
}

async function tick() {
  try {
    const r = await fetch('/state', { cache: 'no-store' });
    last = await r.json();
    if (restarting && !last.restarting) { location.reload(); return; }
    restarting = !!last.restarting;
    render(last);
    if (last.phase === 'done' || last.phase === 'error') return;
  } catch (e) {
    if (restarting) { setTimeout(tick, 800); return; }  // the new process is taking over this port
    return;  // the local server is gone: keep what is on screen
  }
  setTimeout(tick, 700);
}
tick();
</script>
"""
