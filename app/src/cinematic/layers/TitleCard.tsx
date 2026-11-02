import React, { useMemo } from "react";
import { Group, LinearGradient, Text, matchFont, vec, type SkSize } from "react-native-skia";
import { useDerivedValue, type SharedValue } from "react-native-reanimated";
import { track } from "../timeline";

const TITLE = "SUPER SAIYAN";
const SUB = "THE LEGENDARY WARRIOR";

/** Gold end-of-film title: pops in with a spring while a light sweep crosses the text. */
export function TitleCard({ t, size }: { t: SharedValue<number>; size: SkSize }) {
  const big = useMemo(() => matchFont({ fontFamily: "Avenir Next", fontSize: 58, fontWeight: "900", fontStyle: "italic" }), []);
  const small = useMemo(() => matchFont({ fontFamily: "Avenir Next", fontSize: 17, fontWeight: "800" }), []);
  const w1 = big.measureText(TITLE).width;
  const w2 = small.measureText(SUB).width;
  const cx = size.width / 2;
  const cy = size.height * 0.8;
  // 58pt text is wider than the 402pt screen: scale it to fit with a 20pt margin each side (even at the 10% overshoot)
  const fit = Math.min(1, (size.width - 40) / ((w1 + 8) * 1.1));

  const k = useDerivedValue(() => track("title", t.value));
  const transform = useDerivedValue(() => {
    const x = k.value;
    // spring bounce: overshoots 1 by 10%, then settles at 1
    const s = (0.6 + 0.4 * x + 0.3 * Math.sin(x * Math.PI) * x) * fit;
    return [{ translateX: cx }, { translateY: cy }, { scale: s }, { skewX: -0.08 }];
  });
  const opacity = useDerivedValue(() => Math.min(1, k.value * 2.5));
  const shine = useDerivedValue(() => {
    const p = ((t.value * 0.55) % 1) * (w1 + 300) - w1 / 2 - 150;
    return [vec(p, 0), vec(p + 90, 0)];
  });
  const shineStart = useDerivedValue(() => shine.value[0]);
  const shineEnd = useDerivedValue(() => shine.value[1]);

  return (
    <Group transform={transform} opacity={opacity}>
      {/* red-orange drop shadow behind, anime-logo style */}
      <Text x={-w1 / 2 + 4} y={6} text={TITLE} font={big} color="#7A1F0B" />
      <Text x={-w1 / 2} y={0} text={TITLE} font={big}>
        <LinearGradient start={vec(0, -44)} end={vec(0, 6)} colors={["#FFF6C8", "#FFD23F", "#FF9F1C"]} />
      </Text>
      <Text x={-w1 / 2} y={0} text={TITLE} font={big} blendMode="plus">
        <LinearGradient start={shineStart} end={shineEnd} colors={["#FFFFFF00", "#FFFFFFCC", "#FFFFFF00"]} />
      </Text>
      <Text x={-w2 / 2} y={40} text={SUB} font={small} color="#FFF3B0" />
    </Group>
  );
}
