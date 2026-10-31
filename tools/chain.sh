#!/usr/bin/env bash
# Nối các bước nâng cấp liên tục: chờ render vN xong và capture vN-1 xong → capture vN (tạm dừng render lúc quay)
# → quay xong thì bắt đầu render vN+1 ngay (build_scene đọc code mới nhất lúc đó).
#   tools/chain.sh 3 <udid>       (cần render/v3-build.log đang chạy và render/capture-v2.log)
set -o pipefail
cd "$(dirname "$0")/.."
N=${1:?số bản}
UDID=${2:?udid}
P=$((N - 1)); NX=$((N + 1))
until grep -q "V${N}_DONE" "render/v${N}-build.log" 2>/dev/null; do sleep 5; done
until grep -q "CAPTURE_EXIT" "render/capture-v${P}.log" 2>/dev/null; do sleep 5; done
echo "chain: v${N} render xong, bắt đầu capture"
( PAUSE_PATTERN="render_passes.py" tools/capture-version.sh "v${N}" "$UDID" > "render/capture-v${N}.log" 2>&1
  echo "CAPTURE_EXIT $?" >> "render/capture-v${N}.log" ) &
until grep -qE "flash ở|CAPTURE_EXIT" "render/capture-v${N}.log" 2>/dev/null; do sleep 3; done
echo "chain: đã quay v${N}, bắt đầu render v${NX}"
( (time tools/build.sh) > "render/v${NX}-build.log" 2>&1; echo "V${NX}_DONE $?" >> "render/v${NX}-build.log" ) &
wait
echo "chain: xong capture v${N} và render v${NX}"
tail -3 "render/capture-v${N}.log"
