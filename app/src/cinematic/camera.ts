// Virtual camera: maps between screen coordinates (pt) and the plate (px), exactly like step 1 of the composite shader.
import { PLATE } from "./timeline";

/** x, y: pan (px plate) · zoom · rot (rad) */
export type Cam = [number, number, number, number];

/** Plate px per screen pt, "cover" fit within the 1080×2340 visible area. */
export const coverScale = (w: number, h: number) => {
  "worklet";
  return w > 0 && h > 0 ? Math.min(1080 / w, 2340 / h) : 1;
};

export const plateToScreen = (
  px: number,
  py: number,
  cam: Cam,
  w: number,
  h: number,
  pxScale: number,
): [number, number] => {
  "worklet";
  const cx = ((px - 0.5 * PLATE.w - cam[0]) / pxScale) * cam[2];
  const cy = ((py - 0.5 * PLATE.h - cam[1]) / pxScale) * cam[2];
  const s = Math.sin(cam[3]);
  const k = Math.cos(cam[3]);
  // inverse of the shader rotation
  return [cx * k + cy * s + 0.5 * w, -cx * s + cy * k + 0.5 * h];
};
