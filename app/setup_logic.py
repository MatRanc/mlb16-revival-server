"""Everything the app does to RPCS3 and the host, without the window: patches, per-game config, certificates,
server certificates, invites. Kept separate so it can be tested headless (see test_setup_logic.py)."""
import datetime, ipaddress, json, os, re, shutil, socket, subprocess, sys
from pathlib import Path

import yaml

TITLE_ID = 'BCUS01089'
PPU_HASH = 'PPU-395faa2b9c12c400d03343cad62ce7aad8ec985b'
GAME_HOST = 'production.mlb16.online.scea.com'
TELEMETRY_HOST = 'mlb16.api.wwsga.me'
APP_ID = 'mlb16-online'

# Per-game settings. Graphics are the tested ones from the README; Net points the game at the server.
# Write Color Buffers is what fixes the dark crowd and black PiP boxes. Strict Rendering Mode isn't needed for it, costs
# performance (Macs), and blocks resolution scaling, so it's turned off. The game renders at 720p; sharper = scale.
GRAPHICS = {
    'Write Color Buffers': 'true', 'Read Color Buffers': 'true',
    'Write Depth Buffer': 'true', 'Read Depth Buffer': 'true',
    'Strict Rendering Mode': 'false', 'Disable Vertex Cache': 'true',
    'Shader Precision': 'High', 'Accurate ZCULL stats': 'true', 'Relaxed ZCULL Sync': 'false',
    'Resolution': '1280x720',
}
# Always set: two matches froze with SPU Block Size "Mega" and Accurate SPU Reservations off (a hang, and an RPCS3
# error inside cellSpursRemoveWorkload). These are RPCS3's defaults.
STABILITY = {'SPU Block Size': 'Safe', 'Accurate SPU Reservations': 'true'}
SCALES = {'720p': '100', '1080p': '150'}   # Resolution Scale: 1280x720 x 150% = 1920x1080


def bundle_dir():
    """Where patches/ and server.py are: the repo when run from source, the unpacked bundle when frozen."""
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))


def data_dir():
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home()))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    d = base / APP_ID
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- RPCS3 folders

class Rpcs3:
    """RPCS3's folders. On Windows everything is next to rpcs3.exe, with configs in a config/ subfolder;
    on Linux/macOS it is one folder (~/.config/rpcs3, ~/Library/Application Support/rpcs3)."""

    def __init__(self, root, windows_layout=None):
        self.root = Path(root)
        if windows_layout is None:
            windows_layout = (self.root / 'rpcs3.exe').exists()
        portable = self.root / 'portable'   # RPCS3 uses <exe dir>/portable/ for everything if it exists
        base = portable if portable.is_dir() else self.root
        cfg = base / 'config' if windows_layout and not portable.is_dir() else base
        self.patches = base / 'patches'
        self.patch_config = cfg / 'patch_config.yml'
        self.custom_config = cfg / 'custom_configs' / f'config_{TITLE_ID}.yml'
        self.cert = base / 'dev_flash' / 'data' / 'cert'
        self.cert_backup = base / 'dev_flash' / 'data' / 'cert.orig'

    @staticmethod
    def default_root():
        if sys.platform == 'darwin':
            return Path.home() / 'Library' / 'Application Support' / 'rpcs3'
        if sys.platform != 'win32':
            for p in (Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'rpcs3',
                      Path.home() / '.var' / 'app' / 'net.rpcs3.RPCS3' / 'config' / 'rpcs3'):
                if p.is_dir():
                    return p
        return None   # Windows: the user picks the folder with rpcs3.exe

    def problem(self):
        """None if this looks like a usable RPCS3 folder, else a sentence for the user."""
        if not self.root.is_dir():
            return f'{self.root} does not exist.'
        if not self.cert.is_dir():
            return ('No PS3 firmware found in this RPCS3 folder. Install it in RPCS3 first '
                    '(File → Install Firmware), or pick the folder that contains rpcs3.exe.')
        return None


def _quiet():
    return {'capture_output': True, 'text': True, 'timeout': 10,
            'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0)}


def rpcs3_running():
    """True if an RPCS3 process is running (it would overwrite the files setup writes, or not reload them)."""
    try:
        if sys.platform == 'win32':
            out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq rpcs3.exe', '/NH'], **_quiet()).stdout
            return 'rpcs3.exe' in out.lower()
        return subprocess.run(['pgrep', '-i', '-x', 'rpcs3'], **_quiet()).returncode == 0   # also the AppImage
    except (OSError, subprocess.SubprocessError):
        return False   # can't tell: don't block setup


def rpcs3_command(r, saved=None):
    """How to start RPCS3, or None if the user has to point at it (a Linux AppImage can be anywhere)."""
    if saved and Path(saved).exists():
        return [saved]
    if sys.platform == 'win32':
        exe = r.root / 'rpcs3.exe'
        return [str(exe)] if exe.exists() else None
    if sys.platform == 'darwin':
        return ['open', '-a', 'RPCS3']
    if shutil.which('rpcs3'):
        return ['rpcs3']
    if (Path.home() / '.var' / 'app' / 'net.rpcs3.RPCS3').is_dir() and shutil.which('flatpak'):
        return ['flatpak', 'run', 'net.rpcs3.RPCS3']
    return None


# ---------------------------------------------------------------- YAML as RPCS3 writes it

def load_yaml(path):
    """Every scalar stays a string ('01.10' must not become 1.1), exactly as RPCS3 reads it."""
    try:
        return yaml.load(Path(path).read_text(encoding='utf-8'), Loader=yaml.BaseLoader) or {}
    except FileNotFoundError:
        return {}


def _scalar(s):
    s = str(s)
    if s == '' or s != s.strip() or re.search(r'[:#{}\[\],&*!|>\'"%@`]', s) or s[0] in '-?':
        return json.dumps(s, ensure_ascii=False)   # a JSON string is a valid YAML double-quoted scalar
    return s


def dump_yaml(d, indent=0):
    pad, out = '  ' * indent, []
    for k, v in d.items():
        if isinstance(v, dict):
            out.append(f'{pad}{_scalar(k)}:' + (' {}' if not v else ''))
            if v:
                out.append(dump_yaml(v, indent + 1).rstrip('\n'))
        elif isinstance(v, list):
            out.append(f'{pad}{_scalar(k)}:' + (' []' if not v else ''))
            out += [f'{pad}  - {_scalar(x)}' for x in v]
        else:
            out.append(f'{pad}{_scalar(k)}: {_scalar(v)}')
    return '\n'.join(out) + '\n'


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(text, encoding='utf-8')
    os.replace(tmp, path)


# ---------------------------------------------------------------- patches

def patch_body(path):
    """The patch entries of one of our patch files, without its 'Version' and PPU-hash header lines."""
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith(PPU_HASH))
    return '\n'.join(lines[i + 1:]).strip('\n') + '\n'


def patch_names(text):
    return list(yaml.safe_load(text)[PPU_HASH])


def install_patches(r, crowd_fix=True):
    """Writes patches/BCUS01089_patch.yml (RPCS3 loads it for this game only, next to imported_patch.yml)
    and ticks every patch in it in patch_config.yml. Returns the patch names."""
    files = [bundle_dir() / 'patches' / 'MLB16_online.yml']
    if crowd_fix:
        files.append(bundle_dir() / 'patches' / 'MLB16_crowd_fix.yml')
    text = 'Version: 1.2\n\n' + PPU_HASH + ':\n' + ''.join(patch_body(f) for f in files)
    names = patch_names(text)
    write_text(r.patches / f'{TITLE_ID}_patch.yml', text)

    cfg = load_yaml(r.patch_config)
    game = cfg.setdefault(PPU_HASH, {})
    crowd = patch_names('Version: 1.2\n\n' + PPU_HASH + ':\n' + patch_body(bundle_dir() / 'patches' / 'MLB16_crowd_fix.yml'))
    for n in names:
        game[n] = {'MLB The Show 16': {TITLE_ID: {'01.10': {'Enabled': 'true'}}}}
    if not crowd_fix:   # unticked in the app: untick it in RPCS3 too, wherever it came from
        for n in crowd:
            if n in game:
                game[n] = {'MLB The Show 16': {TITLE_ID: {'01.10': {'Enabled': 'false'}}}}
    write_text(r.patch_config, dump_yaml(cfg))
    return names


def patches_status(r, crowd_fix=True):
    cfg = load_yaml(r.patch_config).get(PPU_HASH, {})
    want = patch_names('Version: 1.2\n\n' + PPU_HASH + ':\n' + patch_body(bundle_dir() / 'patches' / 'MLB16_online.yml'))
    on = [n for n in want if cfg.get(n, {}).get('MLB The Show 16', {}).get(TITLE_ID, {}).get('01.10', {}).get('Enabled') == 'true']
    return (r.patches / f'{TITLE_ID}_patch.yml').exists() and len(on) == len(want)


# ---------------------------------------------------------------- per-game config

def install_game_config(r, server_ip, graphics=True, picture='720p'):
    """Merges our settings into RPCS3's custom config for this game (created if missing). RPCS3 applies it on top
    of the global config, so only these keys change, and only for MLB The Show 16."""
    cfg = load_yaml(r.custom_config)
    net = cfg.setdefault('Net', {})
    net['Internet enabled'] = 'Connected'
    net['PSN status'] = 'RPCN'
    net['UPNP Enabled'] = 'true'
    net['IP swap list'] = f'{GAME_HOST}={server_ip}&&{TELEMETRY_HOST}={server_ip}'
    cfg.setdefault('Core', {}).update(STABILITY)
    video = cfg.setdefault('Video', {})
    if graphics:
        video.update(GRAPHICS)
    video['Resolution Scale'] = SCALES[picture]
    write_text(r.custom_config, dump_yaml(cfg))


def game_config_server(r):
    swap = load_yaml(r.custom_config).get('Net', {}).get('IP swap list', '')
    m = re.search(re.escape(GAME_HOST) + r'=([^&]+)', swap)
    return m.group(1) if m else None


# ---------------------------------------------------------------- certificates in RPCS3

def install_ca(r, ca_pem_bytes):
    """Each PS3 root certificate file becomes original + our CA, so the game trusts the server and other games
    keep working. Built from an untouched backup each time, so switching hosts replaces the old CA."""
    if not r.cert_backup.is_dir():
        shutil.copytree(r.cert, r.cert_backup)
    files = sorted(r.cert_backup.glob('*.cer'))
    for f in files:
        (r.cert / f.name).write_bytes(f.read_bytes() + ca_pem_bytes)
    return len(files)


def installed_ca(r):
    """The CA we appended to CA01.cer, or None."""
    f, b = r.cert / 'CA01.cer', r.cert_backup / 'CA01.cer'
    if not (f.exists() and b.exists()):
        return None
    extra = f.read_bytes()[len(b.read_bytes()):]
    return extra or None


# ---------------------------------------------------------------- the host's own certificates

def make_server_certs(certs_dir):
    """Root CA + server certificate for the game's hosts, like server/make_certs.sh, without needing openssl."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    d = Path(certs_dir)
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)

    def key():
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def pem_key(k):
        return k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                               serialization.NoEncryption())

    ca_key = key()
    ca_name = x509.Name([x509.NameAttribute(NameOID.COUNTRY_NAME, 'US'),
                         x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'MLB16 Revival'),
                         x509.NameAttribute(NameOID.COMMON_NAME, 'MLB16 Revival Root CA')])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now)
          .not_valid_after(now + datetime.timedelta(days=7300))
          .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
          .add_extension(x509.KeyUsage(digital_signature=False, content_commitment=False, key_encipherment=False,
                                       data_encipherment=False, key_agreement=False, key_cert_sign=True,
                                       crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .sign(ca_key, hashes.SHA256()))

    srv_key = key()
    srv = (x509.CertificateBuilder()
           .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, TELEMETRY_HOST)]))
           .issuer_name(ca_name).public_key(srv_key.public_key())
           .serial_number(x509.random_serial_number()).not_valid_before(now)
           .not_valid_after(now + datetime.timedelta(days=3650))
           .add_extension(x509.SubjectAlternativeName([x509.DNSName(TELEMETRY_HOST), x509.DNSName(GAME_HOST)]),
                          critical=False)
           .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=False)
           .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=True,
                                        data_encipherment=False, key_agreement=False, key_cert_sign=False,
                                        crl_sign=False, encipher_only=False, decipher_only=False), critical=False)
           .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
           .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
           .sign(ca_key, hashes.SHA256()))

    (d / 'ca.key').write_bytes(pem_key(ca_key))
    (d / 'ca.pem').write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (d / 'server.key').write_bytes(pem_key(srv_key))
    (d / 'server.pem').write_bytes(srv.public_bytes(serialization.Encoding.PEM))
    for k in ('ca.key', 'server.key'):
        try:
            os.chmod(d / k, 0o600)
        except OSError:
            pass


def host_certs_dir():
    return data_dir() / 'certs'


def ensure_host_certs():
    d = host_certs_dir()
    if not (d / 'server.pem').exists():
        make_server_certs(d)
    return d


# ---------------------------------------------------------------- addresses and invites

def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.2.1', 9))   # no packet is sent; this just picks the outgoing interface
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def tailscale_ip():
    exe = shutil.which('tailscale') or next((p for p in (r'C:\Program Files\Tailscale\tailscale.exe',
                                                         '/Applications/Tailscale.app/Contents/MacOS/Tailscale')
                                             if os.path.exists(p)), None)
    if not exe:
        return None
    try:
        out = subprocess.run([exe, 'ip', '-4'], capture_output=True, text=True, timeout=5,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    ips = [l.strip() for l in out.splitlines() if l.strip()]
    return ips[0] if ips else None


def make_invite(host_ip, ca_pem):
    return json.dumps({'app': APP_ID, 'version': 1, 'host': host_ip, 'ca': ca_pem.decode()}, indent=1)


def read_invite(text):
    """Validates an invite file (it comes from someone else). Returns (host_ip, ca_pem_bytes)."""
    d = json.loads(text)
    if not isinstance(d, dict) or d.get('app') != APP_ID:
        raise ValueError('This is not an MLB16 Online invite file.')
    host = str(ipaddress.ip_address(str(d.get('host', '')).strip()))   # an IP address and nothing else
    ca = str(d.get('ca', ''))
    blocks = re.findall(r'-----BEGIN CERTIFICATE-----[A-Za-z0-9+/=\s]+-----END CERTIFICATE-----', ca)
    if len(blocks) != 1:
        raise ValueError('The invite does not contain exactly one certificate.')
    from cryptography import x509
    cert = x509.load_pem_x509_certificate(blocks[0].encode())
    try:
        is_ca = cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    except x509.ExtensionNotFound:
        is_ca = False
    if not is_ca:
        raise ValueError('The certificate in the invite is not a CA certificate.')
    return host, (blocks[0].strip() + '\n').encode()
