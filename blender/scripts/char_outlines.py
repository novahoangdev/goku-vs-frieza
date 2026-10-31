# Nét viền nhân vật kiểu FighterZ (hậu kỳ, chạy SAU char_shading trong build_scene.py, chung globals).
# Chỉ đụng modifier "Outline" (Solidify inverted-hull) của vật trong GOKU/FRIEZA; viền cảnh giữ nguyên.
#  1) bù khoảng cách camera: driver trên Solidify.thickness theo khoảng cách camera→vật và tiêu cự, nên cận cảnh
#     không thành vệt mực dày cả chục pixel, toàn cảnh không mảnh như sợi tóc mà cũng không đặc thành cục đen.
#  2) theo bộ phận: vật lớn (đầu, tóc, thân, chân) làm nên đường bao ngoài → nét đậm hơn; vật nhỏ (gờ, nút, dây) mảnh hơn.
#  3) bao ngoài đậm, trong mảnh: trọng số theo hướng pháp tuyến so với trục thân nhân vật — mặt quay ra ngoài
#     (mép ngoài tay/chân/đầu, tạo đường bao) nét đủ; mặt quay vào trong (đùi trong, mặt tay áp vào thân) nét mảnh.
#  3b) vuốt nhọn: trọng số đỉnh = độ dày cục bộ của khối (bắn tia vào trong) → mũi lọn tóc, ngón tay, tai, đầu dây
#     nét thu nhỏ dần thay vì cục tròn; khối dày giữ nét đủ.
#  4) màu nét: vật còn dùng viền nâu-đen chung (gờ tay áo, gờ vai Frieza) đổi sang tông tối của chính chất liệu.
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OL_REF = 3.0            # khoảng cách hiệu dụng (quy về ống 50mm) giữ nguyên độ dày gốc — cỡ trung cảnh
OL_POW = 0.3            # độ dày thế giới ∝ d^0.3 → bề rộng pixel ∝ d^-0.7 (xa mảnh dần, gần đậm dần nhưng có hãm)
OL_CLAMP = (0.45, 2.4)
OL_TIP_T = 0.035        # độ dày khối (m) từ đó trở lên nét đủ; mỏng hơn thì nét thu dần
OL_TIP_MIN = 0.35       # hệ số nét ở chỗ mỏng nhất (mũi tóc, đầu ngón)
OL_INNER = 0.4          # hệ số trọng số của mặt quay hẳn vào trong thân (1 = không phân biệt)
OL_LINE_FOR = {"gd_blue_dk": "blue", "fr_rim": "f_purple", "fr_gem": "f_purple"}   # chất liệu → màu nét


def _ol_size_mult(ob):
    """Vật càng lớn càng góp phần đường bao ngoài → nét đậm hơn (đầu/tóc ×1.4, vật nhỏ ×0.85)."""
    d = ob.dimensions.length
    return max(0.85, min(1.4, (d / 0.3) ** 0.45))


def _ol_tip_weights(ob, center):
    """Trọng số 0..1 mỗi đỉnh = độ dày khối tại đó (tia từ đỉnh bắn ngược pháp tuyến), làm mượt 2 vòng,
    nhân hệ số hướng ra ngoài so với tâm thân `center` (thế giới; trục đứng được nén ×0.3 để tay/chân xét theo ngang)."""
    me = ob.data
    n = len(me.vertices)
    if n == 0:
        return None
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    th = []
    for v in me.vertices:
        nr = v.normal
        if nr.length < 1e-6:
            th.append(OL_TIP_T); continue
        hit = bvh.ray_cast(v.co - nr * 1e-4, -nr, OL_TIP_T * 2)
        th.append(OL_TIP_T if hit[0] is None else hit[3])
    nb = [[] for _ in range(n)]
    for e in me.edges:
        a, b = e.vertices
        nb[a].append(b); nb[b].append(a)
    for _ in range(2):
        th = [(th[i] + sum(th[j] for j in nb[i])) / (1 + len(nb[i])) if nb[i] else th[i] for i in range(n)]
    mw = ob.matrix_world
    nm = mw.to_3x3().inverted_safe().transposed()
    out = []
    for v in me.vertices:
        r = mw @ v.co - center
        r.z *= 0.3
        nw = nm @ v.normal
        o = 1.0 if r.length < 1e-4 or nw.length < 1e-6 else r.normalized().dot(nw.normalized())
        o = max(0.0, min(1.0, 0.35 + 0.65 * o))
        out.append(OL_INNER + (1.0 - OL_INNER) * o)
    return [min(1.0, t / OL_TIP_T) ** 0.75 * o for t, o in zip(th, out)]


def _ol_line_color(ob):
    if len(ob.material_slots) < 2 or ob.material_slots[0].material is None:
        return
    key = OL_LINE_FOR.get(ob.material_slots[0].material.name)
    if key and key in LINE_COLORS:
        lm = line_mat(M[key]) if key in M else None
        if lm is None:
            lm = flat(f"line_{key}", LINE_COLORS[key], backface=True)
        lm.use_backface_culling_shadow = True
        ob.material_slots[1].material = lm


def char_outlines():
    cam = bpy.data.objects.get("CAM") or scene.camera
    stats = []
    scene.frame_set(0)                    # tư thế đứng đầu phim để xét hướng trong/ngoài
    for cn, anchor in (("GOKU", "GOKU_chest_anchor"), ("FRIEZA", "FRIEZA_chest_anchor")):
        anc = bpy.data.objects[anchor]
        for ob in bpy.data.collections[cn].all_objects:
            mod = ob.modifiers.get("Outline")
            if mod is None or mod.type != "SOLIDIFY" or mod.thickness == 0:
                continue
            base = mod.thickness * _ol_size_mult(ob)
            target = anc
            if ob.type == "MESH":
                w = _ol_tip_weights(ob, anc.matrix_world.translation.copy())
                if w is not None:
                    vg = ob.vertex_groups.get("ol_w") or ob.vertex_groups.new(name="ol_w")
                    for i, x in enumerate(w):
                        vg.add([i], x, "REPLACE")
                    mod.vertex_group = vg.name
                    mod.thickness_vertex_group = OL_TIP_MIN
                target = ob                       # gốc vật nằm sát khối (đuôi Frieza là curve gốc ở 0 → dùng ngực)
            _ol_line_color(ob)
            fc = mod.driver_add("thickness")
            dr = fc.driver
            dr.type = "SCRIPTED"
            v = dr.variables.new(); v.name, v.type = "d", "LOC_DIFF"
            v.targets[0].id, v.targets[1].id = cam, target
            v = dr.variables.new(); v.name, v.type = "l", "SINGLE_PROP"
            v.targets[0].id_type, v.targets[0].id, v.targets[0].data_path = "CAMERA", cam.data, "lens"
            dr.expression = (f"{base:.6f}*clamp(pow(d*{50.0 / OL_REF:.4f}/max(l,1.0),{OL_POW}),"
                             f"{OL_CLAMP[0]},{OL_CLAMP[1]})")
            assert dr.is_simple_expression, dr.expression
            stats.append(ob.name)
    print("CHAR_OUTLINES", len(stats), "objects")
