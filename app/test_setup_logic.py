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
        assert r.logs == root if windows else r.logs.name == 'rpcs3' and r.logs != root
        if windows:
            assert r.patch_config == root / 'config' / 'patch_config.yml' and r.patches == root / 'patches'

        names = s.install_patches(r, crowd_fix=True)
        assert len(names) == 8, names
        cfg = s.load_yaml(r.patch_config)
        assert cfg['PPU-otherhash']['Some: patch']['Other Game']['BLUS00000']['01.00']['Enabled'] == 'true'
        assert all(cfg[s.PPU_HASH][n]['MLB The Show 16']['BCUS01089']['01.10']['Enabled'] == 'true' for n in names)
        assert '        01.10:' in r.patch_config.read_text()   # version key stays a plain string, never 1.1
        assert s.patches_status(r)
        s.install_patches(r, crowd_fix=False)
        crowd = s.load_yaml(r.patch_config)[s.PPU_HASH]['Crowd fix (single-draw crowd batches)']
        assert crowd['MLB The Show 16']['BCUS01089']['01.10']['Enabled'] == 'false'
        assert s.patches_status(r, crowd_fix=False) and not s.patches_status(r, crowd_fix=True)
        s.install_patches(r, face_fix=False)
        face = s.load_yaml(r.patch_config)[s.PPU_HASH]['Fix holes in player faces']
        assert face['MLB The Show 16']['BCUS01089']['01.10']['Enabled'] == 'false'
        assert s.patches_status(r, face_fix=False) and not s.patches_status(r)

        c0 = s.load_yaml(r.custom_config)
        assert c0['Video']['Resolution Scale'] == '150'
        # speed tweaks copied from a player's global config, all reset by setup
        c0['Core'].update({'SPU Block Size': 'Mega', 'RSX FIFO Fetch Accuracy': 'Fast', 'Libraries Control': ['libx.sprx:lle']})
        c0['Video'].update({'Frame limit': '60', 'Multithreaded RSX': 'true'})
        c0['Log'] = {'sys_net': 'Trace'}
        r.custom_config.write_text(s.dump_yaml(c0))
        s.install_game_config(r, '100.1.2.3', picture='720p')
        c = s.load_yaml(r.custom_config)
        assert c['Core']['PPU Decoder'] == 'Recompiler (LLVM)' and c['Video']['Resolution Scale'] == '100'
        assert all(c['Core'][k] == v for k, v in s.STABILITY.items()) and c['Core']['Libraries Control'] == []
        assert c['Video']['Frame limit'] == 'Auto' and c['Video']['Multithreaded RSX'] == 'false' and c['Log'] == {'sys_net': 'Notice'}
        assert c['Video']['Strict Rendering Mode'] == 'false' and c['Video']['Resolution'] == '1280x720'
        assert c['Video']['Output Scaling Mode'] == 'Bilinear' and c['Video']['Anisotropic Filter Override'] == '0'
        assert s.game_config_status(r, picture='720p') and not s.game_config_status(r, picture='1080p')
        s.install_game_config(r, '100.1.2.3', graphics=False, picture='1080p')
        c = s.load_yaml(r.custom_config)
        assert c['Video']['Resolution Scale'] == '150' and c['Core']['SPU Block Size'] == 'Safe'
        assert c['Video']['Resolution'] == '1920x1080' and c['Video']['Anisotropic Filter Override'] == '8'
        assert c['Video']['Write Color Buffers'] == 'false' and c['Net']['PSN status'] == 'RPCN'   # unticked: RPCS3 defaults
        assert s.game_config_server(r) == '100.1.2.3'
        assert s.game_config_status(r, graphics=False, picture='1080p') and not s.game_config_status(r, picture='1080p')
        r.face_cache.parent.mkdir(parents=True, exist_ok=True)
        r.face_cache.write_text('faces saved without Write Color Buffers')
        s.install_game_config(r, '100.1.2.3', picture='1080p', scale=500)   # turns Write Color Buffers back on
        assert not r.face_cache.exists() and r.face_cache.with_name('HeadFaceCacheFile.old').exists()
        r.face_cache.write_text('rebuilt faces')
        s.install_game_config(r, '100.1.2.3', picture='1080p', scale=500)   # already on: the rebuilt cache stays
        assert r.face_cache.read_text() == 'rebuilt faces'
        assert s.load_yaml(r.custom_config)['Video']['Resolution Scale'] == '500'
        assert s.load_yaml(r.custom_config)['Video']['MSAA'] == 'Disabled' and c['Video']['MSAA'] == 'Auto'
        assert s.game_config_status(r, picture='1080p', scale=500) and not s.game_config_status(r, picture='1080p')

        r.custom_config.write_text('Video: [unclosed\n')   # a corrupt config must not make Set up fail forever
        s.install_game_config(r, '100.1.2.3', picture='1080p')
        assert s.game_config_status(r, picture='1080p') and Path(str(r.custom_config) + '.broken').exists()

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
        for bad in ('{"app": "x"}', '[1, 2]', '"text"', s.make_invite('evil.example.com', ca),
                    s.make_invite('1.2.3.4', (certs / 'server.pem').read_bytes())):
            try:
                s.read_invite(bad)
                raise AssertionError('accepted a bad invite: ' + bad[:40])
            except ValueError:
                pass

fp = Path.home() / '.var' / 'app' / 'net.rpcs3.RPCS3'
assert s.is_newer('v0.4.10', 'v0.4.9') and not s.is_newer('v0.4.9', 'v0.4.10') and not s.is_newer('v0.4.9', 'v0.4.9')
assert not s.is_newer('v0.5.0', 'dev') and not s.is_newer(None, 'v0.4.9') and not s.is_newer('nightly', 'v0.4.9')
assert s.Rpcs3(fp / 'config' / 'rpcs3', windows_layout=False).logs == fp / 'cache' / 'rpcs3' or s.sys.platform == 'darwin'

print('setup_logic: all checks passed')
