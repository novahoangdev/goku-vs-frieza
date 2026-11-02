# Goku's gi modeled on FighterZ (chibi proportions): deep V-neck showing the blue undershirt + orange lapels, sleeveless orange shoulders,
# cloth folds on chest/belt/pants bunching over the boots, navy boots with red stripes + yellow laces at the ankle.
# Runs after goku_details.py (reuses the _gd_* helpers). New objects are named "go_*", visibility keys copied from goku_torso
# (Goku vanishes while teleporting 1001–1011).


def _go_patch(name, target, origin, nu, nv, dirfn, off, mat, col):
    """(u, v) grid ∈ [0,1]² → origin point origin(u, v) (in target's parent coords) → projected along dirfn onto target."""
    bvh = _gd_bvh(target)
    bm = bmesh.new()
    vs = []
    for j in range(nv + 1):
        for i in range(nu + 1):
            p = origin(i / nu, j / nv)
            q = _gd_project(bvh, p, dirfn(p), off) if dirfn else None
            if q is None:                                  # ray missed (shoulder curve edge): snap to the nearest point
                loc, nrm, _i, _d = bvh.find_nearest(p)
                q = loc + nrm.normalized() * off
            vs.append(bm.verts.new(q))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            bm.faces.new((vs[a], vs[a + 1], vs[a + nu + 2], vs[a + nu + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _obj(name, bm, mat, col, smooth=True, outline=0)
    ob.parent = target.parent
    ob.visible_shadow = False
    return ob


def _go_snap_stroke(name, target, pts, r, mat, col, off=0.004, samples=14):
    """Curved stroke snapped to `target` via nearest point (for the shoulder curve around the neck, where ray projection misses/skews)."""
    bvh = _gd_bvh(target)
    P = [Vector(p) for p in pts]
    dense = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(samples):
            t = k / samples
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(P[-1])
    out = []
    for p in dense:
        loc, nrm, _i, _d = bvh.find_nearest(p)
        if loc is not None:
            out.append(loc + nrm.normalized() * off)
    return _gd_tube(name, out, r, mat, col, target.parent) if len(out) > 2 else None


def _go_rope_ring(name, R, r, mat, col, wraps=14, seg=72, ring=8, scale=(1, 1, 1)):
    """Twisted rope ring: cross-section pulses along a helix."""
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = math.tau * i / seg
        row = []
        for j in range(ring):
            b = math.tau * j / ring
            rr = r * (0.82 + 0.3 * abs(math.cos(wraps * a / 2 + b / 2)))
            row.append(bm.verts.new(((R + rr * math.cos(b)) * math.cos(a) * scale[0],
                                     (R + rr * math.cos(b)) * math.sin(a) * scale[1], rr * math.sin(b) * scale[2])))
        rings.append(row)
    for i in range(seg):
        for j in range(ring):
            a_, b_ = rings[i], rings[(i + 1) % seg]
            bm.faces.new((a_[j], b_[j], b_[(j + 1) % ring], a_[(j + 1) % ring]))
    return _obj(name, bm, mat, col, outline=0.0025)


def _go_build():
    c = C_GOKU
    obj = bpy.data.objects
    torso = obj["goku_torso"]
    new = []
    LINE_COLORS.setdefault("goku_rope", "#6A4510")
    Mx = {
        "ink": flat("go_ink", "#2A1208"),                 # lapel outline / overlapping cloth edge: brown-black
        "fold": flat("go_fold", "#93380C"),               # cloth folds: burnt orange
        "fold_dk": flat("go_fold_dk", "#6A220A"),
        "blue_ln": flat("go_blue_ln", "#101C52"),
        "blue_sh": flat("go_blue_sh", "#16286A"),         # hard drop shadow under the lapel onto the blue undershirt
        "rope": toon("goku_rope", "#E8C46E", "#B88C38", "#FFE6A6", rim=0.5),
        "red": toon("go_red", "#C8262E", "#861820", "#EE5A60", rim=0.4),
    }
    fwd = lambda p: Vector((0, 1, 0))

    # ── 1. deep V-neck: blue undershirt hugging the chest, orange lapels overlapping the edge, ink lines ──
    try:
        Z0, Z1, XP, W = 0.29, 0.122, 0.008, 0.104         # top of the V (level with the neck base, under the chin) → V tip; tip slightly off-center (left flap over right)

        def vx(side, v):                                   # V edge at parameter v (0: top, 1: tip), side ±1
            return XP + (side * W - XP) * (1 - v) ** 0.78

        vz = lambda v: Z0 + (Z1 - Z0) * v
        oy = lambda v: -0.035 - 0.095 * min(1.0, v * 3.0)  # snap origin: close to the neck on the top row → blue undershirt joins the collar seamlessly
        new.append(_go_patch("go_undershirt", torso,
                             lambda u, v: Vector((vx(-1, v) + (vx(1, v) - vx(-1, v)) * u, oy(v), vz(v) + 0.004)),
                             16, 18, None, 0.0022, M["blue"], c))
        # hard shadow cast by the lapel onto the blue undershirt (cel shadow): dark band along the left edge of the V
        new.append(_go_patch("go_undershirt_sh", torso,
                             lambda u, v: Vector((vx(1, v) - 0.016 * (1 - v) ** 0.6 * u - 0.002, oy(v), vz(v))),
                             3, 18, None, 0.0032, Mx["blue_sh"], c))
        for side in (-1, 1):
            wd = 0.02
            lap = _go_patch(f"go_lapel_{'L' if side > 0 else 'R'}", torso,
                            lambda u, v, s=side: Vector((vx(s, v) + s * (u * wd - 0.003), oy(v), vz(v) + (0.002 if s > 0 else 0))),
                            3, 20, None, 0.0048 if side > 0 else 0.004, M["gi"], c)
            new.append(lap)
            # ink line on the inner lapel edge (against the blue undershirt) + faint line on the outer edge
            new.append(_go_snap_stroke(f"go_lapel_ink_{side}", torso, [(vx(side, v) - side * 0.003, oy(v), vz(v)) for v in (0, 0.33, 0.66, 1.0)],
                                       0.0026, Mx["ink"], c, off=0.006))
            new.append(_go_snap_stroke(f"go_lapel_out_{side}", torso,
                                       [(vx(side, v) + side * (wd - 0.002), oy(v), vz(v) - 0.004) for v in (0.02, 0.4, 0.75, 0.97)],
                                       0.0018, Mx["fold"], c, off=0.0058))
        # overlapping flap: left flap edge running diagonally from the V tip down to the belt (on Goku's right-hand side)
        new.append(_gd_stroke("go_overlap", torso, [(XP + 0.002, -0.4, Z1 + 0.004), (-0.012, -0.4, 0.085), (-0.03, -0.4, 0.035), (-0.04, -0.4, -0.005)],
                              fwd, 0.0024, Mx["fold_dk"], c, off=0.0045))
        # curved chest fold under the lapel + armpit fold (cel line)
        for side in (-1, 1):
            new.append(_gd_stroke(f"go_chest_fold_{side}", torso,
                                  [(side * 0.13, -0.4, 0.215), (side * 0.112, -0.4, 0.19), (side * 0.098, -0.4, 0.165)],
                                  fwd, 0.0021, Mx["fold"], c, off=0.004))
        new.append(_gd_stroke("go_belly_fold", torso, [(-0.075, -0.4, 0.06), (-0.06, -0.4, 0.04), (-0.05, -0.4, 0.02)],
                              fwd, 0.002, Mx["fold"], c, off=0.004))
    except Exception as e:
        import traceback; traceback.print_exc()
        print("GO v-neck failed", e)

    # ── 2. orange shoulders: removed (v19) — the orange gi body already covers the shoulders; 2 separate shoulder blocks stuck out like knobs at the lapel tips ──

    # ── 3. belt: horizontal wrinkles on the belt cloth ──
    try:
        belt = obj["goku_belt"]
        hip_dir = lambda p: Vector((-p.x, -p.y, 0)).normalized()
        for i, (x0, x1, z) in enumerate(((-0.12, -0.03, 0.06), (-0.1, -0.06, 0.04), (0.09, 0.13, 0.065), (-0.02, 0.03, 0.075))):
            pts = [(x0 + (x1 - x0) * t, -0.3, z + 0.008 * math.sin(t * 3)) for t in (0, 0.5, 1)]
            new.append(_gd_stroke(f"go_belt_fold_{i}", belt, pts, lambda p: Vector((0, 1, 0)), 0.0019, Mx["blue_ln"], c, off=0.002))
    except Exception as e:
        print("GO belt folds failed", e)

    # ── 4. pants: folds bunching over the boot tops + knee folds ──
    try:
        for side, sx in (("R", -1), ("L", 1)):
            sp, th = obj[f"goku_shinpant_{side}"], obj[f"goku_thigh_{side}"]
            rad_in = lambda p: (Vector((-p.x, -p.y, 0)).normalized() if Vector((p.x, p.y)).length > 1e-4 else Vector((0, 1, 0)))
            ring = lambda a, z, R=0.2: (R * math.sin(math.radians(a)), -R * math.cos(math.radians(a)), z)  # a=0: front

            def fold(tag, pts, r=0.0028, mat=Mx["fold"], target=sp):
                ob = _gd_stroke(f"go_{tag}_{side}", target, pts, rad_in, r, mat, c, off=0.003)
                if ob:
                    new.append(ob)
            # "く"-shaped folds around the pant cuff (front, both sides, back)
            for k, a in enumerate((-35, 20, 75, 130, 200, 260)):
                a2 = a * sx
                fold(f"bunch{k}", [ring(a2 - 14, -0.04), ring(a2, -0.068), ring(a2 + 12, -0.092)], 0.0032, Mx["fold_dk"] if k < 2 else Mx["fold"])
            # horizontal fold at the cuff edge
            fold("gather", [ring(sx * -60, -0.098), ring(sx * -20, -0.102), ring(sx * 20, -0.1), ring(sx * 60, -0.097)], 0.003, Mx["fold_dk"])
            # knee folds + vertical folds along the pant leg
            fold("knee", [ring(sx * -30, -0.215), ring(sx * 0, -0.235), ring(sx * 25, -0.225)], 0.0027, Mx["fold"], th)
            fold("thighlong", [ring(sx * 40, -0.05), ring(sx * 48, -0.12), ring(sx * 42, -0.19)], 0.0025, Mx["fold"], th)
            fold("thighback", [ring(sx * 160, -0.07), ring(sx * 178, -0.14), ring(sx * 170, -0.21)], 0.0025, Mx["fold"], th)
            fold("thighside", [ring(sx * 95, -0.03), ring(sx * 100, -0.1), ring(sx * 88, -0.17)], 0.0024, Mx["fold"], th)
    except Exception as e:
        import traceback; traceback.print_exc()
        print("GO pant folds failed", e)

    # ── 5. boots: vertical red stripes on both sides + toe, yellow laces wrapped around the ankle + knot ──
    try:
        for side, sx in (("R", -1), ("L", 1)):
            bt, ft, kn = obj[f"goku_boot_{side}"], obj[f"goku_foot_{side}"], G[f"kn_{side}"]
            rad_in = lambda p: (Vector((-p.x, -p.y, 0)).normalized() if Vector((p.x, p.y)).length > 1e-4 else Vector((0, 1, 0)))
            for k, a in enumerate((-48, 48)):
                pts = [(0.2 * math.sin(math.radians(a)), -0.2 * math.cos(math.radians(a)), z) for z in (-0.09, -0.125, -0.165)]
                ob = _gd_stroke(f"go_boot_stripe{k}_{side}", bt, pts, rad_in, 0.0058, Mx["red"], c, off=0.0015)
                if ob:
                    new.append(ob)
            to_foot = lambda p: (Vector((0, -0.035, -0.235)) - p).normalized()
            ob = _gd_stroke(f"go_toe_stripe_{side}", ft, [(0, -0.07, -0.16), (0, -0.11, -0.175), (0, -0.15, -0.205)],
                            to_foot, 0.0038, Mx["red"], c, off=0.0015)
            if ob:
                new.append(ob)
            for k, (z, R_) in enumerate(((-0.171, 0.0585), (-0.186, 0.057))):
                rg = _go_rope_ring(f"go_rope{k}_{side}", R_, 0.0068, Mx["rope"], c, scale=(1.0, 1.04, 1.0))
                attach(rg, kn, (0, -0.002, z), (-4 + 6 * k, 0, 0))
                new.append(rg)
            kt = sphere(f"go_rope_knot_{side}", 1, Mx["rope"], c, (0.013, 0.01, 0.011), seg=12, outline=0.0025)
            attach(kt, kn, (sx * 0.012, -0.062, -0.179))
            new.append(kt)
            for k, (ang, ln) in enumerate(((sx * 28, 0.026), (sx * -18, 0.02))):
                end = capsule(f"go_rope_end{k}_{side}", 0.0055, ln, Mx["rope"], c, seg=10, outline=0.002)
                attach(end, kn, (sx * 0.012 + math.sin(math.radians(ang)) * ln * 0.5, -0.066, -0.179 - math.cos(math.radians(ang)) * ln * 0.5),
                       (0, ang, 0))
                new.append(end)
    except Exception as e:
        import traceback; traceback.print_exc()
        print("GO boots failed", e)

    new = [o for o in new if o]
    _gd_vis_like(new, torso)
    G.setdefault("details", []).extend(new)
    print("GO goku_outfit:", len(new), "parts")


try:
    _go_build()
except Exception as _e:
    import traceback
    traceback.print_exc()
    print("GO goku_outfit skipped", _e)
