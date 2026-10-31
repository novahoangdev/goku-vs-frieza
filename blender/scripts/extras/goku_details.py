# Chi tiết trau chuốt cho Goku chibi: chữ 悟 trong vòng tròn sau lưng, nút thắt đai, viền cổ tay,
# nét gấp vải, vệt sáng trên các lọn tóc, đường may giày. Chạy sau build_scene.py (dùng chung globals: G, M, helper...).
# Không dời/đổi cỡ phần cũ; vật mới tên "gd_*" và chép khoá ẩn/hiện từ phần gốc (torso / tóc).
from mathutils.bvhtree import BVHTree as _GD_BVH


def _gd_vis_like(obs, ref):
    """Chép các khoá hide_render của `ref` (vd. Goku biến mất lúc dịch chuyển, đổi dạng SSJ)."""
    try:
        ad = ref.animation_data
        keys = []
        if ad and ad.action:
            for fc in _fcurves(ad):
                if fc.data_path == "hide_render":
                    keys = [(int(round(k.co[0])), bool(k.co[1] > 0.5)) for k in fc.keyframe_points]
        for f, hidden in keys:
            kvis(obs, f, not hidden)
        if not keys:
            for o in obs:
                o.hide_render = o.hide_viewport = ref.hide_render
    except Exception as e:
        print("GD vis copy failed", ref.name, e)


def _gd_bvh(target):
    """BVH của mesh gốc (không outline) trong hệ toạ độ của parent của target."""
    mw = target.matrix_basis
    me = target.data
    return _GD_BVH.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])


def _gd_project(bvh, p, d, off):
    hit = bvh.ray_cast(p - d * 0.5, d, 2.0)
    if hit[0] is None:
        return None
    return hit[0] - d * off


def _gd_tube(name, pts, r, mat, col, parent, sides=6, taper=True, outline=0.0):
    """Nét vẽ: ống mảnh chạy qua các điểm (toạ độ parent), thon hai đầu như nét mực."""
    bm = bmesh.new()
    n = len(pts)
    rings = []
    for i, c in enumerate(pts):
        t = i / (n - 1)
        tang = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        q = tang.to_track_quat("Z", "Y")
        rr = r * (max(0.18, math.sin(math.pi * t) ** 0.6) if taper else 1.0)
        rings.append([bm.verts.new(c + q @ Vector((math.cos(a) * rr, math.sin(a) * rr, 0)))
                      for a in (math.tau * k / sides for k in range(sides))])
    for i in range(n - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(sides):
            bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    ob = _obj(name, bm, mat, col, smooth=True, outline=outline)
    ob.parent = parent
    ob.visible_shadow = False
    return ob


def _gd_stroke(name, target, pts, dirfn, r, mat, col, off=0.0035, samples=14):
    """Nét cong dán lên bề mặt `target`: nội suy Catmull-Rom qua pts rồi chiếu theo dirfn(p)."""
    bvh = _gd_bvh(target)
    P = [Vector(p) for p in pts]
    dense = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for s in range(samples):
            t = s / samples
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(P[-1])
    out = [q for q in (_gd_project(bvh, p, dirfn(p), off) for p in dense) if q is not None]
    if len(out) < 3:
        return None
    return _gd_tube(name, out, r, mat, col, target.parent)


def _gd_conform(name, target, verts2d, faces, plane, mat, col, off):
    """Mesh phẳng (u, v) dán ôm lưng: (u, v) → điểm trên mặt phẳng `plane` rồi chiếu vào target."""
    bvh = _gd_bvh(target)
    to3, d = plane
    bm = bmesh.new()
    vs = []
    for u, v in verts2d:
        p = to3(u, v)
        q = _gd_project(bvh, p, d, off)
        vs.append(bm.verts.new(q if q is not None else p))
    for f in faces:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    ob = _obj(name, bm, mat, col, smooth=False, outline=0)
    ob.parent = target.parent
    ob.visible_shadow = False
    return ob


def _gd_disc(n_ring=6, n_seg=40, r=1.0):
    verts, faces = [(0.0, 0.0)], []
    for i in range(1, n_ring + 1):
        rr = r * i / n_ring
        for k in range(n_seg):
            a = math.tau * k / n_seg
            verts.append((rr * math.cos(a), rr * math.sin(a)))
    for k in range(n_seg):
        faces.append((0, 1 + k, 1 + (k + 1) % n_seg))
    for i in range(1, n_ring):
        b0, b1 = 1 + (i - 1) * n_seg, 1 + i * n_seg
        for k in range(n_seg):
            faces.append((b0 + k, b1 + k, b1 + (k + 1) % n_seg, b0 + (k + 1) % n_seg))
    return verts, faces


def _gd_text_mesh(ch, size):
    """Chữ (font Hiragino) → (verts2d, faces) đã tam giác hoá, tâm ở gốc."""
    fc = bpy.data.curves.new("gd_tmp_txt", "FONT")
    fc.body = ch
    for path in FONT_PATHS:
        if os.path.exists(path):
            fc.font = bpy.data.fonts.load(path, check_existing=True)
            break
    fc.size, fc.align_x, fc.align_y = size, "CENTER", "CENTER"
    tmp = bpy.data.objects.new("gd_tmp_txt", fc)
    bpy.context.scene.collection.objects.link(tmp)
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        verts = [(v.co.x, v.co.y) for v in bm.verts]
        bm.verts.index_update()
        faces = [tuple(v.index for v in f.verts) for f in bm.faces]
        bm.free()
        bpy.data.meshes.remove(me)
    finally:
        bpy.data.objects.remove(tmp)
        bpy.data.curves.remove(fc)
    return verts, faces


def _gd_build():
    c = C_GOKU
    obj = bpy.data.objects
    torso, hair_ssj, hair = obj["goku_torso"], obj["goku_hair_ssj"], obj["goku_hair_base"]
    body_new, ssj_new, base_new = [], [], []
    Mx = {
        "gd_gi_line": flat("gd_gi_line", "#B04A14"),          # nét gấp vải: cam cháy, mềm hơn viền
        "gd_blue_dk": toon("gd_blue_dk", "#1F3A8C", "#142660", "#3A5CC0", rim=0.5),
        "gd_seam": flat("gd_seam", "#16245E"),
        "gd_ssj_hl": flat("gd_ssj_hl", "#FFF8D6", 1.1, energy=0.15),
        "gd_hair_hl": flat("gd_hair_hl", "#56608E"),
        "gd_ink": flat("gd_ink", "#1A1414"),
        "gd_white": flat("gd_white", "#FFFDF6"),
    }

    # ── 1. vòng tròn chữ 悟 sau lưng (nhiều cảnh quay qua vai/sau lưng) ──
    try:
        zc, R0 = 0.15, 0.078
        back = (lambda u, v: Vector((-u, 0.4, zc + v)), Vector((0, -1, 0)))  # nhìn từ sau: phải người xem = -X
        dv, df = _gd_disc(r=R0 + 0.006)
        body_new.append(_gd_conform("gd_back_ring", torso, dv, df, back, Mx["gd_ink"], c, 0.0025))
        dv, df = _gd_disc(r=R0)
        body_new.append(_gd_conform("gd_back_disc", torso, dv, df, back, Mx["gd_white"], c, 0.0038))
        tv, tf = _gd_text_mesh("悟", 0.108)
        body_new.append(_gd_conform("gd_back_kanji", torso, tv, tf, back, Mx["gd_ink"], c, 0.0052))
    except Exception as e:
        print("GD back kanji failed", e)

    # ── 2. nút thắt đai phía trước ──
    try:
        k = sphere("gd_belt_knot", 1, M["blue"], c, (0.026, 0.017, 0.022), seg=16, outline=0.003)
        attach(k, G["hips"], (0.05, -0.128, 0.05))
        body_new.append(k)
    except Exception as e:
        print("GD belt knot failed", e)

    # ── 3. cổ tay: gờ viền trên/dưới + đường gân ──
    try:
        for side in ("R", "L"):
            for j, z in enumerate((-0.107, -0.153)):
                t = torus(f"gd_wrist_rim_{side}{j}", 0.0465, 0.0052, Mx["gd_blue_dk"], c, seg=24, ring=6, outline=0.002)
                attach(t, G[f"el_{side}"], (0, 0, z))
                body_new.append(t)
            t = torus(f"gd_sleeve_rim_{side}", 0.05, 0.006, Mx["gd_blue_dk"], c, seg=24, ring=6, outline=0.002)
            attach(t, G[f"sh_{side}"], ((-0.004 if side == "R" else 0.004), 0, -0.074))
            body_new.append(t)
    except Exception as e:
        print("GD wrist failed", e)

    # ── 4. nét gấp vải (mực cam cháy) trên lưng, hông và ống quần ──
    try:
        W = Mx["gd_gi_line"]
        back_dir = lambda p: Vector((0, -1, 0))
        for i, sx in enumerate((-1, 1)):
            # nếp chéo dưới nách sau lưng
            body_new.append(_gd_stroke(f"gd_fold_back_{i}", torso,
                                       [(sx * 0.125, 0.4, 0.22), (sx * 0.112, 0.4, 0.19), (sx * 0.1, 0.4, 0.16)], back_dir, 0.0024, W, c))
            # nếp ngực trước (dưới cổ áo) – chỉ bên không có chữ
            if sx < 0:
                body_new.append(_gd_stroke("gd_fold_front", torso,
                                           [(-0.118, -0.4, 0.2), (-0.095, -0.4, 0.17), (-0.088, -0.4, 0.135)],
                                           lambda p: Vector((0, 1, 0)), 0.0022, W, c))
        for side, sx in (("R", -1), ("L", 1)):
            th = obj[f"goku_thigh_{side}"]
            rad_in = lambda p: Vector((-p.x, -p.y, 0)).normalized() if Vector((p.x, p.y)).length > 1e-4 else Vector((0, 1, 0))
            # nếp xếp bên hông quần + nếp chữ V phía trước đùi
            body_new.append(_gd_stroke(f"gd_fold_thigh_{side}", th,
                                       [(sx * 0.2, 0.0, -0.06), (sx * 0.2, -0.02, -0.11), (sx * 0.2, 0.01, -0.16)], rad_in, 0.0023, W, c))
            body_new.append(_gd_stroke(f"gd_fold_thighf_{side}", th,
                                       [(-sx * 0.05, -0.2, -0.13), (0.0, -0.2, -0.155), (sx * 0.05, -0.2, -0.17)], rad_in, 0.0021, W, c))
            body_new.append(_gd_stroke(f"gd_fold_thighb_{side}", th,
                                       [(-sx * 0.05, 0.2, -0.17), (0.0, 0.2, -0.19), (sx * 0.04, 0.2, -0.2)], rad_in, 0.0021, W, c))
    except Exception as e:
        print("GD folds failed", e)

    # ── 5. giày: đường may giữa mũi + viền cổ giày ──
    try:
        for side in ("R", "L"):
            ft, bt = obj[f"goku_foot_{side}"], obj[f"goku_boot_{side}"]
            fwd = lambda p: Vector((0, 1, 0))
            body_new.append(_gd_stroke(f"gd_boot_front_{side}", bt,
                                       [(0, -0.2, -0.105), (0, -0.2, -0.145), (0, -0.2, -0.185)], fwd, 0.0022, Mx["gd_seam"], c))
    except Exception as e:
        print("GD boots failed", e)

    # ── 6. vệt sáng sắc gần gốc các lọn tóc lớn (kiểu anime), nằm trên mặt sáng của lọn ──
    # Đèn key gắn camera chiếu từ trên-trái khung hình → nhìn từ trước, mặt sáng là mặt -w (về phía -X, phải nhân vật).
    # Chỉ lọn quay mặt về trước; mesh con của chính object tóc nên rung/phồng theo tóc.
    try:
        def lit_face(x):
            """Mặt trên-trái của LOCK_SECTION: x∈[-1, 0] → y."""
            pts = [p for p in LOCK_SECTION[:3]]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                if x0 <= x <= x1:
                    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            return 0.0

        def slivers(tag, hair_ob, frames_list, mat, store, s0=0.06, s1=0.5, xc=-0.48, half=0.24):
            bm = bmesh.new()
            n_ok = 0
            for frames in frames_list:
                P0, w0, n0, _, _ = frames[0]
                if n0.y > -0.25 or n0.z < -0.3:            # lọn quay ra sau / chúc xuống: bỏ
                    continue
                rings = len(frames)
                i0, i1 = max(1, int(s0 * rings)), int(s1 * rings)
                row = []
                for i in range(i0, i1 + 1):
                    P, w, n, hw, ht = frames[i]
                    u = (i - i0) / (i1 - i0)
                    k = math.sin(math.pi * u) ** 0.8 * (1.0 - 0.35 * u)   # thon nhọn 2 đầu, đầu gốc to hơn
                    xs = (xc - half * k, xc + half * k * 0.6)
                    vs = []
                    for x in xs:
                        y = lit_face(x)
                        q = P + w * x * hw + n * y * ht
                        # pháp tuyến mặt sáng: vuông góc với cạnh mép (-1,0) → gờ (0,1.15) trong mặt cắt
                        nf = (n * hw - w * 1.15 * ht).normalized()
                        vs.append(bm.verts.new(q + nf * 0.0022))
                    row.append(vs)
                for a_, b_ in zip(row, row[1:]):
                    bm.faces.new((a_[0], a_[1], b_[1], b_[0]))
                n_ok += 1
            if not bm.faces:
                bm.free()
                return
            ob = _obj(tag, bm, mat, c, smooth=False, outline=0)
            ob.parent = hair_ob
            ob.visible_shadow = False
            store.append(ob)
            print("GD hair highlights", tag, n_ok)

        HL = globals().get("GOKU_HAIR_HL", {})
        slivers("gd_ssj_hl", hair_ssj, HL.get("goku_hair_ssj", []), Mx["gd_ssj_hl"], ssj_new)
        slivers("gd_hair_hl", hair, HL.get("goku_hair_base", []), Mx["gd_hair_hl"], base_new, s0=0.1, s1=0.42, half=0.12)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("GD hair highlights failed", e)

    body_new = [o for o in body_new if o]
    _gd_vis_like(body_new, torso)
    _gd_vis_like(ssj_new, hair_ssj)
    _gd_vis_like(base_new, hair)
    G.setdefault("details", body_new + ssj_new + base_new)
    print("GD goku_details:", len(body_new), "body,", len(ssj_new), "ssj,", len(base_new), "base")


try:
    _gd_build()
except Exception as _e:
    import traceback
    traceback.print_exc()
    print("GD goku_details skipped", _e)
