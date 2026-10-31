# Dọn đá vụn bay lên sát camera (shot quay thấp vòng quanh Goku lúc gồng): hòn nào có lúc cách camera < 2.4 m trong
# frame 100–390 thì dời ra xa camera bằng delta_location (giữ nguyên keyframe bay lên/văng ra), để không che Goku.
import bpy
from mathutils import Vector

_scn = bpy.context.scene
_cam = _scn.camera
_moved = 0
for _d, _a, _r in debris:
    _worst = None
    for _f in range(100, 391, 3):
        _scn.frame_set(_f)
        _c = _cam.matrix_world.translation
        _p = _d.matrix_world.translation
        _v = _p - _c
        _fwd = _cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        if _v.dot(_fwd) <= 0:
            continue                       # sau lưng camera thì không thấy
        if _worst is None or _v.length < _worst[0]:
            _worst = (_v.length, Vector((_v.x, _v.y, 0)))
    if _worst and _worst[0] < 2.4:
        _dir = _worst[1].normalized() if _worst[1].length > 1e-4 else Vector((1, 0, 0))
        _d.delta_location = _dir * (2.4 - _worst[0] + 1.6)
        _moved += 1
_scn.frame_set(0)
print("DEBRIS_CLEAR moved", _moved)
