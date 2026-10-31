// Ghép các bản quay simulator của mọi phiên bản (versions/v*/screen.mp4) đứng cạnh nhau, căn cùng lúc phim bắt đầu,
// mỗi cột có nhãn tên bản → versions/compare.mp4 (tiếng lấy từ bản mới nhất).
//   node tools/compare.cjs [v1 v2 ...]
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const ROOT = path.join(__dirname, "..");
const VER = path.join(ROOT, "versions");
const APP = path.join(ROOT, "app");
const FONT = "/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf";
const names = process.argv.length > 2 ? process.argv.slice(2)
  : fs.readdirSync(VER).filter((d) => /^v\d+$/.test(d) && fs.existsSync(path.join(VER, d, "screen.mp4")))
      .sort((a, b) => Number(a.slice(1)) - Number(b.slice(1)));
if (!names.length) throw new Error("chưa có versions/v*/screen.mp4");
// ≤4 bản: một hàng 432×940 mỗi cột; nhiều hơn: lưới 2 hàng, ô nhỏ lại để khung tổng không quá ~1800 px
const ROWS = names.length > 4 ? 2 : 1;
const COLS = Math.ceil(names.length / ROWS);
const W = ROWS === 1 ? 432 : Math.min(432, Math.floor(1800 / COLS / 2) * 2), H = Math.round(W * 940 / 432 / 2) * 2;

// timeline của từng bản: v22+ đã giãn nhịp (retime) → flash biến hình và độ dài phim khác các bản cũ
const tlOf = (n) => { const p = path.join(VER, n, "timeline.json"); return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : null; };
const rtf = (tl, f) => {
  const R = (tl && tl.retime) || [[0, 0], [1200, 1200]];
  for (let i = 1; i < R.length; i++) if (f <= R[i][0] || i === R.length - 1) return R[i - 1][1] + (f - R[i - 1][0]) * (R[i][1] - R[i - 1][1]) / (R[i][0] - R[i - 1][0]);
  return f;
};
const DUR = Math.max(...names.map((n) => { const tl = tlOf(n); return tl ? tl.frames / tl.fps : 20; })) + 2.5;

// lúc phim bắt đầu trong bản quay: khung sáng nhất 18s đầu là flash biến hình (frame 303 của phim gốc → quy đổi)
const filmStart = (mp4, flashF) => {
  const out = execFileSync("ffmpeg", ["-loglevel", "error", "-t", "18", "-i", mp4, "-vf",
    "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"], { maxBuffer: 1 << 26 }).toString();
  let t = 0, best = 0, m = -1;
  for (const line of out.split("\n")) {
    const pt = line.match(/pts_time:([\d.]+)/); if (pt) t = Number(pt[1]);
    const y = line.match(/YAVG=([\d.]+)/); if (y && Number(y[1]) > m) { m = Number(y[1]); best = t; }
  }
  return Math.max(0, best - flashF / 60);
};

require(path.join(APP, "node_modules/canvaskit-wasm/bin/full/canvaskit.js"))({
  locateFile: (f) => path.join(APP, "node_modules/canvaskit-wasm/bin/full/", f),
}).then((CK) => {
  const tf = CK.Typeface.MakeTypefaceFromData(fs.readFileSync(FONT));
  const font = new CK.Font(tf, 44);
  const tmp = fs.mkdtempSync(path.join(require("os").tmpdir(), "cmp-"));
  const inputs = [], filters = [];
  names.forEach((n, i) => {
    const surf = CK.MakeSurface(W, 90);
    const c = surf.getCanvas();
    c.clear(CK.Color(0, 0, 0, 0));
    const bg = new CK.Paint(); bg.setColor(CK.Color(0, 0, 0, 150));
    c.drawRRect(CK.RRectXY(CK.LTRBRect(W / 2 - 70, 14, W / 2 + 70, 76), 18, 18), bg);
    const p = new CK.Paint(); p.setColor(CK.Color(255, 255, 255, 1.0)); p.setAntiAlias(true);
    const glyphs = font.getGlyphIDs(n); const widths = font.getGlyphWidths(glyphs);
    const tw = widths.reduce((a, b) => a + b, 0);
    c.drawText(n, W / 2 - tw / 2, 61, p, font);
    const png = path.join(tmp, `${n}.png`);
    fs.writeFileSync(png, Buffer.from(surf.makeImageSnapshot().encodeToBytes()));
    const t0 = filmStart(path.join(VER, n, "screen.mp4"), rtf(tlOf(n), 303));
    console.log(n, "phim bắt đầu ở", t0.toFixed(2), "s");
    inputs.push("-ss", String(Math.max(0, t0 - 1)), "-t", String(DUR), "-i", path.join(VER, n, "screen.mp4"), "-i", png);
    filters.push(`[${2 * i}:v]fps=60,scale=${W}:${H}:flags=lanczos[s${i}];[s${i}][${2 * i + 1}:v]overlay=0:${H - 110}[c${i}]`);
  });
  const last = names[names.length - 1];
  const mix = path.join(VER, last, "mix.wav");
  const audio = fs.existsSync(mix) ? ["-i", mix] : [];
  const aIdx = names.length * 2;
  // ô trống cuối lưới (số bản lẻ) tô đen
  const cells = names.map((_, i) => `[c${i}]`);
  if (cells.length < ROWS * COLS) {
    filters.push(`color=black:s=${W}x${H}:r=60:d=${DUR}[blank]`);
    cells.push("[blank]");
  }
  const layout = cells.map((_, i) => `${(i % COLS) * W}_${Math.floor(i / COLS) * H}`).join("|");
  const stack = cells.length > 1 ? `${cells.join("")}xstack=inputs=${cells.length}:layout=${layout}[v]` : "[c0]null[v]";
  const out = path.join(VER, "compare.mp4");
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", ...inputs, ...audio, "-filter_complex",
    [...filters, stack].join(";") + (audio.length ? `;[${aIdx}:a]adelay=1000|1000,apad[a]` : ""),
    "-map", "[v]", ...(audio.length ? ["-map", "[a]"] : []), "-t", String(DUR),
    "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out],
    { stdio: "inherit" });
  console.log("wrote", out);
});
