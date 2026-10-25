"""Private server for MLB The Show 16 online (PS3, v01.10) on RPCS3.

Serves:
- mlb16.api.wwsga.me:443 (WWS telemetry, answered with {})
- production.mlb16.online.scea.com: 10050 plain HTTP / 10051 TLS game API (XML), see gamedata/services.xml
- FLS, the live session server, on FLS_PORT over TCP. Frames are a u16 big-endian length +
  AES-256-ECB(zero-padded XML), keyed with the ASCII bytes of server_private_key.

Players are identified by the online ID in their RPCN ticket at login; later HTTP calls are tied to them
via the X-Analytics-Session-UUID header, and FLS connections via the player_id in their Hello.
FLS messages between players (target="plyr" / "zone") are relayed as-is, stamped with the sender, so
the server does not need to understand challenge/chat payloads.

Known endpoints get real replies (ROUTES); any other .xml call gets an empty success reply and is logged
as 'unhandled'. Everything is logged to requests.jsonl.

usage: python3 server.py      (pip install -r requirements.txt; run ./make_certs.sh once first)
"""
import base64, json, os, re, socket, ssl, struct, threading, time, urllib.parse, uuid
from Crypto.Cipher import AES
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTS = {443: True, 10051: True, 10050: False}   # port: use TLS
FLS_HOST, FLS_PORT = 'production.mlb16.online.scea.com', 10070
FLS_KEY = '00112233445566778899aabbccddeeff'   # any 32 ASCII chars; it is the AES-256 key
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # certs/, logs and player ids live next to this file
LOG = open('requests.jsonl', 'a', buffering=1)
STATE = threading.RLock()


def log(**kv):
    kv['t'] = time.strftime('%H:%M:%S')
    LOG.write(json.dumps(kv) + '\n')
    print(json.dumps(kv)[:400], flush=True)


def ok(inner):
    return ('<?xml version="1.0" encoding="UTF-8"?><result><status><id>0</id>'
            '<message>Successful completion</message></status><response>' + inner + '</response></result>')


def esc(s):
    return str(s).replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;')


# ---------------------------------------------------------------- players

class Player:
    def __init__(self, pid, name):
        self.id, self.name = pid, name
        self.session_uuid = str(uuid.uuid4())
        self.channel = None          # lobby channel id the player is in
        self.fls = None              # FLS connection


PLAYERS = {}         # name -> Player
BY_ID = {}           # player id -> Player
BY_SESSION = {}      # X-Analytics-Session-UUID -> Player
IDS_FILE = 'player_ids.json'
try:
    IDS = json.load(open(IDS_FILE))
except (OSError, ValueError):
    IDS = {}


def player_for(name):
    with STATE:
        if name not in PLAYERS:
            if name not in IDS:
                IDS[name] = 1001 + len(IDS)
                json.dump(IDS, open(IDS_FILE, 'w'))
            p = Player(IDS[name], name)
            PLAYERS[name], BY_ID[p.id] = p, p
        return PLAYERS[name]


def ticket_online_id(ticket_b64):
    """Online ID from an NP ticket: the first TLV of type 4 with length 32 (RPCN and PSN tickets alike)."""
    t = base64.b64decode(ticket_b64)
    i = 8
    while i + 4 <= len(t):
        ty, ln = struct.unpack_from('>HH', t, i)
        if ty in (0x3000, 0x3002):   # container TLVs: descend
            i += 4
            continue
        if ty == 4 and ln == 32:
            return t[i + 4:i + 36].split(b'\0')[0].decode('utf-8', 'replace')
        i += 4 + ln
    raise ValueError('no online id in ticket')


def ticket_attrs(p, prefix=''):
    return ''.join(f' {prefix}{k}="{esc(v)}"' for k, v in (
        ('session_uuid', p.session_uuid), ('signature', '00'), ('player_id', p.id),
        ('username', p.name), ('expiration_date', '2030-01-01T00:00:00Z')))


# ---------------------------------------------------------------- HTTP routes (req: form, query, player)

def login(req):
    p = player_for(ticket_online_id(req['form']['ticket']))
    with STATE:
        BY_SESSION[req['session']] = p
    log(event='login', player=p.name, id=p.id)
    return ok(f'<login_data player_id="{p.id}" player_name="{esc(p.name)}"/>'
              f'<fls_data server_address="{FLS_HOST}" server_port="{FLS_PORT}" server_private_key="{FLS_KEY}"'
              + ticket_attrs(p, 'ticket_') + '/>')


def server_select(req):
    p = req['player']
    return ok(f'<server address="{FLS_HOST}" port="{FLS_PORT}" server_private_key="{FLS_KEY}">'
              f'<ticket{ticket_attrs(p)}/></server>')


ROOMS = {1: 'Revival Room'}


def lobby_list(req):
    # player_skill_level is required on <lobby_channels>; rows need min/max_skill. Other column names are
    # guesses (the compiled UI script only has hashes), so several plausible names are sent at once.
    rows = ''
    for rid, name in ROOMS.items():
        n = sum(1 for p in BY_ID.values() if p.channel == rid)
        rows += (f'<lobby_channel id="{rid}" lobby_channel_id="{rid}" name="{esc(name)}" description="{esc(name)}"'
                 f' min_skill="0" max_skill="100" num_players="{n}" player_count="{n}" players="{n}"'
                 ' max_players="100" capacity="100" ping="0"/>')
    return ok(f'<lobby_channels page="1" total_pages="1" player_skill_level="50">{rows}</lobby_channels>')


def player_row(p):
    # guessed column names, as for rooms; stats are all zero
    return (f'<lobby_channel_player id="{p.id}" player_id="{p.id}" mlb_player_id="{p.id}" username="{esc(p.name)}"'
            f' user_name="{esc(p.name)}" name="{esc(p.name)}" player_name="{esc(p.name)}" online_id="{esc(p.name)}"'
            f' np_online_id="{esc(p.name)}" ping="50" skill_level="50" player_skill_level="50" xp="0" streak="0"'
            ' avg="0" era="0" wins="0" losses="0" quits="0" disc="0" lobby_channel_id="1"/>')


def lobby_players(req):
    rid = int(req['query'].get('lobby_channel_id') or 1)
    rows = ''.join(player_row(p) for p in BY_ID.values() if p.channel == rid)
    return ok(f'<lobby_channel_players page="1" total_pages="1">{rows}</lobby_channel_players>')


def lobby_join(req):
    p = req['player']
    if p:
        p.channel = 1   # shortcut: client sends lobby_channel_id=0; there is only one room
        log(event='room_join', player=p.name)
    return ok('')


def lobby_quit(req):
    p = req['player']
    if p:
        p.channel = None
        log(event='room_quit', player=p.name)
    return ok('')


def lobby_show(req):
    rid = int(req['query'].get('id') or 1)
    return ok(f'<lobby_channel id="{rid}" lobby_channel_id="{rid}" name="{esc(ROOMS.get(rid, "Room"))}"'
              ' min_skill="0" max_skill="100"/>')


ROUTES = {'/mlb_logins/login.xml': login,
          '/servers/select.xml': server_select,
          '/lobby_channels/list_with_my_league_rooms.xml': lobby_list,
          '/lobby_channels/show.xml': lobby_show,
          '/lobby_channel_players/list_with_ping.xml': lobby_players,
          '/lobby_channel_players/join_with_ping.xml': lobby_join,
          '/lobby_channel_players/quit.xml': lobby_quit,
          '/mlb_login/post_update.xml': lambda req: ok(''),
          '/session/ping.xml': lambda req: ok(''),                  # client only records the time of the last good ping
          '/universal_profiles/update.xml': lambda req: ok('')}


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def handle_any(self):
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n).decode('utf-8', 'replace') if n else ''
        path, _, qs = self.path.partition('?')
        session = self.headers.get('X-Analytics-Session-UUID', '')
        log(event='request', port=self.server.server_port, method=self.command, path=self.path,
            headers=dict(self.headers), body=body, tls=getattr(self.connection, 'version', lambda: None)())
        route = ROUTES.get(path)
        if route:
            req = dict(form={k: v[0] for k, v in urllib.parse.parse_qs(body).items()},
                       query={k: v[0] for k, v in urllib.parse.parse_qs(qs).items()},
                       session=session, player=BY_SESSION.get(session))
            try:
                out = route(req).encode()
            except Exception as e:   # keep serving; a bad request should not kill the server
                log(event='route_error', path=path, error=repr(e))
                out = ok('').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/xml;charset=utf-8')   # game parses only this exact value
        elif path.endswith('/telemetry'):
            out = b'{}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
        elif path.endswith('.xml'):
            # shortcut: empty success for endpoints we haven't built yet; replace with real data as needed
            log(event='unhandled', method=self.command, path=self.path)
            out = ok('').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/xml;charset=utf-8')
        else:
            out = b''
            self.send_response(404)
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = handle_any

    def log_message(self, *a):
        pass


class TLSServer(ThreadingHTTPServer):
    def get_request(self):
        raw, addr = self.socket.accept()
        if not self.use_tls:
            return raw, addr
        try:
            conn = CTX.wrap_socket(raw, server_side=True)
        except (ssl.SSLError, OSError) as e:
            # "alert unknown ca" / "bad certificate" here = the PS3 rejected our certificate
            log(event='tls_fail', port=self.server_port, client=addr[0], error=str(e))
            raw.close()
            raise
        return conn, addr

    def handle_error(self, request, client_address):
        pass


CTX = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
CTX.minimum_version = ssl.TLSVersion.TLSv1        # PS3 libssl is TLS 1.0 era
CTX.set_ciphers('ALL:@SECLEVEL=0')
CTX.load_cert_chain('certs/server.pem', 'certs/server.key')


# ---------------------------------------------------------------- FLS

def recv_exact(conn, n):
    buf = b''
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            raise ConnectionError('closed')
        buf += chunk
    return buf


class FlsConn:
    def __init__(self, sock, addr):
        self.sock, self.addr = sock, f'{addr[0]}:{addr[1]}'
        self.aes = AES.new(FLS_KEY.encode(), AES.MODE_ECB)
        self.lock = threading.Lock()
        self.closed = threading.Event()
        self.player = None
        self.layers = set()

    def send_xml(self, xml):
        data = xml.encode()
        data += b'\0' * (-len(data) % 16)
        with self.lock:
            self.sock.sendall(struct.pack('>H', len(data)) + self.aes.encrypt(data))

    def send(self, inner, target_id=None):
        tid = target_id if target_id is not None else (self.player.id if self.player else 0)
        self.send_xml('<?xml version="1.0" encoding="utf-8"?>\n<message delivery="gtd" layer="989fls" sender="srvr" '
                      f'senderID="0" target="plyr" targetID="{tid}">\n\t{inner}\n</message>\n')
        log(event='fls_out', to=self.who(), xml=inner)

    def who(self):
        return self.player.name if self.player else self.addr


def relay(src, xml, attrs):
    """Forward a player-to-player or zone message, stamped with the sender."""
    stamped = re.sub(r'<message ', f'<message sender="plyr" senderID="{src.player.id}" ', xml.replace(
        ' sender="', ' x_sender="'), count=1)
    with STATE:
        if attrs.get('target') == 'plyr':
            dst = BY_ID.get(int(attrs.get('targetID', 0)))
            targets = [dst] if dst and dst.fls else []
        else:   # zone: everyone else registered on the same layer
            targets = [p for p in BY_ID.values() if p.fls and p is not src.player and attrs.get('layer') in p.fls.layers]
    for p in targets:
        try:
            p.fls.send_xml(stamped)
        except OSError:
            pass
    log(event='fls_relay', src=src.who(), layer=attrs.get('layer'), target=attrs.get('target'),
        to=[p.name for p in targets])


def fls_client(sock, addr):
    c = FlsConn(sock, addr)

    def keepalive():   # the client drops FLS if it hears nothing for a while
        while not c.closed.wait(10):
            try:
                c.send('<Keepalive/>')
            except OSError:
                return

    try:
        while True:
            n = struct.unpack('>H', recv_exact(sock, 2))[0]
            xml = c.aes.decrypt(recv_exact(sock, n)).rstrip(b'\0').decode('utf-8', 'replace')
            if 'Keepalive' not in xml:
                log(event='fls_in', src=c.who(), xml=xml)
            m = re.search(r'<message([^>]*)>\s*<(\w+)([^>]*?)/?>', xml)
            if not m:
                continue
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            kind, body = m.group(2), dict(re.findall(r'(\w+)="([^"]*)"', m.group(3)))
            if attrs.get('target', 'srvr') in ('plyr', 'zone') and c.player:
                relay(c, xml, attrs)
            elif kind == 'Hello':
                p = BY_ID.get(int(body.get('player_id', 0))) or player_for(body.get('username', '?'))
                c.player = p
                with STATE:
                    old, p.fls = p.fls, c
                if old and old is not c:
                    old.closed.set()
                c.send(f'<Hello{m.group(3).rstrip("/")}/>')
                threading.Thread(target=keepalive, daemon=True).start()
            elif kind == 'PluginRegister':
                c.layers.add(body.get('Layer'))
            elif kind == 'PluginUnregister':
                c.layers.discard(body.get('Layer'))
    except (ConnectionError, OSError, ValueError) as e:
        log(event='fls_closed', src=c.who(), error=str(e))
    finally:
        c.closed.set()
        with STATE:
            if c.player and c.player.fls is c:
                c.player.fls = None
                c.player.channel = None   # gone from FLS = gone from the room
        sock.close()


def fls_server():
    srv = socket.create_server(('0.0.0.0', FLS_PORT))
    while True:
        sock, addr = srv.accept()
        threading.Thread(target=fls_client, args=(sock, addr), daemon=True).start()


if __name__ == '__main__':
    threading.Thread(target=fls_server, daemon=True).start()
    for port, tls in PORTS.items():
        try:
            srv = TLSServer(('0.0.0.0', port), Handler)
        except PermissionError:   # 443 is only telemetry; the game works without it
            print(f'port {port} needs privileges, skipping it', flush=True)
            continue
        srv.use_tls = tls
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f'listening on {list(PORTS)} + FLS {FLS_PORT}, logging to requests.jsonl', flush=True)
    threading.Event().wait()
