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


def linux_launcher():
    """A .desktop entry, so GNOME/KDE show "MLB16 Online" and the icon (matched by window class) instead of "Tk".
    Also puts the app in the app menu."""
    icon = s.data_dir() / 'icon.png'
    entry = Path.home() / '.local' / 'share' / 'applications' / 'mlb16-online.desktop'
    cmd = [sys.executable] if getattr(sys, 'frozen', False) else [sys.executable, os.path.abspath(__file__)]
    text = ('[Desktop Entry]\nType=Application\nName=MLB16 Online Launcher\nComment=Play MLB The Show 16 online on RPCS3\n'
            f'Exec={" ".join(chr(34) + c + chr(34) for c in cmd)}\nIcon={icon}\nStartupWMClass=Mlb16-online\n'
            'Categories=Game;\nTerminal=false\n')
    try:
        icon.write_bytes((s.bundle_dir() / 'app' / 'icon.png').read_bytes())
        if not entry.exists() or entry.read_text() != text:
            s.write_text(entry, text)
    except OSError:   # cosmetic only
        pass


class Settings(dict):
    path = s.data_dir() / 'settings.json'

    def __init__(self):
        super().__init__(mode='host', crowd_fix=True, face_fix=True, graphics=True, picture='720p')
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
        if line.startswith('listening on'):
            return 'Server ready. Waiting for players…'
        return None if line.startswith(('{', 'port 443 skipped')) else line.rstrip()   # optional telemetry
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


def link(parent, text, url):
    lbl = ttk.Label(parent, text=text, style='Link.TLabel', cursor='hand2')
    lbl.bind('<Button-1>', lambda e: webbrowser.open(url))
    return lbl


class App(tk.Tk):
    def __init__(self):
        if sys.platform == 'win32':   # own taskbar entry and icon, instead of being grouped under python.exe
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('MatRanc.MLB16Online')
            try:   # draw at the screen's real resolution instead of being stretched (blurry) by display scaling
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except (AttributeError, OSError):
                pass
        super().__init__(className='mlb16-online')   # Tk turns this into the window class "Mlb16-online"
        if sys.platform.startswith('linux'):
            linux_launcher()
        self.title('MLB16 Online Launcher')
        try:
            self.iconphoto(True, tk.PhotoImage(file=str(s.bundle_dir() / 'app' / 'icon.png')))
        except tk.TclError:
            pass
        self.minsize(640, 560)
        try:
            import sv_ttk
            sv_ttk.set_theme('dark')
            # sv_ttk recolours every widget (tk_setPalette) on each <<ThemeChanged>>, and Tk 9 sends one after the first
            # ttk widget and after every style.configure, wiping our hint/link/log colours. Apply its palette once
            # now, before any widget exists, then disable it.
            self.tk.call('configure_colors')
            self.tk.eval('proc configure_colors {} {}')
        except Exception:   # the app works with the plain ttk theme too
            pass
        style = ttk.Style(self)
        style.configure('Hint.TLabel', foreground='#9a9a9a')   # fixed colours: "gray" differs between platforms
        style.configure('Link.TLabel', foreground='#4ea1ff')
        style.configure('Running.TLabel', foreground='#3fb950')
        self.cfg = Settings()
        self.server = None
        self.lines = queue.Queue()

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=12, pady=12)
        nb.add(self.setup_tab(nb), text='  1. Set up RPCS3  ')
        nb.add(self.host_tab(nb), text='  2. Run the server (host only)  ')
        nb.bind('<<NotebookTabChanged>>', lambda e: (self.show_addresses(), self.refresh()))   # Tailscale started later
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
        ttk.Label(f, text=hint, style='Hint.TLabel').grid(row=2, column=0, columnspan=3, sticky='w')

        ttk.Label(f, text='How are you playing?', font=('', 11, 'bold')).grid(row=3, column=0, columnspan=3,
                                                                                sticky='w', pady=(16, 0))
        self.mode = tk.StringVar(value=self.cfg['mode'])
        ttk.Radiobutton(f, text="I'm hosting (the server runs on this computer)", variable=self.mode, value='host',
                        command=self.refresh).grid(row=4, column=0, columnspan=3, sticky='w', pady=2)
        ttk.Radiobutton(f, text="I'm joining a friend (they sent me an invite file)", variable=self.mode, value='join',
                        command=self.refresh).grid(row=5, column=0, columnspan=3, sticky='w', pady=2)
        inv = ttk.Frame(f)   # shown only when joining; the empty label keeps the spacing when hosting
        inv.grid(row=6, column=0, columnspan=3, sticky='w', padx=(28, 0), pady=(2, 0))
        self.invite_btn = ttk.Button(inv, text='Open invite…', command=self.open_invite)
        self.invite_label = ttk.Label(inv, style='Hint.TLabel')
        self.invite_label.pack(side='right', padx=(10, 0))

        ttk.Label(f, text='Options', font=('', 11, 'bold')).grid(row=7, column=0, columnspan=3, sticky='w',
                                                                 pady=(16, 0))
        self.crowd = tk.BooleanVar(value=self.cfg['crowd_fix'])
        self.graphics = tk.BooleanVar(value=self.cfg['graphics'])
        self.face = tk.BooleanVar(value=self.cfg['face_fix'])
        fixes = ttk.Frame(f)
        fixes.grid(row=8, column=0, columnspan=3, sticky='w', pady=2)
        ttk.Checkbutton(fixes, text='Crowd fix patch (recommended)', variable=self.crowd,
                        command=self.refresh).pack(side='left')
        ttk.Checkbutton(fixes, text='Face fix patch (recommended, untick for weak GPUs)', variable=self.face,
                        command=self.refresh).pack(side='left', padx=(16, 0))
        ttk.Checkbutton(f, text='Recommended graphics settings (fixes dark crowd and black boxes)',
                        variable=self.graphics, command=self.refresh).grid(row=9, column=0, columnspan=3, sticky='w', pady=2)
        # Resolution and Sharpness share a grid so their controls line up
        pic = ttk.Frame(f)
        pic.grid(row=10, column=0, columnspan=3, sticky='w', pady=(8, 0))
        self.picture = tk.StringVar(value=self.cfg['picture'])
        ttk.Label(pic, text='Resolution:').grid(row=0, column=0, sticky='w', padx=(0, 12))
        res = ttk.Frame(pic)
        res.grid(row=0, column=1, sticky='w')
        ttk.Radiobutton(res, text='720p (fastest)', variable=self.picture, value='720p',
                        command=self.picture_changed).pack(side='left')
        ttk.Radiobutton(res, text='1080p (sharper)', variable=self.picture, value='1080p',
                        command=self.picture_changed).pack(side='left', padx=(16, 0))
        self.scale = tk.IntVar(value=self.cfg.get('scale') or int(s.PICTURE[self.picture.get()]['Resolution Scale']))
        ttk.Label(pic, text='Sharpness:').grid(row=1, column=0, sticky='w', padx=(0, 12), pady=(8, 0))
        sharp = ttk.Frame(pic)
        sharp.grid(row=1, column=1, sticky='w', pady=(8, 0))
        self.scale_slider = ttk.Scale(sharp, from_=100, to=500, length=200, value=self.scale.get(),
                                      command=self.scale_moved)
        self.scale_slider.pack(side='left')
        self.scale_label = ttk.Label(sharp, text=f'{self.scale.get()}%', width=5)
        self.scale_label.pack(side='left', padx=(10, 0))
        ttk.Label(f, text='Higher values need a stronger graphics card. Applied when you click Set up RPCS3.',
                  style='Hint.TLabel').grid(row=11, column=0, columnspan=3, sticky='w', pady=(6, 0))

        self.setup_btn = ttk.Button(f, text='Set up RPCS3', command=self.do_setup)
        self.setup_btn.grid(row=12, column=0, columnspan=3, sticky='ew', pady=(20, 4), ipady=4)
        self.launch_btn = ttk.Button(f, text='Launch RPCS3', command=self.launch_rpcs3)
        self.launch_btn.grid(row=13, column=0, columnspan=3, sticky='ew', ipady=4)

        self.status = ttk.Label(f, justify='left')
        self.status.grid(row=14, column=0, columnspan=3, sticky='w', pady=(16, 0))
        links = ttk.Frame(f)
        links.grid(row=15, column=0, columnspan=3, sticky='w', pady=(12, 0))
        link(links, 'Setup guide', REPO + '#setup').pack(side='left')
        link(links, 'Troubleshooting', REPO + '#troubleshooting').pack(side='left', padx=(16, 0))
        logs = ttk.Label(links, text='Open RPCS3 logs', style='Link.TLabel', cursor='hand2')
        logs.pack(side='left', padx=(16, 0))
        logs.bind('<Button-1>', lambda e: self.open_rpcs3_logs())
        return f

    def pick_rpcs3(self):
        d = filedialog.askdirectory(title='RPCS3 folder', initialdir=self.rpcs3_dir.get() or str(Path.home()))
        if d:
            self.rpcs3_dir.set(d)
            self.refresh()

    def open_rpcs3_logs(self):
        folder = s.Rpcs3(self.rpcs3_dir.get().strip()).logs if self.rpcs3_dir.get().strip() else None
        if not folder or not folder.is_dir():
            messagebox.showinfo('RPCS3 logs', 'No RPCS3 log folder found yet. Pick your RPCS3 folder and start RPCS3 once.')
            return
        webbrowser.open(folder.as_uri())

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

    def launch_rpcs3(self):
        if self.mode.get() == 'host' and not self.server_running() and not messagebox.askyesno(
                'Launch RPCS3', "The server isn't running. Your friend won't be able to connect until you start it "
                                'in tab 2.\n\nLaunch RPCS3 anyway?'):
            return
        r = s.Rpcs3(self.rpcs3_dir.get().strip())
        cmd = s.rpcs3_command(r, self.cfg.get('rpcs3_exe'))
        if not cmd:
            exe = filedialog.askopenfilename(title='Where is RPCS3? (the RPCS3 program or AppImage)')
            if not exe:
                return
            self.cfg['rpcs3_exe'] = exe
            self.cfg.save()
            cmd = [exe]
        env = dict(os.environ)
        if getattr(sys, 'frozen', False):
            # the bundled app points the library search path at its own temp folder; RPCS3 must not inherit that
            # (on Windows it then loads our vcruntime140.dll and refuses to start)
            if sys.platform == 'win32':
                import ctypes
                ctypes.windll.kernel32.SetDllDirectoryW(None)
            for k in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'):
                orig = env.pop(k + '_ORIG', None)
                if orig is None:
                    env.pop(k, None)
                else:
                    env[k] = orig
        try:
            subprocess.Popen(cmd, env=env, cwd=str(Path(cmd[0]).parent) if Path(cmd[0]).is_absolute() else None)
        except OSError as e:
            self.cfg.pop('rpcs3_exe', None)   # ask again next time
            self.cfg.save()
            messagebox.showerror('Launch RPCS3', f'Could not start RPCS3:\n{e}')

    def picture_changed(self):
        self.set_scale(int(s.PICTURE[self.picture.get()]['Resolution Scale']))
        self.refresh()

    def scale_moved(self, value):
        if self.set_scale(round(float(value) / 50) * 50):   # the slider fires on every pixel of a drag
            self.refresh()

    def set_scale(self, v):
        """Snaps the slider to 50% steps. True if the value changed."""
        if self.scale_slider.get() != v:   # set() runs the slider's command again
            self.scale_slider.set(v)
        self.scale_label.config(text=f'{v}%')
        changed = v != self.scale.get()
        self.scale.set(v)
        return changed

    def do_setup(self):
        r = s.Rpcs3(self.rpcs3_dir.get().strip())
        problem = r.problem()
        if problem:
            messagebox.showerror('RPCS3 folder', problem)
            return
        if s.rpcs3_running():
            messagebox.showwarning('Close RPCS3', 'RPCS3 is open. Close it first, then click Set up RPCS3 again.\n\n'
                                   'Only MLB The Show 16 is changed; your other games keep their settings.')
            return
        ip, ca = self.target()
        if ip is None:
            messagebox.showinfo('Invite needed', ca)
            return
        try:
            s.install_patches(r, crowd_fix=self.crowd.get(), face_fix=self.face.get())
            s.install_game_config(r, ip, graphics=self.graphics.get(), picture=self.picture.get(),
                                  scale=self.scale.get())
            s.install_ca(r, ca)
        except OSError as e:
            messagebox.showerror('Setup failed', "Couldn't change the files in your RPCS3 folder. Make sure RPCS3 is "
                                 f'closed and the folder is right, then try again.\n\nDetails: {e}')
            return
        self.cfg.update(rpcs3_dir=str(r.root), mode=self.mode.get(), crowd_fix=self.crowd.get(), face_fix=self.face.get(),
                        graphics=self.graphics.get(), picture=self.picture.get(), scale=self.scale.get())
        self.cfg.save()
        self.refresh()
        messagebox.showinfo('Done', 'RPCS3 is set up.\n\n'
                            + ('Next: start the server in tab 2, then ' if ip == '127.0.0.1' else 'Next: ')
                            + 'click Launch RPCS3, boot the game and go to Online → Game Rooms → Revival Room.\n\n'
                            'To accept a challenge, open the Quick Menu (SELECT).')

    def server_running(self):
        return bool(self.server and self.server.poll() is None)

    def refresh(self):
        hosting = self.mode.get() == 'host'
        if hosting:
            self.invite_btn.pack_forget()
            self.invite_label.config(text='')
        else:
            self.invite_btn.pack(side='left', before=self.invite_label)
            self.invite_label.config(text=f'Loaded: server at {self.cfg["invite_host"]}' if self.cfg.get('invite_host')
                                     else 'No invite loaded yet')
        set_up = ready = False
        r = s.Rpcs3(self.rpcs3_dir.get().strip()) if self.rpcs3_dir.get().strip() else None
        if not r or r.problem():
            text = 'Pick your RPCS3 folder.' if not r else r.problem()
        else:
            want_ip, want_ca = self.target()
            ca = s.installed_ca(r)
            server = s.game_config_server(r)
            where = 'your server' if server == '127.0.0.1' else server
            crowd, graphics, picture, scale = self.crowd.get(), self.graphics.get(), self.picture.get(), self.scale.get()
            # each row compares RPCS3's files with the options chosen above, so a changed option shows up here
            fixes = ' and '.join(n for n, on in (('crowd fix', crowd), ('face fix', self.face.get())) if on)
            rows = [(s.patches_status(r, crowd, self.face.get()),
                     'Patches installed' + (f' (with {fixes})' if fixes else ''), 'Patches'),
                    (s.game_config_status(r, graphics, picture, scale), f'Game settings applied ({picture}, {scale}%)',
                     'Game settings'),
                    (server is not None and server == want_ip, f'Connects to {where}', 'Server address'),
                    (ca is not None and isinstance(want_ca, bytes) and ca == want_ca, 'Server certificate trusted',
                     'Server certificate')]
            lines = [('✓  ' + done) if ok else ('○  ' + todo + ': needs Set up') for ok, done, todo in rows]
            set_up = all(ok for ok, _, _ in rows)
            if hosting:   # the most common first-session failure: everything set up but no server
                lines.append('✓  Server running' if self.server_running() else '○  Server not running: start it in tab 2')
            ready = set_up and (not hosting or self.server_running())
            head = ('Open the invite file your friend sent you, then click "Set up RPCS3":' if want_ip is None else
                    'Ready to play: click Launch RPCS3' if ready else
                    'Almost there: start the server in tab 2' if set_up else
                    'Click "Set up RPCS3" to apply:')
            text = head + '\n' + '\n'.join(lines)
        self.status.config(text=text)
        # highlight the next step: Set up until it's done, Launch once everything is ready
        self.setup_btn.config(style='TButton' if set_up else 'Accent.TButton')
        self.launch_btn.config(style='Accent.TButton' if ready else 'TButton')

    # ------------------------------------------------------------ host tab

    def host_tab(self, nb):
        f = ttk.Frame(nb, padding=16)
        f.columnconfigure(0, weight=1)
        f.rowconfigure(9, weight=1)
        h = ('', 11, 'bold')
        ttk.Label(f, text='1. Start the server', font=h).grid(row=0, column=0, sticky='w')
        bar = ttk.Frame(f)
        bar.grid(row=1, column=0, sticky='ew', pady=(6, 0))
        self.start_btn = ttk.Button(bar, text='Start server', style='Accent.TButton', command=self.start_server)
        self.start_btn.pack(side='left')
        self.stop_btn = ttk.Button(bar, text='Stop', command=self.stop_server, state='disabled')
        self.stop_btn.pack(side='left', padx=8)
        self.server_state = ttk.Label(bar, text='○  Stopped', style='Hint.TLabel')
        self.server_state.pack(side='left', padx=8)

        ttk.Label(f, text='2. Send your friend an invite', font=h).grid(row=2, column=0, sticky='w', pady=(18, 0))
        ttk.Label(f, text='Where is your friend?').grid(row=3, column=0, sticky='w', pady=(6, 0))
        self.where = tk.StringVar()
        self.where_btns = ttk.Frame(f)
        self.where_btns.grid(row=4, column=0, sticky='w')
        inv = ttk.Frame(f)
        inv.grid(row=5, column=0, sticky='w', pady=(8, 0))
        ttk.Button(inv, text='Save invite file…', command=self.save_invite).pack(side='left')
        self.where_hint = ttk.Label(f, style='Hint.TLabel', wraplength=580, justify='left')
        self.where_hint.grid(row=6, column=0, sticky='w', pady=(4, 0))
        ttk.Label(f, text='The invite holds your address and your server certificate (never your private keys).',
                  style='Hint.TLabel', wraplength=580, justify='left').grid(row=7, column=0, sticky='w')

        ttk.Label(f, text='3. Server activity', font=h).grid(row=8, column=0, sticky='w', pady=(18, 0))
        self.log = tk.Text(f, height=10, wrap='word', state='disabled', relief='flat', borderwidth=0,
                           background='#0b0b0b', foreground='#d8d8d8', padx=10, pady=8)   # terminal-like
        self.log.grid(row=9, column=0, sticky='nsew', pady=(4, 0))
        self.log.tag_configure('placeholder', foreground='#6e6e6e')
        self.write_log('Nothing yet. Start the server and activity shows up here.', 'placeholder')
        foot = ttk.Frame(f)
        foot.grid(row=10, column=0, sticky='ew', pady=(8, 0))
        ttk.Label(foot, text='If your firewall asks, allow network access.', style='Hint.TLabel').pack(side='left')
        link(foot, 'Open logs folder', s.data_dir().as_uri()).pack(side='right')
        self.show_addresses()
        return f

    def show_addresses(self):
        lan, ts = s.lan_ip(), s.tailscale_ip()
        self.ts_ip = ts
        for w in self.where_btns.winfo_children():
            w.destroy()
        choices = [(lan, f'Same home network ({lan})' if lan else 'Same home network (no network found)'),
                   (ts, f'Somewhere else, over Tailscale ({ts})' if ts else
                    'Somewhere else: install Tailscale first (see the Setup guide)')]
        for i, (ip, text) in enumerate(choices):
            ttk.Radiobutton(self.where_btns, text=text, variable=self.where, value=ip or f'none{i}',   # unselectable
                            state='normal' if ip else 'disabled',
                            command=self.where_changed).pack(anchor='w', pady=1)
        if self.where.get() not in (lan, ts) or not self.where.get():
            self.where.set(ts or lan or '')
        self.where_changed()

    def where_changed(self):
        ts = self.where.get() and self.where.get() == self.ts_ip
        self.where_hint.config(text='Your friend needs Tailscale too, in your tailnet: invite them, or share this '
                                    'computer with them from the Tailscale admin console.' if ts else '')

    def save_invite(self):
        ip = self.where.get()
        if not ip:
            messagebox.showerror('Invite', 'No network address found. Are you connected to a network?')
            return
        p = filedialog.asksaveasfilename(title='Save invite', defaultextension='.mlb16invite',
                                         initialfile='mlb16-invite.mlb16invite',
                                         filetypes=[('MLB16 invite', '*.mlb16invite')])
        if p:
            ca = (s.ensure_host_certs() / 'ca.pem').read_bytes()
            Path(p).write_text(s.make_invite(ip, ca), encoding='utf-8')
            self.write_log(f'invite saved for {ip}: {p}')
            messagebox.showinfo('Invite saved', f'Saved to:\n{p}\n\nSend this file to your friend (Discord, email, '
                                'anything). They open it in their launcher with "Open invite…", then click Set up RPCS3.')

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
        self.server_state.config(text='●  Running', style='Running.TLabel')
        self.write_log('Server starting…')
        self.refresh()

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
                    self.write_log('Server stopped.' if self.stopping else
                                   'The server stopped unexpectedly. Usually another copy is already running (another '
                                   f'launcher window, or server.py): close it and click Start server. (exit code {code})')
                    self.start_btn.config(state='normal')
                    self.stop_btn.config(state='disabled')
                    self.server_state.config(text='○  Stopped', style='Hint.TLabel')
                    self.refresh()
                    continue
                text = friendly(line)
                if text:
                    self.write_log(text)
        except queue.Empty:
            pass
        self.after(200, self.pump)

    def write_log(self, text, tag=None):
        self.log.config(state='normal')
        self.log.delete(*(self.log.tag_ranges('placeholder') or ('end', 'end')))
        self.log.insert('end', text + '\n', tag)
        self.log.see('end')
        self.log.config(state='disabled')

    def quit_app(self):
        if self.server_running() and not messagebox.askokcancel(
                'Quit', 'The server is running. Quitting stops it and ends any game in progress.'):
            return
        self.stop_server()
        self.destroy()


if __name__ == '__main__':
    if '--server' in sys.argv:
        run_server()
    else:
        App().mainloop()
