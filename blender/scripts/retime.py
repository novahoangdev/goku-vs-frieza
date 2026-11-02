# Film retiming (v22): the 20 s film cut too fast and felt abrupt. Maps old frames → new frames piecewise linearly
# per shot, each shot stretched by its own factor: much slower for the opening, transformation, punch and ending; moderate for
# the combo/chase so it stays frantic. Applied to EVERY keyframe (objects, materials, nodes, camera, FX) and marker before saving;
# the map is stored in scene["retime"] → bake_timeline copies it into timeline.json, shared by app, promo, audio and compare.
import json
import bpy

# (old frame, new frame) at the cut points; new frames are integers so cuts land exactly on a frame
_SEG = [(0, 1.6), (120, 1.4), (240, 1.3), (300, 1.6), (390, 1.5), (510, 1.4), (600, 1.25), (690, 1.2),
        (780, 1.25), (990, 1.3), (1030, 1.5), (1110, 2.0), (1200, None)]
# v23: inserts the Kamehameha sequence (KAME_LEN new frames long) right before the final shot: the map has a vertical jump at GAP_AT
# (original frame 1109.8 — after the hold key 1109.6 of cut 1110, before that cut itself). Everything that reads the map (app, promo,
# audio, tools) looks for the first segment with f <= b, so the zero-length segment at the jump is never divided by 0.
GAP_AT, KAME_LEN = 1109.8, 330
RETIME = [(0, 0)]
for (a, k), (b, _) in zip(_SEG, _SEG[1:]):
    if a < GAP_AT < b:
        RETIME.append((GAP_AT, RETIME[-1][1] + (GAP_AT - a) * k))
        RETIME.append((GAP_AT, RETIME[-1][1] + KAME_LEN))
        RETIME.append((b, RETIME[-1][1] + (b - GAP_AT) * k))
        continue
    RETIME.append((b, RETIME[-1][1] + round((b - a) * k)))
KAME0 = int(round(RETIME[[x for x, _ in RETIME].index(GAP_AT)][1] + 0.5))   # first new frame of the Kamehameha sequence
KAME1 = KAME0 + KAME_LEN                                                     # = cut into the final shot


def rt(f):
    """old frame → new frame (outside the range: extrapolate with the first/last segment's factor)."""
    if f <= RETIME[0][0]:
        return f * _SEG[0][1]
    for (a, na), (b, nb) in zip(RETIME, RETIME[1:]):
        if f <= b:
            return na + (f - a) * (nb - na) / (b - a)
    (a, na), (b, nb) = RETIME[-2], RETIME[-1]
    return nb + (f - b) * (nb - na) / (b - a)


def retime_scene():
    n = 0
    holds = []
    for act in bpy.data.actions:
        fcs = list(getattr(act, "fcurves", []) or [])
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for bag in strip.channelbags:
                    fcs.extend(bag.fcurves)
        for fc in fcs:
            xs = [kp.co.x for kp in fc.keyframe_points]
            if xs and min(xs) < GAP_AT < max(xs):
                holds.append((fc, fc.evaluate(GAP_AT)))      # hold the final state of shot 9 throughout the inserted gap
            for kp in fc.keyframe_points:
                x = kp.co.x
                nx = rt(x)
                kp.co.x = nx
                # Bezier handles: stretched by the local factor around the key (keeps the curve shape)
                for h in ("handle_left", "handle_right"):
                    hv = getattr(kp, h)
                    hv.x = rt(hv.x) if abs(hv.x - x) > 1e-6 else nx
                n += 1
            for m in fc.modifiers:
                if getattr(m, "use_restricted_range", False):
                    m.frame_start, m.frame_end = rt(m.frame_start), rt(m.frame_end)
            fc.update()
    for fc, v in holds:
        kp = fc.keyframe_points.insert(KAME0, v, options={"FAST"})
        kp.interpolation = "CONSTANT"
        fc.update()
    for m in scene.timeline_markers:
        m.frame = int(round(rt(m.frame)))
    scene.frame_start, scene.frame_end = 0, int(round(RETIME[-1][1])) - 1
    scene["retime"] = json.dumps([[a, round(b, 2)] for a, b in RETIME])
    print("RETIME", n, "keys →", RETIME[-1][1], "frames", f"{RETIME[-1][1] / scene.render.fps:.1f}s")
