// Camera ảo: map giữa toạ độ màn hình (pt) và plate (px), giống hệt bước 1 của shader composite.
import { PLATE } from "./timeline";

/** x, y: pan (px plate) · zoom · rot (rad) */
export type Cam = [number, number, number, number];

/** px plate trên mỗi pt màn hình, kiểu "cover" trong vùng hiển thị 1080×2340. */
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
  // nghịch đảo phép xoay trong shader
  return [cx * k + cy * s + 0.5 * w, -cx * s + cy * k + 0.5 * h];
};
