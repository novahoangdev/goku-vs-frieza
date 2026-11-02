# Kamehameha sequence (v23): inserts 5.5 s between the punch from behind (shot 9) and the final shot. retime.py opens
# a gap KAME0..KAME1 (new frames) in every keyframe; every channel keyed on both sides is "held" at KAME0, and this file
# keys the channels that must act inside the gap: Goku's stance at the hip → Ki gathers between his palms → he thrusts
# "HA!" and fires a blue beam across the sea → Frieza blocks with crossed arms → blue blast swallows him → white flash.
#
# Runs inside build_scene.py (shared globals): kame_build() before extras (so char_shading/outline also cover the open hands),
# kame_animate() after retime_scene() (keys straight on the new frames).
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Euler, Quaternion

# shots in the sequence (new-frame offset from KAME0)
K_A, K_B, K_C, K_D, K_E, K_F = 0, 90, 160, 198, 236, 290
K_FIRE, K_HIT = 201, 246
KAME_SHOTS = [K_B, K_C, K_D, K_E, K_F]


def _kame_mat(name, cols, blend=0.42, energy=1.0):
    """Cel energy in 4 tones by view angle (white core → ice blue → blue → deep blue rim), self-emissive."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = blend
    ramp = nt.nodes.new("ShaderNodeValToRGB"); cr = ramp.color_ramp; cr.interpolation = "CONSTANT"
    cr.elements[0].color = hexc(cols[0][1])
    cr.elements[1].position = cols[1][0]
    cr.elements[1].color = hexc(cols[1][1])
    for pos, c in cols[2:]:
        e = cr.elements.new(pos); e.color = hexc(c)
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
    _energy_tail(nt, em.outputs[0], energy)
    return m


KAME_COLS = [(0.0, "#FFFFFF"), (0.34, "#B8F4FF"), (0.58, "#4CC2FF"), (0.8, "#2266F0")]


def _kame_flow_mat(name, cols, energy=1.0):
    """v26 beam body: like _kame_mat but the Facing factor is perturbed by streaky noise along the beam drifting forward (Ki
    billowing out of the hands), no longer a smooth plastic tube. Noise in Object coords (beam along +X, scale X = length)."""
    m = _kame_mat(name, cols, blend=0.3, energy=energy)     # v28 blend 0.42 → 0.3: wider white core, no longer a blue plastic tube
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    lw = next(n for n in N if n.type == "LAYER_WEIGHT")
    ramp = next(n for n in N if n.type == "VALTORGB")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (5.0, 1.6, 1.6)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    flow = N.new("ShaderNodeValue"); flow.name = "flow"
    cx = N.new("ShaderNodeCombineXYZ"); L.new(flow.outputs[0], cx.inputs["X"])
    L.new(cx.outputs[0], mp.inputs["Location"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 3.0
    L.new(mp.outputs[0], nz.inputs["Vector"])
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5
    L.new(nz.outputs["Fac"], sub.inputs[0])
    amt = N.new("ShaderNodeMath"); amt.operation = "MULTIPLY"; amt.inputs[1].default_value = 0.24
    L.new(sub.outputs[0], amt.inputs[0])
    add = N.new("ShaderNodeMath"); add.operation = "ADD"; add.use_clamp = True
    L.new(lw.outputs["Facing"], add.inputs[0]); L.new(amt.outputs[0], add.inputs[1])
    L.new(add.outputs[0], ramp.inputs["Fac"])
    return m


def _open_hand(side, sx, parent, col):
    """Open, slightly cupped hand (same axes as goku_fist): origin at the wrist, fingers along -Z, palm facing (-sx, 0, 0),
    thumb on the -Y side."""
    pn = -sx
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    for v in bm.verts:
        q = v.co.copy()
        sq = lambda x: math.copysign(abs(x) ** 0.7, x)
        y, z, x = sq(q.y) * 0.044, sq(q.z) * 0.04 - 0.042, sq(q.x) * 0.019
        x += pn * 0.012 * (y / 0.044) ** 2          # cupping: palm edges curve toward the palm
        v.co = Vector((x, y, z))
    for y0, L, r in ((-0.03, 0.05, 0.0128), (-0.01, 0.056, 0.0132), (0.01, 0.053, 0.0128), (0.029, 0.043, 0.0112)):
        pts = [Vector((pn * 0.002, y0, -0.07)), Vector((pn * 0.008, y0 * 1.06, -0.07 - 0.55 * L)),
               Vector((pn * 0.02, y0 * 1.1, -0.07 - L))]
        goku_tube(bm, pts, lambda t, r=r: r * (1.0 - 0.15 * t), sides=10)
    goku_tube(bm, [Vector((pn * 0.006, -0.034, -0.02)), Vector((pn * 0.02, -0.058, -0.04)),
                   Vector((pn * 0.03, -0.068, -0.066))], lambda t: 0.0155 * (1.0 - 0.2 * t), sides=10)
    ob = _obj(f"goku_palm_{side}", bm, M["skin"], col, outline=0.0035)
    ob.parent = parent
    return ob


def kame_build():
    G["kwrist"], G["palms"] = {}, []
    for side, sx in (("R", -1), ("L", 1)):
        w = empty(f"GOKU_kwrist_{side}", C_GOKU, G[f"el_{side}"], (0, 0, -0.15), 0.03)
        G["kwrist"][side] = w
        G["palms"].append(_open_hand(side, sx, w, C_GOKU))
    G["fists"] = [bpy.data.objects[f"goku_{p}_{s}"] for p in ("fist", "fingers", "thumb") for s in "RL"]
    kvis(G["palms"], 0, False)

    M["kame"] = _kame_mat("kame", KAME_COLS)
    M["kame_soft"] = _kame_mat("kame_soft", [(0.0, "#FFFFFF"), (0.16, "#DDF8FF"), (0.38, "#8FE0FF"), (0.64, "#45A8FF"),
                                              (0.84, "#2058E0")], blend=0.3)
    core = empty("KAME_core", C_ENV, G["chest"], (0, 0, 0), 0.05)
    # v26 Ki sphere: small white core + many cyan → blue layers (before it was almost solid white, like a rice ball)
    M["kame_ball"] = _kame_mat("kame_ball", [(0.0, "#FFFFFF"), (0.07, "#D8FAFF"), (0.18, "#78DBFF"), (0.36, "#3393FA"),
                                              (0.58, "#1E55DC")], blend=0.42)
    ball = sphere("kame_ball", 1.0, M["kame_ball"], C_ENV, seg=32, outline=0)
    ball.parent = core
    # crackling sparks around the sphere: a few thin zigzag lines, changing direction every 3 frames
    sparks = []
    rng = random.Random(23)
    for i in range(7):
        bm = bmesh.new()
        pts, p = [], Vector((0, 0, 0.9))
        for k in range(6):
            pts.append(p.copy())
            p += Vector((rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35), 0.3))
        goku_tube(bm, pts, lambda t: 0.05 * (1 - 0.6 * t), sides=5)
        sp = _obj(f"kame_spark_{i}", bm, M["kame_soft"], C_ENV, smooth=False)
        sp.parent = ball
        sparks.append(sp)
    light = bpy.data.lights.new("kame_light", "POINT")
    light.color, light.energy, light.shadow_soft_size = (0.45, 0.78, 1.0), 0.0, 0.05
    lo = bpy.data.objects.new("kame_light", light); C_LIGHT.objects.link(lo); lo.parent = core
    # beam body: unit cylinder along +X (origin at the hands), stretched via scale; beam head + muzzle are two spheres
    bm = bmesh.new()
    seg, rings = 40, 48
    rows = []
    for j in range(rings + 1):
        x = j / rings
        rows.append([bm.verts.new((x, math.cos(math.tau * i / seg), math.sin(math.tau * i / seg))) for i in range(seg)])
    for a, b in zip(rows, rows[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    M["kame_flow"] = _kame_flow_mat("kame_flow", KAME_COLS)
    beam = _obj("kame_beam", bm, M["kame_flow"], C_ENV, outline=0)
    beam.rotation_mode = "QUATERNION"
    head = sphere("kame_head", 1.0, M["kame"], C_ENV, seg=32, outline=0)
    boom = sphere("kame_boom", 1.0, M["kame_soft"], C_ENV, seg=48, outline=0)
    tex = bpy.data.textures.new("kame_boom_n", "CLOUDS"); tex.noise_scale, tex.noise_depth = 0.32, 1
    tc = empty("KAME_boom_tc", C_CTRL, None, (0, 0, 0), 0.2)      # noise coords drifting over time: billowing blast
    dsp = boom.modifiers.new("lumpy", "DISPLACE")
    dsp.texture, dsp.strength, dsp.mid_level = tex, 0.3, 0.5
    dsp.texture_coords, dsp.texture_coords_object = "OBJECT", tc
    # sparks around the blast (children of the blast: scale with it), toggled randomly every 3 frames
    bolts = []
    rng = random.Random(57)
    for i in range(10):
        bm = bmesh.new()
        pts, p = [], Vector((0, 0, 0.85))
        for _ in range(7):
            pts.append(p.copy())
            p += Vector((rng.uniform(-0.22, 0.22), rng.uniform(-0.22, 0.22), 0.13))
        goku_tube(bm, pts, lambda t: 0.018 * (1 - 0.5 * t), sides=5)
        b = _obj(f"kame_bolt_{i}", bm, M["kame_soft"], C_ENV, smooth=False)
        b.parent = boom
        b.visible_shadow = False
        bolts.append(b)
    kvis(bolts, 0, False)
    # v28 thin shockwave ring (0.035 → 0.014; scaled up 4.6× the tube was 16 cm thick like a hula hoop), breaks up as it spreads
    ring = torus("kame_ring", 1.0, 0.014, _ripple_mat("kame_ring_m", "#E6FAFF"), C_ENV, seg=96, ring=6, outline=0)
    ring.rotation_mode = "QUATERNION"
    for o in [ball, beam, head, boom, ring] + sparks:
        o.visible_shadow = False
    kvis([ball, beam, head, boom, ring] + sparks, 0, False)
    G["kame"] = dict(core=core, ball=ball, sparks=sparks, light=lo, beam=beam, head=head, boom=boom, ring=ring,
                     bolts=bolts, boom_tc=tc)
    kame_water_build()


# ── 2-joint IK for Goku's arms in chest space (shoulder: free XYZ Euler, elbow: bends on rx only) ──
def _arm_ik(sx, wrist):
    d = GOKU_DIM
    p_sh = Vector((sx * d["sh_x"], 0, d["sh_z"]))
    a = Vector((sx * 0.005, 0, -d["upper"]))
    to = wrist - p_sh
    dist = min(to.length, 0.999 * math.sqrt(a.length_squared + 0.15 ** 2 + 2 * a.length * 0.15))
    # |a + Rx(θ)·(0,0,-0.15)|² = |a|² + 0.15² + 2·0.2·0.15·cosθ  (a almost along -Z)
    c = (dist ** 2 - a.length_squared - 0.15 ** 2) / (2 * d["upper"] * 0.15)
    th = -math.acos(max(-1.0, min(1.0, c)))
    v = a + Vector((0, 0.15 * math.sin(th), -0.15 * math.cos(th)))
    u = to.normalized() * v.length
    rmin = v.rotation_difference(u).to_matrix()
    best = None
    for k in range(72):                               # rotate about the shoulder→wrist axis: pick a low, outward elbow
        rq = Quaternion(u.normalized(), math.radians(k * 5)).to_matrix() @ rmin
        e = rq @ a
        score = -e.z + 0.6 * sx * e.x + 0.25 * e.y
        if best is None or score > best[0]:
            best = (score, rq)
    rsh = best[1]
    rel = Euler((th, 0, 0)).to_matrix()
    return rsh, rel, (p_sh + rsh @ (a + rel @ Vector((0, 0, -0.15))) - wrist).length


def _hand_basis(sx, fingers, normal):
    f = fingers.normalized()
    n = (normal - f * normal.dot(f)).normalized()
    x = -sx * n
    z = -f
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


def kame_pose(f, chest, hips, head, arms, legs):
    """arms: {side: (wrist, finger direction, palm normal)} in chest space."""
    rot = {}
    for side, sx in (("R", -1), ("L", 1)):
        wrist, fing, nrm = arms[side]
        rsh, rel, err = _arm_ik(sx, Vector(wrist))
        if err > 0.02:
            print(f"KAME ik {side}@{f} off by {err:.3f}")
        rw = (rsh @ rel).inverted() @ _hand_basis(sx, Vector(fing), Vector(nrm))
        rot[f"sh_{side}"] = tuple(math.degrees(x) for x in rsh.to_euler("XYZ"))
        rot[f"el_{side}"] = (math.degrees(rel.to_euler("XYZ").x), 0, 0)
        G["kwrist"][side].rotation_euler = rw.to_euler("XYZ")
        G["kwrist"][side].keyframe_insert("rotation_euler", frame=f)
    pose(G, f, "stand", chest=chest, hips=hips, head=head, **rot, **legs)


def _set_interp(objs, f0, f1, mode):
    for o in objs:
        for ad in (o.animation_data, getattr(getattr(o, "data", None), "animation_data", None)):
            if not ad or not ad.action:
                continue
            for fc in _fcurves(ad):
                for kp in fc.keyframe_points:
                    if f0 <= kp.co.x <= f1:
                        kp.interpolation = mode


def kame_animate():
    K = KAME0
    k = lambda o: K + o
    ka = G["kame"]
    # placement: Goku hovers over the sea facing +X, Frieza has struggled back up 12 m away
    fr_end = chase_path(1.0) + Vector((0, 0, 0.5))
    gp = fr_end + Vector((-1.0, 0, 0.25))
    gp.z = SEA_TOP + 1.3                      # v25: skims the sea surface (feet 1.3 m above the water) → visible water reaction
    fp = gp + Vector((12.0, 0.6, 0.7))
    for o in (0, 90, 196):
        root(G, k(o), gp, 90)
    root(G, k(K_FIRE), gp + Vector((-0.05, 0, 0.02)), 90)
    root(G, k(K_FIRE + 4), gp + Vector((-0.14, 0, 0.03)), 90)        # recoils from the kickback, keeps being pushed back while the beam fires
    root(G, k(K_FIRE + 14), gp + Vector((-0.3, 0, 0.03)), 90)
    root(G, k(306), gp + Vector((-0.44, 0, 0.03)), 90)
    root(G, k(329), gp + Vector((-0.47, 0, 0.03)), 90)
    for f in range(k(0), k(330), 6):                                  # gentle hip bob while hovering
        kloc(G["hips"], f, Vector((0, 0, GOKU_DIM["hips"] + 0.02 * math.sin(math.tau * (f - K) / 72))))

    # ── pose ── (chest space: face -Y, right -X, up +Z)
    legs_c = dict(hip_R=(-12, 8, 0), kn_R=(28, 0, 0), hip_L=(18, -6, 0), kn_L=(38, 0, 0))
    legs_f = dict(hip_R=(-34, 8, 0), kn_R=(42, 0, 0), hip_L=(32, -8, 0), kn_L=(22, 0, 0))
    pose(G, k(4), "hero", head=(-6, 0, 0))
    fing_c = Vector((-0.35, -1.0, 0.05))
    for o, pc, tw in ((22, Vector((-0.15, 0.0, 0.02)), -28), (150, Vector((-0.16, 0.02, 0.015)), -34),
                      (196, Vector((-0.17, 0.04, 0.01)), -40)):
        back = -fing_c.normalized() * 0.045
        kame_pose(k(o), chest=(4, 0, tw), hips=(0, 0, -10), head=(8, 0, -tw * 0.85),
                  arms={"R": (pc + back + Vector((0, 0, -0.05)), fing_c, Vector((0, 0, 1))),
                        "L": (pc + back + Vector((0, 0, 0.05)), fing_c, Vector((0, 0, -1)))}, legs=legs_c)
        kloc(ka["core"], k(o), pc + Vector((0, -0.01, 0)))
    for o in (K_FIRE, 329):
        kame_pose(k(o), chest=(6, 0, 0), hips=(0, 0, 0), head=(-2, 0, 0),
                  arms={"R": (Vector((0, -0.29, 0.228)), Vector((-0.25, 0, 1)), Vector((0, -1, 0))),
                        "L": (Vector((0, -0.29, 0.172)), Vector((0.25, 0, -1)), Vector((0, -1, 0)))}, legs=legs_f)
        kloc(ka["core"], k(o), Vector((0, -0.4, 0.2)))
    pose(G, KAME1, "hero", hips=(0, 0, 0), head=(-6, 0, 0))      # final shot: back to the hero pose right at the cut
    kvis(G["fists"], k(13), True)
    kvis(G["palms"], k(14), True); kvis(G["fists"], k(14), False)
    kvis(G["palms"], KAME1, False); kvis(G["fists"], KAME1, True)
    # expression: gritted teeth + fierce eyes while gathering Ki, mouth open yelling "HA!", restored after the sequence
    kvis(G["grit"] + G["eyes_fierce"], k(10), True); kvis(G["mouth"] + G["eyes_ssj"] + G["mouth_open"], k(10), False)
    kvis(G["mouth_open"], k(K_FIRE - 2), True); kvis(G["grit"], k(K_FIRE - 2), False)
    kvis(G["mouth_open"], KAME1, False); kvis(G["grit"] + G["eyes_fierce"], KAME1, False)
    kvis(G["mouth"] + G["eyes_ssj"], KAME1, True)
    # hair shakes harder in the Ki stream, flung back on firing
    hs = G["hair_ssj"]
    rng = random.Random(31)
    for f in range(k(0), k(330), 3):
        o = f - K
        amp = 1.2 + 2.6 * min(1.0, o / 190) if o < K_FIRE else 3.6
        back = 0.0 if o < K_FIRE else -8.0
        hs.rotation_euler = (rad(rng.uniform(-amp, amp) + back), rad(rng.uniform(-amp, amp)), rad(rng.uniform(-amp, amp) * 0.5))
        hs.keyframe_insert("rotation_euler", frame=f)

    # ── Frieza: struggles up, freezes, crosses his arms to block, then gets swallowed ──
    root(F, k(0), fp, 270); root(F, k(K_HIT), fp + Vector((0.1, 0, 0)), 270)
    root(F, k(K_HIT + 16), fp + Vector((1.6, 0.1, 0.4)), 270, -25)
    pose(F, k(0), "shock")
    pose(F, k(K_C + 20), "shock", head=(-16, 0, 0))
    pose(F, k(K_E - 4), "cross")
    pose(F, k(K_HIT + 2), "hit")
    kvis(F["eyes_shock"] + F["mouth_open"], k(0), True)
    kvis(F["eyes_hit"] + F["pain"] + F["eyes"] + F["mouth"] + F["eyes_angry"] + F["snarl"], k(0), False)
    kvis(F["eyes_hit"] + F["pain"], k(K_HIT), True); kvis(F["eyes_shock"] + F["mouth_open"], k(K_HIT), False)
    # tail keeps swaying during the insert (the original keys were held at KAME0)
    for f in range(k(0), k(K_HIT + 20), 20):
        for i, seg in enumerate(F["tail"]):
            krot(seg, f, (-12 - 6 * math.sin(f / 40 + i * 0.7), 0, 14 * math.sin(f / 33 + i * 0.5)))
    fr_all = [o for o in bpy.data.objects if o.name.startswith("fr_") and o.type in {"MESH", "FONT", "CURVE"}]
    scene.frame_set(k(K_HIT))
    vis_now = {o.name: not o.hide_render for o in fr_all}
    hide = [o for o in fr_all if vis_now[o.name]]
    kvis(hide, k(K_HIT + 13), True)             # objects never keyed for visibility: without this key they'd be hidden from frame 0
    kvis(hide, k(K_HIT + 14), False)

    # ── Ki sphere ──
    def kscale(o, f, s):
        o.scale = (s, s, s); o.keyframe_insert("scale", frame=f)
    ball = ka["ball"]
    kvis([ball], k(20), True)
    for o, s in ((20, 0.0), (40, 0.03), (90, 0.05), (160, 0.072), (196, 0.085), (K_FIRE, 0.12), (K_FIRE + 5, 0.16),
                 (290, 0.14), (310, 0.06), (322, 0.0)):
        kscale(ball, k(o), s)
    rng = random.Random(41)
    for f in range(k(24), k(K_FIRE), 3):                              # pulsing + sparks change direction
        sp = ka["sparks"]
        for i, o in enumerate(sp):
            on = rng.random() < 0.55
            o.hide_render = o.hide_viewport = not on
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
            o.rotation_euler = (rng.uniform(0, 6.28), rng.uniform(0, 6.28), rng.uniform(0, 6.28))
            o.keyframe_insert("rotation_euler", frame=f)
            s = rng.uniform(1.1, 1.8); o.scale = (s, s, s); o.keyframe_insert("scale", frame=f)
    kvis(ka["sparks"], k(K_FIRE), False)
    lt = ka["light"].data
    for o, e in ((0, 0), (20, 0), (90, 25), (160, 60), (196, 90), (K_FIRE, 260), (290, 200), (318, 0)):
        lt.energy = e; lt.keyframe_insert("energy", frame=k(o))

    # ── beam: origin at the sphere when firing, flies straight to Frieza's chest ──
    scene.frame_set(k(K_FIRE + 1))
    p0 = ka["core"].matrix_world.translation.copy()
    scene.frame_set(k(K_HIT))
    tgt = bpy.data.objects["FRIEZA_chest_anchor"].matrix_world.translation.copy()
    dv = tgt - p0
    L, dvn = dv.length, dv.normalized()
    q = Vector((1, 0, 0)).rotation_difference(dvn)
    beam, head = ka["beam"], ka["head"]
    beam.location, beam.rotation_quaternion = p0, q
    kvis([beam, head], k(K_FIRE + 1), True)
    for o, ln, r in ((K_FIRE + 1, 0.05, 0.05), (K_FIRE + 5, 0.9, 0.15), (K_E, L * 0.62, 0.2), (K_HIT, L, 0.21),
                     (290, L, 0.2), (306, L, 0.08), (318, L, 0.0)):
        beam.scale = (ln, r, r); beam.keyframe_insert("scale", frame=k(o))
        if o <= K_HIT:
            head.location = p0 + dvn * ln; head.keyframe_insert("location", frame=k(o))
            kscale(head, k(o), r * 1.45)
    kscale(head, k(K_HIT + 2), 0.0)
    kvis([beam, head], k(320), False)
    _set_interp([beam, head], k(0), k(330), "LINEAR")
    fv = M["kame_flow"].node_tree.nodes["flow"].outputs[0]   # Ki streaks drifting forward (texture -X = forward)
    fv.default_value = 0.0; fv.keyframe_insert("default_value", frame=k(K_FIRE))
    fv.default_value = -60.0; fv.keyframe_insert("default_value", frame=k(330))
    _set_interp([M["kame_flow"].node_tree], k(0), k(330), "LINEAR")
    # beam origin follows both hands (Goku is pushed back by recoil the whole time), tip stays at the beam head / Frieza's chest
    cores = []
    for f in range(k(K_FIRE + 1), k(320), 2):
        scene.frame_set(f)
        c = ka["core"].matrix_world.translation.copy()
        h = head.matrix_world.translation.copy() if f <= k(K_HIT) else tgt
        cores.append((f, c, h, beam.scale[1]))
    for f, c, h, r in cores:
        d = h - c
        beam.location = c; beam.keyframe_insert("location", frame=f)
        beam.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(d.normalized())
        beam.keyframe_insert("rotation_quaternion", frame=f)
        beam.scale = (max(0.05, d.length), r, r); beam.keyframe_insert("scale", frame=f)
    # ── blast: blue sphere swells to swallow Frieza + shockwave ring ──
    boom, ring = ka["boom"], ka["ring"]
    boom.location = tgt
    ring.location, ring.rotation_quaternion = tgt, Vector((0, 0, 1)).rotation_difference(dvn)
    kvis([boom, ring], k(K_HIT), True)
    for o, s in ((K_HIT, 0.08), (K_HIT + 6, 0.8), (270, 1.4), (K_F, 2.1), (315, 3.3), (329, 3.8)):
        kscale(boom, k(o), s)
    for o, s in ((K_HIT, 0.25), (K_HIT + 14, 2.6), (K_HIT + 32, 4.6)):
        kscale(ring, k(o), s)
    kvis([ring], k(K_HIT + 33), False)
    for o, a in ((K_HIT, 1.0), (K_HIT + 12, 0.85), (K_HIT + 32, 0.0)):
        _kalpha(ring, k(o), a)
    tc = ka["boom_tc"]
    kloc(tc, k(K_HIT), tgt); kloc(tc, k(330), tgt + Vector((0.6, -0.4, 1.4)))
    rng = random.Random(61)
    for f in range(k(K_HIT + 2), KAME1, 3):
        for b in ka["bolts"]:
            on = rng.random() < 0.5
            b.hide_render = b.hide_viewport = not on
            b.keyframe_insert("hide_render", frame=f); b.keyframe_insert("hide_viewport", frame=f)
            b.rotation_euler = (rng.uniform(0, 6.28), rng.uniform(0, 6.28), rng.uniform(0, 6.28))
            b.keyframe_insert("rotation_euler", frame=f)
    kvis(ka["bolts"], KAME1, False)
    kvis([boom], KAME1, False)
    _set_interp([beam, head, boom, ring, ball, tc], k(0), k(330), "LINEAR")
    kame_water_animate(gp, p0, tgt, [(o, ln) for o, ln, r in ((K_FIRE + 1, 0.05, 0), (K_FIRE + 5, 0.9, 0), (K_E, L * 0.62, 0), (K_HIT, L, 0))], dvn)

    # ── camera ──
    cam, cd = scene.camera, scene.camera.data
    names = {"gc": "GOKU_chest_anchor", "gh": "GOKU_head_anchor", "fh": "FRIEZA_head_anchor", "fc": "FRIEZA_chest_anchor"}
    prev = None
    cuts = {k(o) for o in KAME_SHOTS}
    for f in range(k(0), KAME1):
        scene.frame_set(f)
        A = {n: bpy.data.objects[o].matrix_world.translation.copy() for n, o in names.items()}
        core = ka["core"].matrix_world.translation.copy()
        o = f - K
        if o < K_B:                          # A: "Ka…me…" low medium shot front-right, slow push-in
            t = ease(o / (K_B - 1))
            eye = A["gc"] + lerp(Vector((2.6, -2.15, -0.12)), Vector((1.85, -1.55, -0.1)), t)   # water surface below the feet visible too
            tgt_, lens, roll = A["gc"] + lerp(Vector((0, -0.05, -0.62)), Vector((0, -0.05, -0.4)), t), lerp(27, 31, t), lerp(-3, 2, t)
        elif o < K_C:                        # B: "Ha…me…" close on both hands gathering Ki, Goku's face above
            t = ease((o - K_B) / (K_C - K_B - 1))
            eye = core + lerp(Vector((0.95, -0.72, 0.22)), Vector((0.78, -0.6, 0.18)), t)
            tgt_, lens, roll = lerp(core, A["gh"], 0.55), 34, lerp(4, 0, t)
        elif o < K_D:                        # C: Frieza freezes (seen from Goku's side)
            t = ease((o - K_C) / (K_D - K_C - 1))
            eye = A["fh"] + lerp(Vector((-1.05, -0.38, 0.03)), Vector((-0.82, -0.3, 0.02)), t)
            tgt_, lens, roll = A["fh"] + Vector((0, 0, -0.04)), 42, 0
        elif o < K_E:                        # D: "HA!" over Goku's shoulder, beam shoots across the sea
            t = ease((o - K_D) / (K_E - K_D - 1))
            eye = A["gc"] + lerp(Vector((-1.1, -0.55, 0.3)), Vector((-1.4, -0.62, 0.36)), t)
            tgt_, lens, roll = A["gc"] + Vector((3.2, 0.2, 0.12)), 30, lerp(0, -3, t)
        elif o < K_F:                        # E: beam hits, Frieza crosses his arms to block then gets swallowed
            t = ease((o - K_E) / (K_F - K_E - 1))
            # v26 pulled back from the blast: camera used to be 2.6 m away so the sphere (radius up to 2 m) + glow whited out the frame ~0.5 s
            eye = tgt + lerp(Vector((1.9, -4.6, 0.5)), Vector((2.5, -5.6, 0.8)), t)
            tgt_, lens, roll = tgt + Vector((-1.4, 0.2, 0.3)), 24, lerp(0, 4, t)
        else:                                # F: wide shot behind Goku, blast sphere swelling over the sea
            t = ease((o - K_F) / (330 - K_F - 1))
            # v26 camera moved back-right: Goku's full back in the lower-left third, beam leads the eye to the blast (Goku was cut off at the left edge)
            eye = A["gc"] + lerp(Vector((-3.1, -1.25, 0.55)), Vector((-3.6, -1.45, 0.75)), t)
            tgt_, lens, roll = lerp(A["gc"], tgt, 0.36) + Vector((0, 0, 0.35)), 24, 0
        qq = (tgt_ - eye).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), rad(roll))
        e = qq.to_euler("XYZ", prev) if (prev and f not in cuts) else qq.to_euler("XYZ")
        if f in cuts and prev is not None:    # hold the previous shot right up to the cut (motion blur doesn't smear across the cut)
            cam.keyframe_insert("location", frame=f - 0.4); cam.keyframe_insert("rotation_euler", frame=f - 0.4)
            cd.keyframe_insert("lens", frame=f - 0.4)
        prev = e
        cam.location, cam.rotation_euler, cd.lens = eye, e, lens
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
        cd.keyframe_insert("lens", frame=f)
    cam.keyframe_insert("location", frame=KAME1 - 0.4); cam.keyframe_insert("rotation_euler", frame=KAME1 - 0.4)
    cd.keyframe_insert("lens", frame=KAME1 - 0.4)
    _set_interp([cam], k(0), KAME1, "LINEAR")

    # ── FX tracks for the app ──
    fx = bpy.data.objects["FX"]
    def key(track, o, v, absolute=False):
        fx[track] = float(v)
        fx.keyframe_insert(f'["{track}"]', frame=o if absolute else k(o))
    for o, v in ((0, 0.8), (K_B, 1.0), (K_C - 1, 1.15), (K_C, 0.9), (K_D - 1, 0.85), (K_FIRE, 1.1), (K_E, 0.95),
                 (K_F, 0.9), (329, 0.9)):
        key("aura", o, v)
    for o, v in ((0, 0), (K_FIRE - 1, 0), (K_FIRE, 0.6), (K_FIRE + 6, 0), (K_HIT - 1, 0), (K_HIT, 0.9), (K_HIT + 8, 0),
                 (316, 0), (329, 1.0)):
        key("flash", o, v)
    key("flash", KAME1 + 12, 0, absolute=True)
    for o, v in ((0, 0), (K_B, 0.08), (K_C - 1, 0.25), (K_C, 0), (K_D - 1, 0), (K_FIRE, 0.8), (K_E, 0.45),
                 (K_HIT, 1.0), (K_F, 0.35), (329, 0.15)):
        key("shake", o, v)
    for o, v in ((0, 0), (K_FIRE - 1, 0), (K_FIRE, 0.1), (K_FIRE + 14, 0), (K_HIT - 1, 0), (K_HIT, 0.12), (K_HIT + 16, 0)):
        key("punch", o, v)
    for o, v in ((0, 0), (K_FIRE - 1, 0), (K_FIRE, 1.0), (K_E, 0.6), (K_HIT, 1.0), (K_F, 0)):
        key("speedlines", o, v)
    for o, v in ((0, 0), (K_HIT, 1), (K_HIT + 3, 0)):
        key("impact", o, v)
    for o, v in ((0, 0), (K_FIRE - 1, 0), (K_FIRE, 0), (K_FIRE + 30, 1100), (K_FIRE + 31, 0)):
        key("shock_r", o, v)
    for o, v in ((0, 0), (K_FIRE - 1, 0), (K_FIRE, 1), (K_FIRE + 30, 0)):
        key("shock_k", o, v)
    for t_ in ("beam", "blast", "title"):
        key(t_, 0, 0)
    key("timescale", 0, 1)
    for fc in _fcurves(fx.animation_data):
        name = fc.data_path[2:-2]
        for kp in fc.keyframe_points:
            if k(0) <= kp.co.x <= KAME1 + 12:
                kp.interpolation = "CONSTANT" if name == "impact" else "LINEAR"

    # ── markers: cut, haptic, sound ──
    def mk(o, name):
        scene.timeline_markers.new(name, frame=int(k(o)))
    mk(0, "cut")
    for o in KAME_SHOTS:
        mk(o, "cut")
    f, gap = 24.0, 12.0
    while f < K_FIRE - 3:
        mk(int(f), "haptic:light")
        f += gap
        gap = max(3.5, gap * 0.9)
    mk(K_FIRE, "haptic:heavy"); mk(K_HIT, "haptic:heavy"); mk(K_HIT + 5, "haptic:rigid"); mk(K_HIT + 12, "haptic:rigid")
    mk(0, "kame:start"); mk(330, "kame:end")
    mk(20, "kame:charge"); mk(K_FIRE, "kame:fire"); mk(K_HIT, "kame:hit")
    print("KAME", KAME0, KAME1, f"beam {L:.1f} m")


# ── water reaction (v25): Goku skims the sea surface, so the Ki pressure pushes the water. Real gravity 9.8 m/s² at 60 fps ──
SEA_TOP = -0.65 + 0.012                       # top of the "sea" box (z -0.7, 0.1 thick) + a bit to avoid z-fighting
G_ACC = 9.8 / 60.0 ** 2                       # m/frame²
FOAM_COLS = [(0.0, "#F4FFFD"), (0.45, "#D2F1EE"), (0.78, "#93CFCF")]


def _ripple_mat(name, col="#E2F7F4"):
    """v27 foam: no longer a solid white tube like a marker stroke — the foam breaks into noise-driven patches, and as the ring
    spreads (object color alpha drops 1 → 0) the noise threshold rises so the foam crumbles and vanishes, like real foam on water."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial")
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = hexc(col)
    tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.5; nz.inputs["Detail"].default_value = 2.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    oi = N.new("ShaderNodeObjectInfo")
    thr = N.new("ShaderNodeMath"); thr.operation = "MULTIPLY_ADD"          # threshold = 0.85 - 0.5·alpha
    thr.inputs[1].default_value, thr.inputs[2].default_value = -0.5, 0.85
    L.new(oi.outputs["Alpha"], thr.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"
    L.new(nz.outputs["Fac"], gt.inputs[0]); L.new(thr.outputs[0], gt.inputs[1])
    L.new(gt.outputs[0], mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return m


def _kalpha(o, f, a):
    o.color = (1, 1, 1, a)
    o.keyframe_insert("color", index=3, frame=f)


def _foam_ring(name, mat, seed=0):
    """Foam ring on the water: slightly wobbly radius + uneven band width (not compass-perfect)."""
    ob = torus(name, 1.0, 0.035, mat, C_ENV, seg=96, ring=6, scale=(1, 1, 0.3), outline=0)
    rng = random.Random(500 + seed)
    p1, p2, p3 = (rng.uniform(0, math.tau) for _ in range(3))
    for v in ob.data.vertices:
        a = math.atan2(v.co.y, v.co.x)
        rr = math.hypot(v.co.x, v.co.y)
        wob = 1 + 0.035 * math.sin(3 * a + p1) + 0.02 * math.sin(7 * a + p2)
        th = 0.75 + 0.45 * (0.5 + 0.5 * math.sin(5 * a + p3))   # foam band thick in places, thin in others
        r_new = (1.0 + (rr - 1.0) * th) * wob
        v.co.x, v.co.y = math.cos(a) * r_new, math.sin(a) * r_new
    ob.visible_shadow = False
    return ob


def _crown(name, mat, rng, n=26, top=1.0):
    """Water crown: a low flared wall of water + separate pointed jets spraying outward like water blasted up by an explosion."""
    bm = bmesh.new()
    lo, mid = [], []
    for i in range(n):
        a = math.tau * i / n
        h = top * rng.uniform(0.28, 0.42)
        lo.append(bm.verts.new((math.cos(a), math.sin(a), 0.0)))
        mid.append(bm.verts.new((math.cos(a) * 1.12, math.sin(a) * 1.12, h)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], mid[j], mid[i]))
        if rng.random() < 0.8:                    # jets: sharp tips angled outward, uneven heights
            am = math.tau * (i + 0.5 + rng.uniform(-0.25, 0.25)) / n
            rr = rng.uniform(1.3, 1.65)
            tip = bm.verts.new((math.cos(am) * rr, math.sin(am) * rr, top * rng.uniform(0.7, 1.4)))
            bm.faces.new((mid[i], mid[j], tip))
    ob = _obj(name, bm, mat, C_ENV, smooth=False, outline=0)
    ob.visible_shadow = False
    return ob


def _wake_mesh(name, mat, rng, n=48):
    """Two jagged foam walls along +X (0..1): water under the beam path blown apart to both sides."""
    bm = bmesh.new()
    for side in (-1, 1):
        for i in range(n):
            x0, x1 = i / n, (i + 1) / n
            xm = (x0 + x1) / 2 + rng.uniform(-0.3, 0.3) / n
            h = rng.uniform(0.45, 1.0) * (1 - 0.65 * max(0.0, min(1.0, (x0 - 0.72) / 0.28)))   # near the blast: the crown takes over
            w0 = side * 0.18
            a = bm.verts.new((x0, w0, 0)); b = bm.verts.new((x1, w0, 0))
            t = bm.verts.new((xm, side * (0.18 + 0.32 * h), h))
            bm.faces.new((a, b, t))
    ob = _obj(name, bm, mat, C_ENV, smooth=False, outline=0)
    ob.visible_shadow = False
    return ob


def kame_water_build():
    M["foam"] = _kame_mat("kame_foam", FOAM_COLS, blend=0.35, energy=0.0)
    rng = random.Random(77)
    M["ripple"] = _ripple_mat("kame_ripple")
    # v29 droplets: bright core, cyan rim (they used to share the white foam → droplets looked like white eggs)
    M["drop"] = _kame_mat("kame_drop_m", [(0.0, "#F2FFFD"), (0.35, "#B4E6E6"), (0.7, "#5FB2C2")], blend=0.3, energy=0.0)
    # v28 water crown: real sea-water tones (pale ice-blue core → cyan → blue rim); it used to be almost foam-white
    # so the close-up of the blast burned the whole frame white
    M["crown"] = _kame_mat("kame_crown_m", [(0.0, "#D8F5F2"), (0.3, "#9AD6D8"), (0.62, "#4DA3B6"), (0.85, "#2E7F9C")],
                           blend=0.35, energy=0.0)
    W = dict(ripples=[_foam_ring(f"kame_ripple_{i}", M["ripple"], i) for i in range(5)],
             drops=[], wake=_wake_mesh("kame_wake", M["foam"], rng),
             crown=_crown("kame_crown", M["crown"], rng), crown2=_crown("kame_crown2", M["crown"], rng, n=28, top=0.6),
             wave=_foam_ring("kame_wave", M["ripple"], 9))
    # beam reflection on the water: a strip tapered at both ends along +X (0..1) + a round pool of light under the blast
    M["glint"] = flat("kame_glint", "#BDF2FF", 1.0, energy=0.55)
    bm = bmesh.new()
    n = 40
    up, dn = [], []
    for i in range(n + 1):
        x = i / n
        w = 0.5 * math.sin(math.pi * min(1.0, x * 1.15)) ** 0.5 if x < 0.87 else 0.5 * (1 - x) / 0.13
        up.append(bm.verts.new((x, w, 0))); dn.append(bm.verts.new((x, -w, 0)))
    for i in range(n):
        bm.faces.new((dn[i], dn[i + 1], up[i + 1], up[i]))
    W["glint"] = _obj("kame_glint", bm, M["glint"], C_ENV, smooth=False, outline=0)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.0)
    W["pool"] = _obj("kame_pool", bm, M["glint"], C_ENV, smooth=False, outline=0)
    for o in (W["glint"], W["pool"]):
        o.visible_shadow = False
        kvis([o], 0, False)
    # steam: the blast right at the sea surface boils the water into steam → cel cloud puffs swell around the blast base and rise
    M["steam"] = _kame_mat("kame_steam", [(0.0, "#F2FAFA"), (0.5, "#D6E9EC"), (0.8, "#A9C6CC")], blend=0.45, energy=0.0)
    stex = bpy.data.textures.new("kame_steam_n", "CLOUDS"); stex.noise_scale, stex.noise_depth = 0.45, 1
    W["steam"] = []
    for i in range(9):
        st = sphere(f"kame_steam_{i}", 1.0, M["steam"], C_ENV, seg=24, outline=0)
        dsp = st.modifiers.new("lumpy", "DISPLACE"); dsp.texture, dsp.strength, dsp.mid_level = stex, 0.35, 0.5
        st.visible_shadow = False
        kvis([st], 0, False)
        W["steam"].append(st)

    for i in range(48):
        d = sphere(f"kame_drop_{i}", 1.0, M["drop"], C_ENV, seg=10, outline=0)
        d.visible_shadow = False
        d.rotation_mode = "QUATERNION"
        W["drops"].append(d)
    W["spray"] = []                                # v27 crown water flung up then falling back down
    for i in range(36):
        d = sphere(f"kame_spray_{i}", 1.0, M["drop"], C_ENV, seg=10, outline=0)
        d.visible_shadow = False
        d.rotation_mode = "QUATERNION"
        W["spray"].append(d)
    allw = W["ripples"] + W["drops"] + W["spray"] + [W["wake"], W["crown"], W["crown2"], W["wave"]]
    kvis(allw, 0, False)
    G["kame_water"] = W


def kame_water_animate(gp, p0, tgt, beam_keys, dvn):
    K = KAME0
    k = lambda o: K + o
    W = G["kame_water"]
    base = Vector((gp.x, gp.y, SEA_TOP))

    def kscale(o, f, sx, sz=None):
        o.scale = (sx, sx, sx if sz is None else sz); o.keyframe_insert("scale", frame=f)

    # round ripples under the feet: each ring spreads then fades; the stronger the Ki, the wider and denser the rings
    rip = W["ripples"]
    for i, r in enumerate(rip[:4]):
        r.location = base
        o = 24 + i * 9
        while o < K_FIRE - 6:
            inten = min(1.0, o / K_FIRE)
            period = 40 - 16 * inten
            kvis([r], k(o), True); kscale(r, k(o), 0.35, 1.0); _kalpha(r, k(o), 1.0)
            kscale(r, k(o + period), 1.6 + 2.4 * inten, 1.0); kvis([r], k(o + period), False)
            _kalpha(r, k(o + period * 0.4), 0.8); _kalpha(r, k(o + period), 0.0)
            o += period + 1                        # new ring starts after the hidden frame (its first key doesn't override the last key of the previous ring)
    fire = rip[4]                                  # recoil on firing: one big ring spreading fast
    fire.location = base
    kvis([fire], k(K_FIRE), True); kscale(fire, k(K_FIRE), 0.5, 1.4)
    kscale(fire, k(K_FIRE + 12), 5.0, 1.4); kscale(fire, k(K_FIRE + 40), 9.0, 1.0); kvis([fire], k(K_FIRE + 40), False)
    for o, a in ((K_FIRE, 1.0), (K_FIRE + 12, 0.75), (K_FIRE + 40, 0.0)):
        _kalpha(fire, k(o), a)

    # water spray flung up by the Ki then falling under gravity (real ballistics), fired again after each burst
    rng = random.Random(88)
    for d in W["drops"]:
        f = 30 + rng.uniform(0, 40)
        while f < K_FIRE + 20:
            inten = min(1.0, f / K_FIRE) if f < K_FIRE else 1.25
            a = rng.uniform(0, math.tau)
            r0 = rng.uniform(0.25, 0.9)
            vz = rng.uniform(3.4, 6.4) * (0.55 + 0.45 * inten) / 60.0
            vh = rng.uniform(0.6, 1.6) * (0.5 + 0.5 * inten) / 60.0
            T = 2 * vz / G_ACC
            dirv = Vector((math.cos(a), math.sin(a), 0))
            s = rng.uniform(0.016, 0.034)             # v27: smaller (they used to be egg-sized)
            f0 = int(f)
            kvis([d], k(f0), True)
            for t in list(range(0, int(T), 2)) + [int(T)]:
                d.location = base + dirv * (r0 + vh * t) + Vector((0, 0, vz * t - 0.5 * G_ACC * t * t))
                d.keyframe_insert("location", frame=k(f0 + t))
                vel = dirv * vh + Vector((0, 0, vz - G_ACC * t))           # droplets stretched along velocity (motion smear)
                d.rotation_quaternion = vel.to_track_quat("Z", "Y")
                d.keyframe_insert("rotation_quaternion", frame=k(f0 + t))
                ss = s * (1.0 if t < T * 0.7 else 0.7)
                d.scale = (ss, ss, ss * (1 + 26 * vel.length)); d.keyframe_insert("scale", frame=k(f0 + t))
            kvis([d], k(f0 + int(T) + 1), False)
            f = f0 + T + 2 + rng.uniform(0, 14)
        d.keyframe_insert("location", frame=k(330))

    # foam streak under the beam path: follows the beam head (3 frames late), rises then collapses when the beam stops
    wk = W["wake"]
    flat_d = Vector((dvn.x, dvn.y, 0))
    hdist = flat_d.length
    wk.location = Vector((p0.x, p0.y, SEA_TOP))
    wk.rotation_euler = (0, 0, math.atan2(flat_d.y, flat_d.x))
    kvis([wk], k(K_FIRE + 3), True)
    for o, ln in beam_keys:
        wk.scale = (max(0.05, ln * hdist), 1.0, 0.2 if o <= K_FIRE + 5 else 1.0)
        wk.keyframe_insert("scale", frame=k(o + 3))
    for o, sz in ((290, 1.1), (306, 0.7), (320, 0.05)):
        wk.scale = (wk.scale.x, 1.2, sz); wk.keyframe_insert("scale", frame=k(o))
    kvis([wk], k(321), False)
    gl = W["glint"]                                # beam glint on the water follows the beam head, goes off with the beam
    gl.location = Vector((p0.x, p0.y, SEA_TOP + 0.006))
    gl.rotation_euler = wk.rotation_euler
    kvis([gl], k(K_FIRE + 1), True)
    for o, ln in beam_keys:
        gl.scale = (max(0.05, ln * hdist), 0.5 if o <= K_FIRE + 5 else 0.75, 1); gl.keyframe_insert("scale", frame=k(o))
    for o, sy in ((290, 0.7), (306, 0.3), (318, 0.02)):
        gl.scale = (gl.scale.x, sy, 1); gl.keyframe_insert("scale", frame=k(o))
    kvis([gl], k(319), False)
    pool = W["pool"]                               # blast lights up the water: light pool grows with the blast then fades
    pool.location = Vector((tgt.x, tgt.y, SEA_TOP + 0.007))
    kvis([pool], k(K_HIT), True)
    for o, sx in ((K_HIT, 0.4), (K_HIT + 6, 2.2), (270, 3.2), (300, 3.8), (322, 4.2), (329, 0.05)):
        pool.scale = (sx, sx, 1); pool.keyframe_insert("scale", frame=k(o))
    kvis([pool], k(329), False)
    _set_interp([gl, pool], k(0), KAME1, "LINEAR")

    # blast right above the water: the shockwave hits the water after ~3 frames → crown sprays high, slumps; big wave spreads far
    under = Vector((tgt.x, tgt.y, SEA_TOP))
    cr, cr2, wave = W["crown"], W["crown2"], W["wave"]
    for o in (cr, cr2, wave):
        o.location = under
    kvis([cr, cr2, wave], k(K_HIT + 3), True)
    for o, sx, sz in ((K_HIT + 3, 0.5, 0.2), (K_HIT + 14, 1.7, 3.8), (K_HIT + 34, 2.3, 4.8), (300, 2.7, 4.2),
                      (329, 3.1, 2.0)):
        kscale(cr, k(o), sx, sz)
    for o, sx, sz in ((K_HIT + 3, 0.35, 0.2), (K_HIT + 10, 1.0, 2.8), (K_HIT + 26, 1.5, 3.4), (300, 1.8, 1.9),
                      (329, 2.1, 0.6)):
        kscale(cr2, k(o), sx, sz)
    for o, sx in ((K_HIT + 3, 1.0), (K_HIT + 20, 7.0), (K_HIT + 60, 13.0), (329, 15.0)):
        kscale(wave, k(o), sx, 2.0)
    for o, a in ((K_HIT + 3, 1.0), (K_HIT + 20, 0.8), (K_HIT + 60, 0.4), (329, 0.05)):
        _kalpha(wave, k(o), a)
    kvis([cr, cr2, wave], KAME1, False)
    # v27 water blasted up falls back down: big droplets thrown from the crown wall along ballistic arcs (real g), into the sea
    # (before, the crown just shrank via scale and the water "vanished" in mid-air)
    rs2 = random.Random(1234)
    for d in W["spray"]:
        f0 = K_HIT + 4 + int(rs2.uniform(0, 14))
        a = rs2.uniform(0, math.tau)
        out = Vector((math.cos(a), math.sin(a), 0))
        r0, h0 = rs2.uniform(1.4, 2.4), rs2.uniform(1.2, 3.6)
        vz, vh = rs2.uniform(0.5, 4.0) / 60.0, rs2.uniform(1.5, 4.0) / 60.0
        sz = rs2.uniform(0.035, 0.075)
        T = (vz + math.sqrt(vz * vz + 2 * G_ACC * h0)) / G_ACC          # time to hit the sea surface
        end = min(329 - f0, int(T))
        kvis([d], k(f0), True)
        for t in list(range(0, end, 2)) + [end]:
            d.location = under + out * (r0 + vh * t) + Vector((0, 0, h0 + vz * t - 0.5 * G_ACC * t * t))
            d.keyframe_insert("location", frame=k(f0 + t))
            vel = out * vh + Vector((0, 0, vz - G_ACC * t))
            d.rotation_quaternion = vel.to_track_quat("Z", "Y")
            d.keyframe_insert("rotation_quaternion", frame=k(f0 + t))
            d.scale = (sz, sz, sz * (1 + 18 * vel.length)); d.keyframe_insert("scale", frame=k(f0 + t))
        kvis([d], k(f0 + end + 1), False)
        if end == int(T):                                  # hits the sea before the cut → plop sound (synth_audio.py)
            bpy.context.scene.timeline_markers.new("sfx:plop", frame=k(f0 + end))
    _set_interp(W["spray"], k(0), KAME1, "LINEAR")
    rs = random.Random(99)
    for i, st in enumerate(W["steam"]):          # steam: grows, drifts up + outward, slows toward the end
        ang = math.tau * i / len(W["steam"]) + rs.uniform(-0.3, 0.3)
        out = Vector((math.cos(ang), math.sin(ang), 0))
        s0 = K_HIT + 12 + rs.uniform(0, 14)
        kvis([st], k(s0), True)
        for o, rr, z, sc in ((s0, 1.4, 0.2, 0.15), (s0 + 20, 2.4, 0.9, 0.7), (300, 3.0, 1.8, 1.1), (329, 3.4, 2.6, 1.3)):
            st.location = under + out * rr * rs.uniform(0.85, 1.15) + Vector((0, 0, z))
            st.keyframe_insert("location", frame=k(o))
            st.scale = (sc, sc, sc * 0.8); st.keyframe_insert("scale", frame=k(o))
    kvis(W["steam"], KAME1, False)
    _set_interp(W["steam"], k(0), KAME1, "LINEAR")
    _set_interp(W["ripples"] + [wk, cr, cr2, wave], k(0), KAME1, "LINEAR")
    _set_interp(W["drops"], k(0), KAME1, "LINEAR")
