import React from "react";
import { BlurMask, Group, Path, usePathValue, type SkSize } from "react-native-skia";
import { useDerivedValue, type SharedValue } from "react-native-reanimated";
import { FPS, hash, lastCut, track } from "../timeline";

const BOLT_EVERY = 0.32; // seconds
const BOLT_LIFE = 0.13;

/** Purple sky lightning: a new bolt every ~0.3s (seed changes per cut), lives 0.13s, flickers twice. */
export function Lightning({ t, size }: { t: SharedValue<number>; size: SkSize }) {
  const strength = useDerivedValue(() => {
    const tt = t.value;
    const k = track("lightning", tt);
    const age = (tt % BOLT_EVERY) / BOLT_LIFE;
    const seed = Math.floor(tt / BOLT_EVERY) + lastCut(tt * FPS) * 0.37;
    if (age > 1 || hash(seed * 3.1) > k) return 0;
    return age < 0.35 || (age > 0.55 && age < 0.8) ? 1 : 0.25;
  });

  const path = usePathValue((b) => {
    "worklet";
    const tt = t.value;
    const seed = Math.floor(tt / BOLT_EVERY) + lastCut(tt * FPS) * 0.37;
    const w = size.width;
    const h = size.height;
    // 2 bolts from the top edge down to ~40% of the screen, jagged paths via midpoint displacement
    for (let k = 0; k < 2; k++) {
      let x = w * (0.1 + 0.8 * hash(seed + k * 17.3));
      let y = -10;
      const endY = h * (0.22 + 0.22 * hash(seed + k * 5.1));
      const steps = 11;
      b.moveTo(x, y);
      for (let i = 1; i <= steps; i++) {
        x += (hash(seed * 7.7 + i * 1.31 + k) - 0.5) * w * 0.16;
        y = (endY * i) / steps;
        b.lineTo(x, y);
        if (i === 5 && hash(seed + k + 9.9) > 0.4) {
          // side branch
          const bx = x + (hash(seed + 2.2 + k) - 0.5) * w * 0.3;
          b.lineTo(bx, y + h * 0.06);
          b.moveTo(x, y);
        }
      }
    }
  });

  const glowOpacity = useDerivedValue(() => strength.value * 0.9);
  const coreOpacity = useDerivedValue(() => strength.value);

  return (
    <Group blendMode="plus">
      <Path path={path} style="stroke" strokeWidth={9} color="#A27BFF" opacity={glowOpacity} strokeJoin="round">
        <BlurMask blur={10} style="normal" />
      </Path>
      <Path path={path} style="stroke" strokeWidth={2.2} color="#F1E6FF" opacity={coreOpacity} strokeJoin="round" />
    </Group>
  );
}
