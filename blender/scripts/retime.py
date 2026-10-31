# Giãn nhịp phim (v22): phim 20 s cắt cảnh quá nhanh nên cảm giác cụt ngủn. Ánh xạ frame cũ → frame mới tuyến tính
# từng đoạn theo shot, mỗi shot giãn một hệ số riêng: chậm nhiều ở mở màn, biến hình, cú đấm và cảnh kết; vừa phải ở
# đoạn combo/rượt đuổi cho còn dồn dập. Áp lên MỌI keyframe (vật, material, node, camera, FX) và marker trước khi lưu;
# bản đồ ghi vào scene["retime"] → bake_timeline chép sang timeline.json cho app, promo, audio, compare dùng chung.
import json
import bpy

# (frame cũ, frame mới) tại các điểm cắt cảnh; frame mới là số nguyên để cut rơi đúng frame
_SEG = [(0, 1.6), (120, 1.4), (240, 1.3), (300, 1.6), (390, 1.5), (510, 1.4), (600, 1.25), (690, 1.2),
        (780, 1.25), (990, 1.3), (1030, 1.5), (1110, 2.0), (1200, None)]
# v23: chèn đoạn Kamehameha (dài KAME_LEN frame mới) ngay trước shot kết: bản đồ có một bước nhảy dọc ở GAP_AT
# (frame gốc 1109.8 — sau key giữ-hình 1109.6 của cut 1110, trước chính cut đó). Mọi nơi đọc bản đồ (app, promo,
# audio, tools) đều tìm đoạn đầu tiên có f <= b nên đoạn dài 0 ở bước nhảy không bao giờ bị chia cho 0.
GAP_AT, KAME_LEN = 1109.8, 330
RETIME = [(0, 0)]
for (a, k), (b, _) in zip(_SEG, _SEG[1:]):
    if a < GAP_AT < b:
        RETIME.append((GAP_AT, RETIME[-1][1] + (GAP_AT - a) * k))
        RETIME.append((GAP_AT, RETIME[-1][1] + KAME_LEN))
        RETIME.append((b, RETIME[-1][1] + (b - GAP_AT) * k))
        continue
    RETIME.append((b, RETIME[-1][1] + round((b - a) * k)))
KAME0 = int(round(RETIME[[x for x, _ in RETIME].index(GAP_AT)][1] + 0.5))   # frame mới đầu tiên của đoạn Kamehameha
KAME1 = KAME0 + KAME_LEN                                                     # = cut vào shot kết


def rt(f):
    """frame cũ → frame mới (ngoài khoảng: ngoại suy theo hệ số đoạn đầu/cuối)."""
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
                holds.append((fc, fc.evaluate(GAP_AT)))      # giữ nguyên trạng thái cuối shot 9 suốt khoảng chèn
            for kp in fc.keyframe_points:
                x = kp.co.x
                nx = rt(x)
                kp.co.x = nx
                # tay cầm Bezier: giãn theo hệ số cục bộ quanh key (giữ dáng đường cong)
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
