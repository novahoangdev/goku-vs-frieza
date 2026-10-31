# Chuyển động thứ cấp (v26): tóc Goku và đuôi Frieza có quán tính — cơ thể tăng tốc thì tóc/đuôi trễ lại, quất ra rồi
# dao động tắt dần (lò xo – giảm chấn theo gia tốc trong hệ toạ độ của đầu/hông). Chạy cuối build_scene.py, sau
# retime_scene() + kame_animate() để tính theo đúng nhịp frame cuối cùng; cộng thêm vào key sẵn có (rung khí, lắc đuôi).
import bpy, math
from mathutils import Vector, Quaternion

SPRING_K, SPRING_C = 0.045, 0.24          # tần số riêng ~0.5 s ở 60 fps, tắt dần sau ~2 nhịp
TELEPORT = 0.9                            # m/frame: nhanh hơn = cut / dịch chuyển tức thời → reset lò xo, bỏ gia tốc


class _Spring:
    def __init__(self, gain, lim):
        self.th, self.v, self.gain, self.lim = 0.0, 0.0, gain, lim

    def step(self, a):
        acc = -SPRING_K * self.th - SPRING_C * self.v + self.gain * a
        self.v += acc
        self.th = max(-self.lim, min(self.lim, self.th + self.v))
        return self.th

    def reset(self):
        self.th = self.v = 0.0


def secondary_motion():
    sc = bpy.context.scene
    f0, f1 = sc.frame_start, sc.frame_end
    cuts = {int(m.frame) for m in sc.timeline_markers if m.name == "cut"}
    hips, head = F["hips"], G["head"]
    segs = list(F["tail"])
    hair = [o for o in (G["hair_ssj"], bpy.data.objects.get("goku_hair_base")) if o]
    P_h, R_h, P_g, R_g = {}, {}, {}, {}
    base = {o.name: {} for o in segs + hair}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        mh, mg = hips.matrix_world, head.matrix_world
        P_h[f], R_h[f] = mh.translation.copy(), mh.to_3x3().normalized()
        P_g[f], R_g[f] = mg.translation.copy(), mg.to_3x3().normalized()
        for o in segs + hair:
            base[o.name][f] = tuple(o.rotation_euler)

    def local_acc(P, R, f):
        if f - 1 < f0 or f + 1 > f1:
            return None
        v0, v1 = P[f] - P[f - 1], P[f + 1] - P[f]
        if v0.length > TELEPORT or v1.length > TELEPORT or f in cuts or f + 1 in cuts:
            return None
        return R[f].inverted() @ (v1 - v0)

    # đuôi: gia tốc lên → đuôi trễ xuống (rx âm), gia tốc ngang +X → đuôi lệch -X (rz dương); sóng lan dần ra chóp
    t_up, t_side = _Spring(140.0, 20.0), _Spring(160.0, 22.0)
    # tóc (dựng theo +Z của đầu): tăng tốc về trước (-Y) → tóc ngả ra sau (rx âm), sang +X → tóc lệch -X (ry âm)
    h_fw, h_side = _Spring(110.0, 11.0), _Spring(110.0, 11.0)
    hist = {}
    drag, dv = {}, 0.0                    # lực cản: bay nhanh thì đuôi bị kéo thẳng ra sau (mất độ cong chữ S)
    hv = Vector((0, 0, 0))
    for f in range(f0, f1 + 1):
        if f0 < f < f1:
            v0, v1 = P_h[f] - P_h[f - 1], P_h[f + 1] - P_h[f]
            sp = 0.0 if (v0.length > TELEPORT or v1.length > TELEPORT or f in cuts) else (v0 + v1).length / 2
        else:
            sp = 0.0
        dv += (min(1.0, max(0.0, (sp - 0.08) / 0.25)) - dv) * 0.12   # ~0.3 m/frame (18 m/s) → thẳng hẳn, lọc mượt
        drag[f] = dv
        a = local_acc(P_h, R_h, f)
        if a is None:
            t_up.reset(); t_side.reset()
            a = Vector((0, 0, 0))
        hist[f] = (t_up.step(-a.z), t_side.step(a.x))
        g = local_acc(P_g, R_g, f)
        if g is None:
            h_fw.reset(); h_side.reset()
            g = Vector((0, 0, 0))
        hx, hy = h_fw.step(g.y), h_side.step(-g.x)
        # v29 lực cản không khí lên tóc: bay nhanh thì cả mái bị gió ép ngả ngược hướng bay (vận tốc trong hệ đầu, lọc mượt)
        if f0 < f < f1:
            vg = P_g[f + 1] - P_g[f - 1]
            vl = R_g[f].inverted() @ (vg / 2) if vg.length / 2 < TELEPORT and f not in cuts and f + 1 not in cuts else Vector()
        else:
            vl = Vector()
        hv = hv + (vl - hv) * 0.15
        dmag = min(1.0, max(0.0, (hv.length - 0.06) / 0.25))
        dir_ = hv.normalized() if hv.length > 1e-5 else Vector()
        hx = max(-14.0, min(14.0, hx + 8.0 * dmag * dir_.y))
        hy = max(-14.0, min(14.0, hy - 8.0 * dmag * dir_.x))
        if f % 2 == 0 or f == f1:
            for o in hair:
                b = base[o.name][f]
                o.rotation_euler = (b[0] + math.radians(hx), b[1] + math.radians(hy), b[2])
                o.keyframe_insert("rotation_euler", frame=f)
    for i, s in enumerate(segs):
        w = 0.35 + 0.65 * (i + 1) / len(segs)          # gốc đuôi ít, chóp quất mạnh
        lag = int(round(i * 1.5))                       # sóng truyền dọc đuôi
        for f in range(f0, f1 + 1, 2):
            up, side = hist.get(max(f0, f - lag), (0.0, 0.0))
            b = base[s.name][f]
            st = -s.delta_rotation_euler.x * 0.8 * drag.get(f, 0.0)   # bỏ bớt độ cong sẵn của đốt khi bay nhanh
            s.rotation_euler = (b[0] + math.radians(up * w) + st, b[1], b[2] + math.radians(side * w))
            s.keyframe_insert("rotation_euler", frame=f)
    belt_tails(cuts, f0, f1)
    for o in segs + hair:
        for fc in _fcurves(o.animation_data):
            if fc.data_path == "rotation_euler":
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
    sc.frame_set(f0)
    if __import__("os").environ.get("GVF_SEC_DEBUG"):
        top = sorted(hist.items(), key=lambda kv: -max(abs(kv[1][0]), abs(kv[1][1])))[:400:20]
        print("SECONDARY top", [(f, round(u), round(sd)) for f, (u, sd) in top])
    mx = max(abs(v) for pair in hist.values() for v in pair)
    print(f"SECONDARY tail max {mx:.1f}°, drag max {max(drag.values()):.2f}, frames {f0}-{f1}")


def belt_tails(cuts, f0, f1):
    """v27 đuôi đai vải: vốn dựng cứng theo hông → khi Goku nằm ngang bay đi chúng chĩa ngang như que. Ở đây chúng là
    con lắc mềm: hướng nghỉ = trọng lực trong hệ hông, bay nhanh thì bị gió kéo ra sau ngược hướng bay, cộng lò xo
    theo gia tốc (dừng gấp thì văng tới rồi đung đưa). Dời gốc xoay của mỗi đuôi về điểm buộc ở nút thắt."""
    tails = [bpy.data.objects.get(f"goku_belt_tail_{i}") for i in range(2)]
    tails = [t for t in tails if t]
    if not tails:
        return
    from mathutils import Matrix
    sc, par = bpy.context.scene, tails[0].parent          # hông Goku (F["hips"] là của Frieza)
    P, R = {}, {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        m = par.matrix_world
        P[f], R[f] = m.translation.copy(), m.to_3x3().normalized()
    for t in tails:
        top = max(t.data.vertices, key=lambda v: v.co.z).co.copy()
        t.data.transform(Matrix.Translation(-top))
        t.location = t.location + top
    sx, sy = _Spring(100.0, 18.0), _Spring(100.0, 18.0)
    tx = ty = 0.0
    keys = {}
    for f in range(f0, f1 + 1):
        Ri = R[f].inverted()
        g = Ri @ Vector((0, 0, -1))
        ok = f0 < f < f1 and f not in cuts and f + 1 not in cuts
        v0 = P[f] - P[f - 1] if f > f0 else Vector()
        v1 = P[f + 1] - P[f] if f < f1 else Vector()
        if not ok or v0.length > TELEPORT or v1.length > TELEPORT:
            sx.reset(); sy.reset()
            a = vl = Vector((0, 0, 0))
            jump = True
        else:
            a, vl, jump = Ri @ (v1 - v0), Ri @ ((v0 + v1) / 2), False
        sp = vl.length
        d = g + (-vl.normalized() * min(1.6, sp / 0.12) if sp > 1e-4 else Vector())   # gió ngược hướng bay
        d.normalize()
        # đuôi dựng theo -Z: xoay Y một góc θ đưa chóp về (-sinθ, 0, -cosθ); xoay X một góc φ đưa về (0, sinφ, -cosφ)
        ry = max(-1.3, min(1.3, math.atan2(-d.x, max(0.05, -d.z) if d.z < 0 else 0.05)))
        rx = max(-1.3, min(1.3, math.atan2(d.y, max(0.05, -d.z) if d.z < 0 else 0.05)))
        k = 1.0 if jump else 0.25                      # vải đuổi theo hướng nghỉ mới, không giật tức thì
        tx += (rx - tx) * k
        ty += (ry - ty) * k
        cl = lambda x: max(-0.95, min(0.95, x))        # vải không lật ngược lên trên nút thắt
        keys[f] = (cl(tx * 0.85 + math.radians(sx.step(-a.y))), cl(ty * 0.85 + math.radians(sy.step(a.x))))
    for i, t in enumerate(tails):
        b = tuple(t.rotation_euler)
        for f in range(f0, f1 + 1, 2):
            rx, ry = keys[max(f0, f - i)]                  # đuôi thứ 2 trễ 1 frame cho khỏi lắc đồng bộ
            t.rotation_euler = (b[0] + rx, b[1] + ry, b[2])
            t.keyframe_insert("rotation_euler", frame=f)
        for fc in _fcurves(t.animation_data):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    mx = max(max(abs(a), abs(b)) for a, b in keys.values())
    print(f"BELT tails max {math.degrees(mx):.0f}°")


def grass_wind():
    """Gió khí lúc gồng (Goku ở gốc toạ độ): cỏ bị thổi ngả ra ngoài — shape key "ki_wind" uốn mỗi ngọn theo hướng
    xuyên tâm, cong nhiều theo độ cao ngọn và yếu dần theo khoảng cách; phập phồng khi tụ khí, rạp hẳn lúc nổ biến
    hình (frame gốc 296), rồi dịu lại tới khi bay đi. Key theo frame gốc → quy đổi bằng rt() (chạy sau retime)."""
    obs = [o for o in (bpy.data.objects.get("grass_tufts"), bpy.data.objects.get("env_grass_clumps")) if o]
    for ob in obs:
        me = ob.data
        if not me.shape_keys:
            ob.shape_key_add(name="Basis", from_mix=False)
        sk = ob.shape_key_add(name="ki_wind", from_mix=False)
        mw = ob.matrix_world
        inv = mw.inverted().to_3x3()
        for i, v in enumerate(me.vertices):
            p = mw @ v.co
            h = max(0.0, p.z - 0.01)
            r = math.hypot(p.x, p.y)
            if h <= 0 or r < 0.5:
                continue
            ang = 1.15 * math.exp(-max(0.0, r - 3.0) / 9.0)          # góc rạp tối đa ~66° sát Goku
            d = Vector((p.x / r, p.y / r, 0.0))
            off = d * h * math.sin(ang) + Vector((0, 0, -h * (1 - math.cos(ang))))
            sk.data[i].co = v.co + inv @ off
        keys = [(0, 0.0), (118, 0.0)]
        for f in range(120, 292, 6):
            t = (f - 120) / 170
            keys.append((f, 0.18 + 0.32 * t + 0.07 * math.sin(f * 0.9)))
        keys += [(296, 0.55), (302, 1.0), (330, 0.85), (360, 0.45)]
        for f in range(366, 780, 8):
            keys.append((f, 0.3 + 0.07 * math.sin(f * 0.7)))
        keys += [(790, 0.0)]
        for f, v in keys:
            sk.value = v
            sk.keyframe_insert("value", frame=rt(f))
        # v27 gió giông: cả bãi cỏ ngả theo một hướng (gió từ +Y sang -X… hướng mây trôi), dập dềnh theo từng cơn giật,
        # mạnh lúc giông đầu phim, dịu sau biến hình, gần lặng khi đánh nhau trên không
        sk2 = ob.shape_key_add(name="storm", from_mix=False)
        wd = Vector((-0.8, -0.6, 0.0)).normalized()
        for i, v in enumerate(me.vertices):
            p = mw @ v.co
            h = max(0.0, p.z - 0.01)
            if h <= 0:
                continue
            ang = 0.42 + 0.12 * math.sin(p.x * 0.7 + p.y * 0.5)            # mỗi khóm ngả lệch nhau chút
            off = wd * h * math.sin(ang) + Vector((0, 0, -h * (1 - math.cos(ang))))
            sk2.data[i].co = v.co + inv @ off
        for f in range(0, 1200, 4):
            storm = 1.0 if f < 240 else (0.75 if f < 330 else (0.45 if f < 780 else 0.25))
            gust = 0.5 + 0.3 * math.sin(f * 0.11) + 0.2 * math.sin(f * 0.37 + 1.3)
            sk2.value = storm * gust
            sk2.keyframe_insert("value", frame=rt(f))
    print("GRASS wind", [o.name for o in obs])


def tree_wind():
    """v28 cây đung đưa: gió giông thổi cả rừng ngả theo một hướng (cùng hướng + cơn giật với cỏ, cơn giật tới mỗi cây trễ
    theo vị trí dọc hướng gió), gió khí lúc gồng đẩy cây gần Goku ngả ra ngoài, và sóng xung kích lúc nổ biến hình (frame gốc
    296, Goku ở gốc toạ độ) quật cây ra ngoài rồi bật lại dao động tắt dần, tới cây xa trễ theo khoảng cách (~340 m/s).
    Thân + tán của mỗi cây gắn vào một empty ở gốc thân, xoay empty (trục nằm ngang)."""
    sc = bpy.context.scene
    wd = Vector((-0.8, -0.6, 0.0)).normalized()
    ax_w = Vector((0, 0, 1)).cross(wd)                      # xoay quanh trục này: ngọn cây ngả về phía wd
    trees = {}
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.endswith("_trunk") and "tree" in o.name:
            trees[o.name[:-len("_trunk")]] = o
    n = 0
    for base, tr in sorted(trees.items()):
        parts = [o for o in bpy.data.objects if o.name.startswith(base + "_") and o.parent is None and o.type == "MESH"]
        bb = [tr.matrix_world @ Vector(c) for c in tr.bound_box]
        foot = Vector((tr.matrix_world.translation.x, tr.matrix_world.translation.y, min(v.z for v in bb)))
        hgt = max(v.z for v in bb) - foot.z
        piv = bpy.data.objects.new(base + "_sway", None)
        sc.collection.objects.link(piv)
        piv.location = foot
        piv.rotation_mode = "QUATERNION"
        bpy.context.view_layer.update()
        for o in parts:
            mw = o.matrix_world.copy()
            o.parent = piv
            o.matrix_parent_inverse = piv.matrix_world.inverted()
            o.matrix_world = mw
        r = max(0.5, Vector((foot.x, foot.y)).length)
        ax_r = Vector((0, 0, 1)).cross(Vector((foot.x / r, foot.y / r, 0)))   # ngả ra xa Goku
        stiff = 1.0 / (0.6 + 0.4 * hgt / 3.5)                  # cây cao ngả ít hơn (góc), tán nặng đung chậm hơn
        lag = foot.dot(wd) / 9.0                                # cơn giật đi qua rừng ~9 m/s (frame gốc, hệ số 60/60)
        ph = (abs(foot.x) * 13.7 + abs(foot.y) * 7.3) % math.tau
        delay = r / 340.0 * 60.0
        for f in list(range(0, 1200, 4)) + list(range(290, 360, 2)):
            storm = 1.0 if f < 240 else (0.75 if f < 330 else (0.45 if f < 780 else 0.25))
            fl = f - lag
            gust = 0.5 + 0.3 * math.sin(fl * 0.11) + 0.2 * math.sin(fl * 0.37 + 1.3)
            th_w = math.radians((1.2 + 3.2 * storm * gust) * stiff + 0.6 * math.sin(f * 0.21 + ph) * storm)
            ki = 0.0
            if 120 <= f < 296:
                ki = 0.2 + 0.5 * (f - 120) / 176
            elif 296 <= f < 790:
                ki = 0.35 * max(0.0, 1 - (f - 360) / 430) if f >= 360 else 0.6
            th_r = math.radians(6.0 * ki * math.exp(-r / 14.0) * stiff)
            t = f - 296 - delay                                   # sóng xung kích: quật ra rồi dao động tắt dần
            if t > 0:
                th_r += math.radians(8.0 * math.exp(-r / 22.0) * stiff * math.exp(-t / 18.0) * math.sin(0.22 * t + 0.35) / 0.34)
            rv = ax_w * th_w + ax_r * th_r
            ang = rv.length
            piv.rotation_quaternion = (Quaternion(rv.normalized(), ang) if ang > 1e-6 else Quaternion())
            piv.keyframe_insert("rotation_quaternion", frame=rt(f))
        n += 1
    print("TREES sway", n)


def storm_leaves():
    """v29 lá cây bay trong gió giông: lá nhỏ bị cuốn theo hướng gió (cùng hướng + cơn giật với cỏ/cây), vừa trôi vừa
    chao lượn lên xuống và lật vòng; bay hết vùng thì ẩn rồi xuất hiện lại đầu gió. Lúc nổ biến hình (frame gốc 296) lá
    gần Goku bị sóng xung kích hất văng ra ngoài rồi chậm lại vì lực cản. Key theo frame gốc → rt()."""
    import bmesh, random as _r
    sc = bpy.context.scene
    rng = _r.Random(2929)
    wd = Vector((-0.8, -0.6, 0.0)).normalized()
    side = Vector((0, 0, 1)).cross(wd)
    mat = toon("storm_leaf", "#A8CC62", "#6F9A40", threshold=0.3)       # xanh vàng sáng: nổi trên nền cỏ/trời xanh
    mat.use_backface_culling = False
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((-0.075, 0, 0), (-0.02, 0.028, 0), (0.05, 0.02, 0), (0.075, 0, 0), (0.03, -0.024, 0),
                                    (-0.03, -0.022, 0))]
    bm.faces.new(vs)
    proto = bpy.data.meshes.new("storm_leaf")
    bm.to_mesh(proto)
    proto.materials.append(mat)
    T_B = 296
    n = 0
    for i in range(48):
        ob = bpy.data.objects.new(f"storm_leaf_{i}", proto)
        C_ENV.objects.link(ob)
        ob.visible_shadow = False
        ob.rotation_mode = "XYZ"
        ob.scale = (1.5,) * 3 if i % 3 else (1.0,) * 3
        f, alive = rng.uniform(0, 60), False
        sp = rng.uniform(3.0, 6.0) / 60.0                       # m/frame theo gió
        while f < 560:
            # xuất hiện ở đầu gió, cách Goku 3–10 m, bay xuyên qua khung hình
            p = -wd * rng.uniform(4, 7) + side * rng.uniform(-3.5, 3.5) + Vector((0, 0, rng.uniform(0.2, 1.4)))
            ph, spin = rng.uniform(0, math.tau), rng.uniform(0.15, 0.35)
            life = int(rng.uniform(150, 260))
            kvis([ob], rt(int(f)), True)
            vb = Vector((0, 0, 0))                              # vận tốc do sóng xung kích
            t = 0
            while t <= life and f + t < 560:
                ff = f + t
                gust = 0.5 + 0.3 * math.sin(ff * 0.11) + 0.2 * math.sin(ff * 0.37 + 1.3)
                storm = 1.0 if ff < 240 else (0.75 if ff < 330 else 0.45)
                if T_B <= ff < T_B + 2:
                    r = max(0.4, Vector((p.x, p.y)).length)
                    vb += Vector((p.x / r, p.y / r, 0.35)) * (0.35 / (1 + r / 3.0))
                vb *= 0.93                                     # lực cản không khí
                p = p + wd * sp * storm * (0.4 + 0.9 * gust) + vb
                p.z = max(0.03, p.z + 0.006 * math.sin(ff * 0.09 + ph) - 0.0015)     # chao lượn + rơi chậm
                if t % 2 == 0:
                    ob.location = p + side * 0.25 * math.sin(ff * 0.05 + ph)
                    ob.rotation_euler = (ff * spin, ph + 0.6 * math.sin(ff * 0.07), ff * spin * 0.6)
                    ob.keyframe_insert("location", frame=rt(int(ff)))
                    ob.keyframe_insert("rotation_euler", frame=rt(int(ff)))
                t += 1
            kvis([ob], rt(int(f + t)), False)
            f += t + rng.uniform(4, 30)
        n += 1
    print("LEAVES", n)


def beam_impacts():
    """v30 Death Beam trượt Goku thì phải trúng đất phía sau: bắn tia từ ngón tay Frieza qua đích (BEAM_TARGET) rồi ray-cast
    tìm điểm chạm mặt đất → loé hồng trắng, đất đá văng theo đường đạn (g thật) rồi nằm lại, cụm bụi bốc lên tan dần,
    vết cháy sém để lại trên đất, marker sfx:pop cho tiếng nổ nhỏ. Chạy sau retime (frame cuối)."""
    import bmesh, random as _r
    sc = bpy.context.scene
    fin, bt = bpy.data.objects["FRIEZA_finger_anchor"], bpy.data.objects["BEAM_TARGET"]
    rng = _r.Random(3030)
    g = 9.8 / 60.0 ** 2
    flash_m = flat("beam_hit_flash", "#FFE6FA", 1.6, energy=1.0)
    clod_m = toon("beam_clod", "#7A6A52", "#4E4434", threshold=0.3)
    scorch_m = flat("beam_scorch", "#3A2E2A", 1.0)
    dust_m = bpy.data.materials.get("burst_dust") or clod_m
    n = 0
    for k, bf in enumerate((570, 585, 600, 622, 644, 666)):
        f = int(round(rt(bf)))
        sc.frame_set(f)
        a, b = fin.matrix_world.translation.copy(), bt.matrix_world.translation.copy()
        d = (b - a).normalized()
        hit, loc, nor, _i, ob, _m = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), b + d * 1.0, d)
        if not hit or (loc - b).length > 40:
            continue
        f1 = f + 1 + int((loc - b).length / 40)            # tia đi ~40 m/frame
        sc.timeline_markers.new("sfx:pop", frame=f1)
        # loé: cầu sáng nở nhanh rồi teo
        fl = bpy.data.objects.new(f"beam_hit_flash_{k}", bpy.data.meshes.new(f"beam_hit_flash_{k}"))
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(fl.data); bm.free()
        fl.data.materials.append(flash_m)
        C_ENV.objects.link(fl); fl.visible_shadow = False
        fl.location = loc
        kvis([fl], 0, False); kvis([fl], f1, True)
        for o, sz in ((0, 0.05), (2, 0.55), (5, 0.75), (10, 0.35), (14, 0.0)):
            fl.scale = (sz, sz, sz * 0.8); fl.keyframe_insert("scale", frame=f1 + o)
        kvis([fl], f1 + 15, False)
        # vết cháy sém: đĩa tối dẹt ôm mặt đất, hiện từ lúc trúng
        bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=20, radius=1.0)
        for v in bm.verts:
            v.co *= 1 + 0.25 * math.sin(math.atan2(v.co.y, v.co.x) * 5 + k)
        sm = bpy.data.objects.new(f"beam_scorch_{k}", bpy.data.meshes.new(f"beam_scorch_{k}")); bm.to_mesh(sm.data); bm.free()
        sm.data.materials.append(scorch_m); C_ENV.objects.link(sm); sm.visible_shadow = False
        sm.location = loc + nor * 0.012
        sm.rotation_euler = nor.to_track_quat("Z", "Y").to_euler()
        sm.scale = (0.35, 0.35, 1)
        kvis([sm], 0, False); kvis([sm], f1, True)
        # đất đá văng
        for j in range(7):
            cl = bpy.data.objects.new(f"beam_clod_{k}_{j}", bpy.data.meshes.new(f"beam_clod_{k}_{j}"))
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rng.uniform(0.025, 0.05))
            bm.to_mesh(cl.data); bm.free(); cl.data.materials.append(clod_m)
            C_ENV.objects.link(cl); cl.visible_shadow = False
            ang = rng.uniform(0, math.tau)
            vh = Vector((math.cos(ang), math.sin(ang), 0)) * rng.uniform(1.0, 2.6) / 60.0
            vz = rng.uniform(2.5, 5.0) / 60.0
            T = 2 * vz / g
            kvis([cl], 0, False); kvis([cl], f1, True)
            for t in list(range(0, int(T), 2)) + [int(T)]:
                cl.location = loc + vh * t + Vector((0, 0, vz * t - 0.5 * g * t * t))
                cl.keyframe_insert("location", frame=f1 + t)
                cl.rotation_euler = (t * 0.3, t * 0.2, 0); cl.keyframe_insert("rotation_euler", frame=f1 + t)
            kvis([cl], f1 + int(T) + 40, False)
        # cụm bụi bốc lên, tan dần (dùng chung vật liệu bụi vỡ vụn của vòng bụi biến hình)
        for j in range(4):
            pf = bpy.data.objects.new(f"beam_dust_{k}_{j}", bpy.data.meshes.new(f"beam_dust_{k}_{j}"))
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(pf.data); bm.free()
            pf.data.materials.append(dust_m); C_ENV.objects.link(pf); pf.visible_shadow = False
            off = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0))
            kvis([pf], 0, False); kvis([pf], f1 + 2, True)
            for o, sz, z in ((2, 0.08, 0.05), (8, 0.3, 0.3), (20, 0.42, 0.7), (40, 0.5, 1.1), (60, 0.5, 1.4)):
                pf.location = loc + off * (1 + o / 20) + Vector((0, 0, z))
                pf.keyframe_insert("location", frame=f1 + o)
                pf.scale = (sz,) * 3; pf.keyframe_insert("scale", frame=f1 + o)
                pf.color = (1, 1, 1, 1.0 if o < 20 else max(0.0, 1 - (o - 20) / 40))
                pf.keyframe_insert("color", index=3, frame=f1 + o)
            kvis([pf], f1 + 61, False)
        n += 1
    print("BEAM impacts", n)



def foot_ground_fix():
    """v31 chân Goku lún đất: lúc gồng khí (dáng hạ thấp người) đế giày chìm ~8 cm dưới mặt đất (z = 0) suốt đoạn biến hình.
    Mỗi frame đo đáy đế giày; khi Goku đứng trên bãi cỏ quanh gốc toạ độ mà đế chìm thì nâng cả người (delta_location
    của root GOKU, không đụng key sẵn có) đúng bằng độ lún, lọc mượt để không giật."""
    sc = bpy.context.scene
    root = bpy.data.objects.get("GOKU")
    soles = [bpy.data.objects.get(n) for n in ("goku_sole_L", "goku_sole_R")]
    if not root or not all(soles):
        return
    f0, f1 = sc.frame_start, sc.frame_end
    lift = {}
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f)
        zmin = min((o.matrix_world @ Vector(c)).z for o in soles for c in o.bound_box)
        p = root.matrix_world.translation
        on_field = Vector((p.x, p.y)).length < 6.0
        lift[f] = (-zmin + 0.003) if on_field and -0.2 < zmin < 0.0 else 0.0
    keys, prev, n = sorted(lift), 0.0, 0
    for f in keys:
        v = lift[f]
        # lọc: nâng lên ngay khi lún (không để chìm), hạ xuống từ từ
        prev = v if v > prev else prev + (v - prev) * 0.35
        root.delta_location = (0.0, 0.0, prev)
        root.keyframe_insert("delta_location", index=2, frame=f)
        n += prev > 0.001
    for fc in _fcurves(root.animation_data):
        if fc.data_path == "delta_location":
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    sc.frame_set(f0)
    print("FOOT fix frames", n, "max", round(max(lift.values()), 3))
