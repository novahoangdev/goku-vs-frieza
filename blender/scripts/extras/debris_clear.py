# Clears debris flying up close to the camera (low shot circling Goku while he charges Ki): any rock that gets within 2.4 m of the camera in
# frames 100–390 is pushed away from the camera via delta_location (flying-up/flung-out keyframes kept), so it doesn't cover Goku.
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
            continue                       # behind the camera: not visible
        if _worst is None or _v.length < _worst[0]:
            _worst = (_v.length, Vector((_v.x, _v.y, 0)))
    if _worst and _worst[0] < 2.4:
        _dir = _worst[1].normalized() if _worst[1].length > 1e-4 else Vector((1, 0, 0))
        _d.delta_location = _dir * (2.4 - _worst[0] + 1.6)
        _moved += 1
_scn.frame_set(0)
print("DEBRIS_CLEAR moved", _moved)
