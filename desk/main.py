# -*- coding: utf-8 -*-
# ============================================================================
#  VOIDDESK v5.2 — pannello di controllo della suite Void per muOS
#  Estetica SPDW FACTORY: cyberpunk manga grezzo, megastruttura alla BLAME!
# ============================================================================
import math
import os
import random
import subprocess
import sys
import threading
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame          # noqa: E402
import evinput         # noqa: E402
import fbdisplay       # noqa: E402
import icons           # noqa: E402
import imgmount        # noqa: E402
import intro           # noqa: E402
import jsmap           # noqa: E402
import shell           # noqa: E402
import sysinfo         # noqa: E402

W, H = 640, 480
BG = (7, 8, 11)            # nero megastruttura
PANEL = (18, 20, 26)       # lastra scura
LINE = (34, 38, 47)        # nervature della struttura
INK = (2, 2, 4)            # china: piu' nero del fondo
FG = (233, 233, 226)       # bianco osso
DIM = (148, 150, 152)
FAINT = (100, 103, 110)
OK_G = (96, 225, 120)      # spunta: verde acceso
NO_R = (238, 62, 58)       # croce: rosso sangue
UNK = (110, 112, 120)
ACCENTS = {
    "ambra":   (255, 176, 46),
    "cremisi": (231, 54, 84),
    "ciano":   (74, 206, 224),
    "verde":   (112, 224, 122),
    "acciaio": (208, 214, 210),
}


# colore identitario di ogni ambiente nel selettore START SESSION:
# xfce = accento del tema; gli altri due cambiano combinazione col tema.
ENV_SECONDARY = {
    "ambra":   {"icewm": (74, 206, 224),  "lxde": (112, 224, 122)},
    "cremisi": {"icewm": (255, 176, 46),  "lxde": (74, 206, 224)},
    "ciano":   {"icewm": (231, 54, 84),   "lxde": (255, 176, 46)},
    "verde":   {"icewm": (74, 206, 224),  "lxde": (255, 176, 46)},
    "acciaio": {"icewm": (110, 195, 250), "lxde": (255, 176, 46)},
}
# maschere 16x16 dei marchi ambiente (bit alto = colonna sinistra)
ENV_GLYPHS = {
 "xfce": [0x07E0, 0x1FF8, 0x3FFC, 0x7FFE, 0x7FFE, 0xFFFF, 0xF3CF, 0xF3CF,
          0xFFFF, 0xFFFF, 0x7FFE, 0x799E, 0x3FFC, 0x1FF8, 0x07E0, 0x0000],
 "icewm": [0x03F0, 0x07E0, 0x0FC0, 0x1F80, 0x3FF8, 0x7FF0, 0x07E0, 0x0FC0,
           0x1F80, 0x3F00, 0x7E00, 0x7C00, 0x3800, 0x1800, 0x1000, 0x0000],
 "lxde": [0x0000, 0xC000, 0xF000, 0x7C00, 0x3F00, 0x1FC0, 0x0FF0, 0x07FC,
          0x07FF, 0x0FF0, 0x1F80, 0x3E00, 0x7800, 0xE000, 0x8000, 0x0000],
}
MUOS_APP_ROOTS = os.environ.get(
    "VD_MUOS_ROOTS",
    "/mnt/mmc/MUOS/application:/mnt/sdcard/MUOS/application").split(":")

ENVS = [
    ("xfce",  "DESKTOP XFCE",  "startxfce4"),
    ("icewm", "ICEWM // TURBO", "icewm"),
    ("lxde",  "LXDE // LIGHT",  "lxde-core lxterminal"),
]


def sel_tint(accent):
    """Fondo della riga selezionata: nero tinto con l'accento."""
    return tuple(min(255, BG[i] + accent[i] // 7) for i in range(3))

DATA = os.path.join(APP_DIR, "data")
LOG = os.path.join(DATA, "voiddesk.log")
FONT_PATH = os.path.join(APP_DIR, "assets", "DejaVuSans.ttf")

EXIT_XFCE_LAUNCH = 11
EXIT_XFCE_INSTALL = 12
EXIT_PKG_INSTALL = 13
EXIT_PKG_REMOVE = 14
EXIT_APT_UPDATE = 15
EXIT_MUOS_APP = 16

# ---------------------------------------------------------------------------
# Catalogo componenti: categorie -> voci
#   (nome, pacchetti apt, descrizione, percorsi-prova nel chroot)
# ---------------------------------------------------------------------------
CATEGORIES = [
 ("BASE / DRIVER", [
  ("Server X (Xorg)", "xserver-xorg-core", "il server grafico",
   "usr/bin/Xorg", "xorg"),
  ("Driver video fbdev", "xserver-xorg-video-fbdev", "uscita su framebuffer",
   "usr/lib/xorg/modules/drivers/fbdev_drv.so", "driver"),
  ("Driver input evdev", "xserver-xorg-input-evdev", "tasti e stick",
   "usr/lib/xorg/modules/input/evdev_drv.so", "gamepad"),
  ("startx / xinit", "xinit", "avvio della sessione", "usr/bin/startx",
   "start"),
  ("Utility X11", "x11-xserver-utils x11-utils", "xset, xrefresh, xdpyinfo",
   "usr/bin/xset", "gear"),
  ("D-Bus", "dbus dbus-x11", "comunicazione tra applicazioni",
   "usr/bin/dbus-daemon", "dbus"),
  ("Font DejaVu", "fonts-dejavu-core", "font di sistema",
   "usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "font"),
  ("Certificati CA", "ca-certificates", "connessioni https",
   "usr/sbin/update-ca-certificates", "cert"),
 ]),
 ("DESKTOP XFCE", [
  ("Sessione XFCE", "xfce4-session", "gestore di sessione",
   "usr/bin/startxfce4", "start"),
  ("Window manager", "xfwm4", "cornici e finestre", "usr/bin/xfwm4",
   "window"),
  ("Pannello", "xfce4-panel", "barra applicazioni", "usr/bin/xfce4-panel",
   "panel"),
  ("Scrivania", "xfdesktop4", "sfondo e icone", "usr/bin/xfdesktop",
   "desktop"),
  ("Impostazioni XFCE", "xfce4-settings", "aspetto, tastiera, mouse",
   "usr/bin/xfce4-settings-manager", "gear"),
  ("File manager", "thunar", "Thunar", "usr/bin/thunar", "folder"),
  ("Terminale", "xfce4-terminal", "terminale grafico",
   "usr/bin/xfce4-terminal", "terminal"),
  ("Task manager", "xfce4-taskmanager", "processi e memoria",
   "usr/bin/xfce4-taskmanager", "task"),
  ("Screenshot", "xfce4-screenshooter", "catture schermo",
   "usr/bin/xfce4-screenshooter", "camera"),
  ("Blocco note", "mousepad", "editor di testo", "usr/bin/mousepad", "text"),
 ]),
 ("AMBIENTI DESKTOP", [
  ("IceWM", "icewm",
   "window manager turbo: ~10MB di RAM", "usr/bin/icewm-session",
   "desktop"),
  ("LXDE", "lxde-core lxterminal",
   "desktop completo leggero (openbox+pcmanfm)", "usr/bin/startlxde",
   "desktop"),
 ]),
 ("INPUT / TASTIERA", [
  ("QJoyPad", "qjoypad", "gamepad -> mouse e tasti", "usr/bin/qjoypad",
   "gamepad"),
  ("Tastiera matchbox", "matchbox-keyboard",
   "tastiera virtuale (MENU la apre)", "usr/bin/matchbox-keyboard",
   "keyboard"),
  ("xdotool", "xdotool", "automazione finestre", "usr/bin/xdotool", "mouse"),
  ("Zenity", "zenity", "finestre di dialogo", "usr/bin/zenity", "dialog"),
 ]),
 ("PERIFERICHE", [
  ("Audio ALSA", "alsa-utils", "amixer, alsamixer, aplay", "usr/bin/amixer",
   "speaker"),
  ("PulseAudio + mixer", "pulseaudio pavucontrol",
   "server audio e mixer grafico", "usr/bin/pulseaudio", "mixer"),
  ("Bluetooth", "bluez blueman", "bluetoothctl + gestore grafico",
   "usr/bin/bluetoothctl", "bt"),
  ("WiFi (wpa_gui)", "wpagui", "reti wifi dal desktop", "usr/bin/wpa_gui",
   "wifi"),
  ("Dischi e USB", "gvfs gvfs-backends udisks2 thunar-volman",
   "automount chiavette in Thunar", "usr/sbin/udisksd", "disk"),
  ("Utility rete", "iproute2 iputils-ping wireless-tools",
   "ip, ping, iwconfig", "usr/bin/ping", "net"),
  ("NetworkManager", "network-manager network-manager-gnome",
   "gestione reti (puo' litigare con muOS)", "usr/sbin/NetworkManager",
   "wifi"),
 ]),
 ("BROWSER / RETE", [
  ("NetSurf", "netsurf-gtk", "browser leggerissimo (~20MB)",
   "usr/bin/netsurf-gtk", "globe"),
  ("Falkon", "falkon", "browser Qt completo (~350MB)", "usr/bin/falkon",
   "globe"),
  ("Dillo", "dillo", "browser minimale, velocissimo", "usr/bin/dillo",
   "globe"),
  ("Transmission", "transmission-gtk", "client torrent",
   "usr/bin/transmission-gtk", "download"),
  ("FileZilla", "filezilla", "trasferimento FTP/SFTP", "usr/bin/filezilla",
   "net"),
  ("Remmina", "remmina", "desktop remoto RDP/VNC", "usr/bin/remmina",
   "remote"),
 ]),
 ("MULTIMEDIA", [
  ("mpv", "mpv", "player video", "usr/bin/mpv", "video"),
  ("Audacious", "audacious", "player musicale leggero", "usr/bin/audacious",
   "music"),
  ("Ristretto", "ristretto", "visualizzatore immagini", "usr/bin/ristretto",
   "image"),
  ("Codec ffmpeg", "ffmpeg", "conversione e codec", "usr/bin/ffmpeg",
   "film"),
 ]),
 ("GRAFICA / UFFICIO", [
  ("mtPaint", "mtpaint", "disegno e ritocco leggero", "usr/bin/mtpaint",
   "paint"),
  ("GIMP", "gimp", "fotoritocco completo (PESANTE)", "usr/bin/gimp", "paint"),
  ("AbiWord", "abiword", "videoscrittura", "usr/bin/abiword", "doc"),
  ("Gnumeric", "gnumeric", "fogli di calcolo", "usr/bin/gnumeric", "sheet"),
  ("Lettore PDF", "xpdf", "visualizzatore PDF", "usr/bin/xpdf", "pdf"),
  ("Galculator", "galculator", "calcolatrice", "usr/bin/galculator", "calc"),
 ]),
 ("RETE / SVILUPPO", [
  ("Syncthing", "syncthing", "sincronizza file (muOS ne ha uno suo)",
   "usr/bin/syncthing", "download"),
  ("Tailscale", "!curl -fsSL https://tailscale.com/install.sh | sh",
   "VPN personale (script ufficiale)", "usr/bin/tailscale", "net"),
  ("Barrier", "barrier", "mouse e tastiera dal PC via rete",
   "usr/bin/barrier", "mouse"),
  ("KDE Connect", "kdeconnect", "telefono <-> desktop (PESANTE)",
   "usr/bin/kdeconnect-app", "remote"),
  ("Server SSH", "openssh-server",
   "entra nel desktop dal PC (porta 22)", "usr/sbin/sshd", "net"),
  ("Client SSH", "openssh-client", "ssh, scp verso altri PC",
   "usr/bin/ssh", "net"),
  ("VNC (x11vnc)", "x11vnc", "vedi il desktop dal PC", "usr/bin/x11vnc",
   "remote"),
  ("ADB", "adb", "android debug bridge", "usr/bin/adb", "disk"),
  ("Python 3 completo", "python3-full python3-pip python3-venv",
   "interprete, pip, venv", "usr/bin/pip3", "python"),
  ("Compilatore C/C++", "build-essential", "gcc, make (PESANTE)",
   "usr/bin/gcc", "gear"),
  ("rsync", "rsync", "sincronizza cartelle", "usr/bin/rsync", "download"),
  ("tmux", "tmux", "sessioni terminale persistenti", "usr/bin/tmux",
   "terminal"),
  ("Samba client", "cifs-utils smbclient", "cartelle di rete Windows",
   "usr/bin/smbclient", "folder"),
 ]),
 ("STRUMENTI / CLI", [
  ("Xarchiver", "xarchiver", "archivi zip/tar/7z", "usr/bin/xarchiver",
   "archive"),
  ("Supporto archivi", "zip unzip p7zip-full", "zip, 7z da terminale",
   "usr/bin/7z", "archive"),
  ("htop", "htop", "monitor processi da terminale", "usr/bin/htop",
   "monitor"),
  ("Midnight Commander", "mc", "file manager da terminale", "usr/bin/mc",
   "folder"),
  ("Git", "git", "controllo versione", "usr/bin/git", "git"),
  ("nano", "nano", "editor da terminale", "usr/bin/nano", "edit"),
  ("wget / curl", "wget curl", "download da terminale", "usr/bin/wget",
   "download"),
  ("Info sistema", "neofetch lshw", "neofetch, lshw", "usr/bin/neofetch",
   "info"),
 ]),
]

# ---------------------------------------------------------------------------
# Avvio al boot: SOLO vere applicazioni. Sessione, driver, input e servizi
# (startxfce4, Xorg, qjoypad, matchbox, dbus, pulseaudio, bluetooth...)
# partono gia' da soli: metterli qui li fa partire DOPPI e sfascia il
# desktop (era il bug "le app non si avviano piu'", terminale incluso).
# ---------------------------------------------------------------------------
AUTOSTART_OK = {
    "File manager", "Terminale", "Task manager", "Blocco note",
    "NetSurf", "Falkon", "Dillo", "Transmission", "FileZilla", "Remmina",
    "Audacious", "Ristretto",
    "mtPaint", "GIMP", "AbiWord", "Gnumeric", "Lettore PDF", "Galculator",
    "Syncthing", "Barrier", "KDE Connect", "Server SSH", "VNC (x11vnc)",
    "Xarchiver",
}
AUTOSTART_EXEC = {i[3].split()[0].split("/")[-1]
                  for _c, items in CATEGORIES for i in items
                  if i[0] in AUTOSTART_OK}

# I numeri "Button N" di QJoyPad dipendono dal driver joydev del kernel:
# li calcoliamo leggendo il pad, non tirando a indovinare (jsmap).
KNOWN_NAMES = {304: "A", 305: "B", 306: "Y", 307: "X", 308: "L1",
               309: "R1", 310: "SELECT", 311: "START", 312: "MENU",
               314: "L2", 315: "R2"}
EXTRA_NAMES = ["L3", "R3"]
# tasti volume: sono KEY_ non BTN_, quindi QJoyPad non li vede mai.
# Restano usabili solo dalle funzioni gestite da VoidDesk (es. tastiera).
VOLUME_KEYS = {114: "VOL-", 115: "VOL+"}

PAD_PATH, PAD_KEYS = jsmap.find_pad()
EV2QJ = jsmap.ev_to_qj(PAD_KEYS) if PAD_KEYS else {}


def _build_names():
    out = dict(VOLUME_KEYS)
    for c in sorted(PAD_KEYS or ()):
        if 256 <= c <= 319:
            out[c] = KNOWN_NAMES.get(c)
    extra = [c for c in sorted(PAD_KEYS or ())
             if 256 <= c <= 319 and c not in KNOWN_NAMES]
    for i, c in enumerate(extra):
        out[c] = EXTRA_NAMES[i] if i < len(EXTRA_NAMES) else "B%d" % c
    return {k: v for k, v in out.items() if v}


EV2NAME = _build_names() or dict(KNOWN_NAMES)
NAME2EV = {v: k for k, v in EV2NAME.items()}


def ev_of(name):
    return NAME2EV.get(name)


# funzioni rimappabili: chiave -> (etichetta it, etichetta en, icona,
#                                  azione QJoyPad, default [evdev])
FUNCS_DEF = [
    ("click_l", "Click sinistro", "Left click", "mouse", "mouse 1",
     ["A", "L3"]),
    ("click_r", "Click destro", "Right click", "mouse", "mouse 3",
     ["X", "R3"]),
    ("click_m", "Click centrale", "Middle click", "mouse", "mouse 2", ["Y"]),
    ("wheel_up", "Rotella su", "Wheel up", "mouse", "mouse 4", ["R1"]),
    ("wheel_dn", "Rotella giu'", "Wheel down", "mouse", "mouse 5", ["L1"]),
    ("back", "Indietro", "Back", "globe", "key 166", ["B"]),
    ("enter", "Invio", "Enter", "keyboard", "key 36", ["START"]),
    ("esc", "Esc", "Esc", "keyboard", "key 9", ["SELECT"]),
    ("kbd", "Mostra/nascondi tastiera", "Toggle keyboard", "keyboard",
     "__kbd__", ["MENU"]),
]
# risolvo i nomi in codici evdev realmente presenti sul pad
FUNCS = [(k, it, en, ic, act,
          [ev_of(n) for n in names if ev_of(n) is not None])
         for k, it, en, ic, act, names in FUNCS_DEF]
FUNC_BY_KEY = {f[0]: f for f in FUNCS}


def default_map():
    return {f[0]: list(f[5]) for f in FUNCS}


def write_custom_layout(cfg, path):
    """Genera il .lyt di QJoyPad dalla mappatura personalizzata."""
    m = cfg.get("map") or default_map()
    stick = cfg.get("mouse_stick", "sinistro")
    out = ["# QJoyPad 4.3 Layout File", "# VOIDDESK - mappatura utente",
           "Joystick 1 {"]
    if stick == "sinistro":
        out += ["\tAxis 1: gradient, maxSpeed 3, mouse+h",
                "\tAxis 2: gradient, maxSpeed 3, mouse+v",
                "\tAxis 3: gradient, +key 114, -key 113",
                "\tAxis 4: gradient, +key 117, -key 112"]
    else:
        out += ["\tAxis 3: gradient, maxSpeed 3, mouse+h",
                "\tAxis 4: gradient, maxSpeed 3, mouse+v",
                "\tAxis 1: gradient, +key 114, -key 113",
                "\tAxis 2: gradient, +key 117, -key 112"]
    out += ["\tAxis 5: +key 114, -key 113", "\tAxis 6: +key 116, -key 111"]
    learned = cfg.get("qj_map", {})
    for key, evs in m.items():
        f = FUNC_BY_KEY.get(key)
        if not f or f[4] == "__kbd__":      # la tastiera la gestisce il watcher
            continue
        for ev in evs:
            qj = learned.get(str(ev)) or EV2QJ.get(int(ev))
            if qj:
                out.append("\tButton %d: %s" % (qj, f[4]))
    out.append("}")
    try:
        with open(path, "w") as fh:
            fh.write("\n".join(out) + "\n")
        return True
    except OSError:
        return False


# traduzioni di categorie, descrizioni del catalogo e valori ricorrenti
CAT_EN = {
    "AMBIENTI DESKTOP": "DESKTOP ENVIRONMENTS",
    "BASE / DRIVER": "BASE / DRIVERS", "DESKTOP XFCE": "XFCE DESKTOP",
    "INPUT / TASTIERA": "INPUT / KEYBOARD", "PERIFERICHE": "DEVICES",
    "BROWSER / RETE": "BROWSER / NETWORK", "MULTIMEDIA": "MULTIMEDIA",
    "GRAFICA / UFFICIO": "GRAPHICS / OFFICE", "STRUMENTI / CLI": "TOOLS / CLI",
    "RETE / SVILUPPO": "NETWORK / DEV",
}
DESC_EN = {
    "il server grafico": "the graphics server",
    "uscita su framebuffer": "framebuffer output",
    "tasti e stick": "buttons and sticks",
    "avvio della sessione": "session startup",
    "xset, xrefresh, xdpyinfo": "xset, xrefresh, xdpyinfo",
    "comunicazione tra applicazioni": "inter-app communication",
    "font di sistema": "system fonts",
    "connessioni https": "https connections",
    "gestore di sessione": "session manager",
    "cornici e finestre": "window frames",
    "barra applicazioni": "taskbar",
    "sfondo e icone": "wallpaper and icons",
    "aspetto, tastiera, mouse": "appearance, keyboard, mouse",
    "Thunar": "Thunar",
    "terminale grafico": "graphical terminal",
    "processi e memoria": "processes and memory",
    "catture schermo": "screen captures",
    "editor di testo": "text editor",
    "gamepad -> mouse e tasti": "gamepad -> mouse and keys",
    "tastiera virtuale a schermo": "on-screen keyboard",
    "serve all'auto-comparsa tastiera": "needed for keyboard auto-show",
    "automazione finestre": "window automation",
    "finestre di dialogo": "dialog windows",
    "amixer, alsamixer, aplay": "amixer, alsamixer, aplay",
    "server audio e mixer grafico": "sound server and graphical mixer",
    "bluetoothctl + gestore grafico": "bluetoothctl + graphical manager",
    "reti wifi dal desktop": "wifi networks from the desktop",
    "automount chiavette in Thunar": "USB automount in Thunar",
    "ip, ping, iwconfig": "ip, ping, iwconfig",
    "browser leggerissimo (~20MB)": "ultra-light browser (~20MB)",
    "browser Qt completo (~350MB)": "full Qt browser (~350MB)",
    "browser minimale, velocissimo": "minimal, very fast browser",
    "client torrent": "torrent client",
    "trasferimento FTP/SFTP": "FTP/SFTP transfers",
    "desktop remoto RDP/VNC": "RDP/VNC remote desktop",
    "player video": "video player",
    "player musicale leggero": "light music player",
    "visualizzatore immagini": "image viewer",
    "conversione e codec": "conversion and codecs",
    "disegno e ritocco leggero": "light drawing and editing",
    "fotoritocco completo (PESANTE)": "full photo editor (HEAVY)",
    "videoscrittura": "word processor",
    "fogli di calcolo": "spreadsheets",
    "visualizzatore PDF": "PDF viewer",
    "calcolatrice": "calculator",
    "archivi zip/tar/7z": "zip/tar/7z archives",
    "zip, 7z da terminale": "zip, 7z from the terminal",
    "monitor processi da terminale": "process monitor for the terminal",
    "file manager da terminale": "terminal file manager",
    "controllo versione": "version control",
    "interprete e pip": "interpreter and pip",
    "editor da terminale": "terminal editor",
    "download da terminale": "downloads from the terminal",
    "neofetch, lshw": "neofetch, lshw",
    "tastiera virtuale (MENU la apre)": "on-screen keyboard (MENU opens it)",
    "gestione reti (puo' litigare con muOS)":
        "network manager (may fight with muOS)",
    "entra nel desktop dal PC (porta 22)":
        "log into the desktop from your PC (port 22)",
    "ssh, scp verso altri PC": "ssh, scp to other machines",
    "vedi il desktop dal PC": "see the desktop from your PC",
    "android debug bridge": "android debug bridge",
    "interprete, pip, venv": "interpreter, pip, venv",
    "gcc, make (PESANTE)": "gcc, make (HEAVY)",
    "sincronizza cartelle": "sync folders",
    "sessioni terminale persistenti": "persistent terminal sessions",
    "cartelle di rete Windows": "Windows network shares",
    "sincronizza file (muOS ne ha uno suo)":
        "file sync (muOS has its own instance)",
    "VPN personale (script ufficiale)": "personal VPN (official script)",
    "mouse e tastiera dal PC via rete": "mouse and keyboard from your PC",
    "telefono <-> desktop (PESANTE)": "phone <-> desktop (HEAVY)",
}
VAL_EN = {
    "sinistro": "left stick", "classico": "right stick", "custom": "custom",
    "destro": "right", "ambra": "amber", "cremisi": "crimson",
    "ciano": "cyan", "verde": "green", "acciaio": "steel",
    "installato": "installed", "non installato": "not installed",
    "assente": "missing", "attivo": "on", "spento": "off",
    "non connesso": "not connected", "n/d": "n/a",
    "tutte presenti": "all present", "non raggiungibile": "unreachable",
    "curl assente": "curl missing",
}
STAT_EN = {
    "SISTEMA": "SYSTEM", "MEMORIA": "MEMORY", "ARCHIVIAZIONE": "STORAGE",
    "RETE": "NETWORK", "AUDIO": "AUDIO", "DESKTOP XFCE": "XFCE DESKTOP",
    "RUNTIME": "RUNTIME", "KERNEL": "KERNEL", "ACCESO DA": "UPTIME",
    "TEMPERATURA": "TEMPERATURE", "RAM": "RAM", "SD1 (MMC)": "SD1 (MMC)",
    "SD2 (SDCARD)": "SD2 (SDCARD)", "IMMAGINE XFCE": "XFCE IMAGE",
    "WIFI": "WI-FI", "SEGNALE": "SIGNAL", "INDIRIZZO IP": "IP ADDRESS",
    "BLUETOOTH": "BLUETOOTH", "INTERNET": "INTERNET", "VOLUME": "VOLUME",
    "STATO": "STATUS", "ULTIMA SESSIONE": "LAST SESSION",
    "CONTROLLER": "CONTROLLER", "INTERFACCIA": "INTERFACE",
    "connesso": "connected", "PYTHON": "PYTHON", "PYGAME": "PYGAME",
    "DIPENDENZE": "DEPENDENCIES", "VOID SUITE": "VOID SUITE",
    "PIATTAFORMA": "PLATFORM", "COME FUNZIONA": "HOW IT WORKS",
    "CREDITI": "CREDITS", "TARGET": "TARGET", "OS": "OS",
    "DESKTOP": "DESKTOP", "UI": "UI",
}

COMP_MENU = [
    ("install", "pkg", "Installa / Reinstalla software",
     "Install / reinstall software",
     "catalogo con stato di ogni componente",
     "catalogue with per-component status"),
    ("remove", "archive", "Disinstalla software", "Uninstall software",
     "libera spazio rimuovendo pacchetti",
     "free space by removing packages"),
    ("autostart", "start", "Avvio al boot", "Startup apps",
     "quali programmi partono con XFCE",
     "which programs start with XFCE"),
    ("update", "download", "Aggiorna sistema", "Update system",
     "apt update + upgrade nel chroot",
     "apt update + upgrade in the chroot"),
    ("clean", "task", "Pulisci cache apt", "Clean apt cache",
     "recupera spazio nell'immagine", "reclaim space in the image"),
    ("shell", "terminal", "Terminal shell", "Terminal shell",
     "terminale con tastiera a schermo",
     "terminal with on-screen keyboard"),
]

TR = {
 "it": {
  "xfce_run": "▶  DESKTOP XFCE", "xfce_inst": "▶  INSTALLA DESKTOP XFCE",
  "xfce_run_s": "avvia il desktop a schermo intero",
  "xfce_inst_s": "~400MB via WiFi, 10-20 minuti",
  "comp": "◈  COMPONENTI E PROGRAMMI",
  "comp_s": "driver, desktop, browser, tool: stato e installazione",
  "info": "▤  VOID STATS",
  "info_s": "sistema, memoria, rete, audio, desktop",
  "opts": "⚒  OPZIONI", "opts_s": "tema, lingua, controller, avvio",
  "logs": "≡  LOGS & ABOUT", "logs_s": "diari di bordo e info sul progetto",
  "quit": "◉  ESCI", "quit_s": "torna a muOS",
  "open": "apri", "back": "indietro", "exit": "esci", "install": "installa",
  "change": "cambia", "row": "riga", "page": "pagina", "sel": "seleziona",
  "all": "tutti/nessuno", "inst_sel": "installa selezione",
  "title_comp": "COMPONENTI E PROGRAMMI", "title_info": "VOID STATS",
  "title_logs": "LOGS & ABOUT", "title_opts": "OPZIONI",
  "checking": "controllo in corso...",
  "need_xfce": "Prima installa il desktop XFCE (voce in alto nel menu).",
  "opt_theme": "Tema colore", "opt_lang": "Lingua",
  "opt_ctrl": "Profilo controller", "opt_batt": "Batteria nell'header",
  "opt_intro": "Sigla d'avvio",
  "sess": "▶ START SESSION",
  "sess_s": "scegli e avvia l'ambiente desktop",
  "e_active": "ATTIVO", "e_inst": "installato",
  "e_missing": "non installato - A: installa",
  "e_base": "richiede la base (~400MB) - A: installa tutto",
  "e_launch": "A: avvia", "sess_a": "avvia / installa",
  "mapps": "▣ MUOS APPS", "mapps_s": "le app di muOS, dentro Void",
  "mapps_t": "MUOS APPS", "mapps_none": "nessuna app in MUOS/application",
  "mapps_scan": "scansione e sistemazione glyph...",
  "mapps_go": "avvia", "mapps_r1": "glyph+scan",
  "opt_fx": "Interferenze video",
  "opt_sfx": "Suoni interfaccia",
  "opt_boost": "Void Boost (swap, cpu)",
  "yes": "si'", "no": "no",
  "ho_xfce": "AVVIO DESKTOP XFCE...",
  "ho_inst": "INSTALLAZIONE DESKTOP XFCE...",
  "ho_pkg": "PASSO ALL'INSTALLATORE...",
  "ho_rm": "PASSO AL DISINSTALLATORE...",
  "ho_update": "AGGIORNAMENTO SISTEMA...",
  "cleaning": "pulizia della cache apt...",
  "no_space": "Solo %s liberi nell'immagine XFCE.",
  "no_space_s": "Usa 'Pulisci cache apt' o disinstalla qualcosa.",
  "guide": "GUIDA RAPIDA", "guide_s": "comandi del menu e del desktop",
  "k_ud": "SU/GIU", "k_lr": "SX/DX",
  "free": "liberi: %s",
  "n_sel": "%d selezionati", "mounting": "leggo lo stato dei componenti...",
  "about": "INFO SUL PROGETTO", "about_s": "suite Void, piattaforma, crediti",
  "title_compmenu": "COMPONENTI E PROGRAMMI", "refresh": "aggiorna",
  "title_remove": "DISINSTALLA SOFTWARE", "title_auto": "AVVIO AL BOOT",
  "remove_btn": "disinstalla", "auto_on": "all'avvio", "auto_off": "no",
  "not_inst": "non installato", "sel_none": "nessuna voce selezionata",
  "no_base": "I componenti base del desktop non si possono rimuovere:",
  "confirm_rm": "Disinstallo %d componenti?", "yes_a": "A = si'",
  "no_b": "B = annulla", "shell_hint": "SELECT esce",
  "opt_map": "Mappatura tasti", "title_map": "MAPPATURA TASTI",
  "map_stick": "Mouse sullo stick", "press": "PREMI IL TASTO DA ASSEGNARE A:",
  "press_s": "attendi 5 secondi per annullare",
  "used_by": "Il tasto %s e' gia' usato da: %s",
  "swap_q": "A = scambia le due funzioni     B = annulla",
  "assign": "assegna", "reset": "ripristina", "reset_all": "tutti default",
  "none": "(nessuno)",
 },
 "en": {
  "xfce_run": "▶  XFCE DESKTOP", "xfce_inst": "▶  INSTALL XFCE DESKTOP",
  "xfce_run_s": "launch the full-screen Linux desktop",
  "xfce_inst_s": "about 400MB over Wi-Fi, 10-20 minutes",
  "comp": "◈  COMPONENTS & APPS",
  "comp_s": "drivers, desktop, browsers, tools: status and install",
  "info": "▤  VOID STATS",
  "info_s": "system, memory, network, audio, desktop",
  "opts": "⚒  SETTINGS", "opts_s": "theme, language, controller, startup",
  "logs": "≡  LOGS & ABOUT", "logs_s": "log files and project info",
  "quit": "◉  EXIT", "quit_s": "back to muOS",
  "open": "open", "back": "back", "exit": "exit", "install": "install",
  "change": "change", "row": "line", "page": "scroll", "sel": "select",
  "all": "all / none", "inst_sel": "install selection",
  "title_comp": "COMPONENTS & APPS", "title_info": "VOID STATS",
  "title_logs": "LOGS & ABOUT", "title_opts": "SETTINGS",
  "checking": "checking...",
  "need_xfce": "Install the XFCE desktop first (top menu entry).",
  "opt_theme": "Colour theme", "opt_lang": "Language",
  "opt_ctrl": "Controller profile", "opt_batt": "Status bar icons",
  "opt_intro": "Intro animation",
  "sess": "▶ START SESSION",
  "sess_s": "choose and launch a desktop",
  "e_active": "ACTIVE", "e_inst": "installed",
  "e_missing": "not installed - A: install",
  "e_base": "needs the base (~400MB) - A: install everything",
  "e_launch": "A: launch", "sess_a": "launch / install",
  "mapps": "▣ MUOS APPS", "mapps_s": "muOS apps, inside Void",
  "mapps_t": "MUOS APPS", "mapps_none": "no apps in MUOS/application",
  "mapps_scan": "scanning and fixing glyphs...",
  "mapps_go": "launch", "mapps_r1": "glyph+scan",
  "opt_fx": "Video interference",
  "opt_sfx": "UI sounds",
  "opt_boost": "Void Boost (swap, cpu)",
  "yes": "on", "no": "off",
  "ho_xfce": "STARTING XFCE DESKTOP...",
  "ho_inst": "INSTALLING XFCE DESKTOP...",
  "ho_pkg": "HANDING OFF TO INSTALLER...",
  "ho_rm": "HANDING OFF TO UNINSTALLER...",
  "ho_update": "UPDATING SYSTEM...",
  "cleaning": "cleaning the apt cache...",
  "no_space": "Only %s free inside the XFCE image.",
  "no_space_s": "Use 'Clean apt cache' or uninstall something.",
  "guide": "QUICK GUIDE", "guide_s": "menu and desktop controls",
  "k_ud": "UP/DN", "k_lr": "LT/RT",
  "free": "free: %s",
  "n_sel": "%d selected", "mounting": "reading component status...",
  "opt_map": "Button mapping", "title_map": "BUTTON MAPPING",
  "map_stick": "Mouse on stick", "press": "PRESS THE BUTTON TO ASSIGN TO:",
  "press_s": "wait 5 seconds to cancel",
  "used_by": "Button %s is already assigned to: %s",
  "swap_q": "A = swap the two functions     B = cancel",
  "assign": "assign", "reset": "restore default", "reset_all": "reset all",
  "none": "(none)",
  "about": "ABOUT THE PROJECT", "about_s": "Void suite, platform, credits",
  "title_compmenu": "COMPONENTS & APPS", "refresh": "refresh",
  "title_remove": "UNINSTALL SOFTWARE", "title_auto": "STARTUP APPS",
  "remove_btn": "uninstall", "auto_on": "at startup", "auto_off": "no",
  "not_inst": "not installed", "sel_none": "nothing selected",
  "no_base": "Core desktop components cannot be removed:",
  "confirm_rm": "Uninstall %d components?", "yes_a": "A = yes",
  "no_b": "B = cancel", "shell_hint": "SELECT quits",
 },

}


def font(size):
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.Font(None, size)


def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return "%dB" % n if u == "B" else "%.1f%s" % (n, u)
        n /= 1024.0


def disk_free(path):
    try:
        st = os.statvfs(path)
        return st.f_bavail * st.f_frsize, st.f_blocks * st.f_frsize
    except OSError:
        return None, None


def battery():
    base = "/sys/class/power_supply"
    try:
        for n in os.listdir(base):
            cap = os.path.join(base, n, "capacity")
            if os.path.exists(cap):
                return "%s%%" % open(cap).read().strip()
    except OSError:
        pass
    return "n/d"


bt_on = sysinfo.bt_status
volume_pct = sysinfo.volume
batt_state = sysinfo.battery


def net_test():
    try:
        rc = subprocess.call(["curl", "-sI", "--max-time", "5",
                              "https://ports.ubuntu.com"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return "OK" if rc == 0 else "non raggiungibile"
    except OSError:
        return "curl assente"


def load_cfg():
    import json
    try:
        with open(os.path.join(DATA, "desk_config.json")) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cfg(cfg):
    import json
    try:
        os.makedirs(DATA, exist_ok=True)
        with open(os.path.join(DATA, "desk_config.json"), "w") as f:
            json.dump(cfg, f, indent=1)
    except OSError:
        pass


def mounted(p):
    try:
        return (" %s " % os.path.abspath(p)) in open("/proc/mounts").read()
    except OSError:
        return False


class App(object):
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        self.surface = pygame.display.set_mode((W, H))
        if not fbdisplay.attach(self.surface):
            print("fbdisplay non disponibile")
        self.cfg = load_cfg()
        self.lang = self.cfg.get("lang", "it")
        self.accent = ACCENTS.get(self.cfg.get("theme", "ambra"),
                                  ACCENTS["ambra"])
        self.sel_bg = sel_tint(self.accent)
        self.bg_img = None
        self.fx_img = None
        self.stripe_img = None
        self.build_style()
        self.trans = None
        self.prev_frame = None
        self.last_sel_rect = None
        self.env_sel = 0
        self.mapps = []
        self.mapp_sel = 0
        self.mapp_icons = {}
        self.sfx = self.build_sfx()
        self.busy_label = ""
        self.busy_t0 = 0.0
        self.img_free = None
        self.img_total = None
        self.f_big = font(26)
        self.f_med = font(19)
        self.f_small = font(15)
        self.f_tiny = font(13)
        self.clock = pygame.time.Clock()
        self.running = True
        self.exit_code = 0
        self.stack = ["home"]
        self.sel = 0
        self.sel_log = 0
        self.opt_sel = 0
        self.scroll = 0
        self.log_lines = []
        self.info_lines = None
        self._stat = ({}, 0.0)
        self._dpad_t = 0.0
        self.map_sel = 0
        self.comp_sel = 0
        self.mode = "install"
        self.js_fd = None
        self.capture_t = 0.0
        self.pending = None
        self.rows = []          # righe del gestore componenti
        self.row_sel = 0
        self.marked = set()     # indici selezionati per l'installazione
        self.status = {}        # nome -> True/False/None
        self.logs = [
            ("__about__", ""),
            ("__guide__", ""),
            ("voiddesk.log", LOG),
            ("xfce_session.log", os.path.join(DATA, "xfce_session.log")),
            ("vd_hotkey.log", os.path.join(DATA, "vd_hotkey.log")),
            ("voidcast.log", os.path.join(os.path.dirname(APP_DIR),
                                          "VoidCast", "data",
                                          "voidcast.log")),
            ("mpv.log", os.path.join(os.path.dirname(APP_DIR), "VoidCast",
                                     "data", "mpv.log")),
        ]
        evinput.start()
        self.rebuild_menu()
        if self.cfg.get("intro", True) and \
                os.environ.get("VOIDDESK_NOINTRO") != "1":
            try:
                self.play_intro()
            except Exception as e:
                import traceback
                sys.stderr.write("intro non riuscita: %s\n" % e)
                traceback.print_exc(file=sys.stderr)
        # avviso il loader di consegna (vd_loader) che il menu e' a schermo
        try:
            open("/tmp/.vd_menu_up", "w").close()
        except OSError:
            pass
        # l'avvio automatico di XFCE non esiste piu': pulisco i residui
        self.cfg.pop("auto_xfce", None)
        # bonifica avvio-al-boot: in v4.4 ci si poteva mettere pezzi di
        # sessione; li tolgo dalla config cosi' al prossimo avvio di XFCE
        # i .desktop doppi spariscono e il desktop torna sano.
        a0 = self.cfg.get("autostart") or []
        e0 = self.cfg.get("autostart_exec") or []
        a1 = sorted(n for n in a0 if n in AUTOSTART_OK)
        e1 = sorted(e for e in e0 if e in AUTOSTART_EXEC)
        if a1 != sorted(a0) or e1 != sorted(e0):
            self.cfg["autostart"], self.cfg["autostart_exec"] = a1, e1
            save_cfg(self.cfg)
        try:
            os.remove(os.path.join(DATA, ".autolaunch"))
        except OSError:
            pass

    # ---------------------------------------------------------------- i18n
    def t(self, k):
        return TR.get(self.lang, TR["it"]).get(k, k)

    def tx(self, table, txt):
        """Traduce una stringa di dato/etichetta se la lingua e' inglese."""
        if self.lang != "en" or not txt:
            return txt
        return table.get(txt, txt)

    def rebuild_menu(self):
        xfce_ok = os.path.exists(os.path.join(DATA, ".xfce_ready"))
        t = self.t
        self.menu = [
            (t("sess"), t("sess_s")),
            (t("comp"), t("comp_s")),
            (t("mapps"), t("mapps_s")),
            (t("info"), t("info_s")),
            (t("opts"), t("opts_s")),
            (t("logs"), t("logs_s")),
            (t("quit"), t("quit_s")),
        ]

    # ---------------------------------------------------- stile SPDW/BLAME!
    def build_style(self):
        """Precalcola sfondo e overlay: costano una volta sola, non a frame.
        Megastruttura: nervature verticali, condotti, tacche hazard, sporco
        di china. Overlay: scanline + vignettatura + grana, tutto in una
        Surface sola da bliitare a fine frame."""
        rnd = random.Random(0xB1A)          # fisso: la struttura non balla
        bg = pygame.Surface((W, H))
        bg.fill(BG)
        # nervature verticali della megastruttura
        for gx in range(0, W + 40, 64):
            pygame.draw.line(bg, LINE, (gx, 0), (gx - 28, H), 1)
        # condotti orizzontali (doppia linea = tubo)
        for gy in (118, 296, 430):
            pygame.draw.line(bg, LINE, (0, gy), (W, gy), 1)
            pygame.draw.line(bg, INK, (0, gy + 2), (W, gy + 2), 1)
        # lastre piu' scure, come tavole inchiostrate
        for _ in range(5):
            rx = rnd.randrange(0, W - 120)
            ry = rnd.randrange(52, H - 90)
            rw = rnd.randrange(90, 240)
            rh = rnd.randrange(40, 110)
            pygame.draw.rect(bg, INK, (rx, ry, rw, rh))
            pygame.draw.rect(bg, LINE, (rx, ry, rw, rh), 1)
        # sporco di china: puntinato rado
        for _ in range(420):
            x = rnd.randrange(W)
            y = rnd.randrange(H)
            bg.set_at((x, y), INK if rnd.random() < 0.7 else LINE)
        # tacche hazard sul bordo destro
        for hy in range(60, H - 40, 26):
            pygame.draw.line(bg, self.accent, (W - 4, hy), (W - 1, hy + 7), 2)
        self.bg_img = bg
        # overlay: scanline + vignetta + grana (una Surface, un blit a frame)
        fx = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 3):
            pygame.draw.line(fx, (0, 0, 0, 26), (0, y), (W, y))
        steps, th = 7, 9
        for i in range(steps):
            a = int(88 * ((steps - i) / float(steps)) ** 2.4)
            pygame.draw.rect(fx, (0, 0, 0, a),
                             (i * th, i * th, W - 2 * i * th, H - 2 * i * th),
                             th)
        for _ in range(260):
            fx.set_at((rnd.randrange(W), rnd.randrange(H)),
                      (255, 255, 255, rnd.randrange(6, 16)))
        self.fx_img = fx
        # barra hazard della selezione: strisce diagonali accento/nero
        st = pygame.Surface((6, 24))
        st.fill(INK)
        for d in range(-24, 24, 8):
            pygame.draw.line(st, self.accent, (d, 24), (d + 24, 0), 3)
        self.stripe_img = st
        self.sel_bg = sel_tint(self.accent)

    def build_sfx(self):
        """Suoni UI sintetizzati al volo: blip di apertura, ritorno,
        movimento e scatto d'aggancio. Zero asset; se l'audio manca,
        silenzio e pace."""
        try:
            pygame.mixer.init(22050, -16, 1, 256)
        except pygame.error:
            return None

        def tone(f0, f1, ms, vol=0.30, noise=0.0):
            n = int(22050 * ms / 1000)
            buf = bytearray()
            ph = 0.0
            rnd = random.Random(3)
            for i in range(n):
                t = i / float(n)
                ph += 2 * math.pi * (f0 + (f1 - f0) * t) / 22050
                v = math.sin(ph)
                if noise:
                    v = v * (1 - noise) + noise * (rnd.random() * 2 - 1)
                env = min(1.0, i / 40.0) * (1 - t) ** 1.6
                smp = int(vol * env * 32767 * v)
                buf += smp.to_bytes(2, "little", signed=True)
            return pygame.mixer.Sound(buffer=bytes(buf))
        try:
            return {"open": tone(420, 980, 70),
                    "back": tone(760, 320, 60),
                    "move": tone(1240, 1240, 16, 0.16),
                    "snap": tone(190, 130, 45, 0.34, 0.55)}
        except pygame.error:
            return None

    def play(self, name):
        if self.sfx and self.cfg.get("sfx", True):
            try:
                self.sfx[name].play()
            except (KeyError, pygame.error):
                pass

    def push(self, state, color=None):
        """Apre uno stato come una finestra di un OS cyberpunk: blip,
        cattura del frame corrente, esplosione dal rettangolo selezionato."""
        self.play("open")
        self.prev_frame = self.surface.copy()
        r = self.last_sel_rect or (W // 2 - 60, H // 2 - 40, 120, 80)
        self.trans = {"t0": time.time(), "rect": r, "color": color}
        self.stack.append(state)

    def pop_state(self):
        if len(self.stack) <= 1:
            return
        self.play("back")
        self.prev_frame = self.surface.copy()
        self.trans = {"t0": time.time(), "rect": (0, 42, 52, H - 70),
                      "color": None}
        self.stack.pop()

    def interference(self):
        """Interferenze orizzontali leggere: due bande in scorrimento con
        micro-shift, uno spike raro. Non sono le scanline: e' il tremolio
        del segnale. Spegnibile dalle opzioni."""
        if not self.cfg.get("fx", True):
            return
        t = time.time()
        for spd, ph, amp, hh in ((26.0, 0, 2, 2), (9.0, 170, 1, 3)):
            y = int((t * spd + ph) % (H + 50)) - 25
            if 0 <= y < H - hh:
                band = self.surface.subsurface((0, y, W, hh)).copy()
                self.surface.blit(band,
                                  (amp if int(t * 7) % 2 else -amp, y))
        if int(t * 10) % 47 == 0:
            base = int((t * 26) % (H - 8))
            for k in range(3):
                y = (base + k * 57) % (H - 3)
                band = self.surface.subsurface((0, y, W, 2)).copy()
                self.surface.blit(band, ((-3, 3)[k % 2], y))

    def env_glyph(self, env, x, y, sc, col):
        m = ENV_GLYPHS.get(env)
        if not m:
            return
        for ry in range(16):
            bits = m[ry]
            if not bits:
                continue
            for rx in range(16):
                if bits & (1 << (15 - rx)):
                    pygame.draw.rect(
                        self.surface, col,
                        (x + rx * sc, y + ry * sc, sc - 1, sc - 1))

    # -------------------------------------------------- app muOS in Void
    def scan_muos(self):
        """Censisce MUOS/application su SD1 e SD2: nome, script, icona."""
        apps = []
        me = os.path.realpath(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        for ri, root in enumerate(MUOS_APP_ROOTS):
            try:
                names = sorted(os.listdir(root))
            except OSError:
                continue
            for n in names:
                d = os.path.join(root, n)
                sh_ = os.path.join(d, "mux_launch.sh")
                if not os.path.isfile(sh_):
                    continue
                if (os.path.realpath(d) == me
                        or n.lower().startswith("voiddesk")):
                    continue
                apps.append({"name": n, "dir": d, "script": sh_,
                             "sd": "SD%d" % (ri + 1),
                             "icon": self.find_icon(d)})
        return apps

    def find_icon(self, d):
        cand = []
        g = os.path.join(d, "glyph")
        try:
            cand += [os.path.join(g, f) for f in sorted(os.listdir(g))
                     if f.lower().endswith(".png")]
        except OSError:
            pass
        for f in ("icon.png", "cover.png", "preview.png", "logo.png"):
            p = os.path.join(d, f)
            if os.path.isfile(p):
                cand.append(p)
        return cand[0] if cand else None

    def mapp_icon(self, app, size=36):
        """Icona caricata e scalata, con cache; placeholder SPDW se manca."""
        key = (app["icon"] or app["name"], size)
        if key in self.mapp_icons:
            return self.mapp_icons[key]
        surf = None
        if app["icon"]:
            try:
                img = pygame.image.load(app["icon"])
                surf = pygame.transform.smoothscale(img, (size, size))
            except pygame.error:
                surf = None
        if surf is None:
            surf = self.mapp_placeholder(app["name"], size)
        self.mapp_icons[key] = surf
        return surf

    def mapp_placeholder(self, name, size):
        surf = pygame.Surface((size, size))
        surf.fill(INK)
        cut = max(4, size // 6)
        pygame.draw.polygon(surf, self.accent,
                            [(0, 0), (size - cut, 0), (size - 1, cut),
                             (size - 1, size - 1), (0, size - 1)], 1)
        ch = (name[:1] or "?").upper()
        f = self.f_med if size >= 30 else self.f_small
        img = f.render(ch, True, self.accent)
        surf.blit(img, ((size - img.get_width()) // 2,
                        (size - img.get_height()) // 2))
        return surf

    def normalize_glyphs(self):
        """Ordina le icone: quelle trovate finiscono in <app>/glyph/ (cosi'
        anche muOS le vede); a chi non ne ha, generiamo una glyph SPDW."""
        import shutil
        for app in self.mapps:
            g = os.path.join(app["dir"], "glyph")
            dst = os.path.join(g, "icon.png")
            try:
                if app["icon"] and os.path.dirname(app["icon"]) != g:
                    os.makedirs(g, exist_ok=True)
                    if not os.path.exists(dst):
                        shutil.copy(app["icon"], dst)
                elif not app["icon"]:
                    os.makedirs(g, exist_ok=True)
                    pygame.image.save(
                        self.mapp_placeholder(app["name"], 64), dst)
            except (OSError, pygame.error):
                pass
        self.mapp_icons.clear()
        self.mapps = self.scan_muos()

    def env_color(self, env):
        if env == "xfce":
            return self.accent
        th = self.cfg.get("theme", "ambra")
        return ENV_SECONDARY.get(th, ENV_SECONDARY["ambra"]).get(
            env, self.accent)

    def read_envs(self):
        base = os.path.exists(os.path.join(DATA, ".xfce_ready"))
        extra = set()
        try:
            extra = set(open(os.path.join(DATA, ".envs")).read().split())
        except OSError:
            pass
        return base, extra

    def backdrop(self):
        self.surface.blit(self.bg_img, (0, 0))

    def apply_fx(self):
        self.surface.blit(self.fx_img, (0, 0))

    def npanel(self, x, y, w, h, border=None, fill=PANEL, cut=9):
        """Pannello con l'angolo tagliato in alto a destra, vignetta manga."""
        pts = [(x, y), (x + w - cut, y), (x + w, y + cut),
               (x + w, y + h), (x, y + h)]
        pygame.draw.polygon(self.surface, fill, pts)
        pygame.draw.polygon(self.surface, border or LINE, pts, 1)

    def sel_frame(self, x, y, w, h, color=None):
        """Riga selezionata: lastra tinta, barra hazard, staffe agli angoli
        e un tick che scorre sul bordo basso. `color` e' la tinta
        identitaria dell'ambiente nel selettore START SESSION. Registra
        il rettangolo: origine della prossima transizione a finestra."""
        self.last_sel_rect = (x, y, w, h)
        cut = 8
        a = color or self.accent
        pts = [(x, y), (x + w - cut, y), (x + w, y + cut),
               (x + w, y + h), (x, y + h)]
        pygame.draw.polygon(self.surface,
                            sel_tint(a) if color else self.sel_bg, pts)
        pygame.draw.polygon(self.surface, a, pts, 1)
        # barra hazard a sinistra
        sy = y + 1
        while sy < y + h - 1:
            hh = min(24, y + h - 1 - sy)
            self.surface.blit(self.stripe_img, (x + 1, sy),
                              (0, 0, 6, hh))
            sy += hh
        for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y + cut, -1, 1),
                               (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
            pygame.draw.line(self.surface, a, (cx, cy), (cx + 7 * dx, cy), 2)
            pygame.draw.line(self.surface, a, (cx, cy), (cx, cy + 6 * dy), 2)
        tick = x + 10 + int((time.time() * 90) % max(1, w - 30))
        pygame.draw.line(self.surface, a, (tick, y + h - 1),
                         (tick + 9, y + h - 1), 2)

    def spinner(self, cx, cy, r=11):
        """Rotore di caricamento: tre archi sfalsati, stile radar."""
        t = time.time() * 5.2
        for i, (rr, wd) in enumerate(((r, 3), (r - 5, 2))):
            a0 = t * (1 if i == 0 else -1.4) + i * 2.1
            pygame.draw.arc(self.surface, self.accent,
                            (cx - rr, cy - rr, rr * 2, rr * 2),
                            a0, a0 + 3.6, wd)
        pygame.draw.circle(self.surface, self.accent, (cx, cy), 2)

    def render_busy(self):
        """Frame di attesa animato sopra la schermata corrente."""
        self.render(flip=False)
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        self.surface.blit(veil, (0, 0))
        pw, ph = 380, 110
        px, py = (W - pw) // 2, (H - ph) // 2
        self.npanel(px, py, pw, ph, border=self.accent, fill=INK)
        self.spinner(px + 34, py + ph // 2)
        self.text(self.busy_label, (px + 62, py + 26), self.f_med, FG,
                  maxw=pw - 80)
        el = int(time.time() - self.busy_t0)
        self.text("%d s" % el, (px + 62, py + 58), self.f_small,
                  self.accent)
        dots = "." * (1 + int(time.time() * 2.5) % 3)
        self.text(dots, (px + 62 + self.f_small.size("%d s" % el)[0] + 8,
                         py + 58), self.f_small, DIM)
        pygame.display.flip()

    def run_busy(self, label, fn):
        """Esegue fn in un thread e anima lo spinner finche' non finisce:
        mai piu' schermate incantate durante i lavori lunghi."""
        self.busy_label = label
        self.busy_t0 = time.time()
        box = {}

        def work():
            try:
                box["v"] = fn()
            except Exception as e:      # il chiamante decide cosa farne
                box["e"] = e

        th = threading.Thread(target=work)
        th.daemon = True
        th.start()
        while th.is_alive():
            evinput.poll()              # scarto l'input: niente code strane
            self.render_busy()
            self.clock.tick(30)
        evinput.poll()
        return box.get("v")

    def handoff(self, label):
        """Ultimo frame prima di passare la mano a uno script esterno:
        lo schermo cambia SUBITO, poi vd_loader continua l'animazione."""
        self.backdrop()
        pw, ph = 420, 120
        px, py = (W - pw) // 2, (H - ph) // 2
        self.npanel(px, py, pw, ph, border=self.accent, fill=INK)
        self.spinner(px + 36, py + ph // 2)
        self.text(label, (px + 66, py + 30), self.f_med, FG, maxw=pw - 84)
        self.text("SPDW FACTORY // handoff", (px + 66, py + 62),
                  self.f_tiny, FAINT)
        self.apply_fx()
        pygame.display.flip()

    # --------------------------------------------------------------- disegno
    def text(self, s, pos, f, color, maxw=None):
        if maxw:
            while s and f.size(s)[0] > maxw:
                s = s[:-1]
        self.surface.blit(f.render(s, True, color), pos)

    def mark(self, x, y, state):
        """Spunta verde / croce rossa / trattino grigio, disegnate a mano
        (le emoji non esistono nel font)."""
        if state is True:
            pygame.draw.lines(self.surface, OK_G, False,
                              [(x, y + 7), (x + 4, y + 12), (x + 13, y - 1)],
                              3)
        elif state is False:
            pygame.draw.line(self.surface, NO_R, (x, y - 1), (x + 12, y + 11),
                             3)
            pygame.draw.line(self.surface, NO_R, (x + 12, y - 1), (x, y + 11),
                             3)
        else:
            pygame.draw.line(self.surface, UNK, (x, y + 5), (x + 12, y + 5), 3)

    def checkbox(self, x, y, checked):
        pygame.draw.rect(self.surface, DIM, (x, y, 14, 14), 1)
        if checked:
            pygame.draw.rect(self.surface, self.accent, (x + 3, y + 3, 8, 8))

    def status_snapshot(self):
        now = time.time()
        if now - self._stat[1] > 8:
            pct, chg = sysinfo.battery()
            conn, ssid, lvl, iface, ip = sysinfo.wifi_status()
            self._stat = ({"batt": pct, "chg": chg, "ssid": ssid,
                           "wifi": lvl if conn else None, "conn": conn,
                           "iface": iface, "ip": ip,
                           "bt": sysinfo.bt_status(),
                           "vol": sysinfo.volume()}, now)
        return self._stat[0]

    def header(self, title, right=""):
        self.backdrop()
        pygame.draw.rect(self.surface, INK, (0, 0, W, 42))
        pygame.draw.line(self.surface, LINE, (0, 0), (W, 0), 1)
        pygame.draw.line(self.surface, self.accent, (0, 42), (W, 42), 2)
        pygame.draw.line(self.surface, INK, (0, 44), (W, 44), 2)
        # tratti hazard che mordono la riga dell'header, come una tavola
        for hx in range(0, 46, 9):
            pygame.draw.line(self.surface, self.accent, (hx, 42),
                             (hx + 5, 46), 2)
        if title == "__brand__":
            # ghost cromatici sfalsati: la firma SPDW
            self.text("Void-DESK", (13, 9), self.f_big, (150, 30, 30))
            self.text("Void-DESK", (15, 7), self.f_big, (25, 90, 100))
            self.text("Void-", (14, 8), self.f_big, FG)
            bw = self.f_big.size("Void-")[0]
            self.text("DESK", (14 + bw, 8), self.f_big, self.accent)
            tw = self.f_big.size("Void-DESK")[0]
            self.text("Extensive Desktop Experience // muOS",
                      (14 + tw + 12, 20), self.f_tiny, FAINT)
        else:
            self.text("▚ " + title, (13, 9), self.f_big, (140, 30, 30))
            self.text("▚ " + title, (14, 8), self.f_big, self.accent)
        x = W - 14
        if right:
            rw = self.f_small.size(right)[0]
            x -= rw
            self.text(right, (x, 14), self.f_small, DIM)
            x -= 14
        if self.cfg.get("battery", True):
            st = self.status_snapshot()
            # batteria (con percentuale), volume, bluetooth, wifi
            if st["batt"] is not None:
                txt = "%d%%" % st["batt"]
                tw = self.f_tiny.size(txt)[0]
                x -= tw
                self.text(txt, (x, 16), self.f_tiny,
                          NO_R if st["batt"] <= 20 else DIM)
                x -= 26
                icons.battery_icon(self.surface, x, 8, 20, st["batt"],
                                   st["chg"], OK_G, NO_R, DIM)
            x -= 28
            icons.volume_icon(self.surface, x, 10, 20, st["vol"], self.accent,
                              FAINT)
            if st["bt"] is not None:
                x -= 26
                icons.bt_icon(self.surface, x, 10, 20, st["bt"], self.accent,
                              FAINT)
            x -= 26
            icons.wifi_icon(self.surface, x, 10, 20, st["wifi"], self.accent,
                            FAINT)
            lab = st.get("ip") or st.get("ssid")
            if lab:
                sw = min(self.f_tiny.size(lab)[0], 108)
                x -= sw + 6
                self.text(lab, (x, 16), self.f_tiny, DIM, maxw=108)

    def footer(self, hints):
        pygame.draw.rect(self.surface, INK, (0, H - 28, W, 28))
        pygame.draw.line(self.surface, LINE, (0, H - 28), (W, H - 28), 1)
        x = 10
        for k, lab in hints:
            kw = self.f_small.size(k)[0]
            self.npanel(x, H - 25, kw + 12, 20, border=self.accent, fill=INK,
                        cut=5)
            self.text(k, (x + 6, H - 23), self.f_small, self.accent)
            x += kw + 18
            self.text(lab, (x, H - 23), self.f_small, DIM)
            x += self.f_small.size(lab)[0] + 15

    # ------------------------------------------------------------ componenti
    def chroot_root(self):
        mnt = os.path.join(DATA, "xfce_mnt")
        return mnt if mounted(mnt) else None

    def scan_status(self):
        """Monta l'immagine in sola lettura, verifica i file, poi smonta
        e LIBERA il loop (altrimenti dopo qualche giro i loop finiscono
        e l'installazione non riesce piu' a montare)."""
        img = os.path.join(DATA, "xfce.img")
        mnt = os.path.join(DATA, "xfce_mnt")
        temp = False
        if not imgmount.is_mounted(mnt) and os.path.exists(img):
            imgmount.cleanup_stale(img)
            ok, _err = imgmount.mount_img(img, mnt, ro=True)
            temp = ok
        root = mnt if imgmount.is_mounted(mnt) else None
        if root:
            try:
                sv = os.statvfs(root)
                self.img_free = sv.f_bavail * sv.f_frsize
                self.img_total = sv.f_blocks * sv.f_frsize
                envs = ["xfce"]
                if os.path.exists(os.path.join(
                        root, "usr/bin/icewm-session")):
                    envs.append("icewm")
                if os.path.exists(os.path.join(root, "usr/bin/startlxde")):
                    envs.append("lxde")
                os.makedirs(DATA, exist_ok=True)
                with open(os.path.join(DATA, ".envs"), "w") as f:
                    f.write(" ".join(envs))
            except OSError:
                self.img_free = None
                self.img_total = None
        st = {}
        for _cat, items in CATEGORIES:
            for name, _pkgs, _desc, paths, _ic in items:
                if root is None:
                    st[name] = None
                    continue
                st[name] = all(os.path.exists(os.path.join(root, p))
                               for p in paths.split())
        if temp:
            imgmount.umount_tree(mnt, img)
        self.status = st

    def build_rows(self):
        """Righe piatte: ('cat', titolo) oppure ('item', nome, pkgs, desc)."""
        rows = []
        for cat, items in CATEGORIES:
            rows.append(("cat", cat))
            for name, pkgs, desc, _p, ic in items:
                rows.append(("item", name, pkgs, desc, ic))
        self.rows = rows
        self.row_sel = next(i for i, r in enumerate(rows) if r[0] == "item")

    def move_rows(self, step):
        i = self.row_sel
        n = len(self.rows)
        for _ in range(n):
            i = (i + step) % n
            if self.rows[i][0] == "item":
                self.row_sel = i
                return

    def cat_starts(self):
        """Indici della prima voce di ogni categoria."""
        out = []
        for i, r in enumerate(self.rows):
            if r[0] == "cat" and i + 1 < len(self.rows) \
                    and self.rows[i + 1][0] == "item":
                out.append(i + 1)
        return out

    def jump_category(self, step):
        starts = self.cat_starts()
        if not starts:
            return
        # indice della categoria in cui mi trovo ora
        cur = 0
        for k, s0 in enumerate(starts):
            if self.row_sel >= s0:
                cur = k
        if step > 0:
            self.row_sel = starts[(cur + 1) % len(starts)]
        else:
            # se non sono gia' sulla prima voce, torno all'inizio di questa
            # categoria; altrimenti vado alla precedente (era il bug: SX
            # sembrava non fare nulla)
            if self.row_sel != starts[cur]:
                self.row_sel = starts[cur]
            else:
                self.row_sel = starts[(cur - 1) % len(starts)]

    def install_marked(self):
        idxs = sorted(self.marked) or [self.row_sel]
        names, pkgs = [], []
        for i in idxs:
            if i >= len(self.rows) or self.rows[i][0] != "item":
                continue
            names.append(self.rows[i][1])
            pkgs.append(self.rows[i][2])
        if not pkgs:
            return
        label = (names[0] if len(names) == 1 else
                 ("%d componenti" if self.lang == "it" else "%d components")
                 % len(names))
        # in modalita' disinstalla non si tocca la base del desktop:
        # senza Xorg o sessione XFCE il desktop non parte piu'.
        if self.mode == "remove":
            base = {n for _c, items in CATEGORIES[:2] for n, _p, _d, _pa, _i
                    in items}
            blocked = [n for n in names if n in base]
            if blocked:
                self.info_lines = [
                    ("sec", "info", "ATTENZIONE" if self.lang == "it"
                     else "WARNING"),
                    ("kv", "", self.t("no_base"), NO_R),
                    ("kv", "", ", ".join(blocked[:6]), DIM)]
                self.push("info")
                return
        # guardia: se l'immagine ext4 e' quasi piena, apt fallirebbe a meta'
        # lasciando pacchetti rotti. Meglio dirlo prima.
        if self.mode != "remove" and self.img_free is not None \
                and self.img_free < 250 * 1024 * 1024:
            self.info_lines = [
                ("sec", "disk", "SPAZIO INSUFFICIENTE" if self.lang == "it"
                 else "NOT ENOUGH SPACE"),
                ("kv", "", self.t("no_space") % human(self.img_free), NO_R),
                ("kv", "", self.t("no_space_s"), DIM)]
            self.scroll = 0
            self.push("info")
            return
        os.makedirs(DATA, exist_ok=True)
        with open(os.path.join(DATA, ".install_pkg"), "w") as f:
            f.write("%s\n%s\n" % (label, " ".join(pkgs)))
        self.handoff(self.t("ho_rm") if self.mode == "remove"
                     else self.t("ho_pkg"))
        self.exit_code = (EXIT_PKG_REMOVE if self.mode == "remove"
                          else EXIT_PKG_INSTALL)
        self.running = False

    # ----------------------------------------------------------- info di stato
    def void_stats(self):
        """Righe: ('sec', ICONA, TITOLO) | ('kv', etichetta, valore, colore)"""
        L = []
        st = self.status_snapshot()

        L.append(("sec", "xorg", "SISTEMA"))
        try:
            un = os.uname()
            L.append(("kv", "KERNEL", "%s %s" % (un.sysname, un.release), FG))
        except Exception:
            pass
        ver = ""
        for p in ("/opt/muos/config/system/version",
                  "/opt/muos/config/version.txt"):
            if os.path.exists(p):
                ver = open(p).read().strip().splitlines()[0]
                break
        if ver:
            L.append(("kv", "muOS", ver, FG))
        up = ""
        try:
            s_ = int(float(open("/proc/uptime").read().split()[0]))
            up = "%dh %02dm" % (s_ // 3600, (s_ % 3600) // 60)
        except (OSError, ValueError):
            pass
        if up:
            L.append(("kv", "ACCESO DA", up, FG))
        t = ""
        for z in ("/sys/class/thermal/thermal_zone0/temp",):
            v = ""
            try:
                v = open(z).read().strip()
            except OSError:
                pass
            if v.isdigit():
                iv = int(v)
                t = "%.1f °C" % (iv / 1000.0 if iv > 1000 else float(iv))
        if t:
            L.append(("kv", "TEMPERATURA", t, FG))

        L.append(("sec", "task", "MEMORIA"))
        tot = avail = 0
        try:
            for ln in open("/proc/meminfo"):
                if ln.startswith("MemTotal:"):
                    tot = int(ln.split()[1])
                elif ln.startswith("MemAvailable:"):
                    avail = int(ln.split()[1])
        except OSError:
            pass
        if tot:
            used = tot - avail
            L.append(("kv", "RAM", "%d MB usati / %d MB" %
                      (used // 1024, tot // 1024),
                      NO_R if used * 100 // tot > 85 else FG))

        L.append(("sec", "disk", "ARCHIVIAZIONE"))
        for lbl, p in (("SD1 (mmc)", "/mnt/mmc"), ("SD2 (sdcard)",
                                                   "/mnt/sdcard")):
            free, tt = disk_free(p)
            if free is not None:
                pctf = 100 - (free * 100 // tt if tt else 0)
                L.append(("kv", lbl.upper(), "%s liberi / %s  (%d%% usato)"
                          % (human(free), human(tt), pctf),
                          NO_R if pctf > 92 else FG))
        img = os.path.join(DATA, "xfce.img")
        if os.path.exists(img):
            L.append(("kv", "IMMAGINE XFCE", human(os.path.getsize(img)), FG))

        L.append(("sec", "wifi", "RETE"))
        wtxt = st["ssid"] or ("connesso" if st.get("conn") else
                              "non connesso")
        L.append(("kv", "WIFI", wtxt, OK_G if st.get("conn") else DIM))
        if st.get("iface"):
            L.append(("kv", "INTERFACCIA", st["iface"], FG))
        if st["wifi"] is not None:
            L.append(("kv", "SEGNALE", "%d/3 tacche" % st["wifi"], FG))
        addr = st.get("ip")
        L.append(("kv", "INDIRIZZO IP", addr or "n/d", FG if addr else DIM))
        L.append(("kv", "BLUETOOTH",
                  "n/d" if st["bt"] is None else
                  ("attivo" if st["bt"] else "spento"),
                  OK_G if st["bt"] else DIM))
        L.append(("kv", "INTERNET", net_test(), FG))

        L.append(("sec", "speaker", "AUDIO"))
        L.append(("kv", "VOLUME", "%d%%" % st["vol"] if st["vol"] is not None
                  else "n/d", FG))

        L.append(("sec", "desktop", "DESKTOP XFCE"))
        ready = os.path.exists(os.path.join(DATA, ".xfce_ready"))
        L.append(("kv", "STATO", "installato" if ready else "non installato",
                  OK_G if ready else NO_R))
        last = ""
        try:
            for ln in open(os.path.join(DATA, "xfce_session.log"),
                           errors="replace"):
                if "sessione terminata" in ln:
                    last = ln.strip().split()[-1]
        except OSError:
            pass
        if last:
            L.append(("kv", "ULTIMA SESSIONE",
                  ("uscita %s" if self.lang == "it" else "exit %s") % last,
                  FG))
        L.append(("kv", "CONTROLLER", self.cfg.get("controller",
                                                   "sinistro"), FG))

        L.append(("sec", "gear", "VOID BOOST"))
        bon = self.cfg.get("boost", True)
        L.append(("kv", "STATO", "attivo" if bon else "spento",
                  OK_G if bon else DIM))
        binfo = []
        try:
            binfo = open(os.path.join(DATA, ".boost_info")
                         ).read().strip().splitlines()
        except OSError:
            pass
        for ln in binfo[:3]:
            L.append(("kv", "", ln, FG))
        if bon and not binfo:
            L.append(("kv", "", "dettagli al primo avvio del desktop"
                      if self.lang == "it"
                      else "details at the next desktop launch", DIM))

        L.append(("sec", "python", "RUNTIME"))
        L.append(("kv", "PYTHON", sys.version.split()[0], FG))
        L.append(("kv", "PYGAME", "%s (SDL %s)" % (
            pygame.version.ver,
            ".".join(map(str, pygame.get_sdl_version()))), FG))
        miss = [c for c in ("curl", "gzip", "tar", "chroot", "mount")
                if not any(os.access(os.path.join(d, c), os.X_OK)
                           for d in os.environ.get("PATH", "").split(":"))]
        L.append(("kv", "DIPENDENZE",
                  ("tutte presenti" if self.lang == "it" else "all present")
                  if not miss else
                  (("mancanti: %s" if self.lang == "it" else "missing: %s")
                   % ", ".join(miss)), OK_G if not miss else NO_R))
        return L

    def about_lines(self):
        it = (self.lang == "it")
        L = [("sec", "info", "VOID SUITE")]
        L.append(("kv", "VOIDDESK", "v5.2  -  %s" %
                  ("pannello di controllo + desktop XFCE" if it
                   else "control panel + XFCE desktop"), FG))
        L.append(("kv", "VOIDCAST", "v2.2  -  %s" %
                  ("IPTV, EPG, registrazione" if it
                   else "IPTV, EPG, recording"), FG))
        L.append(("kv", "VOIDDIAG", "v1.5  -  %s" %
                  ("report diagnostico" if it else "diagnostic report"), FG))
        L.append(("sec", "xorg", "PIATTAFORMA" if it else "PLATFORM"))
        L.append(("kv", "TARGET", "Anbernic RG35XX-H", FG))
        L.append(("kv", "OS", "muOS 2601 Jacaranda", FG))
        L.append(("kv", "DESKTOP", "Ubuntu 24.04 + XFCE (chroot ext4)", FG))
        L.append(("kv", "UI", "pygame su /dev/fb0, input evdev", FG))
        L.append(("sec", "gear", "COME FUNZIONA" if it else "HOW IT WORKS"))
        for t in (("immagine ext4 in loopback: aggira i limiti di exFAT"
                   if it else
                   "loopback ext4 image: works around exFAT limits"),
                  ("Xorg su framebuffer, senza GPU"
                   if it else "Xorg on framebuffer, no GPU"),
                  ("QJoyPad traduce il gamepad in mouse e tasti"
                   if it else "QJoyPad turns the gamepad into mouse and keys"),
                  ("START+SELECT: pannello LIVE sopra XFCE"
                   if it else "START+SELECT: LIVE panel over XFCE")):
            L.append(("kv", "", t, DIM))
        L.append(("sec", "git", "CREDITI" if it else "CREDITS"))
        L.append(("kv", "SPDW FACTORY", "Void suite - universo ß", FG))
        L.append(("kv", "MustardOS", "muOS - mustard.foo", DIM))
        L.append(("kv", "MrJackSpade", "RG35XXP-XFCE (ispirazione)"
                  if it else "RG35XXP-XFCE (inspiration)", DIM))
        L.append(("kv", "iptv-org", "liste IPTV libere" if it
                  else "free IPTV playlists", DIM))
        L.append(("kv", "", "DejaVu Fonts - pygame - Ubuntu Ports", DIM))
        return L

    def guide_lines(self):
        it = (self.lang == "it")

        def kv(k, v, c=FG):
            return ("kv", k, v, c)

        L = [("sec", "gamepad", "NEL MENU" if it else "IN THE MENU")]
        L.append(kv("A / B", "conferma / indietro" if it
                    else "confirm / back"))
        L.append(kv("SX / DX", "salta di categoria (componenti)" if it
                    else "jump by category (components)"))
        L.append(kv("X / Y", "seleziona / tutti-nessuno" if it
                    else "mark / all-none"))
        L.append(kv("R1", "aggiorna lo stato dei componenti" if it
                    else "refresh component status"))
        L.append(("sec", "desktop", "DENTRO XFCE" if it else "INSIDE XFCE"))
        L.append(kv("STICK", "muove il mouse" if it else "moves the mouse"))
        L.append(kv("A / X", "click sinistro / destro" if it
                    else "left / right click"))
        L.append(kv("L1 / R1", "rotella giu' / su" if it
                    else "wheel down / up"))
        L.append(kv("MENU", "tastiera a schermo" if it
                    else "on-screen keyboard"))
        L.append(kv("START+SELECT", "pannello LIVE (volume, esci...)" if it
                    else "LIVE panel (volume, quit...)", self.accent))
        L.append(kv("", "per uscire: Logout dal menu XFCE" if it
                    else "to quit: Logout from the XFCE menu", DIM))
        L.append(("sec", "gear", "SE QUALCOSA VA STORTO" if it
                  else "IF SOMETHING BREAKS"))
        L.append(kv("", "i diari sono in LOGS & ABOUT" if it
                    else "log files live in LOGS & ABOUT", DIM))
        L.append(kv("", "mappatura tasti: OPZIONI > Mappatura" if it
                    else "button mapping: SETTINGS > Mapping", DIM))
        L.append(kv("", "ambiente: prima voce START SESSION" if it
                    else "environment: first entry START SESSION", DIM))
        return L

    def load_log(self, path):
        try:
            with open(path, "rb") as f:
                txt = f.read()[-40000:].decode("utf-8", "replace")
            self.log_lines = txt.splitlines()[-400:] or ["(vuoto)"]
        except OSError:
            self.log_lines = ["file non trovato:", path]
        self.scroll = max(0, len(self.log_lines) - 23)

    # ------------------------------------------------------------- opzioni
    def opt_defs(self):
        return [
            ("opt_theme", "theme", list(ACCENTS.keys())),
            ("opt_lang", "lang", ["it", "en"]),
            ("opt_ctrl", "controller", ["sinistro", "classico", "custom"]),
            ("opt_boost", "boost", [True, False]),
            ("opt_fx", "fx", [True, False]),
            ("opt_sfx", "sfx", [True, False]),
            ("opt_map", "__map__", None),
            ("opt_intro", "intro", [True, False]),
            ("opt_batt", "battery", [True, False]),
        ]

    # ---- mappatura tasti ---------------------------------------------
    def cur_map(self):
        m = self.cfg.get("map")
        if not m:
            m = default_map()
            self.cfg["map"] = m
        return m

    def map_rows(self):
        """Riga 0 = stick del mouse, poi una riga per funzione."""
        return ["__stick__"] + [f[0] for f in FUNCS]

    def btn_names(self, evs):
        return ", ".join(EV2NAME.get(e, "?") for e in evs) or self.t("none")

    def owner_of(self, ev, skip):
        for k, evs in self.cur_map().items():
            if k != skip and ev in evs:
                return k
        return None

    def apply_map(self):
        """Scrive il layout personalizzato e attiva il profilo custom."""
        self.cfg["controller"] = "custom"
        write_custom_layout(self.cfg, os.path.join(DATA,
                                                   "qjoypad_custom.lyt"))
        with open(os.path.join(DATA, ".qjoypad_profile"), "w") as f:
            f.write("custom\n")
        save_cfg(self.cfg)

    # -------------------------------------------------------------- input
    def on_button(self, btn):
        if btn in ("UP", "DOWN", "LEFT", "RIGHT"):
            self.play("move")
        top = self.stack[-1]
        if top == "home":
            if btn == "UP":
                self.sel = (self.sel - 1) % len(self.menu)
            elif btn == "DOWN":
                self.sel = (self.sel + 1) % len(self.menu)
            elif btn == "A":
                self.activate(self.sel)
            elif btn in ("B", "START"):
                self.running = False
        elif top == "muosapps":
            n = len(self.mapps)
            if btn == "UP" and n:
                self.mapp_sel = (self.mapp_sel - 1) % n
            elif btn == "DOWN" and n:
                self.mapp_sel = (self.mapp_sel + 1) % n
            elif btn == "R1":
                self.run_busy(self.t("mapps_scan"), self.normalize_glyphs)
                self.mapp_sel = min(self.mapp_sel,
                                    max(0, len(self.mapps) - 1))
            elif btn == "A" and n:
                app = self.mapps[self.mapp_sel]
                os.makedirs(DATA, exist_ok=True)
                with open(os.path.join(DATA, ".muos_app"), "w") as f:
                    f.write("%s\n%s\n" % (app["dir"], app["name"]))
                self.handoff(("AVVIO %s..." if self.lang == "it"
                              else "LAUNCHING %s...") % app["name"].upper())
                self.exit_code = EXIT_MUOS_APP
                self.running = False
            elif btn == "B":
                self.pop_state()
        elif top == "session":
            base, extra = self.read_envs()
            if btn == "UP":
                self.env_sel = (self.env_sel - 1) % len(ENVS)
            elif btn == "DOWN":
                self.env_sel = (self.env_sel + 1) % len(ENVS)
            elif btn == "A":
                env, _lbl, pkgs = ENVS[self.env_sel]
                self.cfg["desk_env"] = env
                save_cfg(self.cfg)
                up = env.upper()
                if not base:
                    # niente base: qualsiasi scelta parte dall'installazione
                    # completa; l'ambiente scelto restera' in config
                    self.handoff(self.t("ho_inst"))
                    self.exit_code = EXIT_XFCE_INSTALL
                elif env == "xfce" or env in extra:
                    self.handoff(("AVVIO DESKTOP %s..." if self.lang == "it"
                                  else "STARTING %s DESKTOP...") % up)
                    self.exit_code = EXIT_XFCE_LAUNCH
                else:
                    os.makedirs(DATA, exist_ok=True)
                    with open(os.path.join(DATA, ".install_pkg"),
                              "w") as f:
                        f.write("%s\n%s\n" % (up, pkgs))
                    self.handoff(("INSTALLO %s..." if self.lang == "it"
                                  else "INSTALLING %s...") % up)
                    self.exit_code = EXIT_PKG_INSTALL
                self.running = False
            elif btn == "B":
                self.pop_state()
        elif top == "compmenu":
            # v4.3 non aveva QUESTO gestore: la schermata si disegnava ma
            # nessun tasto veniva letto — console murata. Mai piu'.
            if btn == "UP":
                self.comp_sel = (self.comp_sel - 1) % len(COMP_MENU)
            elif btn == "DOWN":
                self.comp_sel = (self.comp_sel + 1) % len(COMP_MENU)
            elif btn == "A":
                self.comp_action(COMP_MENU[self.comp_sel][0])
            elif btn == "B":
                self.pop_state()
        elif top == "comp":
            if btn == "UP":
                self.move_rows(-1)
            elif btn == "DOWN":
                self.move_rows(1)
            elif btn == "LEFT":
                self.jump_category(-1)
            elif btn == "RIGHT":
                self.jump_category(1)
            elif btn == "X":
                if self.row_sel in self.marked:
                    self.marked.discard(self.row_sel)
                else:
                    self.marked.add(self.row_sel)
            elif btn == "Y":
                items = {i for i, r in enumerate(self.rows) if r[0] == "item"}
                self.marked = set() if self.marked else items
            elif btn == "R1":
                # il footer lo prometteva da due versioni: ora esiste
                self.run_busy(self.t("mounting"), self.scan_status)
            elif btn == "A":
                if not os.path.exists(os.path.join(DATA, ".xfce_ready")):
                    self.info_lines = [("sec", "info", self.t("need_xfce"))]
                    self.push("info")
                else:
                    self.install_marked()
            elif btn == "B":
                self.marked.clear()
                self.pop_state()
        elif top == "autostart":
            rows = [r for r in self.rows if r[0] == "item"]
            auto = set(self.cfg.get("autostart", []))
            if btn == "UP":
                self.row_sel = (self.row_sel - 1) % len(rows)
            elif btn == "DOWN":
                self.row_sel = (self.row_sel + 1) % len(rows)
            elif btn == "A":
                name, exe = rows[self.row_sel][1], rows[self.row_sel][2]
                if name == "-":
                    return
                execs = set(self.cfg.get("autostart_exec", []))
                if name in auto:
                    auto.discard(name)
                    execs.discard(exe)
                else:
                    auto.add(name)
                    execs.add(exe)
                self.cfg["autostart"] = sorted(auto)
                self.cfg["autostart_exec"] = sorted(execs)
                save_cfg(self.cfg)
            elif btn == "B":
                save_cfg(self.cfg)
                self.pop_state()
        elif top == "options":
            defs = self.opt_defs()
            if btn == "UP":
                self.opt_sel = (self.opt_sel - 1) % len(defs)
            elif btn == "DOWN":
                self.opt_sel = (self.opt_sel + 1) % len(defs)
            elif btn == "A":
                _k, ck, vals = defs[self.opt_sel]
                if ck == "__map__":
                    self.map_sel = 0
                    self.push("map")
                    return
                cur = self.cfg.get(ck, vals[0])
                nxt = vals[(vals.index(cur) + 1) % len(vals)] \
                    if cur in vals else vals[0]
                self.cfg[ck] = nxt
                if ck == "theme":
                    self.accent = ACCENTS[nxt]
                    self.build_style()
                elif ck == "lang":
                    self.lang = nxt
                    self.rebuild_menu()
                elif ck == "controller":
                    with open(os.path.join(DATA, ".qjoypad_profile"),
                              "w") as f:
                        f.write(nxt + "\n")
            elif btn == "B":
                save_cfg(self.cfg)
                self.pop_state()
        elif top == "map":
            rows = self.map_rows()
            if btn == "UP":
                self.map_sel = (self.map_sel - 1) % len(rows)
            elif btn == "DOWN":
                self.map_sel = (self.map_sel + 1) % len(rows)
            elif btn == "A":
                if rows[self.map_sel] == "__stick__":
                    cur = self.cfg.get("mouse_stick", "sinistro")
                    self.cfg["mouse_stick"] = ("destro" if cur == "sinistro"
                                               else "sinistro")
                    self.apply_map()
                else:
                    self.capture_t = time.time()
                    if self.js_fd is None:
                        self.js_fd = jsmap.js_open()
                    jsmap.js_poll(self.js_fd)     # svuota gli eventi vecchi
                    self.push("capture")
            elif btn == "Y":
                key = rows[self.map_sel]
                if key != "__stick__":
                    self.cur_map()[key] = list(FUNC_BY_KEY[key][5])
                    self.apply_map()
            elif btn == "X":
                self.cfg["map"] = default_map()
                self.cfg["mouse_stick"] = "sinistro"
                self.apply_map()
            elif btn == "B":
                self.apply_map()
                self.pop_state()
        elif top == "swap":
            if btn == "A":
                key, ev, other = self.pending
                m = self.cur_map()
                old = list(m[key])
                m[other] = [e for e in m[other] if e != ev] + old
                m[key] = [ev]
                self.apply_map()
                self.pop_state()
            elif btn == "B":
                self.pop_state()
        elif top == "logs":
            if btn == "UP":
                self.sel_log = (self.sel_log - 1) % len(self.logs)
            elif btn == "DOWN":
                self.sel_log = (self.sel_log + 1) % len(self.logs)
            elif btn == "A":
                if self.logs[self.sel_log][0] == "__about__":
                    self.scroll = 0
                    self.info_lines = self.about_lines()
                    self.push("info")
                elif self.logs[self.sel_log][0] == "__guide__":
                    self.scroll = 0
                    self.info_lines = self.guide_lines()
                    self.push("info")
                else:
                    self.load_log(self.logs[self.sel_log][1])
                    self.push("viewer")
            elif btn == "B":
                self.pop_state()
        elif top in ("info", "viewer"):
            if btn == "B":
                self.pop_state()
                self.scroll = 0
            elif top == "info":
                n = len(self.info_lines or [])
                if btn == "DOWN":
                    self.scroll = min(max(0, n - 15), self.scroll + 3)
                elif btn == "UP":
                    self.scroll = max(0, self.scroll - 3)
            elif top == "viewer":
                lim = max(0, len(self.log_lines) - 23)
                if btn == "UP":
                    self.scroll = max(0, self.scroll - 1)
                elif btn == "DOWN":
                    self.scroll = min(lim, self.scroll + 1)
                elif btn == "LEFT":
                    self.scroll = max(0, self.scroll - 22)
                elif btn == "RIGHT":
                    self.scroll = min(lim, self.scroll + 22)
        else:
            # rete di sicurezza: uno stato senza gestore non deve MAI piu'
            # murare la console. B torna sempre indietro.
            if btn == "B" and len(self.stack) > 1:
                self.pop_state()

    def comp_action(self, key):
        if key in ("install", "remove", "autostart"):
            if not os.path.exists(os.path.join(DATA, ".xfce_ready")):
                self.info_lines = [("sec", "info", self.t("need_xfce"))]
                self.push("info")
                return
            self.run_busy(self.t("mounting"), self.scan_status)
            self.build_rows()
            self.marked.clear()
            self.mode = key
            self.push("comp" if key != "autostart" else "autostart")
            if key == "autostart":
                self.auto_rows()
        elif key == "update":
            os.makedirs(DATA, exist_ok=True)
            with open(os.path.join(DATA, ".install_pkg"), "w") as f:
                f.write("update\n-\n")
            self.handoff(self.t("ho_update"))
            self.exit_code = EXIT_APT_UPDATE
            self.running = False
        elif key == "clean":
            self.info_lines = self.run_busy(self.t("cleaning"),
                                            self.apt_clean) or []
            self.scroll = 0
            self.push("info")
        elif key == "shell":
            self.open_shell()

    def apt_clean(self):
        img = os.path.join(DATA, "xfce.img")
        mnt = os.path.join(DATA, "xfce_mnt")
        out = []
        ok, err = imgmount.mount_img(img, mnt)
        if not ok:
            return [("sec", "info", "ERRORE"), ("kv", "mount", err, NO_R)]
        try:
            before = os.statvfs(mnt)
            subprocess.call(["chroot", mnt, "/bin/sh", "-c",
                             "apt-get clean; rm -rf /var/lib/apt/lists/*; "
                             "rm -rf /tmp/* /var/tmp/*"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
            after = os.statvfs(mnt)
            self.img_free = after.f_bavail * after.f_frsize
            freed = (after.f_bavail - before.f_bavail) * after.f_frsize
            out = [("sec", "task", "PULIZIA" if self.lang == "it"
                    else "CLEANUP"),
                   ("kv", "SPAZIO LIBERATO" if self.lang == "it"
                    else "SPACE FREED", human(max(0, freed)), OK_G),
                   ("kv", "LIBERI ORA" if self.lang == "it" else "FREE NOW",
                    human(after.f_bavail * after.f_frsize), FG)]
        finally:
            imgmount.umount_tree(mnt, img)
        return out

    def open_shell(self):
        """Terminale con tastiera a schermo (dentro il chroot se montato)."""
        img = os.path.join(DATA, "xfce.img")
        mnt = os.path.join(DATA, "xfce_mnt")
        state = {"temp": False}

        def prep():
            if os.path.exists(img) and not imgmount.is_mounted(mnt):
                ok, _e = imgmount.mount_img(img, mnt)
                state["temp"] = ok
                if not ok:
                    return
                for typ, src, dst in (("bind", "/dev", "/dev"),
                                      ("proc", "proc", "/proc"),
                                      ("sysfs", "sys", "/sys")):
                    d = os.path.join(mnt, dst.lstrip("/"))
                    if not imgmount.is_mounted(d):
                        os.makedirs(d, exist_ok=True)
                        if typ == "bind":
                            subprocess.call(["mount", "-o", "bind", src, d],
                                            stderr=subprocess.DEVNULL)
                        else:
                            subprocess.call(["mount", "-t", typ, src, d],
                                            stderr=subprocess.DEVNULL)
                try:
                    import shutil
                    shutil.copy("/etc/resolv.conf",
                                os.path.join(mnt, "etc/resolv.conf"))
                except OSError:
                    pass

        self.run_busy(self.t("mounting"), prep)
        temp = state["temp"]
        sh = shell.Shell(self.surface, FONT_PATH, self.accent,
                         mnt if imgmount.is_mounted(mnt) else "", self.lang)
        clock = pygame.time.Clock()
        dpad_t = 0.0
        while sh.running:
            for b in evinput.poll():
                if b != "MENU":
                    sh.on_button(b)
            hx, hy = evinput.hat()
            now = time.time()
            if (hx or hy) and now - dpad_t > 0.13:
                dpad_t = now
                if hy > 0:
                    sh.on_button("UP")
                elif hy < 0:
                    sh.on_button("DOWN")
                if hx < 0:
                    sh.on_button("LEFT")
                elif hx > 0:
                    sh.on_button("RIGHT")
            sh.draw()
            clock.tick(30)
        if temp:
            imgmount.umount_tree(mnt, img)

    def auto_rows(self):
        """Righe della schermata avvio al boot: solo programmi installati."""
        rows = []
        for cat, items in CATEGORIES:
            for name, pkgs, desc, paths, ic in items:
                if name not in AUTOSTART_OK:
                    continue
                if self.status.get(name) and not pkgs.startswith("!"):
                    exe = paths.split()[0].split("/")[-1]
                    rows.append(("item", name, exe, desc, ic))
        self.rows = rows or [("item", "-", "-", "-", "pkg")]
        self.row_sel = 0

    def activate(self, i):
        xfce_ok = os.path.exists(os.path.join(DATA, ".xfce_ready"))
        if i == 0:
            cur = self.cfg.get("desk_env", "xfce")
            self.env_sel = next((j for j, e in enumerate(ENVS)
                                 if e[0] == cur), 0)
            self.push("session")
        elif i == 1:
            self.comp_sel = 0
            self.push("compmenu")
        elif i == 2:
            self.mapp_sel = 0
            self.mapps = self.scan_muos()
            self.push("muosapps")
        elif i == 3:
            self.scroll = 0
            self.info_lines = self.run_busy(self.t("checking"),
                                            self.void_stats) or []
            self.push("info")
        elif i == 4:
            self.opt_sel = 0
            self.push("options")
        elif i == 5:
            self.sel_log = 0
            self.push("logs")
        else:
            self.running = False

    # -------------------------------------------------------------- render
    def render_state(self):
        top = self.stack[-1]
        if top == "home":
            self.header("__brand__")
            y = 64
            for i, (label, sub) in enumerate(self.menu):
                if i == self.sel:
                    self.sel_frame(8, y, W - 16, 54)
                self.text(label, (26, y + 6), self.f_med,
                          FG if i == self.sel else DIM)
                self.text(sub, (26, y + 30), self.f_small, FAINT, maxw=W - 48)
                y += 58
            self.footer([("A", self.t("open")), ("B", self.t("exit"))])
        elif top == "comp":
            n = len(self.marked)
            self.header(self.t("title_remove") if self.mode == "remove"
                        else self.t("title_comp"))
            # riquadro memoria: usati/totale + barra di riempimento
            if self.img_total:
                used = self.img_total - (self.img_free or 0)
                pct = min(100, used * 100 // self.img_total)
                self.npanel(8, 50, W - 16, 32, border=LINE, fill=INK, cut=8)
                self.text("%s / %s" % (human(used), human(self.img_total)),
                          (20, 53), self.f_small, FG)
                ptxt = "%d%%" % pct
                if n:
                    ptxt = (self.t("n_sel") % n) + "   " + ptxt
                self.text(ptxt, (W - 24 - self.f_small.size(ptxt)[0], 53),
                          self.f_small,
                          self.accent if pct < 85 else NO_R)
                bx, bw = 20, W - 48
                pygame.draw.rect(self.surface, (14, 15, 19),
                                 (bx, 72, bw, 6))
                pygame.draw.rect(self.surface,
                                 self.accent if pct < 85 else NO_R,
                                 (bx, 72, bw * pct // 100, 6))
                pygame.draw.rect(self.surface, LINE, (bx, 72, bw, 6), 1)
                y = 88
                per = 8
            else:
                y = 48
                per = 9
            first = max(0, min(self.row_sel - per // 2, len(self.rows) - per))
            for i in range(first, min(first + per, len(self.rows))):
                row = self.rows[i]
                if row[0] == "cat":
                    pygame.draw.line(self.surface, LINE, (10, y + 16),
                                     (W - 10, y + 16), 1)
                    pygame.draw.rect(self.surface, self.accent,
                                     (10, y + 8, 4, 12))
                    self.text(self.tx(CAT_EN, row[1]), (22, y + 6),
                              self.f_small, self.accent)
                    y += 30
                    continue
                name, _pkgs, desc = row[1], row[2], row[3]
                if i == self.row_sel:
                    self.sel_frame(8, y, W - 16, 42)
                self.checkbox(20, y + 13, i in self.marked)
                self.mark(46, y + 12, self.status.get(name))
                self.text(name, (74, y + 3), self.f_med,
                          FG if i == self.row_sel else DIM, maxw=W - 100)
                self.text(self.tx(DESC_EN, desc), (74, y + 23), self.f_tiny,
                          FAINT, maxw=W - 96)
                y += 44
            act = (self.t("remove_btn") if self.mode == "remove"
                   else self.t("inst_sel"))
            self.footer([("A", act), ("X", self.t("sel")),
                         ("Y", self.t("all")), ("R1", self.t("refresh")),
                         ("B", self.t("back"))])
        elif top == "muosapps":
            self.header(self.t("mapps_t"),
                        "%d app" % len(self.mapps) if self.mapps else "")
            if not self.mapps:
                self.npanel(60, 180, W - 120, 100, border=LINE, fill=INK)
                self.text(self.t("mapps_none"), (84, 210), self.f_med, DIM,
                          maxw=W - 160)
                self.text("SD1/SD2: MUOS/application/<app>/mux_launch.sh",
                          (84, 244), self.f_tiny, FAINT, maxw=W - 160)
            else:
                per = 7
                first = max(0, min(self.mapp_sel - per // 2,
                                   len(self.mapps) - per))
                y = 50
                for j in range(first, min(first + per, len(self.mapps))):
                    app = self.mapps[j]
                    if j == self.mapp_sel:
                        self.sel_frame(8, y, W - 16, 52)
                    self.surface.blit(self.mapp_icon(app), (20, y + 8))
                    self.text(app["name"], (68, y + 8), self.f_med,
                              FG if j == self.mapp_sel else DIM,
                              maxw=W - 180)
                    self.text(app["sd"], (68, y + 32), self.f_tiny, FAINT)
                    y += 52
            self.footer([("A", self.t("mapps_go")),
                         ("R1", self.t("mapps_r1")),
                         ("B", self.t("back"))])
        elif top == "session":
            self.header(self.t("sess"))
            base, extra = self.read_envs()
            cur = self.cfg.get("desk_env", "xfce")
            y = 62
            for j, (env, lbl, _pkgs) in enumerate(ENVS):
                col = self.env_color(env)
                inst = base and (env == "xfce" or env in extra)
                if j == self.env_sel:
                    self.sel_frame(8, y, W - 16, 96, color=col)
                else:
                    self.npanel(8, y, W - 16, 96, border=LINE, fill=INK)
                pygame.draw.rect(self.surface, col, (16, y + 12, 5, 72))
                self.env_glyph(env, 30, y + 22, 3,
                               col if (inst or not base) else FAINT)
                self.text(lbl, (92, y + 14), self.f_big,
                          col if (inst or not base) else FAINT)
                if not base:
                    st, sc = self.t("e_base"), DIM
                elif inst:
                    st = self.t("e_inst") + "  ·  " + self.t("e_launch")
                    sc = DIM
                else:
                    st, sc = self.t("e_missing"), FAINT
                self.text(st, (92, y + 52), self.f_small, sc,
                          maxw=W - 240)
                if env == cur and base:
                    tag = "► " + self.t("e_active")
                    tw = self.f_small.size(tag)[0]
                    self.npanel(W - 44 - tw, y + 12, tw + 18, 24,
                                border=col, fill=INK, cut=6)
                    self.text(tag, (W - 35 - tw, y + 16),
                              self.f_small, col)
                y += 108
            self.footer([("A", self.t("sess_a")), ("B", self.t("back"))])
        elif top == "compmenu":
            self.header(self.t("title_compmenu"))
            y = 62
            for i, row in enumerate(COMP_MENU):
                ic = row[1]
                lab = row[2] if self.lang == "it" else row[3]
                sub = row[4] if self.lang == "it" else row[5]
                if i == self.comp_sel:
                    self.sel_frame(8, y, W - 16, 58)
                icons.draw(self.surface, ic, 22, y + 16, 26,
                           self.accent if i == self.comp_sel else DIM)
                self.text(lab, (60, y + 8), self.f_med,
                          FG if i == self.comp_sel else DIM)
                self.text(sub, (60, y + 32), self.f_small, FAINT, maxw=W - 80)
                y += 62
            self.footer([("A", self.t("open")), ("B", self.t("back"))])
        elif top == "autostart":
            rows = [r for r in self.rows if r[0] == "item"]
            auto = set(self.cfg.get("autostart", []))
            self.header(self.t("title_auto"), "%d" % len(auto))
            if not rows:
                self.text(self.t("not_inst"), (26, 70), self.f_med, DIM)
            per = 8
            first = max(0, min(self.row_sel - per // 2, len(rows) - per))
            y = 54
            for i in range(first, min(first + per, len(rows))):
                _t0, name, exe, desc, ic = rows[i]
                on = name in auto
                if i == self.row_sel:
                    self.sel_frame(8, y, W - 16, 44)
                icons.draw(self.surface, ic, 20, y + 11, 22,
                           self.accent if on else DIM)
                self.text(name, (54, y + 3), self.f_med,
                          FG if i == self.row_sel else DIM)
                self.text(exe, (54, y + 24), self.f_tiny, FAINT)
                lab = self.t("auto_on") if on else self.t("auto_off")
                lw = self.f_small.size(lab)[0]
                self.npanel(W - lw - 34, y + 10, lw + 18, 24,
                            border=(OK_G if on else LINE), fill=INK, cut=6)
                self.text(lab, (W - lw - 25, y + 13), self.f_small,
                          OK_G if on else FAINT)
                y += 46
            self.footer([("A", self.t("change")), ("B", self.t("back"))])
        elif top == "map":
            self.header(self.t("title_map"))
            rows = self.map_rows()
            per = 8
            first = max(0, min(self.map_sel - per // 2, len(rows) - per))
            y = 50
            for i in range(first, min(first + per, len(rows))):
                key = rows[i]
                if i == self.map_sel:
                    self.sel_frame(8, y, W - 16, 44)
                if key == "__stick__":
                    icons.draw(self.surface, "gamepad", 20, y + 10, 24,
                               self.accent)
                    self.text(self.t("map_stick"), (54, y + 3), self.f_med,
                              FG if i == self.map_sel else DIM)
                    val = self.cfg.get("mouse_stick", "sinistro")
                else:
                    f = FUNC_BY_KEY[key]
                    icons.draw(self.surface, f[3], 20, y + 10, 24,
                               self.accent)
                    lab = f[1] if self.lang == "it" else f[2]
                    self.text(lab, (54, y + 3), self.f_med,
                              FG if i == self.map_sel else DIM)
                    if key == "kbd":
                        self.text("watcher VoidDesk", (54, y + 25),
                                  self.f_tiny, FAINT)
                    val = self.btn_names(self.cur_map().get(key, []))
                vw = self.f_med.size(val)[0]
                # "chip" col tasto assegnato
                self.npanel(W - vw - 34, y + 8, vw + 16, 26,
                            border=LINE, fill=INK, cut=6)
                self.text(val, (W - vw - 26, y + 11), self.f_med,
                          self.accent)
                y += 46
            self.footer([("A", self.t("assign")), ("Y", self.t("reset")),
                         ("X", self.t("reset_all")), ("B", self.t("back"))])
        elif top == "capture":
            self.header(self.t("title_map"))
            key = self.map_rows()[self.map_sel]
            f = FUNC_BY_KEY[key]
            lab = f[1] if self.lang == "it" else f[2]
            self.npanel(60, 150, W - 120, 170, border=self.accent,
                        fill=INK, cut=14)
            icons.draw(self.surface, f[3], W // 2 - 16, 172, 32, self.accent)
            t1 = self.t("press")
            self.text(t1, (W // 2 - self.f_small.size(t1)[0] // 2, 218),
                      self.f_small, DIM)
            self.text(lab, (W // 2 - self.f_big.size(lab)[0] // 2, 240),
                      self.f_big, FG)
            left = max(0, 5 - int(time.time() - self.capture_t))
            t2 = "%s  (%ds)" % (self.t("press_s"), left)
            self.text(t2, (W // 2 - self.f_tiny.size(t2)[0] // 2, 288),
                      self.f_tiny, FAINT)
        elif top == "swap":
            key, ev, other = self.pending
            self.header(self.t("title_map"))
            fk = FUNC_BY_KEY[key]
            fo = FUNC_BY_KEY[other]
            lk = fk[1] if self.lang == "it" else fk[2]
            lo = fo[1] if self.lang == "it" else fo[2]
            self.npanel(40, 150, W - 80, 170, border=NO_R,
                        fill=INK, cut=14)
            m1 = self.t("used_by") % (EV2NAME.get(ev, "?"), lo)
            self.text(m1, (W // 2 - self.f_med.size(m1)[0] // 2, 180),
                      self.f_med, FG, maxw=W - 100)
            m2 = "%s  →  %s" % (EV2NAME.get(ev, "?"), lk)
            self.text(m2, (W // 2 - self.f_med.size(m2)[0] // 2, 222),
                      self.f_med, self.accent)
            m3 = self.t("swap_q")
            self.text(m3, (W // 2 - self.f_small.size(m3)[0] // 2, 270),
                      self.f_small, DIM)
        elif top == "options":
            self.header(self.t("title_opts"))
            defs = self.opt_defs()
            y = 66
            for i, (lk, ck, vals) in enumerate(defs):
                if ck == "__map__":
                    disp = "▸"
                else:
                    cur = self.cfg.get(ck, vals[0])
                    disp = (self.t("yes") if cur is True else
                            self.t("no") if cur is False
                            else self.tx(VAL_EN, str(cur)))
                if i == self.opt_sel:
                    self.sel_frame(8, y, W - 16, 46)
                self.text(self.t(lk), (26, y + 10), self.f_med,
                          FG if i == self.opt_sel else DIM)
                dw = self.f_med.size(disp)[0]
                self.text(disp, (W - dw - 30, y + 10), self.f_med,
                          self.accent)
                y += 50
            self.footer([("A", self.t("change")), ("B", self.t("back"))])
        elif top == "logs":
            self.header(self.t("title_logs"))
            y = 62
            for i, (name, path) in enumerate(self.logs):
                if i == self.sel_log:
                    self.sel_frame(8, y, W - 16, 44)
                if name == "__about__":
                    icons.draw(self.surface, "info", 20, y + 10, 22,
                               self.accent)
                    self.text(self.t("about"), (50, y + 3), self.f_med,
                              FG if i == self.sel_log else DIM)
                    self.text(self.t("about_s"), (50, y + 24), self.f_tiny,
                              FAINT, maxw=W - 70)
                elif name == "__guide__":
                    icons.draw(self.surface, "doc", 20, y + 10, 22,
                               self.accent)
                    self.text(self.t("guide"), (50, y + 3), self.f_med,
                              FG if i == self.sel_log else DIM)
                    self.text(self.t("guide_s"), (50, y + 24), self.f_tiny,
                              FAINT, maxw=W - 70)
                else:
                    exists = os.path.exists(path)
                    self.mark(22, y + 14, exists if exists else None)
                    self.text(name, (50, y + 3), self.f_med,
                              FG if i == self.sel_log else DIM)
                    self.text(path, (50, y + 24), self.f_tiny, FAINT,
                              maxw=W - 70)
                y += 48
            self.footer([("A", self.t("open")), ("B", self.t("back"))])
        elif top == "info":
            self.header(self.t("title_info"))
            rows = self.info_lines or []
            per = 15
            first = max(0, min(self.scroll, max(0, len(rows) - per)))
            y = 50
            for r in rows[first:first + per]:
                if not isinstance(r, tuple):
                    self.text(str(r), (30, y), self.f_med, FG, maxw=W - 60)
                    y += 24
                    continue
                if r[0] == "sec":
                    icons.draw(self.surface, r[1], 14, y + 1, 15, self.accent)
                    lab = self.tx(STAT_EN, r[2])
                    self.text(lab, (36, y), self.f_small, self.accent)
                    tw = self.f_small.size(lab)[0]
                    pygame.draw.line(self.surface, LINE, (44 + tw, y + 8),
                                     (W - 14, y + 8), 1)
                    y += 22
                else:
                    self.text(self.tx(STAT_EN, r[1]), (30, y), self.f_tiny,
                              FAINT)
                    self.text(self.tx(VAL_EN, r[2]), (220, y - 2),
                              self.f_small, r[3], maxw=W - 240)
                    y += 20
            self.footer([(self.t("k_ud"), self.t("page")), ("B", self.t("back"))])
        elif top == "viewer":
            self.header("LOG", "%d-%d / %d" %
                        (self.scroll + 1,
                         min(self.scroll + 23, len(self.log_lines)),
                         len(self.log_lines)))
            y = 48
            for ln in self.log_lines[self.scroll:self.scroll + 23]:
                self.text(ln, (10, y), self.f_small, DIM, maxw=W - 20)
                y += 17
            self.footer([(self.t("k_ud"), self.t("row")), (self.t("k_lr"), self.t("page")),
                         ("B", self.t("back"))])
        else:
            # stato senza schermata: meglio dirlo che congelarsi
            self.header("VOID-DESK")
            self.npanel(60, 180, W - 120, 100, border=NO_R, fill=INK)
            self.text("stato sconosciuto: %s" % top, (84, 210), self.f_med,
                      NO_R)
            self.text("B: " + self.t("back"), (84, 240), self.f_small, DIM)
        self.apply_fx()

    def render(self, flip=True):
        self.render_state()
        if self.trans:
            k = (time.time() - self.trans["t0"]) / 0.16
            if k >= 1.0:
                self.trans = None
                self.play("snap")
            else:
                e = k * k * (3 - 2 * k)
                cur = self.surface.copy()
                if self.prev_frame:
                    self.surface.blit(self.prev_frame, (0, 0))
                x0, y0, w0, h0 = self.trans["rect"]
                r = pygame.Rect(int(x0 * (1 - e)), int(y0 * (1 - e)),
                                max(10, int(w0 + (W - w0) * e)),
                                max(10, int(h0 + (H - h0) * e)))
                self.surface.set_clip(r)
                self.surface.blit(cur, (0, 0))
                self.surface.set_clip(None)
                c = self.trans.get("color") or self.accent
                pygame.draw.rect(self.surface, c, r, 1)
                for cx, cy, dx, dy in ((r.left, r.top, 1, 1),
                                       (r.right - 1, r.top, -1, 1),
                                       (r.left, r.bottom - 1, 1, -1),
                                       (r.right - 1, r.bottom - 1,
                                        -1, -1)):
                    pygame.draw.line(self.surface, c, (cx, cy),
                                     (cx + 10 * dx, cy), 2)
                    pygame.draw.line(self.surface, c, (cx, cy),
                                     (cx, cy + 8 * dy), 2)
                if r.top > 1 and r.h > 8:
                    band = self.surface.subsurface(
                        (0, max(0, r.top - 1), W, 2)).copy()
                    self.surface.blit(band, (3, max(0, r.top - 1)))
        self.interference()
        if flip:
            pygame.display.flip()

    # --------------------------------------------------------------- intro
    def play_intro(self):
        """Sigla d'avvio; l'ultimo atto atterra dentro il menu vero."""
        real_flip = pygame.display.flip
        pygame.display.flip = lambda *a, **k: None
        try:
            self.render()                 # disegno il menu, senza mostrarlo
            menu_img = self.surface.copy()
        finally:
            pygame.display.flip = real_flip
        # Il tasto con cui muOS ha lanciato l'app puo' essere ancora in coda:
        # svuoto la coda e per un attimo ignoro i tasti, altrimenti la sigla
        # verrebbe saltata prima ancora di cominciare.
        evinput.poll()
        t_start = time.time()

        def can_skip():
            if time.time() - t_start < 0.8:
                evinput.poll()
                return False
            return bool(evinput.poll())

        intro.play(self.surface, pygame.display.flip, "Void-DESK",
                   self.accent, skip_check=can_skip, font_path=FONT_PATH,
                   duration=1.0, menu_surf=menu_img,
                   subtitle="THE COMPLETE XFCE DESKTOP  //  muOS EDITION")

    # ---------------------------------------------------------------- loop
    def handle_capture(self):
        """Cattura: aspetta un tasto fisico. Legge in parallelo js0 per
        imparare il numero pulsante che vede QJoyPad (verita' dal kernel)."""
        js = jsmap.js_poll(self.js_fd)
        raw = evinput.poll_raw()
        if js and raw:
            self.cfg.setdefault("qj_map", {})[str(raw[0])] = js[0] + 1
        if raw:
            ev = raw[0]
            key0 = self.map_rows()[self.map_sel]
            # QJoyPad non vede i tasti volume: ammessi solo per la tastiera
            if ev in VOLUME_KEYS and key0 != "kbd":
                return
            key = self.map_rows()[self.map_sel]
            other = self.owner_of(ev, key)
            self.pop_state()                      # esce da "capture"
            if other:
                self.pending = (key, ev, other)
                self.push("swap")
            else:
                self.cur_map()[key] = [ev]
                self.apply_map()
            return
        if time.time() - self.capture_t > 5:      # annulla per timeout
            self.pop_state()

    def run(self):
        while self.running:
            if self.stack[-1] == "capture":
                self.handle_capture()
                self.render()
                self.clock.tick(30)
                continue
            for btn in evinput.poll():
                if btn != "MENU":
                    self.on_button(btn)
            hx, hy = evinput.hat()
            now = time.time()
            if (hx or hy) and now - self._dpad_t > 0.15:
                self._dpad_t = now
                if hy > 0:
                    self.on_button("UP")
                elif hy < 0:
                    self.on_button("DOWN")
                if hx < 0:
                    self.on_button("LEFT")
                elif hx > 0:
                    self.on_button("RIGHT")
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
            self.render()
            self.clock.tick(30)
        evinput.stop()
        fbdisplay.detach()
        return self.exit_code


if __name__ == "__main__":
    sys.exit(App().run())
