import React from "react";
import { BlurMask, Group, Path, usePathValue, type SkSize } from "react-native-skia";
import { useDerivedValue, type SharedValue } from "react-native-reanimated";
import { FPS, hash, lastCut, track } from "../timeline";

const BOLT_EVERY = 0.32; // giây
const BOLT_LIFE = 0.13;

/** Sét tím trên trời: mỗi ~0.3s một tia mới (seed đổi theo cut), sống 0.13s, nhấp nháy 2 nhịp. */
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
    // 2 tia, đi từ mép trên xuống ~40% màn hình, đường gấp khúc kiểu midpoint displacement
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
          // nhánh phụ
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
