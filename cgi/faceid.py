# blender -b models/marble_bust_01/marble_bust_01_2k.blend --python cgi/faceid.py -- <out_dir> [frames=a-b|t=1.5,8,...] [samples=64]
# Photoreal Face-unlock reel in Cycles (GPU/OptiX). The scanned marble bust (Poly Haven, CC0) is the face; the phone, the IR
# flood, 30,000 ray-traced dots, the depth contours, the two hologram face maps and the flat photo are built here. Camera, lights
# and effects are a pure function of time, keyed from the voice timeline in show/faceid.timing.js (show/build.py), so the 2D
# overlay (counter, captions, robot, share sheet: show3d.html?cfg=faceid in overlay mode) lines up frame for frame.
import bpy, bmesh, sys, json, math, random, pathlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = pathlib.Path(bpy.data.filepath).resolve().parents[2]
args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]; opt = dict(a.split('=', 1) for a in args[1:])
FPS = 30
T = json.loads((ROOT / 'show' / 'faceid.timing.js').read_text(encoding='utf-8').split('=', 1)[1])
LINES = T['lines']
clamp = lambda x, a=0., b=1.: min(b, max(a, x))
p = lambda t, a, b: clamp((t - a) / (b - a)) if b != a else float(t >= b)
ease = lambda x: 1 - (1 - x) ** 3
inout = lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
V = Vector

sc = bpy.context.scene
for o in list(sc.objects):
    if o.name != 'marble_bust_01': bpy.data.objects.remove(o, do_unlink=True)
bust = bpy.data.objects['marble_bust_01']
tex = ROOT / 'models' / 'marble_bust_01' / 'textures'
for im in bpy.data.images:
    if im.filepath.startswith('//textures'): im.filepath = str(tex / im.filepath.replace('\\', '/').split('/')[-1])   # (pathlib reads '//textures/..' as a network share)

# ---------- render settings ----------
sc.render.engine = 'CYCLES'
pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = d.type == 'OPTIX'
sc.cycles.device = 'GPU'; sc.cycles.samples = int(opt.get('samples', 64)); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'
sc.cycles.max_bounces = 6; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = FPS; sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .4
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

# ---------- world: studio HDRI for reflections, near-black to the camera ----------
w = bpy.data.worlds.new('studio'); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(str(ROOT / 'models/hdri/studio_small_09_1k.hdr'))
bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[1].default_value = .35
dark = nt.nodes.new('ShaderNodeBackground'); dark.inputs[0].default_value = (.004, .006, .01, 1)
lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader'); outw = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(env.outputs[0], bg.inputs[0]); nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0])
nt.links.new(bg.outputs[0], mix.inputs[1]); nt.links.new(dark.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], outw.inputs[0])

def mat(name, base=(.5, .5, .5), metal=0., rough=.5, emit=None, estr=0., alpha=1.):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    b.inputs['Alpha'].default_value = alpha
    return m

# floor: dark satin, catches a soft reflection of the bust
# (no floor: the bust floats in a dark studio void)

# ---------- lights ----------
def area(name, loc, look, energy, size, col):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (V(look) - V(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
key = area('key', (-.7, -.9, 1.0), (0, 0, .36), 55, .6, (1, .96, .92))
rim = area('rim', (.8, .7, .8), (0, 0, .38), 70, .5, (.25, .85, 1.0))
fill = area('fill', (.9, -.6, .3), (0, 0, .35), 8, .8, (.6, .7, 1.0))

# ---------- the face ----------
FACE = V((0, -.10, .40))                      # roughly the nose tip in world space
bust.data.materials[0].node_tree  # keep the scan material, add depth contours on top
bm = bust.data.materials[0]; nodes = bm.node_tree.nodes; links = bm.node_tree.links
outn = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL'); orig = outn.inputs['Surface'].links[0].from_socket
tc = nodes.new('ShaderNodeTexCoord'); sep = nodes.new('ShaderNodeSeparateXYZ'); links.new(tc.outputs['Object'], sep.inputs[0])
band = nodes.new('ShaderNodeMath'); band.operation = 'MULTIPLY'; band.inputs[1].default_value = 260; links.new(sep.outputs['Y'], band.inputs[0])
fr = nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'; links.new(band.outputs[0], fr.inputs[0])
line = nodes.new('ShaderNodeMapRange'); line.inputs['From Min'].default_value = 0; line.inputs['From Max'].default_value = .12
line.inputs['To Min'].default_value = 1; line.inputs['To Max'].default_value = 0; line.inputs['From Max'].default_value = .16; links.new(fr.outputs[0], line.inputs['Value'])
sweep = nodes.new('ShaderNodeValue'); sweep.name = 'sweep'                    # 0..1: contour reveal, top to bottom
zmap = nodes.new('ShaderNodeMapRange'); zmap.inputs['From Min'].default_value = .52; zmap.inputs['From Max'].default_value = .18
links.new(sep.outputs['Z'], zmap.inputs['Value'])
lt = nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; links.new(zmap.outputs[0], lt.inputs[0]); links.new(sweep.outputs[0], lt.inputs[1])
mk = nodes.new('ShaderNodeMath'); mk.operation = 'MULTIPLY'; links.new(line.outputs[0], mk.inputs[0]); links.new(lt.outputs[0], mk.inputs[1])
glow = nodes.new('ShaderNodeValue'); glow.name = 'glow'
mk2 = nodes.new('ShaderNodeMath'); mk2.operation = 'MULTIPLY'; links.new(mk.outputs[0], mk2.inputs[0]); links.new(glow.outputs[0], mk2.inputs[1])
em = nodes.new('ShaderNodeEmission'); em.inputs[0].default_value = (.1, .75, 1, 1); em.inputs[1].default_value = 5
mixs = nodes.new('ShaderNodeMixShader'); links.new(mk2.outputs[0], mixs.inputs[0]); links.new(orig, mixs.inputs[1]); links.new(em.outputs[0], mixs.inputs[2])
links.new(mixs.outputs[0], outn.inputs['Surface'])

# ---------- the phone ----------
def phone(name, loc, aim):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); g.location = loc
    g.rotation_euler = (V(aim) - V(loc)).to_track_quat('Y', 'Z').to_euler()     # local +Y (screen side) faces the face
    bpy.ops.mesh.primitive_cube_add(size=1); body = bpy.context.object; body.name = name + '_body'
    body.scale = (.0715, .0078, .147); bpy.ops.object.transform_apply(scale=True)
    bv = body.modifiers.new('round', 'BEVEL'); bv.width = .0075; bv.segments = 10; bv.limit_method = 'NONE'
    body.data.materials.append(mat('titanium', (.18, .19, .21), .95, .28)); body.parent = g
    for poly in body.data.polygons: poly.use_smooth = True
    bpy.ops.mesh.primitive_plane_add(size=1); scr = bpy.context.object; scr.name = name + '_screen'
    scr.scale = (.0665, .1415, 1); bpy.ops.object.transform_apply(scale=True)
    scr.rotation_euler = (math.pi / 2, 0, math.pi); scr.location = (0, .0040, 0); scr.parent = g   # image up = +Z, facing +Y, not mirrored
    m = bpy.data.materials.new(name + '_scr'); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links
    b = n['Principled BSDF']; b.inputs['Base Color'].default_value = (0, 0, 0, 1); b.inputs['Roughness'].default_value = .04
    b.inputs['Coat Weight'].default_value = 1; b.inputs['Coat Roughness'].default_value = .02
    tl = n.new('ShaderNodeTexImage'); tl.image = bpy.data.images.load(str(ROOT / 'cgi/tex/lock.png'))
    th = n.new('ShaderNodeTexImage'); th.image = bpy.data.images.load(str(ROOT / 'cgi/tex/home.png'))
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.name = 'unlock'
    sock = lambda col, ident: next(x for x in col if x.identifier == ident)          # the color sockets, not the float ones with the same name
    L.new(tl.outputs[0], sock(mx.inputs, 'A_Color')); L.new(th.outputs[0], sock(mx.inputs, 'B_Color'))
    L.new(sock(mx.outputs, 'Result_Color'), b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.6
    br = n.new('ShaderNodeValue'); br.name = 'bright'; br.outputs[0].default_value = 1.6; L.new(br.outputs[0], b.inputs['Emission Strength'])
    scr.data.materials.append(m)
    # the sensor pill and its projector dot
    bpy.ops.mesh.primitive_plane_add(size=1); pill = bpy.context.object                      # flat black capsule printed on the glass
    pill.scale = (.026, .0088, 1); bpy.ops.object.transform_apply(scale=True)
    pb = pill.modifiers.new('round', 'BEVEL'); pb.width = .0043; pb.segments = 10; pb.affect = 'VERTICES'
    pill.rotation_euler = (math.pi / 2, 0, math.pi); pill.location = (0, .00415, .0615); pill.parent = g
    pill.data.materials.append(mat('pill', (0, 0, 0), 0, .2))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.0010); proj = bpy.context.object; proj.location = (.007, .0044, .0615); proj.parent = g
    pm = mat('proj', (0, 0, 0), 0, .3, (1, .1, .35), 0); proj.data.materials.append(pm)
    return g, scr, m, proj, pm

PH_LOC = V((.11, -.31, .25)); ph, scr, scrm, proj, projm = phone('phone', PH_LOC, FACE)   # held low and to the side, tilted up: never between a camera and the face
bpy.context.view_layer.update()
PROJ = proj.matrix_world.translation.copy()

# ---------- IR flood light (shown as deep red-violet: the real light is invisible) ----------
fl = bpy.data.lights.new('flood', 'SPOT'); fl.spot_size = math.radians(40); fl.spot_blend = .8; fl.color = (1, .12, .4); fl.shadow_soft_size = .01
flo = bpy.data.objects.new('flood', fl); sc.collection.objects.link(flo); flo.location = PROJ + (FACE - PROJ).normalized() * .02
flo.rotation_euler = (FACE - PROJ).to_track_quat('-Z', 'Y').to_euler()

# ---------- 30,000 dots, ray-traced from the projector onto the face ----------
dg = bpy.context.evaluated_depsgraph_get(); be = bust.evaluated_get(dg); me = be.to_mesh()
bmx = bmesh.new(); bmx.from_mesh(me); bmx.transform(bust.matrix_world); tree = BVHTree.FromBMesh(bmx)
rnd = random.Random(7); hits = []
axis = (FACE - PROJ).normalized(); up = V((0, 0, 1)); right = axis.cross(up).normalized(); up = right.cross(axis).normalized()
for i in range(30000):                                    # fixed pseudo-random pattern inside a cone (like the real projector)
    a = rnd.uniform(-1, 1) * math.radians(19); b = rnd.uniform(-1, 1) * math.radians(23)
    d = (axis + right * math.tan(a) + up * math.tan(b)).normalized()
    hit = tree.ray_cast(PROJ, d, 2.0)
    if hit[0] is not None: hits.append((hit[0] + hit[1] * .0007, i / 30000))
dm = bpy.data.meshes.new('dots'); dm.from_pydata([h[0] for h in hits], [], [])
order = dm.attributes.new('order', 'FLOAT', 'POINT'); order.data.foreach_set('value', [h[1] for h in hits])
dots = bpy.data.objects.new('dots', dm); sc.collection.objects.link(dots)
gn = dots.modifiers.new('points', 'NODES'); ng = bpy.data.node_groups.new('dots', 'GeometryNodeTree'); gn.node_group = ng
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry'); ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
N = ng.nodes; Lk = ng.links; gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
m2p = N.new('GeometryNodeMeshToPoints'); m2p.inputs['Radius'].default_value = .00032
attr = N.new('GeometryNodeInputNamedAttribute'); attr.data_type = 'FLOAT'; attr.inputs['Name'].default_value = 'order'
shown = N.new('ShaderNodeValue'); shown.name = 'shown'
cmp = N.new('FunctionNodeCompare'); cmp.data_type = 'FLOAT'; cmp.operation = 'GREATER_THAN'
Lk.new(attr.outputs['Attribute'], cmp.inputs['A']); Lk.new(shown.outputs[0], cmp.inputs['B'])
dl = N.new('GeometryNodeDeleteGeometry'); dl.domain = 'POINT'
sm = N.new('GeometryNodeSetMaterial'); dmat = mat('dot', (0, 0, 0), 0, .5, (1, .16, .42), 0); dmat.name = 'dotmat'; sm.inputs['Material'].default_value = dmat
Lk.new(gi.outputs[0], m2p.inputs['Mesh']); Lk.new(m2p.outputs[0], dl.inputs['Geometry']); Lk.new(cmp.outputs[0], dl.inputs['Selection'])
Lk.new(dl.outputs[0], sm.inputs['Geometry']); Lk.new(sm.outputs[0], go.inputs[0])
bmx.free(); be.to_mesh_clear()

# ---------- two hologram face maps (saved vs now), side by side, never overlapping ----------
def holo(name, loc, col):
    o = bust.copy(); o.data = bust.data.copy(); o.name = name; sc.collection.objects.link(o)
    o.location = loc; o.scale = (.62, .62, .62); o.rotation_euler = (0, 0, 0)
    o.modifiers.clear(); dec = o.modifiers.new('dec', 'DECIMATE'); dec.ratio = .05
    wf = o.modifiers.new('wire', 'WIREFRAME'); wf.thickness = .0012; wf.use_replace = True
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; n.clear()
    e = n.new('ShaderNodeEmission'); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = 0
    o_ = n.new('ShaderNodeOutputMaterial'); m.node_tree.links.new(e.outputs[0], o_.inputs[0])
    o.data.materials.clear(); o.data.materials.append(m); return o, e
HSAVED, hs_e = holo('saved', V((.70, .35, .05)), (.49, 1, .66))
HNOW, hn_e = holo('now', V((.92, .35, .05)), (.24, .9, 1))

# ---------- the flat photo (stage on the right, far from everything else) ----------
PHOTO = V((2.2, 0, .36))
bpy.ops.mesh.primitive_plane_add(size=1, location=PHOTO); card = bpy.context.object; card.scale = (.15, .2, 1); card.rotation_euler = (math.pi / 2, 0, 0)
pmt = bpy.data.materials.new('photo'); pmt.use_nodes = True; pn = pmt.node_tree.nodes
ti = pn.new('ShaderNodeTexImage'); ph_png = ROOT / 'cgi/tex/photo.png'
if ph_png.exists(): ti.image = bpy.data.images.load(str(ph_png)); pmt.node_tree.links.new(ti.outputs[0], pn['Principled BSDF'].inputs['Base Color'])
pn['Principled BSDF'].inputs['Roughness'].default_value = .45; card.data.materials.append(pmt)
ph2, scr2, scrm2, proj2, projm2 = phone('phone2', PHOTO + V((.03, -.34, -.03)), PHOTO)
bpy.context.view_layer.update(); P2 = proj2.matrix_world.translation.copy()
fdots = []
rnd2 = random.Random(3)
for i in range(2600):                                       # on a flat card the dots land in one flat sheet
    x = rnd2.uniform(-.07, .07); z = rnd2.uniform(-.095, .095); fdots.append(PHOTO + V((x, -.0015, z)))
fm = bpy.data.meshes.new('fdots'); fm.from_pydata(fdots, [], []); fd = bpy.data.objects.new('fdots', fm); sc.collection.objects.link(fd)
fg = fd.modifiers.new('points', 'NODES'); fg.node_group = ng.copy(); fg.node_group.nodes['shown'].outputs[0].default_value = 1.0
fo = fm.attributes.new('order', 'FLOAT', 'POINT'); fo.data.foreach_set('value', [i / 2600 for i in range(2600)])

# ---------- camera ----------
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 55; cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.2; cd.sensor_width = 36
# Shots are described by what they must show, not by guessed coordinates: a subject (center + radius) seen from a direction.
# The camera distance comes from the lens: the subject's diameter fills `fill` of the frame width (portrait, so width is the
# tight side). The overlay covers the top ~27% (counter) and bottom ~32% (captions, robot), so subjects are aimed a little
# low in 3D, which puts them in the clear band; check_framing() below reports anything that lands outside it.
HALF_W = math.tan(math.atan(18 / cd.lens)) * 9 / 16          # tan of half the horizontal field of view
def fit(center, radius, direction, fill=.62, lift=0.):
    dirn = V(direction).normalized(); dist = radius / (fill * HALF_W)
    return center - dirn * dist + V((0, 0, lift)), center
def orbit(a, elev=.12): return V((math.sin(a), math.cos(a), -elev))   # view direction going round the subject at angle a
HEAD = (FACE + V((0, .05, .02)), .13)                                  # the head: center, radius
PHONE = (PH_LOC, .085)
HOLOS = ((HSAVED.location + HNOW.location) / 2 + V((0, 0, .17)), .24)
CARD = (PHOTO + V((0, -.10, 0)), .17)                                  # photo card with its phone in front
def shot(n, s, d):
    if n == 'glance':                                                  # from behind the phone's shoulder: face + phone
        k = inout(p(s, .4, d)); c = HEAD[0].lerp(PH_LOC, .5)
        return fit(c, .2, orbit(-.35 + .15 * k, .18), 1.0)
    if n == 'flood': return fit(HEAD[0].lerp(PH_LOC, .3), .19, orbit(-.9 + s * .03, .1), 1.0)
    if n == 'dots': return fit(HEAD[0], HEAD[1], orbit(-.25 + s * .04, .08), 1.05)
    if n == 'depth': return fit(HEAD[0], HEAD[1], orbit(-.6 + s * .12, .1), 1.05)
    if n == 'compare': return fit(*HOLOS, orbit(s * .03, .05), 1.0)
    if n == 'photo': return fit(*CARD, orbit(-.45 + s * .03, .08), 1.0)
    if n == 'unlock':                                                  # onto the screen, from the face's side of the phone
        k = inout(p(s, 0, d)); nrm = (FACE - PH_LOC).normalized()
        return fit(PH_LOC, PHONE[1], -(nrm * .6 + V((.9 - .1 * k, 0, .25))), 1.05)  # well off to the side, so the head is never in the way
    return fit(HEAD[0], .2, orbit(.5 + s * .06, .12), .85)

def check_framing():                                                    # project each shot's subject; report it if it leaves the clear band
    from bpy_extras.object_utils import world_to_camera_view
    subj = {'glance': [HEAD[0], PH_LOC], 'flood': [HEAD[0]], 'dots': [HEAD[0]], 'depth': [HEAD[0]], 'compare': [HSAVED.location + V((0, 0, .17)), HNOW.location + V((0, 0, .17))],
            'photo': [PHOTO], 'unlock': [PH_LOC], 'twist': [HEAD[0]], 'cta': [HEAD[0]]}
    bad = []
    for L in LINES:
        for s in (0, (L['end'] - L['t0']) / 2, L['end'] - L['t0']):
            cp, ct = shot(L['scene'], s, L['end'] - L['t0']); cam.location = cp; cam.rotation_euler = (ct - cp).to_track_quat('-Z', 'Y').to_euler()
            bpy.context.view_layer.update()
            for q in subj[L['scene']]:
                v = world_to_camera_view(sc, cam, q)
                if not (.1 < v.x < .9 and .3 < v.y < .74): bad.append(f"{L['scene']}@{s:.1f}s ({v.x:.2f},{v.y:.2f})")
    print('FRAMING', 'ok' if not bad else bad)
def frame_state(t):
    li = 0
    for i, l in enumerate(LINES):
        if t >= l['t0'] - .05: li = i
    L = LINES[li]; s = t - L['t0']; d = L['end'] - L['t0']; n = L['scene']
    cp, ct = shot(n, max(s, 0), d)
    if li > 0 and s < .7 and n != 'photo':                                # the photo stage is a hard cut: a pan there crosses empty dark space
        P = LINES[li - 1]; pp, pt = shot(P['scene'], P['end'] - P['t0'], P['end'] - P['t0']); k = inout(clamp(s / .7)); cp = pp.lerp(cp, k); ct = pt.lerp(ct, k)
    return li, L, s, d, n, cp, ct

def apply(t):
    li, L, s, d, n, cp, ct = frame_state(t)
    cam.location = cp; cam.rotation_euler = (ct - cp).to_track_quat('-Z', 'Y').to_euler(); cd.dof.focus_distance = (ct - cp).length
    order = [l['scene'] for l in LINES]; at = lambda sc_: order.index(sc_)
    # IR flood: on in 'flood', a soft glow afterwards while scanning
    fl.energy = (16 * ease(p(s, .2, .8)) if n == 'flood' else 4.0 if n in ('dots', 'depth') else 0)
    projm.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 30 if n in ('flood', 'dots', 'depth') else 0
    # dots appear in 2.2 s, stay through 'depth', gone afterwards; strength fades while contours take over
    ng.nodes['shown'].outputs[0].default_value = ease(p(s, .2, 2.4)) if n == 'dots' else 1.0 if n in ('depth',) else 1.0 if n == 'twist' else 0.0
    dstr = 4 if n in ('dots', 'photo') else 4 * (1 - p(s, .4, 2.0)) + 1 if n == 'depth' else 2.5 if n == 'twist' else 0
    dmat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = dstr
    # depth contours sweep down the face in 'depth', stay faint later
    nodes['sweep'].outputs[0].default_value = ease(p(s, .2, 2.6)) if n == 'depth' else 1.0 if li > at('depth') else 0.0
    nodes['glow'].outputs[0].default_value = 1.0 if n == 'depth' else .5 if n in ('compare', 'twist') else 0.0
    # holograms light up side by side in 'compare'; they turn green together at the match
    k = ease(p(s, .2, .9)) if n == 'compare' else 0
    hs_e.inputs[1].default_value = 2.2 * k; hn_e.inputs[1].default_value = 2.2 * k
    HSAVED.hide_render = HNOW.hide_render = n != 'compare'               # unlit they still show as a dark ghost behind the head
    hn_e.inputs[0].default_value = (.49, 1, .66, 1) if n == 'compare' and s > d * .7 else (.24, .9, 1, 1)
    HNOW.rotation_euler = (0, 0, (1 - ease(p(s, .3, d * .65))) * .5 if n == 'compare' else 0)
    # photo stage: dots sheet + red phone glow
    fd.modifiers['points'].node_group.nodes['shown'].outputs[0].default_value = ease(p(s, .3, 1.6)) if n == 'photo' else 0
    fd.modifiers['points'].node_group.nodes['Set Material'].inputs['Material'].default_value = dmat
    # unlock: the screen swaps to the open lock + app grid and brightens
    u = ease(p(s, .25, .7)) if n == 'unlock' else 1.0 if li > at('unlock') else 0.0
    scrm.node_tree.nodes['unlock'].inputs['Factor'].default_value = u
    scrm.node_tree.nodes['bright'].outputs[0].default_value = 1.6 + 1.2 * (n == 'unlock') * (1 - p(s, .7, 1.6))

check_framing()
if 'frames' in opt:
    a, b = map(int, opt['frames'].split('-')); frames = range(a, b + 1)
else:
    frames = [round(float(x) * FPS) for x in opt.get('t', '1').split(',')]
for f in frames:
    apply(f / FPS); sc.frame_set(f)
    sc.render.filepath = f"{OUT}/{f + 1:05d}.png" if 'frames' in opt else f"{OUT}/t{f / FPS:.2f}.png"
    bpy.ops.render.render(write_still=True)
