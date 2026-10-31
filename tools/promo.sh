#!/usr/bin/env bash
# Quay app trên simulator rồi dựng clip demo 4:3 để đăng X.
#   tools/promo.sh <udid>      (app bản Release, build với EXPO_PUBLIC_DEMO=1, đã cài trên simulator)
# Ra: render/promo/saiyan-awakening-demo.mp4 (H.264 1920×1440 60fps + AAC) và screen.mp4 (bản quay màn hình gốc)
set -eo pipefail
cd "$(dirname "$0")/.."
UDID=${1:?udid}
APP=dev.hoanghoa.saiyanawakening
OUT=render/promo
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
mkdir -p "$OUT"

# 1. status bar sạch kiểu ảnh quảng cáo
xcrun simctl status_bar "$UDID" override --time 9:41 --batteryState charged --batteryLevel 100 \
  --cellularMode active --cellularBars 4 --wifiBars 3 --dataNetwork wifi

# 2. quay: intro gồng Ki (~3s) + phim (~29s sau khi giãn nhịp) + title/nút xem lại
#    PAUSE_PATTERN="render_passes.py": tạm dừng render nền trong lúc quay để simulator không bị giật
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

# 3. về 60fps đều (simulator ghi frame rate thay đổi)
ffmpeg -y -loglevel error -i "$OUT/raw.mov" -vf "fps=60,scale=1206:2622:flags=lanczos" -c:v libx264 -crf 14 -pix_fmt yuv420p -an "$OUT/screen.mp4"

# 4. dò lúc phim bắt đầu: khung sáng nhất trong 18s đầu là flash biến hình (frame 303 của phim gốc → quy đổi)
PEAK=$(ffmpeg -loglevel error -t 18 -i "$OUT/screen.mp4" -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - \
  | awk '/pts_time/{split($0,a,"pts_time:"); t=a[2]} /YAVG/{split($0,b,"="); if (b[2]>m){m=b[2]; best=t}} END{print best}')
FLASH=$(python3 tools/rt.py frame 303)
FILM0=$(python3 -c "print(round(max(0.0, $PEAK - $FLASH/60), 3))")
echo "flash ở ${PEAK}s → phim bắt đầu ở ${FILM0}s trong bản quay"

# 5. dựng clip 4:3 trong Blender
rm -rf "$OUT/frames"
"$BLENDER" -b --factory-startup -P blender/scripts/promo.py -- --screen "$OUT/screen.mp4" --film-start "$FILM0" \
  --out "$OUT/frames" --label "${LABEL:-}" 2>&1 | grep -E "PROMO|Error|Traceback" || true

# 6. ghép tiếng (phim bắt đầu ở giây 3 của clip) + riser nhẹ cho đoạn intro, xuất cho X
ffmpeg -y -loglevel error -stats \
  -framerate 60 -i "$OUT/frames/%04d.png" \
  -i render/audio/mix.wav \
  -f lavfi -i "aevalsrc=0.12*sin(2*PI*(70+45*t)*t)*(t/3)*lt(t\,3):s=48000:d=3.2" \
  -filter_complex "[1:a]adelay=3000|3000,apad[m];[2:a]apad[r];[m][r]amix=inputs=2:normalize=0,afade=t=out:st=$(python3 -c "print(round($FILM_DUR + 5.2, 2))"):d=1.8[a]" \
  -map 0:v -map "[a]" -shortest \
  -c:v libx264 -profile:v high -preset slow -crf 17 -pix_fmt yuv420p -r 60 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  "$OUT/saiyan-awakening-demo.mp4"
xcrun simctl status_bar "$UDID" clear || true   # sim có thể đã bị tắt tay sau khi quay xong
ls -lh "$OUT/saiyan-awakening-demo.mp4"
