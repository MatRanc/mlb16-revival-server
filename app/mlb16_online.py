"""MLB16 Online: sets up RPCS3 for MLB The Show 16 online play and runs the server, in one window.

  python mlb16_online.py            the app
  python mlb16_online.py --server   the server only (the app starts it this way, as its own process)
"""
import json, os, queue, subprocess, sys, threading, webbrowser
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import setup_logic as s

REPO = 'https://github.com/MatRanc/mlb16-revival-server'


def run_server():
    # server.py is loaded at runtime, so PyInstaller can't see its imports: name them here to get them bundled
    import base64, http.server, re, socket, ssl, struct, time, urllib.parse, uuid  # noqa: F401
    from Crypto.Cipher import AES  # noqa: F401
    os.environ['MLB16_DATA_DIR'] = str(s.data_dir())
    certs = s.ensure_host_certs()
    os.chdir(s.data_dir())
    if not (Path('certs') / 'server.pem').exists():
        raise SystemExit(f'no server certificate in {certs}')
    import runpy, warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)   # TLS 1.0 is allowed on purpose (PS3)
    runpy.run_path(str(s.bundle_dir() / 'server' / 'server.py'), run_name='__main__')


class Settings(dict):
    path = s.data_dir() / 'settings.json'

    def __init__(self):
        super().__init__(mode='host', crowd_fix=True, graphics=True)
        try:
            self.update(json.loads(self.path.read_text()))
        except (OSError, ValueError):
            pass

    def save(self):
        s.write_text(self.path, json.dumps(self, indent=1))


def friendly(line):
    """One server log line, as a sentence for the host. None = not worth showing."""
    try:
        d = json.loads(line)
    except ValueError:   # the server cuts long JSON lines short; anything else (errors, tracebacks) is shown
        return None if line.startswith('{') else line.rstrip()
    if not isinstance(d, dict):
        return line.rstrip()
    e, t = d.get('event'), d.get('t', '')
    who = d.get('player') or d.get('src') or ''
    text = {
        'login': f'{who} signed in',
        'room_join': f'{who} joined the room',
        'room_quit': f'{who} left the room',
        'game_start': f'match started: {who} vs player #{d.get("opponent")}',
        'fls_closed': f'{who} disconnected',
        'tls_fail': (f'a connection from {d.get("client")} was refused: it does not trust this server\'s certificate. '
                     'Has that player run setup with your invite?'),
    }.get(e)
    return f'{t}  {text}' if text else None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MLB16 Online')
        self.minsize(640, 560)
        try:
            import sv_ttk
            sv_ttk.set_theme('dark')
        except Exception:   # the app works with the plain ttk theme too
            pass
        self.cfg = Settings()
        self.server = None
        self.lines = queue.Queue()

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=12, pady=12)
        nb.add(self.setup_tab(nb), text='  Set up RPCS3  ')
        nb.add(self.host_tab(nb), text='  Host a game  ')
        self.protocol('WM_DELETE_WINDOW', self.quit_app)
        self.refresh()
        self.after(200, self.pump)

    # ------------------------------------------------------------ setup tab

    def setup_tab(self, nb):
        f = ttk.Frame(nb, padding=16)
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text='RPCS3 folder', font=('', 11, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
        default = s.Rpcs3.default_root()
        self.rpcs3_dir = tk.StringVar(value=self.cfg.get('rpcs3_dir') or (str(default) if default else ''))
        ttk.Entry(f, textvariable=self.rpcs3_dir).grid(row=1, column=0, columnspan=2, sticky='ew', pady=4)
        ttk.Button(f, text='Browse…', command=self.pick_rpcs3).grid(row=1, column=2, padx=(8, 0))
        hint = ('The folder with rpcs3.exe.' if sys.platform == 'win32' else 'Usually found automatically.')
        ttk.Label(f, text=hint, foreground='gray').grid(row=2, column=0, columnspan=3, sticky='w')

        ttk.Label(f, text='Who runs the server?', font=('', 11, 'bold')).grid(row=3, column=0, columnspan=3,
                                                                                sticky='w', pady=(16, 0))
        self.mode = tk.StringVar(value=self.cfg['mode'])
        ttk.Radiobutton(f, text='Me, on this computer', variable=self.mode, value='host',
                        command=self.refresh).grid(row=4, column=0, columnspan=3, sticky='w', pady=2)
        ttk.Radiobutton(f, text='A friend, who sent me an invite file', variable=self.mode, value='join',
                        command=self.refresh).grid(row=5, column=0, columnspan=2, sticky='w', pady=2)
        ttk.Button(f, text='Open invite…', command=self.open_invite).grid(row=5, column=2, padx=(8, 0))
        self.invite_label = ttk.Label(f, foreground='gray')
        self.invite_label.grid(row=6, column=0, columnspan=3, sticky='w', padx=(28, 0))

        ttk.Label(f, text='Options', font=('', 11, 'bold')).grid(row=7, column=0, columnspan=3, sticky='w',
                                                                 pady=(16, 0))
        self.crowd = tk.BooleanVar(value=self.cfg['crowd_fix'])
        self.graphics = tk.BooleanVar(value=self.cfg['graphics'])
        ttk.Checkbutton(f, text='Crowd fix patch (recommended)', variable=self.crowd).grid(
            row=8, column=0, columnspan=3, sticky='w', pady=2)
        ttk.Checkbutton(f, text='Recommended graphics settings (fixes dark crowd and black boxes)',
                        variable=self.graphics).grid(row=9, column=0, columnspan=3, sticky='w', pady=2)

        ttk.Button(f, text='Set up RPCS3', style='Accent.TButton', command=self.do_setup).grid(
            row=10, column=0, columnspan=3, sticky='ew', pady=(18, 4), ipady=4)
        ttk.Label(f, text='Close RPCS3 first. Only MLB The Show 16 is affected; other games keep their settings.',
                  foreground='gray').grid(row=11, column=0, columnspan=3, sticky='w')

        self.status = ttk.Label(f, justify='left')
        self.status.grid(row=12, column=0, columnspan=3, sticky='w', pady=(16, 0))
        link = ttk.Label(f, text='Setup guide and help', foreground='#4ea1ff', cursor='hand2')
        link.grid(row=13, column=0, columnspan=3, sticky='w', pady=(12, 0))
        link.bind('<Button-1>', lambda e: webbrowser.open(REPO))
        return f

    def pick_rpcs3(self):
        d = filedialog.askdirectory(title='RPCS3 folder', initialdir=self.rpcs3_dir.get() or str(Path.home()))
        if d:
            self.rpcs3_dir.set(d)
            self.refresh()

    def open_invite(self):
        p = filedialog.askopenfilename(title='Invite file', filetypes=[('MLB16 invite', '*.mlb16invite'),
                                                                        ('All files', '*')])
        if not p:
            return
        try:
            host, ca = s.read_invite(Path(p).read_text(encoding='utf-8'))
        except (OSError, ValueError) as e:
            messagebox.showerror('Invite', f'That invite file could not be used:\n{e}')
            return
        self.cfg.update(invite_host=host, invite_ca=ca.decode())
        self.mode.set('join')
        self.cfg.save()
        self.refresh()

    def target(self):
        """(server IP, CA bytes) for this player's RPCS3, or a reason it isn't known yet."""
        if self.mode.get() == 'host':
            return '127.0.0.1', (s.ensure_host_certs() / 'ca.pem').read_bytes()
        if not self.cfg.get('invite_host'):
            return None, 'Open the invite file your friend sent you first.'
        return self.cfg['invite_host'], self.cfg['invite_ca'].encode()

    def do_setup(self):
        r = s.Rpcs3(self.rpcs3_dir.get().strip())
        problem = r.problem()
        if problem:
            messagebox.showerror('RPCS3 folder', problem)
            return
        ip, ca = self.target()
        if ip is None:
            messagebox.showinfo('Invite needed', ca)
            return
        try:
            s.install_patches(r, crowd_fix=self.crowd.get())
            s.install_game_config(r, ip, graphics=self.graphics.get())
            s.install_ca(r, ca)
        except OSError as e:
            messagebox.showerror('Setup failed', f'{e}\n\nIs RPCS3 closed, and is this the right folder?')
            return
        self.cfg.update(rpcs3_dir=str(r.root), mode=self.mode.get(), crowd_fix=self.crowd.get(),
                        graphics=self.graphics.get())
        self.cfg.save()
        self.refresh()
        messagebox.showinfo('Done', 'RPCS3 is set up. Start the game, then go to Online → Game Rooms.'
                            + ('\n\nStart the server in the "Host a game" tab first.' if ip == '127.0.0.1' else ''))

    def refresh(self):
        if self.cfg.get('invite_host'):
            self.invite_label.config(text=f'Invite loaded: server at {self.cfg["invite_host"]}')
        else:
            self.invite_label.config(text='No invite loaded')
        r = s.Rpcs3(self.rpcs3_dir.get().strip()) if self.rpcs3_dir.get().strip() else None
        if not r or r.problem():
            self.status.config(text='Pick your RPCS3 folder.' if not r else r.problem())
            return
        want_ip, want_ca = self.target()
        ca = s.installed_ca(r)
        server = s.game_config_server(r)
        rows = [('Patches installed and ticked', s.patches_status(r)),
                (f'Game points at the server ({server or "not set"})', server is not None and server == want_ip),
                ('Server certificate trusted', ca is not None and isinstance(want_ca, bytes) and ca == want_ca)]
        self.status.config(text='\n'.join(('✓  ' if ok else '✗  ') + t for t, ok in rows))

    # ------------------------------------------------------------ host tab

    def host_tab(self, nb):
        f = ttk.Frame(nb, padding=16)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(6, weight=1)
        bar = ttk.Frame(f)
        bar.grid(row=0, column=0, sticky='ew')
        self.start_btn = ttk.Button(bar, text='Start server', style='Accent.TButton', command=self.start_server)
        self.start_btn.pack(side='left')
        self.stop_btn = ttk.Button(bar, text='Stop', command=self.stop_server, state='disabled')
        self.stop_btn.pack(side='left', padx=8)
        self.server_state = ttk.Label(bar, text='Stopped')
        self.server_state.pack(side='left', padx=8)

        ttk.Label(f, text='Your addresses', font=('', 11, 'bold')).grid(row=1, column=0, sticky='w', pady=(16, 0))
        self.addr = ttk.Label(f, justify='left')
        self.addr.grid(row=2, column=0, sticky='w')
        inv = ttk.Frame(f)
        inv.grid(row=3, column=0, sticky='w', pady=(8, 0))
        self.invite_ip = ttk.Combobox(inv, width=28, state='readonly')
        self.invite_ip.pack(side='left')
        ttk.Button(inv, text='Save invite file…', command=self.save_invite).pack(side='left', padx=8)
        ttk.Label(f, text='Send the invite file to your friend. It holds your address and your server certificate '
                          '(never your private keys).', foreground='gray', wraplength=580, justify='left').grid(
            row=4, column=0, sticky='w', pady=(4, 0))

        ttk.Label(f, text='Server activity', font=('', 11, 'bold')).grid(row=5, column=0, sticky='w', pady=(16, 0))
        self.log = tk.Text(f, height=12, wrap='word', state='disabled', relief='flat')
        self.log.grid(row=6, column=0, sticky='nsew', pady=(4, 0))
        ttk.Label(f, text=f'If your firewall asks, allow network access. Logs and certificates: {s.data_dir()}',
                  foreground='gray', wraplength=580, justify='left').grid(row=7, column=0, sticky='w', pady=(8, 0))
        self.show_addresses()
        return f

    def show_addresses(self):
        lan, ts = s.lan_ip(), s.tailscale_ip()
        rows, choices = [], []
        if ts:
            rows.append(f'Tailscale (over the internet): {ts}')
            choices.append(f'{ts}  (Tailscale)')
        if lan:
            rows.append(f'Home network: {lan}')
            choices.append(f'{lan}  (home network)')
        if not ts:
            rows.append('Tailscale not found. Install it to play with friends outside your home network.')
        self.addr.config(text='\n'.join(rows))
        self.invite_ip.config(values=choices)
        if choices:
            self.invite_ip.current(0)

    def save_invite(self):
        if not self.invite_ip.get():
            messagebox.showerror('Invite', 'No network address found.')
            return
        ip = self.invite_ip.get().split()[0]
        p = filedialog.asksaveasfilename(title='Save invite', defaultextension='.mlb16invite',
                                         initialfile='mlb16-invite.mlb16invite',
                                         filetypes=[('MLB16 invite', '*.mlb16invite')])
        if p:
            ca = (s.ensure_host_certs() / 'ca.pem').read_bytes()
            Path(p).write_text(s.make_invite(ip, ca), encoding='utf-8')
            self.write_log(f'invite saved for {ip}: {p}')

    def start_server(self):
        if self.server and self.server.poll() is None:
            return
        cmd = [sys.executable, '--server'] if getattr(sys, 'frozen', False) else [sys.executable, '-u', __file__, '--server']
        self.stopping = False
        self.server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                       env={**os.environ, 'PYTHONUNBUFFERED': '1'},
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        threading.Thread(target=self.read_server, args=(self.server,), daemon=True).start()
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.server_state.config(text='Running')
        self.write_log('server starting…')

    def read_server(self, proc):
        for line in proc.stdout:
            self.lines.put(line)
        self.lines.put(None)   # process ended

    def stop_server(self):
        if self.server and self.server.poll() is None:
            self.stopping = True
            self.server.terminate()

    def pump(self):
        try:
            while True:
                line = self.lines.get_nowait()
                if line is None:
                    code = self.server.wait() if self.server else 0
                    self.write_log('server stopped' if self.stopping else
                                   f'server stopped unexpectedly (exit code {code}). Is another server already running?')
                    self.start_btn.config(state='normal')
                    self.stop_btn.config(state='disabled')
                    self.server_state.config(text='Stopped')
                    continue
                text = friendly(line)
                if text:
                    self.write_log(text)
        except queue.Empty:
            pass
        self.after(200, self.pump)

    def write_log(self, text):
        self.log.config(state='normal')
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.log.config(state='disabled')

    def quit_app(self):
        self.stop_server()
        self.destroy()


if __name__ == '__main__':
    if '--server' in sys.argv:
        run_server()
    else:
        App().mainloop()
