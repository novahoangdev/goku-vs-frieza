#!/usr/bin/env bash
# Chốt một bản nâng cấp để so sánh: build app Release (chế độ demo) → quay simulator → dựng clip 4:3
# → chép clip, bản quay, video đóng gói, timeline và vài khung beauty vào versions/<tên>/.
#   tools/capture-version.sh v2 <udid>
set -eo pipefail
cd "$(dirname "$0")/.."
NAME=${1:?tên bản, vd v2}
UDID=${2:?udid simulator}
OUT=versions/$NAME
mkdir -p "$OUT/stills"

# chép phần render trước, để bản build sau có ghi đè render/ thì bản này vẫn còn nguyên
cp app/assets/cinematic/cinematic.mp4 "$OUT/cinematic-packed.mp4"
cp app/assets/cinematic/timeline.json "$OUT/timeline.json"
cp render/audio/mix.wav "$OUT/mix.wav"
# khung tiêu biểu (frame theo phim 20 s gốc → quy đổi sang phim đã giãn nhịp)
for f in $( (python3 tools/rt.py frame 60 200 330 450 560 700 870 1005 1060 1150; \
             python3 tools/rt.py marker kame:start 130 kame:fire 8 kame:hit 40) | xargs printf '%04d '); do
  [[ -f render/beauty/$f.png ]] && ffmpeg -y -loglevel error -i "render/beauty/$f.png" -q:v 3 "$OUT/stills/$f.jpg" || true
done

# poster màn gồng Ki = khung anh hùng cuối phim của chính bản này
HERO=$(printf '%04d' "$(python3 tools/rt.py frame 1150)")
[[ -f render/beauty/$HERO.png ]] && ffmpeg -y -loglevel error -i render/beauty/$HERO.png \
  -vf "crop=1080:2340:36:78,scale=720:1560:flags=lanczos" -q:v 4 app/assets/cinematic/poster.jpg

(cd app && EXPO_PUBLIC_DEMO=1 CI=1 npx expo run:ios --configuration Release --device "$UDID" --no-bundler) \
  > "render/release-$NAME.log" 2>&1 \
  || grep -q " 0 error(s)" "render/release-$NAME.log" \
  || { tail -20 "render/release-$NAME.log"; exit 1; }
# (build xong nhưng bước mở Simulator qua osascript đôi khi lỗi: app đã cài rồi, promo.sh tự mở lại nên bỏ qua)
LABEL="$NAME  /  $(date "+%d.%m  %H:%M")" PAUSE_PATTERN="${PAUSE_PATTERN:-}" tools/promo.sh "$UDID"
cp render/promo/saiyan-awakening-demo.mp4 "$OUT/saiyan-awakening-demo.mp4"
cp render/promo/screen.mp4 "$OUT/screen.mp4"
echo "CAPTURED $OUT"
ls -lh "$OUT"
