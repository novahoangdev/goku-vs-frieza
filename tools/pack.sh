#!/usr/bin/env bash
# Gộp 4 chuỗi PNG (beauty / matte / energy / depth) + tiếng thành 1 video pack 2304×2496 cho app:
#   beauty 1152×2496 | matte 576×1248 trên energy 576×1248 | depth 576×1248 (nửa dưới cột cuối để đen)
#   PREVIEW=1 tools/pack.sh   → encoder phần cứng của Mac (nhanh), bỏ qua chất lượng
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=app/assets/cinematic/cinematic.mp4
AUDIO=render/audio/mix.wav
mkdir -p "$(dirname "$OUT")"

audio_in=(); audio_map=(); audio_enc=(-an)
if [[ -f "$AUDIO" ]]; then
  audio_in=(-i "$AUDIO"); audio_map=(-map 4:a); audio_enc=(-c:a aac -b:a 192k -ar 48000)
fi
if [[ "${PREVIEW:-0}" == 1 ]]; then
  venc=(-c:v hevc_videotoolbox -q:v 70 -profile:v main10 -pix_fmt p010le)
  fmt=p010le
else
  venc=(-c:v libx265 -preset slow -crf 17 -x265-params keyint=60:min-keyint=60:log-level=error -pix_fmt yuv420p10le)
  fmt=yuv420p10le
fi

ffmpeg -y -loglevel error -stats \
  -framerate 60 -i render/beauty/%04d.png \
  -framerate 60 -i render/matte/%04d.png \
  -framerate 60 -i render/energy/%04d.png \
  -framerate 60 -i render/depth/%04d.png \
  "${audio_in[@]}" \
  -filter_complex "
    [1:v]format=gray16le,scale=576:1248:flags=area,format=gbrp16le[m];
    [2:v]format=gray16le,scale=576:1248:flags=area,format=gbrp16le[e];
    [m][e]vstack=inputs=2[data];
    [3:v]format=gray16le,scale=576:1248:flags=neighbor,pad=576:2496:0:0:black,format=gbrp16le[d];
    [0:v]scale=1152:2496:flags=lanczos,format=gbrp16le[b];
    [b][data][d]hstack=inputs=3,scale=out_color_matrix=bt709:out_range=tv,format=$fmt[v]" \
  -map "[v]" "${audio_map[@]}" -r 60 \
  "${venc[@]}" -tag:v hvc1 -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  "${audio_enc[@]}" -shortest -movflags +faststart \
  "$OUT"
ls -lh "$OUT"
