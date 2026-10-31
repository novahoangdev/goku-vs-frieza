# Xuất timeline.json cho app: toạ độ 2D (px trên plate 1152×2496) của các anchor theo từng frame,
# các track hiệu ứng keyframe trên Empty "FX", và marker (haptic, cut).
#
# Chạy: Blender -b blender/goku_vs_frieza.blend -P blender/scripts/bake_timeline.py
import bpy, json, os
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.context.scene
W, H = scene.render.resolution_x, scene.render.resolution_y
FPS = scene.render.fps
ANCHORS = {
    "goku_chest": "GOKU_chest_anchor",
    "goku_head": "GOKU_head_anchor",
    "goku_fist_r": "GOKU_fist_anchor",
    "frieza_chest": "FRIEZA_chest_anchor",
    "frieza_finger": "FRIEZA_finger_anchor",
    "beam_target": "BEAM_TARGET",
    "blast_point": "BLAST_POINT",
}
TRACKS = ["aura", "flash", "shake", "punch", "speedlines", "impact", "grade", "lightning",
          "shock_r", "shock_k", "title", "beam", "blast"]
fx = bpy.data.objects["FX"]
OUT = os.path.join(os.path.dirname(bpy.data.filepath), "..", "app", "assets", "cinematic", "timeline.json")

out = {"fps": FPS, "frames": 0, "plate": [W, H],
       "anchors": {k: [] for k in list(ANCHORS) + ["goku_trail"]}, "tracks": {k: [] for k in TRACKS + ["fxclock"]}}
clock = 0.0
hist = []                                                          # vị trí ngực Goku (world) các frame trước
for f in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(f)
    for name, obj in ANCHORS.items():
        world = bpy.data.objects[obj].matrix_world.translation
        v = world_to_camera_view(scene, scene.camera, world)      # x, y ∈ [0, 1] gốc dưới-trái; z = độ sâu
        out["anchors"][name] += [round(v.x * W, 1), round((1 - v.y) * H, 1), round(v.z, 2)]
    # goku_trail: chỗ Goku đã đi qua 0.25 s trước theo vận tốc hiện tại → app cho aura toé ngược hướng bay
    gc = bpy.data.objects[ANCHORS["goku_chest"]].matrix_world.translation.copy()
    vel = (gc - hist[-4]) / 4 if len(hist) >= 4 else gc * 0
    if vel.length > 1.5:                                           # dịch chuyển tức thời / qua cut: bỏ
        vel *= 0
    hist.append(gc)
    v = world_to_camera_view(scene, scene.camera, gc - vel * 15)
    out["anchors"]["goku_trail"] += [round(v.x * W, 1), round((1 - v.y) * H, 1), round(v.z, 2)]
    for k in TRACKS:
        out["tracks"][k].append(round(float(fx[k]), 4))
    out["tracks"]["fxclock"].append(round(clock, 4))
    clock += float(fx["timescale"]) / FPS                          # slow-mo thì FX trong app chậm theo
    out["frames"] += 1

# bản đồ giãn nhịp frame cũ → mới (retime.py): app/promo/audio quy đổi các mốc thời gian viết theo phim 20 s cũ
out["retime"] = json.loads(scene.get("retime", "[[0, 0], [1200, 1200]]"))
out["markers"] = sorted(({"f": m.frame, "name": m.name} for m in scene.timeline_markers),
                        key=lambda m: m["f"])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as fp:
    json.dump(out, fp, separators=(",", ":"))
print("BAKED", os.path.abspath(OUT), out["frames"], "frames")
