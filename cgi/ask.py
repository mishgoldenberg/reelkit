# blender -b --factory-startup --python cgi/ask.py -- <out_dir> [frames=a-b|t=1.5,8,...] [samples=48]
# Photoreal "what happens when you ask an AI" reel in Cycles. Four stages far apart (the camera cuts between them):
#   DESK  laptop with the chat; the question as glass token tiles that grow columns of numbers; attention arcs between
#         every pair; candidate next tokens with odds; the gold "Paris" tile flying into the answer row; the answer streaming
#   AISLE a data-center aisle of server racks in light fog, data streaming down it
#   CHIP  the scanned circuit board (Poly Haven, CC0) with a chip covered in twinkling multiplications
# Moving tiles never touch anything: they travel above the rows and land in empty slots.
import bpy, math, random, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import *
from mathutils import Vector as V

OUT, opt = args(); LINES = timeline('ask'); sc = setup(int(opt.get('samples', 48))); world(sc, .3)
TEX = ROOT / 'cgi' / 'tex'
CYAN, GOLD = (.24, .9, 1.0), (1.0, .72, .25)

# ======================= DESK =======================
desk = mat('desk', (.02, .022, .028), .1, .22)
box(sc, 'desk', (1.6, .9, .04), (0, .15, -.02), desk)
alu = mat('alu', (.32, .34, .38), .92, .28)
lap = bpy.data.objects.new('laptop', None); sc.collection.objects.link(lap); lap.location = (0, .18, 0)
box(sc, 'lap_base', (.33, .23, .012), (0, 0, .006), alu, .004, lap)
hinge = bpy.data.objects.new('hinge', None); sc.collection.objects.link(hinge); hinge.parent = lap; hinge.location = (0, .115, .012); hinge.rotation_euler = (-.22, 0, 0)
box(sc, 'lid', (.33, .008, .215), (0, 0, .1075), alu, .003, hinge)
chat = bpy.data.materials.new('chat'); chat.use_nodes = True; cn = chat.node_tree.nodes; cl = chat.node_tree.links; cn.clear()
chat_imgs = [bpy.data.images.load(str(TEX / f'chat_{k}.png')) for k in range(8)]
chat_tex = cn.new('ShaderNodeTexImage'); chat_tex.image = chat_imgs[0]; chat_em = cn.new('ShaderNodeEmission'); chat_em.inputs[1].default_value = 1.4
co = cn.new('ShaderNodeOutputMaterial'); cl.new(chat_tex.outputs[0], chat_em.inputs[0]); cl.new(chat_em.outputs[0], co.inputs[0])
plane(sc, 'screen', .31, .198, (0, -.0045, .108), chat, (math.pi / 2, 0, 0), hinge)
area(sc, 'desk_key', (-.6, -.7, .8), (0, .1, .25), 40, .6, (1, .95, .9))
area(sc, 'desk_rim', (.7, .8, .6), (0, .1, .3), 45, .5, (.3, .8, 1))

# token tiles: question row (6) above the laptop, answer row (7) below it in front
glass = mat('glass', (.75, .92, 1.0), 0, .06, None, 0, .92)
TILE = V((.088, .016, .042))
def tile(i, pos, gold=False):
    g = bpy.data.objects.new(f'tile{i}', None); sc.collection.objects.link(g); g.location = pos
    m = mat(f'glass{i}', (1, .85, .5) if gold else (.75, .92, 1.0), 0, .06, GOLD if gold else CYAN, 0, .9)
    body = box(sc, f'tile{i}_b', tuple(TILE), (0, 0, 0), m, .006, g)
    t = image_emission(f'txt{i}', TEX / f'tok_{i:02d}.png', 3); plane(sc, f'tile{i}_t', .084, .042, (0, -TILE.y / 2 - .0012, 0), t, (math.pi / 2, 0, 0), g)
    return g, m, t
QZ, QY = .50, -.05
Q = [tile(i, V(((i - 2.5) * .1, QY, QZ))) for i in range(6)]
AZ, AY = .39, -.16
ANS = [tile(6 + i, V(((i - 3) * .1, AY, AZ)), gold=(i == 5)) for i in range(7)]       # i == 5 is " Paris"
# each question token grows a column of numbers (16 bars) under it
bars = []
rnd = random.Random(4)
bar_m = mat('bar', (0, 0, 0), 0, .5, CYAN, 4)
for i in range(6):
    for j in range(16):
        h = rnd.uniform(.004, .03)
        b = box(sc, f'bar{i}_{j}', (.0035, .004, h), (Q[i][0].location.x - .04 + j * .0053, QY, QZ - .036 - h / 2), bar_m)
        bars.append((b, i, h))
# attention arcs between every pair of question tiles
arc_m = mat('arc', (0, 0, 0), 0, .5, CYAN, 0); ARC = arc_m.node_tree.nodes['Principled BSDF']
arcs = []
for i in range(6):
    for j in range(i + 1, 6):
        cu = bpy.data.curves.new(f'arc{i}{j}', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .0011; cu.bevel_resolution = 2
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
        a, b = Q[i][0].location + V((0, 0, .026)), Q[j][0].location + V((0, 0, .026)); h = .03 + .018 * (j - i)
        for bp, pt, hd in ((sp.bezier_points[0], a, a + V((0, 0, h))), (sp.bezier_points[1], b, b + V((0, 0, h)))):
            bp.co = pt; bp.handle_left_type = bp.handle_right_type = 'FREE'; bp.handle_right = hd; bp.handle_left = hd
        o = bpy.data.objects.new(f'arc{i}{j}', cu); sc.collection.objects.link(o); o.data.materials.append(arc_m); arcs.append((o, i, j))
# candidate next tokens with odds, off to the right of the answer row (never in the row's way)
CAND = V((.46, AY - .02, .48))
cands = []
for i, pct in enumerate([92, 3, 1]):
    g = bpy.data.objects.new(f'cand{i}', None); sc.collection.objects.link(g); g.location = CAND + V((0, 0, -i * .05))
    plane(sc, f'cand{i}_t', .19, .04, (0, 0, 0), image_emission(f'candt{i}', TEX / f'cand_{i}.png', 3 if i == 0 else 1.2), (math.pi / 2, 0, 0), g)
    box(sc, f'cand{i}_bar', (.16 * pct / 100 + .002, .004, .006), (-.075 + (.16 * pct / 100) / 2, 0, -.022), mat(f'cbar{i}', (0, 0, 0), 0, .5, GOLD if i == 0 else CYAN, 6 if i == 0 else 2), 0, g)
    cands.append(g)

# ======================= AISLE =======================
AX = V((12, 0, 0))
rack_m = mat('rack', (.03, .033, .04), .85, .32)
floor_m = mat('dcfloor', (.03, .035, .045), .2, .18)
box(sc, 'dc_floor', (3.4, 16, .02), AX + V((0, 4, -.01)), floor_m)
led_cols = [mat('ledb', (0, 0, 0), 0, .5, (.25, .55, 1), 6), mat('ledw', (0, 0, 0), 0, .5, (.85, .95, 1), 5), mat('ledg', (0, 0, 0), 0, .5, (.3, 1, .55), 5)]
rnd = random.Random(9)
for side in (-1, 1):
    for k in range(9):
        c = AX + V((side * 1.0, k * 1.15, 1.0))
        box(sc, f'rk{side}{k}', (.7, 1.0, 2.0), c, rack_m, .01)
        for u in range(18):
            if rnd.random() < .8:
                box(sc, f'led{side}{k}{u}', (.004, rnd.uniform(.15, .7), .012), c + V((-side * .352, rnd.uniform(-.2, .2), -.85 + u * .1)), led_cols[rnd.randrange(3)])
for k in range(6):
    area(sc, f'dc_l{k}', AX + V((0, k * 1.8, 2.6)), AX + V((0, k * 1.8 + .01, 0)), 60, .5, (.8, .9, 1))
fog = box(sc, 'fog', (3.0, 15, 3.0), AX + V((0, 4, 1.5)), bpy.data.materials.new('fogm'))
fm = fog.data.materials[0]; fm.use_nodes = True; fnn = fm.node_tree.nodes; fnn.remove(fnn['Principled BSDF'])
vol = fnn.new('ShaderNodeVolumePrincipled'); vol.inputs['Density'].default_value = .012; vol.inputs['Color'].default_value = (.6, .8, 1, 1)
fm.node_tree.links.new(vol.outputs[0], fnn['Material Output'].inputs['Volume'])
st_m = mat('streak', (0, 0, 0), 0, .5, CYAN, 30)
stream = [box(sc, f'streak{i}', (.012, .22, .012), AX + V((0, 0, 1.3)), st_m) for i in range(14)]   # data flying down the aisle

# ======================= CHIP =======================
CX = V((24, 0, 0))
with bpy.data.libraries.load(str(ROOT / 'models/circuit_board/circuit_board_2k.blend')) as (src, dst): dst.objects = ['circuit_board']
board = dst.objects[0]; sc.collection.objects.link(board); board.location = CX
for im in bpy.data.images:
    if im.filepath.startswith('//textures'): im.filepath = str(ROOT / 'models/circuit_board/textures' / im.filepath.replace(chr(92), '/').split('/')[-1])
die = box(sc, 'die', (.09, .09, .012), CX + V((0, 0, .085)), mat('die', (.05, .05, .06), .7, .25), .003)
# a grid of tiny lights on the die: each one a multiplication, twinkling with time
gn_o = bpy.data.objects.new('mults', bpy.data.meshes.new('mults')); sc.collection.objects.link(gn_o)
pts = [(CX.x - .04 + i * .0027, CX.y - .04 + j * .0027, .0915) for i in range(30) for j in range(30)]
gn_o.data.from_pydata(pts, [], [])
gm = gn_o.modifiers.new('pts', 'NODES'); ngp = bpy.data.node_groups.new('mults', 'GeometryNodeTree'); gm.node_group = ngp
ngp.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry'); ngp.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
gi = ngp.nodes.new('NodeGroupInput'); go = ngp.nodes.new('NodeGroupOutput'); m2p = ngp.nodes.new('GeometryNodeMeshToPoints'); m2p.inputs['Radius'].default_value = .0006
mult_m = bpy.data.materials.new('mult'); mult_m.use_nodes = True; mn = mult_m.node_tree.nodes; ml = mult_m.node_tree.links; mn.clear()
tc = mn.new('ShaderNodeTexCoord'); nz = mn.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 900
tw = mn.new('ShaderNodeValue'); tw.name = 'time'; ml.new(tc.outputs['Object'], nz.inputs['Vector']); ml.new(tw.outputs[0], nz.inputs['W'])
rp = mn.new('ShaderNodeMapRange'); rp.inputs['From Min'].default_value = .55; rp.inputs['From Max'].default_value = .75; rp.inputs['To Max'].default_value = 40
ml.new(nz.outputs['Fac'], rp.inputs['Value']); em2 = mn.new('ShaderNodeEmission'); em2.inputs[0].default_value = (*CYAN, 1)
ml.new(rp.outputs[0], em2.inputs[1]); mo = mn.new('ShaderNodeOutputMaterial'); ml.new(em2.outputs[0], mo.inputs[0])
smt = ngp.nodes.new('GeometryNodeSetMaterial'); smt.inputs['Material'].default_value = mult_m
ngp.links.new(gi.outputs[0], m2p.inputs['Mesh']); ngp.links.new(m2p.outputs[0], smt.inputs['Geometry']); ngp.links.new(smt.outputs[0], go.inputs[0])
area(sc, 'chip_key', CX + V((-.35, -.4, .5)), CX + V((0, 0, .08)), 25, .4, (1, .95, .9))
area(sc, 'chip_rim', CX + V((.4, .3, .3)), CX + V((0, 0, .08)), 30, .3, (.3, .8, 1))

# ======================= camera =======================
cam = Cam(sc, 50, 2.4)
ROWQ = V((0, QY, QZ)); ROWA = V((0, AY, AZ)); SCREEN = V((0, .17, .13))
def shot(n, s, d):
    if n == 'send':   k = inout(p(s, .5, d)); return cam.fit(SCREEN.lerp(ROWQ, .3 + .4 * k), .2 + .16 * k, orbit(-.25 + .1 * k, .18), 1.0)
    if n == 'tokens': return cam.fit(ROWQ + V((0, 0, -.02)), .34, orbit(-.15 + s * .03, .1), 1.0)
    if n == 'datacenter': return AX + V((.15, -1.2 + s * .55, 1.45)), AX + V((0, 7, 1.15))
    if n == 'weights': return cam.fit(CX + V((0, 0, .09)), .07 - s * .004, orbit(-.4 + s * .05, .9), 1.0)
    if n == 'attention': return cam.fit(ROWQ + V((0, 0, .04)), .3, orbit(.2 - s * .05, .25), 1.0)
    if n == 'predict':                     # close on the candidates, then follow Paris into the sentence
        k = inout(p(s, 1.0, 2.3)); return cam.fit(CAND.lerp(ROWA + V((.12, 0, .03)), k), .16 + .24 * k, orbit(-.1, .1), 1.0)
    if n == 'loop': return cam.fit((ROWQ + ROWA) / 2, .36, orbit(.1 - s * .03, .12), 1.0)
    if n == 'why': return cam.fit(SCREEN, .17, orbit(-.05, .05), 1.0)
    a = .35 + s * .05; return cam.fit((ROWQ + ROWA) / 2 + V((0, .05, 0)), .42, orbit(a, .15), 1.0)
def subjects(n):
    return {'send': [SCREEN + V((0, 0, .05))], 'tokens': [ROWQ], 'datacenter': [], 'weights': [CX + V((0, 0, .09))], 'attention': [ROWQ],
            'predict': [CAND, ROWA], 'loop': [ROWA], 'why': [SCREEN], 'twist': [ROWQ], 'cta': [ROWQ]}[n]
check_framing(sc, cam, LINES, shot, subjects)

# ======================= per frame =======================
def show(g, on):                    # hide a group with everything in it (hiding a parent alone does not hide its children)
    g.hide_render = not on
    for c in g.children_recursive: c.hide_render = not on
order = [l['scene'] for l in LINES]
def apply(t):
    li, L, s, d, n, cp, ct = state(LINES, t, shot); cam.place(cp, ct)
    after = lambda name: li > order.index(name)
    # question tiles pop in on 'send', stay
    for i, (g, m, txt) in enumerate(Q):
        k = back(p(s, .9 + i * .12, 1.2 + i * .12)) if n == 'send' else 1.0
        g.scale = (max(k, .001),) * 3; show(g, not (n == 'send' and s < .9 + i * .12))
        m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = .9 if n in ('attention', 'loop') else .3   # faint inner glow
    # columns of numbers grow on 'tokens'
    for b, i, h in bars:
        k = ease(p(s, .5 + i * .2, 1.2 + i * .2)) if n == 'tokens' else 1.0 if after('tokens') else 0.0
        b.hide_render = k < .02; b.scale = (1, 1, max(k, .02)); b.location.z = QZ - .036 - h * k / 2
    # attention: arcs light up pair by pair, then all glow; they pulse again on every new token in 'loop'
    for o, i, j in arcs:
        idx = i * 6 + j
        on = (n == 'attention' and s > .4 + idx * .06) or n == 'loop' or (after('attention') and n in ('predict', 'twist', 'cta'))
        o.hide_render = not on
    pulse = (n == 'loop' and (s * 2.2) % 1 < .35)
    ARC.inputs['Emission Strength'].default_value = 3 + (6 if pulse else 0) if n in ('attention', 'loop') else 1.5
    # candidates on 'predict'; the gold Paris tile lifts off the top candidate and flies (over the row) into its slot
    for i, g in enumerate(cands):
        k = back(p(s, .3 + i * .15, .6 + i * .15)) if n == 'predict' else 0
        show(g, k >= .01); g.scale = (max(k, .01),) * 3
    # answer row: "The capital of France is" is already written when 'predict' starts (they pop in quickly), the gold
    # " Paris" tile lifts off the top candidate and arcs over the row into its empty slot, and in 'loop' the final "." follows
    for i, (g, m, txt) in enumerate(ANS):
        slot = V(((i - 3) * .1, AY, AZ)); g.location = slot; g.scale = (1, 1, 1)
        if i < 5:
            show(g, n == 'predict' or after('predict'))
            if n == 'predict': g.scale = (max(back(p(s, .1 + i * .06, .3 + i * .06)), .01),) * 3
        elif i == 5:
            show(g, (n == 'predict' and s > 1.0) or after('predict'))
            if n == 'predict':
                k = inout(p(s, 1.2, 2.4)); g.location = CAND.lerp(slot, k) + V((0, 0, .12 * math.sin(math.pi * k)))
                g.scale = (max(back(p(s, 1.0, 1.25)), .01),) * 3
        else:
            show(g, (n == 'loop' and s > 1.6) or after('loop'))
            if n == 'loop': g.scale = (max(back(p(s, 1.6, 1.85)), .01),) * 3
    # data streaming down the aisle
    for i, o in enumerate(stream):
        k = (t * .8 + i / len(stream)) % 1; o.location = AX + V(((i % 3 - 1) * .12, -1 + k * 11, 1.2 + (i % 4) * .12)); o.hide_render = n != 'datacenter'
    mult_m.node_tree.nodes['time'].outputs[0].default_value = t * 1.6
    # the chat screen: question only, then the answer streaming word by word during 'why'
    kk = int(clamp((s - .2) / 2.6) * 7) if n == 'why' else 7 if after('why') else 0
    chat_tex.image = chat_imgs[kk]

render(sc, OUT, opt, apply)
