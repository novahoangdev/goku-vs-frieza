import { Skia } from "react-native-skia";

// Lớp phủ trong không gian màn hình: speed lines, flash, vignette, letterbox. Vẽ bằng blend srcOver.
export const overlay = Skia.RuntimeEffect.Make(`
uniform float2 view;
uniform float2 center;     // tâm speed lines (pt)
uniform float  speed;      // 0..1
uniform float  flash;      // 0..1 (trắng)
uniform float3 tint;       // màu flash
uniform float  vignette;   // 0..1
uniform float  bars;       // letterbox 0..1
uniform float  t;

float hash(float x) { return fract(sin(x * 127.1) * 43758.5453); }

// vạch hình nêm trong ô góc u: nhọn ở r0, phình dần ra mép; fw = 1px tính theo đơn vị ô
float wedge(float u, float r, float fw, float seed) {
  float cell = floor(u);
  float h1 = hash(cell + seed);
  float h2 = hash(cell + seed + 1.7);
  float h3 = hash(cell + seed + 4.3);
  float r0 = 0.12 + 0.26 * h3;                         // điểm mũi nhọn
  float w = (0.03 + 0.2 * h2) * smoothstep(r0, r0 + 0.3, r); // độ dày thay đổi theo vạch
  float c = 0.25 + 0.5 * hash(cell + seed + 2.9);      // vị trí lệch ngẫu nhiên trong ô
  // nhân w/fw để vạch mảnh hơn 1px mờ dần thay vì lan ra (tránh moiré ở tâm)
  return step(0.5, h1) * (1.0 - smoothstep(-fw, fw, abs(fract(u) - c) - w)) * clamp(w / fw, 0.0, 1.0);
}

half4 main(float2 xy) {
  half4 o = half4(0.0);
  float2 d = xy - center;
  float ang = atan(d.y, d.x);
  float rl = length(d);
  float r = rl / length(view);
  // speed lines kiểu manga: nêm trắng dày mỏng khác nhau, viền tách màu nhẹ ở xa tâm
  if (speed > 0.01) {
    float u = ang * 38.0 + floor(t * 24.0) * 3.1;
    float fw = 38.0 / max(rl, 1.0);
    float e = 0.06 * speed * r;                         // lệch sắc: đỏ/lam trượt theo góc
    float cr = wedge(u - e, r, fw, 0.0);
    float cg = wedge(u, r, fw, 0.0);
    float cb = wedge(u + e, r, fw, 0.0);
    float a = speed * 0.85;
    o = half4(half3(cr, cg, cb) * a, max(cg, max(cr, cb)) * a);
    // chấm halftone mực ở rìa màn hình, xoay 45°
    float2 g = float2(xy.x + xy.y, xy.y - xy.x) * 0.1;
    float rad = 0.42 * smoothstep(0.32, 0.6, r) * speed;
    float dotA = (1.0 - smoothstep(rad - 0.08, rad, length(fract(g) - 0.5))) * step(0.02, rad) * 0.28;
    o = o * (1.0 - dotA) + half4(0.04, 0.02, 0.08, 1.0) * dotA;
  }
  // vignette màu phim: xanh navy sâu thay vì đen tuyền (shadow lạnh, highlight ấm kiểu color grade anime)
  float2 uv = xy / view - 0.5;
  float v = smoothstep(0.35, 0.85, length(uv * float2(1.0, 0.75))) * vignette;
  o = o * (1.0 - v) + half4(0.012, 0.03, 0.06, 1.0) * v;
  // hạt phim mịn nhấp nháy 24 fps, mạnh hơn ở vùng tối rìa màn hình
  float2 gp = mod(floor(xy * 0.5) + mod(floor(t * 24.0), 64.0) * float2(37.0, 11.0), 256.0);
  float g = fract(sin(dot(gp, float2(12.9898, 78.233))) * 43758.5453);
  float ga = (0.025 + 0.05 * v) * (0.4 + 0.6 * g);
  o = o * (1.0 - ga) + half4(half3(g), 1.0) * ga;
  // flash
  o = o * (1.0 - flash) + half4(half3(tint) * flash, flash);
  // focus burst khi flash mạnh: tia mực + vòng tròn nở ra trên nền trắng (khung impact kiểu anime)
  float k = smoothstep(0.35, 0.9, flash);
  if (k > 0.01) {
    float u = ang * 64.0;
    float cell = floor(u);
    float h = hash(cell + 9.1);
    float r0 = 0.16 + 0.3 * hash(cell + 5.3);
    float w = (0.04 + 0.16 * h) * smoothstep(r0, r0 + 0.3, r);
    float fw = 64.0 / max(rl, 1.0);
    float streak = step(0.62, h) * (1.0 - smoothstep(-fw, fw, abs(fract(u) - 0.5) - w)) * clamp(w / fw, 0.0, 1.0);
    float ph = 1.0 - flash;                              // 0 lúc đỉnh flash → vòng nở ra khi flash tắt
    float rr = 0.08 + ph * 1.2;
    float th = 0.006 * (1.0 - ph) * (0.6 + 0.4 * sin(ang * 3.0 + 1.3) * sin(ang * 7.0)); // dày mỏng không đều như nét cọ
    float ring = (1.0 - smoothstep(th, th + 0.002, abs(r - rr))) * 0.45;
    float a = max(streak, ring) * k * 0.85;
    o = o * (1.0 - a) + half4(0.07, 0.04, 0.12, 1.0) * a;
  }
  // letterbox
  float bh = bars * view.y * 0.11;
  if (xy.y < bh || xy.y > view.y - bh) { o = half4(0.0, 0.0, 0.0, 1.0); }
  return o;
}`)!;
