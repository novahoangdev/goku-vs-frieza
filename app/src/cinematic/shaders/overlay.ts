import { Skia } from "react-native-skia";

// Screen-space overlay: speed lines, flash, vignette, letterbox. Drawn with srcOver blending.
export const overlay = Skia.RuntimeEffect.Make(`
uniform float2 view;
uniform float2 center;     // speed lines center (pt)
uniform float  speed;      // 0..1
uniform float  flash;      // 0..1 (white)
uniform float3 tint;       // flash color
uniform float  vignette;   // 0..1
uniform float  bars;       // letterbox 0..1
uniform float  t;

float hash(float x) { return fract(sin(x * 127.1) * 43758.5453); }

// wedge-shaped line in angular cell u: sharp at r0, widening toward the edge; fw = 1px in cell units
float wedge(float u, float r, float fw, float seed) {
  float cell = floor(u);
  float h1 = hash(cell + seed);
  float h2 = hash(cell + seed + 1.7);
  float h3 = hash(cell + seed + 4.3);
  float r0 = 0.12 + 0.26 * h3;                         // tip position
  float w = (0.03 + 0.2 * h2) * smoothstep(r0, r0 + 0.3, r); // thickness varies per line
  float c = 0.25 + 0.5 * hash(cell + seed + 2.9);      // random offset within the cell
  // multiply by w/fw so lines thinner than 1px fade out instead of spreading (avoids moire at the center)
  return step(0.5, h1) * (1.0 - smoothstep(-fw, fw, abs(fract(u) - c) - w)) * clamp(w / fw, 0.0, 1.0);
}

half4 main(float2 xy) {
  half4 o = half4(0.0);
  float2 d = xy - center;
  float ang = atan(d.y, d.x);
  float rl = length(d);
  float r = rl / length(view);
  // manga-style speed lines: white wedges of varying thickness, slight color fringing far from the center
  if (speed > 0.01) {
    float u = ang * 38.0 + floor(t * 24.0) * 3.1;
    float fw = 38.0 / max(rl, 1.0);
    float e = 0.06 * speed * r;                         // chromatic offset: red/blue shifted along the angle
    float cr = wedge(u - e, r, fw, 0.0);
    float cg = wedge(u, r, fw, 0.0);
    float cb = wedge(u + e, r, fw, 0.0);
    float a = speed * 0.85;
    o = half4(half3(cr, cg, cb) * a, max(cg, max(cr, cb)) * a);
    // ink halftone dots at the screen edges, rotated 45°
    float2 g = float2(xy.x + xy.y, xy.y - xy.x) * 0.1;
    float rad = 0.42 * smoothstep(0.32, 0.6, r) * speed;
    float dotA = (1.0 - smoothstep(rad - 0.08, rad, length(fract(g) - 0.5))) * step(0.02, rad) * 0.28;
    o = o * (1.0 - dotA) + half4(0.04, 0.02, 0.08, 1.0) * dotA;
  }
  // film-tinted vignette: deep navy instead of pure black (cool shadows, warm highlights like an anime color grade)
  float2 uv = xy / view - 0.5;
  float v = smoothstep(0.35, 0.85, length(uv * float2(1.0, 0.75))) * vignette;
  o = o * (1.0 - v) + half4(0.012, 0.03, 0.06, 1.0) * v;
  // fine film grain flickering at 24 fps, stronger in the dark screen edges
  float2 gp = mod(floor(xy * 0.5) + mod(floor(t * 24.0), 64.0) * float2(37.0, 11.0), 256.0);
  float g = fract(sin(dot(gp, float2(12.9898, 78.233))) * 43758.5453);
  float ga = (0.025 + 0.05 * v) * (0.4 + 0.6 * g);
  o = o * (1.0 - ga) + half4(half3(g), 1.0) * ga;
  // flash
  o = o * (1.0 - flash) + half4(half3(tint) * flash, flash);
  // focus burst on a strong flash: ink rays + an expanding ring on white (anime-style impact frame)
  float k = smoothstep(0.35, 0.9, flash);
  if (k > 0.01) {
    float u = ang * 64.0;
    float cell = floor(u);
    float h = hash(cell + 9.1);
    float r0 = 0.16 + 0.3 * hash(cell + 5.3);
    float w = (0.04 + 0.16 * h) * smoothstep(r0, r0 + 0.3, r);
    float fw = 64.0 / max(rl, 1.0);
    float streak = step(0.62, h) * (1.0 - smoothstep(-fw, fw, abs(fract(u) - 0.5) - w)) * clamp(w / fw, 0.0, 1.0);
    float ph = 1.0 - flash;                              // 0 at the flash peak → the ring expands as the flash fades
    float rr = 0.08 + ph * 1.2;
    float th = 0.006 * (1.0 - ph) * (0.6 + 0.4 * sin(ang * 3.0 + 1.3) * sin(ang * 7.0)); // uneven thickness like a brush stroke
    float ring = (1.0 - smoothstep(th, th + 0.002, abs(r - rr))) * 0.45;
    float a = max(streak, ring) * k * 0.85;
    o = o * (1.0 - a) + half4(0.07, 0.04, 0.12, 1.0) * a;
  }
  // letterbox
  float bh = bars * view.y * 0.11;
  if (xy.y < bh || xy.y > view.y - bh) { o = half4(0.0, 0.0, 0.0, 1.0); }
  return o;
}`)!;
