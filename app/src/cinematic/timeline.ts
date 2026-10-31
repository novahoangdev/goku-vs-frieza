// Dữ liệu xuất từ Blender (blender/scripts/bake_timeline.py) và các hàm đọc chạy được trong worklet.
import { makeMutable } from "react-native-reanimated";
import data from "../../assets/cinematic/timeline.json";

export const FPS: number = data.fps;
export const FRAMES: number = data.frames;
export const DURATION = FRAMES / FPS;

/**
 * Phim được giãn nhịp theo shot (blender/scripts/retime.py). Các mốc thời gian viết tay trong app vẫn theo phim
 * 20 s gốc → quy đổi qua bản đồ frame cũ → mới ghi trong timeline.json (bản cũ không có: giữ nguyên).
 */
const RETIME = ((data as { retime?: number[][] }).retime ?? [[0, 0], [1200, 1200]]) as [number, number][];
export const rtf = (f: number) => {
  for (let i = 1; i < RETIME.length; i++) {
    const [a, na] = RETIME[i - 1];
    const [b, nb] = RETIME[i];
    if (f <= b || i === RETIME.length - 1) return na + ((f - a) * (nb - na)) / (b - a);
  }
  return f;
};
/** giây theo phim gốc → giây trong phim đã giãn */
export const rts = (sec: number) => rtf(sec * FPS) / FPS;
export const PLATE = { w: data.plate[0], h: data.plate[1] };
/** Vùng hiển thị ở giữa plate; phần lề còn lại dành cho camera ảo rung / punch-in. */
export const VISIBLE = { w: 1080, h: 2340 };

type Store = { tracks: Record<string, number[]>; anchors: Record<string, number[]> };
/**
 * Dữ liệu track/anchor (~35 nghìn số) đi sang UI runtime đúng MỘT lần qua shared value này, rồi được
 * cache vào global của runtime đó. Không capture mảng vào worklet, cũng không `.get()` mỗi frame:
 * cả hai cách đều tạo bản sao mới liên tục và làm Hermes trên UI thread hết bộ nhớ.
 */
const store = makeMutable<Store>({
  tracks: data.tracks as Record<string, number[]>,
  anchors: data.anchors as Record<string, number[]>,
});
const tl = (): Store => {
  "worklet";
  const g = globalThis as unknown as { __saiyanTimeline?: Store };
  if (!g.__saiyanTimeline) g.__saiyanTimeline = store.get();
  return g.__saiyanTimeline;
};

const markers = data.markers as { f: number; name: string }[];
export const HAPTICS = markers
  .filter((m) => m.name.startsWith("haptic:"))
  .map((m) => ({ t: m.f / FPS, style: m.name.slice(7) }));
export const CUTS = [0, ...markers.filter((m) => m.name === "cut").map((m) => m.f)];
export const EXPLOSIONS = markers.filter((m) => m.name === "haptic:medium").map((m) => m.f);
/** Đoạn Kamehameha chèn trước shot kết (frame mới; bản cũ không có thì null). */
const kame0 = markers.find((m) => m.name === "kame:start");
const kame1 = markers.find((m) => m.name === "kame:end");
export const KAME = kame0 && kame1 ? { f0: kame0.f, f1: kame1.f } : null;

export const SHOTS = [
  { f: 0, name: "Namek storm" },
  { f: 120, name: "Powering up" },
  { f: 240, name: "The eyes" },
  { f: 300, name: "Explosion" },
  { f: 390, name: "Super Saiyan" },
  { f: 510, name: "Frieza attacks" },
  { f: 600, name: "Dodge" },
  { f: 780, name: "Chase" },
  { f: 990, name: "Counterattack" },
  { f: 1110, name: "Finale" },
]
  .map((s) => ({ ...s, f: Math.round(rtf(s.f)) }))
  .concat(KAME ? [{ f: KAME.f0, name: "Kamehameha" }] : [])
  .sort((a, b) => a.f - b.f);

/** Nội suy tuyến tính một track theo thời gian (giây). */
export const track = (name: string, t: number) => {
  "worklet";
  const arr = tl().tracks[name];
  const f = Math.min(Math.max(t * FPS, 0), arr.length - 1);
  const i = Math.floor(f);
  const j = Math.min(i + 1, arr.length - 1);
  return arr[i] + (arr[j] - arr[i]) * (f - i);
};

/** Anchor (px plate) ở đúng frame video đang hiển thị; z < 0 nghĩa là nằm sau camera. */
export const anchor = (name: string, frame: number): [number, number, number] => {
  "worklet";
  const arr = tl().anchors[name];
  const i = Math.min(Math.max(Math.round(frame), 0), arr.length / 3 - 1) * 3;
  return [arr[i], arr[i + 1], arr[i + 2]];
};

/** Frame của cut gần nhất ≤ f: hạt và tia sét đổi seed sau mỗi cut. */
export const lastCut = (f: number) => {
  "worklet";
  let c = 0;
  for (let i = 0; i < CUTS.length; i++) {
    if (CUTS[i] <= f) c = CUTS[i];
  }
  return c;
};

/** Hash 1D → 0..1 */
export const hash = (x: number) => {
  "worklet";
  const s = Math.sin(x * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
};

/** Value noise 1D trong khoảng -1..1 cho rung màn hình. */
export const n1 = (x: number) => {
  "worklet";
  const i = Math.floor(x);
  const f = x - i;
  const u = f * f * (3 - 2 * f);
  return (hash(i) + (hash(i + 1) - hash(i)) * u) * 2 - 1;
};
