# Frieza (final form) cho đúng chất hơn: chạy sau build_scene.py + frieza_details.py, dùng chung globals (F, M, helper...).
# - lỗ tai: viền tròn nổi quanh decal lỗ tai hai bên đầu
# - mọi vật fr_* thêm sau choreograph (extras) cũng tắt cùng Frieza ở frame 1151
import bpy
from mathutils import Vector


def _ff_try(label, fn):
    try:
        fn()
    except Exception as e:                       # một chi tiết hỏng không được làm hỏng cả bản dựng
        print("frieza_form:", label, "FAILED", repr(e))


def _ff_ears():
    head = bpy.data.objects["fr_head"]
    hc = head.location.copy()
    a, b, c = 0.18 * 1.0, 0.18 * 0.96, 0.18 * 1.02   # R_ * HS trong build_frieza
    rim_m = M["f_white"]
    hole = toon("fr_ear_hole", "#5E4C7E", "#3A2C55", threshold=0.3)
    for side, sgn in (("R", 1), ("L", -1)):
        d = head_dir(180 + sgn * 90, 2)
        if "fr_head_frame" in globals():         # v17 đầu không còn là elip: lấy điểm + pháp tuyến từ hàm bề mặt đầu
            p, n = fr_head_frame(d)
        else:
            p = d / ((d.x / a) ** 2 + (d.y / b) ** 2 + (d.z / c) ** 2) ** 0.5
            n = Vector((p.x / a ** 2, p.y / b ** 2, p.z / c ** 2)).normalized()
        q = n.to_track_quat("Z", "Y")
        rim = torus(f"fr_ear_rim_{side}", 0.0145, 0.0055, rim_m, C_FRIEZA, seg=24, ring=8, scale=(1.0, 1.0, 1.0), outline=0.0025)
        rim.parent = F["head"]
        rim.location = hc + p + n * 0.001
        rim.rotation_mode = "QUATERNION"
        rim.rotation_quaternion = q
        rim.scale = (0.85, 1.25, 1.0)                # lỗ tai hơi dọc
        rim.visible_shadow = False
        dot = sphere(f"fr_ear_in_{side}", 1, hole, C_FRIEZA, (0.0105, 0.0105, 0.004), seg=16, outline=0)
        dot.parent = F["head"]
        dot.location = hc + p - n * 0.0008
        dot.rotation_mode = "QUATERNION"
        dot.rotation_quaternion = q
        dot.scale = (0.85, 1.25, 1.0)
        dot.visible_shadow = False


def _ff_vis():
    def keyed(o):
        ad = o.animation_data
        return ad and ad.action and any(fc.data_path == "hide_render" for fc in _fcurves(ad))
    late = [o for o in bpy.data.objects if o.name.startswith("fr_") and not keyed(o)]
    kvis(late, 1150, True)
    kvis(late, 1151, False)
    print("frieza_form: vis keyed", len(late))


for _l, _f in (("ears", _ff_ears), ("vis", _ff_vis)):
    _ff_try(_l, _f)
print("frieza_form: done")
