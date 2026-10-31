import { useDerivedValue, type SharedValue } from "react-native-reanimated";
import type { SkSize } from "react-native-skia";
import { EXPLOSIONS, FPS, HAPTICS, KAME, anchor, hash, lastCut, n1, rts, track } from "./timeline";
import { coverScale, plateToScreen, type Cam } from "./camera";

/**
 * Frame các cú đấm trúng (hit spark): haptic rigid ở đoạn né/đỡ đòn (> 11s) và heavy ở cú phản đòn (> 16s);
 * các haptic dồn dập cách nhau < 0.2s gộp làm một để spark không bị reset liên tục.
 */
// các mốc (giây) theo phim 20 s gốc, quy đổi sang phim đã giãn nhịp
const T11 = rts(11), T13 = rts(13), T16 = rts(16), T165 = rts(16.5), T18 = rts(18);
const HITS: number[] = [];
const inKame = (f: number) => {
  "worklet";
  return KAME !== null && f >= KAME.f0 && f < KAME.f1;
};
for (const h of HAPTICS) {
  if (inKame(h.t * FPS)) continue; // haptic của Kamehameha là lúc bắn / nổ, không phải cú đấm
  if ((h.style === "rigid" && h.t > T11) || (h.style === "heavy" && h.t > T16)) {
    const f = Math.round(h.t * FPS);
    if (!HITS.length || f - HITS[HITS.length - 1] > 0.2 * FPS) HITS.push(f);
  }
}
const HIT_LIFE = 0.4; // giây
const BOLT_EVERY = 0.32; // giây: mỗi ~0.3 s có thể loé một tia sét mới (xác suất theo track lightning)
const BOLT_LIFE = 0.13;

/** Tính mọi uniform cho lớp composite + overlay từ đồng hồ `t` và frame video đang hiển thị. */
export function useFxUniforms(t: SharedValue<number>, videoTime: SharedValue<number>, size: SkSize) {
  const cam = useDerivedValue<Cam>(() => {
    const ft = track("fxclock", t.value);
    const trauma = track("shake", t.value) ** 2; // rung theo trauma²
    return [
      trauma * 26 * n1(ft * 23),
      trauma * 40 * n1(ft * 23 + 7.3),
      1 + track("punch", t.value),
      trauma * 0.008 * n1(ft * 17 + 3.1),
    ];
  });

  const composite = useDerivedValue(() => {
    const tt = t.value;
    const vf = videoTime.value * FPS; // anchor bám frame video đang hiển thị
    const ft = track("fxclock", tt);
    const chest = anchor("goku_chest", vf);
    const head = anchor("goku_head", vf);
    // độ lớn của Goku trên plate: khoảng cách đầu–ngực, 130px ≈ cảnh trung
    const fist = anchor("goku_fist_r", vf);
    const finger = anchor("frieza_finger", vf);
    const target = anchor("beam_target", vf);
    const bpoint = anchor("blast_point", vf);
    const aura = track("aura", tt);
    const impactAt = tt > T16 ? fist : chest;
    let life = -1;
    for (let i = 0; i < EXPLOSIONS.length; i++) {
      const age = (vf - EXPLOSIONS[i]) / (0.9 * FPS);
      if (age >= 0 && age < 1) life = age;
    }
    let hit = [0, 0, -1, 0];
    for (let i = 0; i < HITS.length; i++) {
      const age = (vf - HITS[i]) / (HIT_LIFE * FPS);
      if (age >= 0 && age < 1) {
        // giữ nguyên điểm trúng ở frame chạm (nắm đấm rút về thì spark vẫn ở chỗ cũ); cỡ theo Goku lúc đó
        const hf = anchor("goku_fist_r", HITS[i]);
        const hc = anchor("goku_chest", HITS[i]);
        const hh = anchor("goku_head", HITS[i]);
        const hs = Math.min(3, Math.max(0.12, Math.hypot(hh[0] - hc[0], hh[1] - hc[1]) / 130));
        hit = hf[2] > 0 ? [hf[0], hf[1], age, 100 * hs] : hit;
      }
    }
    const beamOk = finger[2] > 0 && target[2] > 0;
    // lửa aura toé ngược hướng bay khi Goku lướt nhanh trên màn hình (goku_trail: chỗ Goku ở 0.25 s trước)
    const trail = anchor("goku_trail", vf);
    let ax = 0;
    let ay = -1;
    if (chest[2] > 0 && trail[2] > 0) {
      const dx = trail[0] - chest[0];
      const dy = trail[1] - chest[1];
      const len = Math.hypot(dx, dy);
      const k = Math.min(1, Math.max(0, (len - 40) / 120)) * 0.9;
      if (len > 1) {
        ax = (k * dx) / len;
        ay = -(1 - k) + (k * dy) / len;
        const n = Math.hypot(ax, ay) || 1;
        ax /= n;
        ay /= n;
      }
    }
    const ascale = Math.min(3, Math.max(0.12, Math.hypot(head[0] - chest[0], head[1] - chest[1]) / 130));
    // sét trời: nhấp nháy 2 nhịp trong 0.13 s, seed đổi theo tia + theo cut
    const boltAge = (tt % BOLT_EVERY) / BOLT_LIFE;
    const boltSeed = Math.floor(tt / BOLT_EVERY) + lastCut(tt * FPS) * 0.37;
    const boltOn = boltAge > 1 || hash(boltSeed * 3.1) > track("lightning", tt)
      ? 0 : boltAge < 0.35 || (boltAge > 0.55 && boltAge < 0.8) ? 1 : 0.25;
    return {
      view: [size.width, size.height],
      pxScale: coverScale(size.width, size.height),
      cam: cam.value,
      t: ft,
      chest: [chest[0], chest[1]],
      ascale,
      aura: chest[2] > 0 ? aura : 0,
      grade: track("grade", tt),
      impact: track("impact", tt),
      shock: [impactAt[0], impactAt[1], track("shock_r", tt), track("shock_k", tt)],
      chroma: track("punch", tt) * 1.5 + track("flash", tt) * 0.4,
      rays: Math.max(0, aura - 1) * 2.5 + track("flash", tt) * 0.4,
      beam: [finger[0], finger[1], target[0], target[1]],
      beamOn: beamOk ? track("beam", tt) : 0,
      blast: [finger[0], finger[1], bpoint[0], bpoint[1]],
      blastP: finger[2] > 0 ? track("blast", tt) : 0,
      explo: [bpoint[0], bpoint[1], bpoint[2] > 0 ? life : -1],
      hit,
      depthZ: [chest[2], finger[2], target[2], bpoint[2]],
      adir: [ax, ay],
      bolt: [boltOn, boltSeed % 1000],
    };
  });

  const overlay = useDerivedValue(() => {
    const tt = t.value;
    const vf = videoTime.value * FPS;
    const pxScale = coverScale(size.width, size.height);
    const center =
      tt > T165 && tt < T18
        ? anchor("goku_fist_r", vf)
        : tt > T13 && tt < T165
          ? [576, 1248, 1]
          : anchor("goku_chest", vf);
    const [sx, sy] = plateToScreen(center[0], center[1], cam.value, size.width, size.height, pxScale);
    const flash = track("flash", tt);
    const lightning = track("lightning", tt);
    return {
      view: [size.width, size.height],
      center: [sx, sy],
      speed: track("speedlines", tt),
      flash: Math.min(flash, 0.95),
      tint: inKame(vf) ? [0.84, 0.95, 1] : tt > T13 && tt < T165 ? [1, 0.72, 0.95] : [1, 0.98, 0.9],
      vignette: 0.35 + lightning * 0.25,
      bars: track("title", tt),
      t: tt,
    };
  });

  return { cam, composite, overlay };
}
