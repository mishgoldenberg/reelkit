# Shared pieces for the Blender reels (cgi/<id>.py): render setup, dark studio world, materials, lights, the camera that
# frames subjects from the lens (no guessed coordinates), the framing check against the overlay's clear band, and the
# frame loop. Every scene is a pure function of time t, read from the voice timeline show/<id>.timing.js.
import bpy, sys, json, math, pathlib
from mathutils import Vector as V

ROOT = pathlib.Path(__file__).resolve().parents[1]
FPS = 30
clamp = lambda x, a=0., b=1.: min(b, max(a, x))
p = lambda t, a, b: clamp((t - a) / (b - a)) if b != a else float(t >= b)
ease = lambda x: 1 - (1 - x) ** 3
inout = lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
back = lambda x: 1 + 2.6 * (x - 1) ** 3 + 1.6 * (x - 1) ** 2

def args():
    a = sys.argv[sys.argv.index('--') + 1:]
    return a[0], dict(x.split('=', 1) for x in a[1:])

def timeline(rid):
    return json.loads((ROOT / 'show' / f'{rid}.timing.js').read_text(encoding='utf-8').split('=', 1)[1])['lines']

def setup(samples):
    sc = bpy.context.scene
    for o in list(sc.objects): bpy.data.objects.remove(o, do_unlink=True)
    sc.render.engine = 'CYCLES'
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
    for d in pr.devices: d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'; sc.cycles.samples = samples; sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'; sc.cycles.max_bounces = 6
    sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
    sc.render.fps = FPS; sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    return sc

def world(sc, strength=.35, color=(.004, .006, .01)):
    """studio HDRI for reflections and light, near-black where the camera sees the background"""
    w = bpy.data.worlds.new('studio'); sc.world = w; nt = w.node_tree if w.node_tree else None
    if nt is None: w.use_nodes = True; nt = w.node_tree
    nt.nodes.clear()
    env = nt.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(str(ROOT / 'models/hdri/studio_small_09_1k.hdr'))
    bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs[1].default_value = strength
    dark = nt.nodes.new('ShaderNodeBackground'); dark.inputs[0].default_value = (*color, 1)
    lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(env.outputs[0], bg.inputs[0]); nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0])
    nt.links.new(bg.outputs[0], mix.inputs[1]); nt.links.new(dark.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs[0])

def mat(name, base=(.5, .5, .5), metal=0., rough=.5, emit=None, estr=0., transmission=0., ior=1.45):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    b.inputs['Transmission Weight'].default_value = transmission; b.inputs['IOR'].default_value = ior
    if emit: b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    return m

def image_emission(name, path, strength=1.):
    """an emissive picture with alpha (text on tiles, labels): transparent where the image is"""
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; n.clear()
    ti = n.new('ShaderNodeTexImage'); ti.image = bpy.data.images.load(str(path))
    em = n.new('ShaderNodeEmission'); em.inputs[1].default_value = strength
    tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader'); out = n.new('ShaderNodeOutputMaterial')
    val = n.new('ShaderNodeValue'); val.name = 'strength'; val.outputs[0].default_value = strength; L.new(val.outputs[0], em.inputs[1])
    L.new(ti.outputs['Color'], em.inputs[0]); L.new(ti.outputs['Alpha'], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0]); m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    return m

def area(sc, name, loc, look, energy, size, col=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (V(look) - V(loc)).to_track_quat('-Z', 'Y').to_euler(); return o

def box(sc, name, size, loc, material, bevel=0., parent=None, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name); x, y, z = (s / 2 for s in size)
    verts = [(sx * x, sy * y, sz * z) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(verts, [], faces); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot; o.data.materials.append(material)
    if bevel: bv = o.modifiers.new('round', 'BEVEL'); bv.width = bevel; bv.segments = 6; bv.limit_method = 'NONE'
    if parent: o.parent = parent
    return o

def plane(sc, name, w, h, loc, material, rot=(math.pi / 2, 0, 0), parent=None):
    """a w x h plane standing up, facing -Y by default (toward a camera in front)"""
    me = bpy.data.meshes.new(name); me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(); [setattr(uv.data[i], 'uv', c) for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = rot
    o.data.materials.append(material)
    if parent: o.parent = parent
    return o

class Cam:
    """camera that frames a subject (center, radius) seen along a direction, sized from the lens"""
    def __init__(self, sc, lens=55, fstop=2.4):
        self.sc = sc; self.d = bpy.data.cameras.new('cam'); self.o = bpy.data.objects.new('cam', self.d); sc.collection.objects.link(self.o); sc.camera = self.o
        self.d.lens = lens; self.d.sensor_width = 36; self.d.dof.use_dof = True; self.d.dof.aperture_fstop = fstop; self.d.clip_start = .005
        self.half_w = (18 / lens) * 9 / 16
    def fit(self, center, radius, direction, fill=1.):
        dirn = V(direction).normalized(); return V(center) - dirn * (radius / (fill * self.half_w)), V(center)
    def place(self, cp, ct):
        self.o.location = cp; self.o.rotation_euler = (ct - cp).to_track_quat('-Z', 'Y').to_euler(); self.d.dof.focus_distance = max((ct - cp).length, .01)

def orbit(a, elev=.1):                     # view direction going round a subject that faces -Y
    return V((math.sin(a), math.cos(a), -elev))

def state(lines, t, shot, cut_dist=1.5):
    """which line is playing, and the camera: this scene's move, blended from the previous one (hard cut if far apart)"""
    li = 0
    for i, l in enumerate(lines):
        if t >= l['t0'] - .05: li = i
    L = lines[li]; s = t - L['t0']; d = L['end'] - L['t0']; n = L['scene']
    cp, ct = shot(n, max(s, 0), d)
    if li > 0 and s < .7:
        P = lines[li - 1]; pp, pt = shot(P['scene'], P['end'] - P['t0'], P['end'] - P['t0'])
        if (pp - cp).length < cut_dist: k = inout(clamp(s / .7)); cp = pp.lerp(cp, k); ct = pt.lerp(ct, k)
    return li, L, s, d, n, cp, ct

def check_framing(sc, cam, lines, shot, subjects):
    """project each scene's subject points; report any that leave the band between the counter and the captions"""
    from bpy_extras.object_utils import world_to_camera_view
    bad = []
    for L in lines:
        d = L['end'] - L['t0']
        for s in (0, d / 2, d):
            cp, ct = shot(L['scene'], s, d); cam.place(cp, ct); bpy.context.view_layer.update()
            for q in subjects(L['scene']):
                v = world_to_camera_view(sc, cam.o, V(q))
                if not (.08 < v.x < .92 and .29 < v.y < .74) or v.z < 0: bad.append(f"{L['scene']}@{s:.1f}s ({v.x:.2f},{v.y:.2f})")
    print('FRAMING', 'ok' if not bad else bad)

def render(sc, out, opt, apply):
    if 'frames' in opt:
        a, b = map(int, opt['frames'].split('-')); frames = range(a, b + 1)
    else:
        frames = [round(float(x) * FPS) for x in opt.get('t', '1').split(',')]
    for f in frames:
        apply(f / FPS); sc.frame_set(f)
        sc.render.filepath = f"{out}/{f + 1:05d}.png" if 'frames' in opt else f"{out}/t{f / FPS:.2f}.png"
        bpy.ops.render.render(write_still=True)
