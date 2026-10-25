"""Headless check of setup_logic against fake RPCS3 folders (Linux and Windows layouts). Run: python test_setup_logic.py"""
import shutil, ssl, tempfile
from pathlib import Path

import setup_logic as s


def fake_rpcs3(root, windows):
    cert = root / 'dev_flash' / 'data' / 'cert'
    cert.mkdir(parents=True)
    for i in (1, 2):
        (cert / f'CA0{i}.cer').write_bytes(b'-----BEGIN CERTIFICATE-----\nORIGINAL%d\n-----END CERTIFICATE-----\n' % i)
    if windows:
        (root / 'rpcs3.exe').write_bytes(b'')
    r = s.Rpcs3(root)
    # an existing patch_config with another game and a quoted version, like RPCS3 writes it
    r.patch_config.parent.mkdir(parents=True, exist_ok=True)
    r.patch_config.write_text('PPU-otherhash:\n  "Some: patch":\n    Other Game:\n      BLUS00000:\n        01.00:\n'
                              '          Enabled: true\n')
    r.custom_config.parent.mkdir(parents=True, exist_ok=True)
    r.custom_config.write_text('Core:\n  PPU Decoder: Recompiler (LLVM)\nVideo:\n  Resolution Scale: 150\n')
    return r


for windows in (False, True):
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        r = fake_rpcs3(root, windows)
        assert r.problem() is None
        if windows:
            assert r.patch_config == root / 'config' / 'patch_config.yml' and r.patches == root / 'patches'

        names = s.install_patches(r, crowd_fix=True)
        assert len(names) == 6, names
        cfg = s.load_yaml(r.patch_config)
        assert cfg['PPU-otherhash']['Some: patch']['Other Game']['BLUS00000']['01.00']['Enabled'] == 'true'
        assert all(cfg[s.PPU_HASH][n]['MLB The Show 16']['BCUS01089']['01.10']['Enabled'] == 'true' for n in names)
        assert '        01.10:' in r.patch_config.read_text()   # version key stays a plain string, never 1.1
        assert s.patches_status(r)
        s.install_patches(r, crowd_fix=False)
        crowd = s.load_yaml(r.patch_config)[s.PPU_HASH]['Crowd fix (single-draw crowd batches)']
        assert crowd['MLB The Show 16']['BCUS01089']['01.10']['Enabled'] == 'false'

        s.install_game_config(r, '100.1.2.3')
        c = s.load_yaml(r.custom_config)
        assert c['Core']['PPU Decoder'] == 'Recompiler (LLVM)' and c['Video']['Resolution Scale'] == '150'
        assert c['Video']['Write Color Buffers'] == 'true' and c['Net']['PSN status'] == 'RPCN'
        assert s.game_config_server(r) == '100.1.2.3'

        certs = root / 'hostcerts'
        s.make_server_certs(certs)
        ca = (certs / 'ca.pem').read_bytes()
        assert s.install_ca(r, ca) == 2 and s.installed_ca(r) == ca
        assert (r.cert / 'CA01.cer').read_bytes().startswith(b'-----BEGIN CERTIFICATE-----\nORIGINAL1')
        s.install_ca(r, ca)   # re-running does not stack a second copy
        assert (r.cert / 'CA01.cer').read_bytes().count(b'BEGIN CERTIFICATE') == 2

        # the server certificate verifies against the CA for both game hosts
        ctx = ssl.create_default_context(cafile=str(certs / 'ca.pem'))
        srv = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        srv.load_cert_chain(certs / 'server.pem', certs / 'server.key')

        host, got = s.read_invite(s.make_invite('100.1.2.3', ca))
        assert host == '100.1.2.3' and got == ca
        for bad in ('{"app": "x"}', s.make_invite('evil.example.com', ca),
                    s.make_invite('1.2.3.4', (certs / 'server.pem').read_bytes())):
            try:
                s.read_invite(bad)
                raise AssertionError('accepted a bad invite: ' + bad[:40])
            except ValueError:
                pass

print('setup_logic: all checks passed')
