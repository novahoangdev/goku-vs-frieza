#!/usr/bin/env bash
# Toàn bộ pipeline: vẽ texture mặt → dựng scene → render 4 pass (beauty/matte/energy/depth) → bake timeline
# → tổng hợp âm thanh → pack video.
#   tools/build.sh            bản final (100%, 16 sample, motion blur)
#   PREVIEW=1 tools/build.sh  bản xem nhanh (50%, 6 sample)
set -eo pipefail
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
if [[ "${PREVIEW:-0}" == 1 ]]; then RARGS=(--pct 50 --samples 6); else RARGS=(--pct 100 --samples 16 --motion-blur); fi

"$(dirname "$BLENDER")/../Resources/5.2/python/bin/python3.13" blender/scripts/face_textures.py | tail -1
"$BLENDER" -b --factory-startup -P blender/scripts/build_scene.py 2>&1 | grep -E "SAVED|Error|Traceback" || true
"$BLENDER" -b blender/goku_vs_frieza.blend -P blender/scripts/bake_timeline.py 2>&1 | grep -E "BAKED|Error|Traceback" || true
"$BLENDER" -b blender/goku_vs_frieza.blend -P blender/scripts/render_passes.py -- --out render "${RARGS[@]}" "$@" 2>&1 \
  | grep -E "── render|Error|Traceback" || true
# nhạc nền riêng (tuỳ chọn): render/audio/bgm.mp3|m4a|aac|flac|ogg → bgm.wav 48 kHz; synth_audio dùng nó thay nhạc tổng hợp
for f in render/audio/bgm.{mp3,m4a,aac,flac,ogg}; do
  [[ -f "$f" ]] && ffmpeg -y -loglevel error -i "$f" -ar 48000 -ac 2 render/audio/bgm.wav && echo "BGM $f" && break
done
"$BLENDER" -b --factory-startup --python blender/scripts/synth_audio.py 2>&1 | grep -E "AUDIO|Error|Traceback" || true
tools/pack.sh
