#!/usr/bin/env bash
# Chain upgrade steps back to back: wait for render vN and capture vN-1 to finish → capture vN (render paused while recording)
# → once recorded, start rendering vN+1 right away (build_scene picks up the latest code at that point).
#   tools/chain.sh 3 <udid>       (needs a running render/v3-build.log and render/capture-v2.log)
set -o pipefail
cd "$(dirname "$0")/.."
N=${1:?version number}
UDID=${2:?udid}
P=$((N - 1)); NX=$((N + 1))
until grep -q "V${N}_DONE" "render/v${N}-build.log" 2>/dev/null; do sleep 5; done
until grep -q "CAPTURE_EXIT" "render/capture-v${P}.log" 2>/dev/null; do sleep 5; done
echo "chain: v${N} render done, starting capture"
( PAUSE_PATTERN="render_passes.py" tools/capture-version.sh "v${N}" "$UDID" > "render/capture-v${N}.log" 2>&1
  echo "CAPTURE_EXIT $?" >> "render/capture-v${N}.log" ) &
until grep -qE "flash at|CAPTURE_EXIT" "render/capture-v${N}.log" 2>/dev/null; do sleep 3; done
echo "chain: recorded v${N}, starting render v${NX}"
( (time tools/build.sh) > "render/v${NX}-build.log" 2>&1; echo "V${NX}_DONE $?" >> "render/v${NX}-build.log" ) &
wait
echo "chain: finished capture v${N} and render v${NX}"
tail -3 "render/capture-v${N}.log"
