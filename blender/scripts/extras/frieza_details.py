# Polish details for Frieza (runs after build_scene.py, shared globals: F, M, C_FRIEZA, helpers...).
# - crescent highlight spots on the purple head dome, shoulder armor, chest gem; vertical highlight streaks on the forearms and shins
# - light purple ink lines for pecs/abs (decal projected onto the torso)
# - toes (2 per foot), bright rim under the shoulder armor, glossier chest gem
# "Projected" decals: a flat grid casts rays (BVH on the base mesh, ignoring the outline) onto the surface, parented to that same object so it
# moves with the rig without touching the position/scale of the original part.
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _fd_proj(name, ob, center, d, up, w, h, mat, off=0.0015, grid=12):
    bm0 = bmesh.new(); bm0.from_mesh(ob.data)
    bvh = BVHTree.FromBMesh(bm0)
    d = Vector(d).normalized(); up = Vector(up)
    up = (up - d * d.dot(up)).normalized()
    right = d.cross(up).normalized()             # looking -Y: d × up points -X (character's right), same as face_decal
    center = Vector(center)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new(); vs = {}
    for i in range(grid + 1):
        for j in range(grid + 1):
            u, v = i / grid, j / grid
            o = center + right * (u - 0.5) * w + up * (v - 0.5) * h
            hit, nrm, _, _ = bvh.ray_cast(o + d * 0.5, -d, 1.0)
            if hit is None:
                hit, nrm, _, _ = bvh.find_nearest(o)
            vs[i, j] = (bm.verts.new(hit + nrm.normalized() * off), (u, v))
    bm0.free()
    for i in range(grid):
        for j in range(grid):
            q = [vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]]
            f = bm.faces.new([x[0] for x in q])
            for lp, (_, uv) in zip(f.loops, q):
                lp[uvl].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    dec = _obj(name, bm, mat, C_FRIEZA, outline=0)
    dec.parent = ob
    dec.location = (0, 0, 0)
    dec.visible_shadow = False
    return dec


def _fd_try(label, fn):
    try:
        fn()
    except Exception as e:                       # one broken detail must not break the whole build
        print("frieza_details:", label, "FAILED", repr(e))


_FD = bpy.data.objects
_fd_tex = {}


def _fd_mat(png):
    if png not in _fd_tex:
        _fd_tex[png] = tex_mat(f"tx_{png[:-4]}", png)
    return _fd_tex[png]


def _fd_dome():
    _fd_proj("fr_dome_shine", _FD["fr_dome"], (0, 0, 0), head_dir(180 + 30, 56), (0, 0, 1), 0.16, 0.1,
             _fd_mat("frieza_shine.png"), off=0.0075)
    # small secondary spot on the other side of the dome, visible from the front camera angle
    _fd_proj("fr_dome_shine2", _FD["fr_dome"], (0, 0, 0), head_dir(180 - 38, 50), (0, 0, 1), 0.07, 0.045,
             _fd_mat("frieza_shine.png"), off=0.0075)


def _fd_plates():
    for side, sx in (("R", -1), ("L", 1)):
        _fd_proj(f"fr_shoulder_shine_{side}", _FD[f"fr_shoulder_{side}"], (0, 0, 0), (sx * 0.35, -0.55, 0.75), (0, 0.4, 1),
                 0.07, 0.05, _fd_mat("frieza_shine.png"))
        _fd_proj(f"fr_fore_shine_{side}", _FD[f"fr_fore_{side}"], (0, 0, 0.01), (sx * 0.55, -0.85, 0), (0, 0, 1),
                 0.024, 0.085, _fd_mat("frieza_streak.png"))
        _fd_proj(f"fr_shin_shine_{side}", _FD[f"fr_shin_{side}"], (0, 0, 0.01), (sx * 0.5, -0.9, 0), (0, 0, 1),
                 0.028, 0.085, _fd_mat("frieza_streak.png"))   # v16 shorter shins


def _fd_abs():
    # v17 rebuilt torso (fr_torso origin at the chest joint): chest line matches the lower pec edge, abs extend down to the waist
    _fd_proj("fr_abs", _FD["fr_torso"], (0, 0, 0.074), (0, -1, 0), (0, 0, 1), 0.19, 0.2, _fd_mat("frieza_abs.png"))


def _fd_collar():
    # v17 hint of collarbones: 2 light purple ink lines under the neck, projected diagonally from front-top down the shoulder slope
    _fd_proj("fr_collar", _FD["fr_torso"], (0, -0.04, 0.232), (0, -1, 0.75), (0, 0.6, 1), 0.2, 0.1,
             _fd_mat("frieza_collar.png"))


def _fd_gem():
    gem = _FD["fr_chest_gem"]
    gm = toon("fr_gem", "#B24FE6", "#6C2496", "#E6B0FF", rim=0.9, spec=1.0, threshold=0.25)
    gem.data.materials[0] = gm
    _fd_proj("fr_gem_shine", gem, (0, 0, 0), (-0.35, -0.85, 0.45), (0, 0, 1), 0.045, 0.032, _fd_mat("frieza_shine.png"),
             off=0.001, grid=8)


def _fd_toes():
    W_ = M["f_white"]
    for side, sx in (("R", -1), ("L", 1)):
        for k, tx in enumerate((-0.016, 0.016)):    # v17 smaller, tidier feet: 2 round tapered toes at the tip of the foot
            t = sphere(f"fr_toe_{side}{k}", 0.016, W_, C_FRIEZA, (1.0, 1.35, 0.85), seg=16, outline=0.004)
            attach(t, F[f"kn_{side}"], (tx, -0.018 - 0.056, globals().get("FR_FOOT_Z", -0.235) - 0.004))
            t.visible_shadow = False


def _fd_shoulder_rim():
    rim = toon("fr_rim", "#7C36AE", "#4C1872", "#A866D8", rim=0.6)   # bottom edge of the dark purple armor (bright lilac ring like Saturn's)
    for side, sx in (("R", -1), ("L", 1)):
        sh = _FD[f"fr_shoulder_{side}"]
        r = torus(f"fr_shoulder_rim_{side}", 0.067, 0.0062, rim, C_FRIEZA, seg=32, ring=8, scale=(1.12, 1.0, 1.0), outline=0.002)
        r.parent = sh.parent
        r.location = sh.location + Vector((0, 0, -0.008))
        r.rotation_euler = sh.rotation_euler
        r.visible_shadow = False


for _l, _f in (("dome", _fd_dome), ("plates", _fd_plates), ("abs", _fd_abs), ("collar", _fd_collar), ("gem", _fd_gem),
               ("toes", _fd_toes), ("shoulder_rim", _fd_shoulder_rim)):
    _fd_try(_l, _f)
print("frieza_details: done")
