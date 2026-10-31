# Clip demo đăng X (4:3, kiểu "phone mockup"): iPhone 3D khung titan phát bản quay màn hình app,
# nền gradient đổi màu theo từng đoạn phim, chữ lớn phía sau máy, camera zoom/nghiêng theo nhịp, end card.
#
# Chạy: Blender -b --factory-startup -P blender/scripts/promo.py -- \
#         --screen render/promo/screen.mp4 --film-start 3.0 --out render/promo/frames [--pct 100]
import bpy, bmesh, json, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
SCREEN = os.path.abspath(arg("--screen", "render/promo/screen.mp4"))
FILM0 = float(arg("--film-start", "3.0"))      # giây trong bản quay màn hình lúc phim bắt đầu
OUT = os.path.abspath(arg("--out", "render/promo/frames"))
PCT = int(arg("--pct", "100"))
LABEL = arg("--label", "")                     # nhãn nhỏ góc dưới trái (vd "v3"), để so sánh các bản
FPS = 60
P_FILM = 3.0                                   # phim bắt đầu ở giây 3 của clip promo
# phim đã giãn nhịp (retime.py): mọi mốc bên dưới viết theo clip của phim 20 s gốc (phim bắt đầu ở P_FILM)
# → F() quy đổi sang clip mới; FR() là giây thật của clip mới
_TL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app", "assets", "cinematic", "timeline.json")))
_RT = _TL.get("retime", [[0, 0], [1200, 1200]])
FILM = _TL["frames"] / _TL["fps"]


def _rts(sec):
    f = sec * FPS
    for (a, na), (b, nb) in zip(_RT, _RT[1:]):
        if f <= b or [b, nb] == _RT[-1]:
            return (na + (f - a) * (nb - na) / (b - a)) / FPS
    return sec


DUR = P_FILM + FILM + 4.0
# đoạn Kamehameha (v23) chèn giữa phim: không quy đổi được từ giây phim gốc → lấy thẳng từ marker (giây thật)
_KM = {m["name"]: P_FILM + m["f"] / FPS for m in _TL["markers"] if m["name"].startswith("kame:")}
KAME = all(k in _KM for k in ("kame:start", "kame:fire", "kame:hit", "kame:end"))
FR = lambda sec: round(sec * FPS)
F = lambda sec: FR(P_FILM + _rts(sec - P_FILM) if sec > P_FILM else sec)
rad = math.radians

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1440, PCT
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 0, FR(DUR) - 1
sc.view_settings.view_transform = "Standard"
sc.eevee.taa_render_samples = 16
sc.eevee.use_fast_gi = False
sc.render.film_transparent = False


def hexc(h):
    h = h.lstrip("#")
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1.0,)


def mat_emit(name, color, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    e = n.new("ShaderNodeEmission"); e.inputs["Color"].default_value = hexc(color); e.inputs["Strength"].default_value = strength
    o = n.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(e.outputs[0], o.inputs[0])
    return m, e


def link(ob):
    sc.collection.objects.link(ob)
    return ob


# ── nền: mặt phẳng phát sáng, gradient dọc 2 màu, đổi theo đoạn + quầng sáng sau máy ──
SECTIONS = [  # (giây bắt đầu, màu trên, màu dưới)
    (0.0, "#0E2620", "#2F6B57"),     # Namek
    (8.0, "#3A1E05", "#F0A51E"),     # Super Saiyan
    (11.5, "#190A2C", "#7B3FBF"),    # Frieza
    (16.0, "#05272C", "#2E9093"),    # truy đuổi
    (19.5, "#2A0606", "#E2522B"),    # phản đòn
    (23.0, "#1C1306", "#D59A27"),    # end card
]
bg_me = bpy.data.meshes.new("bg")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1)
bm.to_mesh(bg_me); bm.free()
bg = link(bpy.data.objects.new("bg", bg_me))
bg.scale = (16, 12, 1)
bg.rotation_euler = (rad(90), 0, 0)
bg.location = (0, 6, 0)
bgm = bpy.data.materials.new("bg"); bgm.use_nodes = True
N, Lk = bgm.node_tree.nodes, bgm.node_tree.links
N.clear()
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Generated"], sep.inputs[0])
top = N.new("ShaderNodeRGB"); bot = N.new("ShaderNodeRGB")
mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
Lk.new(sep.outputs["Y"], mix.inputs["Factor"])
ca = [s for s in mix.inputs if s.name == "A" and s.type == "RGBA"][0]
cb = [s for s in mix.inputs if s.name == "B" and s.type == "RGBA"][0]
Lk.new(bot.outputs[0], ca); Lk.new(top.outputs[0], cb)
# quầng sáng tròn giữa
grad = N.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
mp = N.new("ShaderNodeMapping"); mp.inputs["Location"].default_value = (0.5, 0.5, 0); mp.inputs["Scale"].default_value = (1.6, 2.1, 1)
sub = N.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0)
Lk.new(tc.outputs["Generated"], sub.inputs[0]); Lk.new(sub.outputs[0], mp.inputs[0]); Lk.new(mp.outputs[0], grad.inputs[0])
glow = N.new("ShaderNodeMath"); glow.operation = "MULTIPLY"; glow.inputs[1].default_value = 0.35
Lk.new(grad.outputs["Fac"], glow.inputs[0])
add = N.new("ShaderNodeMix"); add.data_type = "RGBA"; add.blend_type = "ADD"
Lk.new(glow.outputs[0], add.inputs["Factor"])
Lk.new(mix.outputs[2], [s_ for s_ in add.inputs if s_.name == "A" and s_.type == "RGBA"][0])
[s_ for s_ in add.inputs if s_.name == "B" and s_.type == "RGBA"][0].default_value = (1, 0.92, 0.75, 1)
em = N.new("ShaderNodeEmission"); Lk.new(add.outputs[2], em.inputs["Color"])
out = N.new("ShaderNodeOutputMaterial"); Lk.new(em.outputs[0], out.inputs[0])
bg_me.materials.append(bgm)
SEC_F = [(F(t0), ct, cbm) for t0, ct, cbm in SECTIONS]
if KAME:                                       # xanh Kamehameha, rồi vàng kết trước end card
    SEC_F += [(FR(_KM["kame:start"]), "#04122E", "#2F86E8"), (FR(_KM["kame:end"]), "#2A1A05", "#E0A030")]
    SEC_F.sort()
for i, (f0, ct, cbm) in enumerate(SEC_F):
    keys = [(f0, ct, cbm)]
    if i:
        keys.insert(0, (f0 - 5, SEC_F[i - 1][1], SEC_F[i - 1][2]))   # chuyển màu trong 5 frame
    for f, a, b in keys:
        top.outputs[0].default_value, bot.outputs[0].default_value = hexc(a), hexc(b)
        top.outputs[0].keyframe_insert("default_value", frame=f)
        bot.outputs[0].keyframe_insert("default_value", frame=f)

# ── world: phản chiếu lên khung titan ──
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = hexc("#B9B4AE")
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6


# ── iPhone ──
def rounded_rect(bm, w, h, r, z, segs=14):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(segs + 1):
            a = rad(a0 + 90 * k / segs)
            pts.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z)))
    return bm.faces.new(pts)


PW, PH, PR, THICK = 1.0, 2.13, 0.16, 0.09
SW = PW - 0.06
SH = SW * 2622 / 1206
phone = link(bpy.data.objects.new("PHONE", None))
# khung
me = bpy.data.meshes.new("body"); bm = bmesh.new()
f0 = rounded_rect(bm, PW, PH, PR, -THICK / 2)
ext = bmesh.ops.extrude_face_region(bm, geom=[f0])
bmesh.ops.translate(bm, vec=(0, 0, THICK), verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
body = link(bpy.data.objects.new("body", me))
bev = body.modifiers.new("bevel", "BEVEL"); bev.width, bev.segments, bev.limit_method = 0.025, 5, "ANGLE"
me.shade_smooth() if hasattr(me, "shade_smooth") else None
ti = bpy.data.materials.new("titanium"); ti.use_nodes = True
bsdf = next(n for n in ti.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs["Base Color"].default_value = hexc("#8F8A83"); bsdf.inputs["Metallic"].default_value = 1.0; bsdf.inputs["Roughness"].default_value = 0.32
me.materials.append(ti)
body.parent = phone
body.rotation_euler = (rad(90), 0, 0)
# kính đen + màn hình
for name, wdt, hgt, r, yoff, kind in (("glass", PW - 0.012, PH - 0.012, PR - 0.006, -THICK / 2 - 0.004, "black"),
                                      ("screen", SW, SH, PR - 0.035, -THICK / 2 - 0.006, "screen")):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rounded_rect(bm, wdt, hgt, r, 0)
    uv = bm.loops.layers.uv.new()
    for face in bm.faces:
        for l in face.loops:
            l[uv].uv = (l.vert.co.x / wdt + 0.5, l.vert.co.y / hgt + 0.5)
    bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me))
    ob.parent = phone
    ob.rotation_euler = (rad(90), 0, 0)
    ob.location = (0, yoff, 0)
    if kind == "black":
        me.materials.append(mat_emit("glass", "#050505")[0])
    else:
        sm = bpy.data.materials.new("screen"); sm.use_nodes = True
        n = sm.node_tree.nodes; n.clear()
        tex = n.new("ShaderNodeTexImage")
        img = bpy.data.images.load(SCREEN); img.source = "MOVIE"
        tex.image = img
        iu = tex.image_user
        iu.frame_duration = 100000
        iu.frame_start = F(P_FILM) - round(FILM0 * FPS)   # frame promo đầu tiên của bản quay
        iu.use_auto_refresh = True
        iu.use_cyclic = False
        e = n.new("ShaderNodeEmission"); e.inputs["Strength"].default_value = 1.0
        o = n.new("ShaderNodeOutputMaterial")
        sm.node_tree.links.new(tex.outputs["Color"], e.inputs["Color"]); sm.node_tree.links.new(e.outputs[0], o.inputs[0])
        me.materials.append(sm)
# dynamic island
me = bpy.data.meshes.new("island"); bm = bmesh.new()
rounded_rect(bm, 0.3, 0.085, 0.0425, 0)
bm.to_mesh(me); bm.free()
isl = link(bpy.data.objects.new("island", me))
isl.parent = phone; isl.rotation_euler = (rad(90), 0, 0); isl.location = (0, -THICK / 2 - 0.008, SH / 2 - 0.075)
me.materials.append(mat_emit("island", "#000000")[0])
# nút bên
for i, (x, z, hh) in enumerate(((PW / 2 + 0.006, 0.45, 0.22), (-PW / 2 - 0.006, 0.55, 0.12), (-PW / 2 - 0.006, 0.3, 0.16), (-PW / 2 - 0.006, 0.08, 0.16))):
    me = bpy.data.meshes.new(f"btn{i}"); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=(0.02, 0.04, hh), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    b = link(bpy.data.objects.new(f"btn{i}", me)); b.parent = phone; b.location = (x, 0, z); me.materials.append(ti)

key = bpy.data.lights.new("key", "AREA"); key.energy, key.size = 900, 6
kl = link(bpy.data.objects.new("key", key)); kl.location = (-4, -5, 5); kl.rotation_euler = (rad(50), 0, rad(-40))


# ── chữ ──
def text(name, body, font, size, color, loc, strength=1.0, align="CENTER", extrude=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y, cu.extrude = body, size, align, "CENTER", extrude
    cu.font = bpy.data.fonts.load(font)
    ob = link(bpy.data.objects.new(name, cu))
    ob.rotation_euler = (rad(90), 0, 0)
    ob.location = loc
    cu.materials.append(mat_emit(name + "_m", color, strength)[0])
    return ob


IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
BLACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
DIN = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf"
BIG = [("NAMEK", 3.4, 7.8, "#3F8A71"), ("SUPER SAIYAN", 8.0, 11.5, "#FFE08A"), ("FRIEZA", 11.5, 16.0, "#A877E0"),
       ("CHASE", 16.0, 19.5, "#4FC3C3"), ("IMPACT", 19.5, 23.0, "#FF8A5B")]
BIG_F = [(w_, F(t0), F(t1), c_) for w_, t0, t1, c_ in BIG]
if KAME:
    BIG_F = [(w_, f0, min(f1, FR(_KM["kame:start"])), c_) for w_, f0, f1, c_ in BIG_F]
    BIG_F.append(("KAMEHAMEHA", FR(_KM["kame:start"]), FR(_KM["kame:end"]), "#8FDDFF"))
for word, f0, f1, col in BIG_F:
    ob = text("big_" + word, word, IMPACT, 1.7 if len(word) > 6 else 2.6, col, (0, 4, 0.0), 0.9)
    for f, vis in ((0, False), (f0, True), (f1, False)):
        ob.hide_render = not vis
        ob.keyframe_insert("hide_render", frame=f)
    ob.location = (1.2, 4, 0); ob.keyframe_insert("location", frame=f0)
    ob.location = (-1.2, 4, 0); ob.keyframe_insert("location", frame=f1)

end = [text("logo1", "SAIYAN", BLACK, 0.56, "#FFD23F", (-1.15, 0, 1.0), 1.1),
       text("logo2", "AWAKENING", BLACK, 0.36, "#FFF3B0", (-1.15, 0, 0.52), 1.0),
       text("tag", f"Goku vs Frieza  /  {round(FILM)}s cinematic", DIN, 0.15, "#FFFFFF", (-1.15, 0, 0.0), 1.0),
       text("credit1", "Expo  /  React Native  /  Reanimated", DIN, 0.1, "#FFE9C2", (-1.15, 0, -0.38), 0.9),
       text("credit2", "Skia Graphite + WebGPU  /  Blender  /  Codex", DIN, 0.1, "#FFE9C2", (-1.15, 0, -0.56), 0.9)]
for ob in end:
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=0)
    ob.hide_render = False; ob.keyframe_insert("hide_render", frame=FR(P_FILM + FILM + 0.4))
    ob.scale = (0.85, 0.85, 0.85); ob.keyframe_insert("scale", frame=FR(P_FILM + FILM + 0.4))
    ob.scale = (1, 1, 1); ob.keyframe_insert("scale", frame=FR(P_FILM + FILM + 0.9))

# ── chuyển động: camera + máy ──
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 50; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 24
cam = link(bpy.data.objects.new("cam", cam_d)); sc.camera = cam
if LABEL:                                      # gắn vào camera nên đứng yên một góc màn hình
    lb = text("label", LABEL, DIN, 0.032, "#FFFFFF", (0, 0, 0), 0.75, align="LEFT")
    lb.parent = cam
    lb.location, lb.rotation_euler = (-0.6, -0.43, -2.0), (0, 0, 0)
cam.rotation_euler = (rad(90), 0, 0)


def kc(t, x, y, z, raw=False):
    cam.location = (x, y, z); cam.keyframe_insert("location", frame=FR(t) if raw else F(t))


def kp(t, rx=0, ry=0, rz=0, x=0, z=0, raw=False):
    phone.rotation_euler = (rad(rx), rad(ry), rad(rz)); phone.keyframe_insert("rotation_euler", frame=FR(t) if raw else F(t))
    phone.location = (x, 0, z); phone.keyframe_insert("location", frame=FR(t) if raw else F(t))


p = P_FILM
kc(0, 0, -10.5, 0); kp(0, 10, 0, -28)
kc(p, 0, -7.6, 0); kp(p, 0, 0, -6)
kc(p + 4.0, 0, -6.6, 0.1); kp(p + 4.0, 0, 0, 0)
kc(p + 4.9, 0, -3.0, 0.35)                                  # zoom vào cảnh cận mắt
kc(p + 5.05, 0, -8.6, 0); kp(p + 5.05, 0, 0, 0)            # crash zoom-out đúng lúc nổ
kc(p + 6.5, 0, -7.4, 0); kp(p + 6.5, -4, 0, 4)
kc(p + 8.5, -0.5, -7.2, 0); kp(p + 8.5, -6, 0, 20)
kp(p + 10.0, 2, 0, -14)
kc(p + 13.0, 0.3, -6.6, 0); kp(p + 13.0, 0, 3, -6)
kp(p + 14.2, 4, -6, 12); kp(p + 15.4, -2, 6, -12); kp(p + 16.4, 0, 0, 4)
kc(p + 16.4, 0, -7.0, 0)
kc(p + 17.1, 0, -4.2, 0.1)                                  # zoom vào cú đấm
kc(p + 17.6, 0, -7.8, 0); kp(p + 17.6, 0, 0, 0)
if KAME:                                       # Kamehameha: nghiêng máy lúc tụ khí, zoom sát lúc "HA!", lùi ra khi nổ
    ks, kf, kh, ke = _KM["kame:start"], _KM["kame:fire"], _KM["kame:hit"], _KM["kame:end"]
    kc(ks + 0.2, 0, -7.4, 0, raw=True); kp(ks + 0.2, -3, 0, 10, raw=True)
    kc(kf - 0.15, 0, -5.4, 0.15, raw=True); kp(kf - 0.15, 0, 0, -4, raw=True)
    kc(kf + 0.1, 0, -6.6, 0.05, raw=True)
    kc(kh + 0.1, 0, -8.2, 0, raw=True); kp(kh + 0.1, 2, 0, 6, raw=True)
    kc(ke - 0.1, 0, -7.6, 0, raw=True); kp(ke - 0.1, 0, 0, 0, raw=True)
kc(p + FILM, 0, -7.6, 0, raw=True); kp(p + FILM, 0, 0, -4, 0, raw=True)
kc(p + FILM + 0.9, 0, -8.6, 0, raw=True); kp(p + FILM + 0.9, 0, 0, -16, 1.75, raw=True)
kc(DUR, 0, -8.4, 0, raw=True); kp(DUR, 0, 0, -20, 1.75, raw=True)
for ob in (cam, phone):
    for fc in (ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, "fcurves") else []):
        for k in fc.keyframe_points:
            k.interpolation, k.easing = "BEZIER", "AUTO"
# rung khi nổ / đấm: camera là con của một Empty, rung trên Empty để không đụng keyframe di chuyển
rig = link(bpy.data.objects.new("shake", None))
cam.parent = rig
rig.location = (0, 0, 0); rig.keyframe_insert("location", frame=0)
for f0 in [F(p + 5.0), F(p + 17.17)] + ([FR(_KM["kame:fire"]), FR(_KM["kame:hit"])] if KAME else []):
    for i in range(12):
        a = (1 - i / 12) * 0.07
        rig.location = (a * (1 if i % 2 else -1), 0, a * 0.6 * (1 if i % 3 else -1))
        rig.keyframe_insert("location", frame=f0 + i * 2)
    rig.location = (0, 0, 0); rig.keyframe_insert("location", frame=f0 + 26)

os.makedirs(OUT, exist_ok=True)
sc.render.image_settings.file_format = "PNG"
STILLS = arg("--stills", "")
if STILLS:                                     # duyệt nhanh vài khoảnh khắc (giây trong clip promo)
    for sec in (float(x) for x in STILLS.split(",")):
        sc.frame_set(FR(sec))                     # giây thật của clip mới
        sc.render.filepath = os.path.join(OUT, f"still_{sec:05.2f}.png")
        bpy.ops.render.render(write_still=True)
    sys.exit(0)
sc.render.filepath = os.path.join(OUT, "####")
print("PROMO frames", sc.frame_end + 1)
bpy.ops.render.render(animation=True)
print("PROMO DONE", OUT)
