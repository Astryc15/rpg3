#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MAGI RPG: Sobrevivência. Mundo aberto, vilas, masmorras, árvore de habilidades.
Requisitos: Python 3.9+ e pygame 2   ->   pip install pygame   |   python magi_rpg.py
Controles: WASD mover | mouse/Espaço atacar | Q E R Djinn | F interagir | H comer | G poção
           C fogueira (5 madeira) | Tab menu | Esc pausa/config | F11 tela cheia"""
import pygame as pg, math, random, json, os, array
from collections import defaultdict
from types import SimpleNamespace as NS
pg.init()
try: pg.mixer.init(22050, -16, 1, 512)
except Exception: pass
W, H, TS = 1100, 680, 32
scr = pg.display.set_mode((W, H), pg.SCALED | pg.RESIZABLE); pg.display.set_caption('Magi RPG: Sobrevivência')
clk = pg.time.Clock()
FN, FS, FB, FT = pg.font.Font(None, 23), pg.font.Font(None, 18), pg.font.Font(None, 36), pg.font.Font(None, 72)
Y, CY, RD = (252, 238, 9), (2, 215, 242), (255, 0, 60)
SAVE = os.path.join(os.path.expanduser('~'), '.magi_rpg_save.json')
CFG = dict(vol=.5, dif=1.0, shake=1)
Z = NS(mode='start', clk=None, mp=(0, 0), hs=0, shk=0, t=0, fl=None, st={}, tab='inv', sel=None, sk_sel=None, shop=None, zone='', zt=0, name_edit=True)

# ---------------------------------------------------------------- utilidades
def hs(x, y, s=0):
    n = math.sin(x * 127.1 + y * 311.7 + s * 74.7) * 43758.5453; return n - math.floor(n)
def vn(x, y, s):
    xi, yi = math.floor(x), math.floor(y); xf, yf = x - xi, y - yi
    u, v = xf * xf * (3 - 2 * xf), yf * yf * (3 - 2 * yf)
    a, b, c, d = hs(xi, yi, s), hs(xi + 1, yi, s), hs(xi, yi + 1, s), hs(xi + 1, yi + 1, s)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v
def sh(c, k): return tuple(max(0, min(255, int(v * k))) for v in c[:3])
def cv(w, h): return pg.Surface((w, h), pg.SRCALPHA)
def R(s, x, y, w, h, c): s.fill(c, (x, y, w, h))
def dist(a, b): return math.hypot(a['x'] - b['x'], a['y'] - b['y'])
def fin(s, sc=2):
    ol = pg.mask.from_surface(s).to_surface(setcolor=(16, 12, 22, 255), unsetcolor=(0, 0, 0, 0))
    o = cv(s.get_width() + 2, s.get_height() + 2)
    for d in ((0, 1), (2, 1), (1, 0), (1, 2)): o.blit(ol, d)
    o.blit(s, (1, 1)); return pg.transform.scale(o, (o.get_width() * sc, o.get_height() * sc)) if sc != 1 else o
GL = {}
def glow(r, col):
    if (r, col) not in GL:
        s = pg.Surface((r * 2, r * 2))
        for i in range(r, 0, -2):
            f = (1 - i / r) ** 2; pg.draw.circle(s, tuple(int(c * f) for c in col), (r, r), i)
        GL[(r, col)] = s
    return GL[(r, col)]
SN = {}
def beep(f, d=.08, v=.3, w='sq'):
    if not CFG['vol'] or not pg.mixer.get_init(): return
    try:
        k = (int(f), d, w)
        if k not in SN:
            n = int(22050 * d); a = array.array('h')
            for i in range(n):
                x = math.sin(6.283 * f * i / 22050); x = (1 if x > 0 else -1) if w == 'sq' else x
                a.append(int(x * 7000 * (1 - i / n)))
            SN[k] = pg.mixer.Sound(buffer=a.tobytes())
        SN[k].set_volume(v * CFG['vol']); SN[k].play()
    except Exception: pass

# ---------------------------------------------------------------- dados
RACES = {'fa': dict(n='Fanalis', d='Força lendária: mais vida e ataque.', hp=40, mp=-15, atk=6, spd=0, ves=0, sk=(168, 116, 79), hr=(217, 56, 30), ou=(138, 28, 28)),
         'mg': dict(n='Magnoshutat', d='Mestres do Magoi: mais mana e Djinn +25%.', hp=-15, mp=50, atk=-2, spd=0, ves=.25, sk=(240, 207, 174), hr=(59, 76, 192), ou=(74, 58, 160)),
         'im': dict(n='Imuchakk', d='Guerreiros ágeis: mais velocidade e vida.', hp=10, mp=0, atk=2, spd=.4, ves=0, sk=(232, 185, 143), hr=(43, 183, 168), ou=(31, 111, 120)),
         'hu': dict(n='Humano', d='Equilibrado: aprende rápido (+15% XP).', hp=0, mp=10, atk=0, spd=.1, ves=0, sk=(217, 160, 102), hr=(47, 111, 224), ou=(42, 79, 168))}
RK = list(RACES)
PAL = dict(sk=[(168, 116, 79), (240, 207, 174), (232, 185, 143), (217, 160, 102), (120, 80, 56), (250, 224, 200), (190, 140, 100)],
           hr=[(217, 56, 30), (59, 76, 192), (43, 183, 168), (47, 111, 224), (30, 26, 34), (240, 220, 120), (200, 200, 210), (160, 60, 160)],
           ou=[(138, 28, 28), (74, 58, 160), (31, 111, 120), (42, 79, 168), (40, 40, 50), (180, 140, 40), (90, 120, 50), (160, 60, 90)])
RC = [(154, 165, 177), (2, 215, 242), (180, 76, 255), (252, 238, 9)]; RN = ['Comum', 'Raro', 'Épico', 'Lendário']
TN = dict(w='Arma', a='Acessório', d='Vaso de Djinn', p='Consumível'); STN = dict(atk='Ataque', df='Defesa', hp='Vida', mp='Magoi', spd='Velocidade', crit='Crítico')
DJ = [dict(n='Baal', sub='Raio Divino: relâmpagos caem sobre inimigos.', col=(79, 208, 255), mp=25, cd=240),
      dict(n='Amon', sub='Espada de Fogo: explosão que incendeia.', col=(255, 106, 42), mp=30, cd=300),
      dict(n='Zagan', sub='Cura Verdejante: restaura 40% da vida.', col=(110, 232, 110), mp=30, cd=420),
      dict(n='Vinea', sub='Gelo Eterno: congela inimigos próximos.', col=(159, 233, 255), mp=28, cd=360),
      dict(n='Zepar', sub='Lâminas Giratórias: dez lâminas perfurantes.', col=(200, 162, 255), mp=35, cd=330)]
IT = []
def _w(n, wt, d, rg, cd, col, r, p, pr=0): IT.append(dict(n=n, t='w', wt=wt, d=d, rg=rg, cd=cd, col=col, r=r, p=p, pr=pr))
def _a(n, sl, st, col, r, p): IT.append(dict(n=n, t='a', sl=sl, st=st, col=col, r=r, p=p))
_w('Espada de Ferro', 'sword', 10, 52, 26, (205, 214, 227), 0, 40); _w('Cimitarra de Sinbad', 'scim', 15, 56, 22, (232, 224, 160), 1, 120)
_w('Lança Fanalis', 'spear', 14, 84, 30, (208, 176, 128), 1, 110); _w('Adagas Gêmeas', 'dag', 8, 38, 12, (168, 240, 255), 1, 100)
_w('Cajado de Magoi', 'staff', 13, 0, 28, (255, 155, 232), 2, 200, 1); _w('Arco de Rukh', 'bow', 12, 0, 30, (159, 232, 112), 1, 130, 1)
_w('Machado de Guerra', 'axe', 26, 62, 46, (176, 184, 200), 2, 240); _w('Lâmina de Amon', 'scim', 34, 66, 24, (255, 106, 42), 3, 600)
_a('Turbante de Aladdin', 'head', dict(mp=25, df=1), (238, 238, 255), 1, 90); _a('Chapéu de Mago', 'head', dict(mp=20, atk=2), (90, 61, 176), 1, 90)
_a('Coroa Real', 'head', dict(hp=30, df=4), (245, 197, 24), 2, 220); _a('Flauta de Aladdin', 'neck', dict(mp=30, crit=.03), (255, 210, 122), 2, 200)
_a('Colar de Ouro', 'neck', dict(hp=35), (245, 197, 24), 0, 70); _a('Cachecol de Rukh', 'neck', dict(spd=.3, df=1), (255, 77, 109), 1, 110)
_a('Anel de Metal', 'ring', dict(atk=5), (192, 200, 216), 1, 100); _a('Anel de Magoi', 'ring', dict(mp=30), (68, 170, 255), 1, 100)
_a('Pena de Rukh', 'ring', dict(crit=.08), (255, 248, 192), 2, 210); _a('Botas Voadoras', 'feet', dict(spd=.5), (125, 227, 255), 2, 230)
_a('Sandálias do Deserto', 'feet', dict(df=2, hp=10), (200, 154, 90), 0, 60); _a('Bracelete Fanalis', 'ring', dict(atk=4, df=2), (217, 56, 30), 2, 190)
for i in range(5): IT.append(dict(n='Vaso de ' + DJ[i]['n'], t='d', dj=i, col=DJ[i]['col'], r=2 if i < 3 else 3, p=300 + 150 * (i > 2)))
IT.append(dict(n='Poção de Vida', t='p', pt='hp', col=(255, 51, 85), r=0, p=25)); IT.append(dict(n='Poção de Magoi', t='p', pt='mp', col=(58, 139, 255), r=0, p=25))
BR = [('GUERREIRO', RD, [('for', 'Força', 'Ataque +4 por nível', 5, 'atk', 4, []), ('vit', 'Vigor', 'Vida +20 por nível', 5, 'hp', 20, ['for']), ('cri', 'Golpe Preciso', 'Crítico +3% por nível', 5, 'crit', .03, ['for']),
       ('fur', 'Fúria Fanalis', 'Vel. de ataque +6%', 5, 'aspd', .06, ['vit']), ('arm', 'Pele de Ferro', 'Defesa +2 por nível', 5, 'df', 2, ['cri'])]),
      ('MAGOI', CY, [('res', 'Reserva de Magoi', 'Magoi +20 por nível', 5, 'mp', 20, []), ('ves', 'Metal Vessel', 'Poder dos Djinn +12%', 5, 'ves', .12, ['res']), ('reg', 'Fluxo de Rukh', 'Regeneração de Magoi +30%', 5, 'mpreg', .3, ['res']),
       ('cdr', 'Dupla Conjuração', 'Recarga dos Djinn -6%', 5, 'cdr', .06, ['ves']), ('exp', 'Ressonância', 'Área dos Djinn +10%', 5, 'area', .1, ['reg'])]),
      ('SOBREVIVENTE', Y, [('met', 'Metabolismo', 'Fome cai 10% mais devagar', 5, 'hung', .1, []), ('pes', 'Pés Leves', 'Velocidade +0,12', 5, 'spd', .12, ['met']), ('col', 'Coletor', 'Coleta dupla +15%', 5, 'gath', .15, ['met']),
       ('oly', 'Olho de Rukh', 'XP ganho +10%', 5, 'xp', .1, ['pes']), ('sor', 'Sorte', 'Itens raros +4%', 5, 'luck', .04, ['col'])])]
MOB = dict(coelho=dict(hp=8, dm=0, sp=2.4, xp=2, sz=8, md='flee'), javali=dict(hp=48, dm=9, sp=1.7, xp=12, sz=12, md='neu'), slime=dict(hp=30, dm=6, sp=.9, xp=8, sz=11, md='hos'),
           goblin=dict(hp=45, dm=9, sp=1.5, xp=14, sz=10, md='hos'), lobo=dict(hp=58, dm=11, sp=2.0, xp=20, sz=11, md='hos'), escorpiao=dict(hp=55, dm=12, sp=1.3, xp=18, sz=10, md='hos'),
           ghoul=dict(hp=95, dm=15, sp=1.1, xp=32, sz=12, md='hos'), espectro=dict(hp=70, dm=18, sp=2.1, xp=45, sz=11, md='hos'), boss=dict(hp=1100, dm=28, sp=1.2, xp=600, sz=22, md='hos'))
def tr(k): return sum(S['tr'].get(n[0], 0) * n[5] for b in BR for n in b[2] if n[4] == k)

# ---------------------------------------------------------------- mundo
RS, SOL = 44, {3, 4, 6, 8, 9, 12, 15, 21}
VC, DC, TC = {}, {}, {}
def base_e(x, y): return vn(x / 18, y / 18, 1) * .65 + vn(x / 6, y / 6, 2) * .35
def VIL(rx, ry):
    if (rx, ry) not in VC:
        v = None
        if (rx, ry) == (0, 0): v = (RS // 2, RS // 2)
        elif hs(rx, ry, 31) > .7:
            c = (rx * RS + 22 + int(hs(rx, ry, 32) * 7) - 3, ry * RS + 22 + int(hs(rx, ry, 33) * 7) - 3)
            if base_e(*c) > .43: v = c
        VC[(rx, ry)] = v
    return VC[(rx, ry)]
def DUN(rx, ry):
    if (rx, ry) not in DC:
        d = None
        if not VIL(rx, ry) and hs(rx, ry, 53) > .72:
            c = (rx * RS + 22 + int(hs(rx, ry, 54) * 17) - 8, ry * RS + 22 + int(hs(rx, ry, 55) * 17) - 8)
            if base_e(*c) > .43: d = c
        DC[(rx, ry)] = d
    return DC[(rx, ry)]
HOUSES = [(-10, -8), (-3, -9), (4, -8), (-10, 3), (4, 3)]
def vtile(dx, dy):
    if abs(dx) > 13 or abs(dy) > 12: return None
    for hx, hy in HOUSES:
        if hx <= dx < hx + 6 and hy <= dy < hy + 5:
            r = dy - hy
            return 8 if r < 3 else 10 if (r == 4 and dx - hx == 2) else 9
        if dy == hy + 5 and dx == hx + 2: return 7
    if dx == 0 and dy == 0: return 15
    return 7 if abs(dx) <= 3 and abs(dy) <= 3 or abs(dx) <= 1 or abs(dy) <= 1 else 2
def _tile(x, y):
    rx, ry = x // RS, y // RS; v = VIL(rx, ry)
    if v:
        t = vtile(x - v[0], y - v[1])
        if t is not None: return t
    d = DUN(rx, ry)
    if d:
        dx, dy = x - d[0], y - d[1]
        if abs(dx) <= 2 and abs(dy) <= 2: return (7 if (dx == 0 and dy == 2) else 12) if (abs(dx) == 2 or abs(dy) == 2) else (11 if dx == dy == 0 else 7)
    e = base_e(x, y)
    if e < .37: return 0
    if e < .42: return 1
    des = vn(x / 26, y / 26, 4) > .6
    if e > .74: return 3
    if hs(x, y, 9) > .94: return 6 if des else 4
    if hs(x, y, 12) > .975 and not des: return 13
    return 5 if des else 2
def tile(x, y):
    if DG: return DG['g'][y][x] if 0 <= x < DG['w'] and 0 <= y < DG['h'] else 21
    t = TC.get((x, y))
    if t is None:
        t = TC[(x, y)] = _tile(x, y)
        if len(TC) > 90000: TC.clear()
    return t
def chest_at(x, y): return tile(x, y) in (2, 5) and x * x + y * y > 40 and hs(x, y, 5) > .993 and not DG
def solid(x, y): return tile(int(x // TS), int(y // TS)) in SOL
def col(x, y, r): return solid(x - r, y - r) or solid(x + r, y - r) or solid(x - r, y + r) or solid(x + r, y + r)
def mv(o, dx, dy, r):
    if not col(o['x'] + dx, o['y'], r): o['x'] += dx
    if not col(o['x'], o['y'] + dy, r): o['y'] += dy
def near_village(x, y):
    v = VIL(int(x // TS) // RS, int(y // TS) // RS)
    return bool(v) and math.hypot(x - v[0] * TS, y - v[1] * TS) < 17 * TS

def gen_dg(rx, ry):
    r = random.Random(rx * 73856093 ^ ry * 19349663); w, h = 60, 44; g = [[21] * w for _ in range(h)]; rooms = []
    for _ in range(80):
        rw, rh = r.randint(6, 11), r.randint(5, 9); x, y = r.randint(1, w - rw - 2), r.randint(1, h - rh - 2)
        if any(x < q[0] + q[2] + 2 and x + rw + 2 > q[0] and y < q[1] + q[3] + 2 and y + rh + 2 > q[1] for q in rooms): continue
        rooms.append((x, y, rw, rh))
        for j in range(y, y + rh):
            for i in range(x, x + rw): g[j][i] = 20
        if len(rooms) >= 9: break
    cs = [(q[0] + q[2] // 2, q[1] + q[3] // 2) for q in rooms]
    for a, b in zip(cs, cs[1:]):
        x, y = a
        while x != b[0]: g[y][x] = g[y + 1][x] = 20; x += 1 if b[0] > x else -1
        while y != b[1]: g[y][x] = g[y][x + 1] = 20; y += 1 if b[1] > y else -1
    g[cs[0][1]][cs[0][0]] = 22; mobs, chests, lights = [], [], []
    for n, q in enumerate(rooms):
        lights += [((q[0] + 1) * TS + 16, (q[1] + 1) * TS + 16), ((q[0] + q[2] - 2) * TS + 16, (q[1] + q[3] - 2) * TS + 16)]
        if n == 0: continue
        if n == len(rooms) - 1: mobs.append(dict(i=len(mobs), k='boss', x=cs[n][0] * TS + 16, y=cs[n][1] * TS + 16)); continue
        for _ in range(r.randint(2, 4)): mobs.append(dict(i=len(mobs), k=r.choice(['goblin', 'ghoul', 'espectro', 'lobo']), x=(q[0] + r.randint(1, q[2] - 2)) * TS + 16, y=(q[1] + r.randint(1, q[3] - 2)) * TS + 16))
        if r.random() < .65: chests.append(dict(id='%d,%d:%d' % (rx, ry, n), x=(q[0] + r.randint(1, q[2] - 2)) * TS + 16, y=(q[1] + r.randint(1, q[3] - 2)) * TS + 16))
    return dict(g=g, w=w, h=h, rooms=rooms, mobs=mobs, chests=chests, lights=lights, id=(rx, ry), sp=((cs[0][0]) * TS + 16, (cs[0][1] + 1) * TS + 16))

# ---------------------------------------------------------------- sprites
CS = {}
def char(o, d, f, eh=None, en=None, ef=None):
    if d == 3: return pg.transform.flip(char(o, 2, f, eh, en, ef), True, False)
    key = (o['race'], tuple(o['skin']), tuple(o['hr']), tuple(o['ou']), d, f, eh, en, ef)
    if key in CS: return CS[key]
    race, sk, hr, ou = o['race'], tuple(o['skin']), tuple(o['hr']), tuple(o['ou'])
    s = cv(16, 28); sk2, ou2, ouh = sh(sk, .78), sh(ou, .72), sh(ou, 1.25); side, back = d == 2, d == 1; lg = (0, 1, 0, -1)[f]
    pants, boots = (54, 48, 72), IT[ef]['col'] if ef is not None else (88, 60, 40)
    long = race in ('mg', 'hu')
    if long or race == 'im':
        if back: R(s, 4, 13, 8, 9 if long else 5, hr)
        elif long: R(s, 3, 6, 2, 11, hr); R(s, 11, 6, 2, 11, hr)
    lh1, lh2 = 6 - (lg > 0), 6 - (lg < 0)
    bx, bw = (5, 6) if side else (3, 10)
    if side: R(s, 6, 21, 3, lh1 if lg >= 0 else 6, pants); R(s, 6 + (lg > 0) * 2 - (lg < 0) * 2, 20 + 6, 4, 1, boots)
    else:
        R(s, 4, 21, 3, lh1, pants); R(s, 9, 21, 3, lh2, pants); R(s, 3, 20 + lh1, 4, 1, boots); R(s, 9, 20 + lh2, 4, 1, boots)
    if race == 'mg' and back: R(s, 3, 13, 10, 12, sh(ou, .55))
    R(s, bx, 13, bw, 8, ou); R(s, bx, 18, bw, 3, ou2); R(s, bx, 13, 1, 8, ouh); R(s, bx, 20, bw, 1, (90, 60, 34))
    if not back:
        if race == 'fa':
            for i in range(8): s.set_at((min(bx + i, bx + bw - 1), 13 + i), (176, 28, 28)); s.set_at((min(bx + i + 1, bx + bw - 1), 13 + i), (140, 20, 20))
        elif race == 'mg': R(s, 6, 13, 4, 1, (255, 225, 77)); R(s, 7, 14, 2, 2, (255, 225, 77))
        elif race == 'im': R(s, bx - 1, 13, bw + 2, 2, (240, 240, 240)); [s.set_at((bx + i, 14), (170, 170, 180)) for i in range(0, bw, 2)]
        else: R(s, bx, 17, bw, 1, (202, 162, 74))
        if en is not None: R(s, 7, 13, 2, 2, IT[en]['col'])
    a1 = lg
    if side: R(s, 7, 14 + a1, 2, 6, ou); R(s, 7, 20 + a1, 2, 2, sk)
    else:
        R(s, 1, 14 - a1, 2, 6, ou); R(s, 1, 20 - a1, 2, 2, sk); R(s, 13, 14 + a1, 2, 6, ou); R(s, 13, 20 + a1, 2, 2, sk)
    R(s, 4, 5, 8, 8, sk); R(s, 5, 12, 6, 1, sk2)
    for p in ((4, 5), (11, 5), (4, 12), (11, 12)): s.set_at(p, (0, 0, 0, 0))
    if not side and not back: R(s, 3, 9, 1, 2, sk); R(s, 12, 9, 1, 2, sk)
    if back: R(s, 3, 5, 10, 8, hr); R(s, 4, 4, 8, 1, hr)
    else:
        R(s, 4, 5, 8, 3, hr)
        if side: R(s, 9, 5, 3, 7, hr)
        if race == 'fa': R(s, 4, 3, 2, 3, hr); R(s, 7, 1, 2, 5, hr); R(s, 10, 3, 2, 3, hr)
        if race == 'mg': R(s, 3, 5, 1, 5, hr); R(s, 12, 5, 1, 5, hr)
        if race == 'hu' or race == 'im': R(s, 3, 6, 1, 3, hr); R(s, 12, 6, 1, 3, hr)
        if race == 'hu' or race == 'im': R(s, 11 if not side else 11, 8, 2, 8 if race == 'hu' else 5, hr) if side else None
        if side: R(s, 5, 9, 1, 2, (24, 20, 32)); s.set_at((3, 10), sk2)
        else: R(s, 6, 9, 1, 2, (24, 20, 32)); R(s, 9, 9, 1, 2, (24, 20, 32))
        if race == 'im' and not side: R(s, 5, 11, 1, 1, (210, 60, 60)); R(s, 10, 11, 1, 1, (210, 60, 60))
        if race == 'mg': R(s, 7, 6, 2, 1, (255, 225, 77))
    if eh is not None:
        c = IT[eh]['col']
        if eh == 10: R(s, 4, 3, 8, 2, c); [R(s, x, 1, 2, 2, c) for x in (4, 7, 10)]
        elif eh == 9: R(s, 3, 5, 10, 1, c); R(s, 5, 3, 6, 2, c); R(s, 7, 0, 2, 3, c)
        else: R(s, 3, 2, 10, 4, c); R(s, 3, 5, 10, 1, sh(c, .78)); R(s, 7, 3, 2, 2, (230, 60, 90))
    CS[key] = fin(s); return CS[key]

WS = {}
def wsp(t, c):
    if (t, c) in WS: return WS[(t, c)]
    s = cv(28, 12); br, gd = (110, 74, 42), (214, 172, 80)
    if t in ('sword', 'scim'):
        R(s, 0, 4, 4, 3, br); R(s, 0, 3, 1, 5, gd); R(s, 4, 2, 2, 7, gd)
        for i in range(17):
            y = 4 - (int(2.2 * math.sin(i / 17 * 2.6)) if t == 'scim' else 0); R(s, 6 + i, y, 1, 3, c); s.set_at((6 + i, y), sh(c, 1.3))
        R(s, 23, 4, 1, 2, c) if t == 'sword' else None
    elif t == 'spear': R(s, 0, 5, 21, 1, (130, 90, 50)); pg.draw.polygon(s, c, [(20, 2), (27, 5), (20, 8)]); R(s, 20, 4, 4, 1, sh(c, 1.3))
    elif t == 'dag': R(s, 0, 4, 3, 3, br); R(s, 3, 3, 1, 5, gd); R(s, 4, 4, 10, 3, c); R(s, 4, 4, 10, 1, sh(c, 1.3)); R(s, 14, 5, 2, 1, c)
    elif t == 'staff': R(s, 0, 5, 22, 1, (130, 82, 170)); pg.draw.circle(s, c, (24, 5), 3); pg.draw.circle(s, (255, 255, 255), (23, 4), 1)
    elif t == 'axe': R(s, 0, 5, 20, 1, (120, 80, 46)); pg.draw.polygon(s, c, [(15, 5), (18, 0), (26, 0), (24, 5), (26, 10), (18, 10)]); R(s, 18, 1, 7, 1, sh(c, 1.3))
    else:
        pg.draw.arc(s, c, (2, -6, 12, 24), -1.3, 1.3, 2); R(s, 12, 0, 1, 1, c)
        pg.draw.line(s, (235, 235, 235), (2 + int(6 * math.cos(-1.3)) + 6, 6 + int(12 * math.sin(-1.3))), (2 + int(6 * math.cos(1.3)) + 6, 6 + int(12 * math.sin(1.3))))
    WS[(t, c)] = fin(s); return WS[(t, c)]
IC = {}
def icon(i):
    if i in IC: return IC[i]
    b = IT[i]; s = cv(14, 14); c = b['col']
    if b['t'] == 'w':
        w = wsp(b['wt'], c); w = pg.transform.rotate(pg.transform.scale(w, (w.get_width() // 2, w.get_height() // 2)), 45); o = cv(32, 32); o.blit(w, (16 - w.get_width() // 2, 16 - w.get_height() // 2)); IC[i] = o; return o
    if b['t'] == 'a':
        if b['sl'] == 'head': pg.draw.circle(s, c, (7, 8), 5); R(s, 1, 8, 12, 2, sh(c, .8))
        elif b['sl'] == 'neck': pg.draw.arc(s, c, (2, 0, 10, 10), 3.5, 6, 1); R(s, 6, 8, 2, 3, c)
        elif b['sl'] == 'ring': pg.draw.circle(s, c, (7, 8), 4, 2); R(s, 6, 2, 2, 2, (255, 255, 255))
        else: R(s, 3, 1, 4, 9, c); R(s, 3, 8, 8, 3, sh(c, .8))
    elif b['t'] == 'd': pg.draw.ellipse(s, c, (1, 5, 11, 7)); R(s, 5, 2, 3, 4, c); R(s, 10, 4, 3, 2, c); R(s, 3, 7, 3, 1, (255, 255, 255))
    else: R(s, 5, 1, 4, 3, (220, 220, 230)); pg.draw.circle(s, c, (7, 9), 4)
    IC[i] = fin(s); return IC[i]
MS = {}
def mob_spr(k, f, flip=False):
    if (k, f, flip) in MS: return MS[(k, f, flip)]
    s = cv(30 if k == 'boss' else 18, 30 if k == 'boss' else 18); b = f
    if k == 'coelho': pg.draw.ellipse(s, (232, 224, 208), (3, 8, 10, 7)); R(s, 10, 6, 5, 5, (240, 232, 216)); R(s, 11, 2, 2, 5, (240, 232, 216)); R(s, 13, 3, 2, 4, (240, 232, 216)); R(s, 2, 10, 2, 2, (255, 255, 255)); R(s, 13, 8, 1, 1, (20, 20, 30)); R(s, 5, 14, 2, 2 - b, (200, 190, 175)); R(s, 10, 14, 2, 1 + b, (200, 190, 175))
    elif k == 'javali': pg.draw.ellipse(s, (110, 70, 50), (2, 6, 13, 8)); R(s, 4, 5, 8, 2, (70, 44, 32)); R(s, 12, 7, 5, 6, (120, 78, 56)); R(s, 16, 10, 2, 2, (200, 160, 140)); R(s, 15, 12, 1, 2, (255, 255, 240)); R(s, 14, 8, 1, 1, (20, 20, 30)); R(s, 4, 13, 2, 4 - b, (70, 44, 32)); R(s, 10, 13, 2, 3 + b, (70, 44, 32))
    elif k == 'slime': pg.draw.ellipse(s, (90, 220, 120), (2, 6 + b, 14, 10 - b)); R(s, 5, 8 + b, 3, 2, (210, 255, 220)); R(s, 6, 11, 2, 2, (20, 40, 30)); R(s, 11, 11, 2, 2, (20, 40, 30))
    elif k == 'goblin': R(s, 5, 8, 6, 6, (110, 80, 50)); R(s, 4, 2, 8, 6, (110, 170, 80)); R(s, 1, 3, 3, 2, (110, 170, 80)); R(s, 12, 3, 3, 2, (110, 170, 80)); R(s, 5, 4, 2, 2, (220, 40, 40)); R(s, 9, 4, 2, 2, (220, 40, 40)); R(s, 12, 9, 5, 1, (210, 210, 220)); R(s, 5, 14, 2, 3 - b, (70, 50, 30)); R(s, 9, 14, 2, 2 + b, (70, 50, 30))
    elif k == 'lobo': pg.draw.ellipse(s, (120, 125, 135), (1, 6, 13, 7)); R(s, 11, 4, 6, 6, (132, 138, 148)); R(s, 16, 7, 2, 2, (40, 40, 50)); R(s, 11, 2, 2, 3, (132, 138, 148)); R(s, 14, 2, 2, 3, (132, 138, 148)); R(s, 0, 6, 3, 2, (150, 155, 165)); R(s, 13, 5, 1, 1, (255, 220, 60)); R(s, 3, 12, 2, 4 - b, (90, 94, 104)); R(s, 9, 12, 2, 3 + b, (90, 94, 104))
    elif k == 'escorpiao': pg.draw.ellipse(s, (180, 120, 40), (3, 8, 10, 6)); R(s, 12, 6, 2, 3, (200, 140, 50)); R(s, 13, 3, 2, 3, (200, 140, 50)); R(s, 10, 2, 3, 2, (200, 140, 50)); R(s, 9, 3, 2, 2, (230, 40, 40)); R(s, 0, 7 - b, 4, 3, (150, 96, 30)); R(s, 0, 12 + b, 4, 3, (150, 96, 30)); R(s, 6, 9, 1, 1, (20, 20, 20))
    elif k == 'ghoul': R(s, 5, 8, 6, 7, (130, 110, 150)); R(s, 4, 1, 8, 8, (156, 146, 176)); R(s, 5, 4, 2, 3, (20, 10, 30)); R(s, 9, 4, 2, 3, (20, 10, 30)); R(s, 5, 7, 6, 1, (240, 240, 240)); R(s, 2, 9 + b, 3, 2, (130, 110, 150)); R(s, 11, 9 - b, 3, 2, (130, 110, 150)); R(s, 5, 15, 2, 2, (80, 70, 100)); R(s, 9, 15, 2, 2, (80, 70, 100))
    elif k == 'espectro': pg.draw.polygon(s, (255, 60, 110, 210), [(3, 15), (3, 6), (6, 2), (12, 2), (15, 6), (15, 15), (13, 13 + b), (11, 16), (9, 13 + b), (7, 16), (5, 13 + b)]); R(s, 6, 6, 2, 3, (255, 255, 255)); R(s, 10, 6, 2, 3, (255, 255, 255))
    else:
        pg.draw.ellipse(s, (70, 40, 110), (4, 8, 22, 20)); R(s, 8, 2 + b, 14, 10, (96, 56, 150)); pg.draw.polygon(s, (230, 220, 255), [(8, 4), (5, 0), (11, 3)]); pg.draw.polygon(s, (230, 220, 255), [(22, 4), (25, 0), (19, 3)]); R(s, 10, 6 + b, 3, 3, (255, 60, 60)); R(s, 17, 6 + b, 3, 3, (255, 60, 60)); R(s, 11, 11 + b, 8, 1, (255, 255, 255))
    o = fin(s); MS[(k, f, flip)] = pg.transform.flip(o, True, False) if flip else o; return MS[(k, f, flip)]
def paint(base, n=26, seed=0, var=(.84, .92, 1.08, 1.16)):
    s = cv(16, 16); s.fill(base); r = random.Random(seed)
    for _ in range(n): s.fill(sh(base, r.choice(var)), (r.randrange(16), r.randrange(16), r.choice((1, 2)), r.choice((1, 1, 2))))
    return s
TEX = {}
def mk_tex():
    big = lambda s: pg.transform.scale(s, (32, 32))
    def grass(v):
        s = paint((74, 150, 66), 30, v); r = random.Random(v + 9)
        for _ in range(4): x, y = r.randrange(1, 14), r.randrange(2, 15); s.set_at((x, y), (44, 110, 48)); s.set_at((x + 1, y - 1), (44, 110, 48))
        if v == 3: s.set_at((5, 7), (255, 110, 200)); s.set_at((11, 3), (255, 240, 120))
        return s
    TEX[2] = [big(grass(v)) for v in range(4)]; TEX[13] = TEX[4] = TEX[2]
    TEX[1] = [big(paint((224, 203, 143), 22, v)) for v in range(4)]
    def desert(v):
        s = paint((214, 176, 100), 26, v + 20)
        for y in (4, 11):
            for x in range(16): s.set_at((x, y + int(1.6 * math.sin(x / 2.2 + v))), (190, 152, 84))
        return s
    TEX[5] = TEX[6] = [big(desert(v)) for v in range(4)]
    def path(v):
        s = paint((156, 130, 94), 22, v + 40); r = random.Random(v)
        for _ in range(3): x, y = r.randrange(14), r.randrange(14); R(s, x, y, 2, 1, (182, 158, 120)); R(s, x, y + 1, 2, 1, (120, 98, 70))
        return s
    TEX[7] = TEX[15] = [big(path(v)) for v in range(4)]
    def rock(v):
        s = grass(v); pg.draw.ellipse(s, (70, 76, 88), (1, 5, 14, 11)); pg.draw.ellipse(s, (112, 118, 130), (1, 3, 14, 11)); pg.draw.ellipse(s, (150, 156, 168), (3, 4, 7, 5)); s.set_at((9, 8), (70, 76, 88)); s.set_at((10, 9), (70, 76, 88)); return s
    TEX[3] = [big(rock(v)) for v in range(4)]
    def water(f):
        s = paint((44, 112, 180), 18, 60, (.92, 1.05)); [R(s, 2 + i * 4, (f * 4 + i * 5) % 16, 5, 1, (130, 190, 235)) for i in range(3)]; return s
    TEX[0] = [big(water(f)) for f in range(4)]
    def roof(v):
        s = paint((176, 64, 48), 8, v, (.9, 1.1))
        for y in range(0, 16, 4):
            R(s, 0, y + 3, 16, 1, (110, 40, 34)); R(s, 0, y, 16, 1, (205, 92, 66))
            for x in range((y // 4 % 2) * 4, 16, 8): R(s, x, y, 1, 3, (130, 48, 38))
        return s
    TEX[8] = [big(roof(v)) for v in range(4)]
    def wall(v, door=False):
        s = paint((228, 206, 160), 6, v, (.95, 1.04))
        for x in range(0, 16, 4): R(s, x, 0, 1, 16, (196, 172, 126))
        R(s, 0, 15, 16, 1, (150, 120, 84))
        if door: R(s, 3, 1, 10, 15, (122, 76, 40)); R(s, 3, 1, 10, 1, (90, 54, 28)); R(s, 11, 9, 1, 2, (250, 220, 90))
        elif v % 2: R(s, 4, 3, 8, 7, (110, 70, 40)); R(s, 5, 4, 6, 5, (110, 184, 230)); R(s, 7, 4, 2, 5, (110, 70, 40)); R(s, 5, 6, 6, 1, (110, 70, 40))
        return s
    TEX[9] = [big(wall(v)) for v in range(4)]; TEX[10] = [big(wall(0, True))] * 4
    def stone(base, v, line):
        s = paint(base, 14, v + 70, (.9, 1.1))
        for y in (0, 8): R(s, 0, y, 16, 1, line)
        for y, o in ((0, 4), (8, 11)): R(s, o, y, 1, 8, line)
        return s
    TEX[12] = [big(stone((122, 126, 134), v, (80, 84, 94))) for v in range(4)]
    TEX[20] = [big(stone((60, 56, 74), v, (44, 40, 58))) for v in range(4)]
    TEX[21] = [big(stone((28, 26, 40), v, (14, 12, 22))) for v in range(4)]
    def stairs(c, bright):
        s = paint((50, 48, 60), 8, 3)
        for i in range(5): R(s, 2 + i, 2 + i * 2, 12 - 2 * i, 2, sh(c, .5 + .25 * i))
        if bright: R(s, 7, 12, 2, 2, (252, 238, 9))
        return s
    TEX[11] = [big(stairs((120, 124, 140), 0))] * 4; TEX[22] = [big(stairs((120, 160, 190), 1))] * 4
mk_tex()
OB = {}
def objs():
    for v in range(4):
        s = cv(16, 26); g = [(40, 112, 48), (52, 134, 56), (70, 160, 70), (96, 186, 88)] if v < 3 else [(150, 70, 34), (184, 96, 40), (214, 130, 50), (238, 170, 70)]
        R(s, 6, 16, 4, 9, (92, 60, 34)); R(s, 6, 16, 1, 9, (120, 82, 48)); R(s, 9, 18, 1, 7, (66, 42, 24)); r = random.Random(v)
        for cx, cy, rr, c in ((8, 9, 8, g[0]), (6, 8, 6, g[1]), (9, 6, 5, g[2]), (6, 5, 3, g[3])): pg.draw.circle(s, c, (cx, cy), rr)
        for _ in range(16):
            x, y = r.randrange(1, 15), r.randrange(1, 15)
            if s.get_at((x, y))[3]: s.set_at((x, y), g[r.randrange(4)])
        OB[('tree', v)] = fin(s)
    s = cv(16, 24); R(s, 6, 3, 4, 20, (46, 140, 76)); R(s, 6, 3, 1, 20, (90, 190, 110)); R(s, 2, 9, 4, 3, (46, 140, 76)); R(s, 2, 6, 2, 6, (46, 140, 76)); R(s, 10, 12, 4, 3, (46, 140, 76)); R(s, 12, 8, 2, 7, (46, 140, 76)); OB['cactus'] = fin(s)
    for k, c in (('bush', 1), ('bush0', 0)):
        s = cv(14, 10); pg.draw.ellipse(s, (36, 110, 46), (0, 2, 14, 8)); pg.draw.ellipse(s, (58, 150, 62), (1, 1, 10, 6))
        if c: [R(s, x, y, 2, 2, (220, 40, 80)) for x, y in ((3, 3), (8, 4), (6, 6), (10, 7))]
        OB[k] = fin(s)
    s = cv(12, 8); R(s, 1, 2, 10, 6, (92, 60, 34)); R(s, 2, 1, 8, 2, (140, 100, 60)); OB['stump'] = fin(s)
    s = cv(16, 14); pg.draw.ellipse(s, (130, 134, 146), (0, 3, 16, 11)); pg.draw.ellipse(s, (40, 90, 150), (3, 4, 10, 7)); R(s, 0, 0, 2, 8, (92, 60, 34)); R(s, 14, 0, 2, 8, (92, 60, 34)); R(s, 0, 0, 16, 2, (176, 64, 48)); OB['well'] = fin(s)
    s = cv(6, 22); R(s, 2, 4, 2, 18, (60, 56, 70)); R(s, 0, 0, 6, 5, (255, 220, 120)); R(s, 1, 1, 4, 3, (255, 250, 200)); OB['lamp'] = fin(s)
    for k, o in (('chest', 0), ('chesto', 1)):
        s = cv(14, 12); R(s, 0, 4 if not o else 1, 14, 4, (150, 96, 40)); R(s, 0, 7, 14, 5, (110, 68, 28)); R(s, 6, 6, 2, 3, (252, 238, 9)); R(s, 0, 7, 14, 1, (252, 238, 9)); OB[k] = fin(s)
    s = cv(8, 8); pg.draw.circle(s, (252, 220, 40), (4, 4), 3); R(s, 3, 2, 1, 2, (255, 255, 200)); OB['coin'] = fin(s)
objs()

# ---------------------------------------------------------------- estado de jogo
S = None; DG = None
E, PU, EP, PR, FXL, PT, TXL, FIRES, TOAST = [], [], [], [], [], [], [], [], []
Q = dict(ac=0, sw=0, cd=[0, 0, 0], au=0, aucol=(255, 255, 255), inv=0, fr=0, wf=0.0, face=0.0, mvg=False, out=None, nc={}, dep={})
def toast(m, c=CY): TOAST.append([m, c, 220]); del TOAST[:-5]
def stats():
    r = RACES[S['race']]; o = defaultdict(float)
    for it in S['eq'].values():
        if it:
            m = 1 + .2 * it['up']
            for k, v in IT[it['i']].get('st', {}).items(): o[k] += v * m
    w = S['eq'].get('w'); wd = IT[w['i']]['d'] * (1 + .2 * w['up']) if w else 2
    return dict(mhp=round(100 + r['hp'] + S['lv'] * 8 + o['hp'] + tr('hp')), mmp=round(60 + r['mp'] + S['lv'] * 4 + o['mp'] + tr('mp')), atk=round(wd + 3 + r['atk'] + S['lv'] + o['atk'] + tr('atk')),
                df=round(o['df'] + tr('df')), spd=2.1 + r['spd'] + o['spd'] + tr('spd'), crit=.05 + o['crit'] + tr('crit'), ves=1 + r['ves'] + tr('ves'), aspd=1 + tr('aspd'), mpreg=1 + tr('mpreg'),
                cdr=1 - tr('cdr'), area=1 + tr('area'), xpm=1 + tr('xp') + (.15 if S['race'] == 'hu' else 0), hung=1 - tr('hung'), gath=tr('gath'), luck=tr('luck'))
def clampv(): Z.st = stats(); S['hp'] = min(S['hp'], Z.st['mhp']); S['mp'] = min(S['mp'], Z.st['mmp'])
def xpn(l): return round(35 * l * l + 40 * l)
def new_game(o):
    global S
    S = dict(name=o['name'] or 'Herói', race=o['race'], skin=list(o['skin']), hr=list(o['hr']), ou=list(o['ou']), x=RS // 2 * TS + 16, y=(RS // 2 + 5) * TS, hp=999, mp=999, hun=100, xp=0, lv=1, pt=0, gold=60, t=3600,
             tr={}, eq=dict(w=dict(i=0, up=0), d0=dict(i=20, up=0)), inv=[dict(i=25, up=0), dict(i=26, up=0)], mat=dict(madeira=0, pedra=0, carne=0, fruta=3, pao=2), op=[], dg={})
    begin()
def begin():
    global DG
    DG = None; Q['out'] = None; for_l = (E, PU, EP, PR, FXL, PT, TXL, FIRES)
    for l in for_l: l.clear()
    S['eq'].setdefault('w', None); clampv(); Z.mode = 'play'; toast('Bem-vindo, %s! A noite é perigosa: fique perto das vilas e fogueiras.' % S['name'], Y)
def save():
    try:
        d = dict(S); 
        if Q['out']: d['x'], d['y'] = Q['out']
        d['inv_ok'] = 1
        json.dump(dict(S=d, cfg=CFG), open(SAVE, 'w'))
    except Exception: pass
def load():
    global S
    try:
        d = json.load(open(SAVE)); S = d['S']; CFG.update(d.get('cfg', {})); S.setdefault('dg', {}); S.setdefault('op', []); begin(); return True
    except Exception: return False
def roll_item(luck=0, dg=0):
    r = random.random() - luck - dg * .03
    if random.random() < .3: return dict(i=25 + random.randrange(2), up=0)
    rr = 0 if r < .55 else 1 if r < .82 else 2 if r < .96 else 3
    c = [i for i, b in enumerate(IT) if b['t'] != 'p' and b['r'] == rr]; return dict(i=random.choice(c), up=0)

# ---------------------------------------------------------------- efeitos
def burst(x, y, n, c, sp=3, life=30, add=1, g=0, sz=2):
    for _ in range(n):
        a = random.uniform(0, 6.283); v = random.uniform(.3, 1) * sp; PT.append([x, y, math.cos(a) * v, math.sin(a) * v, life, life, c, sz, add, g])
def bolt(x1, y1, x2, y2, c):
    n = 8; pts = [(x1, y1)]
    for i in range(1, n): pts.append((x1 + (x2 - x1) * i / n + random.uniform(-14, 14), y1 + (y2 - y1) * i / n + random.uniform(-14, 14)))
    pts.append((x2, y2)); FXL.append(dict(k='bo', pts=pts, c=c, life=18, max=18)); burst(x2, y2, 10, c, 4, 20)
def popup(x, y, t, c=(255, 255, 255)): TXL.append([x, y, str(t), c, 45])
def hurt(e, base, crit_ok=True):
    cr = crit_ok and random.random() < Z.st['crit']; d = base * random.uniform(.85, 1.15) * (2 if cr else 1)
    a = math.atan2(e['y'] - S['y'], e['x'] - S['x']); e['hp'] -= d; e['kx'], e['ky'] = math.cos(a) * 5, math.sin(a) * 5; e['fl'] = 7; e['ag'] = 1
    popup(e['x'], e['y'] - 30, int(d), Y if cr else (255, 255, 255)); burst(e['x'], e['y'] - 10, 6 if not cr else 14, (255, 230, 160) if cr else (255, 120, 80), 3, 18)
    Z.hs = 5 if cr else 3; Z.shk = max(Z.shk, 7 if cr else 3); beep(180 if not cr else 320, .06)
    if e['hp'] <= 0: kill(e)
def kill(e):
    if e not in E: return
    E.remove(e); m = MOB[e['k']]; dgf = math.hypot(e['x'], e['y']) / 1400
    S['xp'] += round(m['xp'] * (1 + dgf * .2) * Z.st['xpm']); burst(e['x'], e['y'] - 8, 22, (255, 255, 255), 4, 28)
    if m['md'] != 'flee' and m['dm']: PU.append(dict(k='g', v=round(m['xp'] * random.uniform(.4, .9) * (1 + dgf * .3)) + 1, x=e['x'], y=e['y'], t=0))
    if e['k'] in ('coelho', 'javali', 'lobo') and random.random() < .9: PU.append(dict(k='m', v='carne', x=e['x'], y=e['y'], t=0))
    if m['md'] == 'hos' and random.random() < .22 + (.4 if e['k'] == 'boss' else 0): PU.append(dict(k='i', v=roll_item(Z.st['luck'], dgf), x=e['x'] + 8, y=e['y'], t=0))
    if e['k'] == 'boss':
        PU.append(dict(k='i', v=dict(i=23 + random.randrange(2), up=0), x=e['x'], y=e['y'] + 20, t=0)); S['dg'].setdefault('%d,%d' % DG['id'], dict(dead=[], boss=0))['boss'] = 1; toast('O Djinn Sombrio caiu! Um vaso lendário apareceu!', Y)
    if DG: S['dg'].setdefault('%d,%d' % DG['id'], dict(dead=[], boss=0))['dead'].append(e.get('di'))
    while S['xp'] >= xpn(S['lv']):
        S['xp'] -= xpn(S['lv']); S['lv'] += 1; S['pt'] += 1 + (S['lv'] % 5 == 0); clampv(); S['hp'], S['mp'] = Z.st['mhp'], Z.st['mmp']; toast('NÍVEL %d! Pontos de habilidade: %d' % (S['lv'], S['pt']), Y); beep(660, .4, .3, 'sin')
        burst(S['x'], S['y'] - 20, 40, (252, 238, 9), 5, 40)
def proj(x, y, a, sp, d, c, pierce=0, orb=0): PR.append(dict(x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp, d=d, l=70, c=c, p=pierce, o=orb, hit=set(), a=a))
def attack():
    if Q['ac'] > 0: return
    w = S['eq'].get('w'); it = IT[w['i']] if w else dict(wt='fist', rg=36, cd=24, col=(255, 255, 255), pr=0)
    Q['ac'] = it['cd'] / Z.st['aspd']; Q['sw'] = 14; a = Q['face']; y = S['y'] - 22
    if it['pr']: proj(S['x'], y, a, 8, Z.st['atk'] * (1.05 if it['wt'] == 'staff' else 1.1), it['col'], 0, it['wt'] == 'staff')
    else:
        arc = .3 if it['wt'] == 'spear' else 1.2 if it['wt'] == 'axe' else .8 if it['wt'] == 'dag' else .95
        FXL.append(dict(k='sl', x=S['x'], y=y, a=a, r=it['rg'], w=arc, life=12, max=12, c=it['col']))
        for e in E[:]:
            d = dist(e, S)
            if d < it['rg'] + e['sz']:
                da = abs((math.atan2(e['y'] - S['y'], e['x'] - S['x']) - a + math.pi) % 6.283 - math.pi)
                if da < arc + .3 or d < 26: hurt(e, Z.st['atk'])
    beep(520 if it['wt'] == 'dag' else 280, .08, .25, 'sq')
def cast(n):
    d = S['eq'].get('d%d' % n)
    if not d or Q['cd'][n] > 0: return
    i = IT[d['i']]['dj']; b = DJ[i]; st = Z.st
    if S['mp'] < b['mp']: toast('Magoi insuficiente', RD); return
    S['mp'] -= b['mp']; Q['cd'][n] = b['cd'] * st['cdr']; Q['au'] = 60; Q['aucol'] = b['col']; pw = st['ves'] * (1 + .2 * d['up']); x, y = S['x'], S['y'] - 22; c = b['col']; ar = st['area']
    if i == 0:
        ts = sorted([e for e in E if dist(e, S) < 270 * ar], key=lambda e: dist(e, S))[:5]
        if not ts: bolt(x, y, x + math.cos(Q['face']) * 190, y + math.sin(Q['face']) * 190, c)
        for e in ts: bolt(x, y, e['x'], e['y'] - 12, c); bolt(e['x'], e['y'] - 12, e['x'] + random.uniform(-40, 40), e['y'] + random.uniform(-30, 30), c); hurt(e, st['atk'] * 2.6 * pw)
        Z.fl = (c, 90)
    elif i == 1:
        FXL.append(dict(k='rg', x=S['x'], y=S['y'] - 8, r=135 * ar, life=26, max=26, c=c)); burst(S['x'], S['y'] - 8, 50, (255, 140, 40), 6, 36, 1, -.05, 3)
        for e in E[:]:
            if dist(e, S) < 135 * ar: hurt(e, st['atk'] * 2 * pw); e['bn'] = 200
        Z.fl = (c, 60)
    elif i == 2:
        S['hp'] = min(st['mhp'], S['hp'] + st['mhp'] * .4 * pw)
        for _ in range(30): PT.append([S['x'] + random.uniform(-18, 18), S['y'] - random.uniform(0, 20), random.uniform(-.4, .4), random.uniform(-2.5, -.8), 50, 50, c, 3, 1, 0])
        FXL.append(dict(k='rg', x=S['x'], y=S['y'] - 4, r=50, life=30, max=30, c=c))
    elif i == 3:
        FXL.append(dict(k='rg', x=S['x'], y=S['y'] - 8, r=175 * ar, life=30, max=30, c=c))
        for k in range(10): a = k * .628; FXL.append(dict(k='ic', x=S['x'] + math.cos(a) * 60 * ar, y=S['y'] + math.sin(a) * 60 * ar, a=a, life=50, max=50, c=c))
        for e in E[:]:
            if dist(e, S) < 175 * ar: e['fz'] = 220 * pw; hurt(e, st['atk'] * pw)
    else:
        for k in range(10): proj(S['x'], y, k * .628, 5, st['atk'] * 1.2 * pw, c, 1)
        FXL.append(dict(k='rg', x=S['x'], y=S['y'] - 8, r=60, life=20, max=20, c=c))
    Z.shk = max(Z.shk, 8); beep(880, .3, .35, 'sin'); toast(b['n'] + '!', c)
def hurt_p(d):
    if Q['inv'] > 0: return
    d = max(1, round(d - Z.st['df'] * .5)); S['hp'] -= d; Q['inv'] = 28; Z.shk = 9; popup(S['x'], S['y'] - 50, d, RD); burst(S['x'], S['y'] - 20, 12, (255, 40, 70), 3, 20); beep(110, .15, .4)
    if S['hp'] <= 0:
        S['hp'] = Z.st['mhp'] * .6; S['gold'] = int(S['gold'] * .75); S['hun'] = max(S['hun'], 40); E.clear(); EP.clear(); toast('Você desmaiou... acordou em um lugar seguro (-25% de ouro)', RD)
        if DG: leave_dg()
        else: S['x'], S['y'] = RS // 2 * TS + 16, (RS // 2 + 5) * TS
def use_pot(i):
    it = S['inv'][i]; b = IT[it['i']]
    if b['pt'] == 'hp': S['hp'] = min(Z.st['mhp'], S['hp'] + 60 + Z.st['mhp'] * .25)
    else: S['mp'] = min(Z.st['mmp'], S['mp'] + 60)
    del S['inv'][i]; beep(500, .15, .3, 'sin')
def quick_pot(t):
    for i, it in enumerate(S['inv']):
        if IT[it['i']].get('pt') == t: use_pot(i); return
    toast('Sem poção', RD)
def eat():
    for k, v in (('carne', 35), ('pao', 40), ('fruta', 15)):
        if S['mat'][k] > 0 and S['hun'] < 95: S['mat'][k] -= 1; S['hun'] = min(100, S['hun'] + v); S['hp'] = min(Z.st['mhp'], S['hp'] + 8); toast('Você comeu (%s)' % k, (255, 160, 60)); beep(400, .1, .2, 'sin'); return
    toast('Sem comida ou barriga cheia', RD)
def enter_dg(rx, ry):
    global DG
    Q['out'] = (S['x'], S['y'] + 40); DG = gen_dg(rx, ry); st = S['dg'].setdefault('%d,%d' % (rx, ry), dict(dead=[], boss=0)); E.clear(); PU.clear(); FIRES.clear()
    for m in DG['mobs']:
        if m['i'] not in st['dead']: E.append(new_mob(m['k'], m['x'], m['y'], .8, m['i']))
    S['x'], S['y'] = DG['sp']; Z.zone, Z.zt = 'Masmorra Sombria', 200; beep(150, .5, .4, 'sin')
def leave_dg():
    global DG
    DG = None; S['x'], S['y'] = Q['out']; Q['out'] = None; E.clear(); PU.clear(); EP.clear(); Z.zone, Z.zt = 'Mundo Aberto', 150
def new_mob(k, x, y, dgf, di=None, lead=None):
    m = MOB[k]; hp = m['hp'] * (1 + dgf * .4 + .03 * S['lv']) * CFG['dif']
    return dict(k=k, x=x, y=y, hp=hp, mh=hp, sz=m['sz'], cd=60, fz=0, bn=0, kx=0, ky=0, fl=0, wa=random.uniform(0, 6.28), ag=0, wind=0, f=0.0, di=di, lead=lead, fr=1, bt=0)
def night(): return clampf(.5 - math.sin(6.283 * (S['t'] / 21600 % 1)) * .9, 0, 1)
def clampf(v, a, b): return max(a, min(b, v))
def spawn():
    if DG: return
    n = night(); hos = sum(1 for e in E if MOB[e['k']]['md'] == 'hos'); pas = len(E) - hos
    a = random.uniform(0, 6.283); r = random.uniform(430, 650); x, y = S['x'] + math.cos(a) * r, S['y'] + math.sin(a) * r; t = tile(int(x // TS), int(y // TS))
    if t in SOL or t == 0 or near_village(x, y) or any(math.hypot(x - f['x'], y - f['y']) < 260 for f in FIRES): return
    des = t in (5, 6); dgf = math.hypot(x, y) / 1400
    tb = ([('coelho', 4), ('javali', 2), ('slime', 2)] if not des else [('escorpiao', 3), ('coelho', 1)]) if n < .35 else ([('goblin', 3), ('lobo', 3), ('ghoul', 2), ('slime', 1)] if not des else [('escorpiao', 2), ('ghoul', 3), ('espectro', 2)])
    if dgf > 1.4 and n >= .35: tb += [('espectro', 2), ('ghoul', 2)]
    k = random.choices([a for a, _ in tb], [w for _, w in tb])[0]
    if MOB[k]['md'] == 'hos' and hos >= 3 + int(n * 9): return
    if MOB[k]['md'] != 'hos' and pas >= 5: return
    cnt = random.randint(2, 4) if k in ('goblin', 'lobo') else random.randint(1, 2) if k == 'coelho' else 1; ld = None
    for i in range(cnt):
        m = new_mob(k, x + random.uniform(-30, 30), y + random.uniform(-30, 30), dgf, None, ld)
        if col(m['x'], m['y'], 8): continue
        ld = ld or m; E.append(m)
def mob_ai(e, dt):
    m = MOB[e['k']]; dx, dy = S['x'] - e['x'], S['y'] - e['y']; d = math.hypot(dx, dy) or 1; e['cd'] = max(0, e['cd'] - dt); e['fl'] = max(0, e['fl'] - dt); n = night(); e['bt'] += dt
    if e['bn'] > 0:
        e['bn'] -= dt
        if Q['fr'] % 20 == 0: e['hp'] -= Z.st['atk'] * .15; burst(e['x'], e['y'] - 10, 3, (255, 150, 40), 2, 16)
        if e['hp'] <= 0: kill(e); return
    fire = next((f for f in FIRES if math.hypot(e['x'] - f['x'], e['y'] - f['y']) < 150), None)
    if e['fz'] > 0: e['fz'] -= dt
    elif fire and m['md'] != 'flee':
        a = math.atan2(e['y'] - fire['y'], e['x'] - fire['x']); mv(e, math.cos(a) * m['sp'] * dt, math.sin(a) * m['sp'] * dt, e['sz'] * .7)
    elif e['wind'] > 0:
        e['wind'] -= dt
        if e['wind'] <= 0:
            if d < e['sz'] + 30: hurt_p(m['dm'] * (1 + math.hypot(e['x'], e['y']) / 1400 * .3) * CFG['dif'])
            e['cd'] = 70; e['kx'], e['ky'] = dx / d * 6, dy / d * 6
    else:
        if m['md'] == 'hos' and d < 270 + n * 110: e['ag'] = 1
        if m['md'] == 'flee' and d < 180: e['ag'] = 1
        if d > 720: e['ag'] = 0
        if e['ag'] and m['md'] == 'flee': a = math.atan2(-dy, -dx); mv(e, math.cos(a) * m['sp'] * dt, math.sin(a) * m['sp'] * dt, e['sz'] * .7); e['fr'] = 1 if -dx > 0 else -1
        elif e['ag']:
            if e['k'] == 'boss' and e['bt'] > 150: e['bt'] = 0; [EP.append(dict(x=e['x'], y=e['y'], vx=math.cos(k * .5) * 3, vy=math.sin(k * .5) * 3, l=140, dm=14)) for k in range(13)]; Z.shk = 6
            if d > e['sz'] + 22: mv(e, dx / d * m['sp'] * dt, dy / d * m['sp'] * dt, e['sz'] * .7); e['f'] += dt * .15
            elif e['cd'] <= 0 and m['dm']: e['wind'] = 22
            e['fr'] = 1 if dx > 0 else -1
        else:
            ld = e['lead']
            if ld and ld in E and dist(ld, e) > 90: a = math.atan2(ld['y'] - e['y'], ld['x'] - e['x']); mv(e, math.cos(a) * m['sp'] * .6 * dt, math.sin(a) * m['sp'] * .6 * dt, e['sz'] * .7); e['f'] += dt * .1
            else:
                if Q['fr'] % 100 == 0: e['wa'] += random.uniform(-2, 2)
                if hs(e['x'] // 40, Q['fr'] // 200, 1) > .4: mv(e, math.cos(e['wa']) * .35 * dt, math.sin(e['wa']) * .35 * dt, e['sz'] * .7); e['f'] += dt * .08; e['fr'] = 1 if math.cos(e['wa']) > 0 else -1
    mv(e, e['kx'] * dt, e['ky'] * dt, e['sz'] * .7); e['kx'] *= .85; e['ky'] *= .85
    if not DG and d > 950: E.remove(e)
def gather():
    tx, ty = int(S['x'] // TS), int(S['y'] // TS); best = None
    for j in range(-1, 2):
        for i in range(-1, 2):
            t = tile(tx + i, ty + j)
            if t in (3, 4, 13):
                d = math.hypot((tx + i) * TS + 16 - S['x'], (ty + j) * TS + 16 - S['y'])
                if d < 54 and (best is None or d < best[0]): best = (d, tx + i, ty + j, t)
    if not best: return False
    _, x, y, t = best
    if S['t'] - Q['dep'].get((x, y), -99999) < 10800: toast('Recurso esgotado, volte mais tarde', RD); return True
    Q['dep'][(x, y)] = S['t']; q = 1 + (random.random() < Z.st['gath'])
    k = 'madeira' if t == 4 else 'pedra' if t == 3 else 'fruta'
    S['mat'][k] += q + (t == 13); toast('+%d %s' % (q + (t == 13), k), (255, 200, 120)); burst(x * TS + 16, y * TS + 16, 10, (160, 200, 120), 3, 22, 0, .1, 3); beep(300, .07, .25); return True
def npcs():
    v = VIL(int(S['x'] // TS) // RS, int(S['y'] // TS) // RS)
    if not v: return []
    if v not in Q['nc']:
        r = random.Random(v[0] * 31 + v[1]); cs = lambda: dict(race=r.choice(RK), skin=r.choice(PAL['sk']), hr=r.choice(PAL['hr']), ou=r.choice(PAL['ou']))
        st = [r.choice([i for i, b in enumerate(IT) if b['t'] != 'p' and b['r'] <= 1]) for _ in range(5)]
        Q['nc'][v] = [dict(k='mercador', x=(v[0] + 2) * TS, y=(v[1] - 2) * TS, o=cs(), stock=st), dict(k='curandeira', x=(v[0] - 2) * TS, y=(v[1] + 2) * TS, o=cs()), dict(k='anciao', x=(v[0] + 5) * TS, y=(v[1] + 6) * TS, o=cs())]
    return Q['nc'][v]
TIPS = ['A noite traz criaturas piores. Acenda uma fogueira (C) e fique por perto.', 'Masmorras escondem Vasos de Djinn. Procure as ruínas de pedra.', 'Coelhos e javalis dão carne. Coma (H) antes que a fome o enfraqueça.', 'Gaste pontos na Árvore de Habilidades. Cada ramo muda seu estilo.']
def interact():
    if DG:
        if tile(int(S['x'] // TS), int(S['y'] // TS)) == 22: leave_dg(); return
        for c in DG['chests']:
            if c['id'] not in S['op'] and math.hypot(c['x'] - S['x'], c['y'] - S['y']) < 40: open_chest(c['id'], c['x'], c['y'], 2); return
        return
    for n in npcs():
        if math.hypot(n['x'] - S['x'], n['y'] - S['y']) < 60:
            if n['k'] == 'mercador': Z.mode, Z.tab, Z.shop = 'menu', 'shop', n
            elif n['k'] == 'curandeira': S['hp'], S['mp'] = Z.st['mhp'], Z.st['mmp']; toast('A curandeira restaurou sua vida e Magoi.', (110, 232, 110)); burst(S['x'], S['y'] - 20, 30, (110, 232, 110), 3, 40)
            else: toast(random.choice(TIPS), Y)
            return
    tx, ty = int(S['x'] // TS), int(S['y'] // TS)
    for j in range(-1, 2):
        for i in range(-1, 2):
            if tile(tx + i, ty + j) == 11: rx, ry = (tx + i) // RS, (ty + j) // RS; enter_dg(rx, ry); return
    if not gather(): toast('Nada para fazer aqui')
def open_chest(cid, x, y, bonus=0):
    S['op'].append(cid); dgf = math.hypot(x, y) / 1400 + bonus
    for _ in range(2 + (random.random() < .4)): PU.append(dict(k='i', v=roll_item(Z.st['luck'], dgf), x=x + random.uniform(-20, 20), y=y + random.uniform(8, 24), t=0))
    PU.append(dict(k='g', v=round(random.uniform(20, 60) * (1 + dgf)), x=x, y=y + 20, t=0)); toast('Baú aberto!', Y); burst(x, y, 24, (252, 238, 9), 4, 36); beep(400, .3, .3, 'sin')

# ---------------------------------------------------------------- atualização
def update(dt):
    Z.t += dt; Q['fr'] += 1; S['t'] += dt; st = Z.st = stats(); k = pg.key.get_pressed()
    ix = (k[pg.K_d] or k[pg.K_RIGHT]) - (k[pg.K_a] or k[pg.K_LEFT]); iy = (k[pg.K_s] or k[pg.K_DOWN]) - (k[pg.K_w] or k[pg.K_UP]); Q['mvg'] = bool(ix or iy)
    wet = tile(int(S['x'] // TS), int(S['y'] // TS)) == 0
    if Q['mvg']:
        l = math.hypot(ix, iy); mv(S, ix / l * st['spd'] * (.55 if wet else 1) * dt, iy / l * st['spd'] * (.55 if wet else 1) * dt, 7); Q['wf'] += dt * .16
        if wet and Q['fr'] % 6 == 0: burst(S['x'], S['y'], 2, (190, 230, 255), 1.5, 18, 0, .05)
    for r in range(8, 400, 8):
        if not col(S['x'], S['y'], 7): break
        for a in range(0, 63, 5):
            x, y = S['x'] + math.cos(a / 10) * r, S['y'] + math.sin(a / 10) * r
            if not col(x, y, 7): S['x'], S['y'] = x, y; break
        else: continue
        break
    mx, my = Z.mp; Q['face'] = math.atan2(my - H / 2 + 20, mx - W / 2)
    if pg.mouse.get_pressed()[0] and Z.mode == 'play' or k[pg.K_SPACE]: attack()
    Q['ac'] -= dt; Q['sw'] = max(0, Q['sw'] - dt); Q['au'] -= dt; Q['inv'] -= dt; Z.shk = max(0, Z.shk - .5 * dt); Q['cd'] = [c - dt for c in Q['cd']]
    S['mp'] = min(st['mmp'], S['mp'] + .07 * dt * st['mpreg']); S['hun'] = max(0, S['hun'] - .0035 * dt * st['hung'])
    if S['hun'] > 30: S['hp'] = min(st['mhp'], S['hp'] + .012 * dt)
    if S['hun'] <= 0: S['hp'] -= .03 * dt; (hurt_p(0) if S['hp'] <= 0 else None)
    if S['hun'] < 25 and Q['fr'] % 900 == 0: toast('Você está com fome! Coma (H).', (255, 160, 60))
    for f in FIRES[:]:
        f['l'] -= dt
        if f['l'] <= 0: FIRES.remove(f)
        elif math.hypot(f['x'] - S['x'], f['y'] - S['y']) < 100: S['hp'] = min(st['mhp'], S['hp'] + .05 * dt)
    if not DG:
        if Q['fr'] % 80 == 0 or (len(E) < 4 and Q['fr'] % 25 == 0): spawn()
        tx, ty = int(S['x'] // TS), int(S['y'] // TS)
        for j in range(-1, 2):
            for i in range(-1, 2):
                if chest_at(tx + i, ty + j) and '%d,%d' % (tx + i, ty + j) not in S['op'] and math.hypot((tx + i) * TS + 16 - S['x'], (ty + j) * TS + 16 - S['y']) < 30: open_chest('%d,%d' % (tx + i, ty + j), (tx + i) * TS + 16, (ty + j) * TS + 16)
        z = 'Vila' if near_village(S['x'], S['y']) else ('Mundo Aberto' if True else '')
        if z != Z.zone: Z.zone, Z.zt = z if z != 'Vila' else 'Vila de Sindria (zona segura)', 200
    else:
        for c in DG['chests']:
            if c['id'] not in S['op'] and math.hypot(c['x'] - S['x'], c['y'] - S['y']) < 30: open_chest(c['id'], c['x'], c['y'], 2)
    for e in E[:]: mob_ai(e, dt) if e in E else None
    for e in EP[:]:
        e['x'] += e['vx'] * dt; e['y'] += e['vy'] * dt; e['l'] -= dt
        if math.hypot(e['x'] - S['x'], e['y'] - S['y'] + 14) < 14: hurt_p(e['dm']); e['l'] = 0
        if e['l'] <= 0 or solid(e['x'], e['y']): EP.remove(e)
    for p in PR[:]:
        p['x'] += p['vx'] * dt; p['y'] += p['vy'] * dt; p['l'] -= dt
        if solid(p['x'], p['y']): p['l'] = 0
        for e in E[:]:
            if id(e) in p['hit'] or math.hypot(e['x'] - p['x'], e['y'] - 12 - p['y']) > e['sz'] + 8: continue
            hurt(e, p['d']); p['hit'].add(id(e))
            if not p['p']: p['l'] = 0; break
        if Q['fr'] % 2 == 0: PT.append([p['x'], p['y'], 0, 0, 14, 14, p['c'], 2, 1, 0])
        if p['l'] <= 0: PR.remove(p)
    for p in PU[:]:
        p['t'] += dt; d = math.hypot(p['x'] - S['x'], p['y'] - S['y'])
        if d < 80 and p['t'] > 15: a = math.atan2(S['y'] - p['y'], S['x'] - p['x']); p['x'] += math.cos(a) * 4 * dt; p['y'] += math.sin(a) * 4 * dt
        if d < 18 and p['t'] > 15:
            if p['k'] == 'g': S['gold'] += p['v']; popup(S['x'], S['y'] - 50, '+%d' % p['v'], Y); beep(900, .05, .2, 'sin')
            elif p['k'] == 'm': S['mat'][p['v']] += 1; popup(S['x'], S['y'] - 50, '+1 ' + p['v'], (255, 160, 120))
            elif len(S['inv']) < 30: S['inv'].append(p['v']); toast('Item: ' + IT[p['v']['i']]['n'], RC[IT[p['v']['i']]['r']]); beep(700, .1, .25, 'sin')
            else:
                if Q['fr'] % 120 == 0: toast('Inventário cheio', RD)
                continue
            PU.remove(p)
        elif p['t'] > 7200: PU.remove(p)
    for p in PT[:]:
        p[0] += p[2] * dt; p[1] += p[3] * dt; p[3] += p[9] * dt; p[4] -= dt
        if p[4] <= 0: PT.remove(p)
    for t in TXL[:]:
        t[1] -= .5 * dt; t[4] -= dt
        if t[4] <= 0: TXL.remove(t)
    for f in FXL[:]:
        f['life'] -= dt
        if f['life'] <= 0: FXL.remove(f)
        elif f['k'] == 'ic': burst(f['x'], f['y'], 1, f['c'], 1, 14)
    for q in TOAST[:]:
        q[2] -= dt
        if q[2] <= 0: TOAST.remove(q)
    if Z.zt > 0: Z.zt -= dt
    if Q['fr'] % 240 == 0: save()

# ---------------------------------------------------------------- desenho
def txt(t, p, f=FN, c=(225, 240, 250), a='l'):
    s = f.render(str(t), True, c); r = s.get_rect()
    if a == 'c': r.midtop = p
    elif a == 'r': r.topright = p
    else: r.topleft = p
    scr.blit(s, r); return r
def panel(r, c=Y):
    x, y, w, h = r; pg.draw.rect(scr, (9, 12, 20), r); pg.draw.rect(scr, sh(c, .3), r, 1)
    for sx, sy, a, b in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        pg.draw.line(scr, c, (sx, sy), (sx + 16 * a, sy), 2); pg.draw.line(scr, c, (sx, sy), (sx, sy + 16 * b), 2)
def btn(r, t, on=False, c=Y, dis=False):
    rc = pg.Rect(r); hov = rc.collidepoint(Z.mp) and not dis; cc = (70, 70, 70) if dis else c
    pg.draw.rect(scr, cc if (on or hov) else (14, 16, 24), rc); pg.draw.rect(scr, cc, rc, 1)
    txt(t, (rc.centerx, rc.centery - 8), FN, (0, 0, 0) if (on or hov) else cc, 'c'); return bool(Z.clk and not dis and rc.collidepoint(Z.clk))
def bar(x, y, w, h, v, c, lbl=''):
    pg.draw.rect(scr, (0, 0, 0), (x, y, w, h)); pg.draw.rect(scr, c, (x, y, int(w * clampf(v, 0, 1)), h)); pg.draw.rect(scr, sh(c, .5), (x, y, w, h), 1)
    if lbl: txt(lbl, (x + w - 4, y + (h - 14) // 2), FS, (255, 255, 255), 'r')
def draw_world(cx, cy):
    ents = []; x0, y0 = cx // TS, cy // TS
    for ty in range(y0, (cy + H) // TS + 2):
        for tx in range(x0, (cx + W) // TS + 2):
            t = tile(tx, ty); v = int(hs(tx, ty, 3) * 4); px, py = tx * TS - cx, ty * TS - cy
            if t == 0: img = TEX[0][(int(Z.t // 18) + tx + ty) % 4]
            else: img = TEX[t][v]
            scr.blit(img, (px, py))
            if t == 4: ents.append(((ty + 1) * TS, OB[('tree', v if hs(tx, ty, 8) < .85 else 3)] if S['t'] - Q['dep'].get((tx, ty), -99999) > 10800 else OB['stump'], (px + 16 - 19, py + TS - (56 if S['t'] - Q['dep'].get((tx, ty), -99999) > 10800 else 16))))
            elif t == 6: ents.append(((ty + 1) * TS, OB['cactus'], (px + 16 - 18, py + TS - 52)))
            elif t == 13: ents.append(((ty + 1) * TS, OB['bush0' if S['t'] - Q['dep'].get((tx, ty), -99999) < 10800 else 'bush'], (px + 2, py + 12)))
            elif t == 15: ents.append(((ty + 1) * TS, OB['well'], (px, py + 4)))
            elif t == 11 or t == 22:
                if Q['fr'] % 2 == 0 and random.random() < .1: PT.append([tx * TS + 16 + random.uniform(-8, 8), ty * TS + 16, 0, -.8, 40, 40, (200, 160, 255) if t == 11 else (252, 238, 9), 2, 1, 0])
            if not DG and chest_at(tx, ty): ents.append(((ty + 1) * TS, OB['chesto' if '%d,%d' % (tx, ty) in S['op'] else 'chest'], (px + 3, py + 14)))
    if DG:
        for c in DG['chests']: ents.append((c['y'] + 12, OB['chesto' if c['id'] in S['op'] else 'chest'], (c['x'] - cx - 15, c['y'] - cy - 4)))
    else:
        v = VIL(int(S['x'] // TS) // RS, int(S['y'] // TS) // RS)
        if v:
            for dx, dy in ((-4, -4), (4, -4), (-4, 4), (4, 4)): ents.append(((v[1] + dy + 1) * TS, OB['lamp'], ((v[0] + dx) * TS + 16 - 7 - cx, (v[1] + dy) * TS - 12 - cy)))
            for n in npcs():
                f = int(Z.t // 30) % 2; d = 0 if n['y'] < S['y'] + 30 else 1 if False else 0
                ents.append((n['y'], char(n['o'], 0, 0), (n['x'] - cx - 18, n['y'] - cy - 56 - f)))
    for f in FIRES: ents.append((f['y'], None, f))
    for e in E:
        m = MOB[e['k']]; img = mob_spr(e['k'], int(e['f']) % 2, e['fr'] < 0)
        if e['fl'] > 0: img = img.copy(); img.fill((140, 140, 140, 0), special_flags=pg.BLEND_RGB_ADD)
        elif e['fz'] > 0: img = img.copy(); img.fill((0, 60, 110, 0), special_flags=pg.BLEND_RGB_ADD)
        if e['wind'] > 0 and Q['fr'] % 4 < 2: img = img.copy(); img.fill((120, 0, 0, 0), special_flags=pg.BLEND_RGB_ADD)
        ents.append((e['y'], img, (e['x'] - cx - img.get_width() // 2, e['y'] - cy - img.get_height() + 6 + math.sin(Z.t * .12 + e['x']) * (1.5 if e['k'] in ('slime', 'espectro') else 0)), e))
    if Q['au'] > 0: scr.blit(glow(46, tuple(int(c * Q['au'] / 60) for c in Q['aucol'])), (S['x'] - cx - 46, S['y'] - cy - 40), special_flags=pg.BLEND_RGB_ADD)
    a = Q['face']; dr = 3 if math.cos(a) > 0 and abs(math.cos(a)) > abs(math.sin(a)) else 2 if abs(math.cos(a)) > abs(math.sin(a)) else 1 if math.sin(a) < 0 else 0
    eq = S['eq']; g = lambda k: eq[k]['i'] if eq.get(k) else None
    spr = char(S, dr, int(Q['wf']) % 4 if Q['mvg'] else 0, g('head'), g('neck'), g('feet')); px, py = S['x'] - cx, S['y'] - cy; bob = 0 if Q['mvg'] else int(math.sin(Z.t * .08) * 1)
    if not (Q['inv'] > 0 and Q['fr'] % 4 < 2):
        w = eq.get('w'); behind = math.sin(a) < -.5
        ents.append((S['y'] + (-.5 if behind else 0), spr, (px - 18, py - 56 + bob)))
        if w:
            it = IT[w['i']]; img = wsp(it['wt'], it['col']); sw = Q['sw'] / 14; th = 0; ang = a
            if sw > 0 and not it['pr']:
                if it['wt'] == 'spear': th = math.sin(sw * math.pi) * 18
                else: ang = a - 1.2 + 2.4 * (1 - sw)
            hx, hy = px + math.cos(a) * (8 + th), py - 24 + math.sin(a) * 5 + bob
            im2 = pg.transform.flip(img, False, True) if math.cos(ang) < 0 else img
            rot = pg.transform.rotate(im2, -math.degrees(ang)); ln = img.get_width() / 2 - 6
            rr = rot.get_rect(center=(hx + math.cos(ang) * ln, hy + math.sin(ang) * ln))
            ents.append((S['y'] + (-.6 if behind else .6), rot, rr.topleft))
    for en in sorted(ents, key=lambda q: q[0]):
        if en[1] is None:
            f = en[2]; fx, fy = f['x'] - cx, f['y'] - cy; R(scr, 0, 0, 0, 0, (0, 0, 0)) if False else None
            pg.draw.rect(scr, (92, 60, 34), (fx - 10, fy - 4, 20, 5)); pg.draw.rect(scr, (92, 60, 34), (fx - 5, fy - 8, 10, 5))
            for _ in range(5):
                hh = random.randint(8, 20); w2 = random.randint(3, 6); c = random.choice(((255, 200, 60), (255, 120, 30), (255, 230, 120)))
                pg.draw.rect(scr, c, (fx - w2 // 2 + random.randint(-4, 4), fy - 6 - hh, w2, hh))
        else:
            scr.blit(en[1], en[2])
            if len(en) > 3:
                e = en[3]
                if e['hp'] < e['mh']: bw = 30 if e['k'] != 'boss' else 80; pg.draw.rect(scr, (0, 0, 0), (en[2][0] + en[1].get_width() // 2 - bw // 2, en[2][1] - 6, bw, 5)); pg.draw.rect(scr, RD, (en[2][0] + en[1].get_width() // 2 - bw // 2, en[2][1] - 6, int(bw * max(0, e['hp'] / e['mh'])), 5))
    for p in PU:
        b = math.sin(Z.t * .1 + p['x']) * 3; x, y = p['x'] - cx, p['y'] - cy
        if p['k'] == 'g': scr.blit(OB['coin'], (x - 10, y - 14 + b))
        elif p['k'] == 'm': pg.draw.ellipse(scr, (200, 70, 70), (x - 7, y - 10 + b, 14, 9)); pg.draw.rect(scr, (240, 230, 220), (x + 4, y - 12 + b, 4, 3))
        else:
            scr.blit(glow(22, RC[IT[p['v']['i']]['r']]), (x - 22, y - 30 + b), special_flags=pg.BLEND_RGB_ADD); ic = icon(p['v']['i']); scr.blit(ic, (x - 16, y - 32 + b))
    for p in PR:
        x, y = p['x'] - cx, p['y'] - cy
        if p['o'] or p['p']: pg.draw.circle(scr, p['c'], (x, y), 5); pg.draw.circle(scr, (255, 255, 255), (x, y), 2)
        else: pg.draw.line(scr, (232, 214, 160), (x, y), (x - math.cos(p['a']) * 14, y - math.sin(p['a']) * 14), 2); pg.draw.circle(scr, p['c'], (x, y), 2)
    for e in EP: pg.draw.circle(scr, (200, 60, 255), (e['x'] - cx, e['y'] - cy), 5); pg.draw.circle(scr, (255, 255, 255), (e['x'] - cx, e['y'] - cy), 2)
    for f in FXL:
        a2 = f['life'] / f['max']; k = f['k']
        if k == 'sl':
            r = int(f['r']); s = cv(r * 2 + 8, r * 2 + 8); n = 14; pts = []
            for i in range(n + 1): aa = f['a'] - f['w'] + 2 * f['w'] * i / n; pts.append((r + 4 + math.cos(aa) * r, r + 4 + math.sin(aa) * r))
            for i in range(n, -1, -1): aa = f['a'] - f['w'] + 2 * f['w'] * i / n; pts.append((r + 4 + math.cos(aa) * r * .55, r + 4 + math.sin(aa) * r * .55))
            pg.draw.polygon(s, (*f['c'], int(170 * a2)), pts); scr.blit(s, (f['x'] - cx - r - 4, f['y'] - cy - r - 4))
        elif k == 'bo':
            pts = [(x - cx, y - cy) for x, y in f['pts']]; pg.draw.lines(scr, sh(f['c'], .6), False, pts, 7); pg.draw.lines(scr, f['c'], False, pts, 4); pg.draw.lines(scr, (255, 255, 255), False, pts, 2)
        elif k == 'rg':
            r = int(f['r'] * (1 - a2 * .75)); pg.draw.circle(scr, tuple(int(c * a2) for c in f['c']), (f['x'] - cx, f['y'] - cy), max(2, r), max(1, int(8 * a2)), draw_top_right=True, draw_top_left=True, draw_bottom_left=True, draw_bottom_right=True)
            scr.blit(glow(max(8, r), tuple(int(c * a2 * .5) for c in f['c'])), (f['x'] - cx - max(8, r), f['y'] - cy - max(8, r)), special_flags=pg.BLEND_RGB_ADD)
        else:
            x, y = f['x'] - cx, f['y'] - cy; h = 26 * min(1, (1 - a2) * 5); pg.draw.polygon(scr, (200, 240, 255), [(x - 5, y), (x, y - h), (x + 5, y)]); pg.draw.polygon(scr, (120, 200, 255), [(x, y - h), (x + 5, y), (x + 1, y)])
    for p in PT:
        f = p[4] / p[5]; x, y = int(p[0] - cx), int(p[1] - cy)
        if p[8]: scr.fill(tuple(int(c * f) for c in p[6]), (x, y, p[7], p[7]), special_flags=pg.BLEND_RGB_ADD)
        else: scr.fill(tuple(int(c * (.4 + .6 * f)) for c in p[6]), (x, y, p[7], p[7]))
    for t in TXL:
        sf = FN.render(t[2], True, (0, 0, 0)); scr.blit(sf, (t[0] - cx - sf.get_width() // 2 + 1, t[1] - cy + 1)); sf = FN.render(t[2], True, t[3]); sf.set_alpha(int(255 * min(1, t[4] / 15))); scr.blit(sf, (t[0] - cx - sf.get_width() // 2, t[1] - cy))
def lighting(cx, cy):
    n = .62 if DG else night() * .85
    if n < .03: return
    amb = tuple(int(255 - (255 - c) * n) for c in ((34, 38, 78) if not DG else (22, 24, 44))); L = pg.Surface((W, H)); L.fill(amb)
    def lt(x, y, r, c): L.blit(glow(r, c), (x - cx - r, y - cy - r), special_flags=pg.BLEND_RGB_ADD)
    lt(S['x'], S['y'] - 20, 170, (255, 235, 190))
    for f in FIRES: lt(f['x'], f['y'] - 10, 220 + random.randint(-8, 8), (255, 170, 80))
    for p in PR: lt(p['x'], p['y'], 60, p['c'])
    for e in E:
        if e['k'] == 'espectro': lt(e['x'], e['y'] - 10, 60, (255, 40, 100))
    if DG:
        for x, y in DG['lights']: lt(x, y, 150, (255, 180, 90))
    else:
        v = VIL(int(S['x'] // TS) // RS, int(S['y'] // TS) // RS)
        if v:
            for dx, dy in ((-4, -4), (4, -4), (-4, 4), (4, 4)): lt((v[0] + dx) * TS + 16, (v[1] + dy) * TS - 6, 160, (255, 220, 140))
    if Q['au'] > 0: lt(S['x'], S['y'] - 20, 140, tuple(int(c * Q['au'] / 60) for c in Q['aucol']))
    scr.blit(L, (0, 0), special_flags=pg.BLEND_RGB_MULT)
MM = cv(120, 120)
def hud():
    panel((12, 12, 300, 112)); txt(S['name'], (24, 18), FB, Y); txt('NV %d  %s' % (S['lv'], RACES[S['race']]['n']), (24, 44), FS, CY)
    st = Z.st; bar(24, 62, 270, 14, S['hp'] / st['mhp'], RD, '%d/%d' % (S['hp'], st['mhp'])); bar(24, 80, 270, 12, S['mp'] / st['mmp'], CY, '%d/%d' % (S['mp'], st['mmp']))
    bar(24, 96, 270, 8, S['hun'] / 100, (255, 150, 40)); bar(24, 108, 270, 4, S['xp'] / xpn(S['lv']), Y)
    for i in range(3):
        x = W // 2 - 105 + i * 74; d = S['eq'].get('d%d' % i); c = DJ[IT[d['i']]['dj']]['col'] if d else (40, 50, 70); r = pg.Rect(x, H - 82, 64, 64)
        pg.draw.rect(scr, (9, 12, 20), r); pg.draw.rect(scr, c, r, 2)
        if d:
            scr.blit(icon(d['i']), (x + 16, H - 66)); cd = Q['cd'][i]
            if cd > 0: pg.draw.rect(scr, (0, 0, 0, 0), r); s = pg.Surface((64, int(64 * cd / (DJ[IT[d['i']]['dj']]['cd'] * Z.st['cdr'])))); s.set_alpha(170); scr.blit(s, (x, H - 82))
        txt('QER'[i], (x + 4, H - 80), FS, Y)
    txt('Madeira %d  Pedra %d  Carne %d  Fruta %d  Pão %d   [H] comer  [G] poção  [C] fogueira' % tuple(S['mat'][k] for k in ('madeira', 'pedra', 'carne', 'fruta', 'pao')), (W // 2, H - 100), FS, (200, 215, 230), 'c')
    mm = Z.st.get('mm', 0); tx, ty = int(S['x'] // TS), int(S['y'] // TS)
    if Q['fr'] % 10 == 0:
        cl = {0: (44, 112, 180), 1: (224, 203, 143), 2: (74, 150, 66), 3: (112, 118, 130), 4: (40, 112, 48), 5: (214, 176, 100), 6: (46, 140, 76), 7: (156, 130, 94), 8: (176, 64, 48), 9: (228, 206, 160), 10: (122, 76, 40), 11: (200, 160, 255), 12: (122, 126, 134), 13: (58, 150, 62), 15: (90, 130, 190), 20: (90, 84, 110), 21: (20, 18, 30), 22: (252, 238, 9)}
        for y in range(-30, 30):
            for x in range(-30, 30): MM.fill(cl.get(tile(tx + x, ty + y), (0, 0, 0)), ((x + 30) * 2, (y + 30) * 2, 2, 2))
        for e in E: MM.fill((255, 0, 60), (60 + int((e['x'] - S['x']) / 16), 60 + int((e['y'] - S['y']) / 16), 3, 3))
        MM.fill(CY, (58, 58, 4, 4))
    scr.blit(MM, (W - 134, 12)); pg.draw.rect(scr, Y, (W - 134, 12, 120, 120), 2)
    ph = S['t'] / 21600 % 1; hh = int((ph * 24 + 6) % 24); txt('Dia %d  %02d:%02d  $%d' % (S['t'] // 21600 + 1, hh, int(ph * 24 * 60 % 60), S['gold']), (W - 14, 138), FN, Y, 'r')
    for i, q in enumerate(TOAST): s = FN.render(q[0], True, q[1]); pg.draw.rect(scr, (9, 12, 20), (12, H - 150 - i * 26, s.get_width() + 14, 24)); pg.draw.rect(scr, q[1], (12, H - 150 - i * 26, 3, 24)); scr.blit(s, (22, H - 146 - i * 26))
    if Z.zt > 0: txt(Z.zone, (W // 2, 24), FB, Y, 'c')
    for n in ([] if DG else npcs()):
        if math.hypot(n['x'] - S['x'], n['y'] - S['y']) < 60: txt('[F] ' + n['k'].capitalize(), (n['x'] - (S['x'] - W / 2), n['y'] - (S['y'] - H / 2) - 80), FS, Y, 'c')
    if Z.fl: s = pg.Surface((W, H)); s.fill(Z.fl[0]); s.set_alpha(Z.fl[1]); scr.blit(s, (0, 0)); Z.fl = (Z.fl[0], Z.fl[1] - 6) if Z.fl[1] > 6 else None

# ---------------------------------------------------------------- menus
def slot(r, it, sel=False, lbl=''):
    c = RC[IT[it['i']]['r']] if it else (40, 55, 80); rc = pg.Rect(r); pg.draw.rect(scr, (44, 40, 8) if sel else (11, 15, 22), rc); pg.draw.rect(scr, Y if sel else c, rc, 2 if sel else 1)
    if lbl: txt(lbl, (rc.x + 3, rc.y + 2), FS, (120, 140, 160))
    if it:
        ic = icon(it['i']); scr.blit(ic, ic.get_rect(center=rc.center))
        if it['up']: txt('+%d' % it['up'], (rc.right - 4, rc.bottom - 16), FS, Y, 'r')
    return bool(Z.clk and rc.collidepoint(Z.clk))
def sel_item(): return S['inv'][Z.sel[1]] if Z.sel and Z.sel[0] == 'i' and Z.sel[1] < len(S['inv']) else S['eq'].get(Z.sel[1]) if Z.sel and Z.sel[0] == 'e' else None
def ui_inv():
    panel((50, 100, 1000, 520)); sl = [('w', 'Arma'), ('head', 'Cabeça'), ('neck', 'Colar'), ('ring', 'Anel'), ('feet', 'Botas'), ('d0', 'Djinn I'), ('d1', 'Djinn II'), ('d2', 'Djinn III')]
    txt('EQUIPADO', (74, 116), FS, CY)
    for n, (k, lb) in enumerate(sl):
        if slot((74 + n % 2 * 76, 136 + n // 2 * 76, 68, 68), S['eq'].get(k), Z.sel == ('e', k), lb): Z.sel = ('e', k)
    txt('MOCHILA  %d/30' % len(S['inv']), (260, 116), FS, CY)
    for i in range(30):
        if slot((260 + i % 6 * 74, 136 + i // 6 * 74, 68, 68), S['inv'][i] if i < len(S['inv']) else None, Z.sel == ('i', i)): Z.sel = ('i', i)
    x = 724; it = sel_item()
    if not it: txt('Selecione um item', (x, 136), FN, (130, 150, 170)); return
    b = IT[it['i']]; m = 1 + .2 * it['up']; txt(b['n'] + (' +%d' % it['up'] if it['up'] else ''), (x, 130), FB, RC[b['r']]); txt('%s  %s' % (RN[b['r']], TN[b['t']]), (x, 160), FS, (150, 170, 190)); y = 186
    ls = []
    if b['t'] == 'w': ls += [('Dano', round(b['d'] * m)), ('Alcance', b['rg'] or 'Distância')]
    for k, v in b.get('st', {}).items(): ls.append((STN[k], '%d%%' % round(v * m * 100) if k == 'crit' else '%.1f' % (v * m) if k == 'spd' else round(v * m)))
    for a, v in ls: txt(a, (x, y), FN); txt(v, (x + 290, y), FN, Y, 'r'); y += 22
    if b['t'] == 'd': dj = DJ[b['dj']]; txt(dj['sub'], (x, y), FS, dj['col']); txt('Custo: %d Magoi' % dj['mp'], (x, y + 18), FS, CY); y += 44
    y += 10; inv = Z.sel[0] == 'i'; cost = round(b['p'] * .5 * (it['up'] + 1)); bt = pg.Rect
    if inv and btn((x, y, 140, 34), 'Usar' if b['t'] == 'p' else 'Equipar'):
        if b['t'] == 'p': use_pot(Z.sel[1]); Z.sel = None
        else:
            sl2 = 'w' if b['t'] == 'w' else b['sl'] if b['t'] == 'a' else next((k for k in ('d0', 'd1', 'd2') if not S['eq'].get(k)), 'd0')
            if b['t'] == 'd' and any(S['eq'].get(k) and S['eq'][k]['i'] == it['i'] for k in ('d0', 'd1', 'd2')): toast('Esse Djinn já está equipado', RD)
            else:
                old = S['eq'].get(sl2); S['eq'][sl2] = it; S['inv'].remove(it)
                if old: S['inv'].append(old)
                Z.sel = ('e', sl2); clampv(); beep(600, .1, .25, 'sin')
        return
    if not inv and btn((x, y, 140, 34), 'Remover'):
        if len(S['inv']) < 30: S['eq'][Z.sel[1]] = None; S['inv'].append(it); Z.sel = ('i', len(S['inv']) - 1); clampv()
        return
    if it['up'] < 5 and b['t'] != 'p' and btn((x + 150, y, 140, 34), 'Melhorar $%d' % cost, dis=S['gold'] < cost): S['gold'] -= cost; it['up'] += 1; clampv(); beep(800, .2, .3, 'sin')
    if inv and btn((x, y + 42, 140, 34), 'Vender $%d' % round(b['p'] * .4 * (1 + it['up'] * .5)), c=RD): S['gold'] += round(b['p'] * .4 * (1 + it['up'] * .5)); S['inv'].remove(it); Z.sel = None
def custom(o, x, y):
    for i, k in enumerate(RK):
        if btn((x + i * 118, y, 112, 32), RACES[k]['n'], o['race'] == k):
            o['race'] = k; r = RACES[k]; o['skin'], o['hr'], o['ou'] = r['sk'], r['hr'], r['ou']
            if o is S: clampv()
    txt(RACES[o['race']]['d'], (x, y + 40), FS, (160, 180, 200))
    for j, (k, lb) in enumerate((('skin', 'Pele'), ('hr', 'Cabelo'), ('ou', 'Roupa'))):
        key = 'sk' if k == 'skin' else k; pl = PAL[key]; idx = pl.index(tuple(o[k])) if tuple(o[k]) in pl else 0; yy = y + 70 + j * 42
        txt(lb, (x, yy + 7)); 
        if btn((x + 80, yy, 34, 32), '<'): o[k] = list(pl[(idx - 1) % len(pl)])
        for q, c in enumerate(pl): pg.draw.rect(scr, c, (x + 122 + q * 26, yy + 4, 22, 24)); pg.draw.rect(scr, Y if q == idx else (40, 40, 40), (x + 122 + q * 26, yy + 4, 22, 24), 2 if q == idx else 1)
        if btn((x + 122 + len(pl) * 26 + 4, yy, 34, 32), '>'): o[k] = list(pl[(idx + 1) % len(pl)])
    spr = char(o, int(Z.t // 50) % 4, int(Z.t // 8) % 4 if int(Z.t // 200) % 2 else 0, *(((S['eq'][k]['i'] if S['eq'].get(k) else None) for k in ('head', 'neck', 'feet')) if o is S else (None, None, None)))
    big = pg.transform.scale(spr, (spr.get_width() * 4, spr.get_height() * 4)); pg.draw.rect(scr, (14, 14, 22), (x + 480, y, 220, 270)); pg.draw.rect(scr, Y, (x + 480, y, 220, 270), 1); scr.blit(big, big.get_rect(midbottom=(x + 590, y + 262)))
def ui_char():
    panel((50, 100, 1000, 520)); custom(S, 80, 130); st = Z.st; x, y = 80, 360; txt('ATRIBUTOS', (x, y - 22), FS, CY)
    for i, (a, v) in enumerate((('Vida', st['mhp']), ('Magoi', st['mmp']), ('Ataque', st['atk']), ('Defesa', st['df']), ('Velocidade', '%.1f' % st['spd']), ('Crítico', '%d%%' % round(st['crit'] * 100)), ('Poder Djinn', 'x%.2f' % st['ves']), ('Fome', '%d%%' % S['hun']))):
        txt(a, (x + (i // 4) * 300, y + i % 4 * 24)); txt(v, (x + 240 + (i // 4) * 300, y + i % 4 * 24), FN, Y, 'r')
    txt('Nível %d   XP %d/%d   Pontos de habilidade: %d' % (S['lv'], S['xp'], xpn(S['lv']), S['pt']), (x, y + 110), FN, Y)
def sk_pos(bi, i): ox = (-60, 0, 60, -60, 60)[i]; return 190 + bi * 330 + 80 + (0 if i == 0 else ox), 200 + (0, 1, 1, 2, 2)[i] * 120
def ui_skills():
    panel((50, 100, 1000, 520)); txt('ÁRVORE DE HABILIDADES   Pontos: %d' % S['pt'], (74, 114), FB, Y); hov = None
    for bi, (nm, c, nodes) in enumerate(BR):
        txt(nm, (190 + bi * 330 + 80, 150), FN, c, 'c')
        for i, n in enumerate(nodes):
            x, y = sk_pos(bi, i)
            for r_ in n[6]:
                j = [q[0] for q in nodes].index(r_); x2, y2 = sk_pos(bi, j); pg.draw.line(scr, c if S['tr'].get(r_, 0) else (50, 56, 70), (x, y), (x2, y2), 3)
        for i, n in enumerate(nodes):
            x, y = sk_pos(bi, i); rk = S['tr'].get(n[0], 0); ok = all(S['tr'].get(r_, 0) > 0 for r_ in n[6]); rc = pg.Rect(x - 70, y - 26, 140, 52)
            pg.draw.rect(scr, sh(c, .35) if rk else (14, 17, 26), rc); pg.draw.rect(scr, c if ok else (60, 66, 80), rc, 2); txt(n[1], (x, y - 20), FS, (255, 255, 255) if ok else (110, 118, 130), 'c'); txt('%d/%d' % (rk, n[3]), (x, y + 2), FN, c, 'c')
            if rc.collidepoint(Z.mp): hov = n
            if Z.clk and rc.collidepoint(Z.clk) and ok and S['pt'] > 0 and rk < n[3]: S['tr'][n[0]] = rk + 1; S['pt'] -= 1; clampv(); beep(700, .15, .3, 'sin'); burst(x, y, 16, c, 3, 24)
    if hov: txt(hov[1] + ': ' + hov[2], (W // 2, 580), FN, Y, 'c')
def ui_shop():
    panel((50, 100, 1000, 520)); n = Z.shop; txt('MERCADOR   $%d' % S['gold'], (74, 114), FB, Y); y = 160
    for lb, k, c, p in (('Poção de Vida', 25, None, 25), ('Poção de Magoi', 26, None, 25)):
        txt(lb, (80, y + 8)); 
        if btn((380, y, 160, 32), 'Comprar $%d' % p, dis=S['gold'] < p or len(S['inv']) >= 30): S['gold'] -= p; S['inv'].append(dict(i=k, up=0))
        y += 40
    txt('Pão (+40 fome)', (80, y + 8))
    if btn((380, y, 160, 32), 'Comprar $12', dis=S['gold'] < 12): S['gold'] -= 12; S['mat']['pao'] += 1
    y += 50
    for i in n['stock']:
        b = IT[i]; price = round(b['p'] * 1.2); txt(b['n'], (80, y + 8), FN, RC[b['r']]); scr.blit(icon(i), (300, y - 6))
        if btn((380, y, 160, 32), 'Comprar $%d' % price, dis=S['gold'] < price or len(S['inv']) >= 30): S['gold'] -= price; S['inv'].append(dict(i=i, up=0)); beep(800, .1, .25)
        y += 40
    txt('MATERIAIS', (640, 130), FS, CY); txt('Madeira %d ($3)  Pedra %d ($4)  Carne %d ($5)' % (S['mat']['madeira'], S['mat']['pedra'], S['mat']['carne']), (640, 152), FN)
    if btn((640, 190, 300, 36), 'Vender madeira, pedra e carne'): S['gold'] += S['mat']['madeira'] * 3 + S['mat']['pedra'] * 4 + S['mat']['carne'] * 5; S['mat'].update(madeira=0, pedra=0, carne=0); beep(900, .1, .3)
def ui_cfg():
    panel((50, 100, 1000, 520)); x, y = 90, 140; txt('CONFIGURAÇÕES', (x, y), FB, Y); y += 50
    txt('Volume: %d%%' % round(CFG['vol'] * 100), (x, y + 8))
    if btn((x + 220, y, 40, 32), '-'): CFG['vol'] = max(0, round(CFG['vol'] - .1, 2))
    if btn((x + 270, y, 40, 32), '+'): CFG['vol'] = min(1, round(CFG['vol'] + .1, 2))
    y += 46; txt('Dificuldade: x%.1f (novos inimigos)' % CFG['dif'], (x, y + 8))
    if btn((x + 330, y, 40, 32), '-'): CFG['dif'] = max(.6, round(CFG['dif'] - .2, 1))
    if btn((x + 380, y, 40, 32), '+'): CFG['dif'] = min(2.0, round(CFG['dif'] + .2, 1))
    y += 46; txt('Tremor de tela', (x, y + 8))
    if btn((x + 220, y, 120, 32), 'Ligado' if CFG['shake'] else 'Desligado', bool(CFG['shake'])): CFG['shake'] = 0 if CFG['shake'] else 1
    y += 56
    if btn((x, y, 180, 36), 'Salvar jogo'): save(); toast('Jogo salvo', CY)
    if btn((x + 200, y, 180, 36), 'Tela cheia (F11)'): pg.display.toggle_fullscreen()
    if btn((x + 400, y, 180, 36), 'Salvar e sair', c=RD): save(); raise SystemExit
    txt('Controles: WASD mover | mouse/Espaço atacar | Q E R Djinn | F interagir | H comer | G poção | C fogueira | Tab menu', (x, y + 60), FS, (150, 170, 190))
def menu():
    s = pg.Surface((W, H)); s.set_alpha(210); s.fill((3, 5, 10)); scr.blit(s, (0, 0)); tabs = [('inv', 'Inventário'), ('ch', 'Personagem'), ('sk', 'Habilidades'), ('cf', 'Config')] + ([('shop', 'Loja')] if Z.shop else [])
    for i, (k, n) in enumerate(tabs):
        if btn((W // 2 - len(tabs) * 80 + i * 160, 40, 150, 40), n + ('  (%d)' % S['pt'] if k == 'sk' and S['pt'] else ''), Z.tab == k, CY if k != 'sk' else Y): Z.tab = k; Z.clk = None
    {'inv': ui_inv, 'ch': ui_char, 'sk': ui_skills, 'cf': ui_cfg, 'shop': ui_shop if Z.shop else ui_inv}[Z.tab]()
    txt('Tab/Esc fecha', (W // 2, 632), FS, (120, 140, 160), 'c')
D = dict(name='Aladdin', race='hu', skin=list(RACES['hu']['sk']), hr=list(RACES['hu']['hr']), ou=list(RACES['hu']['ou']))
def start_screen():
    scr.fill((6, 8, 14)); txt('MAGI RPG', (W // 2 + 3, 43), FT, RD, 'c'); txt('MAGI RPG', (W // 2, 40), FT, Y, 'c'); txt('Sobrevivência em mundo aberto. Crie seu herói.', (W // 2, 108), FN, CY, 'c')
    txt('Nome (digite):', (80, 150), FS, CY); pg.draw.rect(scr, (14, 16, 24), (80, 170, 260, 32)); pg.draw.rect(scr, Y, (80, 170, 260, 32), 1); txt(D['name'] + ('_' if Z.t // 25 % 2 else ''), (88, 178), FN, Y)
    custom(D, 80, 230)
    if btn((80, 560, 220, 44), 'Iniciar jornada', True): new_game(D)
    if os.path.exists(SAVE) and btn((320, 560, 220, 44), 'Continuar'): load()

def main():
    while True:
        dt = min(2.5, clk.tick(60) / 16.667); Z.clk = None; Z.mp = pg.mouse.get_pos(); Z.t += dt * (Z.mode != 'play')
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                if S: save()
                return
            if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1: Z.clk = ev.pos
            if ev.type == pg.KEYDOWN:
                k = ev.key
                if k == pg.K_F11: pg.display.toggle_fullscreen()
                if Z.mode == 'start':
                    if k == pg.K_BACKSPACE: D['name'] = D['name'][:-1]
                    elif ev.unicode.isprintable() and len(D['name']) < 14 and ev.unicode: D['name'] += ev.unicode
                elif Z.mode == 'menu':
                    if k in (pg.K_TAB, pg.K_ESCAPE): Z.mode = 'play'; Z.shop = None; clampv()
                elif Z.mode == 'play':
                    if k == pg.K_TAB: Z.mode, Z.tab = 'menu', 'inv'
                    elif k == pg.K_ESCAPE: Z.mode, Z.tab = 'menu', 'cf'
                    elif k == pg.K_q: cast(0)
                    elif k == pg.K_e: cast(1)
                    elif k == pg.K_r: cast(2)
                    elif k == pg.K_f: interact()
                    elif k == pg.K_h: eat()
                    elif k == pg.K_g: quick_pot('hp')
                    elif k == pg.K_c:
                        if S['mat']['madeira'] >= 5 and not DG: S['mat']['madeira'] -= 5; FIRES.append(dict(x=S['x'], y=S['y'] + 10, l=18000)); toast('Fogueira acesa: cura e afasta monstros', (255, 170, 80))
                        else: toast('Precisa de 5 madeira (fora de masmorras)', RD)
        if Z.mode == 'start': start_screen()
        else:
            if Z.mode == 'play':
                if Z.hs > 0: Z.hs -= 1; Z.st = stats()
                else: update(dt)
            sh_ = Z.shk * CFG['shake']; cx, cy = int(S['x'] - W / 2 + random.uniform(-sh_, sh_) * .5), int(S['y'] - H / 2 + 20 + random.uniform(-sh_, sh_) * .5)
            scr.fill((10, 12, 18)); draw_world(cx, cy); lighting(cx, cy); hud()
            if Z.mode == 'menu': menu()
        pg.display.flip()
if __name__ == '__main__':
    main(); pg.quit()
