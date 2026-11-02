import { useFrameCallback, useSharedValue, type SharedValue } from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";
import { DURATION, FPS, HAPTICS } from "./timeline";
import { fireHaptic } from "./haptics";

/**
 * 120Hz clock phase-locked to the video: each UI frame adds dt, then nudges toward `videoTime`
 * (the video only reports its time 60 times/s). Drift beyond 2 frames (seek, hitch) snaps straight to it.
 * Fires haptics when passing markers and reports the end of the film.
 */
export function useCinematicClock(
  videoTime: SharedValue<number>,
  playing: SharedValue<boolean>,
  onEnd: () => void,
) {
  const t = useSharedValue(0);
  const lastT = useSharedValue(0);

  useFrameCallback(({ timeSincePreviousFrame }) => {
    "worklet";
    const vt = videoTime.get();
    if (!playing.get()) {
      t.set(vt);
      lastT.set(vt);
      return;
    }
    const next = t.get() + (timeSincePreviousFrame ?? 0) / 1000;
    const err = vt - next;
    const now = Math.abs(err) > 2 / FPS ? vt : next + err * 0.1;
    t.set(now);
    const prev = lastT.get();
    for (let i = 0; i < HAPTICS.length; i++) {
      const h = HAPTICS[i];
      if (prev < h.t && now >= h.t) scheduleOnRN(fireHaptic, h.style);
    }
    lastT.set(now);
    if (vt >= DURATION - 1.5 / FPS) {
      playing.set(false);
      scheduleOnRN(onEnd);
    }
  });

  return t;
}
