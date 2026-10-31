# renders a flat "photo" of the bust (front, soft light) used as the printed photo in the faceid reel: cgi/tex/photo.png
import bpy, pathlib, math
from mathutils import Vector as V
ROOT = pathlib.Path(bpy.data.filepath).resolve().parents[2]; sc = bpy.context.scene
for im in bpy.data.images:
    if im.filepath.startswith('//textures'): im.filepath = str(ROOT / 'models/marble_bust_01/textures' / im.filepath.replace(chr(92), '/').split('/')[-1])
sc.render.engine = 'CYCLES'; pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices: d.use = d.type == 'OPTIX'
sc.cycles.device = 'GPU'; sc.cycles.samples = 48; sc.render.resolution_x, sc.render.resolution_y = 600, 800
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.55, .6, .68, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1
for o in list(sc.objects):
    if o.name != 'marble_bust_01': bpy.data.objects.remove(o, do_unlink=True)
c = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', c); sc.collection.objects.link(co); sc.camera = co
co.location = (0, -1.1, .38); co.rotation_euler = (V((0, 0, .36)) - co.location).to_track_quat('-Z', 'Y').to_euler(); c.lens = 85
l = bpy.data.lights.new('k', 'AREA'); l.energy = 60; l.size = 1; lo = bpy.data.objects.new('k', l); sc.collection.objects.link(lo); lo.location = (-.6, -.8, .9); lo.rotation_euler = (V((0, 0, .36)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = str(ROOT / 'cgi/tex/photo.png'); bpy.ops.render.render(write_still=True)
