#!/usr/bin/env python3
"""Map times in the original 20 s film to the retimed film (the "retime" map in timeline.json).
  python3 tools/rt.py frame 303 1150 [--tl path]   → new frames (rounded)
  python3 tools/rt.py sec 5.05                      → new seconds
  python3 tools/rt.py dur                           → film length (seconds)
  python3 tools/rt.py marker kame:fire 8 [...]      → new marker frame + offset (inserted segments missing from the original film)"""
import json, sys

args = sys.argv[1:]
tl_path = "app/assets/cinematic/timeline.json"
if "--tl" in args:
    i = args.index("--tl"); tl_path = args[i + 1]; del args[i:i + 2]
TL = json.load(open(tl_path))
RT = TL.get("retime", [[0, 0], [1200, 1200]])


def rtf(f):
    for (a, na), (b, nb) in zip(RT, RT[1:]):
        if f <= b or [b, nb] == RT[-1]:
            return na + (f - a) * (nb - na) / (b - a)
    return f


mode = args[0]
if mode == "marker":
    out = []
    for name, off in zip(args[1::2], args[2::2]):
        m = next((m["f"] for m in TL["markers"] if m["name"] == name), None)
        if m is not None:
            out.append(str(m + int(off)))
    print(" ".join(out))
    sys.exit(0)
vals = [float(x) for x in args[1:]]
if mode == "dur":
    print(f"{TL['frames'] / TL['fps']:.3f}")
elif mode == "frame":
    print(" ".join(str(round(rtf(v))) for v in vals))
else:
    print(" ".join(f"{rtf(v * TL['fps']) / TL['fps']:.3f}" for v in vals))
