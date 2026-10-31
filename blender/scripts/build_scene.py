# Dựng toàn bộ cảnh "Saiyan Awakening" bằng code: Namek, Goku/Frieza (placeholder toon),
# vũ đạo 20 giây, camera 10 shot, Empty FX (track hiệu ứng), marker haptic/cut.
#
# Chạy: /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
#         -P blender/scripts/build_scene.py
# Kết quả: blender/goku_vs_frieza.blend
import bpy, bmesh, glob, math, os, random
from mathutils import Vector, Quaternion, Euler, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(os.path.dirname(HERE), "textures")
BLEND = os.environ.get("GVF_BLEND") or os.path.join(os.path.dirname(HERE), "goku_vs_frieza.blend")
FPS, FRAMES = 60, 1200
W, H = 1152, 2496
rad = math.radians
random.seed(7)

if bpy.app.background:
    bpy.ops.wm.read_factory_settings(use_empty=True)
else:                                   # chạy trong Blender đang mở (MCP lookdev): giữ addon
    bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.name = "Cinematic"


# ───────────────────────────── render settings ─────────────────────────────
def setup_render():
    r = scene.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.fps = FPS
    scene.frame_start, scene.frame_end = 0, FRAMES - 1
    r.film_transparent = False
    r.filter_size = 1.0
    r.use_motion_blur = False          # render_passes.py bật cho bản final
    r.motion_blur_shutter = 0.3        # v23: 0.5 nhoè nhân vật khi bay nhanh, aura app vẽ lên phần nhoè trông như lệch lớp
    try:
        r.motion_blur_position = "START"  # tránh nhoè qua điểm cut
    except TypeError:
        pass
    scene.eevee.taa_render_samples = 16
    scene.eevee.use_fast_gi = False      # GI screen-space gây lấm tấm nhiễu qua ngưỡng toon
    scene.eevee.use_raytracing = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    r.dither_intensity = 1.0


# ───────────────────────────── collections ─────────────────────────────
def coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


C_ENV, C_GOKU, C_FRIEZA, C_LIGHT, C_CTRL = (coll(n) for n in ("ENV", "GOKU", "FRIEZA", "LIGHTS", "CTRL"))


# ───────────────────────────── materials ─────────────────────────────
def hexc(h, a=1.0):
    h = h.lstrip("#")
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (a,)


def _energy_tail(nt, surface, energy):
    """Mọi material kết thúc bằng Mix(surface, Emission(energy)): render_passes.py bật
    `energy_mode` = 1 để xuất lớp năng lượng (chỉ vật phát sáng còn trắng)."""
    N, L = nt.nodes, nt.links
    ev = N.new("ShaderNodeValue"); ev.name = "energy"; ev.outputs[0].default_value = energy
    ee = N.new("ShaderNodeEmission"); ee.inputs["Color"].default_value = (1, 1, 1, 1)
    L.new(ev.outputs[0], ee.inputs["Strength"])
    mode = N.new("ShaderNodeValue"); mode.name = "energy_mode"; mode.outputs[0].default_value = 0.0
    mix = N.new("ShaderNodeMixShader")
    L.new(mode.outputs[0], mix.inputs[0])
    L.new(surface, mix.inputs[1])
    L.new(ee.outputs[0], mix.inputs[2])
    out = N.new("ShaderNodeOutputMaterial")
    L.new(mix.outputs[0], out.inputs["Surface"])


def toon(name, base, shade, light=None, glow=0.0, energy=0.0, threshold=0.2, rim=0.0, spec=0.0, bands=0.0):
    """Cel-shading: Diffuse → Shader to RGB → ColorRamp (Constant) → Emission.
    rim: viền sáng ở mép phía được chiếu (kiểu anime); spec: đốm bóng gắt (Frieza, tóc)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    diff = N.new("ShaderNodeBsdfDiffuse")
    s2r = N.new("ShaderNodeShaderToRGB")
    ramp = N.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    cr.elements[0].position, cr.elements[0].color = 0.0, hexc(shade)
    cr.elements[1].position, cr.elements[1].color = threshold, hexc(base)
    if light:
        e = cr.elements.new(0.92)
        e.color = hexc(light)
    L.new(diff.outputs[0], s2r.inputs[0])
    L.new(s2r.outputs["Color"], ramp.inputs["Fac"])
    color = ramp.outputs["Color"]
    if rim > 0 or spec > 0:
        # pháp tuyến trong không gian camera: viền sáng + đốm bóng luôn hiện, không phụ thuộc hướng đèn
        geo = N.new("ShaderNodeNewGeometry")
        vt = N.new("ShaderNodeVectorTransform")
        vt.vector_type, vt.convert_from, vt.convert_to = "NORMAL", "WORLD", "CAMERA"
        L.new(geo.outputs["Normal"], vt.inputs[0])

        def dot_gt(vec, thr):
            dp = N.new("ShaderNodeVectorMath"); dp.operation = "DOT_PRODUCT"
            L.new(vt.outputs[0], dp.inputs[0]); dp.inputs[1].default_value = Vector(vec).normalized()
            gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = thr
            L.new(dp.outputs["Value"], gt.inputs[0])
            return gt.outputs[0]

        def mix_toward(col, fac_socket, amount, target):
            k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = amount
            L.new(fac_socket, k.inputs[0])
            mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
            mx.inputs[7].default_value = target
            L.new(k.outputs[0], mx.inputs[0]); L.new(col, mx.inputs[6])
            return mx.outputs[2]

        if rim > 0:
            lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
            edge = N.new("ShaderNodeMath"); edge.operation = "GREATER_THAN"; edge.inputs[1].default_value = 0.62
            L.new(lw.outputs["Facing"], edge.inputs[0])
            both = N.new("ShaderNodeMath"); both.operation = "MULTIPLY"
            L.new(edge.outputs[0], both.inputs[0]); L.new(dot_gt((0.7, 0.55, 0.0), 0.2), both.inputs[1])
            color = mix_toward(color, both.outputs[0], rim, hexc(light or "#FFFFFF"))
        if spec > 0:
            color = mix_toward(color, dot_gt((-0.35, 0.55, 0.76), 0.93), spec, (1, 1, 1, 1))
    if bands > 0:                                # vân đá nằm ngang (cột đá Namek)
        geo2 = N.new("ShaderNodeNewGeometry")
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo2.outputs["Position"], sep.inputs[0])
        wob = N.new("ShaderNodeTexNoise"); wob.inputs["Scale"].default_value = 0.35
        L.new(geo2.outputs["Position"], wob.inputs["Vector"])
        zz = N.new("ShaderNodeMath"); zz.operation = "MULTIPLY_ADD"
        zz.inputs[1].default_value = 3.0
        L.new(wob.outputs["Fac"], zz.inputs[0]); L.new(sep.outputs["Z"], zz.inputs[2])
        sn = N.new("ShaderNodeMath"); sn.operation = "SINE"
        sc = N.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 0.9
        L.new(zz.outputs[0], sc.inputs[0]); L.new(sc.outputs[0], sn.inputs[0])
        gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.45
        L.new(sn.outputs[0], gt.inputs[0])
        k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = bands
        L.new(gt.outputs[0], k.inputs[0])
        mb = N.new("ShaderNodeMix"); mb.data_type = "RGBA"; mb.blend_type = "MULTIPLY"
        mb.inputs[7].default_value = (0.78, 0.82, 0.8, 1)
        L.new(k.outputs[0], mb.inputs[0]); L.new(color, mb.inputs[6])
        color = mb.outputs[2]
    g = N.new("ShaderNodeValue"); g.name = "glow"; g.outputs[0].default_value = glow
    add = N.new("ShaderNodeMath"); add.operation = "ADD"; add.inputs[1].default_value = 1.0
    em = N.new("ShaderNodeEmission")
    L.new(color, em.inputs["Color"])
    L.new(g.outputs[0], add.inputs[0])
    L.new(add.outputs[0], em.inputs["Strength"])
    _energy_tail(nt, em.outputs[0], energy)
    return m


def toon_tex(name, png, tile=8.0, shade=(0.68, 0.74, 0.8), threshold=0.25, fallback=None, flow=0.0, box=False, haze=0.38):
    """Cel-shading trên ảnh vẽ tay lặp lại theo toạ độ world XY (mặt đất): vùng tối = ảnh × `shade`."""
    path = os.path.join(TEX, png)
    if not os.path.exists(path):
        return fallback
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    geo = N.new("ShaderNodeNewGeometry")
    sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 1.0 / tile
    L.new(geo.outputs["Position"], sc.inputs[0])
    if flow:                                   # nước trôi: cộng độ lệch theo thời gian vào toạ độ
        fv = N.new("ShaderNodeValue"); fv.name = "flow"
        fv.outputs[0].default_value = 0.0; fv.outputs[0].keyframe_insert("default_value", frame=0)
        fv.outputs[0].default_value = flow; fv.outputs[0].keyframe_insert("default_value", frame=FRAMES - 1)
        for fc in _fcurves(m.node_tree.animation_data):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        comb = N.new("ShaderNodeCombineXYZ"); L.new(fv.outputs[0], comb.inputs["X"]); L.new(fv.outputs[0], comb.inputs["Y"])
        ad = N.new("ShaderNodeVectorMath"); ad.operation = "ADD"
        L.new(sc.outputs[0], ad.inputs[0]); L.new(comb.outputs[0], ad.inputs[1])
        sc = ad
    t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True); t.extension = "REPEAT"
    if box:                                    # mặt đứng (cột đá): chiếu hộp theo toạ độ world
        t.projection, t.projection_blend = "BOX", 0.25
    L.new(sc.outputs[0], t.inputs["Vector"])
    diff = N.new("ShaderNodeBsdfDiffuse")
    s2r = N.new("ShaderNodeShaderToRGB"); L.new(diff.outputs[0], s2r.inputs[0])
    bw = N.new("ShaderNodeRGBToBW"); L.new(s2r.outputs["Color"], bw.inputs[0])
    lit = N.new("ShaderNodeMath"); lit.operation = "GREATER_THAN"; lit.inputs[1].default_value = threshold
    L.new(bw.outputs[0], lit.inputs[0])
    dark = N.new("ShaderNodeMix"); dark.data_type = "RGBA"; dark.blend_type = "MULTIPLY"
    dark.inputs[0].default_value = 1.0; dark.inputs[7].default_value = tuple(shade) + (1.0,)
    L.new(t.outputs["Color"], dark.inputs[6])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    L.new(lit.outputs[0], mx.inputs[0]); L.new(dark.outputs[2], mx.inputs[6]); L.new(t.outputs["Color"], mx.inputs[7])
    color = mx.outputs[2]
    if haze:                                   # phối cảnh khí quyển: càng xa camera càng nhạt dần về màu chân trời
        cam = N.new("ShaderNodeCameraData")
        hz = N.new("ShaderNodeMapRange")
        hz.inputs["From Min"].default_value, hz.inputs["From Max"].default_value = 25.0, 180.0
        hz.inputs["To Min"].default_value, hz.inputs["To Max"].default_value = 0.0, haze
        L.new(cam.outputs["View Distance"], hz.inputs["Value"])
        hm = N.new("ShaderNodeMix"); hm.data_type = "RGBA"
        hm.inputs[7].default_value = hexc("#86B9A2")
        L.new(hz.outputs["Result"], hm.inputs[0]); L.new(color, hm.inputs[6])
        color = hm.outputs[2]
    dim = N.new("ShaderNodeValue"); dim.name = "dim"; dim.outputs[0].default_value = 1.0   # choreograph tối dần khi trời giông
    em = N.new("ShaderNodeEmission"); L.new(color, em.inputs["Color"]); L.new(dim.outputs[0], em.inputs["Strength"])
    _energy_tail(nt, em.outputs[0], 0.0)
    return m


def rock_small_mat(name="rock_small"):
    """Đá nhỏ trên cỏ kiểu anime: 3 tông cel (bóng / nền / mặt trên sáng theo pháp tuyến world, nên nhìn từ trên
    xuống vẫn ra khối), vân rock.jpg chỉ điều sắc độ nhẹ, xanh xám ngả lam hợp tông Namek, có haze như mặt đất."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    # sáng/tối theo N·L với hướng key_sun (50°, 0, −35°) thay vì Shader-to-RGB: đá nhỏ + viền solidify tự đổ bóng
    # lên chính nó khi shadow map thô (camera xa) → cả hòn đá thành một mảng tối
    geo = N.new("ShaderNodeNewGeometry")
    ndl = N.new("ShaderNodeVectorMath"); ndl.operation = "DOT_PRODUCT"
    L.new(geo.outputs["Normal"], ndl.inputs[0]); ndl.inputs[1].default_value = Vector((-0.44, -0.63, 0.64)).normalized()
    lit = N.new("ShaderNodeMath"); lit.operation = "GREATER_THAN"; lit.inputs[1].default_value = 0.08
    L.new(ndl.outputs["Value"], lit.inputs[0])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], sep.inputs[0])
    top = N.new("ShaderNodeMath"); top.operation = "GREATER_THAN"; top.inputs[1].default_value = 0.72
    L.new(sep.outputs["Z"], top.inputs[0])
    side = N.new("ShaderNodeMath"); side.operation = "LESS_THAN"; side.inputs[1].default_value = 0.25   # mặt hông dốc: tối hơn
    L.new(sep.outputs["Z"], side.inputs[0])
    c = N.new("ShaderNodeMix"); c.data_type = "RGBA"            # bóng (không được chiếu) ↔ nền
    c.inputs[6].default_value = hexc("#3C5C5D"); c.inputs[7].default_value = hexc("#698B85")
    L.new(lit.outputs[0], c.inputs[0])
    sd = N.new("ShaderNodeMix"); sd.data_type = "RGBA"
    sd.inputs[7].default_value = hexc("#50716E")
    k = N.new("ShaderNodeMath"); k.operation = "MULTIPLY"; L.new(side.outputs[0], k.inputs[0]); L.new(lit.outputs[0], k.inputs[1])
    L.new(k.outputs[0], sd.inputs[0]); L.new(c.outputs[2], sd.inputs[6])
    hi = N.new("ShaderNodeMix"); hi.data_type = "RGBA"
    hi.inputs[7].default_value = hexc("#8DB0A3")
    k2 = N.new("ShaderNodeMath"); k2.operation = "MULTIPLY"; L.new(top.outputs[0], k2.inputs[0]); L.new(lit.outputs[0], k2.inputs[1])
    L.new(k2.outputs[0], hi.inputs[0]); L.new(sd.outputs[2], hi.inputs[6])
    color = hi.outputs[2]
    path = os.path.join(TEX, "rock.jpg")
    if os.path.exists(path):                    # vân đá: chỉ nhân sắc độ 0.86–1.08, không đổi màu
        sc = N.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 1.0 / 0.7
        L.new(geo.outputs["Position"], sc.inputs[0])
        t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        t.projection, t.projection_blend = "BOX", 0.3
        L.new(sc.outputs[0], t.inputs["Vector"])
        tb = N.new("ShaderNodeRGBToBW"); L.new(t.outputs["Color"], tb.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.15, 0.6
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.86, 1.08
        L.new(tb.outputs[0], mr.inputs["Value"])
        mul = N.new("ShaderNodeVectorMath"); mul.operation = "SCALE"
        L.new(color, mul.inputs[0]); L.new(mr.outputs["Result"], mul.inputs["Scale"])
        color = mul.outputs[0]
    cam = N.new("ShaderNodeCameraData")
    hz = N.new("ShaderNodeMapRange")
    hz.inputs["From Min"].default_value, hz.inputs["From Max"].default_value = 25.0, 180.0
    hz.inputs["To Min"].default_value, hz.inputs["To Max"].default_value = 0.0, 0.38
    L.new(cam.outputs["View Distance"], hz.inputs["Value"])
    hm = N.new("ShaderNodeMix"); hm.data_type = "RGBA"
    hm.inputs[7].default_value = hexc("#86B9A2")
    L.new(hz.outputs["Result"], hm.inputs[0]); L.new(color, hm.inputs[6])
    em = N.new("ShaderNodeEmission"); L.new(hm.outputs[2], em.inputs["Color"])
    _energy_tail(nt, em.outputs[0], 0.0)
    return m


def rock_lump(bm, center, r, rng, squash=0.72):
    """Một hòn đá nhỏ có khối: icosphere méo ngẫu nhiên, đáy phẳng chìm nhẹ, ~70% nhô khỏi mặt cỏ."""
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=r)
    rot = Euler((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(0, 6.3))).to_matrix()
    sx, sy = rng.uniform(0.85, 1.25), rng.uniform(0.75, 1.05)
    for v in tmp.verts:
        q = Vector((v.co.x * sx, v.co.y * sy, v.co.z * squash)) * rng.uniform(0.86, 1.12)
        q = rot @ q
        q.z = max(q.z, -r * squash * 0.3)       # đáy phẳng
        v.co = q + Vector((center[0], center[1], r * squash * 0.3 - 0.02))
    _merge(bm, tmp)


def tex_mat(name, png, strength=1.0, energy=0.0):
    """Decal mặt vẽ sẵn (face_textures.py): ảnh RGBA → Emission, phần trong suốt bỏ qua (dithered)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    img = bpy.data.images.load(os.path.join(TEX, png), check_existing=True)
    t = N.new("ShaderNodeTexImage"); t.image = img; t.interpolation = "Cubic"; t.extension = "CLIP"
    em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = strength
    L.new(t.outputs["Color"], em.inputs["Color"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    L.new(t.outputs["Alpha"], mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    _energy_tail(nt, mix.outputs[0], energy)
    # lớp năng lượng cũng phải theo alpha, nếu không cả miếng dán chữ nhật sẽ sáng lên
    # so theo tên: wrapper Python của node bpy tạo mới mỗi lần truy cập nên `is not` luôn đúng (trước v25 lỗi này nối
    # nhầm → lớp energy không theo alpha, cả miếng dán mắt SSJ sáng thành mảng chữ nhật, app bloom mờ trắng nửa mặt)
    ee = next(n for n in N if n.type == "EMISSION" and n.name != em.name)
    tail = next(n for n in N if n.type == "MIX_SHADER" and n.name != mix.name)
    tr2 = N.new("ShaderNodeBsdfTransparent")
    m2 = N.new("ShaderNodeMixShader")
    L.new(t.outputs["Alpha"], m2.inputs[0]); L.new(tr2.outputs[0], m2.inputs[1]); L.new(ee.outputs[0], m2.inputs[2])
    L.new(m2.outputs[0], tail.inputs[2])
    if energy > 0:
        # v25 chỉ phần màu (mống mắt xanh) phát sáng: tròng trắng + mi đen không vào lớp energy
        # (trước cả con mắt trắng loé → app bloom thành mảng mờ trắng che nửa mặt Goku SSJ)
        sp = N.new("ShaderNodeSeparateColor"); L.new(t.outputs["Color"], sp.inputs[0])
        mx = N.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
        L.new(sp.outputs[1], mx.inputs[0]); L.new(sp.outputs[2], mx.inputs[1])
        df = N.new("ShaderNodeMath"); df.operation = "SUBTRACT"
        L.new(mx.outputs[0], df.inputs[0]); L.new(sp.outputs[0], df.inputs[1])
        wt = N.new("ShaderNodeMath"); wt.operation = "MULTIPLY"; wt.use_clamp = True; wt.inputs[1].default_value = 3.0
        L.new(df.outputs[0], wt.inputs[0])
        ev = N["energy"]
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        L.new(ev.outputs[0], mul.inputs[0]); L.new(wt.outputs[0], mul.inputs[1])
        L.new(mul.outputs[0], ee.inputs["Strength"])
    try:
        m.surface_render_method = "DITHERED"
    except (AttributeError, TypeError):
        m.blend_method = "HASHED"
    return m


def flat(name, color, strength=1.0, energy=0.0, backface=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hexc(color)
    em.inputs["Strength"].default_value = strength
    _energy_tail(nt, em.outputs[0], energy)
    m.use_backface_culling = backface
    return m


M = {
    "skin": toon("skin", "#FAD3AE", "#EBAA88", "#FFE8D0", rim=0.7),
    "gi": toon("gi", "#F58A24", "#D0602A", "#FFB45C", rim=0.7),
    "blue": toon("blue", "#2C50B4", "#1E347A", "#5B80E0", rim=0.7),
    "hair": toon("hair", "#1F1F25", "#08080B", "#3E3F49", threshold=0.5, rim=0.8, spec=0.6),
    "hair_ssj": toon("hair_ssj", "#FFDA4A", "#EF9F30", "#FFEE9A", glow=0.05, energy=0.15, threshold=0.4, rim=0.8, spec=0.5),
    "eye": flat("eye", "#101018"),
    "eye_ssj": flat("eye_ssj", "#2EC4B6", 1.2, energy=0.6),
    "f_white": toon("f_white", "#F7F4FB", "#D3C8E8", "#FFFFFF", rim=0.6),
    "f_purple": toon("f_purple", "#9A44CC", "#5A2280", "#C88AF0", rim=0.8, spec=0.9),
    "f_eye": flat("f_eye", "#D7263D", 1.0, energy=0.2),
    "ground": toon("ground", "#5FA38F", "#3B6E62", threshold=0.25),
    "grass_top": toon("grass_top", "#77C08C", "#4A8661", threshold=0.25),
    "rock": toon("rock", "#86A88C", "#557463", "#B4D2B8", threshold=0.3, bands=1.0),
    "rock_small": rock_small_mat(),
    "water": toon("water", "#3E9C9A", "#2A6F72", "#8ED9CF", threshold=0.35),
    "trunk": toon("trunk", "#B9B07E", "#7D7550"),
    "canopy": toon("canopy", "#6FC6A0", "#3F8C6E", "#A6E8C4"),
    "crack": flat("crack", "#FFD45C", 1.2, energy=0.6),
    "crack_edge": flat("crack_edge", "#4A2414", 1.0),   # khe nứt rực sáng lúc gồng khí
    "cloud": toon("cloud", "#6F9A82", "#46685A", "#A9CDB6", threshold=0.3),
    "debris": toon("debris", "#8FA890", "#5C7564"),
    "grass_dark": toon("grass_dark", "#4F9480", "#356657", threshold=0.25),
    "house": toon("house", "#F1EDDC", "#C9C2A5", "#FFFFF4", rim=0.5),
    "window": flat("window", "#2F3E3A"),
    "splash": toon("splash", "#E7FBF6", "#8ED9CF"),
    "outline": flat("outline", "#2B1B17", backface=True),
}


# ───────────────────────────── geometry helpers ─────────────────────────────
# nét viền màu (colored lineart): mỗi chất liệu nhân vật có viền là tông tối của chính nó thay vì nâu đen chung
LINE_COLORS = {"skin": "#8E4A30", "gi": "#7E2C0C", "blue": "#0E1A4A", "hair": "#05050C", "hair_ssj": "#A0560A",
               "f_white": "#3E2A66", "f_purple": "#2A0C44", "boot_tie": "#5A0C10", "white": "#3A3A55",
               "rock_small": "#24403C"}
_LINES = {}


def line_mat(mat):
    key = mat.name if mat.name in LINE_COLORS else None
    if key is None:
        return M["outline"]
    if key not in _LINES:
        _LINES[key] = flat(f"line_{key}", LINE_COLORS[key], backface=True)
    return _LINES[key]


def _obj(name, bm, mat, col, smooth=True, outline=0.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    me.materials.append(mat)
    if outline > 0:
        me.materials.append(line_mat(mat))
        mod = ob.modifiers.new("Outline", "SOLIDIFY")
        mod.thickness, mod.offset = outline, 1.0
        mod.use_flip_normals, mod.use_rim = True, False
        mod.material_offset = 1
    return ob


def sphere(name, r, mat, col, scale=(1, 1, 1), seg=24, outline=0.006):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return _obj(name, bm, mat, col, outline=outline)


def cyl(name, r1, r2, depth, mat, col, seg=16, outline=0.006, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r1, radius2=r2, depth=depth)
    return _obj(name, bm, mat, col, smooth=smooth, outline=outline)


def box(name, size, mat, col, outline=0.004):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    return _obj(name, bm, mat, col, smooth=False, outline=outline)


def torus(name, R, r, mat, col, seg=32, ring=10, scale=(1, 1, 1), outline=0.005):
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        rings.append([bm.verts.new((
            (R + r * math.cos(b)) * math.cos(a) * scale[0],
            (R + r * math.cos(b)) * math.sin(a) * scale[1],
            r * math.sin(b) * scale[2])) for b in (2 * math.pi * j / ring for j in range(ring))])
    for i in range(seg):
        for j in range(ring):
            a, b = rings[i], rings[(i + 1) % seg]
            bm.faces.new((a[j], b[j], b[(j + 1) % ring], a[(j + 1) % ring]))
    return _obj(name, bm, mat, col, outline=outline)


def spikes(name, center_r, spec, mat, col, cap=None, outline=0.006):
    """Tóc anime: gom nhiều chóp nón (và một chỏm cap) thành 1 mesh, gốc ở tâm đầu."""
    bm = bmesh.new()
    if cap:
        tmp = bmesh.new()
        bmesh.ops.create_uvsphere(tmp, u_segments=20, v_segments=12, radius=center_r * cap[0])
        for v in tmp.verts:
            v.co = Vector((v.co.x, v.co.y * cap[1], v.co.z)) + Vector((0, cap[2], cap[3]))
        _merge(bm, tmp)
    for az, el, length, radius in spec:
        d = Vector((math.cos(rad(el)) * math.sin(rad(az)),
                    math.cos(rad(el)) * math.cos(rad(az)),
                    math.sin(rad(el))))
        tmp = bmesh.new()
        bmesh.ops.create_cone(tmp, cap_ends=True, cap_tris=False, segments=6,
                              radius1=radius, radius2=0.0, depth=length)
        q = d.to_track_quat("Z", "Y")
        pos = d * (center_r * 0.72 + length * 0.5)
        bmesh.ops.transform(tmp, matrix=Matrix.Translation(pos) @ q.to_matrix().to_4x4(), verts=tmp.verts)
        _merge(bm, tmp)
    return _obj(name, bm, mat, col, smooth=False, outline=outline)


def _merge(dst, src):
    me = bpy.data.meshes.new("_tmp")
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


def empty(name, col, parent=None, loc=(0, 0, 0), size=0.1):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = size
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    e.rotation_mode = "XYZ"
    return e


def attach(ob, parent, loc, rot=(0, 0, 0)):
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = tuple(rad(a) for a in rot)
    return ob


# ───────────────────────────── characters (chibi) ─────────────────────────────
M.update({
    "white": toon("white", "#FFFFFF", "#C9CFE0", threshold=0.15),
    "iris": flat("iris", "#15141F"),
    "iris_ssj": flat("iris_ssj", "#22B8B0", 1.15, energy=0.6),
    "pupil": flat("pupil", "#05050A"),
    "shine": flat("shine", "#FFFFFF", 1.4),
    "blush": toon("blush", "#F7A3A0", "#E88480", threshold=0.1),
    "mouth": flat("mouth", "#5A1E1E"),
    "tongue": flat("tongue", "#E0606A"),
    "brow_ssj": toon("brow_ssj", "#F4C534", "#D19A12"),
    "ink": flat("ink", "#1A1414"),
    "boot_sole": toon("boot_sole", "#3A2A28", "#1E1514"),
    "boot_tie": toon("boot_tie", "#C22F35", "#86181F", "#F0636A", rim=0.6),
    "f_iris": flat("f_iris", "#E0263F", 1.1, energy=0.15),
    "f_lip": flat("f_lip", "#5B2A7A"),
    "charge": flat("charge", "#FF7BE0", 1.6, energy=0.9),
    "star_in": flat("star_in", "#FFF8D8", 1.6, energy=1.0),
    "star_out": flat("star_out", "#FF8A1E", 1.3, energy=0.6),
})
FONT_PATHS = ["/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc", "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
              "/System/Library/Fonts/Hiragino Sans GB.ttc"]


def capsule(name, r, length, mat, col, scale=(1, 1, 1), seg=24, outline=0.005):
    """Viên thuốc trục Z, tâm ở gốc: tay chân bo tròn mềm."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2 + 1, radius=r)
    for v in bm.verts:
        v.co.z += length / 2 if v.co.z > 1e-6 else (-length / 2 if v.co.z < -1e-6 else 0)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return _obj(name, bm, mat, col, outline=outline)


def tcap(name, r_top, r_bot, length, mat, col, scale=(1, 1, 1), seg=24, outline=0.005):
    """Viên thuốc thon: nửa trên bán kính r_top, nửa dưới r_bot (ống quần, bắp tay, eo)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2 + 1, radius=1.0)
    for v in bm.verts:
        r = r_top if v.co.z > 1e-6 else r_bot
        v.co = Vector((v.co.x * r, v.co.y * r, v.co.z * r + (length / 2 if v.co.z > 1e-6 else -length / 2)))
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return _obj(name, bm, mat, col, outline=outline)


def skin_limb(name, prof, joint_a, joint_b, mat, col, seg=28, rfn=None, blend=0.045, outline=0.005):
    """Tay/chân liền một khối (thay 2 khúc cứng nối ở khớp như ma-nơ-canh): biên dạng [(z, r)] trong không gian khớp A
    chạy qua khớp B (z = B.location.z) tới đầu chi. Phần trên đi theo A (vật là con của A), phần dưới bẻ theo B qua
    Hook có trọng số chuyển mượt quanh khớp (±blend) → khuỷu/gối cong liền như da thật, không gãy khúc, không lộ mép.
    rfn(t, z, r, w): nắn mặt cắt (cơ bắp), w = trọng số phần dưới (0 trên khớp → 1 dưới khớp)."""
    off = Vector(joint_b.location)
    bm = bmesh.new()
    dl = bm.verts.layers.deform.verify()
    rings = []
    for z, r in prof:
        w = _smooth(off.z + blend, off.z - blend, z)
        c0 = Vector((off.x * w, off.y * w, z))
        ring = []
        for i in range(seg):
            t = math.tau * i / seg
            rr = rfn(t, z, r, w) if rfn else r
            v = bm.verts.new(c0 + Vector((rr * math.cos(t), rr * math.sin(t), 0)))
            v[dl][0] = w
            ring.append(v)
        rings.append((ring, c0, w))
    for (a, _, _), (b, _, _) in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    for ring, c0, w in (rings[0], rings[-1]):
        cv = bm.verts.new(c0)
        cv[dl][0] = w
        for i in range(seg):
            bm.faces.new((cv, ring[i], ring[(i + 1) % seg]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(name, bm, mat, col, outline=outline)
    ob.vertex_groups.new(name="bend")            # nhóm 0 = lớp deform đã ghi ở trên
    attach(ob, joint_a, (0, 0, 0))
    hk = ob.modifiers.new("bend", "HOOK")
    hk.object, hk.vertex_group, hk.falloff_type = joint_b, "bend", "NONE"
    hk.matrix_inverse = Matrix.Translation(off).inverted()
    ob.modifiers.move(len(ob.modifiers) - 1, 0)  # bẻ trước, viền (solidify) sau → viền đi theo khớp
    return ob


def lathe(name, prof, mat, col, seg=32, scale=(1, 1, 1), rfn=None, outline=0.005):
    """Khối tròn xoay quanh trục Z theo biên dạng [(z, r), ...] từ trên xuống (ống quần phồng, đai vải).
    rfn(t, z, r) → r': chỉnh bán kính theo góc t để nắn nếp vải dồn / ép mặt trong."""
    bm = bmesh.new()
    rings = [[bm.verts.new(((rfn(t, z, r) if rfn else r) * math.cos(t) * scale[0],
                            (rfn(t, z, r) if rfn else r) * math.sin(t) * scale[1], z * scale[2]))
              for t in (math.tau * i / seg for i in range(seg))] for z, r in prof]
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    for ring, z in ((rings[0], prof[0][0]), (rings[-1], prof[-1][0])):
        cv = bm.verts.new((0, 0, z * scale[2]))
        for i in range(seg):
            bm.faces.new((cv, ring[i], ring[(i + 1) % seg]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj(name, bm, mat, col, outline=outline)


def head_dir(az, el):
    """Hướng từ tâm đầu (local). az=180 là chính diện (-Y), az>180 lệch sang phải nhân vật (-X)."""
    return Vector((math.cos(rad(el)) * math.sin(rad(az)), math.cos(rad(el)) * math.cos(rad(az)), math.sin(rad(el))))


def decal(name, parent, center, R, az, el, w, h, mat, col, layer=0, roll=0.0, depth=0.012):
    """Chi tiết phẳng dán trên mặt cầu của đầu (mắt, má, miệng...), xếp lớp theo `layer`."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)
    bmesh.ops.scale(bm, vec=Vector((w / 2, h / 2, depth / 2)), verts=bm.verts)
    ob = _obj(name, bm, mat, col, outline=0)
    d = head_dir(az, el)
    q = d.to_track_quat("Z", "Y") @ Quaternion((0, 0, 1), rad(roll))
    ob.parent = parent
    ob.location = center + d * (R + 0.002 + layer * 0.0035)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = q
    return ob


def face_decal(name, parent, center, radii, az, el, w, h, mat, col, layer=0, roll=0.0, grid=10):
    """Miếng dán có UV ôm sát đầu elip (bán trục `radii`): dùng cho mắt/miệng/má vẽ sẵn.
    UV +u hướng sang phải nhân vật (-X), +v hướng lên, nên ảnh mắt phải có khoé ngoài ở +u."""
    a, b, c = radii
    d0 = head_dir(az, el)
    surf = lambda d: d / math.sqrt((d.x / a) ** 2 + (d.y / b) ** 2 + (d.z / c) ** 2)
    p0 = surf(d0)
    n0 = Vector((p0.x / a ** 2, p0.y / b ** 2, p0.z / c ** 2)).normalized()
    up = (Vector((0, 0, 1)) - n0 * n0.z).normalized()
    right = n0.cross(up).normalized()          # mặt nhìn -Y: n × up trỏ về -X (phải nhân vật)
    q = Quaternion(n0, rad(roll))
    up, right = q @ up, q @ right
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = {}
    off = 0.0016 + layer * 0.0011
    for i in range(grid + 1):
        for j in range(grid + 1):
            u, v = i / grid, j / grid
            p = p0 + right * (u - 0.5) * w + up * (v - 0.5) * h
            ps = surf(p.normalized())
            nn = Vector((ps.x / a ** 2, ps.y / b ** 2, ps.z / c ** 2)).normalized()
            vs[i, j] = (bm.verts.new(ps + nn * off), (u, v))
    for i in range(grid):
        for j in range(grid):
            quad = [vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]]
            f = bm.faces.new([q_[0] for q_ in quad])
            for loop, (_, uvc) in zip(f.loops, quad):
                loop[uv].uv = uvc
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(name, bm, mat, col, outline=0)
    ob.parent = parent
    ob.location = center
    ob.visible_shadow = False
    return ob


def build_rig(prefix, col, d):
    """Khung nhân vật bằng Empty (trục trùng world lúc rest). Quy ước: mặt nhìn -Y, tay phải ở -X.
    +rx ở cột sống = cúi về trước; +rx ở tay/chân buông = vung ra sau; +ry tay phải = dang ra ngoài."""
    R = {}
    R["root"] = empty(f"{prefix}", col, size=0.4)
    R["hips"] = empty(f"{prefix}_hips", col, R["root"], (0, 0, d["hips"]))
    R["chest"] = empty(f"{prefix}_chest", col, R["hips"], (0, 0, d["chest"]))
    R["head"] = empty(f"{prefix}_head", col, R["chest"], (0, 0, d["neck"]))
    for side, sx in (("R", -1), ("L", 1)):
        R[f"sh_{side}"] = empty(f"{prefix}_shoulder_{side}", col, R["chest"], (sx * d["sh_x"], 0, d["sh_z"]))
        R[f"el_{side}"] = empty(f"{prefix}_elbow_{side}", col, R[f"sh_{side}"], (sx * 0.005, 0, -d["upper"]))
        R[f"hip_{side}"] = empty(f"{prefix}_hip_{side}", col, R["hips"], (sx * d["hip_x"], 0, 0))
        R[f"kn_{side}"] = empty(f"{prefix}_knee_{side}", col, R[f"hip_{side}"], (0, 0, -d["thigh"]))
    return R


def eyes(prefix, parent, hc, R, col, iris_mats, spread=20, el=0, w=0.058, h=0.078):
    """Mắt anime: lòng trắng · tròng (một bản cho mỗi material trong iris_mats) · đồng tử · 2 điểm sáng."""
    out = {k: [] for k in iris_mats}
    for side, sgn in (("R", 1), ("L", -1)):
        az = 180 + sgn * spread
        decal(f"{prefix}_sclera_{side}", parent, hc, R, az, el, w, h, M["white"], col, 0)
        for key, mat in iris_mats.items():
            out[key].append(decal(f"{prefix}_iris_{key}_{side}", parent, hc, R, az - sgn * 2, el - 3, w * 0.66, h * 0.74, mat, col, 1))
        decal(f"{prefix}_pupil_{side}", parent, hc, R, az - sgn * 2, el - 3, w * 0.3, h * 0.36, M["pupil"], col, 2)
        decal(f"{prefix}_shine_{side}", parent, hc, R, az + sgn * 3, el + 4, w * 0.24, h * 0.22, M["shine"], col, 3)
        decal(f"{prefix}_shine2_{side}", parent, hc, R, az - sgn * 5, el - 9, w * 0.12, h * 0.1, M["shine"], col, 3)
    return out


def _lerp_tab(tab, x):
    """Nội suy tuyến tính theo bảng [(x, y), ...] (x tăng dần)."""
    if x <= tab[0][0]:
        return tab[0][1]
    for (x0, y0), (x1, y1) in zip(tab, tab[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return tab[-1][1]


def _ell_surf(radii, d):
    """Điểm trên mặt elip đầu theo hướng d (local quanh tâm đầu) + pháp tuyến tại đó."""
    a, b, c = radii
    p = d / math.sqrt((d.x / a) ** 2 + (d.y / b) ** 2 + (d.z / c) ** 2)
    return p, Vector((p.x / a ** 2, p.y / b ** 2, p.z / c ** 2)).normalized()


def _azel(d):
    """Ngược của head_dir: hướng → (az, el) độ; az=180 chính diện."""
    return math.degrees(math.atan2(d.x, d.y)) % 360, math.degrees(math.asin(max(-1.0, min(1.0, d.z))))


def _hl_at(hairline, so):
    """el chân tóc tại độ lệch có dấu so (>0: phía phải nhân vật). hairline: list [(độ lệch, el)] đối xứng, hoặc
    dict(tab=list, bangs=[(tâm, độ sâu, nửa rộng)]) → mép tóc trước cắt răng cưa thành các mũi mái nhọn rủ xuống trán."""
    if isinstance(hairline, dict):
        el = _lerp_tab(hairline["tab"], abs(so))
        for tip, depth, hw in hairline["bangs"]:
            el -= depth * max(0.0, 1 - abs(so - tip) / hw) ** 1.4
        return el
    return _lerp_tab(hairline, abs(so))


def goku_hair_shell(radii, hairline, thick, seg=48, ring=28):
    """Chỏm tóc ôm sát đầu có chân tóc rõ: trên đường chân tóc dày `thick(el)`, dưới thì chìm vào đầu.
    hairline: [(độ lệch khỏi chính diện 0..180, el chân tóc)] → trán lộ ra, tai không bị che.
    thick(el, off): độ dày tóc theo el và độ lệch khỏi chính diện (dày hơn ở mái trước để nhìn từ dưới vẫn thấy tóc)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=1.0)
    hsh = bm.verts.layers.float.new("hsh")
    for v in bm.verts:
        d = v.co.normalized()
        az, el = _azel(d)
        off = abs(((az - 180) + 180) % 360 - 180)
        v[hsh] = 0.0 if off < 60 and el > 30 else 1.0     # chỏm lộ giữa các lọn: tông cam, trừ phía trên mái trước
        hl = _hl_at(hairline, ((az - 180) + 180) % 360 - 180)
        k = max(0.0, min(1.0, (el - hl + 5) / 9))
        k = k * k * (3 - 2 * k)
        p, n = _ell_surf(radii, d)
        v.co = p + n * (-0.014 + (thick(el, off) + 0.014) * k)
    return bm


def goku_lock(radii, path, w, th, lift=0.011, root_lift=0.03, rings=14, sides=8, arch=0.008):
    """Lọn tóc mái: path = [(az, el), ...] từ chân tóc tới ngọn, dẹt theo mặt đầu, thon nhọn, vồng ra khỏi trán
    (`arch`) rồi hạ xuống còn cách da `lift` ở ngọn để không cắt vào lông mày."""
    bm = bmesh.new()
    pts = []
    for i in range(rings + 1):
        s = i / rings
        x = s * (len(path) - 1)
        j = min(int(x), len(path) - 2)
        t = x - j
        az = path[j][0] + (path[j + 1][0] - path[j][0]) * t
        el = path[j][1] + (path[j + 1][1] - path[j][1]) * t
        p, n = _ell_surf(radii, head_dir(az, el))
        h = lift + (root_lift - lift) * (1 - s) ** 1.5 + arch * math.sin(math.pi * s) ** 1.5
        pts.append((p + n * h, n, s))
    loops = []
    for i, (c, n, s) in enumerate(pts[:-1]):
        tang = (pts[i + 1][0] - pts[max(i - 1, 0)][0]).normalized()
        side = tang.cross(n).normalized()
        nn = side.cross(tang).normalized()
        ww = w * 0.5 * min(1.0, 0.85 + s * 2.0) * (1 - s) ** 0.7
        tt = th * 0.5 * (1 - s) ** 0.5
        loops.append([bm.verts.new(c + side * x * ww + nn * y * tt) for x, y in LOCK_SECTION])
    _blade_faces(bm, loops, pts[-1][0])
    return bm


# mặt cắt lọn tóc anime: 2 cung lồi gặp nhau ở gờ sống (+y) và ở 2 mép → mỗi nửa lọn bo mượt (một ranh sáng-tối gọn),
# chỉ gờ + mép là cạnh sắc chia mặt sáng / mặt tối như tóc FighterZ (không lấm tấm mặt kim cương)
LOCK_SECTION = [(-1, 0), (-0.75, 0.45), (-0.45, 0.8), (0, 1.1), (0.45, 0.8), (0.75, 0.45), (1, 0),
                (0.6, -0.4), (0, -0.55), (-0.6, -0.4)]


def _blade_faces(bm, loops, tip_co):
    n = len(loops[0])
    tip = bm.verts.new(tip_co)
    for a, b in zip(loops, loops[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    for k in range(n):
        bm.faces.new((loops[-1][k], loops[-1][(k + 1) % n], tip))
    bm.faces.new(list(reversed(loops[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


GOKU_HAIR_HL = {}                                # đường sáng trên từng lọn (toạ độ local của mesh tóc) → extras/goku_details.py


def goku_blade(radii, az, el, d0, d1, L, W, T=None, face=None, sink=0.024, rings=16, hl=None, roll=0.0, sweep=0.0,
               twist=0.0, root=0.0, tri=False):
    """Lọn tóc lớn kiểu SSJ: gốc rộng cắm trong chỏm tóc ở (az, el), đi theo Bezier bậc 2 (hướng gốc d0 → hướng ngọn d1,
    mỗi hướng là (az, el)), bản rộng W phình ở 1/4 đầu rồi thon nhọn, dày T, gờ sống quay ra ngoài theo `face`.
    sweep: hất phần cao ra sau (+Y) như ngọn lửa trong gió. hl: list nhận khung từng vòng cho extras.
    twist: xoắn dần mặt lọn dọc chiều dài (độ ở ngọn) → nhìn ngang vẫn thấy bản rộng. root: phần gốc (theo s) mang
    thuộc tính "hsh" → shader tô tông cam tối (bóng lọn phía trên đổ xuống lọn phía dưới)."""
    if tri:                                      # gai tam giác mất phần bụng lá → bù bản gốc rộng hơn
        W *= 1.28
    T = T or W * 0.5
    p, nrm = _ell_surf(radii, head_dir(az, el))
    P0 = p - nrm * sink
    P1 = P0 + head_dir(*d0) * L * 0.5
    P2 = P1 + head_dir(*d1) * L * 0.5
    bez = lambda s: P0 * (1 - s) ** 2 + P1 * 2 * s * (1 - s) + P2 * s * s
    spine = lambda s: bez(s) + Vector((0, sweep * max(0.0, bez(s).z - 0.12) ** 1.3, 0))
    if face is None:                             # lọn hai bên quay mặt rộng chéo về phía trước (góc máy chủ yếu từ trước)
        off = (az - 180 + 180) % 360 - 180
        face = (180 + (off * 0.7 if abs(off) <= 115 else off), 22)
    F = head_dir(*face)
    P = [spine(i / rings) for i in range(rings + 1)]
    bm = bmesh.new()
    hsh = bm.verts.layers.float.new("hsh")
    loops, frames = [], []
    for i in range(rings):
        s = i / rings
        t = (P[i + 1] - P[max(i - 1, 0)]).normalized()
        n = F - t * F.dot(t)
        n = n.normalized() if n.length > 1e-3 else t.orthogonal().normalized()
        if roll or twist:
            n = Quaternion(t, rad(roll + twist * s)) @ n
        w = t.cross(n)
        hw = W * 0.5 * ((1 - s) ** 0.95 if tri else (1 - s) ** 0.75 * (1 + 0.8 * s))   # tri: gai tam giác (tóc đen)
        ht = T * 0.5 * (1 - s) ** 0.6
        sh = max(0.0, 1.0 - s / root) if root > 0 else 0.0
        ring = [bm.verts.new(P[i] + w * x * hw + n * y * ht) for x, y in LOCK_SECTION]
        for v in ring:
            v[hsh] = sh
        loops.append(ring)
        frames.append((P[i], w, n, hw, ht))
    _blade_faces(bm, loops, P[-1])
    if hl is not None:
        hl.append(frames)
    return bm


def _goku_thick(t0, top, front):
    """Độ dày tóc: mỏng ở thái dương/gáy, dày dần lên đỉnh, phồng thêm một gờ ở mái trước (el≈38)."""
    return lambda el, off: (t0 + top * max(0.0, el) / 90
                            + front * math.exp(-((el - 38) / 16) ** 2) * max(0.0, math.cos(math.radians(off))))


def goku_hair(name, radii, blades, mat, col, hairline, thick, locks=(), outline=0.007, sweep=0.0, tri=False):
    """Tóc Goku: chỏm ôm đầu có chân tóc + các lọn lớn dẹt có gờ (goku_blade) xếp lớp thành khối lửa
    + lọn mái rủ trên trán (goku_lock), gộp 1 mesh. Cạnh gờ/mép lọn để sắc (2 mặt sáng-tối kiểu cel)."""
    bm = goku_hair_shell(radii, hairline, thick, *((144, 48) if isinstance(hairline, dict) else ()))
    hl = GOKU_HAIR_HL.setdefault(name, [])
    for b in blades:
        args, kw = (b[:-1], b[-1]) if isinstance(b[-1], dict) else (b, {})
        _merge(bm, goku_blade(radii, *args, hl=hl, **{"sweep": sweep, "tri": tri, **kw}))
    for lk in locks:
        _merge(bm, goku_lock(radii, *lk))
    ob = _obj(name, bm, mat, col, smooth=True, outline=outline)
    ob.visible_shadow = False                    # không tự đổ bóng: mỗi lọn chỉ 2 tông theo gờ, không loang mảng tối
    try:
        ob.data.set_sharp_from_angle(angle=rad(42))
    except Exception as e:
        print("hair sharp edges skipped", e)
    return ob


def goku_tube(bm, pts, r, sides=10, samples=8, flat=1.0):
    """Ống bo tròn hai đầu chạy theo Catmull-Rom qua pts (ngón tay chibi). r: số hoặc hàm r(t), t∈[0,1].
    Khung trực giao vận chuyển song song (không lật khi đường đổi hướng); flat<1 làm dẹt mặt cắt."""
    P = [Vector(p) for p in pts]
    dense = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(samples):
            t = k / samples
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(P[-1])
    L = [0.0]
    for a, b in zip(dense, dense[1:]):
        L.append(L[-1] + (b - a).length)
    tot = L[-1]
    rf = r if callable(r) else (lambda t, r=r: r)
    t0 = (dense[1] - dense[0]).normalized()
    nrm = t0.cross(Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))).normalized()
    loops = []
    for i, c in enumerate(dense):
        tang = (dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]).normalized()
        nrm = (nrm - tang * nrm.dot(tang)).normalized()
        bi = tang.cross(nrm)
        rr = rf(L[i] / tot)
        d = min(L[i], tot - L[i])
        cap = math.sqrt(max(0.0, 1 - (1 - d / rr) ** 2)) if d < rr else 1.0
        rr *= max(cap, 0.2)
        loops.append([bm.verts.new(c + nrm * math.cos(a) * rr + bi * math.sin(a) * rr * flat)
                      for a in (math.tau * k / sides for k in range(sides))])
    for a, b in zip(loops, loops[1:]):
        for k in range(sides):
            bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    for ring, end, sgn in ((loops[0], dense[0], -1), (loops[-1], dense[-1], 1)):
        tg = (dense[1] - dense[0]) if sgn < 0 else (dense[-1] - dense[-2])
        pole = bm.verts.new(end + tg.normalized() * sgn * rf(0.0 if sgn < 0 else 1.0) * 0.12)
        for k in range(sides):
            f = (ring[k], ring[(k + 1) % sides], pole)
            bm.faces.new(f if sgn > 0 else tuple(reversed(f)))
    return bm


def goku_fist(side, sx, parent, col, center=(0, 0, -0.19)):
    """Nắm đấm chibi (thay quả bóng tròn): mu bàn tay bo vuông + 4 ngón cuộn vào lòng (gờ đốt ngón ở mặt đấm,
    các đốt giữa xếp lớp có nét mực ngăn cách ở phía lòng bàn tay) + ngón cái to ôm ngang ngón trỏ/giữa.
    Khung tay (trong không gian khuỷu): W = về phía mặt đấm (-Z), P = lòng bàn tay hướng vào thân (-sx X),
    U = dọc hàng đốt, ngón trỏ ở phía trước (-Y) → nhìn chính diện thấy ngón cái + lọn ngón trỏ."""
    O = Vector(center)
    U, Pv, W = Vector((0, 1, 0)), Vector((-sx, 0, 0)), Vector((0, 0, -1))
    h = lambda u, v, w: O + U * u + Pv * v + W * w
    skin = M["skin"]
    # mu/lòng bàn tay: cầu nắn thành khối vuông bo tròn
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    ext = (0.047, 0.038, 0.048)
    for v in bm.verts:
        q = v.co
        sq = lambda x: math.copysign(abs(x) ** 0.72, x)
        uu, vv, ww = sq(q.y) * ext[0], sq(q.x) * ext[1], sq(-q.z) * ext[2]
        v.co = h(0.004 + uu, 0.0 + vv, -0.008 + ww)
    # ụ thịt gốc ngón cái (lấp chỗ hõm giữa ngón cái và ngón trỏ khi nhìn từ phía ngón cái)
    tmp = bmesh.new()
    bmesh.ops.create_uvsphere(tmp, u_segments=16, v_segments=10, radius=0.022)
    for v in tmp.verts:
        v.co = h(-0.026, 0.03, -0.022) + v.co
    _merge(bm, tmp)
    ob = _obj(f"goku_fist_{side}", bm, skin, col, outline=0.0045)
    ob.parent = parent
    # 4 ngón cuộn: từ đốt ở mu tay → vòng qua mặt đấm → ép vào lòng bàn tay
    bm = bmesh.new()
    for u, r, sh in ((-0.034, 0.0148, 0.0), (-0.011, 0.0152, 0.002), (0.012, 0.0146, 0.0), (0.033, 0.0128, -0.006)):
        path = [(-0.022, 0.03 + sh), (-0.006, 0.049 + sh), (0.02, 0.049 + sh), (0.038, 0.028 + sh), (0.04, 0.0 + sh)]
        goku_tube(bm, [h(u, v, w) for v, w in path], lambda t, r=r: r * (1.0 - 0.12 * t), sides=10)
    ob = _obj(f"goku_fingers_{side}", bm, skin, col, outline=0.003)
    ob.parent = parent
    # ngón cái: gốc ở cạnh ngón trỏ gần cổ tay → vắt ngang trước đốt giữa ngón trỏ/giữa
    bm = bmesh.new()
    path = [(-0.034, 0.026, -0.034), (-0.04, 0.05, -0.006), (-0.02, 0.06, 0.01), (0.004, 0.056, 0.015)]
    goku_tube(bm, [h(*p) for p in path], lambda t: 0.0175 * (1.0 - 0.18 * t), sides=12)
    ob = _obj(f"goku_thumb_{side}", bm, skin, col, outline=0.003)
    ob.parent = parent



def goku_hairline(name, radii, hairline, thick, color, col, parent, off_max=104, r=0.0045):
    """Nét mực chạy dọc chân tóc (chỗ chỏm tóc trồi lên khỏi da) từ tóc mai bên này sang bên kia.
    Dò el mà mặt chỏm (goku_hair_shell) cắt mặt da cho từng độ lệch → nét bám đúng mép tóc ở cả 2 dạng.
    Gắn làm con của chính mesh tóc nên rung/phồng theo tóc."""
    def shell_off(el, off):
        hl = _hl_at(hairline, off)
        k = max(0.0, min(1.0, (el - hl + 5) / 9))
        k = k * k * (3 - 2 * k)
        return -0.014 + (thick(el, off) + 0.014) * k
    pts = []
    step = 1 if isinstance(hairline, dict) else 3
    for i in range(-off_max, off_max + 1, step):
        lo, hi = _hl_at(hairline, i) - 5, _hl_at(hairline, i) + 4
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if shell_off(mid, i) < 0 else (lo, mid)
        p, n = _ell_surf(radii, head_dir(180 + i, (lo + hi) / 2 - 0.8))
        pts.append(p + n * 0.0012)
    bm = goku_tube(bmesh.new(), pts, lambda t: r * (0.3 + 0.7 * min(1.0, 5 * min(t, 1 - t))), sides=6, samples=3)
    ob = _obj(name, bm, flat(name, color), col, outline=0)
    ob.parent = parent
    ob.visible_shadow = False
    return ob


def _bl(off, el, d0, d1, L, W, **kw):
    """Spec lọn lớn theo độ lệch khỏi chính diện: off>0 lệch sang phải nhân vật (trái khung hình khi nhìn chính diện)."""
    spec = (180 + off, el, (180 + d0[0], d0[1]), (180 + d1[0], d1[1]), L, W)
    return spec + (kw,) if kw else spec


def goku_hair_forms(R, hc, radii, c):
    """Tóc đen + tóc SSJ: khối lọn lớn dẹt (không phải chùm gai mảnh). Trả về (tóc, nét chân tóc) cho mỗi dạng."""
    # ── tóc đen (Goku thường): các lọn lớn xoè ngang và hất lên, mái 5 lọn kinh điển trên trán ──
    # v24 theo dáng Goku DBZ: cụm chóp 2 lọn dài xếp lớp vút lên rồi quét ngang sang phải nhân vật + ra sau, mỗi bên 3-4 lọn
    # dài chĩa ngang xếp tầng (phải nhân vật hếch lên, trái hơi chúc), lọn to gốc thon dài tới ngọn nhọn (không phải gai kim nhím)
    base = [
        _bl(20, 74, (72, 82), (86, 46), 0.6, 0.3, twist=-15),                # lọn chóp lớn nhất
        _bl(-8, 70, (40, 80), (84, 50), 0.48, 0.26, twist=-10),
        _bl(32, 62, (74, 64), (88, 42), 0.46, 0.25, twist=-10),                # lọn thứ 3 xếp dưới, cùng quét ngang                # lọn chóp thứ 2 nằm trước, cùng hướng
        _bl(-36, 64, (-50, 76), (-90, 52), 0.3, 0.22),                        # chóp phụ ngả ngược lại
        _bl(150, 66, (140, 78), (112, 56), 0.42, 0.26),                        # đỉnh sau
        _bl(-150, 62, (-150, 70), (-122, 50), 0.34, 0.24),
        _bl(55, 52, (80, 48), (96, 48), 0.46, 0.25),                           # phải nhân vật: 4 lọn dài chĩa ngang, hếch lên
        _bl(78, 30, (92, 24), (98, 28), 0.44, 0.23, face=(275, 20)),
        _bl(98, 10, (106, 4), (110, 8), 0.36, 0.2, face=(285, 15)),
        _bl(120, 32, (118, 30), (114, 36), 0.38, 0.22),
        _bl(-55, 52, (-82, 44), (-96, 40), 0.44, 0.22),                         # trái nhân vật: 4 lọn dài chĩa ngang, ngọn hơi chúc
        _bl(-78, 26, (-94, 14), (-100, 8), 0.44, 0.21, face=(85, 20)),
        _bl(-98, 4, (-106, -8), (-110, -12), 0.36, 0.18, face=(75, 15)),
        _bl(-120, 30, (-118, 24), (-114, 22), 0.38, 0.21),
        _bl(180, 36, (180, 30), (180, 40), 0.34, 0.3),                         # sau: quạt
        _bl(150, 8, (146, -4), (140, 4), 0.3, 0.24),
        _bl(-150, 8, (-146, -8), (-140, -2), 0.3, 0.24),
        _bl(180, -26, (180, -56), (180, -40), 0.17, 0.2),                      # gáy: mép răng cưa
        _bl(160, -30, (162, -60), (160, -44), 0.15, 0.17),
        _bl(-160, -30, (-162, -60), (-160, -44), 0.15, 0.17),
        _bl(140, -20, (140, -50), (138, -32), 0.13, 0.15),
        _bl(-140, -20, (-140, -50), (-138, -32), 0.13, 0.15),
    ]
    # chân tóc trước: trán lộ ít giữa các lọn mái; sau gáy kéo xuống tận cổ
    HL = [(0, 40), (25, 36), (50, 26), (70, 14), (86, 8), (100, 6), (115, -12), (130, -48), (150, -74), (180, -84)]
    # mái Goku: các lọn dày rủ xuống trán tới chân mày — lọn phải nhân vật cong ra đuôi mày, lọn giữa dài rủ giữa 2 mày,
    # lọn trái + một lọn dài ôm má trái xuống ngang mắt, 2 lọn thái dương, tóc mai nhọn trước tai
    locks = [([(198, 58), (210, 32), (220, 4)], 0.16, 0.05, 0.012, 0.055, 14, 10, 0.016),
             ([(184, 60), (181, 32), (176, -2)], 0.16, 0.05, 0.012, 0.055, 14, 10, 0.016),
             ([(166, 58), (158, 32), (152, 4)], 0.15, 0.046, 0.012, 0.055, 14, 10, 0.014),
             ([(150, 48), (140, 20), (135, -12)], 0.12, 0.04, 0.012, 0.05, 14, 10, 0.012)]
    for sg in (1, -1):
        locks += [([(180 + sg * 42, 44), (180 + sg * 52, 26), (180 + sg * 58, 10)], 0.1, 0.03),
                  ([(180 + sg * 66, 24), (180 + sg * 72, 6), (180 + sg * 76, -14)], 0.065, 0.018)]
    HL = dict(tab=HL, bangs=[(-40, 6, 10), (-14, 7, 9), (10, 8, 10), (34, 6, 10)])
    th_base = _goku_thick(0.02, 0.055, 0.006)
    # v22 gai tam giác to bản ở gốc (lọn hình lá xếp chồng thành một cục đen to hơn cả đầu)
    hair = goku_hair("goku_hair_base", radii, base, M["hair"], c, HL, th_base, locks, tri=True)
    attach(hair, R["head"], tuple(hc))
    hl_base = goku_hairline("goku_hairline_base", radii, HL, th_base, LINE_COLORS["hair"], c, hair)
    # ── SSJ: khối lửa dựng ngược hất ra sau, lọn lớn xếp lớp toả từ đỉnh; một lọn mái rủ giữa trán ──
    # lọn phía sau xếp thành hàng từ gáy lên đỉnh (so le như vảy): hàng dưới ngắn, ôm sát rồi vút lên, chui dưới
    # hàng trên; hàng trên dài, xoè ra sau rồi hất lên → nhìn từ sau là các tầng ngọn lửa, không toả đều từ một tâm.
    # root: phần gốc tô tông cam (bóng lọn trên đổ xuống), hàng càng thấp gốc tối càng dài
    BK = dict(root=0.42)
    ssj = [
        # chóp: 2 lọn cao nhất dựng gần thẳng đứng, nghiêng nhẹ ngược nhau (kiểu FighterZ)
        _bl(8, 62, (8, 76), (30, 82), 0.62, 0.25, roll=-20, twist=-25, T=0.15),
        _bl(-22, 60, (-20, 74), (-60, 80), 0.58, 0.24, roll=20, twist=25, T=0.15),
        # đỉnh-sau: dựng sau chóp, lấp khe giữa các lọn cao khi nhìn chính diện
        _bl(180, 66, (180, 82), (180, 68), 0.56, 0.24, root=0.25),
        _bl(140, 60, (140, 78), (128, 66), 0.5, 0.19, root=0.25),
        _bl(-140, 60, (-140, 78), (-128, 66), 0.5, 0.19, root=0.25),
        # trên-bên: nghiêng ra ~30° rồi vút lên
        _bl(42, 52, (52, 50), (58, 74), 0.48, 0.23, twist=-20, root=0.18),
        _bl(-42, 52, (-52, 50), (-58, 74), 0.46, 0.23, twist=20, root=0.18),
        # thái dương: chĩa ra ~45°, ngọn cong lên
        _bl(76, 38, (86, 28), (88, 66), 0.44, 0.22, face=(265, 30), root=0.22),
        _bl(-76, 38, (-86, 28), (-88, 66), 0.42, 0.22, face=(95, 30), root=0.22),
        # trên tai: chĩa ngang ra, hếch nhẹ
        _bl(100, 16, (102, 6), (102, 42), 0.36, 0.17, face=(275, 25), root=0.25),
        _bl(-100, 16, (-102, 6), (-102, 42), 0.36, 0.17, face=(85, 25), root=0.25),
        _bl(112, -2, (114, -8), (114, 10), 0.24, 0.13, root=0.3),
        _bl(-112, -2, (-114, -8), (-114, 10), 0.24, 0.13, root=0.3),
        # sau: 2 hàng lọn dài chĩa ra sau rồi hất lên (không ôm sát đầu thành cánh hoa)
        _bl(160, 42, (162, 50), (156, 72), 0.52, 0.24, twist=12, **BK),
        _bl(-160, 42, (-162, 50), (-156, 72), 0.52, 0.24, twist=-12, **BK),
        _bl(124, 34, (124, 44), (114, 68), 0.44, 0.22, **BK),
        _bl(-124, 34, (-124, 44), (-114, 68), 0.44, 0.22, **BK),
        # v20 nửa dưới gáy: 1 lọn giữa bản to rủ xuống gáy + 2 lọn xoè chéo vút lên hai bên (trước 4 lọn nhỏ xếp tâm → nhìn từ sau như
        # quả thông / bông atiso)
        _bl(180, 8, (180, -28), (180, -8), 0.36, 0.27, **BK),
        _bl(145, 8, (140, 24), (126, 58), 0.42, 0.21, **BK),
        _bl(-145, 8, (-140, 24), (-126, 58), 0.42, 0.21, **BK),
        # gáy: chĩa xuống, ngọn hất ra
        _bl(180, -34, (180, -70), (180, -30), 0.2, 0.17, root=0.5),
        _bl(158, -30, (160, -55), (160, -15), 0.15, 0.14, root=0.5),
        _bl(-158, -30, (-160, -55), (-160, -15), 0.15, 0.14, root=0.5),
        # lớp trước ngay trên trán: lọn ngắn hơn đứng trước 2 lọn chóp
        _bl(20, 48, (26, 72), (36, 78), 0.42, 0.21),
        _bl(-16, 48, (-22, 72), (-34, 76), 0.4, 0.21),
    ]
    HL_SSJ = [(0, 34), (25, 30), (50, 20), (70, 11), (86, 8), (100, 6), (115, -12), (130, -48), (150, -74), (180, -84)]
    # mái: lọn đặc trưng rủ giữa trán (giữa 2 lông mày) + 2 lọn ngắn + 2 lọn ôm thái dương + tóc mai trước tai
    locks_ssj = [([(176, 64), (184, 46), (196, 26), (200, 4)], 0.22, 0.042, 0.012, 0.065, 18, 10, 0.03),
                 ([(166, 60), (156, 40), (146, 22), (141, 4)], 0.18, 0.036, 0.012, 0.055, 16, 10, 0.02)]
    for sg in (1, -1):
        locks_ssj += [([(180 + sg * 38, 46), (180 + sg * 48, 28), (180 + sg * 56, 12)], 0.1, 0.022),
                      ([(180 + sg * 64, 26), (180 + sg * 72, 6), (180 + sg * 77, -16)], 0.085, 0.022)]   # tóc mai SSJ rõ hơn trước tai
    HL_SSJ = dict(tab=HL_SSJ, bangs=[(-52, 10, 10), (-30, 14, 11), (-8, 10, 9), (14, 16, 11), (38, 12, 10), (58, 9, 9)])
    th_ssj = _goku_thick(0.02, 0.05, 0.008)
    hair_ssj = goku_hair("goku_hair_ssj", radii, ssj, M["hair_ssj"], c, HL_SSJ, th_ssj, locks_ssj, sweep=0.22)
    attach(hair_ssj, R["head"], tuple(hc))
    hl_ssj = goku_hairline("goku_hairline_ssj", radii, HL_SSJ, th_ssj, LINE_COLORS["hair_ssj"], c, hair_ssj)
    return hair, hl_base, hair_ssj, hl_ssj


def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def goku_face_warp(co, radii):
    """Nắn đầu cầu thành mặt anime chibi (local quanh tâm đầu, mặt nhìn -Y): má bầu ngay dưới mắt, hàm thon
    dần về một cằm nhỏ mềm hơi nhô trước-dưới, gầm hàm nâng lên (lộ cổ, nhìn nghiêng thấy đường hàm).
    Chỉ chạm nửa dưới phía trước (el < ~-8°, không chạm gáy): đỉnh/sau đầu giữ đúng elip để tóc vẫn ôm khít.
    Dùng chung cho mesh đầu và phần vỏ tóc chìm dưới da (goku_hair_shell) để vỏ tóc không lòi ra dưới hàm."""
    a, b, c = radii
    u = Vector((co.x / a, co.y / b, co.z / c))
    if u.length < 1e-6:
        return Vector(co)
    u.normalize()
    keep_back = _smooth(0.6, 0.15, u.y)                    # 0 ở gáy (tóc phủ) → 1 ở nửa trước
    lower = _smooth(-0.14, -0.95, u.z) * keep_back           # 0 trên tầm mắt → 1 ở đáy đầu
    front = _smooth(0.3, -0.7, u.y)                          # 1 ở mặt trước
    p = Vector(co)
    # hàm thon: bóp ngang nửa dưới, mạnh ở phía trước (cằm nhỏ), nhẹ dần về mang tai
    p.x *= 1 - 0.2 * lower ** 1.25 * (0.3 + 0.7 * front)
    # má bầu: phồng nhẹ ra ngoài ở hai bên mặt, ngay dưới mắt
    for sx in (-1, 1):
        dch = Vector((sx * 0.62, -0.62, -0.48)).normalized()
        w = math.exp(-((u - dch).length / 0.4) ** 2)
        p += Vector((u.x * a, u.y * b * 0.6, u.z * c * 0.4)).normalized() * 0.01 * w
    # cằm mềm: kéo nhẹ ra trước-dưới
    wc = math.exp(-((u - Vector((0, -0.6, -0.8))).length / 0.36) ** 2)
    p += Vector((0, -0.45, -0.55)).normalized() * 0.013 * wc
    # gầm hàm: nâng phần đáy (trừ chóp cằm) để cằm thành mỏm và lộ cổ
    under = _smooth(-0.5, -0.98, u.z) * _smooth(-0.85, -0.25, u.y) * keep_back
    p.z += 0.024 * under
    p.y += 0.01 * under * _smooth(-0.6, 0.0, u.y)            # gầm hàm lùi về sau một chút
    return p


def goku_face_shape(ob, radii):
    """Áp goku_face_warp lên mọi đỉnh của một mesh dựng quanh tâm đầu (đầu, vỏ tóc, nét chân tóc)."""
    for v in ob.data.vertices:
        v.co = goku_face_warp(v.co, radii)
    ob.data.update()


def goku_snap_decals(head, decals, radii):
    """face_decal() dựng miếng dán ôm theo elip `radii`; sau khi nắn đầu (goku_face_shape) chiếu lại từng đỉnh
    theo tia từ tâm đầu lên mesh thật, giữ nguyên độ nổi (lớp) của nó: không lơ lửng, không chìm/nhấp nháy."""
    from mathutils.bvhtree import BVHTree
    me = head.data
    bvh = BVHTree.FromPolygons([v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    a, b, c = radii
    for ob in decals:
        off_loc = Vector(ob.location) - Vector(head.location)
        for v in ob.data.vertices:
            q = v.co + off_loc
            d = q.normalized()
            ell = d / math.sqrt((d.x / a) ** 2 + (d.y / b) ** 2 + (d.z / c) ** 2)
            off = q.length - ell.length
            hit, nrm, _i, _d = bvh.ray_cast(Vector((0, 0, 0)), d, 1.0)
            if hit is None:
                continue
            v.co = hit + nrm.normalized() * max(off, 0.0014) - off_loc
        ob.data.update()


GOKU_DIM = dict(hips=0.545, chest=0.08, neck=0.33, sh_x=0.17, sh_z=0.25, upper=0.2, hip_x=0.085, thigh=0.25)
LEG_DROP = 0.115                                 # v9 chân Goku ngắn đi: nâng root ở đòn kết liễu để nắm đấm vẫn trúng mặt
FRIEZA_DIM = dict(hips=0.56, chest=0.06, neck=0.27, sh_x=0.15, sh_z=0.2, upper=0.17, hip_x=0.07, thigh=0.21)
FR_FOOT_Z = -0.205                               # v16 chân Frieza ngắn chibi: đùi 0.26→0.21, cẳng 0.235→0.205 (hông giữ nguyên:
                                                 # thân/đầu/anchor không đổi chỗ; Frieza luôn bay nên bàn chân không cần chạm đất)


def build_goku():
    c, R_ = C_GOKU, 0.2
    R = build_rig("GOKU", c, GOKU_DIM)
    hc = Vector((0, 0, R_ * 0.86))                      # tâm đầu, tính từ khớp cổ
    # thân: võ phục cam, cổ chữ V lộ áo xanh, đai xanh, chữ 悟 trên ngực
    attach(sphere("goku_pelvis", 1, M["gi"], c, (0.14, 0.11, 0.1)), R["hips"], (0, 0, 0.0))
    torso = attach(tcap("goku_torso", 0.135, 0.112, 0.1, M["gi"], c, (1.1, 0.85, 1)), R["chest"], (0, 0, 0.12))
    for v in torso.data.vertices:                       # vai xuôi: hạ đỉnh ngực 0.305 → 0.28 để lộ một đoạn cổ ngắn
        if v.co.z > 0.05:
            v.co.z = 0.05 + (v.co.z - 0.05) * 0.8
    # cổ chữ V sâu lộ áo xanh + ve áo: dán ôm ngực trong extras/goku_outfit.py; ở đây chỉ cổ áo xanh ôm quanh chân cổ
    attach(torus("goku_undershirt", 0.05, 0.0095, M["blue"], c, seg=24, ring=8, scale=(1.08, 1.0, 1), outline=0.003),
           R["chest"], (0, 0.002, 0.27), (6, 0, 0))
    # đai vải xanh bản to (kiểu sash), mép trên bo vào bụng; 2 đuôi đai dẹt rủ từ nút thắt
    sash = [(0.096, 0.0), (0.096, 0.112), (0.094, 0.13), (0.088, 0.138), (0.07, 0.141), (0.05, 0.143),
            (0.032, 0.146), (0.024, 0.145), (0.019, 0.134), (0.017, 0.0)]
    attach(lathe("goku_belt", sash, M["blue"], c, seg=40, scale=(1.0, 0.8, 1),
                 rfn=lambda t, z, r: r * (1 + 0.035 * max(0.0, math.cos(3 * t + 0.6 + z * 30)) ** 3)), R["hips"], (0, 0, 0.0))
    # nút thắt + 2 đuôi đai là dải vải dẹt loe dần, rủ chéo (v19: 1 viên thuốc tròn nhìn như cái thìa)
    attach(sphere("goku_belt_knot", 1, M["blue"], c, (0.026, 0.014, 0.021), seg=20, outline=0.003),
           R["hips"], (0.052, -0.124, 0.03), (0, 18, 0))
    for i, pts in enumerate(([(0.046, -0.126, 0.026), (0.038, -0.131, -0.025), (0.031, -0.132, -0.075), (0.028, -0.129, -0.112)],
                             [(0.06, -0.126, 0.026), (0.07, -0.13, -0.02), (0.081, -0.131, -0.062), (0.087, -0.128, -0.09)])):
        bm = goku_tube(bmesh.new(), [Vector(p) for p in pts], lambda t: 0.0048 + 0.0018 * t, sides=12, flat=3.6)
        attach(_obj(f"goku_belt_tail_{i}", bm, M["blue"], c, outline=0.003), R["hips"], (0, 0, 0))
    attach(cyl("goku_emblem", 0.042, 0.042, 0.006, M["white"], c, seg=28, outline=0.003), R["chest"], (0.0795, -0.084, 0.1196), (98, 0, 30))
    try:
        fc = bpy.data.curves.new("goku_kanji", "FONT")
        fc.body = "悟"
        for path in FONT_PATHS:
            if os.path.exists(path):
                fc.font = bpy.data.fonts.load(path)
                break
        fc.size, fc.align_x, fc.align_y, fc.extrude = 0.062, "CENTER", "CENTER", 0.0015
        k = bpy.data.objects.new("goku_kanji", fc)
        c.objects.link(k)
        fc.materials.append(M["ink"])
        attach(k, R["chest"], (0.0816, -0.0876, 0.119), (98, 0, 30))
    except Exception as e:  # thiếu font thì bỏ qua chữ
        print("KANJI skipped", e)
    # cổ ngắn lộ giữa cằm và cổ áo (chân cổ chìm trong ngực, đỉnh chìm trong đầu)
    neck = attach(cyl("goku_neck", 0.053, 0.048, 0.13, M["skin"], c, seg=20), R["chest"], (0, 0, 0.295))
    # đầu to kiểu chibi: má bầu, cằm nhỏ; mặt vẽ sẵn (face_textures.py) dán ôm theo elip của đầu
    HS = (1.06, 0.97, 0.93)
    radii = tuple(R_ * k for k in HS)
    head = attach(sphere("goku_head", R_, M["skin"], c, HS, seg=56, outline=0.007), R["head"], tuple(hc))
    goku_face_shape(head, radii)
    # da mặt riêng: dải sáng rất nhẹ (dải sáng gắt của "skin" in thành một hình oval nhạt quanh miệng như mõm chó)
    face_skin = toon("goku_skin_face", "#FAD3AE", "#F2BE9C", "#FAD3AE")   # bóng mặt dịu: nhìn từ dưới lên bóng cằm không thành mảng loang
    head.material_slots[0].material = face_skin
    # v30 cổ tông bóng như anime (cằm đổ bóng xuống cổ): trước cùng màu mặt → cổ sáng như khúc gỗ dưới cằm
    neck.material_slots[0].material = toon("goku_neck_skin", "#EFBC98", "#E3A985", "#EFBC98")
    # tai chibi nhỏ, tròn, lộ ra dưới tóc mai ở ngang tầm mắt, hơi xoay về trước; lõm tai tông da tối
    ear_in = toon("goku_ear_in", "#E9A684", "#D88E6E")
    for side, sx in (("R", -1), ("L", 1)):
        p, n = _ell_surf(radii, head_dir(180 - sx * 90 + sx * 8, -13))
        ear = attach(sphere(f"goku_ear_{side}", 0.05, M["skin"], c, (0.42, 0.72, 0.98), outline=0.004),
                     R["head"], tuple(hc + p + n * 0.006), (0, sx * 8, -sx * 18))
        ear.material_slots[0].material = face_skin
        q = ear.rotation_euler.to_matrix()
        attach(sphere(f"goku_ear_in_{side}", 0.05, ear_in, c, (0.16, 0.42, 0.6), seg=20, outline=0),
               R["head"], tuple(Vector(ear.location) + q @ Vector((sx * 0.0125, -0.004, -0.002))), (0, sx * 8, -sx * 18))
    T = {k: tex_mat(f"tx_{k}", f"{k}.png") for k in ("goku_eye_R", "goku_eye_L", "goku_eye_ssj_R", "goku_eye_ssj_L",
                                                       "goku_brow_R", "goku_brow_L", "goku_brow_ssj_R", "goku_brow_ssj_L",
                                                       "goku_mouth", "goku_mouth_open", "goku_nose", "blush")}
    T["goku_eye_ssj_R"] = tex_mat("tx_goku_eye_ssj_R", "goku_eye_ssj_R.png", energy=0.5)
    T["goku_eye_ssj_L"] = tex_mat("tx_goku_eye_ssj_L", "goku_eye_ssj_L.png", energy=0.5)
    for k in ("goku_eye_shut_R", "goku_eye_shut_L", "goku_eye_blink_R", "goku_eye_blink_L", "goku_eye_angry_R", "goku_eye_angry_L",
              "goku_brow_angry_R", "goku_brow_angry_L", "goku_mouth_grit"):
        T[k] = tex_mat(f"tx_{k}", f"{k}.png")
    for k in ("goku_eye_ssj_fierce_R", "goku_eye_ssj_fierce_L"):
        T[k] = tex_mat(f"tx_{k}", f"{k}.png", energy=0.5)
    ey = {"base": [], "ssj": [], "shut": [], "blink": [], "angry": [], "fierce": []}
    brows_base, brows_ssj, brows_angry, blush = [], [], [], []
    for side, sgn in (("R", 1), ("L", -1)):
        az = 180 + sgn * 25
        ey["base"].append(face_decal(f"goku_eye_{side}", R["head"], hc, radii, az, -16, 0.145, 0.17, T[f"goku_eye_{side}"], c, 1))
        ey["ssj"].append(face_decal(f"goku_eye_ssj_{side}", R["head"], hc, radii, az, -16, 0.145, 0.17, T[f"goku_eye_ssj_{side}"], c, 1))
        ey["shut"].append(face_decal(f"goku_eye_shut_{side}", R["head"], hc, radii, az, -16, 0.12, 0.12, T[f"goku_eye_shut_{side}"], c, 1))
        ey["angry"].append(face_decal(f"goku_eye_angry_{side}", R["head"], hc, radii, az, -16, 0.145, 0.17, T[f"goku_eye_angry_{side}"], c, 1))
        ey["fierce"].append(face_decal(f"goku_eye_ssj_fierce_{side}", R["head"], hc, radii, az, -16, 0.145, 0.17, T[f"goku_eye_ssj_fierce_{side}"], c, 1))
        brows_angry.append(face_decal(f"goku_brow_angry_{side}", R["head"], hc, radii, 180 + sgn * 24, 5, 0.09, 0.06, T[f"goku_brow_angry_{side}"], c, 2, roll=sgn * 4))
        ey["blink"].append(face_decal(f"goku_eye_blink_{side}", R["head"], hc, radii, az, -18, 0.12, 0.1, T[f"goku_eye_blink_{side}"], c, 1))
        brows_base.append(face_decal(f"goku_brow_{side}", R["head"], hc, radii, 180 + sgn * 25, 14, 0.09, 0.045, T[f"goku_brow_{side}"], c, 2, roll=sgn * 8))
        brows_ssj.append(face_decal(f"goku_brow_ssj_{side}", R["head"], hc, radii, 180 + sgn * 24, 5, 0.09, 0.06, T[f"goku_brow_ssj_{side}"], c, 2, roll=sgn * 4))
        blush.append(face_decal(f"goku_blush_{side}", R["head"], hc, radii, 180 + sgn * 44, -32, 0.07, 0.042, T["blush"], c, 0))
    # miệng to hơn một chút để đọc được ở cỡ khung truyện (key ẩn/hiện giữ nguyên tên)
    smirk = face_decal("goku_mouth_smirk", R["head"], hc, radii, 180, -40, 0.09, 0.056, tex_mat("tx_goku_mouth_smirk", "goku_mouth_smirk.png"), c, 0)
    mouth = face_decal("goku_mouth", R["head"], hc, radii, 180, -40, 0.09, 0.056, T["goku_mouth"], c, 0)
    mouth_open = face_decal("goku_mouth_open", R["head"], hc, radii, 180, -42, 0.094, 0.098, T["goku_mouth_open"], c, 0)
    grit = face_decal("goku_mouth_grit", R["head"], hc, radii, 180, -40, 0.1, 0.06, T["goku_mouth_grit"], c, 0)
    # mũi anime: nét bóng nhỏ (decal) + một mỏm da rất nhỏ để nhìn 3/4, nghiêng thấy sống mũi
    nose = face_decal("goku_nose", R["head"], hc, radii, 180 + 3, -27, 0.04, 0.04, T["goku_nose"], c, 0)
    goku_snap_decals(head, ey["base"] + ey["ssj"] + ey["shut"] + ey["angry"] + ey["blink"] + ey["fierce"] + brows_base + brows_ssj
                     + brows_angry + blush + [smirk, mouth, mouth_open, grit, nose], radii)
    from mathutils.bvhtree import BVHTree
    hb = BVHTree.FromPolygons([v.co for v in head.data.vertices], [tuple(p_.vertices) for p_ in head.data.polygons])
    tip, tn, _i, _d = hb.ray_cast(Vector((0, 0, 0)), head_dir(180, -24.5), 1.0)
    nose_tip = attach(sphere("goku_nose_tip", 1, face_skin, c, (0.0075, 0.009, 0.0085), seg=16, outline=0),
                      R["head"], tuple(hc + tip - tn * 0.0045), (-30, 0, 0))
    nose_tip.visible_shadow = False
    # bóng cằm hắt xuống cổ (cel): dải da tối quanh đỉnh cổ, mép dưới võng chữ U ở phía trước
    neck_sh_m = bpy.data.materials.get("goku_neck_shadow") or toon("goku_neck_shadow", "#E7A383", "#D48F72", "#E7A383")
    bm = bmesh.new()
    rows = []
    for j, t in enumerate((0.0, 1.0)):
        row = []
        for i in range(24):
            ang = math.tau * i / 24                            # ang=0: phía trước (-Y)
            front_w = max(0.0, math.cos(ang))
            z = 0.355 if t > 0.5 else 0.34 - 0.034 * front_w ** 1.6     # chữ U sâu rõ ở trước (mép thẳng như dán băng)
            r = 0.053 - 0.005 * (z - 0.23) / 0.13 + 0.0009
            row.append(bm.verts.new((r * math.sin(ang), -r * math.cos(ang), z)))
        rows.append(row)
    for i in range(24):
        bm.faces.new((rows[0][i], rows[0][(i + 1) % 24], rows[1][(i + 1) % 24], rows[1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    neck_sh = attach(_obj("goku_neck_shadow", bm, neck_sh_m, c, outline=0), R["chest"], (0, 0, 0))
    neck_sh.visible_shadow = False
    hair, hl_base, hair_ssj, hl_ssj = goku_hair_forms(R, hc, radii, c)
    for ob in (o for o in (hair, hl_base, hair_ssj, hl_ssj) if o):   # vỏ tóc chìm dưới da đi theo hàm thon (không lòi ra như râu)
        goku_face_shape(ob, radii)
    # tay chân bo tròn
    for side, sx in (("R", -1), ("L", 1)):
        attach(tcap(f"goku_sleeve_{side}", 0.06, 0.055, 0.045, M["blue"], c), R[f"sh_{side}"], (sx * 0.004, 0, -0.035))
        # bắp tay có cơ (v19: viên thuốc thẳng như tay ma-nơ-canh): bắp tay trước nhô dưới tay áo, cơ tam đầu sau,
        # cẳng tay phình gần khuỷu rồi thon vào cổ tay — tay chắc kiểu Goku FighterZ
        L = GOKU_DIM["upper"]
        def arm_rfn(t, z, r, w, sx=sx):
            fr_, bk, out = max(0.0, -math.sin(t)), max(0.0, math.sin(t)), max(0.0, -sx * math.cos(t))
            up = (0.16 * fr_ ** 1.5 * math.exp(-((z + 0.135) / 0.03) ** 2)
                  + 0.07 * bk ** 1.5 * math.exp(-((z + 0.1) / 0.04) ** 2))
            lo = 0.1 * out ** 1.5 * math.exp(-((z + L + 0.035) / 0.035) ** 2)
            return r * (1 + up * (1 - w) + lo * w)
        # v22 cả cánh tay liền một khối bẻ ở khuỷu (skin_limb) thay 2 khúc rời
        skin_limb(f"goku_arm_{side}", [(0.0, 0.0), (-0.005, 0.035), (-0.03, 0.046), (-0.07, 0.049), (-0.11, 0.051),
                                       (-0.14, 0.05), (-0.165, 0.046), (-0.185, 0.044), (-L, 0.045), (-L - 0.02, 0.049),
                                       (-L - 0.04, 0.052), (-L - 0.065, 0.05), (-L - 0.09, 0.045), (-L - 0.115, 0.041),
                                       (-L - 0.14, 0.04), (-L - 0.15, 0.0)],
                  R[f"sh_{side}"], R[f"el_{side}"], M["skin"], c, seg=28, rfn=arm_rfn)
        attach(cyl(f"goku_wrist_{side}", 0.046, 0.046, 0.05, M["blue"], c), R[f"el_{side}"], (0, 0, -0.13))
        goku_fist(side, sx, R[f"el_{side}"], c)
        # chân chibi ngắn mập: quần võ cam ống rộng phồng dần xuống gối rồi dồn túm trên cổ giày (nếp vải dồn),
        # giày xanh navy cổ cao (sọc đỏ + dây buộc vàng ở extras/goku_outfit.py)
        squash = lambda t, sx=sx: 1 - 0.13 * max(0.0, -sx * math.cos(t)) ** 1.5      # ép mặt trong: 2 ống không lẹm nhau
        attach(lathe(f"goku_thigh_{side}", [(0.07, 0.0), (0.07, 0.042), (0.056, 0.074), (0.03, 0.09), (0.0, 0.094),
                                            (-0.06, 0.097), (-0.12, 0.098), (-0.18, 0.096), (-0.23, 0.09), (-0.265, 0.078),
                                            (-0.285, 0.055), (-0.292, 0.0)], M["gi"], c,
                     rfn=lambda t, z, r, sq=squash, sx=sx: r * sq(t) * (1 + 0.03 * max(0.0, -z - 0.12) / 0.17
                                                                         * math.cos(4 * t + sx * 1.1 + z * 9) ** 2)),
               R[f"hip_{side}"], (0, 0, 0))
        attach(sphere(f"goku_knee_{side}", 0.082, M["gi"], c), R[f"kn_{side}"], (0, 0, 0.0))
        bunch = lambda z: max(0.0, 1 - abs(z + 0.072) / 0.04)                      # nếp dồn mạnh nhất ngay trên giày
        attach(lathe(f"goku_shinpant_{side}", [(0.06, 0.0), (0.06, 0.05), (0.04, 0.08), (0.0, 0.092), (-0.03, 0.1),
                                               (-0.055, 0.104), (-0.075, 0.1), (-0.09, 0.087), (-0.1, 0.07),
                                               (-0.106, 0.055), (-0.109, 0.04), (-0.111, 0.0)], M["gi"], c, seg=40,
                     rfn=lambda t, z, r, sq=squash, sx=sx: r * sq(t) * (1 + 0.11 * bunch(z)
                                                                         * math.cos(3.5 * t + sx * 0.8 - z * 14) ** 4)),
               R[f"kn_{side}"], (0, 0, 0))
        LINE_COLORS.setdefault("goku_boot", "#070C2C")
        boot_m = bpy.data.materials.get("goku_boot") or toon("goku_boot", "#1E2C72", "#121A4A", "#4057A8", rim=0.6)
        attach(tcap(f"goku_boot_{side}", 0.062, 0.055, 0.085, boot_m, c), R[f"kn_{side}"], (0, 0, -0.135))
        attach(sphere(f"goku_foot_{side}", 1, boot_m, c, (0.062, 0.102, 0.046)), R[f"kn_{side}"], (0, -0.035, -0.235))
        attach(sphere(f"goku_sole_{side}", 1, M["boot_sole"], c, (0.06, 0.1, 0.018), outline=0.003), R[f"kn_{side}"], (0, -0.035, -0.267))
    R["chest_anchor"] = empty("GOKU_chest_anchor", c, R["chest"], (0, 0, 0.14), 0.05)
    R["head_anchor"] = empty("GOKU_head_anchor", c, R["head"], tuple(hc), 0.05)
    R["face_anchor"] = empty("GOKU_face_anchor", c, R["head"], tuple(hc + Vector((0, -0.5, 0))), 0.05)
    R["fist_anchor"] = empty("GOKU_fist_anchor", c, R["el_R"], (0, 0, -0.2), 0.05)
    R["ssj"] = [hair_ssj, hl_ssj] + ey["ssj"] + brows_ssj
    R["base"] = [hair, hl_base] + ey["base"] + brows_base
    R["hair_ssj"] = hair_ssj
    R["eyes_base"], R["eyes_ssj"], R["eyes_shut"], R["eyes_blink"], R["eyes_angry"] = ey["base"], ey["ssj"], ey["shut"], ey["blink"], ey["angry"]
    R["mouth"], R["mouth_open"], R["smirk"] = [mouth], [mouth_open], [smirk]
    R["eyes_fierce"], R["grit"], R["brows_angry"], R["blush"] = ey["fierce"], [grit], brows_angry, blush
    return R


def fr_finger_bm(sx, base, length, r, curl, spread=0.0, seg=12, rings=8):
    """Ngón tay chibi tròn: ống bo hai đầu theo trục -Z, uốn cong `curl` độ về phía lòng bàn tay (+X ở tay phải,
    sx=-1), xoè `spread` độ quanh pháp tuyến lòng bàn tay. Trả về bmesh trong hệ toạ độ của khuỷu tay."""
    n, down, side = Vector((-sx, 0, 0)), Vector((0, 0, -1)), Vector((0, 1, 0))   # n: hướng lòng bàn tay
    phi = max(rad(curl), 1e-4)
    rho = length / phi
    q = Quaternion(n, rad(spread))

    def frame(s_):                                   # tâm + 2 trục ngang tại toạ độ dọc ngón s_ (kéo thẳng ở 2 đầu)
        a = min(max(s_, 0.0), length) / rho
        C = n * rho * (1 - math.cos(a)) + down * rho * math.sin(a)
        T = n * math.sin(a) + down * math.cos(a)
        N = n * math.cos(a) - down * math.sin(a)
        return C + T * (s_ - length if s_ > length else min(s_, 0.0)), N
    prof = [(-r * math.cos(t), r * math.sin(t)) for t in (math.pi / 2 * k / 4 for k in range(1, 4))]   # nắp đầu
    prof += [(length * k / rings, r) for k in range(rings + 1)]
    prof += [(length + r * math.sin(t), r * math.cos(t)) for t in (math.pi / 2 * k / 4 for k in range(1, 4))]
    bm = bmesh.new()
    ringsv = []
    for s_, rr in prof:
        C, N = frame(s_)
        ringsv.append([bm.verts.new(q @ (C + (N * math.cos(t) + side * math.sin(t)) * rr) + Vector(base))
                       for t in (math.tau * i / seg for i in range(seg))])
    top = bm.verts.new(q @ frame(-r)[0] + Vector(base))
    bot = bm.verts.new(q @ frame(length + r)[0] + Vector(base))
    for j in range(len(ringsv) - 1):
        for i in range(seg):
            bm.faces.new((ringsv[j][i], ringsv[j][(i + 1) % seg], ringsv[j + 1][(i + 1) % seg], ringsv[j + 1][i]))
    for i in range(seg):
        bm.faces.new((top, ringsv[0][(i + 1) % seg], ringsv[0][i]))
        bm.faces.new((bot, ringsv[-1][i], ringsv[-1][(i + 1) % seg]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


FR_HEAD_R, FR_HEAD_HS = 0.18, (0.95, 0.94, 1.03)   # v22 hẹp ngang chút: đầu thuôn như quả trứng, không tròn như quả bóng


def _fr_sstep(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def fr_head_surf(d):
    """Đầu Frieza final form (local quanh tâm đầu hc): elip gốc, sọ tròn giữ nguyên dưới vòm tím; nửa dưới mặt
    thon dần về hai bên má tới cằm nhỏ mềm, gò má nhô rất nhẹ. Hàm bán kính theo hướng nên decal/vòm ôm theo được."""
    d = Vector(d).normalized()
    a, b, c = (FR_HEAD_R * k for k in FR_HEAD_HS)
    r = 1.0 / math.sqrt((d.x / a) ** 2 + (d.y / b) ** 2 + (d.z / c) ** 2)
    low = _fr_sstep(-0.18, -0.9, d.z)                    # 0 từ tầm mắt trở lên → 1 dưới cằm
    side = d.x * d.x / (d.x * d.x + d.y * d.y + 0.04)    # 1 ngang hai bên, 0 trước/sau (ổn định ở cực dưới)
    front = max(0.0, -d.y) / math.sqrt(d.x * d.x + d.y * d.y + 1e-6)
    k = 1.0 - low * (0.085 * side + 0.015)              # quai hàm thon (0.1 cằm nhọn như bóng đèn, 0.065 mặt bánh bao)
    k += 0.022 * low * front ** 6 * _fr_sstep(-0.35, -0.7, d.z) * (1 - _fr_sstep(-0.8, -0.97, d.z))   # cằm nhỏ mềm
    for sgn in (1, -1):                                  # gò má rất nhẹ, ngoài-dưới mắt
        g = head_dir(180 + sgn * 46, -14)
        k += 0.012 * math.exp(-(1 - d.dot(g)) / 0.018)
    k += 0.012 * _fr_sstep(0.2, 0.9, d.z) * max(0.0, d.y) # sọ sau hơi đầy (dưới vòm)
    return d * (r * k)


def fr_head_frame(d, surf=None):
    """Điểm trên mặt đầu theo hướng d + pháp tuyến (sai phân hữu hạn trên hàm bề mặt)."""
    surf = surf or fr_head_surf
    d = Vector(d).normalized()
    t1 = d.cross(Vector((0, 0, 1)))
    if t1.length < 1e-3:
        t1 = d.cross(Vector((1, 0, 0)))
    t1.normalize()
    t2 = d.cross(t1)
    e = 2e-3
    n = (surf(d + t1 * e) - surf(d - t1 * e)).cross(surf(d + t2 * e) - surf(d - t2 * e)).normalized()
    return surf(d), (n if n.dot(d) > 0 else -n)


FR_DOME_RD = 1.048


def fr_face_decal(name, parent, center, az, el, w, h, mat, col, layer=0, roll=0.0, grid=10, surf=None, lift=0.0):
    """Như face_decal nhưng ôm theo bề mặt đầu Frieza (fr_head_surf), không phải elip."""
    p0, n0 = fr_head_frame(head_dir(az, el), surf)
    up = (Vector((0, 0, 1)) - n0 * n0.z).normalized()
    right = n0.cross(up).normalized()
    q = Quaternion(n0, rad(roll))
    up, right = q @ up, q @ right
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = {}
    off = 0.0016 + layer * 0.0011 + lift
    for i in range(grid + 1):
        for j in range(grid + 1):
            u, v = i / grid, j / grid
            ps, nn = fr_head_frame(p0 + right * (u - 0.5) * w + up * (v - 0.5) * h, surf)
            vs[i, j] = (bm.verts.new(ps + nn * off), (u, v))
    for i in range(grid):
        for j in range(grid):
            quad = [vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]]
            f = bm.faces.new([q_[0] for q_ in quad])
            for loop, (_, uvc) in zip(f.loops, quad):
                loop[uv].uv = uvc
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(name, bm, mat, col, outline=0)
    ob.parent = parent
    ob.location = center
    ob.visible_shadow = False
    return ob


def _fr_spline(prof, n=6):
    """Làm mượt biên dạng [(z, r)] bằng Catmull-Rom (n điểm mỗi đoạn) để khối tròn xoay không gãy khúc."""
    P = [prof[0]] + list(prof) + [prof[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    out.append(prof[-1])
    return out


def fr_body(name, prof, mat, col, parent, origin=(0, 0, 0), sy=1.0, rfn=None, seg=32, outline=0.005):
    """Khối tròn xoay mượt cho thân/tay/chân Frieza; `prof` theo toạ độ khớp cha, gốc vật đặt ở `origin`."""
    oz = origin[2]
    pr = [(z - oz, r) for z, r in _fr_spline(prof)]
    f = (lambda t, z, r: rfn(t, z + oz, r)) if rfn else None
    return attach(lathe(name, pr, mat, col, seg=seg, scale=(1, sy, 1), rfn=f, outline=outline), parent, origin)


def _fr_bump(x, x0, s):
    return math.exp(-((x - x0) / s) ** 2 / 2)


def build_frieza():
    c, R_ = C_FRIEZA, 0.18
    R = build_rig("FRIEZA", c, FRIEZA_DIM)
    W_, P = M["f_white"], M["f_purple"]
    hc = Vector((0, 0, R_ * 0.92))
    # v22 dáng chữ V: ngực/vai nở, eo + hông thon, đùi gọn (v19–v21 hông + đùi rộng hơn ngực như cái bình)
    # v17 dáng final form thon gọn (trước: thân hình quả lê, hông/đùi phình): ngực nở có cơ ngực, eo thắt,
    # hông gọn, đùi thon dần vào giáp ống chân. Khối tròn xoay mượt (fr_body) thay cho cầu/viên thuốc.
    def torso_rfn(t, z, r):                      # mặt cắt: cơ ngực nhô trước, lưng phẳng hơn
        fr_, cs = max(0.0, -math.sin(t)), abs(math.cos(t))
        pec = _fr_bump(z, 0.152, 0.03) * _fr_bump(cs, 0.5, 0.26) * fr_ ** 1.5
        back = max(0.0, math.sin(t)) * _fr_bump(z, 0.13, 0.06)
        return r * (1 + 0.085 * pec - 0.04 * back)
    attach(fr_body("fr_torso", [(0.274, 0.008), (0.27, 0.048), (0.262, 0.088), (0.248, 0.12), (0.228, 0.142),
                                (0.2, 0.156), (0.17, 0.157), (0.14, 0.145), (0.11, 0.124), (0.08, 0.102), (0.05, 0.088),
                                (0.02, 0.08), (-0.01, 0.076), (-0.035, 0.068), (-0.055, 0.045), (-0.062, 0.008)],
                   W_, c, R["chest"], sy=0.74, rfn=torso_rfn), R["chest"], (0, 0, 0))
    def pelvis_rfn(t, z, r):                     # mông nhỉnh ra sau, bụng dưới phẳng
        return r * (1 + 0.06 * max(0.0, math.sin(t)) * _fr_bump(z, -0.045, 0.03) - 0.03 * max(0.0, -math.sin(t)))
    # v22 hông thon ở eo, đáy tròn xuống ôm gốc đùi (hết gờ như quần đùi)
    fr_body("fr_pelvis", [(0.066, 0.008), (0.062, 0.034), (0.045, 0.058), (0.022, 0.068), (-0.008, 0.078), (-0.04, 0.083),
                          (-0.066, 0.076), (-0.09, 0.064), (-0.106, 0.036), (-0.112, 0.008)],
            W_, c, R["hips"], sy=0.8, rfn=pelvis_rfn)
    gy = -0.131 * 0.74 * (1 + 0.085 * _fr_bump(0.0, 0.5, 0.26)) - 0.009
    gem = attach(sphere("fr_chest_gem", 1, P, c, (0.04, 0.022, 0.034), outline=0.003), R["chest"], (0, gy, 0.15))
    gem.visible_shadow = False                   # vật nhỏ cong: tự đổ bóng lên chính nó thành sọc lấm tấm
    # cổ chắc hơn (v19: cổ que 0.045 làm đầu như bóng đèn cắm trên que), loe cơ ức đòn chũm xuống vai
    # v25 cổ thon phía trên + dẹt trước-sau: cằm nhô ra trước cổ (trước mặt trước cổ nhô hơn cằm → đầu liền cổ như
    # con ki bowling, không thấy đường hàm)
    # v30 cổ tông bóng (cằm đổ bóng xuống cổ như anime): trước cùng trắng với đầu → đầu liền một khối với cổ to
    NECK_ = toon("fr_neck_skin", "#E4DCF0", "#CFC2E6", "#E4DCF0")
    LINE_COLORS.setdefault("fr_neck_skin", LINE_COLORS.get("f_white", "#3E2A66"))
    fr_body("fr_neck", [(0.335, 0.008), (0.33, 0.04), (0.315, 0.05), (0.292, 0.054), (0.272, 0.062),
                        (0.255, 0.086), (0.24, 0.06), (0.232, 0.008)], NECK_, c, R["chest"], seg=28, sy=0.8,
            rfn=lambda t, z, r: r * (1 - 0.18 * max(0.0, -math.sin(t)) * _fr_bump(z, 0.29, 0.025)))
    # đầu final form: sọ tròn dưới vòm, nửa dưới mặt thon về cằm nhỏ (fr_head_surf); decal/vòm/tai ôm theo hàm này
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1.0)
    for v in bm.verts:
        v.co = fr_head_surf(v.co)
    # mặt riêng: gần như sáng toàn mặt (trước nửa mặt phủ mảng bóng lavender như bị bẩn), nét viền tím như thân
    face_m = toon("fr_face", "#F9F6FC", "#E9E2F4", "#FFFFFF", rim=0.6)
    LINE_COLORS["fr_face"] = LINE_COLORS["f_white"]
    attach(_obj("fr_head", bm, face_m, c, outline=0.007), R["head"], tuple(hc))
    # vòm đầu tím bóng: vỏ lớn hơn đầu 3.5%, dựng theo (az, el) từ mép lên đỉnh nên mép trơn liền mạch.
    # v15: vòm to đúng nguyên tác — mép trước xuống sát trên chân mày (~26°), thái dương 13° (trên lỗ tai), gáy -32°
    cut = lambda az: 5 - 29.5 * math.cos(az) - 8 * math.cos(2 * az) - 7 * max(0.0, -math.cos(az)) ** 3   # v22 mép trước 26.5° → 19.5°
    bm = bmesh.new()
    # v27 rd 1.035 → 1.048: mặt trong vòm trùng gần khít vỏ viền của đầu (r + 0.007) → nhìn xa z-fight thành đường chấm trắng dọc mép
    NA, NE, rd = 64, 16, FR_DOME_RD
    rows = []
    for j in range(NE):
        row = []
        for i in range(NA):
            az = math.tau * i / NA
            lim = rad(cut(az))
            e = lim + (rad(89.0) - lim) * (j / (NE - 1)) ** 0.9
            row.append(bm.verts.new(fr_head_surf(Vector((math.cos(e) * math.sin(az), math.cos(e) * math.cos(az),
                                                         math.sin(e)))) * rd))
        rows.append(row)
    top = bm.verts.new(fr_head_surf(Vector((0, 0, 1))) * rd)
    for j in range(NE - 1):
        for i in range(NA):
            bm.faces.new((rows[j][i], rows[j + 1][i], rows[j + 1][(i + 1) % NA], rows[j][(i + 1) % NA]))   # pháp tuyến hướng ra
    for i in range(NA):
        bm.faces.new((rows[-1][i], top, rows[-1][(i + 1) % NA]))
    dome = _obj("fr_dome", bm, P, c, outline=0.006)
    sol = dome.modifiers.new("Thick", "SOLIDIFY"); sol.thickness, sol.offset = 0.006, 1.0
    dome.modifiers.move(1, 0)
    attach(dome, R["head"], tuple(hc))
    T = {k: tex_mat(f"tx_{k}", f"{k}.png") for k in ("frieza_eye_R", "frieza_eye_L", "frieza_eye_shock_R", "frieza_eye_shock_L",
                                                       "frieza_eye_blink_R", "frieza_eye_blink_L", "frieza_mouth", "frieza_mouth_open",
                                                       "frieza_eye_angry_R", "frieza_eye_angry_L", "frieza_eye_hit_R", "frieza_eye_hit_L",
                                                       "frieza_mouth_snarl", "frieza_mouth_pain")}
    R["eyes"], R["eyes_shock"], R["eyes_blink"], R["eyes_angry"], R["eyes_hit"] = [], [], [], [], []
    for side, sgn in (("R", 1), ("L", -1)):
        R["eyes"].append(fr_face_decal(f"fr_eye_{side}", R["head"], hc, 180 + sgn * 20, -2, 0.132, 0.142, T[f"frieza_eye_{side}"], c, 1))
        R["eyes_blink"].append(fr_face_decal(f"fr_eye_blink_{side}", R["head"], hc, 180 + sgn * 20, -3, 0.132, 0.104, T[f"frieza_eye_blink_{side}"], c, 1))
        R["eyes_shock"].append(fr_face_decal(f"fr_eye_shock_{side}", R["head"], hc, 180 + sgn * 20, -2, 0.136, 0.159, T[f"frieza_eye_shock_{side}"], c, 1))
        R["eyes_angry"].append(fr_face_decal(f"fr_eye_angry_{side}", R["head"], hc, 180 + sgn * 20, -2, 0.132, 0.142, T[f"frieza_eye_angry_{side}"], c, 1))
        R["eyes_hit"].append(fr_face_decal(f"fr_eye_hit_{side}", R["head"], hc, 180 + sgn * 20, -2, 0.132, 0.13, T[f"frieza_eye_hit_{side}"], c, 1))
        # vạch tím dưới mắt (final form), luôn hiện bất kể nét mặt
        fr_face_decal(f"fr_cheek_{side}", R["head"], hc, 180 + sgn * 26, -20, 0.058, 0.055,
                      tex_mat(f"tx_frieza_cheek_{side}", f"frieza_cheek_{side}.png"), c, 0)
    ear = tex_mat("tx_frieza_ear", "frieza_ear.png")
    for side, sgn in (("R", 1), ("L", -1)):
        fr_face_decal(f"fr_ear_{side}", R["head"], hc, 180 + sgn * 90, 2, 0.035, 0.05, ear, c, 0)
    # vòm đầu giờ phủ tới trán: gân giận dán lên mặt vòm, giọt mồ hôi xuống thái dương (dưới mép vòm)
    R["anger"] = fr_face_decal("fr_anger", R["head"], hc, 180 - 40, 37, 0.09, 0.09, tex_mat("tx_anger", "anger.png"), c, 2,
                               surf=lambda d: fr_head_surf(d) * FR_DOME_RD, lift=0.0065)
    R["sweat"] = fr_face_decal("fr_sweat", R["head"], hc, 180 + 56, 8, 0.05, 0.07, tex_mat("tx_sweat", "sweat.png"), c, 2)
    # v26 mũi: hai lỗ mũi nhỏ giữa mắt và miệng (trước mặt trơn không mũi như mặt nạ)
    fr_face_decal("fr_nose", R["head"], hc, 180, -17, 0.05, 0.034, tex_mat("tx_frieza_nose", "frieza_nose.png"), c, 0)
    R["mouth"] = [fr_face_decal("fr_mouth", R["head"], hc, 180, -29, 0.088, 0.08, T["frieza_mouth"], c, 0)]
    R["laugh"] = [fr_face_decal("fr_mouth_laugh", R["head"], hc, 180, -30, 0.068, 0.05, tex_mat("tx_frieza_mouth_laugh", "frieza_mouth_laugh.png"), c, 0)]
    R["mouth_open"] = [fr_face_decal("fr_mouth_open", R["head"], hc, 180, -31, 0.06, 0.064, T["frieza_mouth_open"], c, 0)]
    R["snarl"] = [fr_face_decal("fr_mouth_snarl", R["head"], hc, 180, -30, 0.082, 0.056, T["frieza_mouth_snarl"], c, 0)]
    R["pain"] = [fr_face_decal("fr_mouth_pain", R["head"], hc, 180, -32, 0.078, 0.076, T["frieza_mouth_pain"], c, 0)]
    for side, sx in (("R", -1), ("L", 1)):
        # giáp vai dạng vòm (nửa dưới ép dẹt thành đáy phẳng ôm vai) thay vì quả cầu đeo vòng như sao Thổ
        pad = attach(sphere(f"fr_shoulder_{side}", 0.07, P, c, (1.12, 1.0, 0.74)), R[f"sh_{side}"], (sx * 0.012, 0, 0.012))
        for v in pad.data.vertices:
            if v.co.z < 0:
                v.co.z *= 0.42
        # bắp tay trên thon (gốc chìm trong giáp vai), cẳng tay giáp tím ôm, loe nhẹ ở khuỷu
        # v22 tay trắng liền một khối bẻ ở khuỷu (skin_limb), cẳng tay trắng chạy dưới giáp tím
        Lf = FRIEZA_DIM["upper"]
        skin_limb(f"fr_arm_{side}", [(0.02, 0.0), (0.012, 0.038), (-0.012, 0.047), (-0.05, 0.047), (-0.095, 0.041),
                                     (-0.14, 0.036), (-Lf, 0.034), (-Lf - 0.03, 0.032), (-Lf - 0.08, 0.03),
                                     (-Lf - 0.13, 0.028), (-Lf - 0.15, 0.0)],
                  R[f"sh_{side}"], R[f"el_{side}"], W_, c, seg=24, blend=0.04,
                  rfn=lambda t, z, r, w: r * (1 - 0.06 * (1 - w) * abs(math.sin(t))))
        fr_body(f"fr_fore_{side}", [(0.016, 0.006), (0.008, 0.032), (-0.008, 0.044), (-0.035, 0.048), (-0.07, 0.046),
                                    (-0.098, 0.041), (-0.118, 0.037), (-0.128, 0.028), (-0.133, 0.006)],
                P, c, R[f"el_{side}"], (0, 0, -0.065), sy=0.92, seg=28)
        # v16 bàn tay chibi 4 ngón (3 ngón + cái), thay cho găng tròn: lòng bàn tay dẹt + ngón bo tròn.
        # Hai bộ ngón đổi bằng hiện/ẩn (finger_when_shooting): co hờ (khoanh tay, đấm, bay) và xoè (hoảng, trúng đòn).
        attach(sphere(f"fr_hand_{side}", 0.045, W_, c, (0.78, 1.0, 0.86)), R[f"el_{side}"], (0, 0, -0.155))
        attach(capsule(f"fr_thumb_{side}", 0.0125, 0.024, W_, c, seg=12, outline=0.003),
               R[f"el_{side}"], (-sx * 0.03, -0.032, -0.162), (62, 0, -sx * 28))
        ys = (-0.018, 0.004, 0.026)
        def fset(name, ids, curl, spread, L):
            bm = bmesh.new()
            for i in ids:
                _merge(bm, fr_finger_bm(sx, (0, ys[i], -0.178), L * (0.88 if i == 2 else 1.0), 0.0118, curl,
                                        spread * (i - 1)))
            ob = _obj(name, bm, W_, c, outline=0.003)
            ob.parent = R[f"el_{side}"]
            ob.visible_shadow = False            # ngón nhỏ: tự đổ bóng thành vệt lấm tấm
            return ob
        R[f"fingers_{side}"] = [fset(f"fr_fingers_{side}", (1, 2) if side == "R" else (0, 1, 2), 95, 0, 0.036)]
        if side == "R":                          # ngón trỏ co hờ: ẩn khi ngón trỏ duỗi bắn Death Beam
            R["finger_idx_R"] = fset("fr_finger_idx_R", (0,), 95, 0, 0.036)
        R[f"fingers_open_{side}"] = fset(f"fr_fingers_open_{side}", (0, 1, 2), 18, -13, 0.042)
        if side == "R":                          # ngón trỏ duỗi ra (bắn Death Beam)
            attach(capsule("fr_finger_R", 0.0118, 0.035, W_, c, seg=12, outline=0.003), R["el_R"], (0, -0.014, -0.205))
        # đùi thon dần vào gối (gốc chìm trong hông), giáp ống chân tím có bắp chân, bàn chân nhỏ gọn (ngón: frieza_details)
        def thigh_rfn(t, z, r, sx=sx):
            inner = max(0.0, -sx * math.cos(t))      # mặt trong đùi phẳng hơn để hai đùi không cấn nhau
            return r * (1 - 0.1 * inner * _fr_bump(z, -0.03, 0.06))
        # v22 chân trắng liền một khối bẻ ở gối (skin_limb) thay đùi + quả cầu gối rời; ống chân trắng chạy dưới giáp tím
        Lt = FRIEZA_DIM["thigh"]
        skin_limb(f"fr_leg_{side}", [(0.004, 0.0), (-0.004, 0.034), (-0.022, 0.05), (-0.05, 0.056), (-0.085, 0.052),
                                     (-0.135, 0.044), (-0.175, 0.039), (-Lt + 0.01, 0.037), (-Lt, 0.038),
                                     (-Lt - 0.02, 0.037), (-Lt - 0.07, 0.035), (-Lt - 0.13, 0.031), (-Lt - 0.18, 0.029),
                                     (-Lt - 0.2, 0.0)],
                  R[f"hip_{side}"], R[f"kn_{side}"], W_, c, seg=28, blend=0.04,
                  rfn=lambda t, z, r, w, f=thigh_rfn: f(t, z, r) if w < 0.5 else r)
        def shin_rfn(t, z, r):                   # bắp chân nhô sau, ống chân trước hơi sống
            return r * (1 + 0.1 * max(0.0, math.sin(t)) * _fr_bump(z, -0.06, 0.035))
        fr_body(f"fr_shin_{side}", [(-0.008, 0.006), (-0.012, 0.032), (-0.022, 0.045), (-0.04, 0.048), (-0.072, 0.045),
                                    (-0.11, 0.039), (-0.145, 0.034), (-0.165, 0.033), (-0.177, 0.026), (-0.182, 0.006)],
                P, c, R[f"kn_{side}"], (0, 0, -0.09), sy=0.95, rfn=shin_rfn, seg=28)
        attach(sphere(f"fr_foot_{side}", 1, W_, c, (0.04, 0.064, 0.03)), R[f"kn_{side}"], (0, -0.018, FR_FOOT_Z + 0.006))
    # đuôi: 8 khớp Empty (vũ đạo xoay các khớp này) + 1 đường cong NURBS liền mạch móc (hook) vào từng khớp,
    # vát tròn thon dần từ gốc tới chóp
    prev, R["tail"] = R["hips"], []
    # v17 dáng chữ S thanh thoát: cong sẵn bằng delta_rotation (cộng thêm vào key lắc đuôi ở choreograph, không đổi
    # vũ đạo): gốc rủ xuống sau mông, giữa vòng ra sau, chóp hất lên; đốt ngắn dần về chóp
    s_rx = (-4, -12, -10, 16, 34, 42, 40, 34)
    s_ln = (0.1, 0.1, 0.098, 0.096, 0.092, 0.088, 0.084, 0.08)
    for i in range(8):
        seg = empty(f"FRIEZA_tail_{i}", c, prev, (0, 0.08, -0.03) if i == 0 else (0, s_ln[i - 1], 0))
        seg.delta_rotation_euler = (rad(s_rx[i]), 0, rad(4 * math.sin(i * 0.9)))
        R["tail"].append(seg)
        prev = seg
    tip = empty("FRIEZA_tail_tip", c, prev, (0, s_ln[-1], 0))
    bpy.context.view_layer.update()
    hooks = [R["hips"]] + R["tail"] + [tip]
    cu = bpy.data.curves.new("fr_tail", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("NURBS")
    sp.points.add(len(hooks) - 1)
    sp.order_u, sp.use_endpoint_u = 4, True
    for i, h in enumerate(hooks):
        p = h.matrix_world.translation + (Vector((0, 0.03, -0.02)) if i == 0 else Vector())
        sp.points[i].co = (p.x, p.y, p.z, 1.0)
        sp.points[i].radius = (1.0, 0.86, 0.7, 0.56, 0.44, 0.34, 0.25, 0.17, 0.09, 0.0)[i]   # gốc dày, thon nhọn tới chóp
    cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps, cu.resolution_u = 0.064, 5, True, 12
    tail = bpy.data.objects.new("fr_tail", cu)
    c.objects.link(tail)
    cu.materials.append(W_)
    cu.materials.append(line_mat(W_))
    for i, h in enumerate(hooks):
        hk = tail.modifiers.new(f"hook_{i}", "HOOK")
        hk.object = h
        hk.vertex_indices_set([i])
        hk.matrix_inverse = h.matrix_world.inverted()
    ol = tail.modifiers.new("Outline", "SOLIDIFY")
    ol.thickness, ol.offset, ol.use_flip_normals, ol.use_rim, ol.material_offset = -0.004, -1.0, True, False, 1   # pháp tuyến ống vát hướng vào trong
    R["finger_anchor"] = empty("FRIEZA_finger_anchor", c, R["el_R"], (0, -0.012, -0.235), 0.05)
    # quả cầu khí: lõi trắng nóng → hồng → viền tím hồng đậm theo góc nhìn (trước là một đĩa hồng phẳng như miếng dán)
    nt = M["charge"].node_tree
    em = next(n for n in nt.nodes if n.type == "EMISSION")
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    ramp = nt.nodes.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "CONSTANT"
    cr.elements[0].color, cr.elements[1].position, cr.elements[1].color = hexc("#FFFFFF"), 0.1, hexc("#FF62D2")
    e = cr.elements.new(0.32); e.color = hexc("#B81C9C")
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    R["charge"] = sphere("fr_charge", 0.032, M["charge"], c, seg=24, outline=0)   # đầu ngón tay tụ khí trước khi bắn
    attach(R["charge"], R["finger_anchor"], (0, 0, 0))
    R["charge"].visible_shadow = False
    R["head_anchor"] = empty("FRIEZA_head_anchor", c, R["head"], tuple(hc), 0.05)
    R["chest_anchor"] = empty("FRIEZA_chest_anchor", c, R["chest"], (0, 0, 0.12), 0.05)
    return R


# ───────────────────────────── environment ─────────────────────────────
CHASE_SPIRES = [(22, 4.6, 0), (38, -10, 0), (55, 8, 0), (72, -6, 0)]   # cột 0 từng nằm ngay trên đường bay (bay xuyên lõi đá)
BLASTS = [(840, Vector((30.0, 9.5, 8.0))), (900, Vector((48.0, -8.5, 10.0))), (955, Vector((63.0, 6.5, 7.0)))]


def chase_path(u):
    """Đường bay shot 8 (u: 0..1), luồn giữa các cột đá."""
    return Vector((4 + u * 80, 9 * math.sin(u * math.tau * 1.15), 5 + 3 * math.sin(u * math.tau * 0.9 + 0.6)))


def build_env():
    c = C_ENV
    g = cyl("ground", 75, 75, 0.6, toon_tex("ground_tex", "ground_grass.jpg", fallback=M["ground"]), c, seg=64, outline=0, smooth=False)
    g.location = (0, 0, -0.3)
    sea = box("sea", (3000, 3000, 0.1), toon_tex("sea_tex", "sea.jpg", tile=14.0, shade=(0.75, 0.82, 0.86), threshold=0.3, fallback=M["water"], flow=1.6), c, outline=0)
    sea.location = (0, 0, -0.7)

    rock = toon_tex("rock_tex", "rock.jpg", tile=6.0, shade=(0.66, 0.72, 0.74), threshold=0.3, fallback=M["rock"], box=True)
    leaves = toon_tex("canopy_tex", "foliage.jpg", tile=1.4, shade=(0.62, 0.7, 0.72), threshold=0.3, fallback=M["canopy"], box=True)
    tops = toon_tex("top_tex", "ground_grass.jpg", tile=4.0, shade=(0.68, 0.74, 0.8), threshold=0.25, fallback=M["grass_top"], box=True)

    def spire(name, x, y, r, hgt, base_z=-0.7):
        s = cyl(name, r, r * 0.72, hgt, rock, c, seg=9, outline=0.06, smooth=False)
        s.location = (x, y, base_z + hgt / 2)
        s.rotation_euler = (0, 0, random.random() * 6)
        top = cyl(name + "_top", r * 0.8, r * 0.78, 0.5, tops, c, seg=9, outline=0.04, smooth=False)
        top.location = (x, y, base_z + hgt + 0.2)
        if random.random() < 0.7:
            tree(name + "_tree", x + random.uniform(-r, r) * 0.3, y + random.uniform(-r, r) * 0.3, base_z + hgt + 0.4, 1.5)

    def tree(name, x, y, z, s=1.0):
        t = cyl(name + "_trunk", 0.12 * s, 0.08 * s, 3.2 * s, M["trunk"], c, seg=8, outline=0.02)
        t.location = (x, y, z + 1.6 * s)
        top = sphere(name + "_canopy", 1.0 * s, leaves, c, (1, 1, 0.85), seg=20, outline=0.03)
        top.location = (x, y, z + 3.5 * s)

    for i, (x, y, _) in enumerate(CHASE_SPIRES):
        spire(f"spire_chase_{i}", x, y, 3.2, 16 + i * 2)
    n = 0
    while n < 34:
        a, d = random.uniform(0, math.tau), random.uniform(16, 160)
        x, y = math.cos(a) * d, math.sin(a) * d
        if abs(y) < 14 and 0 < x < 90:      # chừa đường bay
            continue
        spire(f"spire_{n}", x, y, random.uniform(2, 6), random.uniform(8, 40))
        n += 1
    for i in range(26):
        a, d = random.uniform(0, math.tau), random.uniform(9, 60)
        tree(f"tree_{i}", math.cos(a) * d, math.sin(a) * d, 0, random.uniform(0.8, 1.4))
    # mây: cụm nhiều khối cầu phồng (chỉ dùng khi không có bầu trời vẽ tay, vì ảnh trời đã có mây)
    for i in range(0 if os.path.exists(os.path.join(TEX, "sky_calm.jpg")) else 16):
        bm = bmesh.new()
        sz = random.uniform(10, 18)
        for k in range(6):
            tmp = bmesh.new()
            r = sz * random.uniform(0.45, 0.8)
            bmesh.ops.create_uvsphere(tmp, u_segments=16, v_segments=10, radius=r)
            off = Vector((random.uniform(-1.6, 1.6) * sz, random.uniform(-0.6, 0.6) * sz, random.uniform(-0.1, 0.35) * sz))
            for v in tmp.verts:
                v.co = Vector((v.co.x, v.co.y, v.co.z * 0.6)) + off
            _merge(bm, tmp)
        cl = _obj(f"cloud_{i}", bm, M["cloud"], c, outline=0)
        a = random.uniform(0, math.tau)
        cl.location = (math.cos(a) * 150, math.sin(a) * 150, random.uniform(55, 90))
        cl.rotation_euler = (0, 0, a + math.pi / 2)
    # thảm cỏ loang + bụi cỏ + đá nhỏ quanh sân đấu (chừa vòng nứt quanh Goku)
    bm = bmesh.new()
    for i in range(0 if os.path.exists(os.path.join(TEX, "ground_grass.jpg")) else 36):   # đất đã vẽ tay thì bỏ thảm loang
        a, d = random.uniform(0, math.tau), random.uniform(6, 55)
        tmp = bmesh.new()
        bmesh.ops.create_circle(tmp, cap_ends=True, segments=20, radius=1.0)
        sx, sy = random.uniform(1.5, 4.5), random.uniform(1.0, 3.0)
        rot = random.uniform(0, math.pi)
        for v in tmp.verts:
            x, y = v.co.x * sx, v.co.y * sy
            v.co = Vector((math.cos(a) * d + x * math.cos(rot) - y * math.sin(rot), math.sin(a) * d + x * math.sin(rot) + y * math.cos(rot), 0.004))
        _merge(bm, tmp)
    if bm.verts:
        _obj("grass_patches", bm, M["grass_dark"], c, smooth=False, outline=0)
    else:
        bm.free()
    bm = bmesh.new()
    for i in range(420):
        a, d = random.uniform(0, math.tau), random.uniform(3.5, 40)
        base = Vector((math.cos(a) * d, math.sin(a) * d, 0))
        for k in range(3):
            tmp = bmesh.new()
            h = random.uniform(0.18, 0.4)
            bmesh.ops.create_cone(tmp, cap_ends=False, segments=4, radius1=0.035, radius2=0.0, depth=h)
            tilt = Euler((random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), random.uniform(0, 6)))
            for v in tmp.verts:
                v.co = tilt.to_matrix() @ (v.co + Vector((0, 0, h / 2))) + base + Vector((random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), 0))
            _merge(bm, tmp)
    tufts = _obj("grass_tufts", bm, M["grass_top"], c, smooth=False, outline=0)
    tufts.visible_shadow = False
    # đá nhỏ: trước là 70 icosphere bẹt nửa chìm tô một màu nâu → nhìn như vết bẩn. Giờ ít hơn (~40%), có khối,
    # 3 tông cel + viền, đôi khi kèm 1–2 hòn con. Vẫn gọi `random` đúng số lần cũ để không xáo vết nứt/debris phía sau.
    bm = bmesh.new()
    prng = random.Random(911)
    for i in range(70):
        a, d = random.uniform(0, math.tau), random.uniform(5, 45)
        r0 = random.uniform(0.12, 0.45)
        if prng.random() > 0.42:
            continue
        cx, cy = math.cos(a) * d, math.sin(a) * d
        rock_lump(bm, (cx, cy), r0 * 0.75, prng)
        for _ in range(prng.choice((0, 1, 1, 2))):
            oa = prng.uniform(0, math.tau)
            rock_lump(bm, (cx + math.cos(oa) * r0 * 1.2, cy + math.sin(oa) * r0 * 1.2), r0 * prng.uniform(0.3, 0.5), prng)
    peb = _obj("pebbles", bm, M["rock_small"], c, smooth=False, outline=0.012)
    # nhà mái vòm người Namek ở hậu cảnh
    for i, (x, y, sz) in enumerate([(-18, 26, 2.6), (-23, 21, 1.8), (-12, 31, 2.0), (26, 34, 2.4), (31, 29, 1.6)]):
        hb = sphere(f"house_{i}", sz, M["house"], c, (1, 1, 0.82), seg=28, outline=0.03)
        hb.location = (x, y, sz * 0.25)
        for k in range(3):
            ang = math.atan2(-y, -x) + (k - 1) * 0.55
            dvec = Vector((math.cos(ang), math.sin(ang), 0))
            w = cyl(f"house_{i}_win_{k}", sz * 0.13, sz * 0.13, 0.05, M["window"], c, seg=16, outline=0)
            w.location = Vector((x, y, sz * 0.25 + sz * 0.42)) + dvec * sz * 0.93
            w.rotation_euler = dvec.to_track_quat("Z", "Y").to_euler()
        door = sphere(f"house_{i}_door", sz * 0.24, M["window"], c, (1, 0.3, 1.4), outline=0)
        dvec = Vector((math.cos(math.atan2(-y, -x) + 1.2), math.sin(math.atan2(-y, -x) + 1.2), 0))
        door.location = Vector((x, y, sz * 0.25)) + dvec * sz * 0.98
        door.rotation_euler = (0, 0, math.atan2(dvec.y, dvec.x) + math.pi / 2)
    # vết nứt toả ra quanh Goku, debris, cột nước
    cracks = []
    for i in range(14):
        a = i / 14 * math.tau + random.uniform(-0.15, 0.15)
        piv = empty(f"crack_{i}", c, None, (0, 0, 0.005))
        piv.rotation_euler = (0, 0, a)
        # khe nứt zigzag thon dần: mép tối + lõi rực sáng (piv giãn theo Y nên biên độ ngang giữ nguyên khi lan dài)
        zr = random.Random(300 + i)
        pts = [(0.0, 0.0)] + [(zr.uniform(-0.035, 0.035), (k_ + zr.uniform(-0.3, 0.3)) / 9) for k_ in range(1, 9)] + [(0.0, 1.0)]
        for nm, w0, mat, z in ((f"crack_mesh_{i}", 0.05, M["crack_edge"], 0.0), (f"crack_core_{i}", 0.022, M["crack"], 0.004)):
            bm = bmesh.new()
            left, right = [], []
            for j, (x, y) in enumerate(pts):
                w = w0 * (1 - j / (len(pts) - 1)) ** 0.7 + 0.002
                left.append(bm.verts.new((x - w, y, z))); right.append(bm.verts.new((x + w, y, z)))
            for j in range(len(pts) - 1):
                bm.faces.new((left[j], right[j], right[j + 1], left[j + 1]))
            k = _obj(nm, bm, mat, c, smooth=False, outline=0)
            k.visible_shadow = False
            attach(k, piv, (0, 0, 0))
        cracks.append((piv, random.uniform(1.6, 4.0)))
    debris = []
    chunk = M["rock_small"]      # cùng chất liệu đá nhỏ (trước: rock.jpg nâu phẳng → chấm bẩn trên cỏ khi nằm yên)
    for i in range(46):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.05, 0.22))
        d = _obj(f"debris_{i}", bm, chunk, c, smooth=False, outline=0.01)
        a, r = random.uniform(0, math.tau), random.uniform(1.2, 6.0)
        debris.append((d, a, r))
    splash = cyl("splash", 1.6, 0.2, 6, M["splash"], c, seg=14, outline=0.05)
    # bờ đá quanh đảo: vách đá gồ ghề từ mặt biển lên sát mép cỏ (trước đó là mặt hông của khối trụ cỏ, ảnh bị kéo
    # thành sọc dọc). Dùng RNG riêng để không xáo các vật ngẫu nhiên phía sau.
    rng = random.Random(75)
    bm = bmesh.new()
    seg, rows = 220, 4
    ring = []
    for j in range(rows + 1):
        z = -0.72 + 0.7 * j / rows
        row = []
        for i in range(seg):
            a = math.tau * i / seg
            r = 75.0 + 0.25 + rng.uniform(0.0, 0.5) + (0.35 if j < rows else 0.0) * rng.random()
            row.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z + (rng.uniform(-0.05, 0.0) if j == rows else 0.0))))
        ring.append(row)
    for j in range(rows):
        for i in range(seg):
            a, b = ring[j], ring[j + 1]
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    # gờ trên phủ lên mép cỏ một chút để không hở khe
    top = [bm.verts.new((v.co.x * 74.6 / v.co.xy.length, v.co.y * 74.6 / v.co.xy.length, 0.02)) for v in ring[-1]]
    for i in range(seg):
        bm.faces.new((ring[-1][i], ring[-1][(i + 1) % seg], top[(i + 1) % seg], top[i]))
    bm.normal_update()
    cliff = _obj("shore_cliff", bm, rock, c, smooth=False, outline=0.03)
    # bọt sóng trắng vỗ quanh chân vách: vành khuyên trên mặt biển, alpha = noise cắt cứng × mờ dần ra ngoài
    fm = bpy.data.materials.new("foam")
    fm.use_nodes = True
    nt = fm.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    geo = N.new("ShaderNodeNewGeometry")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 3.0
    L.new(geo.outputs["Position"], nz.inputs["Vector"])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(sep.outputs["X"], cmb.inputs["X"]); L.new(sep.outputs["Y"], cmb.inputs["Y"])
    L.new(cmb.outputs[0], ln.inputs[0])
    fall = N.new("ShaderNodeMapRange")
    fall.inputs["From Min"].default_value, fall.inputs["From Max"].default_value = 75.6, 77.6
    fall.inputs["To Min"].default_value, fall.inputs["To Max"].default_value = 0.38, 0.62
    L.new(ln.outputs["Value"], fall.inputs["Value"])
    cut = N.new("ShaderNodeMath"); cut.operation = "GREATER_THAN"
    L.new(nz.outputs["Fac"], cut.inputs[0]); L.new(fall.outputs["Result"], cut.inputs[1])
    a = N.new("ShaderNodeMath"); a.operation = "MULTIPLY"; a.inputs[1].default_value = 0.9
    L.new(cut.outputs[0], a.inputs[0])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = hexc("#EFFFFB"); em.inputs["Strength"].default_value = 1.0
    mode = N.new("ShaderNodeValue"); mode.name = "energy_mode"; mode.outputs[0].default_value = 0.0
    blk = N.new("ShaderNodeEmission"); blk.inputs["Strength"].default_value = 0.0
    pick = N.new("ShaderNodeMixShader"); L.new(mode.outputs[0], pick.inputs[0])
    L.new(em.outputs[0], pick.inputs[1]); L.new(blk.outputs[0], pick.inputs[2])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(a.outputs[0], mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(pick.outputs[0], mx.inputs[2])
    out = N.new("ShaderNodeOutputMaterial"); L.new(mx.outputs[0], out.inputs["Surface"])
    try:
        fm.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        fm.blend_method = "BLEND"
    bm = bmesh.new()
    inner = [bm.verts.new((math.cos(math.tau * i / 220) * 75.3, math.sin(math.tau * i / 220) * 75.3, -0.64)) for i in range(220)]
    outer = [bm.verts.new((math.cos(math.tau * i / 220) * 77.6, math.sin(math.tau * i / 220) * 77.6, -0.64)) for i in range(220)]
    for i in range(220):
        bm.faces.new((inner[i], outer[i], outer[(i + 1) % 220], inner[(i + 1) % 220]))
    foam = _obj("shore_foam", bm, fm, c, smooth=False, outline=0)
    foam.visible_shadow = False
    return cracks, debris, splash


# ───────────────────────────── world & lights ─────────────────────────────
def build_world():
    w = bpy.data.worlds.new("Namek")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])

    def ramp(c0, c1):
        r = N.new("ShaderNodeValToRGB")
        r.color_ramp.elements[0].position, r.color_ramp.elements[0].color = 0.0, hexc(c0)
        r.color_ramp.elements[1].position, r.color_ramp.elements[1].color = 0.55, hexc(c1)
        L.new(sep.outputs["Z"], r.inputs["Fac"])
        bg = N.new("ShaderNodeBackground")
        L.new(r.outputs["Color"], bg.inputs["Color"])
        return bg

    calm, storm = ramp("#C9EDB4", "#6CC07A"), ramp("#5B7A62", "#18241E")
    # bầu trời vẽ tay (Codex): ảnh 2:1 quấn 2 vòng quanh 360°, chân ảnh (biển + mesa xa) đặt ở đường chân trời
    if os.path.exists(os.path.join(TEX, "sky_calm.jpg")):
        at = N.new("ShaderNodeMath"); at.operation = "ARCTAN2"
        L.new(sep.outputs["Y"], at.inputs[0]); L.new(sep.outputs["X"], at.inputs[1])
        u = N.new("ShaderNodeMath"); u.operation = "DIVIDE"; u.inputs[1].default_value = math.pi
        L.new(at.outputs[0], u.inputs[0])
        drift = N.new("ShaderNodeValue"); drift.name = "sky_drift"      # mây trôi chậm theo thời gian
        # v30 mây giông cuồn cuộn trôi nhanh lúc giông đầu phim (gió mạnh), chậm hẳn sau nổ biến hình (frame gốc 296)
        for f_, v_ in ((0, 0.0), (296, 0.026), (FRAMES - 1, 0.04)):
            drift.outputs[0].default_value = v_; drift.outputs[0].keyframe_insert("default_value", frame=f_)
        for fc in _fcurves(nt.animation_data):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        ud = N.new("ShaderNodeMath"); ud.operation = "ADD"
        L.new(u.outputs[0], ud.inputs[0]); L.new(drift.outputs[0], ud.inputs[1])
        uw = N.new("ShaderNodeMath"); uw.operation = "FLOORED_MODULO"; uw.inputs[1].default_value = 1.0   # ảnh EXTEND: gói u về 0..1
        L.new(ud.outputs[0], uw.inputs[0])
        u = uw
        for bg, png, hv in ((calm, "sky_calm.jpg", 0.055), (storm, "sky_storm.jpg", 0.03)):
            v = N.new("ShaderNodeMath"); v.operation = "MULTIPLY_ADD"
            v.inputs[1].default_value = 1.05; v.inputs[2].default_value = hv
            L.new(sep.outputs["Z"], v.inputs[0])
            cv = N.new("ShaderNodeCombineXYZ")
            L.new(u.outputs[0], cv.inputs["X"]); L.new(v.outputs[0], cv.inputs["Y"])
            im = N.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(os.path.join(TEX, png), check_existing=True)
            im.extension = "EXTEND"; im.interpolation = "Cubic"
            L.new(cv.outputs[0], im.inputs["Vector"])
            L.new(im.outputs["Color"], bg.inputs["Color"])
    mix = N.new("ShaderNodeMixShader"); mix.name = "storm"
    L.new(calm.outputs[0], mix.inputs[1]); L.new(storm.outputs[0], mix.inputs[2])
    amb = N.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = hexc("#7FA88F"); amb.inputs["Strength"].default_value = 0.0   # GI của EEVEE gây nhiễu qua ngưỡng toon
    lp = N.new("ShaderNodeLightPath")
    cam = N.new("ShaderNodeMixShader")
    L.new(lp.outputs["Is Camera Ray"], cam.inputs[0])
    L.new(amb.outputs[0], cam.inputs[1]); L.new(mix.outputs[0], cam.inputs[2])
    out = N.new("ShaderNodeOutputWorld")
    L.new(cam.outputs[0], out.inputs["Surface"])
    return mix


def build_lights(goku):
    sun_d = bpy.data.lights.new("key_sun", "SUN")
    sun_d.energy, sun_d.angle, sun_d.color = 3.4, rad(0.2), (1.0, 0.97, 0.9)
    sun_d.shadow_filter_radius = 0.5
    sun = bpy.data.objects.new("key_sun", sun_d)
    C_LIGHT.objects.link(sun)
    sun.rotation_euler = (rad(50), 0, rad(-35))
    rim_d = bpy.data.lights.new("rim_sun", "SUN")
    rim_d.energy, rim_d.color = 1.2, (0.75, 0.85, 1.0)
    rim = bpy.data.objects.new("rim_sun", rim_d)
    C_LIGHT.objects.link(rim)
    rim.rotation_euler = (rad(60), 0, rad(150))
    auras = []
    for i, (x, y, z) in enumerate([(0.8, 0.4, 1.2), (-0.8, 0.4, 1.2), (0, -0.7, 0.4), (0, 0.6, 2.0)]):
        d = bpy.data.lights.new(f"aura_light_{i}", "POINT")
        d.energy, d.color, d.shadow_soft_size = 0.0, (1.0, 0.78, 0.25), 0.4
        d.use_shadow = False                 # chỉ là ánh hắt; bóng mềm của đèn điểm gây nhiễu
        o = bpy.data.objects.new(f"aura_light_{i}", d)
        C_LIGHT.objects.link(o)
        o.parent, o.location = goku["root"], (x, y, z)
        auras.append(d)
    return sun_d, auras


# ───────────────────────────── keyframe helpers ─────────────────────────────
def kloc(ob, f, loc):
    ob.location = loc
    ob.keyframe_insert("location", frame=f)


def krot(ob, f, rot):
    ob.rotation_euler = tuple(rad(a) for a in rot)
    ob.keyframe_insert("rotation_euler", frame=f)


def kval(owner, path, f, v):
    setattr(owner, path, v) if not path.startswith("[") else owner.__setitem__(path[2:-2], v)
    owner.keyframe_insert(path, frame=f)


def kvis(objs, f, visible):
    for o in objs:
        o.hide_render = o.hide_viewport = not visible
        o.keyframe_insert("hide_render", frame=f)
        o.keyframe_insert("hide_viewport", frame=f)


def constant(ob, frames=None):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad):
        for kp in fc.keyframe_points:
            if frames is None or int(round(kp.co.x)) in frames:
                kp.interpolation = "CONSTANT"


def _fcurves(ad):
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


POSE = {
    "stand": dict(sh_R=(0, 8, 0), sh_L=(0, -8, 0), el_R=(-12, 0, 0), el_L=(-12, 0, 0)),
    "clench": dict(head=(28, 0, 0), chest=(10, 0, 0), sh_R=(-6, 12, 0), sh_L=(-6, -12, 0),
                   el_R=(-28, 0, 0), el_L=(-28, 0, 0), hip_R=(0, 5, 0), hip_L=(0, -5, 0)),
    "power": dict(head=(-18, 0, 0), chest=(-12, 0, 0), sh_R=(5, 32, 0), sh_L=(5, -32, 0),
                  el_R=(-75, 0, 0), el_L=(-75, 0, 0), hip_R=(-22, 10, 0), hip_L=(-22, -10, 0),
                  kn_R=(38, 0, 0), kn_L=(38, 0, 0)),
    "scream": dict(head=(-38, 0, 0), chest=(-24, 0, 0), sh_R=(18, 55, 0), sh_L=(18, -55, 0),
                   el_R=(-25, 0, 0), el_L=(-25, 0, 0), hip_R=(-12, 14, 0), hip_L=(-12, -14, 0),
                   kn_R=(22, 0, 0), kn_L=(22, 0, 0)),
    "hero": dict(head=(-4, 0, 0), chest=(-4, 0, 0), sh_R=(0, 16, 0), sh_L=(0, -16, 0),
                 el_R=(-18, 0, 0), el_L=(-18, 0, 0), hip_R=(0, 8, 0), hip_L=(0, -8, 0)),
    "dodge_r": dict(head=(0, -18, 12), chest=(0, -16, 0), sh_R=(0, 25, 0), sh_L=(0, -10, 0),
                    el_R=(-30, 0, 0), el_L=(-40, 0, 0), hip_R=(0, 10, 0), hip_L=(0, -4, 0)),
    "dodge_l": dict(head=(0, 18, -12), chest=(0, 16, 0), sh_R=(0, 10, 0), sh_L=(0, -25, 0),
                    el_R=(-40, 0, 0), el_L=(-30, 0, 0), hip_R=(0, 4, 0), hip_L=(0, -10, 0)),
    "guard": dict(chest=(8, 0, 0), sh_R=(-70, 10, 0), sh_L=(-70, -10, 0), el_R=(-80, 0, 0),
                  el_L=(-80, 0, 0), kn_R=(25, 0, 0), kn_L=(15, 0, 0), hip_R=(-20, 0, 0)),
    "fly": dict(head=(-55, 0, 0), sh_R=(10, 14, 0), sh_L=(10, -14, 0), el_R=(-10, 0, 0),
                el_L=(-10, 0, 0), hip_R=(4, 3, 0), hip_L=(4, -3, 0), kn_R=(20, 0, 0), kn_L=(8, 0, 0)),
    "punch": dict(chest=(4, 0, -28), head=(0, 0, 18), sh_R=(-88, 0, 0), el_R=(0, 0, 0),
                  sh_L=(10, -15, 0), el_L=(-95, 0, 0), hip_R=(-25, 0, 0), kn_R=(30, 0, 0), kn_L=(10, 0, 0)),
    # Frieza
    "cross": dict(sh_R=(-35, -20, 0), sh_L=(-35, 20, 0), el_R=(-95, 0, 35), el_L=(-95, 0, -35),
                  head=(-6, 0, 0), kn_R=(25, 0, 0), kn_L=(35, 0, 0), hip_R=(-10, 0, 0)),
    "shock": dict(head=(-12, 0, 0), chest=(-14, 0, 0), sh_R=(-10, 25, 0), sh_L=(-10, -25, 0),
                  el_R=(-45, 0, 0), el_L=(-45, 0, 0), kn_R=(20, 0, 0), kn_L=(20, 0, 0)),
    "point": dict(chest=(0, 0, 12), sh_R=(-84, 6, 0), el_R=(-4, 0, 0), sh_L=(5, -12, 0),
                  el_L=(-20, 0, 0), kn_R=(15, 0, 0), kn_L=(30, 0, 0)),
    "dash": dict(chest=(25, 0, 0), sh_R=(-80, 0, 0), el_R=(-10, 0, 0), sh_L=(15, -20, 0),
                 el_L=(-30, 0, 0), hip_R=(-30, 0, 0), kn_R=(60, 0, 0), kn_L=(30, 0, 0)),
    "kick": dict(chest=(-15, 0, 0), head=(8, 0, 0), sh_R=(10, 35, 0), sh_L=(10, -35, 0), el_R=(-30, 0, 0),
                 el_L=(-30, 0, 0), hip_R=(-95, 0, 0), kn_R=(5, 0, 0), hip_L=(10, 0, 0), kn_L=(25, 0, 0)),
    "hit": dict(chest=(50, 0, 0), head=(-25, 0, 0), sh_R=(-50, 20, 0), sh_L=(-50, -20, 0),
                el_R=(-20, 0, 0), el_L=(-20, 0, 0), hip_R=(-40, 0, 0), hip_L=(-40, 0, 0),
                kn_R=(50, 0, 0), kn_L=(50, 0, 0)),
}
PARTS = ("hips", "chest", "head", "sh_R", "el_R", "sh_L", "el_L", "hip_R", "kn_R", "hip_L", "kn_L")


def pose(R, f, name, **extra):
    """Key mọi khớp theo pose; hông chỉ key khi được truyền (dành cho lộn vòng lúc bay)."""
    p = dict(POSE[name])
    p.update(extra)
    for part in PARTS:
        if part == "hips" and "hips" not in p:
            continue
        krot(R[part], f, p.get(part, (0, 0, 0)))


def root(R, f, loc, yaw=0.0, pitch=0.0, roll=0.0):
    kloc(R["root"], f, loc)
    krot(R["root"], f, (pitch, roll, yaw))      # XYZ: cúi (pitch) trước rồi mới quay (yaw)


# ───────────────────────────── choreography ─────────────────────────────
def choreograph(G, F, fx, sun, auras, storm, cracks, debris, splash):
    goku_pos = Vector((0, 0, 0))
    fr_pos = Vector((0, 9, 3.0))

    # Shot 1–5: Goku đứng trên đất (nhìn +Y về phía Frieza)
    root(G, 0, goku_pos, 180)
    pose(G, 0, "clench")
    pose(G, 110, "clench", head=(24, 0, 0))
    pose(G, 150, "power", head=(10, 0, 0))
    kloc(G["root"], 150, goku_pos + Vector((0, 0, -0.1)))
    pose(G, 235, "power")
    pose(G, 290, "power", head=(-30, 0, 0), chest=(-16, 0, 0))
    pose(G, 300, "scream")
    pose(G, 330, "scream", sh_R=(18, 60, 0), sh_L=(18, -60, 0))
    pose(G, 380, "hero")
    kloc(G["root"], 300, goku_pos + Vector((0, 0, -0.1)))
    kloc(G["root"], 380, goku_pos)
    pose(G, 509, "hero", head=(-6, 0, 4))

    # Frieza lơ lửng khoanh tay
    for f in range(0, 511, 30):
        root(F, f, fr_pos + Vector((0, 0, 0.08 * math.sin(f / 30 * math.pi))), 0)
    pose(F, 0, "cross")
    pose(F, 505, "cross")
    pose(F, 525, "shock")
    pose(F, 548, "shock", head=(-16, 0, 0))
    pose(F, 562, "point")
    pose(F, 690, "point")
    root(F, 690, fr_pos)

    # Shot 7: né Death Beam (bullet-time), rồi Frieza lao vào combo
    beams = [570, 585, 600, 622, 644, 666]
    sides = ["dodge_r", "dodge_l", "dodge_r", "dodge_l", "dodge_r", "dodge_l"]
    pose(G, 560, "hero")
    for bf, sd in zip(beams, sides):
        pose(G, bf - 6, "hero")
        pose(G, bf + 2, sd)
        pose(G, bf + 12, sd)
    root(G, 680, goku_pos, 180)
    # combo cận chiến: Frieza lao tới đấm → Goku đỡ (719) → Frieza đá → Goku né lên → Goku phản đòn
    # đấm vào thế chéo tay của Frieza (747) → Frieza bật lùi rồi bay đi (vào shot truy đuổi)
    G0 = goku_pos + Vector((0, 0, 1.4))
    root(G, 705, G0, 180); pose(G, 705, "guard")
    root(F, 700, fr_pos + Vector((0, -1, 0.2))); pose(F, 700, "dash")
    root(F, 712, Vector((0, 1.7, 1.55))); pose(F, 712, "dash")
    root(F, 718, Vector((0, 0.7, 1.45))); pose(F, 717, "punch")
    root(G, 716, G0, 180); pose(G, 716, "guard")
    root(G, 722, G0 + Vector((0, -0.14, 0.02)), 182)             # bị đẩy lùi khi đỡ
    pose(F, 724, "stand")
    root(F, 726, Vector((0, 0.72, 1.48)), 8); pose(F, 731, "kick")
    root(G, 727, G0 + Vector((0, -0.12, 0.05)), 180); pose(G, 727, "guard")
    root(G, 732, G0 + Vector((0.08, -0.08, 0.32)), 172); pose(G, 732, "dodge_r")   # bật lên né cú đá
    pose(F, 737, "stand")
    root(F, 738, Vector((0, 0.82, 1.5)), 0); pose(F, 741, "cross")
    root(G, 739, G0 + Vector((0, -0.05, 0.1)), 180); pose(G, 739, "guard")
    root(G, 746, G0 + Vector((0, 0.16, 0.08)), 176); pose(G, 744, "punch")       # phản đòn
    root(F, 747, Vector((0, 0.86, 1.5)), 0)
    root(F, 753, Vector((0.05, 1.6, 1.75)), -6); pose(F, 753, "hit")             # bật lùi
    pose(G, 756, "punch")
    root(G, 762, G0 + Vector((0, 0.05, 0.12)), 180); pose(G, 764, "guard")
    root(F, 766, Vector((0.35, 2.3, 2.0)), 20); pose(F, 766, "dash")
    pose(G, 779, "guard")
    root(G, 779, goku_pos + Vector((-0.6, 0, 1.8)), 170)
    root(F, 779, Vector((0.6, 1.3, 1.8)), 10)

    # Shot 8: truy đuổi (Goku dẫn trước, Frieza đuổi theo bắn ki blast)
    def follow(R, f, u, roll_extra=0.0, pose_name="fly"):
        p = chase_path(u)
        t = (chase_path(u + 0.005) - chase_path(u - 0.005)).normalized()   # sai phân đối xứng, không kẹp biên
        yaw = math.degrees(math.atan2(-t.x, t.y)) + 180  # mặt -Y quay theo hướng bay
        curv = (chase_path(u + 0.02) - 2 * p + chase_path(u - 0.02)).y
        root(R, f, p, yaw, 78)
        krot(R["hips"], f, (0, 0, -curv * 120 + roll_extra))   # nghiêng theo cua / lộn vòng
    krot(G["hips"], 779, (0, 0, 0))
    krot(F["hips"], 779, (0, 0, 0))
    for f in range(780, 991, 5):
        u = (f - 780) / 210
        rollG = 0.0
        for c0 in (860, 930):
            if c0 <= f <= c0 + 20:
                rollG = (f - c0) / 20 * 360
        follow(G, f, min(u * 0.95 + 0.02, 1.0), rollG)
        follow(F, f, max(u * 0.95 - 0.012, 0.0))
    pose(G, 780, "fly")
    pose(F, 780, "fly", sh_R=(-150, 0, 0))
    for bf, _ in BLASTS:
        pose(F, bf - 14, "fly", sh_R=(-160, 0, 0), el_R=(0, 0, 0))
        pose(F, bf - 4, "fly", sh_R=(-150, 0, 0))
    pose(G, 989, "fly")
    pose(F, 989, "fly")

    # Shot 9: Goku biến mất → hiện sau lưng Frieza → đấm (hit-stop 1030–1045)
    end = chase_path(1.0)
    fr_end = end + Vector((0, 0, 0.5))
    root(F, 992, fr_end, 90)
    pose(F, 992, "shock")
    root(G, 992, end + Vector((4, 0, 0.6)), -90)
    pose(G, 992, "hero")
    body = [o for o in bpy.data.objects if o.name.startswith("goku_") and o.type in {"MESH", "FONT"}
            and o not in G["base"] + G["mouth_open"] + G["eyes_shut"] + G["eyes_blink"] + G["eyes_angry"] + G["smirk"]
            + G["eyes_fierce"] + G["grit"] + G["brows_angry"] + G["blush"]]
    kvis(body, 1000, True)
    kvis(body, 1001, False)
    kvis(body, 1012, True)
    root(F, 1012, fr_end, 90)
    root(G, 1012, fr_end + Vector((-0.8, 0, 0.02 + LEG_DROP)), 90)       # sát sau lưng Frieza, nhìn +X
    pose(G, 1012, "hero")
    root(G, 1026, fr_end + Vector((-0.78, 0, 0.02 + LEG_DROP)), 90)
    root(G, 1030, fr_end + Vector((-0.5, 0, LEG_DROP)), 90)          # lao tới, nắm đấm chạm mặt Frieza
    root(F, 1024, fr_end, 270)                                 # Frieza quay lại
    pose(F, 1024, "shock")
    pose(G, 1024, "guard")
    pose(G, 1030, "punch")
    pose(G, 1045, "punch")
    pose(F, 1030, "hit")
    pose(F, 1045, "hit")
    root(F, 1045, fr_end + Vector((0.35, 0, 0)), 270)
    root(F, 1109, fr_end + Vector((40, -6, -4)), 270, -30)
    pose(G, 1070, "hero")
    root(G, 1045, fr_end + Vector((-0.5, 0, LEG_DROP)), 90)
    root(G, 1109, fr_end + Vector((-0.7, 0, 0.2)), 90)

    # Shot 10: Frieza rơi xuống biển, Goku lơ lửng
    sp_pos = fr_end + Vector((70, -10, 0))
    sp_pos.z = -0.7
    root(F, 1150, sp_pos + Vector((0, 0, 0.5)), 270, -70)
    kvis([o for o in bpy.data.objects if o.name.startswith("fr_")], 1150, True)
    kvis([o for o in bpy.data.objects if o.name.startswith("fr_")], 1151, False)
    splash.location = sp_pos
    splash.scale = (0.01, 0.01, 0.01)
    splash.keyframe_insert("scale", frame=1150)
    splash.scale = (1, 1, 1)
    splash.keyframe_insert("scale", frame=1162)
    splash.scale = (1.4, 1.4, 0.2)
    splash.keyframe_insert("scale", frame=1199)
    for f in range(1110, 1200, 15):
        root(G, f, fr_end + Vector((-1.2, 0, 0.2 + 0.06 * math.sin(f / 15))), 90 + (f - 1110) * 0.4)
    pose(G, 1199, "hero", head=(-8, 0, 0))

    # Đuôi Frieza lắc nhẹ suốt clip
    for f in range(0, 1200, 20):
        for i, seg in enumerate(F["tail"]):
            krot(seg, f, (-12 - 6 * math.sin(f / 40 + i * 0.7), 0, 14 * math.sin(f / 33 + i * 0.5)))

    # Biến hình: chớp tóc/mắt 3 nhịp rồi chuyển hẳn
    kvis(G["ssj"], 0, False)
    kvis(G["base"], 0, True)
    for f0 in (248, 266, 284):
        kvis(G["ssj"], f0, True); kvis(G["base"], f0, False)
        kvis(G["ssj"], f0 + 4, False); kvis(G["base"], f0 + 4, True)
    # miệng: há khi thét (biến hình) và khi tung cú đấm
    kvis(G["mouth_open"], 0, False)
    kvis(G["mouth"], 0, True)   # key đầu tiên của miệng là "ẩn" ở 292 → thiếu key này thì Goku mất miệng suốt 0–292
    for f0, f1 in ((292, 338), (1026, 1048)):
        kvis(G["mouth_open"], f0, True); kvis(G["mouth"], f0, False)
        kvis(G["mouth_open"], f1, False); kvis(G["mouth"], f1, True)
    kvis(G["ssj"], 300, True)
    kvis(G["base"], 300, False)
    hs = G["hair_ssj"]
    for f in (240, 296):                       # 3 nhịp chớp SSJ trước đó: tóc gần đủ cỡ, không lộ đầu trọc
        hs.scale = (0.95, 0.95, 0.95); hs.keyframe_insert("scale", frame=f)
    hs.scale = (0.6, 0.6, 0.55); hs.keyframe_insert("scale", frame=300)
    hs.scale = (1.08, 1.08, 1.12); hs.keyframe_insert("scale", frame=306)
    hs.scale = (1, 1, 1); hs.keyframe_insert("scale", frame=316)
    glow = M["hair_ssj"].node_tree.nodes["glow"].outputs[0]
    energy = M["hair_ssj"].node_tree.nodes["energy"].outputs[0]
    for f, gv, ev in ((299, 0.2, 0.15), (300, 2.2, 1.0), (318, 0.7, 0.6), (334, 0.3, 0.3), (390, 0.05, 0.1)):   # tóc vàng nhạt: glow 3.0 làm trắng bệch cả khối lúc thét; energy thấp để bloom trong app không tẩy trắng tóc
        glow.default_value, energy.default_value = gv, ev
        glow.keyframe_insert("default_value", frame=f)
        energy.keyframe_insert("default_value", frame=f)

    # lơ lửng: hông nhấp nhô nhẹ khi bay tại chỗ (Frieza chờ trên trời, Goku cuối phim)
    for R_, (f0, f1), h0 in ((F, (0, 700), FRIEZA_DIM["hips"]), (G, (1110, 1199), GOKU_DIM["hips"])):
        kloc(R_["hips"], max(f0 - 6, 0), Vector((0, 0, h0)))      # trước đó giữ đúng độ cao gốc (chân không lún)
        for f in range(f0, f1 + 1, 6):
            kloc(R_["hips"], f, Vector((0, 0, h0 + 0.035 * math.sin(math.tau * (f - f0) / 96))))

    # ký hiệu anime: Frieza nổi gân 💢 khi thấy Goku biến hình (cận mặt + qua vai), toát mồ hôi khi mất dấu Goku; Goku cười nhếch
    an, sw = F["anger"], F["sweat"]
    kvis([an, sw], 0, False)
    kvis([an], 530, True); kvis([an], 602, False)
    kvis([sw], 996, True); kvis([sw], 1030, False)
    kloc(sw, 996, sw.location.copy())
    kloc(sw, 1028, sw.location + Vector((0, 0, -0.01)))         # giọt mồ hôi trượt xuống
    kvis(F["laugh"], 0, False)
    kvis(F["laugh"], 498, True); kvis(F["mouth"], 498, False)
    kvis(F["laugh"], 524, False); kvis(F["mouth"], 524, True)
    kvis(G["smirk"], 0, False)
    for f0, f1 in ((395, 560), (668, 700)):
        kvis(G["smirk"], f0, True); kvis(G["mouth"], f0, False)
        kvis(G["smirk"], f1, False); kvis(G["mouth"], f1, True)

    # đầu ngón Frieza sáng hồng, phồng lên vài frame trước mỗi phát Death Beam / ki blast
    ch = F["charge"]
    ch.scale = (0, 0, 0); ch.keyframe_insert("scale", frame=0)
    for fire in beams + [bf - 13 for bf, _ in BLASTS]:
        for f, k in ((fire - 10, 0.0), (fire - 2, 1.0), (fire, 1.5), (fire + 3, 0.0)):
            ch.scale = (k, k, k); ch.keyframe_insert("scale", frame=f)

    # Frieza: mắt mở to hoảng hốt khi mất dấu Goku tới lúc trúng đòn, há miệng khi bị đấm
    kvis(F["eyes_shock"], 0, False); kvis(F["mouth_open"], 0, False); kvis(F["eyes"], 0, True); kvis(F["mouth"], 0, True)
    kvis(F["eyes_shock"], 1000, True); kvis(F["eyes"], 1000, False)
    kvis(F["mouth_open"], 1000, True); kvis(F["mouth"], 1000, False)

    # giận dần trước khi hét (236→292): mắt cụp mi; vẫn nhường chỗ cho 3 nhịp chớp SSJ
    kvis(G["eyes_angry"], 0, False)
    kvis(G["eyes_angry"], 236, True); kvis(G["eyes_base"], 236, False)
    for f0 in (248, 266, 284):
        kvis(G["eyes_angry"], f0, False)
        kvis(G["eyes_angry"], f0 + 4, True); kvis(G["eyes_base"], f0 + 4, False)
    kvis(G["eyes_angry"], 292, False)

    # hét lúc biến hình: mắt nhắm tịt "> <" (chèn sau các key bật/tắt SSJ để đè lên)
    kvis(G["eyes_shut"], 0, False)
    kvis(G["eyes_shut"], 292, True); kvis(G["eyes_base"] + G["eyes_ssj"], 292, False)
    kvis(G["eyes_ssj"], 300, False)
    kvis(G["eyes_shut"], 336, False); kvis(G["eyes_ssj"], 336, True)

    # chớp mắt (4 frame), tránh các đoạn đang đổi nét mặt
    kvis(G["eyes_blink"] + F["eyes_blink"], 0, False)
    for f0, eyes in ((90, G["eyes_base"]), (205, G["eyes_base"]), (445, G["eyes_ssj"]), (640, G["eyes_ssj"]), (1140, G["eyes_ssj"])):
        kvis(G["eyes_blink"], f0, True); kvis(eyes, f0, False)
        kvis(G["eyes_blink"], f0 + 4, False); kvis(eyes, f0 + 4, True)
    for f0, eyes in ((140, F["eyes"]), (470, F["eyes"]), (590, F["eyes_angry"])):
        kvis(F["eyes_blink"], f0, True); kvis(eyes, f0, False)
        kvis(F["eyes_blink"], f0 + 4, False); kvis(eyes, f0 + 4, True)

    # ── nét mặt theo nhịp truyện (sau mọi key ở trên để đè lên cùng frame) ──
    # Goku: mày đen cau lại khi giận dần (236→300), vẫn nhường 3 nhịp chớp SSJ; má hồng chỉ lúc còn hiền (0→236)
    brA, brB = G["brows_angry"], [o for o in G["base"] if o.name.startswith("goku_brow_")]
    kvis(brA, 0, False); kvis(brA, 236, True); kvis(brB, 236, False)
    for f0 in (248, 266, 284):
        kvis(brA, f0, False); kvis(brA, f0 + 4, True); kvis(brB, f0 + 4, False)
    kvis(brA, 300, False)
    kvis(G["blush"], 0, True); kvis(G["blush"], 236, False)
    # Goku đánh combo (705→780) và cú đấm sau lưng (1012→1048): nghiến răng, hét khi tung đòn, mắt SSJ hẹp lại
    kvis(G["grit"] + G["eyes_fierce"], 0, False)
    for f0, f1 in ((705, 744), (762, 780), (1012, 1026)):
        kvis(G["grit"], f0, True); kvis(G["mouth"], f0, False)
        kvis(G["grit"], f1, False)
    kvis(G["mouth"], 780, True)                 # 744 và 1026 nối thẳng sang miệng hét (key bên dưới / ở trên)
    kvis(G["grit"], 236, True); kvis(G["mouth"], 236, False)   # gồng Ki: nghiến răng đi cùng mày giận (trước đó vẫn cười)
    kvis(G["grit"], 292, False)                 # 292 nối thẳng sang miệng thét biến hình
    for f0, f1 in ((744, 762),):
        kvis(G["mouth_open"], f0, True); kvis(G["mouth"], f0, False)
        kvis(G["mouth_open"], f1, False)
    for f0, f1 in ((742, 764), (1026, 1048)):
        kvis(G["eyes_fierce"], f0, True); kvis(G["eyes_ssj"], f0, False)
        kvis(G["eyes_fierce"], f1, False); kvis(G["eyes_ssj"], f1, True)
    # cuối phim: Goku SSJ cười nhếch tự tin
    kvis(G["smirk"], 1118, True); kvis(G["mouth"], 1118, False)
    # Frieza: cười "ho ho ho" nhắm mắt khinh khỉnh; khựng lại khi Goku biến hình rồi giận (nghiến răng) tới hết loạt Death Beam
    kvis(F["eyes_blink"], 501, True); kvis(F["eyes"], 501, False)
    kvis(F["eyes_blink"], 521, False)
    kvis(F["eyes_angry"] + F["eyes_hit"] + F["snarl"] + F["pain"], 0, False)
    kvis(F["eyes_shock"], 521, True)
    kvis(F["mouth_open"], 524, True); kvis(F["mouth"], 524, False)
    kvis(F["eyes_shock"], 532, False); kvis(F["eyes_angry"], 532, True)
    kvis(F["mouth_open"], 532, False); kvis(F["snarl"], 532, True)
    kvis(F["snarl"], 566, False); kvis(F["mouth"], 566, True)
    kvis(F["eyes_angry"], 700, False); kvis(F["eyes"], 700, True)
    # Frieza trúng đòn (1030): nhắm nghiến, miệng méo; giữ tới lúc rơi xuống biển
    kvis(F["eyes_hit"], 1030, True); kvis(F["eyes_shock"], 1030, False)
    kvis(F["pain"], 1030, True); kvis(F["mouth_open"], 1030, False)
    # shot 10 bật mọi fr_* ở 1150 (frame rơi xuống biển): chỉ giữ đúng nét trúng đòn, các nét khác vẫn ẩn
    kvis(F["eyes"] + F["eyes_blink"] + F["eyes_shock"] + F["eyes_angry"] + F["mouth"] + F["laugh"] + F["mouth_open"]
         + F["snarl"], 1150, False)

    # tóc đen rung dần lên khi gồng khí (140→300), dựng nhẹ lên trước lúc biến hình
    hb = [o for o in G["base"] if o.name == "goku_hair_base"][0]
    rng0 = random.Random(5)
    for f in range(130, 301, 3):
        k = max(0.0, (f - 130) / 170)
        amp = 0.6 + 3.4 * k * k
        hb.rotation_euler = (rad(rng0.uniform(-amp, amp) - 4 * k), rad(rng0.uniform(-amp, amp)), rad(rng0.uniform(-amp, amp) * 0.5))
        hb.keyframe_insert("rotation_euler", frame=f)
        hb.scale = (1 + 0.03 * k, 1 + 0.03 * k, 1 + 0.06 * k)
        hb.keyframe_insert("scale", frame=f)

    # tóc rung trong luồng khí: mạnh lúc vừa biến hình, nhẹ dần nhưng không tắt hẳn
    rng = random.Random(11)
    for f in range(300, 1200, 3):
        amp = 3.2 if f < 420 else (1.6 if f < 780 else 1.0)
        back = -12.0 if 784 <= f <= 986 else 0.0          # bay: gió hất tóc ra sau
        hs.rotation_euler = (rad(rng.uniform(-amp, amp) + back), rad(rng.uniform(-amp, amp)), rad(rng.uniform(-amp, amp) * 0.5))
        hs.keyframe_insert("rotation_euler", frame=f)

    # Vết nứt lan + debris bay lên rồi văng ra
    for piv, length in cracks:
        piv.scale = (1, 0.001, 1); piv.keyframe_insert("scale", frame=140)
        piv.scale = (1, length * 0.45, 1); piv.keyframe_insert("scale", frame=239)
        piv.scale = (1.0, length, 1); piv.keyframe_insert("scale", frame=310)
    # v25: khe nứt rực sáng khi gồng, loé mạnh lúc nổ biến hình rồi nguội dần thành khe tối ánh than hồng (không sáng mãi)
    cn = M["crack"].node_tree.nodes
    cem = next(n for n in cn if n.type == "EMISSION" and not n.inputs["Strength"].is_linked)
    for f, col, st, en in ((300, "#FFD45C", 1.2, 0.6), (330, "#FFF0A8", 1.6, 0.95), (420, "#F0A040", 1.0, 0.3),
                           (560, "#4E2614", 0.8, 0.0)):
        cem.inputs["Color"].default_value = hexc(col); cem.inputs["Color"].keyframe_insert("default_value", frame=f)
        cem.inputs["Strength"].default_value = st; cem.inputs["Strength"].keyframe_insert("default_value", frame=f)
        cn["energy"].outputs[0].default_value = en; cn["energy"].outputs[0].keyframe_insert("default_value", frame=f)
    # v25: khí nhấc đá lơ lửng, vụ nổ biến hình (frame 296) hất văng → bay theo đường đạn (g = 9.8 m/s², 60 fps), chạm đất
    # nảy vài lần mất dần năng lượng rồi nằm yên trên cỏ (trước: key tay, đá cắm xuống dưới mặt đất ở frame 420)
    rng_d = random.Random(909)
    rng_h = random.Random(919)
    g_acc, T_BURST = 9.8 / 60.0 ** 2, 296
    dust_m = toon("dust", "#DCE3C8", "#A9B694", threshold=0.35)
    for d, a, r in debris:
        rr = max(d.dimensions) * 0.42
        dirv = Vector((math.cos(a), math.sin(a), 0))
        p0 = Vector((math.cos(a) * r, math.sin(a) * r, rr))
        lift = random.uniform(0.6, 2.8)
        for _ in range(4):                          # giữ đúng số lần gọi random cũ (5/hòn) → không xáo các vật ngẫu nhiên phía sau
            random.random()
        kloc(d, 120, p0)
        krot(d, 120, (0, 0, 0))
        hover = p0 + Vector((0, 0, lift))
        kloc(d, 290, hover)
        rot = Vector((rng_d.uniform(-30, 30), rng_d.uniform(-30, 30), rng_d.uniform(-50, 50)))
        krot(d, 290, rot)
        # v30 đá bị khí nâng không bay êm: rung lắc + nhấp nhô trong trường khí, càng gần lúc nổ càng dữ (RNG riêng)
        ph = rng_h.uniform(0, math.tau)
        for ff in range(132, 290, 6):
            t = (ff - 120) / 170
            e = t * t * (3 - 2 * t)
            amp = 0.015 + 0.05 * t * t
            kloc(d, ff, p0.lerp(hover, e) + Vector((rng_h.uniform(-1, 1) * amp * 0.6, rng_h.uniform(-1, 1) * amp * 0.6,
                                                     amp * math.sin(ff * 0.35 + ph))))
            krot(d, ff, tuple(rot * e + Vector((rng_h.uniform(-1, 1), rng_h.uniform(-1, 1), rng_h.uniform(-1, 1))) * 6 * t))
        kloc(d, T_BURST, hover + Vector((0, 0, 0.04)))
        krot(d, T_BURST, rot)
        pos = hover + Vector((0, 0, 0.04))
        vel = dirv * rng_d.uniform(6.0, 14.0) / 60 + Vector((0, 0, rng_d.uniform(2.5, 7.5) / 60))
        w = Vector((rng_d.uniform(-22, 22), rng_d.uniform(-22, 22), rng_d.uniform(-12, 12)))
        f = T_BURST
        land = None
        while f < T_BURST + 170:
            for _ in range(2):
                vel.z -= g_acc
                pos += vel
                rot += w
                if pos.z < rr:                      # chạm đất: nảy lại (hệ số hồi phục 0.35), ma sát cỏ hãm trượt + xoay
                    if land is None and -vel.z > 0.03:   # lần chạm đất đầu: bụi đất bung lên
                        land = (f, Vector((pos.x, pos.y, 0.02)), -vel.z)
                    pos.z = rr
                    vel.z = -vel.z * 0.35
                    vel.x *= 0.55; vel.y *= 0.55
                    w *= 0.45
                    if vel.z < 0.012:
                        vel.z = 0.0
                if pos.z <= rr + 1e-4 and vel.z == 0.0:
                    vel.x *= 0.8; vel.y *= 0.8; w *= 0.6
            f += 2
            kloc(d, f, pos.copy())
            krot(d, f, tuple(rot))
            if pos.z <= rr + 1e-4 and vel.length < 0.002:
                break
        for fc in _fcurves(d.animation_data):
            for kp in fc.keyframe_points:
                if kp.co.x >= T_BURST:
                    kp.interpolation = "LINEAR"
        if land:
            lf, lp, vz = land
            scene.timeline_markers.new("sfx:thud", frame=int(lf))   # synth_audio: tiếng đá rơi bịch đúng frame chạm đất
            bm = bmesh.new()
            for _ in range(4):                      # cụm 4 cục bụi tròn lệch nhau
                tmp = bmesh.new()
                bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=rng_d.uniform(0.6, 1.0))
                off = Vector((rng_d.uniform(-0.7, 0.7), rng_d.uniform(-0.7, 0.7), rng_d.uniform(0.0, 0.5)))
                for v in tmp.verts:
                    v.co += off
                _merge(bm, tmp)
            pf = _obj(f"dust_{d.name}", bm, dust_m, d.users_collection[0], outline=0.01)
            pf.visible_shadow = False
            pf.location = lp
            sz = min(0.45, rr * (1.2 + 9 * vz))
            kvis([pf], 0, False); kvis([pf], lf, True)
            for o, k_, z in ((0, 0.15, 0.0), (8, 0.8, 0.08), (22, 1.0, 0.18), (30, 0.55, 0.24)):
                pf.scale = (sz * k_, sz * k_, sz * k_ * 0.7); pf.keyframe_insert("scale", frame=lf + o)
                pf.location = lp + Vector((0, 0, z)); pf.keyframe_insert("location", frame=lf + o)
            kvis([pf], lf + 31, False)

    # v28 vòng bụi sóng xung kích: nổ biến hình hất bụi mặt đất thành vòng cuộn toả ra ngoài, chậm dần vì lực cản
    # không khí (r = r0 + R·(1 − e^(−t/τ))), bốc lên nhẹ rồi tan; RNG riêng để không xô lệch chuỗi random chung
    rng_b = random.Random(4242)
    coll = next((o.users_collection[0] for o in bpy.data.objects if o.name.startswith("dust_")), scene.collection)
    # bụi phẳng 2 tông theo góc nhìn (lõi sáng, mép sẫm), không viền; tan bằng cách vỡ vụn theo nhiễu khi alpha màu
    # object giảm (toon có viền trước trông như tảng đá xám)
    bd_m = bpy.data.materials.new("burst_dust")
    bd_m.use_nodes = True
    N, L = bd_m.node_tree.nodes, bd_m.node_tree.links
    for n_ in list(N):
        N.remove(n_)
    o_ = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    rp = N.new("ShaderNodeValToRGB"); rp.color_ramp.interpolation = "CONSTANT"
    rp.color_ramp.elements[0].color = hexc("#E6E4CC"); rp.color_ramp.elements[1].position = 0.55
    rp.color_ramp.elements[1].color = hexc("#BFC29F")
    L.new(lw.outputs["Facing"], rp.inputs["Fac"]); L.new(rp.outputs["Color"], em.inputs["Color"])
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    oi = N.new("ShaderNodeObjectInfo")
    th = N.new("ShaderNodeMath"); th.operation = "MULTIPLY_ADD"; th.inputs[1].default_value, th.inputs[2].default_value = -0.75, 0.95
    L.new(oi.outputs["Alpha"], th.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"
    L.new(nz.outputs["Fac"], gt.inputs[0]); L.new(th.outputs[0], gt.inputs[1])
    L.new(gt.outputs[0], mx.inputs["Fac"]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], o_.inputs["Surface"])
    NB = 18
    for i in range(NB):
        a = math.tau * (i + rng_b.uniform(-0.3, 0.3)) / NB
        out = Vector((math.cos(a), math.sin(a), 0))
        bm = bmesh.new()
        for _ in range(4):
            tmp = bmesh.new()
            bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=rng_b.uniform(0.55, 0.9))
            off = Vector((rng_b.uniform(-0.8, 0.8), rng_b.uniform(-0.8, 0.8), rng_b.uniform(0.0, 0.45)))
            for v in tmp.verts:
                v.co += off
            _merge(bm, tmp)
        pf = _obj(f"burst_dust_{i}", bm, bd_m, coll, outline=0)
        pf.visible_shadow = False
        R_, tau, sz = rng_b.uniform(5.5, 7.5), rng_b.uniform(13, 18), rng_b.uniform(0.4, 0.6)
        kvis([pf], 0, False); kvis([pf], T_BURST + 1, True)
        for t in (1, 4, 8, 14, 22, 32, 46, 62, 80):
            r = 0.9 + R_ * (1 - math.exp(-t / tau))
            k_ = min(1.0, t / 14) * (1.0 if t < 46 else max(0.0, 1 - (t - 46) / 34))   # nở ra rồi tan
            pf.location = out * r + Vector((0, 0, 0.1 + 0.55 * (1 - math.exp(-t / 30))))
            pf.keyframe_insert("location", frame=T_BURST + t)
            pf.scale = (sz * (0.3 + 0.9 * k_) * (1 + t / 60),) * 2 + (sz * (0.3 + 0.9 * k_) * (0.9 + t / 80),)
            if t == 80:
                pf.scale = (0.001, 0.001, 0.001)
            pf.keyframe_insert("scale", frame=T_BURST + t)
            pf.color = (1, 1, 1, 1.0 if t < 22 else max(0.0, 1 - (t - 22) / 58))
            pf.keyframe_insert("color", index=3, frame=T_BURST + t)
        kvis([pf], T_BURST + 81, False)

    # Trời chuyển giông, mặt trời dịu
    s = storm.inputs[0]
    for f, v in ((0, 0.25), (240, 1.0)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    for f, v in ((0, 3.4), (240, 2.3), (300, 3.0)):
        sun.energy = v
        sun.keyframe_insert("energy", frame=f)
    gm = bpy.data.materials.get("ground_tex")
    if gm:
        dv = gm.node_tree.nodes["dim"].outputs[0]
        for f, v in ((0, 1.0), (240, 0.8), (300, 0.86)):
            dv.default_value = v
            dv.keyframe_insert("default_value", frame=f)

    # ── Track FX (đọc bởi bake_timeline.py) ──
    T = {k: [] for k in ("aura", "flash", "shake", "punch", "speedlines", "impact", "grade",
                         "lightning", "shock_r", "shock_k", "title", "timescale", "beam", "blast")}

    def key(track, f, v):
        T[track].append((f, v))

    key("aura", 0, 0); key("aura", 299, 0); key("aura", 300, 0.2); key("aura", 306, 1.4); key("aura", 336, 1.0)
    key("aura", 509, 1.0); key("aura", 520, 0.8); key("aura", 779, 0.8); key("aura", 790, 0.7)
    key("aura", 989, 0.7); key("aura", 1028, 1.2); key("aura", 1060, 0.9); key("aura", 1199, 0.5)
    for f0 in (248, 266, 284):
        key("aura", f0, 0.0); key("aura", f0 + 1, 0.45); key("aura", f0 + 4, 0.0)
    key("flash", 0, 0)
    for f0 in (248, 266, 284):
        key("flash", f0 - 1, 0); key("flash", f0, 0.55); key("flash", f0 + 3, 0)
    key("flash", 299, 0); key("flash", 303, 1.0); key("flash", 316, 0)
    for bf, _ in BLASTS:
        key("flash", bf - 1, 0); key("flash", bf, 0.35); key("flash", bf + 8, 0)
    key("flash", 1029, 0); key("flash", 1032, 1.0); key("flash", 1040, 0)
    key("flash", 1170, 0); key("flash", 1174, 0.5); key("flash", 1185, 0)
    key("shake", 0, 0); key("shake", 120, 0); key("shake", 239, 0.4); key("shake", 240, 0.15)
    key("shake", 299, 0.2); key("shake", 300, 1.0); key("shake", 336, 0.0)
    for bf, _ in BLASTS:
        key("shake", bf - 1, 0); key("shake", bf, 0.6); key("shake", bf + 20, 0)
    key("shake", 718, 0); key("shake", 719, 0.35); key("shake", 730, 0)
    key("shake", 746, 0); key("shake", 747, 0.35); key("shake", 758, 0)
    key("shake", 1029, 0); key("shake", 1030, 1.0); key("shake", 1066, 0)
    key("punch", 0, 0)
    for f0 in (248, 266, 284):
        key("punch", f0 - 1, 0); key("punch", f0, 0.05); key("punch", f0 + 8, 0)
    for bf in beams:
        key("punch", bf - 1, 0); key("punch", bf, 0.04); key("punch", bf + 8, 0)
    for f0, amt in ((719, 0.05), (747, 0.08)):           # đòn chạm trong combo
        key("punch", f0 - 1, 0); key("punch", f0, amt); key("punch", f0 + 8, 0)
    key("punch", 1029, 0); key("punch", 1030, 0.12); key("punch", 1045, 0.12); key("punch", 1060, 0)
    key("speedlines", 0, 0); key("speedlines", 299, 0); key("speedlines", 300, 1); key("speedlines", 335, 0)
    key("speedlines", 779, 0); key("speedlines", 790, 0.7); key("speedlines", 980, 0.7); key("speedlines", 990, 0)
    key("speedlines", 1029, 0); key("speedlines", 1030, 1); key("speedlines", 1055, 0)
    key("impact", 0, 0); key("impact", 300, 1); key("impact", 303, 0); key("impact", 747, 1); key("impact", 748, 0)
    key("impact", 1030, 1); key("impact", 1032, 0)
    key("grade", 0, 0); key("grade", 300, 0); key("grade", 330, 1)
    key("lightning", 0, 0.5); key("lightning", 239, 0.7); key("lightning", 240, 1.0); key("lightning", 330, 0.3)
    key("lightning", 779, 0.3); key("lightning", 780, 0.15)
    key("shock_r", 0, 0); key("shock_r", 300, 0); key("shock_r", 345, 1500); key("shock_r", 1030, 0); key("shock_r", 1060, 1100)
    key("shock_k", 0, 0); key("shock_k", 299, 0); key("shock_k", 300, 1); key("shock_k", 345, 0)
    key("shock_k", 1029, 0); key("shock_k", 1030, 1); key("shock_k", 1060, 0)
    key("title", 0, 0); key("title", 1150, 0); key("title", 1176, 1)
    key("timescale", 0, 1); key("timescale", 615, 1); key("timescale", 635, 0.25); key("timescale", 675, 0.25); key("timescale", 690, 1)
    key("beam", 0, 0)
    for bf in beams:
        dur = 14 if bf < 600 else 22
        key("beam", bf - 1, 0); key("beam", bf, 1); key("beam", bf + dur, 1); key("beam", bf + dur + 4, 0)
    key("blast", 0, 0)
    for bf, _ in BLASTS:
        key("blast", bf - 13, 0); key("blast", bf, 1); key("blast", bf + 1, 0)

    step_tracks = {"impact"}
    for name, ks in T.items():
        fx[name] = float(ks[0][1])
        for f, v in sorted(ks):
            fx[name] = float(v)
            fx.keyframe_insert(f'["{name}"]', frame=f)
    for fc in _fcurves(fx.animation_data):
        name = fc.data_path[2:-2]
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT" if name in step_tracks else "LINEAR"

    # Đèn aura bám track aura
    for d in auras:
        for f, v in sorted(T["aura"]):
            d.energy = 55 * v
            d.keyframe_insert("energy", frame=f)

    # Đích của Death Beam & ki blast
    bt = bpy.data.objects["BEAM_TARGET"]
    offs = [(0.35, 0.1), (-0.32, 0.05), (0.3, 0.12), (-0.3, 0.0), (0.28, 0.15), (-0.33, 0.08)]
    for bf, (ox, oz) in zip(beams, offs):
        kloc(bt, bf - 1, Vector((ox, -0.3, 1.25 + oz)))
    constant(bt)
    # ki blast trượt, nổ sát bên Goku (máy truy đuổi nhìn lùi nên điểm nổ phải ở cạnh/sau Goku mới vào khung)
    bp = bpy.data.objects["BLAST_POINT"]
    for k, (bf, _) in enumerate(BLASTS):
        g = (bf - 780) / 210 * 0.95 + 0.02
        tang = (chase_path(min(g + 0.01, 1)) - chase_path(max(g - 0.01, 0))).normalized()
        side = Vector((-tang.y, tang.x, 0)).normalized() * (1 if k % 2 == 0 else -1)
        kloc(bp, bf - 13, chase_path(max(g - 0.02, 0)) + side * 0.7 + Vector((0, 0, -0.3)))
    constant(bp)

    # Marker: haptic + cut
    def mk(f, name):
        scene.timeline_markers.new(name, frame=f)
    f, gap = 125.0, 8.4
    while f < 238:
        mk(int(f), "haptic:light")
        f += gap
        gap = max(3.0, gap * 0.9)
    for f0 in (248, 266, 284):
        mk(f0, "haptic:rigid")
    mk(300, "haptic:heavy"); mk(305, "haptic:heavy")
    for bf in beams:
        mk(bf, "haptic:light")
    for bf in beams[2:]:
        mk(bf + 8, "haptic:soft")
    mk(719, "haptic:rigid"); mk(747, "haptic:rigid")
    for bf, _ in BLASTS:
        mk(bf, "haptic:medium")
    for f0 in (1030, 1034, 1038):
        mk(f0, "haptic:heavy")
    mk(1176, "haptic:success")
    for f0 in CUTS:
        mk(f0, "cut")


# ───────────────────────────── cameras ─────────────────────────────
SHOTS = [0, 120, 240, 300, 390, 510, 600, 780, 990, 1110, 1200]
CUTS = [120, 240, 300, 390, 510, 550, 600, 690, 780, 990, 1012, 1030, 1110]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def orbit(center, radius, ang, height):
    return center + Vector((math.cos(rad(ang)) * radius, math.sin(rad(ang)) * radius, height))


def cam_for(f, A):
    """(eye, target, focal mm, roll độ) cho frame f. A: vị trí world của các anchor."""
    gc, gh, fh, fc = A["gc"], A["gh"], A["fh"], A["fc"]
    if f < 120:                                   # 1. drone dolly-in
        t = ease(f / 119)
        eye = gc + lerp(Vector((-14, -20, 17)), Vector((-3.0, -5.2, 2.0)), t)
        tgt = lerp((gc + fc) / 2, gc + Vector((0, 2.5, 0.4)), t)
        return eye, tgt, 24, 0
    if f < 240:                                   # 2. low-angle orbit quanh Goku
        t = (f - 120) / 119
        return orbit(gc, 2.2, lerp(70, 110, t), -0.55), gc + Vector((0, 0, 0.2)), 32, lerp(-4, 4, t)
    if f < 300:                                   # 3. cận mắt, 4 frame cuối crash zoom
        t = (f - 240) / 59
        # crash zoom dừng ở cỡ mặt vẫn thấy đủ hai mắt + miệng (trước đây lao tới 0.7 m: mặt thành mảng da phẳng)
        d = lerp(1.6, 1.42, t) if f < 296 else lerp(1.42, 1.22, (f - 295) / 4)
        fwd = (A["gface"] - gh).normalized()
        return gh + fwd * d + Vector((0.02, 0, 0.0)), gh + Vector((0, 0, -0.03)), 85, 0
    if f < 390:                                   # 4. crash zoom-out
        t = ease((f - 300) / 8)
        t2 = ease((f - 308) / 81)
        d = lerp(0.8, 3.3, t) + 1.1 * t2
        focal = lerp(135, 28, t)
        # máy thấp kiểu hero nhưng luôn ở trên mặt cỏ (~0.3 m): trước đây z = ngực − 0.7 ≈ −0.02 → máy nằm dưới đất,
        # nửa giữa khung là mặt dưới khối đất (dải xanh đục) và chỉ thấy đế giày Goku
        return gc + Vector((-0.35 * d, 0.92 * d, -0.13 * t - 0.25)), gc + Vector((0, 0, 0.3 * t)), focal, lerp(0, -6, t)
    if f < 510:                                   # 5. orbit 180° → hero low-angle
        t = ease((f - 390) / 119)
        return orbit(gc, lerp(3.3, 2.6, t), lerp(-60, 115, t), lerp(0.45, -0.5, t)), gc + Vector((0, 0, 0.25)), lerp(35, 28, t), 0
    if f < 550:                                   # 6a. dolly zoom vào mặt Frieza
        t = ease((f - 510) / 39)
        d = lerp(1.1, 4.4, t)
        return fh + Vector((0.05, -d, 0.02)), fh, 30 * d / 1.1, 0
    if f < 600:                                   # 6b. qua vai Frieza nhìn Goku
        t = (f - 550) / 49
        return fh + Vector((lerp(0.24, 0.2, t), 0.55, 0.07)), gc + Vector((0, 0, 0.25)), lerp(62, 68, t), 0   # tele nén khoảng cách
    if f < 690:                                   # 7a. bullet-time orbit 90°
        t = ease((f - 600) / 89)
        return orbit(gh, 1.8, lerp(35, 125, t), 0.12), gh + Vector((0, 0, -0.12)), 35, 0
    if f < 780:                                   # 7b. Frieza lao tới (qua vai Goku), rồi combo ngang, kết bằng whip pan
        mid = (gc + fc) / 2
        t = (f - 690) / 89
        eye = mid + Vector((lerp(3.6, 3.0, t), lerp(-1.1, 0.4, t), 0.3))
        tgt = mid
        k = ease((f - 708) / 14)
        eye = lerp(gc + Vector((0.75, -2.3, 0.35)), eye, k)
        tgt = lerp(gc + (fc - gc) * 0.3 + Vector((0, 0, 0.1)), tgt, k)
        if f >= 768:
            w = ease((f - 768) / 11)
            tgt = mid + Vector((0, -w * 6.0, w * 1.5))
        return eye, tgt, 32, 0
    if f < 990:                                   # 8. bám đuôi truy đuổi
        u = (f - 780) / 210
        p = chase_path(max(u * 0.95 - 0.035, 0.0))
        tang = (chase_path(min(u + 0.01, 1)) - chase_path(max(u - 0.01, 0))).normalized()
        curv = (chase_path(min(u + 0.03, 1)) - 2 * chase_path(u) + chase_path(max(u - 0.03, 0))).y
        # bay trước mặt Goku, nhìn lùi lại: thấy mặt Goku né và Frieza đuổi phía sau (đường bay không đụng cột đá)
        ahead = chase_path(min(u * 0.95 + 0.055, 1.0))
        eye = ahead + Vector((0, 0, 0.5)) + Vector((-tang.y, tang.x, 0)).normalized() * 0.7
        return eye, gc * 0.72 + fc * 0.28, 30, max(-14.0, min(14.0, -curv * 60))
    if f < 1012:                                  # 9a. Frieza mất dấu Goku: đẩy máy vào mặt hoảng hốt
        t = ease((f - 990) / 21)
        return fh + Vector((lerp(1.8, 1.25, t), -0.55, 0.06)), fh + Vector((0, 0, -0.08)), 40, lerp(0, -4, t)
    if f < 1030:                                  # 9b. Goku hiện sau lưng
        t = (f - 1012) / 17
        mid = (gc + fc) / 2
        return mid + Vector((0.2, -3.8 + t * 0.4, 0.3)), mid, 32, 0
    if f < 1110:                                  # 9c. crash zoom vào điểm va chạm, theo Frieza văng
        t = ease((f - 1030) / 5)
        hit = A["gf"]
        if f < 1046:
            return hit + Vector((0.25, lerp(-2.6, -1.8, t), 0.25)), hit, lerp(30, 45, t), lerp(0, 6, t)
        t3 = ease((f - 1046) / 20)                # qua vai Goku nhìn Frieza văng đi xa
        dirv = (fc - gc).normalized() if (fc - gc).length > 0.5 else Vector((1, 0, 0))
        eye = gc - dirv * 2.3 + Vector((0, -0.55, 0.35))
        tgt = lerp(hit, gc + dirv * 2.6 + Vector((0, 0, -0.1)), t3)
        return eye, tgt, lerp(34, 30, t3), lerp(4, 0, t3)
    t = ease((f - 1110) / 89)                     # 10. lùi máy hạ thấp: Goku hiên ngang trên nền trời giông
    return gc + lerp(Vector((1.7, -0.9, 0.45)), Vector((2.4, 0.15, -0.8)), t), gc + lerp(Vector((0, 0, 0.1)), Vector((0, 0, 0.5)), t), lerp(35, 28, t), lerp(0, 3, t)


def build_camera():
    cd = bpy.data.cameras.new("CAM")
    cd.clip_start, cd.clip_end = 0.05, 3000
    cd.sensor_fit = "AUTO"
    cam = bpy.data.objects.new("CAM", cd)
    C_CTRL.objects.link(cam)
    scene.camera = cam
    cam.rotation_mode = "XYZ"
    names = {"gc": "GOKU_chest_anchor", "gh": "GOKU_head_anchor", "fh": "FRIEZA_head_anchor",
             "fc": "FRIEZA_chest_anchor", "gf": "GOKU_fist_anchor", "gface": "GOKU_face_anchor"}
    prev_e = None
    rows = []
    for f in range(FRAMES):
        scene.frame_set(f)
        A = {k: bpy.data.objects[n].matrix_world.translation.copy() for k, n in names.items()}
        eye, tgt, focal, roll = cam_for(f, A)
        q = (tgt - eye).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), rad(roll))
        e = q.to_euler("XYZ", prev_e) if prev_e else q.to_euler("XYZ")
        if f in CUTS:
            e = q.to_euler("XYZ")
        prev_e = e
        rows.append((f, eye, e, focal))
    for f, eye, e, focal in rows:
        if f in CUTS and rows[f - 1]:
            pf, peye, pe, pfocal = rows[f - 1]
            cam.location, cam.rotation_euler, cd.lens = peye, pe, pfocal
            cam.keyframe_insert("location", frame=f - 0.4)
            cam.keyframe_insert("rotation_euler", frame=f - 0.4)
            cd.keyframe_insert("lens", frame=f - 0.4)
        cam.location, cam.rotation_euler, cd.lens = eye, e, focal
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        cd.keyframe_insert("lens", frame=f)
    for ad in (cam.animation_data, cd.animation_data):
        for fc in _fcurves(ad):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


# ── nhân vật: cel 3 tông + viền sáng màu + đốm bóng anime (hậu kỳ trên các material toon của GOKU/FRIEZA) ──
RIM_GOKU, RIM_GOKU_SSJ, RIM_FRIEZA = "#E4F4FF", "#FFE07A", "#F0E6FF"
AO_DIST, AO_CUT, OCC_DOWN = 0.05, 0.4, 0.6
THR = 0.22
HI = 1.35
RIM_EDGE = 0.6
KEY_DIR = Vector((-0.6, 0.5, 0.62)).normalized()   # hướng tới char_key trong không gian camera: trái-trên, chếch về trước
# (name: occ = tông thứ 3 ở khe/ hõm (AO), rim = độ mạnh viền sáng, spec = đốm bóng, spec_col)
CHAR_SHADE = {
    "skin": dict(hi=HI, occ="#C97C62", rim=0.5),
    # v27 mặt chibi tròn, đèn key cao → nửa mặt dưới mắt rơi vào vùng tối (thr 0.1) thành mảng loang ngang má, lại thêm
    # tông thứ 3 (úp xuống) → bỏ occ, hạ ngưỡng tối để chỉ mép quay hẳn đi mới tối; rim 0.4 phủ quai hàm + cổ khi quay từ dưới
    "goku_skin_face": dict(thr=0.025, rim=0.12),
    "goku_neck_skin": dict(thr=0.1, rim=0.0),
    "goku_ear_in": dict(occ="#B86A55", rim=0.0),
    "gi": dict(hi=HI, occ="#9E3A12", rim=0.8),
    # vải/giày xanh: viền sáng xanh tươi riêng (trộn với viền vàng SSJ thành dải xám be quanh đai, băng cổ tay)
    "blue": dict(hi=HI, occ="#101F5A", rim=0.7, rim_col="#7C98FF"),
    "gd_blue_dk": dict(hi=HI, occ="#0C1748", rim=0.6, rim_col="#5E78E0"),
    "goku_boot": dict(hi=HI, occ="#0A1240", rim=0.6, spec=0.6, spec_col="#9DB4FF", rim_col="#6A84EA"),
    "boot_sole": dict(occ="#120C0B", rim=0.3),
    "goku_rope": dict(hi=HI, occ="#8A6224", rim=0.5),
    "go_red": dict(hi=HI, occ="#5E0E14", rim=0.5),
    "white": dict(occ="#9EA6C4", rim=0.3),
    # v26 tông sáng thứ 3 (xám lam) ở mặt đón đèn + đốm bóng rõ hơn → các lọn đen tách khối như tóc đen anime
    "hair": dict(thr=0.35, hi=0.82, occ="#050507", rim=0.0, spec=0.38, spec_col="#767986"),  # v28 đen trung tính như ảnh mẫu (trước ngả xanh navy); rim 0.1 thành vòng cung xám như băng đô trên mái khi quay từ dưới
    "hair_ssj": dict(thr=0.3, hi=2.0, occ="#C77A1E", root="#E9A53E", rim=0.6, spec=0.35, spec_col="#FFF6CC"),  # đốm bóng 0.6 thành vệt bầu dục trắng trên chỏm trước trán
    "f_white": dict(occ="#B4A6D6", rim=0.8),
    "fr_neck_skin": dict(occ="#B4A6D6", rim=0.3),
    "fr_face": dict(thr=0.06, occ="#DDD3EE", rim=0.5),
    "f_purple": dict(occ="#3A1258", rim=0.8, rim_col="#C98AF2"),   # đốm bóng: decal frieza_details.py; viền sáng tím tươi (gần trắng làm mép giáp bạc màu)
    "fr_gem": dict(occ="#4A1470", rim=0.9),
    "fr_rim": dict(occ="#5E2C88", rim=0.6),
    "fr_ear_hole": dict(occ="#2A1E40", rim=0.0),
}


def char_key_light():
    """Đèn key cho nhân vật gắn theo camera (chiếu từ trên-trái khung hình), chỉ chiếu GOKU/FRIEZA (light linking):
    shot nào nhân vật cũng sáng rõ kiểu anime. Mặt trời thế giới chỉ chiếu cảnh nhưng vẫn đổ bóng nhân vật xuống đất."""
    world = bpy.data.collections.new("LL_world_sun")
    world.children.link(C_ENV)
    bpy.data.objects["key_sun"].light_linking.receiver_collection = world
    chars = bpy.data.collections.new("LL_char_key")
    chars.children.link(C_GOKU)
    chars.children.link(C_FRIEZA)
    d = bpy.data.lights.new("char_key", "SUN")
    d.energy, d.angle, d.color = 3.2, rad(0.2), (1.0, 0.97, 0.92)
    d.shadow_filter_radius = 0.5
    ob = bpy.data.objects.new("char_key", d)
    C_LIGHT.objects.link(ob)
    ob.parent = scene.camera
    ob.rotation_euler = KEY_DIR.to_track_quat("Z", "Y").to_euler()
    ob.light_linking.receiver_collection = chars
    # chỉ chính nhân vật đổ bóng của đèn key (tóc lên trán, cằm xuống cổ); cây/mây/cột đá không làm nhân vật tối thui
    ob.light_linking.blocker_collection = chars


def char_shading():
    """Chạy sau extras: nâng mọi material toon gắn trên GOKU/FRIEZA lên kiểu FighterZ — tông thứ 3 (AO) ở khe,
    viền sáng màu theo nhân vật ở mép đối diện đèn key (Goku chuyển ấm khi SSJ), đốm bóng gắt theo nửa-vector của key."""
    owners = {}
    for cn in ("GOKU", "FRIEZA"):
        for ob in bpy.data.collections[cn].all_objects:
            for ms in getattr(ob, "material_slots", []):
                m = ms.material
                if m and m.use_nodes and "glow" in m.node_tree.nodes and any(n.type == "VALTORGB" for n in m.node_tree.nodes):
                    owners.setdefault(m, cn)
    # viền inverted-hull là vỏ kín bao quanh vật: nếu đổ bóng nó che chính vật → cả nhân vật chìm trong tông tối.
    # Vỏ có pháp tuyến lật nên bật backface culling cho bóng là vỏ thôi che đèn (chỉ cho nhân vật; cảnh giữ nguyên)
    ol_char = None
    for cn in ("GOKU", "FRIEZA"):
        for ob in bpy.data.collections[cn].all_objects:
            if ob.type != "MESH" or "Outline" not in ob.modifiers:
                continue
            for ms in ob.material_slots[1:]:
                lm = ms.material
                if lm is None:
                    continue
                if lm.name == "outline":
                    ol_char = ol_char or lm.copy()
                    ol_char.name = "outline_char"
                    ms.material = lm = ol_char
                lm.use_backface_culling_shadow = True
    # không gian "Camera" của Vector Transform: X phải, Y lên, Z hướng VÀO cảnh (mặt nhìn thấy có z < 0)
    H = (Vector((KEY_DIR.x, KEY_DIR.y, -KEY_DIR.z)) + Vector((0, 0, -1))).normalized()
    for m, cn in owners.items():
        cfg = CHAR_SHADE.get(m.name, {})
        nt = m.node_tree
        N, L = nt.nodes, nt.links
        ramp = next(n for n in N if n.type == "VALTORGB")
        em = next(n for n in N if n.type == "EMISSION" and n.inputs["Color"].is_linked)
        if "thr" in cfg or THR:
            ramp.color_ramp.elements[1].position = cfg.get("thr", THR)
        els = ramp.color_ramp.elements
        if len(els) > 2 and "hi" in cfg:          # dải sáng thứ 3 chỉ khi ánh khí hắt mạnh, không phủ cả người
            els[2].position = cfg["hi"]
        color = ramp.outputs["Color"]
        geo = N.new("ShaderNodeNewGeometry")
        vt = N.new("ShaderNodeVectorTransform")
        vt.vector_type, vt.convert_from, vt.convert_to = "NORMAL", "WORLD", "CAMERA"
        L.new(geo.outputs["Normal"], vt.inputs[0])

        def mth(op, a, b=None):
            n = N.new("ShaderNodeMath"); n.operation = op
            for i, v in enumerate((a, b)):
                if v is None:
                    continue
                if isinstance(v, (int, float)):
                    n.inputs[i].default_value = v
                else:
                    L.new(v, n.inputs[i])
            return n.outputs[0]

        def dot(vec):
            dp = N.new("ShaderNodeVectorMath"); dp.operation = "DOT_PRODUCT"
            L.new(vt.outputs[0], dp.inputs[0]); dp.inputs[1].default_value = Vector(vec).normalized()
            return dp.outputs["Value"]

        def mix(col, fac, target):
            mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
            L.new(fac, mx.inputs[0]); L.new(col, mx.inputs[6])
            if isinstance(target, tuple):
                mx.inputs[7].default_value = target
            else:
                L.new(target, mx.inputs[7])
            return mx.outputs[2]

        # 0) tóc: gốc mỗi lọn + chỏm (thuộc tính "hsh" của goku_blade/shell) và khe giữa các lọn (AO) luôn tông cam
        #     dù ở mặt sáng → khối tóc xếp lớp có chiều sâu, nhìn từ sau không thành một mảng vàng phẳng
        if cfg.get("root"):
            at = N.new("ShaderNodeAttribute"); at.attribute_name = "hsh"
            under = mth("GREATER_THAN", at.outputs["Fac"], 0.02)
            ao2 = N.new("ShaderNodeAmbientOcclusion"); ao2.inputs["Distance"].default_value = cfg.get("root_ao", 0.03)
            under = mth("MAXIMUM", under, mth("LESS_THAN", ao2.outputs["AO"], cfg.get("root_cut", 0.55)))
            color = mix(color, under, hexc(cfg["root"]))
        # 1) tông thứ 3 (bóng sâu): trong vùng tối, mặt úp xuống (dưới cằm, nách, dưới tóc/vạt áo) + khe hẹp (AO đậm)
        if cfg.get("occ"):
            s2r = next(n for n in N if n.type == "SHADERTORGB")
            bw = N.new("ShaderNodeRGBToBW"); L.new(s2r.outputs["Color"], bw.inputs[0])
            dark = mth("LESS_THAN", bw.outputs[0], ramp.color_ramp.elements[1].position)
            down = mth("GREATER_THAN", dot((0.0, -1.0, -0.25)), OCC_DOWN)
            ao = N.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = AO_DIST
            crease = mth("LESS_THAN", ao.outputs["AO"], AO_CUT)
            occ = mth("MAXIMUM", mth("MULTIPLY", dark, down), mth("MULTIPLY", dark, crease))
            color = mix(color, occ, hexc(cfg["occ"]))
        # 2) viền sáng: mép bóng (Facing) ở phía đối diện key (phải-trên khung hình), màu theo nhân vật
        if cfg.get("rim", 0) > 0:
            lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
            edge = mth("GREATER_THAN", lw.outputs["Facing"], RIM_EDGE)
            side = mth("GREATER_THAN", dot((0.8, 0.45, 0.0)), 0.18)
            fac = mth("MULTIPLY", mth("MULTIPLY", edge, side), cfg["rim"])
            if cfg.get("rim_col"):
                color = mix(color, fac, hexc(cfg["rim_col"]))
            elif cn == "GOKU":
                ssj = N.new("ShaderNodeValue"); ssj.name = "ssj"
                for f, v in ((0, 0.0), (300, 1.0)):          # viền ấm vàng từ lúc biến hình SSJ (frame 300)
                    ssj.outputs[0].default_value = v
                    ssj.outputs[0].keyframe_insert("default_value", frame=f)
                for fc in _fcurves(nt.animation_data):
                    for kp in fc.keyframe_points:
                        if fc.data_path.startswith('nodes["ssj"]'):
                            kp.interpolation = "CONSTANT"
                rc = N.new("ShaderNodeMix"); rc.data_type = "RGBA"
                rc.inputs[6].default_value, rc.inputs[7].default_value = hexc(RIM_GOKU), hexc(RIM_GOKU_SSJ)
                L.new(ssj.outputs[0], rc.inputs[0])
                color = mix(color, fac, rc.outputs[2])
            else:
                color = mix(color, fac, hexc(RIM_FRIEZA))
        # 3) đốm bóng gắt: N·H (nửa-vector key/camera) qua ngưỡng
        if cfg.get("spec", 0) > 0:
            fac = mth("MULTIPLY", mth("GREATER_THAN", dot(H), 0.94), cfg["spec"])
            color = mix(color, fac, hexc(cfg.get("spec_col", "#FFFFFF")))
        L.new(color, em.inputs["Color"])


def trail_mat(name, color, energy, z0, z1, peak):
    """Vệt khí mờ dần theo trục Z của vật (z0 đậm → z1 trong suốt); lớp energy cũng theo alpha."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = z1, z0
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.0, peak
    L.new(sep.outputs["Z"], mr.inputs["Value"])
    pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.6
    L.new(mr.outputs["Result"], pw.inputs[0])
    out = N.new("ShaderNodeOutputMaterial")
    mode = N.new("ShaderNodeValue"); mode.name = "energy_mode"; mode.outputs[0].default_value = 0.0
    ev = N.new("ShaderNodeValue"); ev.name = "energy"; ev.outputs[0].default_value = energy
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = hexc(color); em.inputs["Strength"].default_value = 1.4
    ee = N.new("ShaderNodeEmission"); ee.inputs["Color"].default_value = (1, 1, 1, 1); L.new(ev.outputs[0], ee.inputs["Strength"])
    pick = N.new("ShaderNodeMixShader"); L.new(mode.outputs[0], pick.inputs[0])
    L.new(em.outputs[0], pick.inputs[1]); L.new(ee.outputs[0], pick.inputs[2])
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader"); L.new(pw.outputs[0], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(pick.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        m.blend_method = "BLEND"
    return m


def flight_trails(G, F):
    """Vệt khí kéo dài sau lưng khi bay truy đuổi: vàng (Goku), hồng tím (Frieza). Nằm trong CTRL nên không vào matte."""
    for R, col, en, f0, f1 in ((G, "#FFC83A", 0.7, 786, 986), (F, "#E25BFF", 0.5, 786, 986)):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=0.0, radius2=0.12, depth=2.3)
        for v in bm.verts:
            v.co.z += 0.5 - 1.15                     # miệng loe ở ngực (z 0.5), chóp nhọn ở z -1.8 phía sau
        # v25: thêm các vệt khí mảnh dài ngắn khác nhau toả quanh lõi (trước: một khối nón trơn như cái phễu tím)
        rs = random.Random(int(col[1:], 16) % 1000)   # seed cố định (hash() của str đổi mỗi lần chạy)
        for k in range(7):
            tmp = bmesh.new()
            ln = rs.uniform(1.3, 2.7)
            bmesh.ops.create_cone(tmp, cap_ends=False, segments=8, radius1=0.0, radius2=rs.uniform(0.018, 0.045), depth=ln)
            a_, r_ = math.tau * k / 7 + rs.uniform(-0.3, 0.3), rs.uniform(0.07, 0.19)
            for v in tmp.verts:
                v.co.z += 0.45 - ln / 2
                v.co.x += math.cos(a_) * r_ * (0.4 + 0.6 * (0.45 - v.co.z) / ln)
                v.co.y += math.sin(a_) * r_ * (0.4 + 0.6 * (0.45 - v.co.z) / ln)
            _merge(bm, tmp)
        ob = _obj(f"{R['root'].name.lower()}_trail", bm, trail_mat(f"trail_{R['root'].name}", col, en, 0.5, -1.8, 0.6),
                  C_CTRL, outline=0)
        ob.parent = R["root"]
        ob.visible_shadow = False
        ob.scale = (0, 0, 0); ob.keyframe_insert("scale", frame=0); ob.keyframe_insert("scale", frame=f0 - 1)
        for f in range(f0, f1, 4):
            k = 1.0 + 0.12 * math.sin(f * 1.7)       # chập chờn nhẹ
            ob.scale = (k, k, 1.0 + 0.1 * math.sin(f * 2.3)); ob.keyframe_insert("scale", frame=f)
        ob.scale = (0, 0, 0); ob.keyframe_insert("scale", frame=f1 + 2)


def impact_stars(G, F):
    """Ngôi sao va chạm kiểu anime (2 lớp: cam ngoài, trắng trong) bật ra rồi tắt ở mỗi đòn chạm, luôn quay mặt về camera."""
    def star_mesh(name, r_out, r_in, n, mat, z):
        bm = bmesh.new()
        ring = []
        for k in range(n * 2):
            a = math.pi * k / n + (0.2 if k % 2 else 0.0)
            r = r_out * (1.0 if k % 2 == 0 else r_in) * (1.0 if k % 4 else 0.82)
            ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
        bm.faces.new(ring)
        return _obj(name, bm, mat, C_CTRL, smooth=False, outline=0)

    for i, (f0, parent, loc) in enumerate(((719, F["el_R"], (0, 0, -0.22)), (747, G["el_R"], (0, 0, -0.24)),
                                          (1030, G["el_R"], (0, 0, -0.24)))):
        piv = empty(f"IMPACT_{i}", C_CTRL, parent, loc, 0.05)
        cons = piv.constraints.new("DAMPED_TRACK")
        cons.target, cons.track_axis = scene.camera, "TRACK_Z"
        big = 1.6 if f0 == 1030 else 1.0
        for st in (star_mesh(f"impact_{i}_out", 0.22, 0.42, 8, M["star_out"], 0.0),
                   star_mesh(f"impact_{i}_in", 0.15, 0.4, 8, M["star_in"], 0.004)):
            st.parent = piv
            st.visible_shadow = False
            for f, k in ((0, 0.0), (f0 - 1, 0.0), (f0, 0.7 * big), (f0 + 2, 1.15 * big), (f0 + 7, 0.0)):
                st.scale = (k, k, k)
                st.keyframe_insert("scale", frame=f)
            st.rotation_euler = (0, 0, 0); st.keyframe_insert("rotation_euler", frame=f0)
            st.rotation_euler = (0, 0, rad(25)); st.keyframe_insert("rotation_euler", frame=f0 + 7)


def blob_shadows(G, F):
    """Bóng tròn kiểu anime dưới chân: bám XY của root, nằm trên mặt đất (hoặc mặt biển ngoài đảo),
    nhỏ dần rồi biến mất khi nhân vật bay lên cao (driver biểu thức đơn giản, không cần Python)."""
    m = bpy.data.materials.new("blob_shadow")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    ln = N.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(tc.outputs["Object"], ln.inputs[0])
    mr = N.new("ShaderNodeMapRange")              # elip đặc kiểu cel, chỉ mềm ở sát mép
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.86, 1.0
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.62, 0.0
    L.new(ln.outputs["Value"], mr.inputs["Value"])
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = hexc("#0A2A22")
    mode = N.new("ShaderNodeValue"); mode.name = "energy_mode"; mode.outputs[0].default_value = 0.0
    black = N.new("ShaderNodeEmission"); black.inputs["Strength"].default_value = 0.0
    pick = N.new("ShaderNodeMixShader"); L.new(mode.outputs[0], pick.inputs[0])
    L.new(em.outputs[0], pick.inputs[1]); L.new(black.outputs[0], pick.inputs[2])
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader"); L.new(mr.outputs["Result"], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(pick.outputs[0], mix.inputs[2])
    out = N.new("ShaderNodeOutputMaterial"); L.new(mix.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except (AttributeError, TypeError):
        m.blend_method = "BLEND"

    for R, rad_ in ((G, 0.32), (F, 0.27)):
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=32, radius=1.0)
        ob = _obj(f"{R['root'].name.lower()}_shadow", bm, m, C_CTRL, smooth=False, outline=0)
        ob.visible_shadow = False
        ob.scale = (rad_ * 1.25, rad_, 1.0)
        if R is G:                                   # khớp lúc Goku biến mất (dịch chuyển tức thời)
            kvis([ob], 1000, True); kvis([ob], 1001, False); kvis([ob], 1012, True)
        else:                                        # Frieza bị hạ thì tắt theo
            kvis([ob], 1150, True); kvis([ob], 1151, False)

        def var(dr, name, axis):
            v = dr.driver.variables.new(); v.name, v.type = name, "TRANSFORMS"
            t = v.targets[0]; t.id, t.transform_type, t.transform_space = R["root"], f"LOC_{axis}", "WORLD_SPACE"
        for i, axis in enumerate("XY"):
            dr = ob.driver_add("location", i)
            var(dr, "v", axis)
            dr.driver.expression = "v"
        dr = ob.driver_add("location", 2)
        var(dr, "x", "X"); var(dr, "y", "Y")
        dr.driver.expression = "-0.645 + 0.65 * (sqrt(x * x + y * y) < 74.5)"
        for i, k in enumerate((rad_ * 1.25, rad_)):
            dr = ob.driver_add("scale", i)
            var(dr, "x", "X"); var(dr, "y", "Y"); var(dr, "z", "Z")
            # root ở lòng bàn chân: bay cao hơn mặt dưới ~1.6m thì bóng tắt hẳn
            dr.driver.expression = (f"{k} * max(0, 1 - max(0, z + 0.645 - 0.65 * (sqrt(x * x + y * y) < 74.5)) / 1.6)")


def finger_when_shooting():
    """Ngón trỏ Frieza chỉ duỗi ra quanh các phát Death Beam / ki blast; lúc khác nắm tay tròn
    (giơ tay lên ngực mà duỗi một ngón dễ thành cử chỉ khiếm nhã)."""
    fg = bpy.data.objects["fr_finger_R"]
    for f, v in ((0, False), (550, True), (690, False), (825, True), (970, False), (1150, False)):
        kvis([fg], f, v)
    # bàn tay 4 ngón: xoè khi hoảng (thấy Goku biến hình → trước khi chỉ tay) và từ lúc mất dấu Goku tới khi rơi;
    # còn lại co hờ. Ngón trỏ co hờ ẩn khi ngón trỏ duỗi. Key 1150 đè key "hiện" chung ở choreograph, 1151 vẫn tắt.
    relax = F["fingers_R"] + F["fingers_L"]
    opened = [F["fingers_open_R"], F["fingers_open_L"]]
    for f, v in ((0, True), (518, False), (550, True), (992, False), (1150, False)):
        kvis(relax, f, v)
        kvis(opened, f, not v)
    for f, v in ((0, True), (518, False), (690, True), (825, False), (970, True), (992, False), (1150, False)):
        kvis([F["finger_idx_R"]], f, v)


# ───────────────────────────── main ─────────────────────────────
setup_render()
storm = build_world()
G = build_goku()
F = build_frieza()
cracks, debris, splash = build_env()
sun, auras = build_lights(G)
fx = empty("FX", C_CTRL, size=0.5)
empty("BEAM_TARGET", C_CTRL)
empty("BLAST_POINT", C_CTRL)
choreograph(G, F, fx, sun, auras, storm, cracks, debris, splash)
build_camera()
char_key_light()
impact_stars(G, F)
flight_trails(G, F)
blob_shadows(G, F)
finger_when_shooting()
exec(compile(open(os.path.join(HERE, "kamehameha.py")).read(), "kamehameha.py", "exec"), globals())
kame_build()                         # v23: bàn tay xoè, quả cầu, tia, cầu nổ (trước extras để được tô cel + viền)
# chi tiết bổ sung theo từng mảng (mỗi file một người làm, chạy sau cùng, dùng chung globals: G, F, M, helper...)
# GVF_EXTRAS=a.py:b.py để thử riêng vài file thay vì cả thư mục extras/
_extras = os.environ.get("GVF_EXTRAS")
for _fn in (_extras.split(":") if _extras else sorted(glob.glob(os.path.join(HERE, "extras", "*.py")))):
    print("EXTRAS", _fn)
    exec(compile(open(_fn).read(), _fn, "exec"), globals())
char_shading()                       # sau extras: phủ cả material nhân vật do extras tạo
exec(compile(open(os.path.join(HERE, "char_outlines.py")).read(), "char_outlines.py", "exec"), globals())
char_outlines()                      # sau char_shading: nét viền nhân vật đổi độ dày theo camera/bộ phận, vuốt nhọn mũi
exec(compile(open(os.path.join(HERE, "retime.py")).read(), "retime.py", "exec"), globals())
retime_scene()                       # cuối cùng: giãn nhịp mọi keyframe + marker theo shot (phim 20 s → ~29 s)
kame_animate()                       # rồi key đoạn Kamehameha vào khoảng trống retime để lại (frame mới)
exec(compile(open(os.path.join(HERE, "secondary.py")).read(), "secondary.py", "exec"), globals())
secondary_motion()                   # sau cùng: tóc/đuôi có quán tính theo gia tốc của đầu/hông (nhịp frame cuối)
grass_wind()                         # cỏ ngả ra ngoài theo gió khí lúc gồng/biến hình
tree_wind()                          # v28 cây đung đưa theo gió giông + sóng xung kích biến hình
storm_leaves()                       # v29 lá cây bay theo gió giông, bị sóng xung kích hất văng
beam_impacts()                       # v30 Death Beam trượt Goku trúng đất phía sau: loé, đất văng, bụi, vết cháy
foot_ground_fix()                    # v31 chân Goku không lún xuống đất lúc gồng khí
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
