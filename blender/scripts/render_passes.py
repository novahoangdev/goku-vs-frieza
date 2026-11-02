# Renders 4 passes for the video pack: beauty (color), matte (Goku white / everything else black), energy (emissive objects only),
# depth (depth along the view axis, normalized log: the app uses it so 2D effects are occluded by near objects on the right layer).
#
# Run: Blender -b blender/goku_vs_frieza.blend -P blender/scripts/render_passes.py -- \
#         --out render --pct 100 --samples 16 [--passes beauty,matte,energy,depth] [--frames 0-2051] [--motion-blur]
import bpy, math, os, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv else default


OUT = os.path.abspath(arg("--out", "render"))
PCT = int(arg("--pct", "100"))
SAMPLES = int(arg("--samples", "16"))
PASSES = arg("--passes", "beauty,matte,energy,depth").split(",")
# depth: 0 ↔ Z_NEAR m, 1 ↔ Z_FAR m (and the sky); log so it stays precise near the camera. The app decodes with the same constants.
Z_NEAR, Z_FAR = 0.05, 400.0
scene = bpy.context.scene
F0, F1 = (int(x) for x in arg("--frames", f"{scene.frame_start}-{scene.frame_end}").split("-"))   # default: the whole film

r = scene.render
r.resolution_percentage = PCT
scene.frame_start, scene.frame_end = F0, F1
scene.eevee.taa_render_samples = SAMPLES
r.use_motion_blur = "--motion-blur" in argv
r.image_settings.file_format = "PNG"
vl = scene.view_layers[0]


def matte_material():
    m = bpy.data.materials.new("matte_white")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def set_energy_mode(v):
    for m in bpy.data.materials:
        if m.use_nodes and "energy_mode" in m.node_tree.nodes:
            m.node_tree.nodes["energy_mode"].outputs[0].default_value = v


def holdout(names, on):
    for lc in vl.layer_collection.children:
        if lc.name in names:
            lc.holdout = on


def depth_material():
    m = bpy.data.materials.new("depth_log")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    cd = N.new("ShaderNodeCameraData")
    lg = N.new("ShaderNodeMath"); lg.operation = "LOGARITHM"; lg.inputs[1].default_value = math.e
    L.new(cd.outputs["View Z Depth"], lg.inputs[0])
    nm = N.new("ShaderNodeMath"); nm.operation = "MULTIPLY_ADD"; nm.use_clamp = True
    nm.inputs[1].default_value = 1.0 / math.log(Z_FAR / Z_NEAR)
    nm.inputs[2].default_value = -math.log(Z_NEAR) / math.log(Z_FAR / Z_NEAR)
    L.new(lg.outputs[0], nm.inputs[0])
    em = N.new("ShaderNodeEmission")
    L.new(nm.outputs[0], em.inputs["Strength"])
    out = N.new("ShaderNodeOutputMaterial")
    L.new(em.outputs[0], out.inputs["Surface"])
    return m


def render(name, gray, depth="8", transparent=None):
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    r.filepath = os.path.join(OUT, name, "####")
    r.image_settings.color_mode = "BW" if gray else "RGB"
    r.image_settings.color_depth = depth
    r.film_transparent = gray if transparent is None else transparent
    print(f"── render {name} {F0}-{F1} @ {PCT}%", flush=True)
    bpy.ops.render.render(animation=True)


if "beauty" in PASSES:
    render("beauty", False)

# matte / energy are only used at 576×1248 in the video pack: render at half resolution, fewer samples for speed
if "matte" in PASSES or "energy" in PASSES or "depth" in PASSES:
    r.resolution_percentage = max(25, PCT // 2)
    scene.eevee.taa_render_samples = min(SAMPLES, 8)
    PCT = r.resolution_percentage

if "matte" in PASSES:
    vl.material_override = matte_material()
    holdout({"ENV", "FRIEZA", "CTRL"}, True)
    render("matte", True)
    vl.material_override = None
    holdout({"ENV", "FRIEZA", "CTRL"}, False)

if "energy" in PASSES:
    set_energy_mode(1.0)
    render("energy", True)
    set_energy_mode(0.0)

if "depth" in PASSES:
    # values must go straight to the file: disable tone mapping (Raw), dither, AA (1 sample), motion blur; sky background = farthest (1.0)
    vs = scene.view_settings
    saved = (vs.view_transform, vs.look, r.dither_intensity, r.use_motion_blur, scene.world, r.filter_size)
    try:
        vs.view_transform = "Raw"
    except TypeError:
        pass
    vs.look = "None"
    r.dither_intensity = 0.0
    r.use_motion_blur = False
    r.filter_size = 0.01
    scene.eevee.taa_render_samples = 1
    w = bpy.data.worlds.new("depth_far"); w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 1.0
    scene.world = w
    vl.material_override = depth_material()
    holdout({"CTRL"}, True)
    render("depth", True, "16", transparent=False)
    holdout({"CTRL"}, False)
    vl.material_override = None
    vs.view_transform, vs.look, r.dither_intensity, r.use_motion_blur, scene.world, r.filter_size = saved
