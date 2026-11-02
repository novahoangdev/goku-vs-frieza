#!/usr/bin/env bash
# Snapshot an upgrade for comparison: build the Release app (demo mode) → record the simulator → make the 4:3 clip
# → copy the clip, screen recording, packed video, timeline and a few beauty frames into versions/<name>/.
#   tools/capture-version.sh v2 <udid>
set -eo pipefail
cd "$(dirname "$0")/.."
NAME=${1:?version name, e.g. v2}
UDID=${2:?simulator udid}
OUT=versions/$NAME
mkdir -p "$OUT/stills"

# copy the render outputs first so this version stays intact even if a later build overwrites render/
cp app/assets/cinematic/cinematic.mp4 "$OUT/cinematic-packed.mp4"
cp app/assets/cinematic/timeline.json "$OUT/timeline.json"
cp render/audio/mix.wav "$OUT/mix.wav"
# key frames (frames in the original 20 s film → mapped to the retimed film)
for f in $( (python3 tools/rt.py frame 60 200 330 450 560 700 870 1005 1060 1150; \
             python3 tools/rt.py marker kame:start 130 kame:fire 8 kame:hit 40) | xargs printf '%04d '); do
  [[ -f render/beauty/$f.png ]] && ffmpeg -y -loglevel error -i "render/beauty/$f.png" -q:v 3 "$OUT/stills/$f.jpg" || true
done

# Ki charge screen poster = this version's own final hero frame
HERO=$(printf '%04d' "$(python3 tools/rt.py frame 1150)")
[[ -f render/beauty/$HERO.png ]] && ffmpeg -y -loglevel error -i render/beauty/$HERO.png \
  -vf "crop=1080:2340:36:78,scale=720:1560:flags=lanczos" -q:v 4 app/assets/cinematic/poster.jpg

(cd app && EXPO_PUBLIC_DEMO=1 CI=1 npx expo run:ios --configuration Release --device "$UDID" --no-bundler) \
  > "render/release-$NAME.log" 2>&1 \
  || grep -q " 0 error(s)" "render/release-$NAME.log" \
  || { tail -20 "render/release-$NAME.log"; exit 1; }
# (the build succeeds but opening Simulator via osascript sometimes fails: the app is installed and promo.sh relaunches it, so ignore it)
LABEL="$NAME  /  $(date "+%d.%m  %H:%M")" PAUSE_PATTERN="${PAUSE_PATTERN:-}" tools/promo.sh "$UDID"
cp render/promo/saiyan-awakening-demo.mp4 "$OUT/saiyan-awakening-demo.mp4"
cp render/promo/screen.mp4 "$OUT/screen.mp4"
echo "CAPTURED $OUT"
ls -lh "$OUT"
