# FighterZ-style character outlines (post pass, runs AFTER char_shading in build_scene.py, shared globals).
# Only touches the "Outline" modifier (Solidify inverted hull) on objects in GOKU/FRIEZA; scene outlines stay as they are.
#  1) camera-distance compensation: a driver on Solidify.thickness from the camera→object distance and focal length, so close-ups
#     don't become ink strokes dozens of pixels thick, and wide shots are neither hair-thin nor clotted into black blobs.
#  2) per body part: large objects (head, hair, torso, legs) form the outer silhouette → bolder lines; small ones (ridges, buttons, cords) thinner.
#  3) bold outside, thin inside: weight by normal direction relative to the character's body axis — faces pointing outward
#     (outer edges of arms/legs/head, forming the silhouette) get full lines; faces pointing inward (inner thighs, arms against the body) thin lines.
#  3b) tapering: vertex weight = local thickness of the volume (rays cast inward) → hair-lock tips, fingers, ears, cord ends
#     taper off instead of ending in round blobs; thick volumes keep full lines.
#  4) line color: objects still using the shared brown-black outline (sleeve ridges, Frieza's shoulder ridges) switch to the dark tone of their own material.
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OL_REF = 3.0            # effective distance (normalized to a 50mm lens) that keeps the original thickness — about a medium shot
OL_POW = 0.3            # world thickness ∝ d^0.3 → pixel width ∝ d^-0.7 (thinner when far, bolder when close, but damped)
OL_CLAMP = (0.45, 2.4)
OL_TIP_T = 0.035        # volume thickness (m) at or above which lines are full; thinner volumes taper the line
OL_TIP_MIN = 0.35       # line factor at the thinnest spots (hair tips, fingertips)
OL_INNER = 0.4          # weight factor for faces pointing straight into the body (1 = no distinction)
OL_LINE_FOR = {"gd_blue_dk": "blue", "fr_rim": "f_purple", "fr_gem": "f_purple"}   # material → line color


def _ol_size_mult(ob):
    """The bigger the object, the more it contributes to the outer silhouette → bolder lines (head/hair ×1.4, small objects ×0.85)."""
    d = ob.dimensions.length
    return max(0.85, min(1.4, (d / 0.3) ** 0.45))


def _ol_tip_weights(ob, center):
    """Per-vertex 0..1 weight = volume thickness at that point (ray cast from the vertex against the normal), smoothed 2 passes,
    times an outward-facing factor relative to the body center `center` (world; vertical axis squashed ×0.3 so arms/legs are judged horizontally)."""
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
    scene.frame_set(0)                    # standing pose at the start of the film to judge inside/outside
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
                target = ob                       # object origin close to the volume (Frieza's tail is a curve with origin at 0 → use the chest)
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
