import React from "react";
import {
  Atlas,
  Circle,
  Group,
  RadialGradient,
  useRSXformBuffer,
  useRectBuffer,
  useTexture,
  vec,
  type SkSize,
} from "react-native-skia";
import { useDerivedValue, type SharedValue } from "react-native-reanimated";
import { FPS, anchor, hash, lastCut, rts, track } from "../timeline";

const D0 = rts(2), D1 = rts(5); // bụi bay lúc gồng (mốc theo phim 20 s gốc)
import { coverScale, plateToScreen, type Cam } from "../camera";

const COUNT = 220;
const TEX = 32;
const PERIOD = 1.3; // giây một vòng đời hạt

/**
 * Tia lửa vàng bay lên quanh Goku (theo aura) + bụi lơ lửng lúc gồng.
 * Hạt "stateless": vị trí tính thẳng từ seed và fxclock, đổi seed sau mỗi cut.
 */
export function Sparks({
  t,
  videoTime,
  cam,
  size,
}: {
  t: SharedValue<number>;
  videoTime: SharedValue<number>;
  cam: SharedValue<Cam>;
  size: SkSize;
}) {
  const texture = useTexture(
    <Circle cx={TEX / 2} cy={TEX / 2} r={TEX / 2}>
      <RadialGradient c={vec(TEX / 2, TEX / 2)} r={TEX / 2} colors={["#FFFBEA", "#FFD23F", "#FF9F1C00"]} positions={[0, 0.35, 1]} />
    </Circle>,
    { width: TEX, height: TEX },
  );
  const sprites = useRectBuffer(COUNT, (rect) => {
    "worklet";
    rect.setXYWH(0, 0, TEX, TEX);
  });

  const state = useDerivedValue(() => {
    const tt = t.value;
    const vf = videoTime.value * FPS;
    const chest = anchor("goku_chest", vf);
    const pxScale = coverScale(size.width, size.height);
    const [sx, sy] = plateToScreen(chest[0], chest[1], cam.value, size.width, size.height, pxScale);
    const aura = chest[2] > 0 ? track("aura", tt) : 0;
    const dust = tt > D0 && tt < D1 ? 1 : 0;
    // độ lớn của Goku trên màn hình: khoảng cách đầu–ngực (130px plate ≈ cảnh trung)
    const head = anchor("goku_head", vf);
    const scale = chest[2] > 0 ? Math.min(3, Math.hypot(head[0] - chest[0], head[1] - chest[1]) / 130 / pxScale * 2.7) : 0;
    return { sx, sy, aura, dust, scale, clock: track("fxclock", tt), seed: lastCut(vf) * 0.013 };
  });

  const transforms = useRSXformBuffer(COUNT, (xf, i) => {
    "worklet";
    const s = state.value;
    const r1 = hash(i + s.seed);
    const r2 = hash(i * 1.7 + 3.3 + s.seed);
    const phase = (s.clock / PERIOD + r1) % 1;
    const isDust = i % 3 === 0;
    const k = isDust ? s.dust : s.aura;
    const spread = (isDust ? 260 : 95) * s.scale;
    // hạt khí bốc dọc hai mép người (như lửa aura), không rải đều lên mặt/thân: |lệch ngang| ≥ 35% bề rộng vùng hạt
    const side = r2 < 0.5 ? -1 : 1;
    const off = isDust ? (r2 - 0.5) * spread : side * (0.35 + 0.65 * Math.abs(r2 - 0.5) * 2) * spread * 0.5;
    const x = s.sx + off * (1 + phase * 0.6);
    const y = s.sy + (isDust ? 160 : 70) * s.scale - phase * (isDust ? 120 : 230) * s.scale;
    const life = Math.sin(phase * Math.PI);
    const sc = k * life * (0.12 + 0.28 * hash(i * 9.1)) * Math.min(s.scale, 1.6);
    xf.set(sc, 0, x - (TEX / 2) * sc, y - (TEX / 2) * sc);
  });

  return (
    <Group blendMode="plus">
      <Atlas image={texture} sprites={sprites} transforms={transforms} />
    </Group>
  );
}
