# Undersea-cable reel in Cycles: a sandy seabed with scanned rocks and a shell (Poly Haven, CC0), the cable lying across it,
# blue water (volume haze, light shafts from the surface, drifting marine snow) and a school of sardines built here
# (procedural fish, instanced, each swimming on its own phase). Run: blender -b --factory-startup --python cgi/ocean.py -- <out> t=1,2 samples=24
import bpy, math, random, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import *

OUT, opt = args()
sc = setup(int(opt.get('samples', 32)))
sc.cycles.volume_bounces = 1; sc.cycles.volume_step_rate = 4
M = ROOT / 'models'
rnd = random.Random(7)

# ---------- water: blue fog that eats red light with distance, a sky that is the bright surface ----------
w = bpy.data.worlds.new('sea'); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[0].default_value = (.004, .03, .05, 1); bg.inputs[1].default_value = 1
vol = nt.nodes.new('ShaderNodeVolumePrincipled'); vol.inputs['Color'].default_value = (.25, .7, .85, 1); vol.inputs['Density'].default_value = .035
vol.inputs['Absorption Color'].default_value = (.0, .25, .42, 1); vol.inputs['Anisotropy'].default_value = .6
out = nt.nodes.new('ShaderNodeOutputWorld'); nt.links.new(bg.outputs[0], out.inputs['Surface']); nt.links.new(vol.outputs[0], out.inputs['Volume'])

# sunlight from the surface, broken up by a wave pattern so the floor gets moving caustics and the haze gets shafts
sun = bpy.data.lights.new('surface', 'SPOT'); sun.energy = 150000; sun.spot_size = math.radians(70); sun.spot_blend = .6; sun.shadow_soft_size = 0
sun.color = (.75, .95, 1); sun.use_nodes = True; ln = sun.node_tree.nodes; ll = sun.node_tree.links
em = ln['Emission']; tc = ln.new('ShaderNodeTexCoord'); vor = ln.new('ShaderNodeTexVoronoi'); vor.feature = 'SMOOTH_F1'; vor.voronoi_dimensions = '4D'
vor.inputs['Scale'].default_value = 22; vor.name = 'waves'
ramp = ln.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = .0; ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
ramp.color_ramp.elements[1].position = .12; ramp.color_ramp.elements[1].color = (.15, .15, .15, 1)
ll.new(tc.outputs['Normal'], vor.inputs['Vector']); ll.new(vor.outputs['Distance'], ramp.inputs['Fac']); ll.new(ramp.outputs['Color'], em.inputs['Color'])
so = bpy.data.objects.new('surface', sun); sc.collection.objects.link(so); so.location = (1.5, 2, 14); so.rotation_euler = (math.radians(8), math.radians(-5), 0)
area(sc, 'fill', (-4, -6, 3), (0, 0, 0), 300, 6, (.4, .7, 1))

# ---------- seabed: a big sand plane with gentle dunes and ripples ----------
sand = bpy.data.materials.new('sand'); sand.use_nodes = True; sn = sand.node_tree.nodes; sl = sand.node_tree.links; b = sn['Principled BSDF']
S = M / 'coast_sand_01'
def tex(pat, colour=True):
    f = next(S.glob(pat)); t = sn.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(f))
    if not colour: t.image.colorspace_settings.name = 'Non-Color'
    m = sn.new('ShaderNodeMapping'); m.inputs['Scale'].default_value = (6, 6, 6); c = sn.new('ShaderNodeTexCoord'); sl.new(c.outputs['UV'], m.inputs[0]); sl.new(m.outputs[0], t.inputs[0]); return t
tint = sn.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = .55
tint.inputs['B'].default_value = (.55, .75, .8, 1); sl.new(tex('*diff*').outputs[0], tint.inputs['A']); sl.new(tint.outputs['Result'], b.inputs['Base Color'])
nm = sn.new('ShaderNodeNormalMap'); sl.new(tex('*nor_gl*', False).outputs[0], nm.inputs['Color']); sl.new(nm.outputs[0], b.inputs['Normal'])
sl.new(tex('*rough*', False).outputs[0], b.inputs['Roughness'])
# caustics: the wavy surface focuses sunlight into moving bright lines on the floor (painted in the floor shader, animated by W)
cc = sn.new('ShaderNodeTexCoord'); cv = sn.new('ShaderNodeTexVoronoi'); cv.feature = 'DISTANCE_TO_EDGE'; cv.voronoi_dimensions = '4D'; cv.name = 'caustic'
cv.inputs['Scale'].default_value = 3.2
warp = sn.new('ShaderNodeTexNoise'); warp.inputs['Scale'].default_value = .8; warp.inputs['Detail'].default_value = 2
wmix = sn.new('ShaderNodeMix'); wmix.data_type = 'VECTOR'; wmix.inputs['Factor'].default_value = .35
sl.new(cc.outputs['Object'], wmix.inputs[4]); sl.new(warp.outputs['Color'], wmix.inputs[5]); sl.new(cc.outputs['Object'], warp.inputs['Vector']); sl.new(wmix.outputs[1], cv.inputs['Vector'])
cr = sn.new('ShaderNodeMapRange'); cr.inputs['From Min'].default_value = 0; cr.inputs['From Max'].default_value = .05; cr.inputs['To Min'].default_value = .35; cr.inputs['To Max'].default_value = 0
cv2 = sn.new('ShaderNodeTexVoronoi'); cv2.feature = 'DISTANCE_TO_EDGE'; cv2.voronoi_dimensions = '4D'; cv2.name = 'caustic2'; cv2.inputs['Scale'].default_value = 4.6
sl.new(wmix.outputs[1], cv2.inputs['Vector']); cmin = sn.new('ShaderNodeMath'); cmin.operation = 'MULTIPLY'
mr1 = sn.new('ShaderNodeMath'); mr1.operation = 'SQRT'; mr2 = sn.new('ShaderNodeMath'); mr2.operation = 'SQRT'
sl.new(cv.outputs['Distance'], mr1.inputs[0]); sl.new(cv2.outputs['Distance'], mr2.inputs[0]); sl.new(mr1.outputs[0], cmin.inputs[0]); sl.new(mr2.outputs[0], cmin.inputs[1])
sl.new(cmin.outputs[0], cr.inputs['Value'])   # bright where both layers' edges cross, like real caustic webs
cm_ = sn.new('ShaderNodeMix'); cm_.data_type = 'RGBA'; cm_.blend_type = 'ADD'; sl.new(cr.outputs['Result'], cm_.inputs['Factor'])
cm_.inputs['B'].default_value = (.5, .8, .85, 1); sl.new(tint.outputs['Result'], cm_.inputs['A']); sl.new(cm_.outputs['Result'], b.inputs['Base Color'])
bpy.ops.mesh.primitive_grid_add(x_subdivisions=300, y_subdivisions=300, size=40); bed = bpy.context.object; bed.data.materials.append(sand)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.smart_project(); bpy.ops.object.mode_set(mode='OBJECT')
for v in bed.data.vertices:
    x, y = v.co.x, v.co.y
    v.co.z = .35 * math.sin(x * .25 + y * .1) + .18 * math.sin(y * .4 - x * .15) + .03 * math.sin(x * 3.1 + y * .8)
bpy.ops.object.shade_smooth()
def floor_z(x, y): return .35 * math.sin(x * .25 + y * .1) + .18 * math.sin(y * .4 - x * .15) + .03 * math.sin(x * 3.1 + y * .8)

# ---------- scanned rocks and a shell ----------
def load(name, loc, scale, rot=0):
    bpy.ops.import_scene.gltf(filepath=str(next((M / name).glob('*.gltf'))))
    o = bpy.context.selected_objects[0]
    while o.parent: o = o.parent
    o.location = loc; o.scale = (scale,) * 3; o.rotation_euler = (0, 0, rot); return o
load('coast_rocks_01', (-3.4, 5.5, floor_z(-3.4, 5.5) - .05), .35, .6)
load('coast_rocks_03', (3.2, 6.5, floor_z(3.2, 6.5) - .05), .3, 2.2)
load('boulder_01', (-1.6, 2.2, floor_z(-1.6, 2.2) - .05), .35, 1.1)
load('lambis_shell', (.95, .2, floor_z(.95, .2) + .02), 1.0, .8)

# ---------- light pulses: a shader piece shared by the cable and the glass fibres ----------
# bright narrow pulses travel along +x (phase moves them); before a booster at x=BX they fade, after it they are strong again
BX = -5.0
def pulse_emission(m, axis_scale=1.0, colour=(.35, .95, 1), axis='X'):
    n = m.node_tree.nodes; L = m.node_tree.links; b = n['Principled BSDF']
    tc = n.new('ShaderNodeTexCoord'); sx = n.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sx.inputs[0])
    ph = n.new('ShaderNodeValue'); ph.name = 'phase'; st = n.new('ShaderNodeValue'); st.name = 'pulse'
    sub = n.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; L.new(sx.outputs[axis], sub.inputs[0]); L.new(ph.outputs[0], sub.inputs[1])
    mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 2.4 * axis_scale; L.new(sub.outputs[0], mul.inputs[0])
    sn_ = n.new('ShaderNodeMath'); sn_.operation = 'SINE'; L.new(mul.outputs[0], sn_.inputs[0])
    nar = n.new('ShaderNodeMapRange'); nar.inputs['From Min'].default_value = .9; nar.inputs['From Max'].default_value = 1; L.new(sn_.outputs[0], nar.inputs['Value'])
    gate = n.new('ShaderNodeMath'); gate.operation = 'GREATER_THAN'; gate.inputs[1].default_value = BX; L.new(sx.outputs['X'], gate.inputs[0])
    fade = n.new('ShaderNodeMapRange'); fade.inputs['From Min'].default_value = BX - 7; fade.inputs['From Max'].default_value = BX
    fade.inputs['To Min'].default_value = 1; fade.inputs['To Max'].default_value = .12; L.new(sx.outputs['X'], fade.inputs['Value'])
    gmax = n.new('ShaderNodeMath'); gmax.operation = 'MAXIMUM'; L.new(gate.outputs[0], gmax.inputs[0]); L.new(fade.outputs['Result'], gmax.inputs[1])
    useg = n.new('ShaderNodeValue'); useg.name = 'use_gain'; useg.outputs[0].default_value = 0    # 1 = show the fading before the booster
    gl = n.new('ShaderNodeMix'); gl.data_type = 'FLOAT'; L.new(useg.outputs[0], gl.inputs['Factor']); gl.inputs['A'].default_value = 1; L.new(gmax.outputs[0], gl.inputs['B'])
    m1 = n.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; L.new(nar.outputs['Result'], m1.inputs[0]); L.new(gl.outputs['Result'], m1.inputs[1])
    m2 = n.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(st.outputs[0], m2.inputs[1])
    b.inputs['Emission Color'].default_value = (*colour, 1); L.new(m2.outputs[0], b.inputs['Emission Strength'])
    return m

# ---------- the cable: lies across the seabed (rebuilt every frame so it can be lifted or dragged), dark polyethylene ----------
CX = [x * .25 for x in range(-60, 61)]
def cable_y(x): return .6 + .25 * math.sin(x * .3)
cu = bpy.data.curves.new('cable', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .045; cu.bevel_resolution = 6; cu.use_fill_caps = True
sp = cu.splines.new('POLY'); sp.points.add(len(CX) - 1)
cab = bpy.data.objects.new('cable', cu); sc.collection.objects.link(cab)
cm = mat('cable', (.02, .022, .025), 0, .45); cn = cm.node_tree.nodes; noise = cn.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 40
mx = cn.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (.02, .022, .025, 1); mx.inputs['B'].default_value = (.12, .14, .09, 1)
cm.node_tree.links.new(noise.outputs['Fac'], mx.inputs['Factor']); cm.node_tree.links.new(mx.outputs['Result'], cn['Principled BSDF'].inputs['Base Color'])
pulse_emission(cm); cab.data.materials.append(cm)
DEF = {'lift': (0., 0.), 'shift': (0., 0.)}                          # (x where, amount): the hook lifts it, the anchor drags it
def cable_pos(x):
    lx, la = DEF['lift']; sx_, sa = DEF['shift']
    y = cable_y(x) + sa * math.exp(-((x - sx_) / 1.1) ** 2)
    z = floor_z(x, y) + .045 + la * math.exp(-((x - lx) / 1.6) ** 2) + .115 * math.exp(-((x - BX) / .9) ** 2)   # rises into the booster
    return V((x, y, z))
def lay_cable():
    for pt, x in zip(sp.points, CX): pt.co = (*cable_pos(x), 1)
# two more cables further off, so the wide shot reads as a network
for k, (y0, ph) in enumerate([(-4.5, 1.), (7.5, 2.2)]):
    c2 = bpy.data.curves.new(f'cable{k}', 'CURVE'); c2.dimensions = '3D'; c2.bevel_depth = .045; c2.bevel_resolution = 4
    s2 = c2.splines.new('POLY'); xs2 = [x * .5 for x in range(-36, 37)]; s2.points.add(len(xs2) - 1)
    for pt, x in zip(s2.points, xs2):
        y = y0 + .4 * math.sin(x * .2 + ph) + x * .08 * (1 if k else -1); pt.co = (x, y, floor_z(x, y) + .045, 1)
    o2 = bpy.data.objects.new(f'cable{k}', c2); sc.collection.objects.link(o2); o2.data.materials.append(cm)

# the booster (repeater): a pressure housing the cable runs into, on the seabed at x=BX
def booster_mesh():
    me = bpy.data.meshes.new('booster'); verts, faces = [], []; R = 24
    prof = [(-.62, .05), (-.48, .13), (-.40, .16), (.40, .16), (.48, .13), (.62, .05)]   # (x, radius): tapered ends meet the cable
    for x, r in prof:
        for j in range(R): a = 2 * math.pi * j / R; verts.append((x, r * math.cos(a), r * math.sin(a)))
    for i in range(len(prof) - 1):
        for j in range(R): faces.append((i * R + j, i * R + (j + 1) % R, (i + 1) * R + (j + 1) % R, (i + 1) * R + j))
    me.from_pydata(verts, [], faces); [setattr(p, 'use_smooth', True) for p in me.polygons]; return me
boost = bpy.data.objects.new('booster', booster_mesh()); sc.collection.objects.link(boost)
bm_ = mat('booster', (.16, .17, .16), .6, .45); bn = bm_.node_tree.nodes; bno = bn.new('ShaderNodeTexNoise'); bno.inputs['Scale'].default_value = 18
bmx = bn.new('ShaderNodeMix'); bmx.data_type = 'RGBA'; bmx.inputs['A'].default_value = (.16, .17, .16, 1); bmx.inputs['B'].default_value = (.2, .22, .12, 1)
bm_.node_tree.links.new(bno.outputs['Fac'], bmx.inputs['Factor']); bm_.node_tree.links.new(bmx.outputs['Result'], bn['Principled BSDF'].inputs['Base Color'])
ring = bn.new('ShaderNodeValue'); ring.name = 'ring'; bn['Principled BSDF'].inputs['Emission Color'].default_value = (.35, .95, 1, 1)
bm_.node_tree.links.new(ring.outputs[0], bn['Principled BSDF'].inputs['Emission Strength']); boost.data.materials.append(bm_)

# ---------- sardines: one procedural fish, instanced on points that the script moves every frame ----------
def fish_mesh():
    me = bpy.data.meshes.new('fish'); verts, faces = [], []; R, L = 10, 14
    for i in range(L + 1):
        u = i / L; x = -.5 + u                                    # nose at +x .5, tail at -x .5 (body length 1)
        rad = .16 * math.sin(math.pi * min(1, (u * .95 + .02))) ** .8 * (1 - .55 * (1 - u) ** 3)
        for j in range(R):
            a = 2 * math.pi * j / R; verts.append((x, rad * .55 * math.cos(a), rad * math.sin(a)))
    for i in range(L):
        for j in range(R): faces.append((i * R + j, i * R + (j + 1) % R, (i + 1) * R + (j + 1) % R, (i + 1) * R + j))
    t0 = len(verts); verts += [(-.5, 0, 0), (-.72, 0, .17), (-.66, 0, 0), (-.72, 0, -.17)]; faces += [(t0, t0 + 1, t0 + 2), (t0, t0 + 2, t0 + 3)]
    me.from_pydata(verts, [], faces); me.validate()
    for pl in me.polygons: pl.use_smooth = True
    return me
fish = bpy.data.objects.new('fish', fish_mesh()); sc.collection.objects.link(fish); fish.hide_render = True
fm = bpy.data.materials.new('sardine'); fm.use_nodes = True; fn = fm.node_tree.nodes; fl_ = fm.node_tree.links; fb = fn['Principled BSDF']
geo = fn.new('ShaderNodeNewGeometry'); sep = fn.new('ShaderNodeSeparateXYZ'); fl_.new(geo.outputs['Normal'], sep.inputs[0])
grad = fn.new('ShaderNodeValToRGB'); grad.color_ramp.elements[0].color = (.75, .8, .85, 1); grad.color_ramp.elements[1].color = (.03, .12, .2, 1)
grad.color_ramp.elements[0].position = .45; grad.color_ramp.elements[1].position = .7
fl_.new(sep.outputs['Z'], grad.inputs['Fac']); fl_.new(grad.outputs['Color'], fb.inputs['Base Color'])
fb.inputs['Metallic'].default_value = .85; fb.inputs['Roughness'].default_value = .22
fish.data.materials.append(fm)
bend = fish.modifiers.new('swim', 'SIMPLE_DEFORM'); bend.deform_method = 'BEND'; bend.deform_axis = 'Z'; bend.angle = 0

N_FISH = 420
pm = bpy.data.meshes.new('school'); pm.from_pydata([(0, 0, 0)] * N_FISH, [], []); school = bpy.data.objects.new('school', pm); sc.collection.objects.link(school)
rot = pm.attributes.new('rot', 'FLOAT_VECTOR', 'POINT'); scl = pm.attributes.new('scl', 'FLOAT', 'POINT')
ng = bpy.data.node_groups.new('school', 'GeometryNodeTree'); ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry'); N = ng.nodes; Lk = ng.links
gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput'); inst = N.new('GeometryNodeInstanceOnPoints'); oi = N.new('GeometryNodeObjectInfo')
oi.inputs['Object'].default_value = fish; oi.transform_space = 'RELATIVE'
ra = N.new('GeometryNodeInputNamedAttribute'); ra.data_type = 'FLOAT_VECTOR'; ra.inputs['Name'].default_value = 'rot'
sa = N.new('GeometryNodeInputNamedAttribute'); sa.data_type = 'FLOAT'; sa.inputs['Name'].default_value = 'scl'
real = N.new('GeometryNodeRealizeInstances')
Lk.new(gi.outputs[0], inst.inputs['Points']); Lk.new(oi.outputs['Geometry'], inst.inputs['Instance']); Lk.new(ra.outputs['Attribute'], inst.inputs['Rotation'])
Lk.new(sa.outputs['Attribute'], inst.inputs['Scale']); Lk.new(inst.outputs[0], real.inputs[0]); Lk.new(real.outputs[0], go.inputs[0])
school.modifiers.new('school', 'NODES').node_group = ng

FISH = [(rnd.uniform(0, 2 * math.pi), rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.uniform(.85, 1.15)) for _ in range(N_FISH)]
SCHOOL_C = V((1.5, 4.8, 2.3))                                   # above and behind the action, never in the shark's path
def swim(t):
    """the school drifts as a whole and turns slowly; every fish keeps its own place, wobble and speed"""
    co, ro, sz = [], [], []
    cen = SCHOOL_C + V((math.sin(t * .25) * 1.2, math.cos(t * .2) * .6, .25 * math.sin(t * .4)))
    head = .4 * math.sin(t * .25) + math.pi                     # heading, swimming roughly toward -x
    for ph, a, b_, c, s in FISH:
        p = cen + V((a * 1.3, b_ * .7, c * .45)) + V((math.sin(t * 1.3 + ph) * .08, math.cos(t * 1.1 + ph) * .08, math.sin(t * .9 + ph) * .05))
        co += [*p]; ro += [0, .05 * math.sin(t * 2 + ph), head + .15 * math.sin(t * .7 + ph)]; sz.append(.13 * s)
    pm.vertices.foreach_set('co', co); rot.data.foreach_set('vector', ro); scl.data.foreach_set('value', sz); pm.update()
    bend.angle = .35 * math.sin(t * 11)

# ---------- marine snow: tiny drifting specks catching the light ----------
sn_m = bpy.data.meshes.new('snow'); SNOW = [(rnd.uniform(-5, 5), rnd.uniform(-3, 8), rnd.uniform(-.3, 5)) for _ in range(3000)]
sn_m.from_pydata(SNOW, [], []); snow = bpy.data.objects.new('snow', sn_m); sc.collection.objects.link(snow)
g2 = bpy.data.node_groups.new('snow', 'GeometryNodeTree'); g2.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
g2.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
a_ = g2.nodes.new('NodeGroupInput'); z_ = g2.nodes.new('NodeGroupOutput'); m2p = g2.nodes.new('GeometryNodeMeshToPoints'); m2p.inputs['Radius'].default_value = .0025
smat = g2.nodes.new('GeometryNodeSetMaterial'); smat.inputs['Material'].default_value = mat('snow', (.8, .9, .9), 0, .5, (.6, .85, 1), .4)
g2.links.new(a_.outputs[0], m2p.inputs[0]); g2.links.new(m2p.outputs[0], smat.inputs[0]); g2.links.new(smat.outputs[0], z_.inputs[0])
snow.modifiers.new('snow', 'NODES').node_group = g2
def drift(t):
    sn_m.vertices.foreach_set('co', [c for x, y, z in SNOW for c in (x + .05 * math.sin(t * .3 + y), y, (z - t * .03) % 5.3 - .3)]); sn_m.update()

# ---------- the shark: rigged bull shark by nerk987 (BlendSwap, CC-BY), posed from code: body wave, jaw, head ----------
with bpy.data.libraries.load(str(M / 'bull_shark/src/BullShark.blend')) as (src, dst): dst.objects = ['rig', 'LowPoly']
RIG, SHARK = dst.objects
for o in (RIG, SHARK): sc.collection.objects.link(o)
RIG.hide_render = True
SH = bpy.data.objects.new('shark_root', None); sc.collection.objects.link(SH); RIG.parent = SH
RIG.location = (0, 0, -2.05); SH.scale = (.3,) * 3                 # model is ~9.7 m long; a bull shark is ~3 m
RIG.animation_data_clear()                                         # the file's own swim cycle would overwrite our pose every frame
for pb in RIG.pose.bones: pb.rotation_mode = 'XYZ'
def shark_pose(t, bite=0., wave=1.):
    """swimming S-wave down the body (head leads, tail swings most), jaw open by `bite` (0..1)"""
    RIG.pose.bones['spine_master'].rotation_euler = (0, 0, wave * .10 * math.sin(t * 5.5))
    for i, n in enumerate(['spine.002', 'spine.001', 'spine']):
        RIG.pose.bones[n].rotation_euler = (0, 0, wave * (.10 + .08 * i) * math.sin(t * 5.5 - (i + 1) * .8))
    RIG.pose.bones['head'].rotation_euler = (0, 0, -wave * .05 * math.sin(t * 5.5))
    RIG.pose.bones['jaw'].rotation_euler = (.55 * bite, 0, 0); RIG.pose.bones['jaw.master'].rotation_euler = (.2 * bite, 0, 0)

# ---------- stage B, the coast (x ~ 60): shallow bright water, sand sloping down, the armoured cable coming out of the sand ----------
B0 = 60.
def shore_z(x, y): return -.25 * (x - B0) + .12 * math.sin(y * .5 + x * .3) + .02 * math.sin(x * 4 + y)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=200, y_subdivisions=200, size=34, location=(B0 + 4, 0, 0)); shore = bpy.context.object
shore.data.materials.append(sand)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.smart_project(); bpy.ops.object.mode_set(mode='OBJECT')
for v in shore.data.vertices: v.co.z = shore_z(v.co.x + shore.location.x, v.co.y)
bpy.ops.object.shade_smooth()
surf_me = bpy.data.meshes.new('surface'); surf_me.from_pydata([(-20, -20, 0), (20, -20, 0), (20, 20, 0), (-20, 20, 0)], [], [(0, 1, 2, 3)])
surf = bpy.data.objects.new('surface', surf_me); sc.collection.objects.link(surf); surf.location = (B0, 0, 5.5)
sfm = bpy.data.materials.new('surface'); sfm.use_nodes = True; sfn = sfm.node_tree.nodes; sfb = sfn['Principled BSDF']
sfb.inputs['Transmission Weight'].default_value = 1; sfb.inputs['IOR'].default_value = 1.33; sfb.inputs['Roughness'].default_value = .05
swn = sfn.new('ShaderNodeTexNoise'); swn.inputs['Scale'].default_value = 1.4; swn.name = 'swell'; swn.noise_dimensions = '4D'
sbm = sfn.new('ShaderNodeBump'); sbm.inputs['Strength'].default_value = .5; sfm.node_tree.links.new(swn.outputs['Fac'], sbm.inputs['Height']); sfm.node_tree.links.new(sbm.outputs['Normal'], sfb.inputs['Normal'])
surf.data.materials.append(sfm); surf.visible_shadow = False             # without caustics, a glass surface would block the sun
sun2 = bpy.data.lights.new('surface2', 'SPOT'); sun2.energy = 55000; sun2.spot_size = math.radians(80); sun2.spot_blend = .6; sun2.shadow_soft_size = 0; sun2.color = (.8, .97, 1)
so2 = bpy.data.objects.new('surface2', sun2); sc.collection.objects.link(so2); so2.location = (B0 + 2, 1, 13)
# armoured cable: thicker, wrapped in steel wires (diagonal bands), buried under the sand up the slope, lying on it further down
au = bpy.data.curves.new('armour', 'CURVE'); au.dimensions = '3D'; au.bevel_depth = .085; au.bevel_resolution = 6; au.use_fill_caps = True
asp = au.splines.new('POLY'); AX = [B0 - 12 + x * .25 for x in range(0, 105)]; asp.points.add(len(AX) - 1)
EMERGE = B0 - 1.5                                                    # up-slope of here the cable runs under the sand
for pt, x in zip(asp.points, AX):
    y = .4 + .15 * math.sin(x * .4); dz = -.25 if x < EMERGE - .8 else -.25 + .33 * p(x, EMERGE - .8, EMERGE + .4)
    pt.co = (x, y, shore_z(x, y) + .085 + dz, 1)
arm = bpy.data.objects.new('armour', au); sc.collection.objects.link(arm)
am = mat('steelwire', (.25, .24, .22), .85, .4); an_ = am.node_tree.nodes
wv = an_.new('ShaderNodeTexWave'); wv.bands_direction = 'DIAGONAL'; wv.inputs['Scale'].default_value = 9; wv.inputs['Distortion'].default_value = .2
atc = an_.new('ShaderNodeTexCoord'); am.node_tree.links.new(atc.outputs['Object'], wv.inputs['Vector'])
amx = an_.new('ShaderNodeMix'); amx.data_type = 'RGBA'; amx.inputs['A'].default_value = (.12, .11, .1, 1); amx.inputs['B'].default_value = (.5, .48, .44, 1)
am.node_tree.links.new(wv.outputs['Fac'], amx.inputs['Factor']); am.node_tree.links.new(amx.outputs['Result'], an_['Principled BSDF'].inputs['Base Color'])
arm.data.materials.append(am)
def arm_pos(x):
    y = .4 + .15 * math.sin(x * .4); return V((x, y, shore_z(x, y) + .085 + (-.25 if x < EMERGE - .8 else -.25 + .33 * p(x, EMERGE - .8, EMERGE + .4))))

# ---------- stage C, the lab (x ~ -60): the cable cut open, layers stepped back like a diagram, glass fibres carrying light ----------
C0 = V((-60, 0, 1.2))
def cyl(name, r, x0, x1, material, y=0., z=0., verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=x1 - x0, location=(C0.x + (x0 + x1) / 2, C0.y + y, C0.z + z), rotation=(0, math.pi / 2, 0))
    o = bpy.context.object; o.name = name; o.data.materials.append(material); bpy.ops.object.shade_smooth(); return o
jacket = mat('jacket', (.015, .016, .02), 0, .35)
steel = mat('steel', (.6, .6, .62), 1, .25)
copper = mat('copper', (.95, .5, .3), 1, .22)
gel = mat('gel', (.85, .85, .8), 0, .3)
glass = pulse_emission(mat('glass', (.03, .07, .08), 0, .08, ior=1.46), 6, axis='Z')   # fibres run along their local Z
LAB = []
LAB.append(cyl('jacket', .10, 0, 4, jacket))                        # layers step back toward -x: jacket ends at 0, wires at -.15 ...
for k in range(18):
    a = 2 * math.pi * k / 18; LAB.append(cyl(f'wire{k}', .011, -.16, 3.99, steel, .079 * math.cos(a), .079 * math.sin(a), 16))
LAB.append(cyl('copper', .066, -.32, 3.98, copper))
LAB.append(cyl('gel', .05, -.48, 3.97, gel))
FIB = []
for k in range(8):
    a = 2 * math.pi * k / 8; FIB.append(cyl(f'fibre{k}', .006, -3.2, 3.96, glass, .022 * math.cos(a), .022 * math.sin(a), 16))
LAB += FIB
for k, (loc, e, sz) in enumerate([((-61.5, -2, 3), 900, 2.5), ((-58, 2.5, 2), 500, 2), ((-63, 1.5, .2), 300, 3)]):
    LAB.append(area(sc, f'lab{k}', loc, C0, e, sz, (.85, .95, 1)))

# ---------- the anchor (dragged in by a ship above) and the repair grapnel ----------
iron = mat('iron', (.1, .09, .08), .8, .6)
def part(o, parent): o.parent = parent; o.data.materials.append(iron); bpy.ops.object.shade_smooth(); return o
ANC = bpy.data.objects.new('anchor', None); sc.collection.objects.link(ANC)
bpy.ops.mesh.primitive_cylinder_add(radius=.045, depth=1.3, location=(0, 0, .65)); part(bpy.context.object, ANC)
bpy.ops.mesh.primitive_torus_add(major_radius=.09, minor_radius=.022, location=(0, 0, 1.36), rotation=(math.pi / 2, 0, 0)); part(bpy.context.object, ANC)
for sgn in (-1, 1):
    bpy.ops.mesh.primitive_cone_add(radius1=.13, radius2=.01, depth=.5, location=(sgn * .26, 0, .2), rotation=(0, -sgn * 2.2, 0)); o = part(bpy.context.object, ANC); o.scale = (1, .3, 1)   # flat flukes
bpy.ops.mesh.primitive_uv_sphere_add(radius=.09, location=(0, 0, .02)); part(bpy.context.object, ANC)
for k in range(10):                                                  # chain up toward the ship
    bpy.ops.mesh.primitive_torus_add(major_radius=.07, minor_radius=.018, location=(0, -.11 * k - .05, 1.42 + .12 * k), rotation=(0, math.pi / 2 * (k % 2), 0)); part(bpy.context.object, ANC)
GRP = bpy.data.objects.new('grapnel', None); sc.collection.objects.link(GRP)
bpy.ops.mesh.primitive_cylinder_add(radius=.03, depth=.7, location=(0, 0, .35)); part(bpy.context.object, GRP)
for k in range(4):
    a = math.pi / 2 * k + .4
    bpy.ops.mesh.primitive_torus_add(major_radius=.16, minor_radius=.018, location=(.16 * math.cos(a), .16 * math.sin(a), .05), rotation=(math.pi / 2, 0, a + math.pi / 2))
    part(bpy.context.object, GRP)
bpy.ops.mesh.primitive_cylinder_add(radius=.012, depth=12, location=(0, 0, 6.7)); part(bpy.context.object, GRP)
PROPS = {'anchor': [ANC] + list(ANC.children), 'repair': [GRP] + list(GRP.children), 'shark': [SH, RIG, SHARK]}
def show_props(n):
    for k, objs in PROPS.items():
        for o in objs: o.hide_render = (k != n) or o is RIG

# ---------- timeline and shots ----------
LINES = timeline('ocean')
cam = Cam(sc, lens=32, fstop=4)
def along(x, dx=0., up=0.): c = cable_pos(x); return c + V((dx, 0, up))
def shot(n, s, d):
    k = inout(p(s, 0, d))
    if n == 'hook': return V((2, -6, 9)).lerp(V((-1.2, -3.0, 1.1)), inout(p(s, 0, d * .9))), V((0, 1, 0)).lerp(V((.4, 1.2, .5)), k)
    if n == 'coast': return V((B0 + 2.4 - .8 * k, -.5, .2)), V((B0 - 6, 1.6, 2.2))
    if n == 'dive':
        x = EMERGE - .3 + 7 * k; c = arm_pos(x); return c + V((-1.1, -1.2, .6)), arm_pos(x + 1.8)
    if n == 'share': return V((-10 + 2 * k, -8, 4.6)), V((3, 1, -.3))
    if n == 'hose':
        c = cable_pos(.6); return c + V((-.55 + .2 * k, -.75, .32)), c + V((.05, -.25, 0))
    if n == 'armour':
        c = arm_pos(EMERGE); return c + V((-.35 + .2 * k, -.65, .3)), c
    if n == 'cut': a = -2.3 + .8 * k; return C0 + V((-.15, 0, 0)) + V((math.cos(a), math.sin(a) * .9, .25)) * .75, C0 + V((-.25, 0, 0))
    if n == 'fibre': return C0 + V((-.55 - .5 * k, -.42, .16)), C0 + V((-.85 - .5 * k, 0, 0))
    if n == 'light': x = -1.0 - 1.9 * k; return C0 + V((x + .22, -.13, .05)), C0 + V((x - .35, 0, 0))
    if n == 'booster': c = cable_pos(BX); return c + V((-1.9 + .6 * k, -1.5, .55)), c + V((.3, 0, 0))
    if n == 'latency': x = -9 + 16 * k; return cable_pos(x) + V((-.6, -1.5, .5)), cable_pos(x + 1.2)
    if n == 'shark': return V((-1.1, -2.4, .95)), V((.45, .35, .5))
    if n == 'anchor': return V((1.4, -3.2, 1.0)), V((3.4, .2, .35))
    if n == 'repair': return V((-3.6, -3.6, 1.3)), V((-2, .6, .75))
    if n == 'twist': return V((0, -2.2, 1.0)).lerp(V((0, -7, 5)), k), V((0, 1, 0))
    return V((0, -7, 5)).lerp(V((0, -7.8, 5.8)), k), V((0, 1, 0))       # cta

def shark_place(s, d):
    """swim in from the right, pitch down and bite the cable at x=.5, shake, give up, swim off up and away"""
    c = cable_pos(.5); bite_a, bite_b = d * .32, d * .62
    if s < bite_a: u = ease(p(s, 0, bite_a)); pos = V((4.5, -1.2, 1.6)).lerp(c + V((.95, -.1, .5)), u); yaw = math.atan2(-1, .25); pitch = .25 * u; bite = .9 * p(s, bite_a - .5, bite_a)
    elif s < bite_b:
        u = p(s, bite_a, bite_b); shake = math.sin(u * 30) * .12 * (1 - u)
        pos = c + V((.95, -.1, .5)); yaw = math.atan2(-1, .25) + shake; pitch = .25; bite = .9 - .9 * p(s, bite_a, bite_a + .15) + .9 * p(s, bite_a + .4, bite_b - .3) * (1 - p(s, bite_b - .3, bite_b))
        DEF['shift'] = (.5, -.06 * math.sin(u * 30) * (1 - u))
    else:
        u = ease(p(s, bite_b, d)); pos = (c + V((.95, -.1, .5))).lerp(V((-3.5, 1.2, 2.6)), u); yaw = math.atan2(-1, .25) + 1.6 * u; pitch = .25 - .45 * u; bite = 0
    SH.location = pos; SH.rotation_euler = (pitch, 0, yaw); shark_pose(s, bite, 1.0)

def apply(t):
    li, L, s, d, n, cp, ct = state(LINES, t, shot, cut_dist=3)
    DEF['lift'] = (0., 0.); DEF['shift'] = (0., 0.); show_props(n)
    swim(t); drift(t)
    ln['waves'].inputs['W'].default_value = t * .35; sfn['swell'].inputs['W'].default_value = t * .25
    sand.node_tree.nodes['caustic'].inputs['W'].default_value = t * .4; sand.node_tree.nodes['caustic2'].inputs['W'].default_value = 3 - t * .3
    if n == 'shark': shark_place(s, d)
    if n == 'anchor':                                                  # dragged in from the front, snags the cable and pulls it along
        y = -3.2 + 4.6 * ease(p(s, 0, d * .85)); ANC.location = (3.4, y, floor_z(3.4, y) + .05); ANC.rotation_euler = (-.25, 0, .3)
        DEF['shift'] = (3.4, max(0, y - cable_y(3.4) + .15))
    if n == 'repair':
        h = 6 - 5.7 * ease(p(s, 0, d * .35)); lift = 1.2 * ease(p(s, d * .45, d))
        DEF['lift'] = (-2, lift); GRP.location = (-2, cable_y(-2) - .02, (floor_z(-2, cable_y(-2)) + .05 + lift) if s > d * .35 else h)
    lay_cable()
    boost.location = cable_pos(BX); boost.rotation_euler = (0, 0, math.atan2(cable_y(BX + .1) - cable_y(BX - .1), .2))
    # light: pulses on from 'light' onwards; the booster scene shows them fading before it and strong after; slowed down on purpose
    on = 1.0 if li >= [l['scene'] for l in LINES].index('light') else 0.0
    for m_ in (cm, glass):
        m_.node_tree.nodes['phase'].outputs[0].default_value = t * 2.2
        m_.node_tree.nodes['use_gain'].outputs[0].default_value = 1.0 if n == 'booster' else 0.0
    cm.node_tree.nodes['pulse'].outputs[0].default_value = 1.2 * on * (.5 if n in ('twist', 'cta') else 1)
    glass.node_tree.nodes['pulse'].outputs[0].default_value = 8 if n in ('fibre', 'light') else 0
    bn['ring'].outputs[0].default_value = 0
    lab = n in ('cut', 'fibre', 'light')
    vol.inputs['Density'].default_value = 0 if lab else .02 if n in ('coast', 'dive', 'armour') else .035; bg.inputs[0].default_value = (.002, .004, .007, 1) if lab else (.004, .03, .05, 1)
    sun.energy = 150000 * (1 - .8 * ease(p(t, LINES[-2]['t0'], LINES[-2]['t0'] + 2.5)))      # the lights go down for 'lying in the dark'
    cam.place(cp, ct)

def subjects(n):
    return {'hook': [cable_pos(.5)], 'coast': [arm_pos(EMERGE)], 'dive': [], 'share': [cable_pos(0)], 'hose': [cable_pos(.6)], 'armour': [arm_pos(EMERGE)],
            'cut': [C0 + V((-.25, 0, 0))], 'fibre': [], 'light': [], 'booster': [cable_pos(BX)], 'latency': [], 'shark': [cable_pos(.5)],
            'anchor': [cable_pos(3.4)], 'repair': [cable_pos(-2)], 'twist': [cable_pos(0)], 'cta': []}.get(n, [])
lay_cable()
check_framing(sc, cam, LINES, shot, subjects)
render(sc, OUT, opt, apply)
