#!/usr/bin/env bash
# Record the app on the simulator, then build a 4:3 demo clip to post on X.
#   tools/promo.sh <udid>      (Release app built with EXPO_PUBLIC_DEMO=1, already installed on the simulator)
# Output: render/promo/saiyan-awakening-demo.mp4 (H.264 1920×1440 60fps + AAC) and screen.mp4 (the raw screen recording)
set -eo pipefail
cd "$(dirname "$0")/.."
UDID=${1:?udid}
APP=dev.hoanghoa.saiyanawakening
OUT=render/promo
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
mkdir -p "$OUT"

# 1. clean marketing-style status bar
xcrun simctl status_bar "$UDID" override --time 9:41 --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 --wifiBars 3 --dataNetwork wifi

# 2. record: Ki charge intro (~3s) + film (~29s after retiming) + title/replay button
#    PAUSE_PATTERN="render_passes.py": pause the background render while recording so the simulator doesn't stutter
PIDS=""
if [[ -n "${PAUSE_PATTERN:-}" ]]; then PIDS=$(pgrep -f "$PAUSE_PATTERN" || true); fi
resume() { [[ -n "$PIDS" ]] && kill -CONT $PIDS 2>/dev/null || true; }
trap resume EXIT
[[ -n "$PIDS" ]] && kill -STOP $PIDS && sleep 2
xcrun simctl terminate "$UDID" "$APP" 2>/dev/null || true
rm -f "$OUT/raw.mov"
xcrun simctl io "$UDID" recordVideo --codec=h264 --force "$OUT/raw.mov" >/dev/null 2>&1 &
REC=$!
sleep 1.5
xcrun simctl launch "$UDID" "$APP" >/dev/null
FILM_DUR=$(python3 tools/rt.py dur)
sleep "$(python3 -c "print(round($FILM_DUR + 9))")"
kill -INT "$REC"; wait "$REC" 2>/dev/null || true
resume

# 3. resample to constant 60fps (the simulator records a variable frame rate)
ffmpeg -y -loglevel error -i "$OUT/raw.mov" -vf "fps=60,scale=1206:2622:flags=lanczos" -c:v libx264 -crf 14 -pix_fmt yuv420p -an "$OUT/screen.mp4"

# 4. find the film start: the brightest frame in the first 18s is the transformation flash (frame 303 of the original film → mapped)
PEAK=$(ffmpeg -loglevel error -t 18 -i "$OUT/screen.mp4" -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - \
  | awk '/pts_time/{split($0,a,"pts_time:"); t=a[2]} /YAVG/{split($0,b,"="); if (b[2]>m){m=b[2]; best=t}} END{print best}')
FLASH=$(python3 tools/rt.py frame 303)
FILM0=$(python3 -c "print(round(max(0.0, $PEAK - $FLASH/60), 3))")
echo "flash at ${PEAK}s → film starts at ${FILM0}s in the recording"

# 5. build the 4:3 clip in Blender
rm -rf "$OUT/frames"
"$BLENDER" -b --factory-startup -P blender/scripts/promo.py -- --screen "$OUT/screen.mp4" --film-start "$FILM0" \
  --out "$OUT/frames" --label "${LABEL:-}" 2>&1 | grep -E "PROMO|Error|Traceback" || true

# 6. add audio (the film starts at second 3 of the clip) + a soft riser for the intro, export for X
ffmpeg -y -loglevel error -stats \
  -framerate 60 -i "$OUT/frames/%04d.png" \
  -i render/audio/mix.wav \
  -f lavfi -i "aevalsrc=0.12*sin(2*PI*(70+45*t)*t)*(t/3)*lt(t\,3):s=48000:d=3.2" \
  -filter_complex "[1:a]adelay=3000|3000,apad[m];[2:a]apad[r];[m][r]amix=inputs=2:normalize=0,afade=t=out:st=$(python3 -c "print(round($FILM_DUR + 5.2, 2))"):d=1.8[a]" \
  -map 0:v -map "[a]" -shortest \
  -c:v libx264 -profile:v high -preset slow -crf 17 -pix_fmt yuv420p -r 60 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  "$OUT/saiyan-awakening-demo.mp4"
xcrun simctl status_bar "$UDID" clear || true   # the sim may have been shut down by hand after recording
ls -lh "$OUT/saiyan-awakening-demo.mp4"
