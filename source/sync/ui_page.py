"""The local progress page shown in the browser while wishbook_sync.exe runs (served from 127.0.0.1, polls /state)."""

PAGE = r"""<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wishbook | Sync</title>
<link rel="icon" href="{{ICON}}">
<style>
@font-face{font-family:"jf-openhuninn";src:local("jf-openhuninn-2.1"),local("jf open 粉圓 2.1"),url("https://cdn.jsdelivr.net/gh/justfont/open-huninn-font@v2.1/font/jf-openhuninn-2.1.ttf") format("truetype");font-display:swap}
/* everything is sized in rem and the root size follows both the width and the height of the window: big screens scale it up, small ones scale it down */
html{font-size:clamp(12px,min(.55vw + 10px,2.05vh),24px)}
:root{color-scheme:light;--bg:#e8eef6;--card:#fff;--card2:#f2f6fb;--text:#2b3f58;--muted:#8193a8;--line:#e1e8f0;--acc:#1a8cf0;--on-acc:#fff;--soft:#e3f1fe;--good:#1fa971;--on-good:#fff;--bad:#d63f6c;--on-bad:#fff;--track:#e3eaf3;--hover:#e6eef8;--scrim:rgba(30,44,64,.45);--shadow:0 .5rem 1.5rem rgba(43,63,88,.14)}
:root[data-mode=dark]{color-scheme:dark;--bg:#0e1015;--card:#1e222b;--card2:#272c37;--text:#eceff5;--muted:#9aa3b5;--line:#313746;--acc:#6bb8ff;--on-acc:#0b1a2b;--soft:#223348;--good:#62d8a6;--on-good:#0b2a1f;--bad:#ff8aa8;--on-bad:#2a0b14;--track:#2c3340;--hover:#323949;--scrim:rgba(5,6,9,.62);--shadow:0 .5rem 1.5rem rgba(0,0,0,.5)}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:var(--bg);color:var(--text);font:.9375rem/1.5 "jf-openhuninn","Microsoft JhengHei","Microsoft YaHei","Yu Gothic UI","Malgun Gothic",system-ui,sans-serif;transition:background .3s,color .3s}
button{font:inherit;color:inherit;cursor:pointer}
a{color:inherit;text-decoration:none}
svg{display:block}
.stage{min-height:100vh;display:grid;place-items:center;padding:1rem}

/* window: one size in every state */
.win{position:relative;width:32rem;max-width:100%;height:min(35rem,calc(100vh - 2rem));background:var(--card);border-radius:1.75rem;box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column;animation:rise .5s cubic-bezier(.22,1.2,.36,1) both}
.win>*{flex:none}
.win>.body{flex:1 1 0;min-height:0}
.hd{display:flex;align-items:center;gap:.75rem;padding:1rem 1.125rem .5rem 1.25rem}
.hd .lg{width:2.25rem;height:2.25rem;object-fit:contain;animation:pop .5s .15s cubic-bezier(.22,1.3,.36,1) both}
.hd .tt{min-width:0;flex:1}
.hd .tt b{display:block;font-weight:400;font-size:1.125rem;line-height:1.2}
.who{display:flex;align-items:center;gap:.5rem;padding:.25rem .625rem .25rem .25rem;border-radius:62rem;background:var(--card2);font-size:.8125rem;color:var(--muted);max-width:9rem}
.who i{width:1.5rem;height:1.5rem;border-radius:50%;background:var(--acc);color:var(--on-acc);display:grid;place-items:center;font-style:normal;font-size:.75rem;flex:none}
.who span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ib{position:relative;width:2.375rem;height:2.375rem;border:0;border-radius:.75rem;background:var(--card2);color:var(--muted);display:grid;place-items:center;flex:none;transition:background .2s,color .2s,transform .2s}
.ib:hover{background:var(--hover);color:var(--text)}
.ib:active{transform:scale(.95)}
.ib svg{width:1.25rem;height:1.25rem;transition:transform .45s cubic-bezier(.22,1.6,.36,1)}
.ib:hover svg{transform:rotate(60deg)}
.ib .nw{position:absolute;right:-.25rem;top:-.375rem;background:var(--bad);color:var(--on-bad);font-size:.625rem;line-height:1;padding:.1875rem .375rem;border-radius:.5rem;animation:blink 1.6s ease-in-out infinite}
.btn{border:0;border-radius:.875rem;background:var(--acc);color:var(--on-acc);padding:.6875rem 1.125rem;display:inline-flex;align-items:center;justify-content:center;gap:.5rem;font-size:.9375rem;transition:filter .2s,transform .2s}
.btn:hover:not(:disabled){filter:brightness(1.07);transform:translateY(-1px)}
.btn:active:not(:disabled){transform:scale(.97)}
.btn:disabled{background:var(--track);color:var(--muted);cursor:default}
.btn.alt{background:var(--card2);color:var(--text)}
.btn.alt svg{color:var(--acc)}
.btn.alt:disabled svg{color:var(--muted)}
.hero .btn.alt,.gc .btn.alt{background:var(--card)}
.btn.sm{padding:.4375rem .875rem;font-size:.875rem;border-radius:.75rem}
.btn.ghost{background:var(--card2);color:var(--text)}
.gc .btn.ghost{background:var(--card)}
.btn svg{width:1.125rem;height:1.125rem;flex:none}
.btn:hover:not(:disabled) .ic-redo{animation:turn .55s cubic-bezier(.3,1.2,.5,1)}
.btn:hover .ic-arr .mv{animation:nudge .6s ease}
.ic-redo{transform-origin:50% 50%}
.spin{animation:spin .9s linear infinite}
.ft{display:flex;gap:.625rem;padding:.5rem 1.25rem 1.25rem}
.ft .btn{flex:1}
.chip{display:inline-flex;align-items:center;gap:.25rem;font-size:.75rem;line-height:1.125rem;padding:.125rem .625rem;border-radius:.5rem;white-space:nowrap;border:0}
.chip.wait,.chip.skip{background:var(--track);color:var(--muted)}
.chip.q{background:var(--card);color:var(--muted)}
.chip.run{background:var(--acc);color:var(--on-acc)}
.chip.ok{background:var(--good);color:var(--on-good);animation:pop .4s cubic-bezier(.22,1.5,.36,1)}
.chip.bad{background:var(--bad);color:var(--on-bad);animation:pop .4s cubic-bezier(.22,1.5,.36,1);cursor:pointer}
.chip svg{width:.75rem;height:.75rem}
.bar{height:.5rem;border-radius:.5rem;background:var(--track);overflow:hidden}
.bar i{display:block;height:100%;width:0;border-radius:.5rem;background:var(--acc);transition:width .5s ease}
.gimg{display:block;object-fit:cover;background:var(--track)}

/* main window: the games on top, the chosen game below */
.dock{display:flex;gap:.5rem;justify-content:center;padding:.25rem 1.25rem .5rem}
.gi{position:relative;border:0;background:transparent;padding:.1875rem;border-radius:1.125rem;transition:transform .25s cubic-bezier(.22,1.3,.36,1);animation:pop .45s cubic-bezier(.22,1.3,.36,1) backwards}
.gi img{width:3.25rem;height:3.25rem;border-radius:.9375rem;display:block}
.gi:hover{transform:translateY(-.3125rem) scale(1.1)}
.gi.on::after{content:"";position:absolute;left:50%;bottom:-.25rem;width:.375rem;height:.375rem;margin-left:-.1875rem;border-radius:50%;background:var(--acc)}
.gi .bd{position:absolute;right:-.125rem;top:-.125rem;width:.875rem;height:.875rem;border-radius:50%;border:.15625rem solid var(--card);background:var(--acc)}
.gi .bd.ok{background:var(--good)}.gi .bd.bad{background:var(--bad)}.gi .bd.q{background:var(--muted)}
.gi .bd.run{animation:pulse 1.4s ease-in-out infinite}
.body{padding:.25rem 1.25rem;display:flex}
.hero{flex:1;background:var(--card2);border-radius:1.5rem;padding:1rem;display:flex;flex-direction:column;min-height:0}
.hero .top{display:flex;align-items:center;gap:.875rem}
.hero .gimg{width:4.25rem;height:4.25rem;border-radius:1.25rem;flex:none}
.hero .gimg.pop{animation:swap .28s cubic-bezier(.22,1.4,.36,1)}
.hero .tx{min-width:0;flex:1}
.hero .nm{font-size:1.1875rem;line-height:1.25}
.hero .meta{color:var(--muted);font-size:.8125rem;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}
.pools{margin:.875rem 0 .75rem;display:grid;gap:.375rem;align-content:start;flex:1;min-height:0;overflow:hidden}
.pools.many{grid-template-columns:1fr 1fr}  /* seven pools (Wuthering Waves) go two by two so they still fit */
.pools.many .pl{gap:.5rem;padding:.4375rem .625rem}
.pl{display:grid;grid-template-columns:1.375rem 1fr auto;gap:.625rem;align-items:center;background:var(--card);border-radius:.875rem;padding:.4375rem .75rem}
.pl .d{width:1.375rem;height:1.375rem;border-radius:.5rem;display:grid;place-items:center;background:var(--track);color:var(--muted)}
.pl .d svg{width:.8125rem;height:.8125rem}
.pl.ok .d{background:var(--good);color:var(--on-good)}
.pl.run .d{background:var(--acc);color:var(--on-acc)}
.pl.bad .d{background:var(--bad);color:var(--on-bad)}
.pl .n{font-size:.875rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pl .c{font-size:.8125rem;color:var(--muted);white-space:nowrap}
.pl.run .c{color:var(--acc)}
.hero>.btn{width:100%}
.hero>.btn[hidden]{display:none}

/* sign-in and code */
.cover{flex:1;display:grid;align-content:center;justify-items:center;text-align:center;padding:1rem 2rem 2rem;gap:.375rem}
.cover .big{width:4.5rem;height:4.5rem;object-fit:contain}
.cover h2{margin:.25rem 0 0;font-weight:400;font-size:1.375rem}
.cover p{margin:0 0 .875rem;color:var(--muted);font-size:.875rem;max-width:20rem}
.prov{width:100%;max-width:18rem;border:0;border-radius:.875rem;padding:.6875rem 1.125rem;display:flex;align-items:center;justify-content:center;gap:.625rem;color:#fff;margin-bottom:.625rem;transition:transform .2s,filter .2s}
.prov:hover{filter:brightness(1.07)}
.prov:active{transform:scale(.97)}
.prov svg{width:1.25rem;height:1.25rem;transition:transform .35s cubic-bezier(.22,1.6,.36,1)}
.prov:hover svg{transform:rotate(-12deg) scale(1.1)}
.prov.discord{background:#5865f2}
.prov.google{background:#fff;color:#1f1f1f;box-shadow:inset 0 0 0 1px #dadce0}
.lerr{color:var(--bad);font-size:.875rem;max-width:20rem}
.code{font-size:2.5rem;letter-spacing:.14em;line-height:1.2;padding:.5rem 1.5rem;border-radius:1.25rem;background:var(--card2);color:var(--acc);margin:.5rem 0;user-select:all;min-width:9rem}
.copy{margin:.25rem 0 .5rem}
.copy svg{transition:transform .25s cubic-bezier(.22,1.4,.36,1)}
.copy:hover:not(:disabled) svg{transform:translate(1px,1px)}
.warn{font-size:.8125rem;color:var(--muted);max-width:21rem}

/* layers: the settings page and the popups */
.layer{position:absolute;inset:0;display:flex;visibility:hidden;pointer-events:none;transition:visibility 0s .36s}
.layer.on{visibility:visible;pointer-events:auto;transition:visibility 0s}
.scrim{position:absolute;inset:0;background:var(--scrim);opacity:0;transition:opacity .3s cubic-bezier(.4,0,.2,1)}
.layer.on .scrim{opacity:1}
.sheet{position:absolute;inset:0;background:var(--card);display:flex;flex-direction:column;transform:translateY(100%);will-change:transform;transition:transform .3s cubic-bezier(.4,0,.2,1)}
.layer.on .sheet{transform:none;transition:transform .42s cubic-bezier(.22,1.1,.36,1)}
.shd{display:flex;align-items:center;gap:.75rem;padding:1.125rem 1.25rem .875rem}
.shd .av{width:2.75rem;height:2.75rem;border-radius:50%;background:var(--acc);color:var(--on-acc);display:grid;place-items:center;font-size:1.125rem;flex:none}
.shd .ltx{flex:1;min-width:0}
.shd .ltx b{display:block;font-weight:400;font-size:1.125rem;line-height:1.25;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.shd .ltx small{display:block;color:var(--muted);font-size:.8125rem}
.ib.close:hover svg{transform:rotate(90deg)}
.scroll{flex:1;min-height:0;overflow:auto;padding:0 1.25rem 1.25rem;display:grid;gap:.5rem;align-content:start;scrollbar-width:none;--ft:0px;--fb:0px;-webkit-mask-image:linear-gradient(to bottom,transparent 0,#000 var(--ft),#000 calc(100% - var(--fb)),transparent 100%);mask-image:linear-gradient(to bottom,transparent 0,#000 var(--ft),#000 calc(100% - var(--fb)),transparent 100%)}
.scroll::-webkit-scrollbar{display:none}
.scroll.fade-t{--ft:1rem}.scroll.fade-b{--fb:1.5rem}
.gh{display:flex;align-items:center;gap:.5rem;color:var(--muted);font-size:.8125rem;margin:.25rem .25rem .5rem}
.gh svg{width:1rem;height:1rem;color:var(--acc)}
.gc{background:var(--card2);border-radius:1.25rem}
.li{display:flex;align-items:center;gap:.75rem;width:100%;padding:.75rem .875rem;border:0;background:transparent;text-align:left;border-radius:0}
.gc>.li:first-child{border-radius:1.25rem 1.25rem 0 0}
.gc>.li:last-child{border-radius:0 0 1.25rem 1.25rem}
.gc>.li:only-child{border-radius:1.25rem}
.gc>.li+.li,.gc>.acc+.li,.gc>.bar+.li{box-shadow:inset 0 1px 0 var(--line)}
.rico{width:2.375rem;height:2.375rem;border-radius:.75rem;background:var(--acc);color:var(--on-acc);display:grid;place-items:center;flex:none}
.rico svg{width:1.25rem;height:1.25rem;transition:transform .3s cubic-bezier(.22,1.6,.36,1)}
.li.lf:hover{background:var(--hover)}
.li:hover .rico .ic-globe{transform:rotate(40deg)}
.li:hover .rico .ic-moon{transform:rotate(-18deg) scale(1.1)}
.li:hover .rico .ic-sun{transform:rotate(45deg) scale(1.1)}
.li:hover .rico .ic-tag{transform:rotate(-16deg)}
.li:hover .rico .ic-bolt{transform:translate(1px,-1px) scale(1.18)}
.li:hover .rico .ic-list{transform:scale(1.15)}
.li:hover .rico .ic-help{transform:rotate(-14deg) scale(1.12)}
.ltx{flex:1;min-width:0}
.ltx b{display:block;font-weight:400;font-size:.9375rem;line-height:1.3}
.ltx small{display:block;color:var(--muted);font-size:.8125rem;line-height:1.4;margin-top:.125rem}
.ltx small.err{color:var(--bad)}
.li .chv{width:1.125rem;height:1.125rem;color:var(--muted);flex:none;transition:transform .3s cubic-bezier(.22,1.4,.36,1)}
.li.lf.open .chv{transform:rotate(180deg)}
.acc{display:grid;grid-template-rows:0fr;transition:grid-template-rows .3s cubic-bezier(.22,1,.36,1)}
.acc.on{grid-template-rows:1fr}
.acc>.in{overflow:hidden;min-height:0}
.gc .acc .pad{padding:.25rem .875rem .875rem}
.upbar{margin:0 .875rem .75rem}
.selb{display:inline-flex;align-items:center;gap:.5rem;border:0;background:var(--card);color:var(--text);padding:.4375rem .625rem .4375rem .75rem;border-radius:.75rem;font-size:.875rem;transition:background .2s}
.selb:hover{background:var(--hover)}
.selb .chv{width:1.125rem;height:1.125rem;color:var(--muted);transition:transform .3s cubic-bezier(.22,1.4,.36,1)}
.selb.open .chv{transform:rotate(180deg)}
.fl{display:inline-flex;flex:none;width:1.375rem;height:.9375rem}
.fl svg{width:100%;height:100%;border-radius:.1875rem;box-shadow:0 0 0 1px var(--line)}
.dd{position:relative;flex:none}
.menu{position:absolute;right:0;top:calc(100% + .5rem);width:12.5rem;z-index:5;display:grid;grid-template-rows:0fr;visibility:hidden;transition:grid-template-rows .28s cubic-bezier(.22,1,.36,1),visibility 0s .28s}
.menu.on{grid-template-rows:1fr;visibility:visible;transition:grid-template-rows .28s cubic-bezier(.22,1,.36,1),visibility 0s}
.menu>.in{overflow:hidden;min-height:0;background:var(--card);border-radius:1rem;box-shadow:0 0 0 1.5px var(--line),var(--shadow);padding:0 .375rem}
.menu>.in>.mi:first-child{margin-top:.375rem}.menu>.in>.mi:last-child{margin-bottom:.375rem}
.mi{display:flex;align-items:center;gap:.625rem;width:100%;border:0;background:transparent;padding:.5625rem .625rem;border-radius:.625rem;font-size:.875rem;text-align:left;transition:background .15s}
.mi:hover{background:var(--card2)}
.mi span:not(.fl){flex:1}
.mi .fl{width:1.5rem;height:1rem}
.mi>svg{width:1rem;height:1rem;color:var(--acc)}
.mi.on{color:var(--acc)}
.sw{position:relative;width:2.875rem;height:1.625rem;border:0;border-radius:62rem;background:var(--track);flex:none;transition:background .25s}
.sw i{position:absolute;top:.1875rem;left:.1875rem;width:1.25rem;height:1.25rem;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.25);transition:transform .28s cubic-bezier(.22,1.2,.36,1)}
.sw[aria-checked=true]{background:var(--acc)}
.sw[aria-checked=true] i{transform:translateX(1.25rem)}
.theme{position:relative;width:4.375rem;height:2.375rem;padding:0;border:1px solid rgba(0,0,0,.06);border-radius:62rem;background:#9fd3ff;overflow:hidden;flex:none;transition:background .4s}
:root[data-mode=dark] .theme{background:#1b2350}
.theme .orb{position:absolute;top:.3125rem;left:.3125rem;width:1.625rem;height:1.625rem;border-radius:50%;background:#ffd45c;transition:transform .5s cubic-bezier(.22,1.3,.36,1),background-color .5s,box-shadow .5s}
:root[data-mode=dark] .theme .orb{transform:translateX(1.9375rem);background:#e8eaff;box-shadow:inset -.4rem -.15rem 0 0 #1b2350}
.theme i{position:absolute;width:3px;height:3px;border-radius:50%;background:#fff;opacity:0;transform:scale(.2);transition:opacity .4s .15s,transform .4s .15s}
.theme i:nth-of-type(1){left:2.1rem;top:.5rem}.theme i:nth-of-type(2){left:2.8rem;top:1.3rem}.theme i:nth-of-type(3){left:3.4rem;top:.6rem}
:root[data-mode=dark] .theme i{opacity:.9;transform:none}
.steps{display:grid;gap:.5rem;margin:0;padding:0;counter-reset:s}
.steps li{list-style:none;display:flex;gap:.625rem;align-items:flex-start;font-size:.875rem;line-height:1.45}
.steps li::before{counter-increment:s;content:counter(s);flex:none;width:1.375rem;height:1.375rem;border-radius:.5rem;background:var(--acc);color:var(--on-acc);display:grid;place-items:center;font-size:.75rem;margin-top:.0625rem}
.notes{margin:.75rem 0 0;padding:0;display:grid;gap:.375rem}
.notes li{list-style:none;color:var(--muted);font-size:.8125rem;line-height:1.45}
.logs{display:grid;gap:.5rem}
.logs div{background:var(--card);border-radius:.875rem;padding:.5rem .75rem;font-size:.8125rem;line-height:1.4;overflow-wrap:anywhere}
.logs b{font-weight:400;color:var(--acc);margin-right:.5rem}
.logs span{color:var(--muted)}
.modal{position:absolute;inset:0;display:grid;place-items:center;padding:1.5rem}
.card{position:relative;width:100%;max-width:21rem;background:var(--card);border-radius:1.5rem;padding:1.375rem 1.25rem 1.125rem;box-shadow:var(--shadow);text-align:center;opacity:0;transform:translateY(.75rem) scale(.97);transition:transform .24s cubic-bezier(.4,0,.2,1),opacity .24s cubic-bezier(.4,0,.2,1)}
.layer.on .card{opacity:1;transform:none;animation:spring .5s cubic-bezier(.3,.6,.4,1)}
.card .gimg{width:3.5rem;height:3.5rem;border-radius:1.125rem;margin:0 auto .5rem}
.card h4{margin:0;font-weight:400;font-size:1.125rem}
.card p{margin:.375rem 0 1rem;color:var(--muted);font-size:.875rem;line-height:1.5}
.card .why{background:var(--card2);color:var(--bad);border-radius:.875rem;padding:.5rem .75rem;margin:.625rem 0 1rem;font-size:.875rem;overflow-wrap:anywhere}
.card .vers{max-height:9rem;overflow:auto;text-align:left;margin:.5rem 0 1rem;scrollbar-width:none}
.card .vers::-webkit-scrollbar{display:none}
.card .vers b{font-weight:400;color:var(--acc);font-size:.8125rem}
.card .vers p{margin:0 0 .5rem;color:var(--text)}
.card .row2{display:flex;gap:.5rem}
.card .row2 .btn{flex:1}
.card .upbar{margin:.25rem 0 1rem}

/* the one entrance of the program: springs up from a little smaller, overshoots, settles (move only, nothing fades) */
@keyframes spring{0%{transform:scale(.86)}55%{transform:scale(1.045)}80%{transform:scale(.99)}100%{transform:scale(1)}}
.cover,.body[data-key=main] .hero{animation:spring .5s cubic-bezier(.3,.6,.4,1) backwards}
@keyframes rise{from{opacity:0;transform:translateY(1.25rem) scale(.96)}to{opacity:1;transform:none}}
@keyframes pop{0%{transform:scale(.6);opacity:0}70%{transform:scale(1.08)}100%{transform:scale(1);opacity:1}}
@keyframes swap{from{transform:scale(.9)}to{transform:none}}
@keyframes turn{to{transform:rotate(360deg)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes nudge{0%,100%{transform:none}40%{transform:translateX(2.5px)}70%{transform:translateX(-.5px)}}
@keyframes blink{50%{transform:scale(.88)}}
@keyframes pulse{50%{transform:scale(.8)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
<body>
<div class="stage"><div class="win" id="win"></div></div>

<script>
// ---------------- languages: English is the source text; the others are looked up by it ----------------
const LANGS = [['en', 'English'], ['ja', '日本語'], ['ko', '한국어'], ['zh-Hans', '简体中文'], ['zh-Hant', '繁體中文']];
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
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const LABEL = { wait: 'Not updated', run: 'Syncing', ok: 'Done', skip: 'Skipped', bad: 'Failed' };

const ICONS = {{GAME_ICONS}};
const $ = (id) => document.getElementById(id);
const cmpVer = (a, b) => { const x = String(a || 0).split('.').map(Number), y = String(b || 0).split('.').map(Number); for (let i = 0; i < Math.max(x.length, y.length); i++) { const d = (x[i] || 0) - (y[i] || 0); if (d) return d; } return 0; };

// ---------------- icons (the website's line style) ----------------
const SV = (cls, inner, w = 2.2) => '<svg class="' + cls + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + w + '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + '</svg>';
const IC = {
  redo: SV('ic-redo', '<path d="M20 12a8 8 0 1 0-2.3 5.7M20 6v6h-6"/>'),
  spin: SV('ic-redo spin', '<path d="M20 12a8 8 0 1 0-2.3 5.7M20 6v6h-6"/>'),
  arr: SV('ic-arr', '<g class="mv"><path d="M5 12h14M13 6l6 6-6 6"/></g>'),
  gear: SV('', '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>', 2),
  ck: SV('', '<path d="M5 12.5l4.5 4.5L19 7.5"/>', 2.8),
  x: SV('', '<path d="M7 7l10 10M17 7L7 17"/>', 2.8),
  copy: SV('', '<rect x="9" y="9" width="11" height="11" rx="2.5"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/>'),
  out: SV('', '<path d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4"/><path d="M15 8l4 4-4 4M19 12H9"/>'),
  chev: SV('chv', '<path d="M6 9l6 6 6-6"/>'),
  globe: SV('ic-globe', '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.4 2.4 3.4 5.2 3.4 8.5s-1 6.1-3.4 8.5c-2.4-2.4-3.4-5.2-3.4-8.5s1-6.1 3.4-8.5z"/>'),
  moon: SV('ic-moon', '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>'),
  sun: SV('ic-sun', '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4"/>'),
  bolt: SV('ic-bolt', '<path d="M13 3L5 13.5h6L10 21l8-10.5h-6z"/>'),
  list: SV('ic-list', '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>'),
  help: SV('ic-help', '<circle cx="12" cy="12" r="8.5"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.6 2.3c-.8.4-1.2.9-1.2 1.8M12 16.6h.01"/>'),
  tag: SV('ic-tag', '<path d="M20 12.6L12.6 20a2 2 0 0 1-2.8 0L4 14.2V4h10.2L20 9.8a2 2 0 0 1 0 2.8z"/><path d="M8.5 8.5h.01"/>'),
  sliders: SV('', '<path d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle cx="16" cy="7" r="2"/><circle cx="8" cy="17" r="2"/>'),
  discord: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.74 19.74 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.1 14.1 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.1 13.1 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252-.192.372-.291a.074.074 0 0 1 .078-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .079.009c.12.099.246.198.373.292a.077.077 0 0 1-.006.127 12.3 12.3 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>',
  google: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.46a5.52 5.52 0 0 1-2.4 3.62v3h3.88c2.27-2.09 3.58-5.17 3.58-8.81z"/><path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.94-2.91l-3.88-3a7.2 7.2 0 0 1-10.7-3.78H1.35v3.1A12 12 0 0 0 12 24z"/><path fill="#FBBC05" d="M5.36 14.31a7.2 7.2 0 0 1 0-4.62V6.59H1.35a12 12 0 0 0 0 10.82l4.01-3.1z"/><path fill="#EA4335" d="M12 4.75c1.76 0 3.34.6 4.58 1.8l3.43-3.43A12 12 0 0 0 1.35 6.59l4.01 3.1A7.2 7.2 0 0 1 12 4.75z"/></svg>',
};
const PNAME = { discord: 'Discord', google: 'Google' };
const fl = (c) => '<span class="fl">' + (FLAGS[c] || '') + '</span>';

// ---------------- state of this page ----------------
let S = null;             // the last state the program sent
let sel = null, picked = false, swapKey = null, shownKey = null;  // the game on show; picked: the user chose one, so stop following the one that is syncing
let sheet = false, langOpen = false, fold_ = {}, modal = null, lastModal = '', copied = false, restarting = false;
let lastCheck = 0, pendingCheck = 0, promptedStartup = false, localSettingsAt = 0, errShown = '';
const badShown = {};     // game -> the failure text whose popup was already opened
let mode = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
document.documentElement.dataset.mode = mode;

function post(path, body) { return fetch(path, { method: 'POST', headers: { 'X-Wishbook': '1', 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }).catch(() => {}); }
const startUpdate = () => post('/update');
function changeSetting(patch) { localSettingsAt = Date.now(); if (S) S.settings = { ...(S.settings || {}), ...patch }; return post('/settings', patch); }
function setLang(code) { if (code === LANG) return; LANG = code; document.documentElement.lang = code; document.title = t('Wishbook | Sync'); changeSetting({ lang: code }); }
function setMode(m) { mode = m; document.documentElement.dataset.mode = m; }

function when(iso) {
  if (!iso) return '';
  const d = new Date(iso); if (isNaN(d)) return '';
  const now = new Date(), day = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const hm = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  const diff = Math.round((day(now) - day(d)) / 864e5);
  if (diff === 0) return t('Today {t}', { t: hm });
  if (diff === 1) return t('Yesterday {t}', { t: hm });
  return (d.getMonth() + 1) + '/' + String(d.getDate()).padStart(2, '0') + ' ' + hm;
}
const eff = (g) => (g.queued ? 'q' : g.status);  // the status that is shown: queued wins over the old result
const dotOf = (g) => ({ run: 'run', ok: 'ok', bad: 'bad', q: 'q' }[eff(g)] || '');
function metaOf(g) {
  const e = eff(g);
  if (e === 'run') return g.pool ? t(g.pool) + (g.page ? '・' + t('Page {n}', { n: g.page }) : '') : (g.detail || t('Getting ready…'));
  if (e === 'q') return t('Waiting for the previous game');
  if (e === 'ok' || e === 'bad' || e === 'skip') return g.detail || '';
  return g.last ? t('Last synced: {t}', { t: when(g.last) }) : t('Never synced');
}

// ---------------- pieces ----------------
const gh = (icon, title) => '<div class="gh">' + IC[icon] + '<span>' + title + '</span></div>';
const li = (icon, title, sub, right) => '<div class="li"><span class="rico">' + IC[icon] + '</span><div class="ltx"><b>' + title + '</b>' + (sub ? '<small>' + sub + '</small>' : '') + '</div>' + (right || '') + '</div>';
const lfold = (key, icon, title, inner) => '<button class="li lf ' + (fold_[key] ? 'open' : '') + '" data-act="fold" data-k="' + key + '" aria-expanded="' + !!fold_[key] + '"><span class="rico">' + IC[icon] + '</span><div class="ltx"><b>' + title + '</b></div>' + IC.chev + '</button><div class="acc ' + (fold_[key] ? 'on' : '') + '"><div class="in"><div class="pad">' + inner + '</div></div></div>';
function langItems() {
  return LANGS.map(([c, l]) => '<button class="mi ' + (c === LANG ? 'on' : '') + '" data-act="lang" data-k="' + c + '">' + fl(c) + '<span>' + l + '</span>' + (c === LANG ? IC.ck : '') + '</button>').join('');
}
const iconUrl = () => document.querySelector('link[rel=icon]').href;

function header(s) {
  const signed = !!s.member && !(s.login && s.login.needed);
  const nw = s.version && s.version.newer;
  return '<div class="hd"><img class="lg" src="' + esc(iconUrl()) + '" alt=""><div class="tt"><b>' + esc(t('Wishbook')) + '</b></div>'
    + (signed ? '<div class="who"><i>' + esc((s.member || '?').slice(0, 1).toUpperCase()) + '</i><span>' + esc(s.member) + '</span></div>' : '')
    + '<button class="ib" data-act="sheet" aria-label="' + esc(t('Settings')) + '" title="' + esc(nw ? t('New version V{v} (open for details)', { v: s.version.latest }) : t('Settings')) + '">' + IC.gear + (nw ? '<span class="nw">NEW</span>' : '') + '</button></div>';
}

function loginBody(s) {
  const lg = s.login || {};
  if (lg.waiting) {
    return '<div class="cover" data-key="code"><h2>' + esc(t('Waiting for login')) + '</h2><p>' + esc(t('Finish logging in on the tab that just opened, then enter the code shown in this window.')) + '</p>'
      + '<div class="code">' + esc(lg.code || '····') + '</div>'
      + '<button class="btn sm ghost copy" data-act="copy" ' + (lg.code ? '' : 'disabled') + '>' + (copied ? IC.ck + esc(t('Copied')) : IC.copy + esc(t('Copy code'))) + '</button>'
      + '<div class="warn">' + esc(t('The sign-in page will ask for this code. Do not enter it if you did not just open this program yourself.')) + '</div></div>';
  }
  const provs = (lg.providers || []).map((p) => '<button class="prov ' + esc(p) + '" data-act="login" data-k="' + esc(p) + '">' + (IC[p] || '') + esc(t('Sign in with {p}', { p: PNAME[p] || p })) + '</button>').join('');
  return '<div class="cover" data-key="login"><img class="big" src="' + esc(iconUrl()) + '" alt=""><h2>' + esc(t('Sign in to Wishbook')) + '</h2>'
    + '<p>' + esc(t('Sign in to sync your pull records to your account.')) + '</p>'
    + (provs || '<p>' + esc(t('Sign-in is not open yet.')) + '</p>')
    + (lg.error ? '<div class="lerr">' + esc(lg.error) + '</div>' : '') + '</div>';
}

function mainBody(s) {
  const games = s.games, g = games.find((x) => x.key === sel) || games[0];
  const idle = s.phase === 'idle', canAsk = ['idle', 'running', 'updating'].includes(s.phase);
  const dock = games.map((x, i) => { const d = dotOf(x); return '<button class="gi ' + (x.key === g.key ? 'on' : '') + '" data-act="pick" data-k="' + x.key + '" style="animation-delay:' + (i * 60) + 'ms" title="' + esc(t(x.name)) + '"><img src="' + esc(ICONS[x.key] || '') + '" alt="">' + (d ? '<i class="bd ' + d + '"></i>' : '') + '</button>'; }).join('');
  const e = eff(g);
  const pools = (g.pools || []).map((p) => {
    const st = p.status;
    let c;
    if (st === 'ok') c = t('{n} records', { n: p.n });
    else if (st === 'run') c = g.page ? t('Page {n}', { n: g.page }) : t('Syncing');
    else if (st === 'bad') c = t('Failed');
    else c = (e === 'run' || e === 'bad') ? t('Not started') : t('Not updated');
    const mark = st === 'ok' ? IC.ck : st === 'bad' ? IC.x : st === 'run' ? IC.redo : '';
    return '<div class="pl ' + st + '"><span class="d">' + mark + '</span><span class="n" title="' + esc(t(p.label)) + '">' + esc(t(p.label)) + '</span><span class="c">' + esc(c) + '</span></div>';
  }).join('');
  const chip = e === 'wait' ? '' : (e === 'bad' ? '<button class="chip bad" data-act="fail" data-k="' + g.key + '">' + IC.x + esc(t('Failed')) + '</button>'
    : '<span class="chip ' + e + '">' + (e === 'ok' ? IC.ck : '') + esc(e === 'q' ? t('Queued') : t(LABEL[e] || LABEL.wait)) + '</span>');
  const run = e === 'run' || e === 'q';
  const label = e === 'run' ? t('Syncing') : e === 'q' ? t('Queued') : (g.status === 'wait' ? t('Update') : t('Update again'));
  const hero = '<div class="body" data-key="main"><div class="hero"><div class="top"><img class="gimg ' + (swapKey === g.key ? 'pop' : '') + '" src="' + esc(ICONS[g.key] || '') + '" alt=""><div class="tx"><div class="nm">' + esc(t(g.name)) + '</div><div class="meta">' + esc(metaOf(g)) + '</div></div>' + chip + '</div>'
    + '<div class="pools' + ((g.pools || []).length > 4 ? ' many' : '') + '">' + pools + '</div>'
    + '<button class="btn" data-act="sync" data-k="' + g.key + '" ' + (run || !idle ? 'disabled' : '') + ' ' + (canAsk ? '' : 'hidden') + '>' + IC.redo + esc(label) + '</button></div></div>';
  const ft = '<div class="ft" data-key="ft"><button class="btn alt" data-act="all" ' + (idle ? '' : 'disabled') + '>' + IC.redo + esc(t('Update all')) + '</button><a class="btn" href="' + esc(s.site || '#') + '" target="_blank" rel="noopener">' + esc(t('Open stats site')) + IC.arr + '</a></div>';
  return '<div class="dock" data-key="dock">' + dock + '</div>' + hero + ft;
}

function settings(s) {
  const v = s.version || {}, st = s.settings || {};
  const signed = !!s.member && !(s.login && s.login.needed);
  const cur = LANGS.find((l) => l[0] === LANG) || LANGS[0];
  const langBtn = '<div class="dd"><button class="selb ' + (langOpen ? 'open' : '') + '" data-act="langopen" aria-expanded="' + langOpen + '">' + fl(cur[0]) + '<span>' + cur[1] + '</span>' + IC.chev + '</button><div class="menu ' + (langOpen ? 'on' : '') + '"><div class="in">' + langItems() + '</div></div></div>';
  const busy = s.phase === 'updating', pct = (/(\d+)%/.exec(s.notice || '') || [])[1];
  let ver;
  if (v.newer) {
    const newest = (v.history || []).find((h) => h.version === v.latest);
    const sub = [v.size ? (v.size / 1048576).toFixed(1) + ' MB' : '', newest && newest.date].filter(Boolean).join('・') || t('A new version is available');
    const right = v.canUpdate ? '<button class="btn sm" data-act="update" ' + (s.phase !== 'idle' ? 'disabled' : '') + '>' + IC.redo + esc(busy ? (pct ? t('Downloading {p}%', { p: pct }) : t('Updating')) : t('Update now')) + '</button>' : '';
    ver = li('tag', esc(t('New version V{v} found', { v: v.latest })), esc(sub), right)
      + (busy ? '<div class="bar upbar"><i style="width:' + (pct || 3) + '%"></i></div>' : '')
      + (v.error ? '<div class="ltx" style="padding:0 .875rem .75rem"><small class="err">' + esc(v.error) + '</small></div>' : '');
  } else {
    const checking = v.checking || !!pendingCheck;
    ver = li('tag', esc(t('Up to date')), esc(t('Current V{v}', { v: v.current || '' })), '<button class="btn sm" data-act="check" ' + (checking ? 'disabled' : '') + '>' + (checking ? IC.spin : IC.redo) + esc(t('Check')) + '</button>');
  }
  const hist = (v.history || []).length
    ? '<div class="logs">' + v.history.map((h) => '<div><b>V' + esc(h.version) + '</b><span>' + esc(h.date) + '</span>' + (h.note ? '<br>' + esc(h.note) : '') + '</div>').join('') + '</div>'
    : '<div class="logs"><div><span>' + esc(t('No changelog available (it cannot be loaded while offline).')) + '</span></div></div>';
  const steps = ['Open the in-game pull history once, so the program can find the latest history link.',
    'Come back here and press "Update" next to a game, or "Update all". Nothing runs automatically.',
    'The first time, choose how to sign in, sign in on the page that opens, then enter the code shown in this window. You will stay signed in afterwards.',
    'When it is done, open the stats site to see the result. Closing this tab ends the program.'];
  const head = signed
    ? '<span class="av">' + esc((s.member || '?').slice(0, 1).toUpperCase()) + '</span><div class="ltx"><b>' + esc(s.member) + '</b><small>' + esc(t('Signed in')) + '</small></div><button class="btn sm ghost" data-act="logout" ' + (s.phase === 'idle' ? '' : 'disabled') + '>' + IC.out + esc(t('Sign out')) + '</button>'
    : '<div class="ltx"><b>' + esc(t('Settings')) + '</b></div>';
  return '<div class="sheet"><div class="shd">' + head + '<button class="ib close" data-act="sheet" aria-label="' + esc(t('Close')) + '">' + IC.x + '</button></div><div class="scroll">'
    + '<section>' + gh('sliders', esc(t('General'))) + '<div class="gc">'
    + li('globe', esc(t('Display language')), '', langBtn)
    + li(mode === 'dark' ? 'moon' : 'sun', esc(t('Appearance')), esc(mode === 'dark' ? t('Dark') : t('Light')), '<button class="theme" data-act="theme" aria-label="' + esc(t('Switch appearance')) + '"><span class="orb"></span><i></i><i></i><i></i></button>')
    + '</div></section>'
    + '<section>' + gh('redo', esc(t('Updates'))) + '<div class="gc">'
    + ver
    + li('bolt', esc(t('Allow automatic updates')), esc(t('When a new version is found, download and install it automatically, then restart.')), '<button class="sw" role="switch" data-act="auto" aria-checked="' + !!st.autoUpdate + '"><i></i></button>')
    + lfold('log', 'list', esc(t('Changelog')), hist)
    + '</div></section>'
    + '<section>' + gh('help', esc(t('Help'))) + '<div class="gc">'
    + lfold('how', 'help', esc(t('How to use')), '<ol class="steps">' + steps.map((x) => '<li>' + esc(t(x)) + '</li>').join('') + '</ol><ul class="notes"><li>' + esc(t('If it says the history was never opened or the link has expired, open the in-game pull history again and then press Update.')) + '</li><li>' + esc(t('Your login is stored on this PC in %APPDATA%\\wishbook. Do not share it.')) + '</li></ul>')
    + '</div></section></div></div>';
}

function modalHtml(s) {
  if (!modal) return lastModal;  // keeps the content while the popup plays its way out
  let h = '';
  const ok = '<button class="btn" data-act="close">' + esc(t('OK')) + '</button>';
  if (modal.type === 'fail') {
    const g = s.games.find((x) => x.key === modal.key) || s.games[0];
    h = '<div class="card"><img class="gimg" src="' + esc(ICONS[g.key] || '') + '" alt=""><h4>' + esc(t('{name} failed to sync', { name: t(g.name) })) + '</h4><div class="why">' + esc(g.detail) + '</div><div class="row2">' + ok + '</div></div>';
  } else if (modal.type === 'err') {
    h = '<div class="card"><h4>' + esc(t('Cannot sync')) + '</h4><div class="why">' + esc(modal.text) + '</div><div class="row2">' + ok + '</div></div>';
  } else if (modal.type === 'msg') {
    h = '<div class="card"><h4>' + esc(modal.title) + '</h4><p>' + esc(modal.text) + '</p><div class="row2">' + ok + '</div></div>';
  } else if (modal.type === 'update') {
    const v = s.version || {}, busy = s.phase === 'updating', pct = (/(\d+)%/.exec(s.notice || '') || [])[1];
    const fresh = (v.history || []).filter((x) => cmpVer(x.version, v.current) > 0 && x.note);
    const notes = fresh.length ? fresh.map((x) => '<b>V' + esc(x.version) + (x.date ? '  ' + esc(x.date) : '') + '</b><p>' + esc(x.note) + '</p>').join('') : '<p>' + esc(v.note || t('A new version is available')) + '</p>';
    h = '<div class="card"><h4>' + esc(t('V{v} Wishbook Version Update', { v: v.latest })) + '</h4><div class="vers">' + notes + '</div>'
      + (busy ? '<div class="bar upbar"><i style="width:' + (pct || 3) + '%"></i></div>' : '')
      + '<div class="row2"><button class="btn ghost" data-act="close" ' + (busy ? 'disabled' : '') + '>' + esc(t('Later')) + '</button><button class="btn" data-act="update" ' + (busy ? 'disabled' : '') + '>' + esc(busy ? (pct ? t('Downloading {p}%', { p: pct }) : t('Updating')) : t('Update now')) + '</button></div></div>';
  }
  return (lastModal = '<div class="modal">' + h + '</div>');
}

// ---------------- drawing: only what changed is touched ----------------
function morph(dst, src) {
  const a = [...dst.childNodes], b = [...src.childNodes];
  b.forEach((n, i) => {
    const o = a[i];
    if (!o) { dst.append(n.cloneNode(true)); return; }
    if (o.nodeType !== n.nodeType || o.nodeName !== n.nodeName || (n.nodeType === 1 && o.getAttribute('data-key') !== n.getAttribute('data-key'))) { dst.replaceChild(n.cloneNode(true), o); return; }
    if (n.nodeType === 3) { if (o.nodeValue !== n.nodeValue) o.nodeValue = n.nodeValue; return; }
    if (n.nodeType !== 1) return;
    for (const at of [...o.attributes]) if (!n.hasAttribute(at.name)) o.removeAttribute(at.name);
    for (const at of [...n.attributes]) if (o.getAttribute(at.name) !== at.value) o.setAttribute(at.name, at.value);
    morph(o, n);
  });
  for (let i = a.length - 1; i >= b.length; i--) dst.removeChild(a[i]);
}
function fadeEdges() {
  const b = document.querySelector('.sheet .scroll'); if (!b) return;
  b.classList.toggle('fade-t', b.scrollTop > 2);
  b.classList.toggle('fade-b', b.scrollTop + b.clientHeight < b.scrollHeight - 2);
}
document.addEventListener('scroll', fadeEdges, true);

function verdictDialog(v) {
  if (!v.latest) modal = { type: 'msg', title: t('Notice'), text: t('Cannot reach the site. Please try again later.') };
  else if (!v.newer) modal = { type: 'msg', title: t('Notice'), text: t('You are on the latest version. No update needed.') };
  else if (!v.canUpdate) modal = { type: 'msg', title: t('New version found'), text: t('New version V{v} found.', { v: v.latest }) };
  else modal = { type: 'update' };
}

function render() {
  const s = S; if (!s) return;
  // things that open by themselves
  const v = s.version || {};
  if (pendingCheck && !v.checking && Date.now() - pendingCheck > 900) { pendingCheck = 0; verdictDialog(v); }
  if (!promptedStartup && v.newer && v.canUpdate && s.phase === 'idle' && s.settings && !s.settings.autoUpdate) { promptedStartup = true; modal = { type: 'update' }; }
  if (s.phase === 'updating' && !(modal && modal.type === 'update')) { modal = { type: 'update' }; sheet = false; }
  if (s.phase === 'error' && s.notice && errShown !== s.notice) { errShown = s.notice; modal = { type: 'err', text: s.notice }; }
  for (const g of s.games) {
    if (g.status === 'bad' && g.detail && badShown[g.key] !== g.detail) {
      badShown[g.key] = g.detail;
      if (!modal) { modal = { type: 'fail', key: g.key }; if (!picked) sel = g.key; }
    }
    if (g.status !== 'bad') delete badShown[g.key];
  }
  // which game is on show: follow the one that is syncing until the user picks
  if (!sel && s.games.length) sel = s.games[0].key;
  if (!picked) { const f = s.games.find((g) => g.status === 'run' && !g.queued); if (f) sel = f.key; }
  if (shownKey !== sel) { shownKey = sel; swapKey = sel; }

  const lg = s.login || {};
  const html = header(s) + (lg.needed ? loginBody(s) : mainBody(s))
    + '<div class="layer ' + (sheet ? 'on' : '') + '" data-key="lsheet"><div class="scrim" data-act="sheet"></div>' + settings(s) + '</div>'
    + '<div class="layer ' + (modal ? 'on' : '') + '" data-key="lmodal"><div class="scrim" data-act="close"></div>' + modalHtml(s) + '</div>';
  const tmp = document.createElement('div'); tmp.innerHTML = html;
  morph($('win'), tmp);
  fadeEdges();
  swapKey = null;
}

// ---------------- events ----------------
function autoCheck() {  // opening the settings asks the site (at most every 20s; straight away when there is no verdict yet)
  const v = S && S.version;
  if (Date.now() - lastCheck < 20000 && v && v.latest) return;
  lastCheck = Date.now(); post('/check');
}
document.addEventListener('click', (e) => {
  if (langOpen && !e.target.closest('.dd')) langOpen = false;
  const a = e.target.closest('[data-act]');
  if (!a || a.disabled) { render(); return; }
  const act = a.dataset.act, k = a.dataset.k;
  if (act === 'sheet') { sheet = !sheet; langOpen = false; if (sheet) autoCheck(); }
  else if (act === 'close') modal = null;
  else if (act === 'fail') modal = { type: 'fail', key: k };
  else if (act === 'pick') { picked = true; sel = k; }
  else if (act === 'sync') { picked = true; sel = k; post('/sync', { games: [k] }); }
  else if (act === 'all') post('/sync', { games: S.games.map((g) => g.key) });
  else if (act === 'login') post('/login', { provider: k });
  else if (act === 'copy') { const c = S.login && S.login.code; if (c) { try { navigator.clipboard.writeText(c); } catch (err) { /* the code can still be selected by hand */ } copied = true; setTimeout(() => { copied = false; render(); }, 1600); } }
  else if (act === 'lang') { setLang(k); langOpen = false; }
  else if (act === 'langopen') langOpen = !langOpen;
  else if (act === 'fold') fold_[k] = !fold_[k];
  else if (act === 'theme') { const m = mode === 'dark' ? 'light' : 'dark'; setMode(m); changeSetting({ theme: m }); }
  else if (act === 'auto') changeSetting({ autoUpdate: !(S.settings && S.settings.autoUpdate) });
  else if (act === 'check') { pendingCheck = Date.now(); lastCheck = pendingCheck; post('/check'); }
  else if (act === 'update') startUpdate();
  else if (act === 'logout') { sheet = false; post('/logout'); }
  render();
});
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (langOpen) langOpen = false; else if (modal) modal = null; else if (sheet) sheet = false; else return;
  render();
});

function applyState(st) {
  if (!st || Date.now() - localSettingsAt < 1500) return;
  if (st.lang !== LANG && LANGS.some((l) => l[0] === st.lang)) { LANG = st.lang; document.documentElement.lang = LANG; document.title = t('Wishbook | Sync'); }
  if (st.theme === 'light' || st.theme === 'dark') setMode(st.theme);
}
async function tick() {
  try {
    const r = await fetch('/state', { cache: 'no-store' });
    S = await r.json();
    if (restarting && !S.restarting) { location.reload(); return; }
    restarting = !!S.restarting;
    applyState(S.settings);
    render();
    if (S.phase === 'done' || S.phase === 'error') return;
  } catch (e) {
    if (restarting) { setTimeout(tick, 800); return; }  // the new process is taking over this port
    return;  // the local server is gone: keep what is on screen
  }
  setTimeout(tick, 700);
}
document.title = t('Wishbook | Sync');
tick();
</script>
"""
