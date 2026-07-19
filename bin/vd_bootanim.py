#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  VOIDDESK // vd_bootanim — sigla di avvio dedicata all'ambiente desktop.
#
#  Parte quando la barra di caricamento arriva in fondo, un attimo prima di
#  startx: ~2.6 secondi di puro framebuffer, marchio SPDW FACTORY ma ognuna
#  con l'anima del desktop che sta per aprirsi:
#
#    xfce   la megastruttura: nervature che convergono, il "muso" che si
#           materializza riga per riga tra ghost cromatici. Acciaio e ciano.
#    icewm  la velocita': speedline manga orizzontali, una scheggia di
#           ghiaccio che piomba in scena e vibra all'impatto. Ghiaccio.
#    lxde   la leggerezza: griglia di punti che sale, uno swoosh che
#           plana verso il centro lasciando la scia. Ambra calda.
#
#  uso: vd_bootanim.py <xfce|icewm|lxde>
# ============================================================================
import os
import random
import sys
import time

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(APP, "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fbtext                                   # noqa: E402
from vd_loader import Painter, open_fb          # noqa: E402

BG = (5, 6, 9)
INK = (2, 2, 4)
LINE = (30, 34, 42)
FG = (233, 233, 226)

FPS_DT = 0.085
FRAMES = 30
HOLD = 0.55

# --- glifi 16x16 (bit piu' alto = colonna sinistra) -------------------------
MOUSE = [  # il "muso" xfce, versione lastra
    0b0000011111100000,
    0b0001111111111000,
    0b0011111111111100,
    0b0111111111111110,
    0b0111111111111110,
    0b1111111111111111,
    0b1111001111001111,
    0b1111001111001111,
    0b1111111111111111,
    0b1111111111111111,
    0b0111111111111110,
    0b0111100110011110,
    0b0011111111111100,
    0b0001111111111000,
    0b0000011111100000,
    0b0000000000000000,
]
BOLT = [  # scheggia/fulmine icewm
    0b0000001111110000,
    0b0000011111100000,
    0b0000111111000000,
    0b0001111110000000,
    0b0011111111111000,
    0b0111111111110000,
    0b0000011111100000,
    0b0000111111000000,
    0b0001111110000000,
    0b0011111100000000,
    0b0111111000000000,
    0b0111110000000000,
    0b0011100000000000,
    0b0001100000000000,
    0b0001000000000000,
    0b0000000000000000,
]
SWOOSH = [  # planata lxde
    0b0000000000000000,
    0b1100000000000000,
    0b1111000000000000,
    0b0111110000000000,
    0b0011111100000000,
    0b0001111111000000,
    0b0000111111110000,
    0b0000011111111100,
    0b0000011111111111,
    0b0000111111110000,
    0b0001111110000000,
    0b0011111000000000,
    0b0111100000000000,
    0b1110000000000000,
    0b1000000000000000,
    0b0000000000000000,
]


def glyph(pt, mask, x, y, sc, col, rows=16):
    """Disegna le prime `rows` righe del glifo, scalato a blocchi."""
    for ry in range(min(rows, 16)):
        bits = mask[ry]
        for rx in range(16):
            if bits & (1 << (15 - rx)):
                pt.fill(x + rx * sc, y + ry * sc, sc - 1, sc - 1, col)


def scanlines(pt, fb):
    for y in range(0, fb.h, 3):
        pt.fill(0, y, fb.w, 1, (0, 0, 0))


def frame_base(pt, fb):
    fb.clear(BG)
    pt.fill(0, 0, fb.w, 2, INK)
    pt.fill(0, fb.h - 2, fb.w, 2, INK)


def title(pt, fb, txt, col, acc):
    tw = len(txt) * fbtext.CW * 3
    tx = (fb.w - tw) // 2
    ty = fb.h - 132
    pt.big_text(tx + 2, ty + 2, txt, INK, 3)
    pt.big_text(tx, ty, txt, col, 3)
    for hx in range(tx, tx + tw, 14):
        pt.fill(hx, ty + 66, 8, 4, acc)
    sig = "SPDW FACTORY"
    fb.text((fb.w // fbtext.CW - len(sig)) // 2,
            (ty + 82) // fbtext.CH, sig, (100, 103, 110))


# ---------------------------------------------------------------- XFCE -----
def anim_xfce(pt, fb):
    STEEL = (208, 214, 210)
    CYAN = (74, 206, 224)
    GR = (120, 30, 30)
    GC = (34, 120, 140)
    sc = 9
    gx = (fb.w - 16 * sc) // 2
    gy = 88
    rnd = random.Random(7)
    for f in range(FRAMES):
        frame_base(pt, fb)
        # nervature che convergono verso il centro
        k = 1.0 - f / float(FRAMES)
        for i in range(-5, 6):
            x = fb.w // 2 + int(i * (40 + 220 * k))
            pt.fill(x, 0, 1, fb.h, LINE)
        pt.fill(0, gy + 8 * sc, fb.w, 1, LINE)
        # il muso si materializza riga per riga, tra ghost cromatici
        rows = min(16, 2 + f)
        if f < FRAMES - 4:
            j = rnd.choice((-2, -1, 1, 2))
            glyph(pt, MOUSE, gx + j, gy, sc, GR, rows)
            glyph(pt, MOUSE, gx - j, gy + 1, sc, GC, rows)
        glyph(pt, MOUSE, gx, gy, sc, STEEL if f % 7 else CYAN, rows)
        # riga di scansione che "stampa" il glifo
        if rows < 16:
            pt.fill(gx - 26, gy + rows * sc, 16 * sc + 52, 2, CYAN)
        if f > FRAMES - 10:
            title(pt, fb, "XFCE", STEEL, CYAN)
        scanlines(pt, fb)
        fb.flush()
        time.sleep(FPS_DT)


# --------------------------------------------------------------- ICEWM -----
def anim_icewm(pt, fb):
    ICE = (190, 230, 245)
    BLU = (110, 195, 250)
    DEEP = (26, 52, 78)
    sc = 9
    gy = 96
    tx = (fb.w - 16 * sc) // 2
    rnd = random.Random(11)
    arrive = 12
    for f in range(FRAMES):
        frame_base(pt, fb)
        # speedline manga: trattini orizzontali che sfrecciano
        for _ in range(14):
            y = rnd.randrange(20, fb.h - 20)
            ln = rnd.randrange(60, 260)
            x = (rnd.randrange(fb.w) + f * 90) % (fb.w + ln) - ln
            pt.fill(x, y, ln, 2 if y % 3 else 1,
                    DEEP if y % 4 else (60, 110, 150))
        # la scheggia piomba da sinistra, overshoot e vibrazione
        if f < arrive:
            gx = int(-160 + (tx + 170) * (f / float(arrive)) ** 1.6)
        else:
            gx = tx + ((-3, 3, -2, 2, -1, 1)[f - arrive]
                       if f - arrive < 6 else 0)
        glyph(pt, BOLT, gx + 3, gy + 3, sc, DEEP)
        glyph(pt, BOLT, gx, gy, sc, ICE if f % 5 else BLU)
        if f == arrive:                      # flash d'impatto
            pt.fill(0, gy - 8, fb.w, 3, ICE)
            pt.fill(0, gy + 16 * sc, fb.w, 3, ICE)
        if f > arrive + 3:
            title(pt, fb, "ICEWM", ICE, BLU)
            tag = "// TURBO"
            fb.text((fb.w // fbtext.CW - len(tag)) // 2,
                    (fb.h - 36) // fbtext.CH, tag, BLU)
        scanlines(pt, fb)
        fb.flush()
        time.sleep(FPS_DT)


# ---------------------------------------------------------------- LXDE -----
def anim_lxde(pt, fb):
    AMBER = (255, 176, 46)
    WARM = (255, 214, 130)
    DIMW = (120, 90, 40)
    sc = 8
    ex, ey = (fb.w - 16 * sc) // 2, 92
    for f in range(FRAMES):
        frame_base(pt, fb)
        # griglia di punti che sale, sempre piu' fitta: leggerezza
        off = (f * 5) % 26
        for gy in range(fb.h + 26, 40, -26):
            for gx in range(16, fb.w, 32):
                y = gy - off
                if 0 < y < fb.h:
                    pt.fill(gx, y, 2, 2,
                            LINE if (gx // 32 + gy // 26) % 3 else DIMW)
        # lo swoosh plana in diagonale verso il centro, con la scia
        t = min(1.0, f / float(FRAMES - 8))
        px = int(-140 + (ex + 140) * t)
        py = int(fb.h - 60 - (fb.h - 60 - ey) * t)
        for k, col in ((2, (60, 45, 22)), (1, DIMW)):
            glyph(pt, SWOOSH, px - k * 34, py + k * 22, sc, col)
        glyph(pt, SWOOSH, px, py, sc, AMBER if f % 6 else WARM)
        if t >= 1.0:
            title(pt, fb, "LXDE", WARM, AMBER)
        scanlines(pt, fb)
        fb.flush()
        time.sleep(FPS_DT)


# ------------------------------------------------------------- BGM -----
def synth_bgm(env):
    """Jingle di avvio sintetizzato: campane luminose + delay, quel sapore
    da boot di console anni '99. Tre spartiti diversi, ~3 secondi, zero
    file audio. Se il mixer non c'e', si parte in silenzio."""
    try:
        import pygame
        pygame.mixer.init(22050, -16, 1, 512)
    except Exception:
        return None
    import math as m
    import random as r
    SR = 22050
    N = int(SR * 3.0)
    buf = [0.0] * N

    def note(f, t0, dur, vol=0.22, atk=0.012, shine=True):
        i0 = int(t0 * SR)
        nn = int(dur * SR)
        for i in range(nn):
            if i0 + i >= N:
                break
            t = i / float(nn)
            env_ = min(1.0, (i / SR) / atk) * (1 - t) ** 2.2
            ph = 2 * m.pi * f * i / SR
            v = m.sin(ph)
            if shine:                      # armonica da campana
                v += 0.35 * m.sin(ph * 2.01) + 0.12 * m.sin(ph * 3.0)
            buf[i0 + i] += vol * env_ * v

    def whoosh(t0, dur, vol=0.20):
        i0 = int(t0 * SR)
        nn = int(dur * SR)
        rd = r.Random(5)
        lp = 0.0
        for i in range(nn):
            if i0 + i >= N:
                break
            t = i / float(nn)
            lp += 0.25 * ((rd.random() * 2 - 1) - lp)
            buf[i0 + i] += vol * (t ** 1.4) * lp * 3.0

    if env == "icewm":                    # velocita': scala che sfreccia
        for k, f in enumerate((392, 494, 587, 784, 988, 1175)):
            note(f, 0.14 + k * 0.09, 0.5, 0.20)
        whoosh(0.55, 0.5, 0.24)
        note(58, 1.02, 0.35, 0.30, atk=0.002, shine=False)   # impatto
        note(784, 1.55, 1.2, 0.16)
        note(1175, 1.62, 1.2, 0.12)
    elif env == "lxde":                   # leggerezza: triade calda
        for k, f in enumerate((262, 330, 392)):
            note(f, 0.18 + k * 0.30, 1.5, 0.18, atk=0.10)
        note(784, 1.55, 1.1, 0.10, atk=0.05)
        note(1046, 1.75, 1.0, 0.08, atk=0.05)
    else:                                 # xfce: megastruttura che si accende
        note(110, 0.0, 2.6, 0.14, atk=0.25, shine=False)     # pad basso
        for k, f in enumerate((330, 415, 494, 660)):
            note(f, 0.42 + k * 0.16, 0.9, 0.20)
        note(988, 1.55, 1.2, 0.14)

    D = int(0.18 * SR)                    # eco da sala giochi
    for i in range(D, N):
        buf[i] += buf[i - D] * 0.32
    out = bytearray()
    for v in buf:
        s = max(-1.0, min(1.0, v * 0.8))
        out += int(s * 32767).to_bytes(2, "little", signed=True)
    try:
        import pygame
        return pygame.mixer.Sound(buffer=bytes(out))
    except Exception:
        return None


ANIMS = {"xfce": anim_xfce, "icewm": anim_icewm, "lxde": anim_lxde}


def main():
    env = (sys.argv[1] if len(sys.argv) > 1 else "xfce").lower()
    fb = open_fb()
    if not fb.ok:
        return 0
    pt = Painter(fb)
    bgm = synth_bgm(env)
    if bgm:
        try:
            bgm.play()
        except Exception:
            pass
    ANIMS.get(env, anim_xfce)(pt, fb)
    time.sleep(HOLD)
    if bgm:
        try:
            bgm.fadeout(220)
            time.sleep(0.24)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
