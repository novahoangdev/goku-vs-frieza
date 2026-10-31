#!/usr/bin/env bash
# Chạy app trên simulator ở chế độ tự phát, chụp màn hình theo nhịp để xem nhanh cả phim.
#   tools/sim-shots.sh <udid> <thư mục ảnh> [start_at giây] [số ảnh] [khoảng cách giây]
set -eo pipefail
cd "$(dirname "$0")/../app"
UDID=$1; OUT=$2; START=${3:-0}; N=${4:-10}; GAP=${5:-2}
mkdir -p "$OUT"
pkill -f "expo start" 2>/dev/null || true
EXPO_PUBLIC_AUTOPLAY=1 EXPO_PUBLIC_START_AT=$START npx expo start --dev-client --clear --port 8081 >"$OUT/metro.log" 2>&1 &
until curl -s localhost:8081/status | grep -q running; do sleep 1; done
xcrun simctl terminate "$UDID" dev.hoanghoa.saiyanawakening 2>/dev/null || true
xcrun simctl openurl "$UDID" "exp+saiyan-awakening://expo-development-client/?url=http%3A%2F%2Flocalhost%3A8081&disableOnboarding=1"
# chờ bundle tải xong và video có frame đầu
until grep -qE "Bundled|bundled" "$OUT/metro.log"; do sleep 1; done
sleep 4
for i in $(seq 1 "$N"); do
  xcrun simctl io "$UDID" screenshot --type=png "$OUT/s$(printf %02d $i).png" >/dev/null 2>&1
  sleep "$GAP"
done
echo "SHOTS $OUT"
