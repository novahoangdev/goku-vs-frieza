# Chi tiết môi trường Namek: nhà mái vòm chi tiết hơn, cây Ajisa tán nhiều tầng, cụm đá + bụi cỏ quanh sân đấu,
# mesa / cột đá nhỏ ở xa cho chiều sâu. Chạy sau build_scene (dùng chung globals). RNG riêng, không đụng `random`.
import math as _m
import random as _random_mod
import bmesh as _bmesh
import bpy as _bpy
from mathutils import Vector as _V, Euler as _E

_rng = _random_mod.Random(4242)
_C = C_ENV
ENV_DETAIL_OBJS = []          # dùng cho kiểm tra camera clipping


def _mat(name, fb):
    return _bpy.data.materials.get(name) or fb


_ROCK = _mat("rock_tex", M["rock"])
_PEB = M.get("rock_small") or _mat("pebble_tex", M["rock"])   # đá nhỏ 3 tông có khối (build_scene.rock_small_mat)
_LEAF = _mat("canopy_tex", M["canopy"])
_TOP = _mat("top_tex", M["grass_top"])
_SAMPLES = [chase_path(i / 200) for i in range(201)]


def _clear(x, y, r=0.0, ztop=0.0):
    """True nếu điểm (x,y) bán kính r an toàn: xa đường bay, xa tâm, xa vị trí Frieza (0, 9)."""
    for p in _SAMPLES:
        if p.z - 0.0 < 12 + ztop and _m.hypot(p.x - x, p.y - y) < 4.5 + r:
            return False
    if _m.hypot(x, y) < 4.0 + r:                                  # Goku + camera orbit thấp quanh Goku
        return False
    if abs(x) < 3.5 + r and -11 < y < 13:                         # hành lang Goku ↔ Frieza (+ nền sau lưng Goku ở shot qua vai)
        return False
    return True


def _reg(ob):
    ENV_DETAIL_OBJS.append(ob)
    return ob


def _merge_into(bm, tmp, mat4=None, fn=None):
    if fn:
        for v in tmp.verts:
            v.co = fn(v.co)
    _merge(bm, tmp)


# ───────── 1. nhà mái vòm: khung cửa sổ, vòm cửa, chỏm ăng-ten, vòm phụ, bậc nền ─────────
def _houses():
    trim = M["house"]
    dark = M["window"]
    specs = [(-18, 26, 2.6), (-23, 21, 1.8), (-12, 31, 2.0), (26, 34, 2.4), (31, 29, 1.6)]
    extra = [(-30, 33, 2.2), (-36, 26, 1.4), (14, 44, 2.0), (-8, 45, 1.5)]
    for i, (x, y, sz) in enumerate(extra):
        if not _clear(x, y, sz * 2):
            continue
        k = len(specs)
        hb = sphere(f"house_{k}", sz, M["house"], _C, (1, 1, 0.82), seg=24, outline=0.03)
        hb.location = (x, y, sz * 0.25)
        _reg(hb)
        for j in range(3):
            ang = _m.atan2(-y, -x) + (j - 1) * 0.55
            dv = _V((_m.cos(ang), _m.sin(ang), 0))
            w = cyl(f"house_{k}_win_{j}", sz * 0.13, sz * 0.13, 0.05, dark, _C, seg=16, outline=0)
            w.location = _V((x, y, sz * 0.25 + sz * 0.42)) + dv * sz * 0.93
            w.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
        dv = _V((_m.cos(_m.atan2(-y, -x) + 1.2), _m.sin(_m.atan2(-y, -x) + 1.2), 0))
        door = sphere(f"house_{k}_door", sz * 0.24, dark, _C, (1, 0.3, 1.4), outline=0)
        door.location = _V((x, y, sz * 0.25)) + dv * sz * 0.98
        door.rotation_euler = (0, 0, _m.atan2(dv.y, dv.x) + _m.pi / 2)
        specs.append((x, y, sz))
    for i, (x, y, sz) in enumerate(specs):
        cz = sz * 0.25
        face = _m.atan2(-y, -x)
        # khung tròn quanh 3 cửa sổ (torus mảnh, nằm trên mặt vòm)
        for j in range(3):
            ang = face + (j - 1) * 0.55
            dv = _V((_m.cos(ang), _m.sin(ang), 0))
            rim = torus(f"house_{i}_winrim_{j}", sz * 0.15, sz * 0.03, trim, _C, seg=18, ring=6, outline=0.012)
            rim.location = _V((x, y, cz + sz * 0.42)) + dv * sz * 0.95
            rim.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
        # vòm cửa ra vào: khung hình chữ U nổi
        dv = _V((_m.cos(face + 1.2), _m.sin(face + 1.2), 0))
        arch = torus(f"house_{i}_doorrim", sz * 0.27, sz * 0.045, trim, _C, seg=20, ring=6, scale=(1, 1, 1.35), outline=0.012)
        arch.location = _V((x, y, cz + sz * 0.02)) + dv * sz * 1.0
        arch.rotation_euler = _E((_m.pi / 2, 0, _m.atan2(dv.y, dv.x) + _m.pi / 2))
        # bậc nền (vành đế thấp)
        base = cyl(f"house_{i}_plinth", sz * 1.06, sz * 1.1, 0.22, trim, _C, seg=28, outline=0.02)
        base.location = (x, y, 0.05)
        # chỏm trên: cổ ngắn + bầu tròn + ăng-ten nhỏ với quả cầu
        top_z = cz + sz * 0.82
        neck = cyl(f"house_{i}_neck", sz * 0.16, sz * 0.12, sz * 0.18, trim, _C, seg=14, outline=0.015)
        neck.location = (x, y, top_z + sz * 0.05)
        bulb = sphere(f"house_{i}_bulb", sz * 0.2, M["house"], _C, (1, 1, 0.75), seg=16, outline=0.015)
        bulb.location = (x, y, top_z + sz * 0.2)
        ant = cyl(f"house_{i}_antenna", sz * 0.025, sz * 0.02, sz * 0.5, trim, _C, seg=6, outline=0.008)
        ant.location = (x, y, top_z + sz * 0.5)
        tip = sphere(f"house_{i}_antball", sz * 0.06, M["house"], _C, seg=10, outline=0.008)
        tip.location = (x, y, top_z + sz * 0.77)
        # vòm phụ nhỏ dính bên hông (kiểu nhà Namek nhiều bầu)
        if i % 2 == 0:
            sa = face - 1.4 + _rng.uniform(-0.3, 0.3)
            ss = sz * 0.55
            ann = sphere(f"house_{i}_annex", ss, M["house"], _C, (1, 1, 0.8), seg=20, outline=0.025)
            ann.location = (x + _m.cos(sa) * sz * 0.95, y + _m.sin(sa) * sz * 0.95, ss * 0.2)
            dv2 = _V((_m.cos(face - 0.9), _m.sin(face - 0.9), 0))
            w = cyl(f"house_{i}_annex_win", ss * 0.16, ss * 0.16, 0.05, dark, _C, seg=14, outline=0)
            w.location = _V(ann.location) + _V((0, 0, ss * 0.3)) + dv2 * ss * 0.92
            w.rotation_euler = dv2.to_track_quat("Z", "Y").to_euler()
            _reg(ann)
        for ob in (base, bulb, ant, tip):
            _reg(ob)


# ───────── 2. cây Ajisa: tán nhiều tầng, xù hơn ─────────
def _bushy_trees():
    for ob in list(_C.objects):
        if not ob.name.endswith("_canopy"):
            continue
        base = ob.name[:-len("_canopy")]
        s = ob.dimensions.x / 2.0
        c = _V(ob.location)
        r = _random_mod.Random(sum(map(ord, ob.name)))
        bm = _bmesh.new()
        # vòng búp phồng ngang thân tán + tầng dưới rủ + chỏm trên
        layers = [(-0.35, 0.95, 7, 0.42), (0.05, 0.85, 6, 0.4), (0.45, 0.45, 4, 0.36)]
        for dz, rad, n, sr in layers:
            off = r.uniform(0, _m.tau)
            for k in range(n):
                a = off + k / n * _m.tau
                rr = s * sr * r.uniform(0.85, 1.15)
                tmp = _bmesh.new()
                _bmesh.ops.create_uvsphere(tmp, u_segments=10, v_segments=6, radius=rr)
                p = _V((_m.cos(a) * s * rad * 0.82, _m.sin(a) * s * rad * 0.82, dz * s))
                for v in tmp.verts:
                    v.co = _V((v.co.x, v.co.y, v.co.z * 0.85)) + p
                _merge(bm, tmp)
        tmp = _bmesh.new()
        _bmesh.ops.create_uvsphere(tmp, u_segments=12, v_segments=7, radius=s * 0.5)
        for v in tmp.verts:
            v.co = _V((v.co.x, v.co.y, v.co.z * 0.8)) + _V((0, 0, s * 0.62))
        _merge(bm, tmp)
        puff = _obj(base + "_puffs", bm, _LEAF, _C, smooth=True, outline=0.025)
        puff.location = c
        puff.visible_shadow = True
        _reg(puff)
        ob.scale = (ob.scale.x * 0.95, ob.scale.y * 0.95, ob.scale.z * 1.0)
        # vài nhánh con chìa ra từ thân (cây Ajisa có thân mảnh, gốc loe)
        tr = _C.objects.get(base + "_trunk")
        if tr:
            h = tr.dimensions.z
            root = cyl(base + "_root", tr.dimensions.x * 1.4, tr.dimensions.x * 0.5, h * 0.18, M["trunk"], _C, seg=8, outline=0.015)
            root.location = (tr.location.x, tr.location.y, tr.location.z - h / 2 + h * 0.09)


# ───────── 3. cụm đá + bụi cỏ quanh sân đấu (r ~ 4–14 m) ─────────
def _ground_clutter():
    bm_rock = _bmesh.new()
    bm_grass = _bmesh.new()
    placed = 0
    tries = 0
    while placed < 16 and tries < 600:
        tries += 1
        a, d = _rng.uniform(0, _m.tau), _rng.uniform(5.0, 14.0)
        x, y = _m.cos(a) * d, _m.sin(a) * d
        if not _clear(x, y, 1.2):
            continue
        placed += 1
        n = _rng.randint(2, 4)
        big = _rng.uniform(0.35, 0.75)
        for k in range(n):
            rr = big * (1.0 if k == 0 else _rng.uniform(0.35, 0.65))
            tmp = _bmesh.new()
            _bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=rr)
            ox, oy = (0, 0) if k == 0 else (_rng.uniform(-1, 1) * big * 1.3, _rng.uniform(-1, 1) * big * 1.3)
            sq = _rng.uniform(0.55, 0.85)
            rot = _E((_rng.uniform(-0.3, 0.3), _rng.uniform(-0.3, 0.3), _rng.uniform(0, 6))).to_matrix()
            for v in tmp.verts:
                q = rot @ _V((v.co.x * _rng.uniform(0.92, 1.08), v.co.y, v.co.z * sq))
                v.co = q + _V((x + ox, y + oy, rr * sq * 0.45))
            _merge(bm_rock, tmp)
        # bụi cỏ quanh chân đá: lá dẹt hình mũi giáo
        for g in range(_rng.randint(2, 3)):
            ga = _rng.uniform(0, _m.tau)
            gx, gy = x + _m.cos(ga) * big * 1.6, y + _m.sin(ga) * big * 1.6
            _clump(bm_grass, gx, gy, _rng.uniform(0.8, 1.2))
    # thêm bụi cỏ rời rạc
    tries = 0
    k = 0
    while k < 34 and tries < 800:
        tries += 1
        a, d = _rng.uniform(0, _m.tau), _rng.uniform(4.0, 16.0)
        x, y = _m.cos(a) * d, _m.sin(a) * d
        if not _clear(x, y, 0.4):
            continue
        _clump(bm_grass, x, y, _rng.uniform(0.7, 1.3))
        k += 1
    rocks = _obj("env_rock_clusters", bm_rock, _PEB, _C, smooth=False, outline=0.02)
    grass = _obj("env_grass_clumps", bm_grass, M["grass_top"], _C, smooth=False, outline=0)
    grass.visible_shadow = False
    _reg(rocks)
    _reg(grass)


def _clump(bm, x, y, s):
    for b in range(_rng.randint(6, 9)):
        h = _rng.uniform(0.3, 0.6) * s
        w = 0.06 * s
        a = _rng.uniform(0, _m.tau)
        lean = _rng.uniform(0.15, 0.6)
        verts = [(-w, 0, 0), (w, 0, 0), (w * 0.5, 0, h * 0.55), (0, 0, h)]
        M3 = _E((lean, 0, a)).to_matrix()
        bx, by = x + _rng.uniform(-0.1, 0.1) * s, y + _rng.uniform(-0.1, 0.1) * s
        vs = [bm.verts.new(M3 @ _V(p) + _V((bx, by, 0.0))) for p in verts]
        vl = bm.verts.new(M3 @ _V((-w * 0.5, 0, h * 0.55)) + _V((bx, by, 0.0)))
        bm.faces.new((vs[0], vs[1], vs[2], vl))
        bm.faces.new((vl, vs[2], vs[3]))


# ───────── 4. mesa + cột đá nhỏ ở xa (chiều sâu) ─────────
def _distant():
    n = 0
    tries = 0
    while n < 9 and tries < 400:
        tries += 1
        a, d = _rng.uniform(0, _m.tau), _rng.uniform(95, 170)
        x, y = _m.cos(a) * d, _m.sin(a) * d
        if abs(y) < 22 and -10 < x < 110:      # chừa hướng bay
            continue
        if not _clear(x, y, 12):
            continue
        if n % 3 == 0:      # mesa: khối trụ rộng, thấp, mặt bằng có cỏ
            r = _rng.uniform(7, 12)
            h = _rng.uniform(6, 14)
            body = cyl(f"env_mesa_{n}", r, r * 0.8, h, _ROCK, _C, seg=10, outline=0.08, smooth=False)
            body.location = (x, y, -0.7 + h / 2)
            body.rotation_euler = (0, 0, _rng.uniform(0, 6))
            top = cyl(f"env_mesa_{n}_top", r * 0.82, r * 0.8, 0.5, _TOP, _C, seg=10, outline=0.05, smooth=False)
            top.location = (x, y, -0.7 + h + 0.2)
            _reg(body)
        else:               # cột mảnh, thuôn, nghiêng nhẹ
            r = _rng.uniform(1.2, 2.4)
            h = _rng.uniform(14, 30)
            body = cyl(f"env_spirelet_{n}", r, r * 0.5, h, _ROCK, _C, seg=7, outline=0.05, smooth=False)
            body.location = (x, y, -0.7 + h / 2)
            body.rotation_euler = (_rng.uniform(-0.06, 0.06), _rng.uniform(-0.06, 0.06), _rng.uniform(0, 6))
            top = cyl(f"env_spirelet_{n}_top", r * 0.55, r * 0.5, 0.4, _TOP, _C, seg=7, outline=0.03, smooth=False)
            top.location = (x, y, -0.7 + h + 0.1)
            top.rotation_euler = body.rotation_euler
            _reg(body)
        n += 1


for _fn in (_houses, _bushy_trees, _ground_clutter, _distant):
    try:
        _fn()
    except Exception as _e:
        import traceback as _tb
        print("env_details: lỗi ở", _fn.__name__, _e)
        _tb.print_exc()
print("env_details: thêm", len(ENV_DETAIL_OBJS), "đối tượng")
