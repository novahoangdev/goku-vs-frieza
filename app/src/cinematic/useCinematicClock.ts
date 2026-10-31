import { useFrameCallback, useSharedValue, type SharedValue } from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";
import { DURATION, FPS, HAPTICS } from "./timeline";
import { fireHaptic } from "./haptics";

/**
 * Đồng hồ 120Hz khoá pha theo video: mỗi frame UI cộng dt rồi kéo nhẹ về `videoTime`
 * (video chỉ báo thời gian 60 lần/giây). Lệch quá 2 frame (seek, giật) thì nhảy thẳng.
 * Bắn haptic khi vượt qua marker và báo hết phim.
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
