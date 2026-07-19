# -*- coding: utf-8 -*-
# ============================================================================
#  VOIDDESK // intro — sigla d'avvio disegnata a runtime.
#  Atti: 1) SPDW FACTORY presents  2) montaggio del logo  3) sottotitolo
#        4) atterraggio del logo nell'header e comparsa del menu.
#  Si salta con qualsiasi tasto. Zero file esterni: e' tutto codice.
# ============================================================================
import math
import random
import time

import pygame

FONT = None
STAR_N = 90


def _f(sz, bold=False):
    try:
        f = pygame.font.Font(FONT or None, sz)
    except Exception:
        f = pygame.font.Font(None, sz)
    f.set_bold(bold)
    return f


def _rgb_split(surface, img, x, y, amount, alpha=255):
    """Aberrazione cromatica: rosso e ciano sfalsati. Sapore SPDW."""
    if amount <= 0:
        i = img.copy()
        i.set_alpha(alpha)
        surface.blit(i, (x, y))
        return
    for col, dx in (((255, 60, 60), -amount), ((60, 220, 255), amount)):
        ghost = img.copy()
        ghost.fill(col, special_flags=pygame.BLEND_RGB_MULT)
        ghost.set_alpha(int(alpha * 0.55))
        surface.blit(ghost, (x + dx, y), special_flags=pygame.BLEND_ADD)
    i = img.copy()
    i.set_alpha(alpha)
    surface.blit(i, (x, y))


def _glitch_bands(surface, img, x, y, amount):
    h = img.get_height()
    yy = 0
    while yy < h:
        band = random.randint(2, 7)
        dx = random.randint(-amount, amount) if random.random() < 0.45 else 0
        r = pygame.Rect(0, yy, img.get_width(), min(band, h - yy))
        surface.blit(img.subsurface(r), (x + dx, y + yy))
        yy += band


def _scanlines(surface, alpha=26, step=3):
    ov = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for y in range(0, surface.get_height(), step):
        pygame.draw.line(ov, (0, 0, 0, alpha), (0, y),
                         (surface.get_width(), y))
    surface.blit(ov, (0, 0))


def _vignette(surface, strength=105):
    """Bordi scuri, centro pulito (i rettangoli sono cornici, non pieni:
    prima si sommavano al contrario e spegnevano il logo)."""
    w, h = surface.get_size()
    ov = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = 9
    th = max(2, min(w, h) // (2 * steps))
    for i in range(steps):
        a = int(strength * ((steps - i) / float(steps)) ** 2.2)
        if a <= 0:
            continue
        r = pygame.Rect(i * th, i * th, w - 2 * i * th, h - 2 * i * th)
        pygame.draw.rect(ov, (0, 0, 0, a), r, th)
    surface.blit(ov, (0, 0))


class Stars(object):
    def __init__(self, w, h):
        self.pts = [[random.uniform(0, w), random.uniform(0, h),
                     random.uniform(0.2, 1.0)] for _ in range(STAR_N)]
        self.w, self.h = w, h

    def draw(self, surface, t, speed=0.0):
        for p in self.pts:
            p[0] -= speed * p[2] * 3
            if p[0] < 0:
                p[0] = self.w
                p[1] = random.uniform(0, self.h)
            v = 40 + 170 * p[2] * (0.45 + 0.55 * math.sin(t * 4 + p[2] * 9))
            v = max(0, min(255, int(v)))
            surface.set_at((int(p[0]) % self.w, int(p[1])),
                           (v // 3, v // 3, min(255, v // 2 + 20)))


class Sparks(object):
    def __init__(self):
        self.list = []

    def burst(self, x, y, n, col):
        for _ in range(n):
            a = random.uniform(0, 6.283)
            s = random.uniform(1.5, 7.0)
            self.list.append([x, y, math.cos(a) * s, math.sin(a) * s,
                              random.uniform(0.4, 1.0), col])

    def step(self, surface):
        alive = []
        for p in self.list:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.12
            p[4] -= 0.035
            if p[4] > 0:
                c = tuple(int(v * p[4]) for v in p[5])
                pygame.draw.circle(surface, c, (int(p[0]), int(p[1])),
                                   1 + int(p[4] * 2))
                alive.append(p)
        self.list = alive


def play(surface, flip, app_name="Void-DESK", accent=(255, 176, 46),
         skip_check=None, font_path=None, duration=1.0, menu_surf=None,
         subtitle=None):
    global FONT
    FONT = font_path
    W, H = surface.get_size()
    stars = Stars(W, H)
    sparks = Sparks()
    t0 = time.time()

    f_pres = _f(15)
    f_fact = _f(30, True)
    f_logo = _f(46, True)
    f_sub = _f(15)
    f_tag = _f(12)

    sub_txt = subtitle or "THE COMPLETE XFCE DESKTOP  //  muOS EDITION"
    tag_txt = "Extensive Desktop Experience  //  muOS"

    i_fact = f_fact.render("SPDW FACTORY", True, (240, 240, 246))
    i_pres = f_pres.render("p r e s e n t s", True, (140, 140, 158))
    na, nb = (app_name.split("-", 1) + [""])[:2]
    i_a = f_logo.render(na, True, (244, 244, 250))
    i_b = f_logo.render("-" + nb if nb else "", True, accent)
    i_tag = f_tag.render(tag_txt, True, (120, 120, 140))
    logo_w = i_a.get_width() + i_b.get_width()

    def skipped():
        return bool(skip_check and skip_check())

    def bg(t, speed=0.0, shake=0):
        surface.fill((5, 5, 9))
        stars.draw(surface, t, speed)
        if shake:
            return random.randint(-shake, shake), random.randint(-shake,
                                                                 shake)
        return 0, 0

    def wait(fr):
        return int(fr * duration)

    # =================== ATTO 1: SPDW FACTORY ===================
    n = wait(46)
    for i in range(n):
        if skipped():
            return
        k = i / float(n)
        t = time.time() - t0
        bg(t, 0.4)
        a = int(255 * min(1, k * 3))
        x = W // 2 - i_fact.get_width() // 2
        y = H // 2 - 40
        if k < 0.22:
            _glitch_bands(surface, i_fact, x, y, 5)
        else:
            _rgb_split(surface, i_fact, x, y,
                       int(3 * max(0, 1 - (k - 0.2) * 5)), a)
        lw = int((W - 220) * min(1, k * 1.4))
        pygame.draw.line(surface, accent, (W // 2 - lw // 2, y + 46),
                         (W // 2 + lw // 2, y + 46), 2)
        if k > 0.35:
            pa = int(255 * min(1, (k - 0.35) * 3))
            p = i_pres.copy()
            p.set_alpha(pa)
            surface.blit(p, (W // 2 - p.get_width() // 2, y + 56))
        _scanlines(surface)
        _vignette(surface)
        flip()
        time.sleep(0.018)

    # pausa di lettura
    for _ in range(wait(26)):
        if skipped():
            return
        t = time.time() - t0
        bg(t, 0.4)
        x = W // 2 - i_fact.get_width() // 2
        y = H // 2 - 40
        surface.blit(i_fact, (x, y))
        pygame.draw.line(surface, accent, (W // 2 - (W - 220) // 2, y + 46),
                         (W // 2 + (W - 220) // 2, y + 46), 2)
        surface.blit(i_pres, (W // 2 - i_pres.get_width() // 2, y + 56))
        _scanlines(surface)
        _vignette(surface)
        flip()
        time.sleep(0.018)

    # =================== ATTO 2: dissolvenza + accelerazione stelle ========
    n = wait(20)
    for i in range(n):
        if skipped():
            return
        k = i / float(n)
        t = time.time() - t0
        bg(t, 0.4 + k * 7)
        a = int(255 * (1 - k))
        f = i_fact.copy()
        f.set_alpha(a)
        surface.blit(f, (W // 2 - f.get_width() // 2, H // 2 - 40))
        p = i_pres.copy()
        p.set_alpha(a)
        surface.blit(p, (W // 2 - p.get_width() // 2, H // 2 + 16))
        _scanlines(surface)
        _vignette(surface)
        flip()
        time.sleep(0.016)

    # =================== ATTO 3: montaggio del logo ===================
    ly = H // 2 - 46
    n = wait(40)
    for i in range(n):
        if skipped():
            return
        k = i / float(n)
        t = time.time() - t0
        ease = 1 - (1 - min(1, k * 1.25)) ** 4
        sx, sy = bg(t, 7 * (1 - ease) + 0.4, 3 if 0.62 < k < 0.72 else 0)
        x = W // 2 - logo_w // 2 + sx
        off = int(180 * (1 - ease))
        a = int(255 * min(1, k * 2))
        _rgb_split(surface, i_a, x - off, ly + sy, int(6 * (1 - ease)), a)
        _rgb_split(surface, i_b, x + i_a.get_width() + off, ly + sy,
                   int(6 * (1 - ease)), a)
        # anelli d'impatto
        if k > 0.62:
            for r in (int((k - 0.62) * 700), int((k - 0.62) * 430)):
                if r > 0:
                    al = max(0, 150 - r)
                    if al > 0:
                        rs = pygame.Surface((W, H), pygame.SRCALPHA)
                        pygame.draw.circle(rs, accent + (al,),
                                           (W // 2, ly + 26), r, 2)
                        surface.blit(rs, (0, 0))
        if 0.6 < k < 0.66:
            sparks.burst(W // 2, ly + 26, 6, accent)
        sparks.step(surface)
        # riga luminosa sotto il logo
        gw = int(logo_w * ease)
        pygame.draw.line(surface, accent, (W // 2 - gw // 2, ly + 62),
                         (W // 2 + gw // 2, ly + 62), 3)
        # scia che attraversa il logo
        if 0.45 < k < 0.95:
            px = int((k - 0.45) / 0.5 * (logo_w + 90)) + W // 2 - logo_w // 2 \
                - 45
            sh = pygame.Surface((16, 66), pygame.SRCALPHA)
            for c in range(16):
                al = int(110 * (1 - abs(c - 8) / 8.0))
                pygame.draw.line(sh, accent + (al,), (c, 0), (c, 66))
            surface.blit(sh, (px, ly - 6), special_flags=pygame.BLEND_ADD)
        _scanlines(surface)
        _vignette(surface)
        flip()
        time.sleep(0.018)

    # =================== ATTO 4: sottotitolo che si scrive ===============
    n = wait(52)
    for i in range(n):
        if skipped():
            return
        k = i / float(n)
        t = time.time() - t0
        bg(t, 0.4)
        x = W // 2 - logo_w // 2
        surface.blit(i_a, (x, ly))
        surface.blit(i_b, (x + i_a.get_width(), ly))
        pygame.draw.line(surface, accent, (W // 2 - logo_w // 2, ly + 62),
                         (W // 2 + logo_w // 2, ly + 62), 3)
        sparks.step(surface)
        # macchina da scrivere
        nch = int(len(sub_txt) * min(1, k * 1.7))
        part = sub_txt[:nch]
        if part:
            img = f_sub.render(part, True, (216, 216, 228))
            surface.blit(img, (W // 2 - f_sub.size(sub_txt)[0] // 2, ly + 74))
            if nch < len(sub_txt) and int(t * 6) % 2:
                cw = f_sub.size(part)[0]
                pygame.draw.rect(surface, accent,
                                 (W // 2 - f_sub.size(sub_txt)[0] // 2 + cw,
                                  ly + 76, 7, 15))
        if k > 0.62:
            tg = i_tag.copy()
            tg.set_alpha(int(255 * min(1, (k - 0.62) * 3.2)))
            surface.blit(tg, (W // 2 - tg.get_width() // 2, ly + 100))
        _scanlines(surface)
        _vignette(surface)
        flip()
        time.sleep(0.018)

    # =================== ATTO 5: atterraggio nell'header ===============
    if menu_surf is None:
        for _ in range(wait(10)):
            flip()
            time.sleep(0.02)
        return
    logo_full = pygame.Surface((logo_w, i_a.get_height()), pygame.SRCALPHA)
    logo_full.blit(i_a, (0, 0))
    logo_full.blit(i_b, (i_a.get_width(), 0))
    # posizione/dimensione finali = quelle del logo nell'header del menu
    f_hdr = _f(26)
    tw = f_hdr.size("Void-DESK")[0]
    tx, ty = 14, 8
    n = wait(26)
    frozen = surface.copy()
    for i in range(n):
        if skipped():
            break
        k = i / float(n)
        e = 1 - (1 - k) ** 3
        # il menu entra in dissolvenza
        surface.blit(frozen, (0, 0))
        m = menu_surf.copy()
        m.set_alpha(int(255 * e))
        surface.blit(m, (0, int(18 * (1 - e))))
        # il logo scivola e rimpicciolisce fino all'header
        cw = int(logo_w + (tw - logo_w) * e)
        ch = int(i_a.get_height() * (cw / float(logo_w)))
        cx = int((W // 2 - logo_w // 2) + (tx - (W // 2 - logo_w // 2)) * e)
        cy = int(ly + (ty - ly) * e)
        if cw > 4:
            img = pygame.transform.smoothscale(logo_full, (cw, ch))
            img.set_alpha(255 if e < 0.9 else int(255 * (1 - e) * 10))
            surface.blit(img, (cx, cy))
        # lampo finale
        if k > 0.86:
            fl = pygame.Surface((W, H))
            fl.fill(accent)
            fl.set_alpha(int(70 * (1 - (k - 0.86) / 0.14)))
            surface.blit(fl, (0, 0))
        flip()
        time.sleep(0.016)
    surface.blit(menu_surf, (0, 0))
    flip()
