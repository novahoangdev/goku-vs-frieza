// Data exported from Blender (blender/scripts/bake_timeline.py) and readers that run inside worklets.
import { makeMutable } from "react-native-reanimated";
import data from "../../assets/cinematic/timeline.json";

export const FPS: number = data.fps;
export const FRAMES: number = data.frames;
export const DURATION = FRAMES / FPS;

/**
 * The film is retimed per shot (blender/scripts/retime.py). Hand-written times in the app still refer to the original
 * 20 s film → mapped through the old → new frame map in timeline.json (older builds lack it: unchanged).
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
/** seconds in the original film → seconds in the retimed film */
export const rts = (sec: number) => rtf(sec * FPS) / FPS;
export const PLATE = { w: data.plate[0], h: data.plate[1] };
/** Visible area in the middle of the plate; the remaining margin is for virtual camera shake / punch-in. */
export const VISIBLE = { w: 1080, h: 2340 };

type Store = { tracks: Record<string, number[]>; anchors: Record<string, number[]> };
/**
 * Track/anchor data (~35k numbers) crosses to the UI runtime exactly ONCE through this shared value, then gets
 * cached in that runtime's globals. Never capture the arrays in a worklet or `.get()` them every frame:
 * both keep creating fresh copies and run Hermes on the UI thread out of memory.
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
/** Kamehameha segment inserted before the final shot (new frames; null in older builds). */
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

/** Linearly interpolates a track at a time (seconds). */
export const track = (name: string, t: number) => {
  "worklet";
  const arr = tl().tracks[name];
  const f = Math.min(Math.max(t * FPS, 0), arr.length - 1);
  const i = Math.floor(f);
  const j = Math.min(i + 1, arr.length - 1);
  return arr[i] + (arr[j] - arr[i]) * (f - i);
};

/** Anchor (plate px) at the video frame on screen; z < 0 means behind the camera. */
export const anchor = (name: string, frame: number): [number, number, number] => {
  "worklet";
  const arr = tl().anchors[name];
  const i = Math.min(Math.max(Math.round(frame), 0), arr.length / 3 - 1) * 3;
  return [arr[i], arr[i + 1], arr[i + 2]];
};

/** Frame of the latest cut ≤ f: particles and lightning change seed after each cut. */
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

/** 1D value noise in -1..1 for screen shake. */
export const n1 = (x: number) => {
  "worklet";
  const i = Math.floor(x);
  const f = x - i;
  const u = f * f * (3 - 2 * f);
  return (hash(i) + (hash(i + 1) - hash(i)) * u) * 2 - 1;
};
