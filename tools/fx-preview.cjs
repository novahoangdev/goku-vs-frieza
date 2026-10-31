// Xem trước shader composite ngoài app: lấy khung video pack ở giây t, tính uniform giống useFxUniforms,
// vẽ bằng CanvasKit và lưu PNG. Dùng để chỉnh aura / beam / vụ nổ mà không cần build lại iOS.
//   node tools/fx-preview.cjs <out.png> <giây> [<giây> ...]
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.join(__dirname, "..");
const APP = path.join(ROOT, "app");
const TL = JSON.parse(fs.readFileSync(process.env.FX_TL || path.join(APP, "assets/cinematic/timeline.json"), "utf8"));
const VIDEO = process.env.FX_VIDEO || path.join(APP, "assets/cinematic/cinematic.mp4");
// cú đấm trúng (tia lửa va chạm): marker rung "rigid" sau 11 s và "heavy" sau 16 s, gộp các marker cách nhau < 0.2 s
const RT = TL.retime || [[0, 0], [1200, 1200]];
const rts = (sec) => { const f = sec * TL.fps; for (let i = 1; i < RT.length; i++) if (f <= RT[i][0] || i === RT.length - 1) return (RT[i - 1][1] + (f - RT[i - 1][0]) * (RT[i][1] - RT[i - 1][1]) / (RT[i][0] - RT[i - 1][0])) / TL.fps; return sec; };
const HITS = [];
for (const m of TL.markers) {
  const t = m.f / TL.fps;
  if ((m.name === "haptic:rigid" && t > rts(11)) || (m.name === "haptic:heavy" && t > rts(16)))
    if (!HITS.length || m.f - HITS[HITS.length - 1] > 0.2 * TL.fps) HITS.push(m.f);
}
const hitU = (vf) => {
  let hu = [0, 0, -1, 0];
  for (const f of HITS) {
    const age = (vf - f) / (0.4 * TL.fps);
    if (age >= 0 && age < 1) {
      const fi = anchor("goku_fist_r", f), c0 = anchor("goku_chest", f), h0 = anchor("goku_head", f);
      hu = [fi[0], fi[1], age, 100 * Math.min(3, Math.max(0.12, Math.hypot(h0[0] - c0[0], h0[1] - c0[1]) / 130))];
    }
  }
  return hu;
};
// hướng lửa aura (giống useFxUniforms): bay nhanh trên màn hình thì toé ngược hướng bay
const adir = (vf, chest) => {
  if (!TL.anchors.goku_trail) return [0, -1];
  const tr = anchor("goku_trail", vf);
  if (chest[2] <= 0 || tr[2] <= 0) return [0, -1];
  const dx = tr[0] - chest[0], dy = tr[1] - chest[1], len = Math.hypot(dx, dy);
  if (len <= 1) return [0, -1];
  const k = Math.min(1, Math.max(0, (len - 40) / 120)) * 0.9;
  let ax = (k * dx) / len, ay = -(1 - k) + (k * dy) / len;
  const n = Math.hypot(ax, ay) || 1;
  return [ax / n, ay / n];
};
// sét trời (giống useFxUniforms): FX_BOLT=1 ép loé để xem thử
const CUTS = [0, ...TL.markers.filter((m) => m.name === "cut").map((m) => m.f)];
const lastCut = (f) => CUTS.filter((c) => c <= f).pop() || 0;
const hash1 = (x) => { const s = Math.sin(x * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const bolt = (t) => {
  const age = (t % 0.32) / 0.13, seed = Math.floor(t / 0.32) + lastCut(t * TL.fps) * 0.37;
  if (process.env.FX_BOLT) return [1, seed % 1000];
  return [age > 1 || hash1(seed * 3.1) > track("lightning", t) ? 0 : age < 0.35 || (age > 0.55 && age < 0.8) ? 1 : 0.25, seed % 1000];
};
const [out, ...times] = process.argv.slice(2);
const W = 402, H = 874, SCALE = 2; // iPhone 17 Pro (pt), vẽ @2x

const track = (name, t) => {
  const a = TL.tracks[name];
  const f = Math.min(Math.max(t * TL.fps, 0), a.length - 1);
  const i = Math.floor(f), j = Math.min(i + 1, a.length - 1);
  return a[i] + (a[j] - a[i]) * (f - i);
};
const anchor = (name, frame) => {
  const a = TL.anchors[name];
  const i = Math.min(Math.max(Math.round(frame), 0), a.length / 3 - 1) * 3;
  return [a[i], a[i + 1], a[i + 2]];
};
const src = (f) => fs.readFileSync(path.join(APP, f), "utf8").match(/Make\(`([\s\S]*?)`\)/)[1];

require(path.join(APP, "node_modules/canvaskit-wasm/bin/full/canvaskit.js"))({
  locateFile: (f) => path.join(APP, "node_modules/canvaskit-wasm/bin/full/", f),
}).then((CK) => {
  const fx = CK.RuntimeEffect.Make(src("src/cinematic/shaders/composite.ts"), console.error);
  const tiles = [];
  for (const t of times.map(Number)) {
    // FX_STILL=1: VIDEO là một khung pack đơn lẻ (PNG) của đúng giây t (thử shader trước khi render cả phim)
    const png = execFileSync("ffmpeg", ["-loglevel", "error", "-ss", process.env.FX_STILL ? "0" : String(t), "-i", VIDEO, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], { maxBuffer: 1 << 28 });
    const img = CK.MakeImageFromEncoded(png);
    const vf = t * TL.fps;
    const chest = anchor("goku_chest", vf), head = anchor("goku_head", vf);
    const finger = anchor("frieza_finger", vf), target = anchor("beam_target", vf), bp = anchor("blast_point", vf);
    const aura = track("aura", t);
    const ascale = Math.min(3, Math.max(0.12, Math.hypot(head[0] - chest[0], head[1] - chest[1]) / 130));
    const pxScale = Math.min(1080 / W, 2340 / H);
    const exps = TL.markers.filter((m) => m.name === "haptic:medium").map((m) => m.f);
    let life = -1;
    for (const e of exps) { const age = (vf - e) / (0.9 * TL.fps); if (age >= 0 && age < 1) life = age; }
    const u = [W, H, pxScale, 0, 0, 1 + track("punch", t), 0, track("fxclock", t), chest[0], chest[1], ascale,
      chest[2] > 0 ? aura : 0, track("grade", t), track("impact", t), chest[0], chest[1], track("shock_r", t), track("shock_k", t),
      track("punch", t) * 1.5 + track("flash", t) * 0.4, Math.max(0, aura - 1) * 2.5 + track("flash", t) * 0.4,
      finger[0], finger[1], target[0], target[1], finger[2] > 0 && target[2] > 0 ? track("beam", t) : 0,
      finger[0], finger[1], bp[0], bp[1], finger[2] > 0 ? track("blast", t) : 0, bp[0], bp[1], bp[2] > 0 ? life : -1, ...hitU(vf),
      chest[2], finger[2], target[2], bp[2], ...adir(vf, chest), ...bolt(t)];
    const child = img.makeShaderOptions(CK.TileMode.Clamp, CK.TileMode.Clamp, CK.FilterMode.Linear, CK.MipmapMode.None);
    const shader = fx.makeShaderWithChildren(u.slice(0, fx.getUniformFloatCount()), [child]); // bản shader cũ ít uniform hơn
    const surf = CK.MakeSurface(W * SCALE, H * SCALE);
    const c = surf.getCanvas();
    c.scale(SCALE, SCALE);
    const p = new CK.Paint();
    p.setShader(shader);
    c.drawPaint(p);
    tiles.push(Buffer.from(surf.makeImageSnapshot().encodeToBytes()));
  }
  const tmp = tiles.map((b, i) => { const f = `${out}.${i}.png`; fs.writeFileSync(f, b); return f; });
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", ...tmp.flatMap((f) => ["-i", f]), "-filter_complex",
    tmp.length === 1 ? "[0]scale=600:-1" : `${tmp.map((_, i) => `[${i}]`).join("")}hstack=${tmp.length},scale=${Math.min(2000, tmp.length * 300)}:-1`, out]);
  tmp.forEach((f) => fs.unlinkSync(f));
  console.log("wrote", out);
});
