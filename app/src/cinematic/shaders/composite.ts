import { Skia } from "react-native-skia";

// Một pass duy nhất trên frame video pack (2304×2496):
// camera ảo → shockwave → chromatic → beauty → aura sau lưng Goku (matte) → rim → god rays
// → Death Beam / ki blast / vụ nổ → glow energy → chỉnh màu → impact frame → grain.
// Lớp depth (độ sâu từng điểm ảnh) cho hiệu ứng 2D nằm đúng lớp: vật nào gần camera hơn hiệu ứng thì che nó.
export const composite = Skia.RuntimeEffect.Make(`
uniform shader video;    // frame pack: beauty | matte + energy | depth
uniform float2 view;     // kích thước canvas (pt)
uniform float  pxScale;  // px plate trên mỗi pt màn hình (cover)
uniform float4 cam;      // xy: pan (px plate), z: zoom, w: xoay (rad)
uniform float  t;        // fxclock (giây)
uniform float2 chest;    // anchor ngực Goku (px plate)
uniform float  ascale;   // độ lớn của Goku trên plate (1 ≈ cảnh trung)
uniform float  aura;     // 0..1.4
uniform float  grade;    // 0: Namek lạnh → 1: vàng SSJ
uniform float  impact;   // 1: impact frame đen trắng
uniform float4 shock;    // xy: tâm, z: bán kính, w: cường độ
uniform float  chroma;   // độ lệch màu
uniform float  rays;     // god rays từ ngực Goku
uniform float4 beam;     // xy: ngón tay Frieza, zw: điểm tia đi qua
uniform float  beamOn;
uniform float4 blast;    // xy: điểm bắn, zw: điểm trúng
uniform float  blastP;   // tiến độ ki blast 0..1 (0: tắt)
uniform float3 explo;    // xy: tâm vụ nổ, z: tuổi 0..1 (âm: tắt)
uniform float4 hit;      // hit spark lúc đấm trúng: xy: điểm trúng, z: tuổi 0..1 (âm: tắt), w: bán kính (px plate)
uniform float4 depthZ;   // độ sâu (m) của: x ngực Goku, y ngón tay Frieza, z đích Death Beam, w điểm nổ ki blast
uniform float2 adir;     // hướng lửa aura bốc (px plate, đơn vị): (0,-1) = lên; bay nhanh thì toé ngược hướng bay
uniform float2 bolt;     // sét trời: x độ sáng 0..1, y seed (đổi mỗi tia)

const float2 PLATE  = float2(1152.0, 2496.0);
const float2 MATTE  = float2(1152.0, 0.0);
const float2 ENERGY = float2(1152.0, 1248.0);
const float2 DEPTH  = float2(1728.0, 0.0);

float hash(float2 p) { return fract(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
float noise(float2 p) {
  float2 i = floor(p); float2 f = fract(p); float2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + float2(1, 0)), u.x),
             mix(hash(i + float2(0, 1)), hash(i + float2(1, 1)), u.x), u.y);
}
float fbm(float2 p) {
  float v = 0.0; float a = 0.5;
  for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
  return v;
}
half3 beauty(float2 p) { return video.eval(clamp(p, float2(0.5), PLATE - 0.5)).rgb; }
// Tile ½ độ phân giải; kẹp toạ độ để không lấy lấn sang tile bên cạnh
float tile(float2 origin, float2 p) {
  return video.eval(origin + clamp(p * 0.5, float2(0.5), PLATE * 0.5 - 0.5)).r;
}
// độ sâu (m) theo trục nhìn: tile depth lưu log chuẩn hoá 0.05 m … 400 m (render_passes.py)
float zAt(float2 p) { return 0.05 * exp(tile(DEPTH, p) * 8.987); }
// 1 khi điểm ảnh có vật gần camera hơn hiệu ứng ở độ sâu z; k: khoảng chừa (tỉ lệ) để không tự che
// (depth 8 bit sau giải mã ≈ 3.6 % mỗi bậc → k không nhỏ hơn ~0.03)
float occluded(float zs, float z, float k) { return smoothstep(z * (1.0 - k) - 0.03, z * (1.0 - 2.0 * k) - 0.07, zs); }
// 3 dải màu cứng kiểu anime: viền → giữa → lõi
half3 cel(float a, half3 rim, half3 mid, half3 core) {
  return a > 0.72 ? core : (a > 0.42 ? mid : rim);
}

half4 main(float2 xy) {
  // 1. Màn hình → plate qua camera ảo
  float2 c = xy - 0.5 * view;
  float s = sin(cam.w); float k = cos(cam.w);
  c = float2(c.x * k - c.y * s, c.x * s + c.y * k) / cam.z;
  float2 p = 0.5 * PLATE + c * pxScale + cam.xy;

  // 2. Shockwave: đẩy điểm lấy mẫu quanh vòng sóng
  float2 d = p - shock.xy;
  float r = length(d);
  float x = (r - shock.z) / 45.0;
  float ring = exp(-x * x) * shock.w;
  p -= d / max(r, 1.0) * ring * 34.0;

  // 2b. Không khí rung (heat haze) quanh Goku khi aura cháy: lắc điểm lấy mẫu bằng noise trôi lên trên,
  //     mạnh ở sát người, tắt dần ra ngoài; không lắc chính Goku (matte) để nét mặt không méo
  // hệ trục lửa aura: ey hướng "xuống" (ngược adir), ex vuông góc; mặc định ex = (1,0), ey = (0,1)
  float2 ey = -adir;
  float2 ex = float2(ey.y, -ey.x);
  float zs0 = zAt(p);
  float auraFront = 1.0 - occluded(zs0, depthZ.x, 0.08);
  if (aura > 0.02) {
    float2 hd = (p - chest) / (430.0 * ascale);
    float hm = aura * (1.0 - smoothstep(0.45, 1.5, length(hd * float2(1.0, 0.7))));
    hm *= (1.0 - tile(MATTE, p)) * auraFront;
    float2 hn = float2(noise(p * 0.014 + float2(0.0, -t * 3.1)), noise(p * 0.014 + float2(5.7, -t * 2.4))) - 0.5;
    p += hn * hm * 16.0 * ascale;
  }

  // 2c. Không khí nóng quanh vật phát sáng dựng trong Blender (tia Kamehameha, cầu khí, vụ nổ): 4 mẫu energy lệch
  //     quanh điểm → càng sát nguồn sáng không khí càng rung, vân rung trôi lên như khí nóng bốc; không lắc Goku
  {
    float e4 = max(max(tile(ENERGY, p + float2(34.0, 0.0)), tile(ENERGY, p - float2(34.0, 0.0))),
                   max(tile(ENERGY, p + float2(0.0, 34.0)), tile(ENERGY, p - float2(0.0, 34.0))));
    float hm2 = smoothstep(0.2, 0.7, e4) * (1.0 - tile(MATTE, p));
    if (hm2 > 0.001) {
      float2 hn2 = float2(noise(p * 0.035 + float2(0.0, t * 5.0)), noise(p * 0.035 + float2(3.3, t * 4.1))) - 0.5;
      p += hn2 * hm2 * 10.0;
    }
  }

  // 3. Beauty, lệch màu theo hướng ra ngoài tâm (mạnh hơn ở vòng sóng)
  float2 off = (p - 0.5 * PLATE) * (chroma + ring * 0.5) * 0.006;
  half3 col = half3(beauty(p + off).r, beauty(p).g, beauty(p - off).b);
  float m = tile(MATTE, p);
  float zs = zAt(p);
  // Goku bị nhoè (motion blur) thì matte chỉ còn một phần: coi như vẫn là Goku để aura không phủ lên người
  float mk = smoothstep(0.03, 0.3, m);

  // 4. Aura sau lưng Goku: halo từ matte bị noise kéo lên trên + "quả trứng" quanh ngực
  if (aura > 0.001) {
    float2 flow = float2(0.0, t * 1.7);
    float2 pw = (p - chest) / ascale;             // toạ độ đã chuẩn hoá theo kích thước nhân vật
    float2 ps = float2(dot(pw, ex), dot(pw, ey)); // … xoay theo hướng lửa bốc
    float n = fbm(ps / 90.0 + flow);
    float2 q = p + (ex * (fbm(ps / 60.0 + flow + 7.0) - 0.5) * 80.0 + ey * (n - 0.5) * 170.0) * ascale;
    // lưỡi lửa liếm lên: noise dạng gờ (ridged) theo cột → đỉnh nhọn, đẩy điểm lấy mẫu matte xuống dưới
    // để viền aura vươn lên thành từng ngọn; cột trôi ngang + đập nhanh nên lửa "liếm" chứ không đứng yên
    float tg = noise(float2(ps.x / 24.0 + sin(t * 1.3) * 0.6, t * 3.4));
    float rid = 1.0 - abs(tg * 2.0 - 1.0);
    rid *= rid; rid *= rid;                         // ^4: ngọn hẹp, mũi nhọn
    q += ey * rid * 95.0 * ascale * smoothstep(80.0, -140.0, ps.y);
    float halo = 0.0;
    for (int i = 0; i < 8; i++) {
      float ang = float(i) * 0.785398;
      halo += tile(MATTE, q + (ex * cos(ang) + ey * (sin(ang) * 1.4 + 0.7)) * 34.0 * ascale);
    }
    float2 e = ps / float2(175.0, 300.0);
    // lưỡi lửa: noise kéo dài theo chiều dọc, cuộn lên nhanh, chỉ ở nửa trên của "quả trứng"
    float flame = fbm(float2(ps.x / 26.0, ps.y / 115.0 + t * 2.8));
    float upper = smoothstep(0.35, -0.9, e.y);
    float egg = smoothstep(1.0, 0.55, length(e + float2(0.0, 0.1)) + (n - 0.5) * 0.7 - flame * flame * 0.95 * upper);
    // halo (bám dáng người) cho lõi sáng; "quả trứng" chỉ tạo lớp lửa ngoài mờ hơn
    // Goku bị che (sau cột đá) hoặc ra ngoài khung thì tắt "quả trứng", tránh đốm lửa lơ lửng
    float vis = 0.0;
    for (int i = 0; i < 5; i++) {
      vis = max(vis, tile(MATTE, chest + float2(float(i - 2) * 18.0, float(i - (i / 2) * 2) * 24.0 - 12.0) * ascale));
    }
    // cận cảnh (nhân vật to) thì "quả trứng" mỏng đi, khỏi trùm cả khung hình
    float close = clamp((ascale - 1.6) / 1.4, 0.0, 1.0);
    float a = max(halo / 8.0 * 1.1, egg * 0.55 * vis * (1.0 - close * 0.6)) * aura * (1.0 - mk) * auraFront;
    if (a > 0.2) {
      half3 ac = cel(a, half3(1.0, 0.52, 0.04), half3(1.0, 0.76, 0.1), half3(1.0, 0.97, 0.72));
      // viền mực cam đỏ mảnh ở mép ngoài: ngọn lửa có nét như key-frame anime
      if (a < 0.26) ac = half3(0.86, 0.24, 0.02);
      // trộn màu vàng bão hoà + cộng một lớp sáng: rực mà không đục màu nền
      float op = min(0.9, a * 1.2 + 0.2);
      col = mix(col, ac, op * 0.74) + ac * op * 0.26;
    }
    // hạt khí vàng bay lên quanh người (2 lớp lưới, mỗi ô một hạt vệt dọc, ra khỏi "quả trứng" thì tắt)
    float sparks = 0.0; float sglow = 0.0;
    for (int j = 0; j < 2; j++) {
      float cs = 46.0 + float(j) * 30.0;
      float2 g = ps / cs + float2(float(j) * 0.37, t * (2.2 - float(j) * 0.7));
      float2 id = floor(g); float2 f = fract(g) - 0.5;
      float rnd = hash(id + float(j) * 13.0);
      float2 dp = f - float2(rnd - 0.5, fract(rnd * 7.13) - 0.5) * 0.6;
      float on = step(0.45, fract(rnd * 31.7));
      float dl = length(dp * float2(1.0, 0.32));
      sparks += on * smoothstep(0.075, 0.03, dl);
      sglow += on * exp(-dl * 22.0);
    }
    float zone = smoothstep(1.25, 0.7, length(e + float2(0.0, 0.15))) * vis * (1.0 - close * 0.5) * min(aura, 1.0)
               * (1.0 - mk * 0.88) * auraFront;   // hạt khí toả quanh người, không lấm tấm trên mặt/thân
    col += half3(1.0, 0.72, 0.15) * sglow * zone * 0.8;
    col = mix(col, half3(1.0, 0.98, 0.8), min(sparks * zone, 1.0));
    // rim vàng ở mép trên người Goku
    col += half3(1.0, 0.82, 0.3) * m * (1.0 - tile(MATTE, p + adir * 9.0 * ascale)) * min(aura, 1.0);
  }

  // 5. God rays: kéo vệt sáng từ energy + aura về phía ngực
  if (rays > 0.01) {
    float acc = 0.0;
    float2 dir = (chest - p) / 16.0;
    float jit = hash(xy) * 0.9;                    // lệch mẫu ngẫu nhiên để không thành bóng ma
    for (int i = 0; i < 16; i++) { float k2 = float(i) + jit; acc += tile(ENERGY, p + dir * k2) + tile(MATTE, p + dir * k2) * 0.12; }
    col += half3(1.0, 0.85, 0.4) * acc / 16.0 * rays * 1.1;
  }

  // 6. Death Beam kiểu anime: viền tím → hồng → lõi trắng, đầu tia nhọn thon ra từ ngón tay, gợn rung dọc tia,
  //    loé hình sao (chữ thập + gai ngắn) ở đầu ngón, vệt tốc độ trượt dọc tia, tia điện zigzag lách tách hai bên
  if (beamOn > 0.01) {
    float2 bd = normalize(beam.zw - beam.xy);
    float2 rel = p - beam.xy;
    float along = dot(rel, bd);
    // độ sâu của tia tại điểm này: nội suy 1/z giữa ngón tay và đích (đúng phối cảnh), vật gần hơn thì che tia
    float bu = along / max(length(beam.zw - beam.xy), 1.0);
    float zb = 1.0 / max(mix(1.0 / max(depthZ.y, 0.05), 1.0 / max(depthZ.z, 0.05), bu), 0.002);
    float bOn = beamOn * (1.0 - occluded(zs, zb, 0.035));
    float ay = dot(rel, float2(-bd.y, bd.x));       // lệch ngang có dấu
    float dist = length(rel - bd * max(along, 0.0));
    float fwd = step(0.0, along);
    float tp = mix(0.2, 1.0, smoothstep(0.0, 170.0, along));   // thon nhọn ~170px đầu
    float d2 = dist / tp + sin(along * 0.035 - t * 40.0) * 2.0;
    float soft = exp(-d2 / 45.0) * step(-6.0, along);
    col = mix(col, half3(0.85, 0.2, 0.75), min(soft * 1.2, 0.85) * bOn);
    col = mix(col, half3(1.0, 0.42, 0.88), smoothstep(26.0, 22.0, d2) * fwd * bOn);
    col = mix(col, half3(1.0, 0.92, 0.99), smoothstep(12.0, 9.0, d2) * fwd * bOn);
    // vệt tốc độ: làn mảnh song song tia, mỗi làn một đoạn sáng trượt nhanh ra xa ngón tay
    float lh = hash(float2(floor(ay / 7.0), 3.7));
    float lp = fract((along - t * (1100.0 + lh * 900.0)) / (180.0 + lh * 140.0) + lh);
    float lw = abs(fract(ay / 7.0) - 0.5) * 7.0;     // khoảng cách tới giữa làn (px)
    float sk = step(0.35, lh) * smoothstep(0.0, 0.06, lp) * smoothstep(0.42, 0.3, lp)
             * smoothstep(1.3, 0.5, lw) * step(6.0, abs(ay)) * step(abs(ay), 40.0) * smoothstep(40.0, 120.0, along);
    col = mix(col, half3(1.0, 0.97, 1.0), sk * 0.9 * bOn);
    // tia điện: mỗi đoạn 170px có thể bật một tia zigzag vồng ra một bên rồi về lại tia, đổi hình ~20 lần/giây
    float cu = along / 170.0;
    float fr = floor(t * 20.0);
    float sh = hash(float2(floor(cu), fr));
    float u = fract(cu);
    float zi = u * 3.5 + sh * 3.0;
    float zz = (abs(fract(zi) * 2.0 - 1.0) - 0.5) * (0.5 + hash(float2(floor(zi), sh)));  // mỗi khúc gãy một độ cao
    float sy = (sh > 0.5 ? 1.0 : -1.0) * (14.0 + sin(u * 3.1416) * (24.0 + sh * 30.0) + zz * 20.0 * sin(u * 3.1416));
    float sd = abs(ay - sy);
    float zone = step(0.08, u) * step(u, 0.92) * step(0.55, hash(float2(floor(cu), fr + 0.5))) * step(60.0, along) * bOn;
    col = mix(col, half3(1.0, 0.4, 0.9), smoothstep(6.0, 3.5, sd) * zone);
    col = mix(col, half3(1.0, 0.95, 1.0), smoothstep(2.6, 1.4, sd) * zone);
    // loé ở đầu ngón tay: chữ thập 4 cánh theo hướng tia + gai ngắn ngẫu nhiên, 3 dải cứng
    float rr = length(rel);
    if (rr < 190.0) {
      float ma = atan(rel.y, rel.x);
      float ang = ma - atan(bd.y, bd.x);
      float fl = (0.85 + 0.15 * sin(t * 90.0)) * bOn;
      float sa = ma * 2.2;                            // ~14 góc, mỗi góc có thể có 1 gai
      float gh = hash(float2(floor(sa), floor(t * 24.0)));
      float spike = (1.0 - abs(fract(sa) - 0.5) * 2.0) * step(0.45, gh) * (25.0 + gh * 45.0);
      float rad = 30.0 + pow(abs(cos(ang * 2.0)), 30.0) * 150.0 + pow(abs(sin(ang * 2.0)), 40.0) * 50.0;
      float a = 1.0 - rr / max((rad + spike * spike / 70.0) * fl, 1.0);
      if (a > 0.0) {
        half3 mc = cel(a + 0.2, half3(0.82, 0.2, 0.75), half3(1.0, 0.45, 0.9), half3(1.0, 0.97, 1.0));
        col = mix(col, mc, smoothstep(0.0, 0.06, a));
      }
    }
    col += half3(1.0, 0.55, 0.9) * exp(-rr / 30.0) * 1.2 * bOn;
    // tia sượt qua người rọi ánh hồng lên Goku (má, tóc sát tia) — mạnh ở sát tia, tắt dần ra ~120px
    col += half3(0.55, 0.12, 0.42) * mk * exp(-dist / 55.0) * fwd * beamOn;
  }

  // 7. Ki blast kiểu anime: lõi trắng + quầng hồng/tím 3 dải cứng, đuôi sao chổi thon dần về phía điểm bắn,
  //    tia điện lách tách quanh đầu đạn (nhấp nháy theo t)
  if (blastP > 0.001) {
    float2 bv = blast.zw - blast.xy;
    float bl = max(length(bv), 1.0);
    float2 bd = bv / bl;
    float2 rel = p - mix(blast.xy, blast.zw, blastP);
    float ax = dot(rel, bd);                       // >0: trước đầu đạn, <0: phía đuôi
    float zk = 1.0 / max(mix(1.0 / max(depthZ.y, 0.05), 1.0 / max(depthZ.w, 0.05), blastP), 0.002);
    float kv = 1.0 - occluded(zs, zk, 0.05);             // đạn bay sau lưng Goku / sau cột đá thì bị che
    float ay = dot(rel, float2(-bd.y, bd.x));
    float fl = 0.9 + 0.1 * sin(t * 95.0);          // đầu đạn phập phồng
    float R = 36.0 * fl;
    float tl = min(bl * blastP + 40.0, 300.0);     // đuôi dài theo quãng đã bay
    float back = clamp(-ax / tl, 0.0, 1.0);        // 0: đầu → 1: cuối đuôi
    float bn = noise(float2(ax / 18.0 + t * 40.0, ay / 9.0));
    // trường "độ sáng": đầu tròn hợp với đuôi thon (mép đuôi rung theo noise)
    float head = 1.0 - length(rel) / R;
    float tw = R * pow(1.0 - back, 1.4) * (0.8 + bn * 0.5);
    float tail = (1.0 - abs(ay) / max(tw, 0.5)) * step(ax, 0.0) * step(back, 0.999) * (1.0 - back * 0.35);
    float a = max(head, tail);
    // quầng mềm bên ngoài + vệt sáng mờ dọc đuôi
    float glow = exp(-length(rel) / 46.0) + exp(-abs(ay) / 22.0) * (1.0 - back) * step(ax, 0.0) * 0.5;
    col += half3(1.0, 0.35, 0.8) * min(glow, 1.2) * 0.55 * kv;
    if (a > 0.0) {
      half3 kc = cel(a + 0.12, half3(0.78, 0.16, 0.72), half3(1.0, 0.45, 0.88), half3(1.0, 0.96, 1.0));
      col = mix(col, kc, smoothstep(0.0, 0.08, a) * kv);
    }
    // tia điện: vài tia zigzag toả ra từ đầu đạn, đổi hình ~24 lần/giây
    float rr = length(rel);
    if (rr < R * 2.6) {
      float sa = atan(rel.y, rel.x) * 1.1;
      float fr = floor(t * 24.0);
      float2 sid = float2(floor(sa), fr);
      float sh = hash(sid);
      float sc = 0.5 + (noise(float2(rr / 12.0, sid.x * 7.0 + fr * 5.0)) - 0.5) * 0.9;
      float sd = abs(fract(sa) - sc) * rr / 1.1;      // khoảng cách tới tia (px)
      float zone = step(R * 0.9, rr) * step(rr, R * (1.5 + sh)) * step(0.5, sh) * kv;
      col = mix(col, half3(1.0, 0.4, 0.9), smoothstep(6.0, 4.0, sd) * zone);
      col = mix(col, half3(1.0, 0.95, 1.0), smoothstep(2.6, 1.4, sd) * zone);
    }
  }

  // 8. Vụ nổ cel-shaded kiểu anime: loé trắng → quả cầu lửa 3 tông viền gai → lửa co vào trong, khói tím xám
  //    chiếm dần phần ngoài; vòng sóng xung kích; nằm sau Goku (che bằng matte)
  if (explo.z >= 0.0) {
    float life = explo.z;
    float R = 50.0 + 330.0 * sqrt(life);
    // khí nóng nổi lên: cả quả cầu lửa → khói trôi dần lên trên khi nguội (y plate hướng xuống)
    float2 ep = p - explo.xy + float2(0.0, 110.0 * life * life);
    float r = length(ep);
    float en = fbm(ep / 50.0 + float2(0.0, t * 2.0));
    float spikes = pow(abs(sin(atan(ep.y, ep.x) * 5.0 + en * 3.0)), 6.0);
    float shape = 1.0 - r / R + (en - 0.5) * 0.5 + spikes * 0.18 * (1.0 - life);
    float ev = (1.0 - m) * (1.0 - occluded(zs, depthZ.w, 0.1));
    float vis = ev * (1.0 - smoothstep(0.8, 1.0, life));
    if (shape > 0.0) {
      float burn = shape - life * 0.75;
      half3 ec;
      if (burn > 0.0) {
        ec = cel(burn * 1.6 + 0.1, half3(0.9, 0.18, 0.1), half3(1.0, 0.62, 0.12), half3(1.0, 0.98, 0.88));
        if (shape < 0.06) ec = half3(0.55, 0.08, 0.06);
      } else {
        // khói cel: cụm bông (noise) tô 3 tông theo hướng sáng trên-trái, viền mực ở mép ngoài,
        // vệt than đỏ sẫm ngay sát lửa; nửa sau đời vụ nổ khói bị noise ăn thủng rồi tan
        float pf = noise(ep / 58.0 - float2(0.0, t * 0.8));   // cụm bông to, mềm
        shape -= smoothstep(0.45, 1.0, life) * (1.1 - pf) * 0.5;
        float lit = dot(ep / R, float2(-0.55, -0.83)) * 1.1 + (pf - 0.5) * 0.9 + burn * 1.0;
        ec = lit > 0.3 ? half3(0.62, 0.55, 0.6) : (lit > -0.15 ? half3(0.4, 0.34, 0.42) : half3(0.22, 0.17, 0.25));
        if (burn > -0.035) ec = half3(0.5, 0.1, 0.07);
        if (shape < 0.035) ec = half3(0.11, 0.07, 0.13);
      }
      col = mix(col, ec, smoothstep(0.0, 0.02, shape) * vis);
    }
    // mảnh đá văng: 16 hướng, mỗi hướng một mảnh hình thoi xoay tròn bay ra rồi chúc xuống, tắt cuối đời
    float dsec = atan(ep.y, ep.x) * 2.5465 + 0.5;    // 16 ô góc
    float dc = floor(dsec);
    float dh = hash(float2(dc, 5.3));
    float dang = (dc + (dh - 0.5) * 0.5) / 2.5465;
    float2 cpos = float2(cos(dang), sin(dang)) * R * (0.35 + 1.25 * life) * (0.65 + 0.7 * dh) + float2(0.0, 60.0 * life * life);
    float2 cr = ep - cpos;
    float rot = t * (6.0 + dh * 8.0) + dh * 6.28;
    cr = float2(cr.x * cos(rot) - cr.y * sin(rot), cr.x * sin(rot) + cr.y * cos(rot));
    float csz = (7.0 + 9.0 * fract(dh * 11.3)) * (1.0 - life * 0.5);
    float chip = abs(cr.x) + abs(cr.y) * 1.7;
    float con = step(0.3, dh) * step(0.06, life) * step(life, 0.85) * ev * step(shape, life * 0.75);
    col = mix(col, half3(0.13, 0.08, 0.1), smoothstep(csz, csz - 1.5, chip) * con);
    col = mix(col, half3(0.5, 0.36, 0.3), smoothstep(csz * 0.45, csz * 0.45 - 1.5, chip + cr.y * 0.6) * con);
    col += half3(1.0, 0.95, 0.8) * exp(-r / (R * 0.6)) * max(0.0, 1.0 - life * 6.0) * 1.2 * ev;
    // lửa còn nóng rọi sáng người Goku (matte), yếu dần theo khoảng cách và khi lửa tàn
    float er = length(p - explo.xy);
    col += half3(1.0, 0.62, 0.28) * m * exp(-er / (R * 1.3)) * (1.0 - life) * (1.0 - life) * 0.55;
    col += half3(1.0, 0.85, 0.6) * exp(-abs(r - R * 1.4) / 5.0) * max(0.0, 0.7 - life) * 0.9 * ev;
  }

  // 8b. Hit spark kiểu anime lúc cú đấm trúng: sao trắng nhiều cánh nhọn (4 dải cứng, viền mực) bung ra rồi teo,
  //     vòng sóng mảnh nở nhanh, vạch tốc độ toả ra ngoài; không lấy thêm mẫu texture
  if (hit.z >= 0.0) {
    float ha = hit.z;
    float2 hv = p - hit.xy;
    float hr = length(hv);
    float HS = hit.w;
    float hang = atan(hv.y, hv.x);
    float seed = fract(hit.w * 0.137);
    // sao: 9 cánh dài/ngắn xen kẽ, mỗi cánh nhọn (tam giác mũ cao); bung trong ~10% đầu rồi co + mòn dần
    float su = hang * 1.4324 + seed * 6.0;          // 9 cánh / vòng
    float sh = hash(float2(floor(su), seed));
    float tri = 1.0 - abs(fract(su) - 0.5) * 2.0;
    float pop = smoothstep(0.0, 0.1, ha) * (1.0 - 0.45 * smoothstep(0.1, 1.0, ha));
    float srad = HS * pop * (0.26 + pow(tri, 4.0) * (0.45 + 0.6 * sh));
    float sa = 1.0 - hr / max(srad, 1.0) - ha * 0.55;
    if (sa > 0.0) {
      half3 hc = sa < 0.07 ? half3(0.16, 0.05, 0.12)
               : (sa < 0.22 ? half3(1.0, 0.55, 0.08) : (sa < 0.4 ? half3(1.0, 0.9, 0.35) : half3(1.0, 1.0, 0.97)));
      col = mix(col, hc, smoothstep(0.0, 0.02, sa));
    }
    // vạch toả ra: 40 làn quanh tâm, ~nửa số làn bật, mỗi vạch là nêm thon trượt ra ngoài theo tuổi
    float lu = hang * 6.3662 + seed * 17.0;         // 40 làn / vòng
    float lh = hash(float2(floor(lu), seed + 3.1));
    float r0 = HS * (0.35 + ha * 1.6 + lh * 0.3);
    float ll = HS * (0.35 + 0.5 * lh) * (1.0 - ha);
    float lt = (hr - r0) / max(ll, 1.0);
    float lwid = (1.0 - lt) * 5.0 * ascale;          // nửa bề dày vạch (px), thon về mũi ngoài
    float ldx = abs(fract(lu) - 0.5) * hr * 0.157;   // khoảng cách tới giữa làn (px)
    float lnn = (1.0 - smoothstep(lwid * 0.6, lwid, ldx)) * step(0.0, lt) * step(lt, 1.0) * step(0.45, lh);
    col = mix(col, half3(1.0, 0.98, 0.9), lnn * smoothstep(1.0, 0.6, ha));
    // vòng sóng: nở nhanh (ease-out), mỏng dần
    float rr2 = HS * (0.25 + 1.9 * (1.0 - (1.0 - ha) * (1.0 - ha)));
    float rth = 7.0 * (1.0 - ha) * ascale;
    col = mix(col, half3(1.0, 0.97, 0.85), smoothstep(rth, rth * 0.5, abs(hr - rr2)) * (1.0 - ha) * 0.9);
    // quầng sáng nóng ở tâm, tắt nhanh
    col += half3(1.0, 0.85, 0.5) * exp(-hr / (HS * 0.35)) * (1.0 - ha) * (1.0 - ha) * 0.9;
  }

  // 9a. Ánh sáng tràn: vật phát sáng KHÔNG thuộc Goku (cầu khí, tia Kamehameha / Death Beam, vụ nổ dựng trong Blender)
  //     rọi màu của chính nó lên người Goku — gần thì sáng hơn; tóc SSJ là matte nên không tự rọi chính mình
  if (m > 0.05) {
    half3 spill = half3(0.0);
    for (int i = 0; i < 8; i++) {
      float ang = float(i) * 0.785398 + 0.39;
      for (int j = 1; j <= 2; j++) {
        float2 o = p + float2(cos(ang), sin(ang)) * (24.0 + 44.0 * float(j)) * max(ascale, 0.5);
        spill += beauty(o) * tile(ENERGY, o) * (1.0 - tile(MATTE, o)) * (j == 1 ? 1.4 : 0.6);
      }
    }
    col += spill / 16.0 * m * 0.7;
  }

  // 9. Glow từ lớp energy (tóc vàng loé, mắt) render trong Blender
  //    + bloom mềm: lấy thêm 4 mẫu energy lệch ra xung quanh để quầng sáng loang rộng hơn
  float en = tile(ENERGY, p);
  float eb = tile(ENERGY, p + float2(9.0, 0.0)) + tile(ENERGY, p - float2(9.0, 0.0))
           + tile(ENERGY, p + float2(0.0, 9.0)) + tile(ENERGY, p - float2(0.0, 9.0));
  // sáng theo chính màu của vật phát sáng (trước cộng màu vàng ấm cố định → mống mắt xanh ngọc ngả xanh lục nhạt)
  half3 hue = beauty(p) / max(max(beauty(p).r, beauty(p).g), max(beauty(p).b, 0.05));
  // chừa khoảng sáng: chỗ đã gần trắng (vụ nổ kame, bọt nước) cộng ít đi → không cháy trắng cả khung; quầng loang ra nền tối vẫn đủ
  float headroom = 1.0 - 0.6 * smoothstep(0.55, 1.0, max(col.r, max(col.g, col.b)));
  col += (mix(half3(1.0, 0.9, 0.6), hue, 0.7) * en * 0.42 + half3(1.0, 0.8, 0.45) * eb * 0.07) * headroom;

  // 10. Chỉnh màu: Namek giông lạnh → ấm vàng sau biến hình
  float l = dot(col, half3(0.299, 0.587, 0.114));
  // Goku (matte) bị chỉnh lạnh nhẹ hơn cảnh: trước da mặt tóc đen bị khử màu + ám xanh thành mặt nạ trắng xám
  half3 cold = mix(half3(l), col, mix(0.72, 0.93, mk)) * mix(half3(0.9, 1.0, 1.06), half3(0.98, 1.0, 1.02), mk);
  col = mix(cold, col * half3(1.07, 1.02, 0.9), grade);

  // 10b. Sét trên trời: vẽ trong shader để chỉ hiện ở chỗ là trời (depth xa) → nằm sau cột đá, người, mặt đất
  //      (trước là lớp vẽ đè lên cả Goku); lúc loé cả cảnh sáng lên một thoáng như sét rọi thật
  if (bolt.x > 0.01) {
    float sky = smoothstep(120.0, 300.0, zAt(p));
    float bd = 1e4;
    for (int b = 0; b < 2; b++) {
      float fb = float(b);
      float2 a = float2(view.x * (0.1 + 0.8 * hash(float2(bolt.y, fb * 17.3))), -10.0);
      float endY = view.y * (0.22 + 0.22 * hash(float2(bolt.y + fb * 5.1, 2.0)));
      for (int i = 1; i <= 11; i++) {
        float fi = float(i);
        float2 q = float2(a.x + (hash(float2(bolt.y * 7.7 + fi * 1.31, fb)) - 0.5) * view.x * 0.16, endY * fi / 11.0);
        float2 pa = xy - a; float2 ba = q - a;
        float hb = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
        bd = min(bd, length(pa - ba * hb));
        a = q;
      }
    }
    float glow = exp(-bd / 5.0) * 0.85 + exp(-bd / 20.0) * 0.3;
    col += half3(0.64, 0.48, 1.0) * glow * bolt.x * sky;
    col = mix(col, half3(0.96, 0.92, 1.0), smoothstep(1.8, 0.7, bd) * bolt.x * sky);
    col += half3(0.05, 0.045, 0.075) * bolt.x;
    // sét rọi viền: mép người Goku phía tia sét (trên + ngang về phía tia thứ nhất) loé trắng tím một thoáng
    float bx = view.x * (0.1 + 0.8 * hash(float2(bolt.y, 0.0)));
    float2 ld = normalize(float2(sign(bx - xy.x) * 0.8, -0.6));
    float rimB = clamp(mk - smoothstep(0.03, 0.3, tile(MATTE, p + ld * 14.0)), 0.0, 1.0);
    col = mix(col, half3(0.9, 0.86, 1.0), rimB * bolt.x * 0.75);
  }

  // 11. Impact frame: chỗ tối thành trắng, chỗ sáng thành đen
  if (impact > 0.5) { col = half3(step(l, 0.42)); }

  // 12. Grain nhẹ chống banding
  col += (hash(xy + fract(t) * 91.7) - 0.5) * 0.012;
  return half4(col, 1.0);
}`)!;
