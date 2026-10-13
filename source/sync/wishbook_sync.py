"""Read each game's gacha history URL from local logs/caches, fetch the records from the official API, and upload to the Cloudflare Worker.

Shows progress on a local web page (127.0.0.1) that opens in the browser; no console window is needed.
Usage: python wishbook_sync.py [--game genshin hsr zzz wuwa] [--url <history url>] [--dry-run] [--login] [--no-ui]
Stdlib only. Open the in-game gacha history page once before running so the game writes a fresh URL.
"""
import argparse
import hashlib
import http.server
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

from game_icons import GAME_ICONS
from icon_data import ICON
from locale_data import PROGRAM as PROGRAM_TEXT
from ui_page import PAGE as PAGE_TEMPLATE

PAGE = (PAGE_TEMPLATE.replace('{{ICON}}', ICON).replace('{{GAME_ICONS}}', json.dumps(GAME_ICONS))
        .replace('{{I18N}}', json.dumps(PROGRAM_TEXT, ensure_ascii=False).replace('</', '<\\/')))

VERSION = '0.3.4'  # bumped by tools/release.py, which also writes site/version.json
FROZEN = bool(getattr(sys, 'frozen', False))
EXE = sys.executable if FROZEN else None
HERE = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
LEGACY_CONFIG = os.path.join(HERE, 'config.json')  # older versions kept it next to the exe
# the login lives in the user's profile so the exe can be the only file in its folder (WISHBOOK_CONFIG overrides it, for tests)
CONFIG = os.environ.get('WISHBOOK_CONFIG') or os.path.join(os.environ.get('APPDATA') or HERE, 'wishbook', 'config.json')
DEFAULT_SERVER = 'https://wishbook.xmoiswnx.workers.dev'
UA = 'Mozilla/5.0 wishbook-sync'
HOME = os.path.expanduser('~')
LOCALLOW = os.path.join(HOME, 'AppData', 'LocalLow')

LANGS = ('en', 'zh-Hant', 'zh-Hans', 'ja', 'ko')
LEGACY_LANGS = {'zh': 'zh-Hant', 'zhs': 'zh-Hans'}  # codes saved by earlier versions
LANG = 'en'  # the messages this program writes itself (the page translates its own texts); English is the source language of every text


def system_lang():
    """The language of the Windows display (en when it is none of ours)."""
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except Exception:
        return 'en'
    primary = lid & 0x3FF
    if primary == 0x04:  # Chinese: Taiwan, Hong Kong and Macao use traditional characters
        return 'zh-Hant' if lid in (0x0404, 0x0C04, 0x1404) else 'zh-Hans'
    return {0x11: 'ja', 0x12: 'ko'}.get(primary, 'en')
MSG = PROGRAM_TEXT  # {lang: {zh source text: translation}}; the texts live in locales/program/*.json and are baked into locale_data.py by tools/build_locales.py

def tr(zh, **kw):
    """The message in the chosen language (zh is the source text and also the fallback)."""
    text = MSG.get(LANG, {}).get(zh, zh)
    return text.format(**kw) if kw else text


GAME_NAMES = {'genshin': 'Genshin Impact', 'hsr': 'Honkai: Star Rail', 'zzz': 'Zenless Zone Zero', 'wuwa': 'Wuthering Waves'}

# HoYo games: (pool key, gacha_type sent to the API)
HOYO = {
    'genshin': {
        'api': 'https://public-operation-hk4e-sg.hoyoverse.com/gacha_info/api/getGachaLog',
        'data_dir': 'GenshinImpact_Data',
        'player_log': os.path.join(LOCALLOW, 'miHoYo', 'Genshin Impact', 'output_log.txt'),
        'pools': [('char', '301'), ('weapon', '302'), ('standard', '200'), ('novice', '100')],
        'rarity': lambda r: int(r),
    },
    'hsr': {
        'api': 'https://public-operation-hkrpg-sg.hoyoverse.com/common/gacha_record/api/getGachaLog',
        'data_dir': 'StarRail_Data',
        'player_log': os.path.join(LOCALLOW, 'Cognosphere', 'Star Rail', 'Player.log'),
        'pools': [('char', '11'), ('lc', '12'), ('standard', '1'), ('novice', '2')],
        'rarity': lambda r: int(r),
    },
    'zzz': {
        'api': 'https://public-operation-nap-sg.hoyoverse.com/common/gacha_record/api/getGachaLog',
        'data_dir': 'ZenlessZoneZero_Data',
        'player_log': os.path.join(LOCALLOW, 'miHoYo', 'ZenlessZoneZero', 'Player.log'),
        'pools': [('char', '2001'), ('engine', '3001'), ('standard', '1001'), ('bangboo', '5001')],
        'rarity': lambda r: int(r) + 1,  # rank_type 4/3/2 = S/A/B
    },
}
WUWA_POOLS = {1: 'char', 2: 'weapon', 3: 'std_char', 4: 'std_weapon', 5: 'novice', 6: 'novice_pick', 7: 'thanks'}
WUWA_API = 'https://gmserver-api.aki-game2.net/gacha/record/query'

POOL_LABELS = {
    'genshin': {'char': 'Character Event Wish', 'weapon': 'Weapon Event Wish', 'standard': 'Standard Wish', 'novice': 'Beginners\' Wish'},
    'hsr': {'char': 'Character Event Warp', 'lc': 'Light Cone Event Warp', 'standard': 'Stellar Warp', 'novice': 'Departure Warp'},
    'zzz': {'char': 'Exclusive Channel', 'engine': 'W-Engine Channel', 'standard': 'Stable Channel', 'bangboo': 'Bangboo Channel'},
    'wuwa': {'char': 'Character Event Convene', 'weapon': 'Weapon Event Convene', 'std_char': 'Standard Character Convene', 'std_weapon': 'Standard Weapon Convene',
             'novice': 'Beginner\'s Convene', 'novice_pick': 'Beginner\'s Choice Convene', 'thanks': 'Gratitude Convene'},
}


class Failure(Exception):
    """An expected problem whose message is shown to the user as-is."""


# ---------- progress state, shared with the local web page ----------

class Reporter:
    def __init__(self, games):
        self.lock = threading.Lock()
        self.state = {
            'phase': 'running', 'member': '', 'notice': '', 'site': '', 'restarting': False,
            'login': {'needed': False, 'waiting': False, 'providers': [], 'error': '', 'code': ''},
            'settings': {'lang': LANG, 'autoUpdate': False, 'theme': ''},
            'version': {'current': VERSION, 'latest': None, 'newer': False, 'note': '', 'url': '', 'sha256': '', 'checking': False, 'canUpdate': FROZEN, 'error': '', 'history': [], 'size': 0},
            'games': [{'key': g, 'name': GAME_NAMES[g], 'status': 'wait', 'detail': '', 'progress': None, 'queued': False, 'pool': '', 'page': 0, 'added': None, 'last': '',
                       'pools': [{'label': label, 'status': 'wait', 'n': 0} for label in POOL_LABELS[g].values()]} for g in games],
        }
        self.last_poll = 0.0
        self.polled = False
        self.jobs = queue.Queue()
        self.pending = set()  # games asked for and not finished yet
        self.server = None  # the local page server, set by main()
        self.cfg = {}  # the saved settings (language, auto update); filled in by run()

    def update_settings(self, patch):
        """Called from the page: change the language / auto-update switch and keep it in config.json."""
        global LANG
        with self.lock:
            if patch.get('lang') in LANGS:
                LANG = self.cfg['lang'] = patch['lang']
            if isinstance(patch.get('autoUpdate'), bool):
                self.cfg['autoUpdate'] = patch['autoUpdate']
            if patch.get('theme') in ('light', 'dark'):
                self.cfg['theme'] = patch['theme']
            self.state['settings'] = {'lang': LANG, 'autoUpdate': bool(self.cfg.get('autoUpdate')), 'theme': self.cfg.get('theme', '')}
        try:
            save_config(self.cfg)
        except OSError:
            pass

    def request(self, games, force=False):
        """Called from the page: queue the games that are not already waiting or running."""
        with self.lock:
            if self.state['login']['needed']:  # nothing is synced before signing in
                return
            for g in games:
                if g == '__update__' and force:  # not a game: the self-update job
                    if g not in self.pending and self.state['phase'] == 'idle':
                        self.pending.add(g)
                        self.jobs.put(g)
                    continue
                if g in self.pending or not any(x['key'] == g for x in self.state['games']):
                    continue
                self.pending.add(g)
                self.jobs.put(g)
                for x in self.state['games']:
                    if x['key'] == g:
                        x['status'], x['detail'], x['progress'], x['queued'] = 'wait', '', None, True

    def need_login(self, cfg):
        """Show the sign-in card (first start, or the saved session no longer works)."""
        providers = fetch_login_options(cfg)
        with self.lock:
            self.state['login'].update(needed=True, waiting=False, providers=providers, error='', code='')
            self.state['member'] = ''
        self.phase('idle')

    def logged_in(self, name):
        with self.lock:
            self.state['login'].update(needed=False, waiting=False, error='', code='')
            self.state['member'] = name or ''
        self.phase('idle')

    def logout(self):
        """Called from the page: forget the saved sign-in and show the sign-in card again (not while a sync is running)."""
        with self.lock:
            if self.pending or self.state['login']['needed'] or self.state['phase'] in ('login', 'updating'):
                return
            self.cfg.pop('token', None)
            self.cfg.pop('name', None)
        try:
            save_config(self.cfg)
        except OSError:
            pass
        try:
            self.need_login(self.cfg)
        except (urllib.error.URLError, OSError) as e:
            with self.lock:
                self.state['login'].update(needed=True, waiting=False, providers=[], error=tr('Connection failed: {e}', e=e), code='')
                self.state['member'] = ''
            self.phase('idle')

    def request_login(self, provider):
        """Called from the page: start the browser sign-in with the chosen provider."""
        with self.lock:
            lg = self.state['login']
            if not lg['needed'] or lg['waiting'] or provider not in lg['providers']:
                return
            lg.update(waiting=True, error='')
            self.state['phase'], self.state['notice'] = 'login', tr('Finish logging in on the tab that just opened, then enter the code shown in this window.')  # no blank moment before the sign-in really starts
            self.login_args = provider
        self.jobs.put('__login__')

    def finished(self, game):
        with self.lock:
            self.pending.discard(game)

    def snapshot(self):
        with self.lock:
            self.last_poll = time.time()
            self.polled = True
            return json.dumps(self.state, ensure_ascii=False)

    def phase(self, phase, notice=''):
        with self.lock:
            self.state['phase'] = phase
            self.state['notice'] = notice

    def member(self, name):
        with self.lock:
            self.state['member'] = name or ''

    def game(self, key, status=None, detail=None, progress='keep', **extra):
        """extra: pool (label being read), page, pools (per pool: label, status, n), added, last; they are copied into the game as they are."""
        with self.lock:
            for g in self.state['games']:
                if g['key'] == key:
                    g['queued'] = False
                    if status is not None:
                        g['status'] = status
                    if detail is not None:
                        g['detail'] = detail
                    if progress != 'keep':
                        g['progress'] = progress
                    g.update(extra)
        print(f"[{GAME_NAMES[key]}] {status or ''} {detail or ''}", flush=True)


def serve_ui(reporter, port):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split('?')[0] == '/state':
                body, ctype = reporter.snapshot().encode(), 'application/json; charset=utf-8'
            else:
                body, ctype = PAGE.encode(), 'text/html; charset=utf-8'
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            path = self.path.split('?')[0]
            if path not in ('/sync', '/check', '/update', '/settings', '/login', '/logout') or self.headers.get('X-Wishbook') != '1':
                self.send_response(403)
                self.end_headers()
                return
            if path == '/settings':
                try:
                    patch = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
                except ValueError:
                    patch = {}
                reporter.update_settings(patch if isinstance(patch, dict) else {})
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'ok')
                return
            if path == '/login':
                try:
                    body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
                except ValueError:
                    body = {}
                if isinstance(body, dict):
                    reporter.request_login(str(body.get('provider') or ''))
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'ok')
                return
            if path == '/logout':
                threading.Thread(target=reporter.logout, daemon=True).start()  # asks the site for the provider list, so not on the request thread
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'ok')
                return
            if path == '/update':
                reporter.request(['__update__'], force=True)
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'ok')
                return
            if path == '/check':
                getattr(reporter, 'check', lambda: None)()
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'ok')
                return
            try:
                games = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}').get('games') or []
            except ValueError:
                games = []
            reporter.request([g for g in games if g in GAME_NAMES])
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')

        def log_message(self, *args):
            pass

    server = None
    for _ in range(60 if port else 1):
        try:
            server = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
            break
        except OSError:
            time.sleep(0.5)
    if server is None:
        raise OSError(tr('The local page port is in use'))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def http_json(url, data=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Content-Type': 'application/json'})
    if data is not None:
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


# ---------- locating the history URL ----------

def drives():
    return [f'{c}:\\' for c in 'CDEFGHIJ' if os.path.isdir(f'{c}:\\')]


SKIP_DIRS = {'windows', '$recycle.bin', 'system volume information', 'node_modules', '.git', 'appdata', 'programdata', '$windows.~bt', 'recovery'}


def find_dirs(name, max_depth=5):
    """Directories called `name` under the drive roots (bounded walk so it stays fast)."""
    found = []
    name = name.lower()
    for root in drives():
        base = root.rstrip('\\').count('\\')
        for cur, dirs, _ in os.walk(root):
            depth = cur.count('\\') - base
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS] if depth < max_depth else []
            for d in list(dirs):
                if d.lower() == name:
                    found.append(os.path.join(cur, d))
    return found


def read_tail(path, limit=64 * 1024 * 1024):
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        if size > limit:
            f.seek(size - limit)
        return f.read()


def hoyo_game_dirs(game, cfg):
    spec = HOYO[game]
    dirs = []
    if cfg.get('paths', {}).get(game):
        dirs.append(cfg['paths'][game])
    log = spec['player_log']
    for path in (log, os.path.join(os.path.dirname(log), 'Player-prev.log')):
        try:  # the game logs its own install path near the top of the file; a long log would have lost it in the tail
            with open(path, 'rb') as f:
                text = f.read(512 * 1024).decode('utf-8', 'ignore')
            if os.path.getsize(path) > 512 * 1024:
                text += read_tail(path, 4 * 1024 * 1024).decode('utf-8', 'ignore')
        except OSError:
            continue
        for m in re.finditer(r'([A-Za-z]:[^\r\n"]*?' + spec['data_dir'] + ')', text):
            dirs.append(m.group(1).replace('/', '\\'))
    if not any(os.path.isdir(d) for d in dirs):
        dirs += find_dirs(spec['data_dir'])
    seen, out = set(), []
    for d in dirs:
        if d.lower() not in seen and os.path.isdir(d):
            seen.add(d.lower())
            out.append(d)
    return out


def read_locked(path):
    """Reads a file the running game keeps locked: a plain open is refused, but the OS copy routine is allowed (same trick as the PowerShell script)."""
    try:
        with open(path, 'rb') as f:
            return f.read()
    except PermissionError:
        import ctypes
        tmp = os.path.join(os.environ.get('TEMP', HERE), 'wishbook_cache_copy.tmp')
        if not ctypes.windll.kernel32.CopyFileW(path, tmp, False):
            raise
        try:
            with open(tmp, 'rb') as f:
                return f.read()
        finally:
            os.remove(tmp)


def hoyo_base(url):
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    base = {k: q[k][0] for k in ('authkey_ver', 'sign_type', 'auth_appid', 'lang', 'region', 'game_biz', 'authkey', 'win_mode') if k in q}
    base.setdefault('authkey_ver', '1')
    base.setdefault('sign_type', '2')
    base.setdefault('auth_appid', 'webview_gacha')
    base['lang'] = 'zh-tw'
    return base


def hoyo_params(game, base, gtype, end_id='0', size='20'):
    params = dict(base, gacha_type=gtype, page='1', size=size, end_id=end_id)
    if game == 'zzz':
        params['real_gacha_type'] = str(int(gtype) // 1000)  # 2001 -> 2: the API wants the base type here, with the full one in gacha_type
    return params


def hoyo_url_alive(game, url):
    """True / False when the official API accepts / rejects the key, None when it could not be asked (offline)."""
    spec = HOYO[game]
    try:
        d = http_json(spec['api'] + '?' + urllib.parse.urlencode(hoyo_params(game, hoyo_base(url), spec['pools'][0][1], size='5')))
    except Exception:
        return None
    return d.get('retcode') == 0


def hoyo_url(game, cfg):
    """(newest history URL in the game's web cache that the API still accepts, whether the game seems installed).
    The cache keeps old keys too, so candidates are tried newest first; when none is accepted the newest is returned and the fetch reports it as expired."""
    cands = []  # (file mtime, position in file, url)
    dirs = hoyo_game_dirs(game, cfg)
    for data_dir in dirs:
        web_root = os.path.join(data_dir, 'webCaches')
        files = [os.path.join(web_root, 'Cache', 'Cache_Data', 'data_2')]  # older clients keep a single unversioned cache
        for web in sorted(os.listdir(web_root)) if os.path.isdir(web_root) else []:
            files += [os.path.join(web_root, web, sub, 'data_2') for sub in ('Cache\\Cache_Data', 'Cache')]
        for f in files:
            if not os.path.isfile(f):
                continue
            data = read_locked(f)
            for m in re.finditer(rb'https://[\x21-\x7e]*authkey=[\x21-\x7e]*', data):
                cands.append((os.path.getmtime(f), m.start(), m.group().decode()))
    seen, ordered = set(), []
    for _, _, url in sorted(cands, reverse=True):
        key = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get('authkey', [url])[0]
        if key not in seen:
            seen.add(key)
            ordered.append(url)
    for url in ordered[:8]:
        if hoyo_url_alive(game, url) is not False:  # accepted, or the check itself failed (then trust the newest)
            return url, True
        time.sleep(0.5)
    return (ordered[0] if ordered else None), bool(dirs)


# the game obfuscates Client.log: every byte is XORed with 0xA5 (odd low nibble) or 0xEF (even), so decode it before searching
CLIENT_LOG_TABLE = bytes(x ^ (0xA5 if (x & 0x0F) % 2 == 1 else 0xEF) for x in range(256))
WUWA_URL = re.compile(rb'https://aki-gm-resources[^\s"]*?/aki/gacha/index\.html#/record\?[^"\s]*')


def wuwa_url(cfg):
    """(newest convene-history URL found in the game's logs or None, whether the game seems installed)."""
    dirs = [cfg.get('paths', {}).get('wuwa')] if cfg.get('paths', {}).get('wuwa') else []
    dirs += find_dirs('Wuthering Waves', 5)
    files = []
    for d in dirs:
        logs = os.path.join(d, 'Client', 'Saved', 'Logs')
        if os.path.isdir(logs):
            files += [os.path.join(logs, x) for x in os.listdir(logs) if x.lower().endswith('.log')]
        web = os.path.join(d, 'Client', 'Binaries', 'Win64', 'ThirdParty', 'KrPcSdk_Global', 'KRSDKRes', 'KRSDKWebView')
        files += [os.path.join(web, x) for x in ('debug.log', os.path.join('log', 'debug.log'))]
    files = sorted((f for f in files if os.path.isfile(f)), key=os.path.getmtime, reverse=True)
    for f in files:  # newest file first; the first file with a URL wins
        data = read_tail(f)
        urls = WUWA_URL.findall(data.translate(CLIENT_LOG_TABLE)) or WUWA_URL.findall(data)
        if urls:
            return urls[-1].decode(), True
    return None, bool(dirs)


# ---------- fetching ----------

def pool_states(game):
    return [{'label': label, 'status': 'wait', 'n': 0} for label in POOL_LABELS[game].values()]


def fetch_hoyo(game, url, step):
    spec = HOYO[game]
    base = hoyo_base(url)
    pulls, uid = [], ''
    total = len(spec['pools'])
    ps = pool_states(game)
    show = lambda i, detail, frac, page: step(detail, (i + frac) / total, pool=ps[i]['label'], page=page, pools=[dict(x) for x in ps])
    for i, (pool, gtype) in enumerate(spec['pools']):
        detail = tr('Reading {name}…', name=tr(ps[i]['label']))
        ps[i]['status'] = 'run'
        show(i, detail, 0, 0)
        rows, end_id, page = [], '0', 0
        try:
            while True:
                for attempt in range(6):  # "visit too frequently" (-110) is temporary: wait and ask again
                    d = http_json(spec['api'] + '?' + urllib.parse.urlencode(hoyo_params(game, base, gtype, end_id)))
                    if d.get('retcode') != -110:
                        break
                    time.sleep(4 + attempt * 3)
                if d.get('retcode') != 0:
                    if d.get('retcode') == -101:
                        raise Failure(tr('The history link has expired. Open the in-game pull history again.'))
                    raise Failure(tr('Official API error {code}: {msg}', code=d.get('retcode'), msg=d.get('message')))
                lst = d['data']['list']
                if not lst:
                    break
                rows += lst
                end_id = lst[-1]['id']
                page += 1
                ps[i]['n'] = len(rows)
                show(i, detail, 1 - 1 / (1 + page / 3), page)
                time.sleep(0.7)
        except Exception:
            ps[i]['status'] = 'bad'
            show(i, detail, 0, page)
            raise
        ps[i]['status'] = 'ok'
        chrono = sorted(rows, key=lambda x: int(x['id']))
        pulls += [{'pool': pool, 'id': x['id'], 'time': x['time'], 'item_id': str(x.get('item_id') or ''), 'name': x['name'], 'rarity': spec['rarity'](x['rank_type']), 'kind': x.get('item_type'),
                   'gacha_id': str(x.get('gacha_id') or '') or None} for x in chrono]
        if rows:
            uid = rows[0].get('uid', uid)
    step(tr('Uploading…'), 0.97, pool='', page=0, pools=[dict(x) for x in ps])
    return uid, pulls, 'zh-tw'  # hoyo_base() asks the API for zh-tw names, whatever language the link had


def fetch_wuwa(url, step):
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url.replace('#/record?', '?record_marker&')).query)
    need = {k: q[k][0] for k in ('svr_id', 'player_id', 'record_id', 'resources_id') if k in q}
    if len(need) < 4:
        raise Failure(tr('The history link is missing required fields. Open the in-game pull history again.'))
    lang = q.get('lang', ['zh-Hant'])[0]
    pulls = []
    total = len(WUWA_POOLS)
    ps = pool_states('wuwa')
    show = lambda i, detail, frac: step(detail, (i + frac) / total, pool=ps[i]['label'], page=0, pools=[dict(x) for x in ps])
    for i, (ptype, pool) in enumerate(WUWA_POOLS.items()):
        detail = tr('Reading {name}…', name=tr(POOL_LABELS['wuwa'][pool]))
        ps[i]['status'] = 'run'
        show(i, detail, 0)
        try:
            d = http_json(WUWA_API, {'playerId': need['player_id'], 'cardPoolId': need['resources_id'], 'cardPoolType': ptype, 'serverId': need['svr_id'], 'languageCode': lang, 'recordId': need['record_id']})
            if d.get('code') != 0:
                raise Failure(tr('The history link has expired. Open the in-game pull history again.'))
        except Exception:
            ps[i]['status'] = 'bad'
            show(i, detail, 0)
            raise
        rows = list(reversed(d.get('data') or []))  # API is newest first
        # no record id from the API, so the id is the second plus the nth pull inside that second
        counter, items = {}, []
        for x in rows:
            counter[x['time']] = counter.get(x['time'], 0) + 1
            items.append({'pool': pool, 'id': f"{x['time']}#{counter[x['time']]:02d}", 'time': x['time'], 'item_id': str(x.get('resourceId') or ''), 'name': x['name'], 'rarity': x['qualityLevel'], 'kind': x.get('resourceType')})
        pulls += items
        ps[i]['status'], ps[i]['n'] = 'ok', len(items)
        show(i, detail, 1)
    step(tr('Uploading…'), 0.97, pool='', page=0, pools=[dict(x) for x in ps])
    return need['player_id'], pulls, lang


# ---------- upload / login ----------

def upload(cfg, game, uid, pulls, lang=None):
    server = cfg['server'].rstrip('/')
    total = {'received': 0, 'added': 0, 'added5': 0, 'rejected': 0}
    for i in range(0, len(pulls), 300):
        req = urllib.request.Request(
            server + '/api/sync',
            data=json.dumps({'game': game, 'uid': uid, 'lang': lang, 'pulls': pulls[i:i + 300]}).encode(),
            headers={'Authorization': 'Bearer ' + cfg['token'], 'Content-Type': 'application/json', 'User-Agent': UA},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
        for k in total:
            total[k] += d.get(k, 0)
    return total


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def fetch_login_options(cfg):
    """Which sign-in providers the site offers."""
    d = http_json(cfg['server'].rstrip('/') + '/api/config')
    providers = [p for p in (d.get('providers') or []) if isinstance(p, str)]
    return providers


def provider_login(cfg, reporter, provider):
    """Open the browser for the chosen provider and wait for the Worker to hand back a session token."""
    server = cfg['server'].rstrip('/')
    try:
        start = http_json(server + '/api/auth/start', {'provider': provider, 'lang': LANG})
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Failure(tr('Too many people are signing in right now. Please try again in a moment.'))
        raise
    reporter.state['login']['code'] = str(start.get('user_code') or '')  # shown on the page: the browser asks for it after the provider sign-in
    reporter.phase('login', tr('Finish logging in on the tab that just opened, then enter the code shown in this window.'))
    try:
        webbrowser.open(start['url'])
    except Exception:
        pass
    print(tr('If the browser did not open, open this link manually: ') + start['url'], flush=True)
    for _ in range(200):  # ~10 minutes, same as the server-side expiry
        time.sleep(3)
        r = http_json(server + '/api/auth/poll', {'code': start['code']})
        if r['status'] == 'ok':
            cfg['token'] = r['token']
            cfg['name'] = r.get('name') or ''
            save_config(cfg)
            reporter.logged_in(cfg['name'])
            return
        if r['status'] == 'error':
            why = {'denied': 'You cancelled the authorization', 'too_many': 'Too many wrong codes. Please sign in again.', 'full': 'Registration is full right now. Please try again later.'}.get(r.get('error'), 'The sign-in provider rejected the request')
            raise Failure(tr('Login failed: {r}', r=tr(why)))
        if r['status'] == 'expired':
            break
    raise Failure(tr('Login timed out. Please run it again.'))


def check_session(cfg):
    """The signed-in account's name when the saved token still works, else None (the token is dropped)."""
    if not cfg.get('token'):
        return None
    req = urllib.request.Request(cfg['server'].rstrip('/') + '/api/me', headers={'Authorization': 'Bearer ' + cfg['token'], 'User-Agent': UA})
    try:
        name = json.loads(urllib.request.urlopen(req, timeout=20).read().decode()).get('name') or ''
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise
        cfg.pop('token', None)
        save_config(cfg)
        return None
    if cfg.get('name') != name:
        cfg['name'] = name
        save_config(cfg)
    return name


def game_of_url(url):
    if 'aki-gm-resources' in url:
        return 'wuwa'
    for g, hint in (('genshin', 'hk4e'), ('hsr', 'hkrpg'), ('zzz', 'nap')):
        if hint in url:
            return g
    return None


# ---------- one full run ----------

def sync_game(cfg, g, url, installed, args, reporter):
    if not url:
        reporter.game(g, 'skip', tr('Never opened the in-game pull history') if installed else tr('Game not found'), None)
        return False
    reporter.game(g, 'run', tr('Getting ready…'), 0, pool='', page=0)
    step = lambda detail, p, **extra: reporter.game(g, 'run', detail, p, **extra)
    try:
        uid, pulls, lang = fetch_wuwa(url, step) if g == 'wuwa' else fetch_hoyo(g, url, step)
        if args.dry_run:
            reporter.game(g, 'ok', tr('Dry run: read {n} records (not uploaded)', n=len(pulls)), None)
            return False
        try:
            r = upload(cfg, g, uid, pulls, lang)
        except urllib.error.HTTPError as e:
            if e.code != 401:
                raise
            reporter.need_login(cfg)  # the session ran out: the page asks for a new sign-in
            reporter.game(g, 'bad', tr('Your sign-in has expired. Please sign in again.'), None)
            return True
        detail = tr('{n} new, 5-star +{n5}', n=r['added'], n5=r['added5']) if r['added'] else tr('No new records')
        if r.get('rejected'):
            detail += tr(' ({n} skipped: invalid format)', n=r['rejected'])
        now = time.strftime('%Y-%m-%dT%H:%M:%S')
        cfg.setdefault('last', {})[g] = now
        try:
            save_config(cfg)
        except OSError:
            pass
        reporter.game(g, 'ok', detail, None, pool='', page=0, added=r['added'], last=now)
        return False
    except Failure as e:
        reporter.game(g, 'bad', str(e), None, pool='', page=0)
    except (urllib.error.URLError, OSError) as e:
        reporter.game(g, 'bad', tr('Connection failed: {e}', e=e), None, pool='', page=0)
    return True


def demo(reporter):
    """Fake sequence for checking the page's look (--demo); touches no game files and no server."""
    reporter.member('Demo')
    reporter.state['site'] = DEFAULT_SERVER
    for g, steps, end in (('genshin', ['Character Event Wish', 'Weapon Event Wish', 'Standard Wish'], ('ok', tr('{n} new, 5-star +{n5}', n=12, n5=1))),
                          ('hsr', [], ('skip', tr('Never opened the in-game pull history'))),
                          ('zzz', ['Exclusive Channel', 'W-Engine Channel'], ('ok', tr('No new records'))),
                          ('wuwa', ['Character Event Convene', 'Weapon Event Convene'], ('bad', tr('The history link has expired. Open the in-game pull history again.')))):
        reporter.game(g, 'run', tr('Looking for the history link…'), None)
        time.sleep(0.8)
        for i, label in enumerate(steps):
            reporter.game(g, 'run', tr('Reading {name}…', name=tr(label)), i / max(len(steps), 1))
            time.sleep(1.0)
        reporter.game(g, end[0], end[1], None)
    reporter.phase('done')
    return 0


def do_update(cfg, reporter):
    """Downloads the published exe, swaps it in place of this one (a running exe can be renamed, not overwritten) and starts it again on the same port."""
    v = dict(reporter.state['version'])
    fail = lambda msg: (reporter.state['version'].update(error=msg), reporter.phase('idle'))
    if not FROZEN or not v.get('newer') or not v.get('url'):
        return fail(tr('This build cannot update itself'))
    if not v['url'].startswith(cfg['server'].rstrip('/') + '/'):
        return fail(tr('The download address is not on the official site. Stopped.'))
    new, old = EXE + '.new', EXE + '.old'
    try:
        reporter.state['version']['error'] = ''
        reporter.phase('updating', tr('Downloading version {v}…', v=v['latest']))
        digest, got = hashlib.sha256(), 0
        with urllib.request.urlopen(urllib.request.Request(v['url'], headers={'User-Agent': UA}), timeout=60) as r, open(new, 'wb') as f:
            total = int(r.headers.get('Content-Length') or 0)
            while True:
                chunk = r.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                digest.update(chunk)
                got += len(chunk)
                if total:
                    reporter.phase('updating', tr('Downloading version {v}… {p}%', v=v['latest'], p=got * 100 // total))
        if got < 1_000_000 or (v['sha256'] and digest.hexdigest() != v['sha256']):
            raise Failure(tr('The downloaded file failed verification. Please try again.'))
        reporter.phase('updating', tr('Download complete, replacing the program…'))
        if os.path.exists(old):
            os.remove(old)
        os.replace(EXE, old)
        try:
            os.replace(new, EXE)
        except OSError:
            os.replace(old, EXE)  # put the working exe back
            raise
    except (Failure, OSError, urllib.error.URLError) as e:
        try:
            os.remove(new)
        except OSError:
            pass
        return fail(str(e) if isinstance(e, Failure) else tr('Update failed: {e}', e=e))
    reporter.phase('updating', tr('Update complete, restarting…'))
    reporter.state['restarting'] = True  # the page keeps reconnecting until the new process answers
    time.sleep(1.5)  # let the page see this message
    port = reporter.server.server_address[1] if reporter.server else 0
    if reporter.server:
        reporter.server.shutdown()
        reporter.server.server_close()  # the new process takes over the same port, so the open page just reconnects
    env = {k: val for k, val in os.environ.items() if not k.startswith('_PYI') and k != '_MEIPASS2'}
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'  # a onefile exe starting itself must unpack on its own
    subprocess.Popen([EXE, '--port', str(port), '--no-open'], env=env, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    os._exit(0)


def sync_one(cfg, g, args, reporter):
    reporter.game(g, 'run', tr('Looking for the history link…'), None)
    url, installed = wuwa_url(cfg) if g == 'wuwa' else hoyo_url(g, cfg)
    sync_game(cfg, g, url, installed, args, reporter)


def interactive(cfg, args, reporter):
    """The page shows one button per game; only what the user asks for is synced. Ends when the page has been closed."""
    reporter.phase('idle')
    started = time.time()
    auto_done = False
    while True:
        try:
            g = reporter.jobs.get(timeout=0.5)
        except queue.Empty:
            if not auto_done:  # "allow automatic updates": once the startup check has answered, update straight away (off by default)
                v = reporter.state['version']
                if not cfg.get('autoUpdate'):
                    auto_done = True
                elif v['latest'] is not None:
                    auto_done = True
                    if v['newer'] and v['canUpdate']:
                        reporter.request(['__update__'], force=True)
            gone = reporter.polled and time.time() - reporter.last_poll > 20  # the tab was closed
            never = not reporter.polled and time.time() - started > 180  # the page never opened
            if gone or never:
                return 0
            continue
        if g == '__login__':
            provider = reporter.login_args
            try:
                provider_login(cfg, reporter, provider)
            except Failure as e:
                reporter.state['login'].update(waiting=False, error=str(e), code='')
                reporter.phase('idle')
            except (urllib.error.URLError, OSError) as e:
                reporter.state['login'].update(waiting=False, error=tr('Connection failed: {e}', e=e), code='')
                reporter.phase('idle')
            continue
        if g == '__update__':
            try:
                do_update(cfg, reporter)
            except Exception as e:
                reporter.state['version']['error'] = tr('Update failed: {e}', e=e)
                reporter.phase('idle')
            reporter.finished(g)
            continue
        reporter.phase('running')
        try:
            sync_one(cfg, g, args, reporter)
        except Exception as e:  # one game failing must not end the session
            reporter.game(g, 'bad', tr('Unexpected error: {e}', e=e), None)
        reporter.finished(g)
        if reporter.jobs.empty():
            reporter.phase('idle')


def version_key(v):
    return tuple(int(x) for x in re.findall(r'\d+', v or '0'))


def check_version(cfg, reporter, manual=False):
    """Asks the site which exe version is the newest (site/version.json). A failed check just leaves the version line without a verdict."""
    with reporter.lock:
        if reporter.state['version']['checking']:
            return
        reporter.state['version']['checking'] = True
    try:
        d = http_json(cfg['server'].rstrip('/') + f'/version.json?t={int(time.time())}')
        latest = str(d.get('version') or '')
        with reporter.lock:
            reporter.state['version'].update(latest=latest, newer=version_key(latest) > version_key(VERSION), note=str(d.get('note') or ''), url=str(d.get('url') or ''), sha256=str(d.get('sha256') or '').lower(), error='', size=int(d.get('size') or 0),
                                          history=[{k: str(h.get(k) or '') for k in ('version', 'date', 'note')} for h in (d.get('history') or [])[:40] if isinstance(h, dict)])
    except Exception:
        with reporter.lock:
            reporter.state['version'].update(latest=None, newer=False)
    finally:
        if manual:
            time.sleep(0.8)  # long enough for the page to show "checking" at least once
        with reporter.lock:
            reporter.state['version']['checking'] = False


def run(args, reporter):
    if args.demo:
        return demo(reporter)
    cfg = {}
    if not os.path.isfile(CONFIG) and os.path.isfile(LEGACY_CONFIG) and LEGACY_CONFIG != CONFIG:  # move the old file once
        try:
            with open(LEGACY_CONFIG, encoding='utf-8-sig') as f:
                cfg = json.load(f)
            save_config(cfg)
            os.remove(LEGACY_CONFIG)
        except (OSError, ValueError):
            cfg = {}
    if os.path.isfile(CONFIG):
        with open(CONFIG, encoding='utf-8-sig') as f:
            cfg = json.load(f)
    cfg.setdefault('server', DEFAULT_SERVER)
    global LANG
    cfg['lang'] = LEGACY_LANGS.get(cfg.get('lang'), cfg.get('lang'))
    LANG = cfg['lang'] if cfg.get('lang') in LANGS else system_lang()
    reporter.cfg = cfg
    reporter.state['settings'] = {'lang': LANG, 'autoUpdate': bool(cfg.get('autoUpdate')), 'theme': cfg.get('theme', '')}
    for x in reporter.state['games']:
        x['last'] = str((cfg.get('last') or {}).get(x['key']) or '')
    reporter.state['site'] = cfg['server']
    reporter.check = lambda: threading.Thread(target=check_version, args=(cfg, reporter, True), daemon=True).start()
    threading.Thread(target=check_version, args=(cfg, reporter), daemon=True).start()
    failed = False
    interactive_mode = not (args.url or args.game or args.no_ui)
    try:
        if args.login:
            cfg.pop('token', None)
        name = None if args.dry_run else check_session(cfg)
        if name is not None:
            reporter.member(name)
        elif interactive_mode:
            reporter.need_login(cfg)  # the page shows the sign-in card; the games stay hidden until it is done
        elif not args.dry_run:
            providers = fetch_login_options(cfg)
            provider = args.provider or (providers[0] if providers else '')
            if provider not in providers:
                raise Failure(tr('Login failed: {r}', r=tr('The sign-in provider rejected the request')))
            provider_login(cfg, reporter, provider)
    except (Failure, urllib.error.URLError, OSError) as e:
        reporter.phase('error', str(e) if isinstance(e, Failure) else tr('Connection failed: {e}', e=e))
        return 1

    if not (args.url or args.game or args.no_ui):  # double-click use: wait for the buttons on the page
        return interactive(cfg, args, reporter)
    if args.url:
        g = game_of_url(args.url)
        if not g:
            reporter.phase('error', tr('Cannot tell which game this link is for'))
            return 1
        jobs = [(g, lambda: (args.url, True))]
    else:
        jobs = [(x['key'], None) for x in reporter.state['games']]
    for g, locate in jobs:
        if locate is None:
            reporter.game(g, 'run', tr('Looking for the history link…'), None)
            locate = (lambda: wuwa_url(cfg)) if g == 'wuwa' else (lambda g=g: hoyo_url(g, cfg))
        url, installed = locate()
        failed |= sync_game(cfg, g, url, installed, args, reporter)
    done = {j[0] for j in jobs}
    for x in reporter.state['games']:  # games not run (e.g. with --url) stay out of the way
        if x['key'] not in done:
            reporter.game(x['key'], 'skip', '', None)
    reporter.phase('done')
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', nargs='*', choices=list(GAME_NAMES), help='Sync only the given games and exit, without waiting for the buttons (default: open the window and update with the buttons)')
    ap.add_argument('--url', help='Give a pull-history link directly (the game is detected from it)')
    ap.add_argument('--dry-run', action='store_true', help='Fetch only, do not upload')
    ap.add_argument('--login', action='store_true', help='Sign in again')
    ap.add_argument('--provider', help='Which provider to sign in with when no window is shown (for example discord, google)')
    ap.add_argument('--no-ui', action='store_true', help='Do not open the browser window; print to the command line only')
    ap.add_argument('--no-open', action='store_true', help='Do not open the browser automatically (used when restarting after an update)')
    ap.add_argument('--version', action='store_true', help='Print the version and exit')
    ap.add_argument('--demo', action='store_true', help='Demo window (fake data; reads no game and uploads nothing)')
    ap.add_argument('--port', type=int, default=0, help='Port of the local window (default: random)')
    args = ap.parse_args()
    if args.version:
        print(VERSION)
        return 0

    reporter = Reporter(args.game or list(GAME_NAMES))
    result = {'code': 0}

    def work():
        try:
            result['code'] = run(args, reporter)
        except Exception as e:  # last resort: show it on the page instead of dying silently
            reporter.phase('error', tr('Unexpected error: {e}', e=e))
            result['code'] = 1

    worker = threading.Thread(target=work, daemon=True)
    server = None
    if FROZEN:  # leftover of the previous exe after a self-update; it may still be shutting down, so keep trying for a while
        def clean():
            for _ in range(60):
                if not os.path.exists(EXE + '.old'):
                    return
                try:
                    os.remove(EXE + '.old')
                    return
                except OSError:
                    time.sleep(1)
        threading.Thread(target=clean, daemon=True).start()
    if not args.no_ui:
        server = serve_ui(reporter, args.port)
        reporter.server = server
        if not args.no_open:
            try:
                webbrowser.open(f'http://127.0.0.1:{server.server_address[1]}/')
            except Exception:
                pass
    worker.start()
    worker.join()
    if server and result['code'] == 0 and not (args.url or args.game or args.no_ui):
        server.shutdown()
    elif server:  # one-shot run: keep the page alive until the browser has fetched the final state (or 40s at most)
        end = time.time() + 40
        while time.time() < end and not (reporter.polled and time.time() - reporter.last_poll > 4):
            time.sleep(0.5)
        server.shutdown()
    return result['code']


if __name__ == '__main__':
    sys.exit(main())
