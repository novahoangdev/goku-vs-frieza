# Saiyan Awakening: Goku vs Frieza

Cinematic 20 giây cho iPhone. Blender render phần 3D thành một video "pack" (màu + matte Goku + lớp năng lượng);
app React Native vẽ aura, sét, beam, vụ nổ, speed lines... real-time bằng Skia v3 lên chính video đó, Reanimated giữ
đồng hồ 120Hz và haptic. Thiết kế chi tiết: [PLAN.md](PLAN.md).

## Cấu trúc

```
blender/scripts/build_scene.py    dựng toàn bộ cảnh bằng code: Namek, Goku/Frieza, vũ đạo, camera 10 shot, track FX, marker
blender/scripts/face_textures.py  vẽ mặt anime (mắt, mi, miệng, má) bằng SDF + numpy → blender/textures/*.png
blender/textures/                 texture mặt + bầu trời / mặt đất / biển vẽ tay (sinh bằng Codex image gen)
blender/scripts/render_passes.py  render 3 pass: beauty / matte / energy
blender/scripts/bake_timeline.py  xuất app/assets/cinematic/timeline.json (anchor 2D, track FX, marker)
blender/scripts/synth_audio.py    tổng hợp nhạc + SFX bằng numpy theo marker → render/audio/mix.wav
tools/pack.sh                     FFmpeg: 3 pass + tiếng → app/assets/cinematic/cinematic.mp4 (HEVC 10-bit 1728×2496)
tools/build.sh                    chạy tất cả các bước trên
tools/capture-version.sh          chốt một bản: build Release, quay, dựng clip → versions/<tên>/
versions/                         mỗi bản nâng cấp một thư mục (clip demo, bản quay, ảnh) để so sánh
app/                              Expo SDK 58 · react-native-skia 3.8 · react-native-webgpu 0.19 · Reanimated 4.7
```

## Chạy

```bash
PREVIEW=1 tools/build.sh      # bản xem nhanh: 50%, ít sample (~vài phút)
tools/build.sh                # bản final: 100%, 16 sample, motion blur

cd app
npm install
npx expo run:ios --device     # dev build lên iPhone thật (Skia v3 không chạy trên Expo Go)
```

Bản dev có thanh tua ở trên cùng (kéo để tua, hiện số frame và tên shot).

## Chỉnh nhanh

- Timing hiệu ứng: hàm `choreograph()` trong `build_scene.py`, phần "Track FX"; chạy lại `tools/build.sh` là app nhận timeline mới.
- Hình dạng/màu aura, beam, vụ nổ: `app/src/cinematic/shaders/composite.ts`.
- Speed lines, flash, vignette, letterbox: `app/src/cinematic/shaders/overlay.ts`.
- Nhân vật chibi dựng bằng code (`build_goku`, `build_frieza`); mặt là texture dán ôm theo đầu (`face_decal`).
  Đổi nét mặt trong `face_textures.py` rồi chạy lại build. Muốn thay model tải về (vd Sketchfab) thì giữ tên các Empty
  `GOKU_*_anchor`, `FRIEZA_*_anchor` để bake vẫn chạy.
- Soi model nhanh: mở Blender GUI (addon MCP for Blender), chạy `build_scene.py` trong Blender với
  `GVF_BLEND=<file tạm>` để không ghi đè `.blend` đang render.
- Chi tiết thêm theo mảng nằm ở `blender/scripts/extras/*.py` (Goku, Frieza, cảnh), chạy sau cùng trong `build_scene.py`
  với chung biến (G, F, M, helper). Thử riêng một file: `GVF_EXTRAS=<file.py> GVF_BLEND=<file tạm> blender -b -P build_scene.py`.

## Quay clip demo (đăng X)

```bash
tools/build.sh                                   # video final
cd app && EXPO_PUBLIC_DEMO=1 npx expo run:ios --configuration Release --device <udid> --no-bundler && cd ..
tools/promo.sh <udid>                            # → render/promo/saiyan-awakening-demo.mp4
# hoặc gộp cả hai bước và lưu thành một bản để so sánh:
tools/capture-version.sh v3 <udid>               # → versions/v3/
```

`EXPO_PUBLIC_DEMO=1` cho app tự gồng Ki rồi chạy phim, ẩn công cụ dev. `promo.sh` đặt status bar 9:41, quay
simulator, tự dò điểm bắt đầu phim (khung loé sáng lúc biến hình), rồi `blender/scripts/promo.py` dựng clip 4:3:
iPhone 3D khung titan phát bản quay, nền đổi màu theo từng đoạn, chữ lớn phía sau máy, zoom theo nhịp, end card.
