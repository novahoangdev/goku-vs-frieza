# Saiyan Awakening: Goku vs Frieza

Cinematic 20 giây cho iPhone: Goku biến hình Super Saiyan trên Namek rồi đánh nhau với Frieza.

Plan ý tưởng và kỹ thuật, viết ngày 29/10/2026. Đang triển khai theo các lựa chọn mặc định ở mục 10.

> **Trạng thái (29/10/2026):** đã chạy được từ Blender tới app.
> - Blender: `build_scene.py` dựng toàn bộ 10 shot bằng code (Namek, Goku/Frieza dạng placeholder toon, vũ đạo, camera, track FX, marker). `render_passes.py`, `bake_timeline.py`, `synth_audio.py` (nhạc + SFX tự tổng hợp) và `tools/pack.sh` đều đã chạy được; một lệnh `tools/build.sh` ra `cinematic.mp4` + `timeline.json`.
> - App: video qua `react-native-webgpu` vào Skia v3; shader composite (aura theo matte, beam, ki blast, vụ nổ, shockwave, god rays, chromatic, impact frame, grade); lớp overlay; sét, tia lửa, title; đồng hồ 120Hz; haptic; màn gồng Ki; thanh tua cho bản dev. Typecheck, lint sạch; build iOS thành công.
> - Còn lại: thay placeholder bằng model thật (P2), polish animation (P3), đo hiệu năng trên iPhone thật (P6).

---

## 0. Tóm tắt

**Sản phẩm.** Một màn app iPhone dài khoảng 20 giây. Trên hành tinh Namek đang nổi giông, Goku gồng, tóc chớp vàng rồi bùng nổ thành Super Saiyan lần đầu. Frieza bắn Death Beam, Goku né, hai bên bay truy đuổi giữa các cột đá, cuối cùng Goku phản đòn bằng một cú đấm. Camera có crash zoom, orbit, dolly zoom, whip pan, slow-mo. Màn hình rung và iPhone rung (haptic) theo từng cú va chạm.

**Kiến trúc chọn: video điện ảnh + FX real-time.**

- Blender làm toàn bộ phần 3D: model, rig, animation, mọi góc máy, ánh sáng, cel-shading. Kết quả là một video HEVC "pack", tức mỗi frame chứa ảnh màu, matte (mặt nạ) của Goku và lớp năng lượng.
- Blender xuất thêm `timeline.json`: toạ độ trên màn hình của ngực, đầu, nắm đấm Goku, ngón tay Frieza... ở từng frame, cùng các track hiệu ứng (aura, flash, shake...) mà bạn keyframe ngay trong Blender.
- Trong app, `react-native-webgpu` decode video bằng phần cứng thẳng vào texture trên GPU. `react-native-skia` v3 vẽ texture đó qua một shader SkSL: aura lửa nằm sau lưng Goku (nhờ matte), rim light, shockwave, impact frame, chỉnh màu. Sau đó vẽ thêm sét, tia lửa, speed lines, Death Beam bám theo toạ độ xuất từ Blender. Reanimated giữ đồng hồ 120Hz khoá theo thời gian video, điều khiển camera ảo (rung, punch-in), UI và haptic.

**Vì sao chọn cách này.** Render offline cho chất lượng cao nhất (motion blur, DOF, outline, ánh sáng aura hắt lên người và mặt đất), còn decode video bằng phần cứng thì luôn mượt. Những thứ chi tiết nhỏ và nhấp nháy nhanh như lửa, sét, hạt thì vẽ real-time ở độ phân giải gốc, vì đưa vào video sẽ bị nén vỡ. Render 3D real-time trong app để dành cho bản 2 (mục 9); bản đó dùng lại toàn bộ asset và lớp FX.

**Ước lượng:** khoảng 20–28 ngày công. Nút thắt là animation nhân vật.

### Stack (kiểm tra ngày 29/10/2026)

| Phần | Dùng | Phiên bản | Ghi chú |
|---|---|---|---|
| 3D | Blender | 5.2.2 LTS (máy bạn), mới nhất 5.2.3 LTS | EEVEE + Shader to RGB cho toon |
| App | Expo SDK 58, React Native | expo 58.0.21, RN 0.88.1, React 19.3 | dev build, New Architecture |
| 2D/GPU | `react-native-skia` | **3.8.1** | Tên mới của `@shopify/react-native-skia` (gói cũ dừng ở 2.14). Backend Graphite, chạy Metal qua Dawn |
| Video → GPU | `react-native-webgpu` | 0.19.2 | `createVideoPlayer()`. Dùng chung GPU device với Skia nên phải khớp bản (0.17+ đi với Skia 3.7+) |
| Animation | `react-native-reanimated`, `react-native-worklets` | 4.7.1, 0.13.1 | `useFrameCallback`, `useDerivedValue`, `scheduleOnRN` |
| Gesture, haptic | `react-native-gesture-handler`, `expo-haptics` | theo SDK 58 | màn "giữ để gồng Ki" |
| Encode | FFmpeg + libx265 | đã có trên máy (Homebrew) | HEVC Main10 |
| Concept, storyboard | Codex CLI (image gen) | đã có trên máy | |
| Điều khiển Blender từ ngoài | Blender MCP | | Chưa kết nối: cần mở Blender và bật addon (mục 5.0) |

---

## 1. Chỉnh lại vài điểm trong research bạn gửi

| Research | Thực tế tháng 10/2026 | Plan dùng |
|---|---|---|
| `@shopify/react-native-skia` | Gói đổi tên thành `react-native-skia`. Bản v3 (ra đầu tháng 10/2026) render bằng Graphite. Gói `@shopify` dừng ở 2.14 | `react-native-skia@3.8.1` |
| Custom shader GLSL | Skia dùng SkSL (cú pháp gần GLSL, hàm `half4 main(float2 xy)`) | SkSL qua `Skia.RuntimeEffect.Make` |
| `react-native-video` / `expo-av` phát video, Skia phủ lên trên | Skia v3 bỏ `useVideo`. Video đi qua `react-native-webgpu` vào texture, Skia vẽ thẳng texture đó mà không copy, nên shader áp được lên chính video chứ không chỉ phủ lên trên. `expo-av` không còn trong Expo SDK 58 | `createVideoPlayer()` → `copyExternalImageToTexture` → `Skia.Image.MakeFromGPUTexture` |
| Test nhanh bằng Expo Go | Expo Go chỉ chứa Skia v2 | Dev build: `npx expo run:ios --device` |
| Model low-poly cho mobile | Video render sẵn nên số poly không ảnh hưởng iPhone | Ưu tiên model đẹp và rig sạch |
| MP4/WebM có alpha | iOS decode phần cứng tốt nhất với HEVC/H.264; WebM alpha không phải đường chính trên iOS | Nhét matte vào chính frame video (mục 4.3) |
| Load GLB real-time "rất nặng" | Với Skia v3, three.js (WebGPU) chạy chung GPU device với Skia và trao texture không copy, nên khả thi hơn trước | Để cho bản 2 (mục 9) |
| 0–5s gồng, 5–10s biến hình, 10–20s bay né | Biến hình kéo dài tới giây 10 thì không còn thời gian cho trận đánh | Biến hình gói trong giây 2–6.5, phần còn lại là đánh nhau (10 shot) |

---

## 2. Kịch bản 20 giây

Bối cảnh lấy từ cảnh kinh điển trên Namek: Frieza vừa giết Krillin, Goku nổi giận và biến hình lần đầu (xem lại tập 95 của DBZ để học bố cục và nhịp). Trời Namek xanh lục chuyển sang giông bão, sét tím, mặt đất nứt.

Khung hình dọc 9:19.5 (vừa màn iPhone), 60fps, 1200 frame.

| # | Thời gian (frame) | Shot | Camera (Blender) | Diễn xuất |
|---|---|---|---|---|
| 1 | 0.0–2.0 (0–119) | Namek nổi giông | Drone từ trên cao, dolly-in và hạ dần độ cao, 24mm | Goku tóc đen, áo rách, cúi đầu nắm chặt tay; Frieza lơ lửng cười khẩy; trời tối dần |
| 2 | 2.0–4.0 (120–239) | Gồng | Low-angle, orbit 40° quanh Goku, 35mm | Siết nắm đấm, đá vụn lơ lửng bay lên, mặt đất nứt toả ra |
| 3 | 4.0–5.0 (240–299) | Đôi mắt | Cận cảnh mắt, push-in chậm, 4 frame cuối crash zoom-in | Đồng tử chớp đen ↔ xanh ngọc, tóc chớp vàng 3 nhịp |
| 4 | 5.0–6.5 (300–389) | Bùng nổ | Crash zoom-out 135→24mm trong 8 frame, kéo lùi | Tóc dựng vàng, aura nổ, sóng xung kích san phẳng mặt đất, đá văng |
| 5 | 6.5–8.5 (390–509) | Super Saiyan | Orbit 180° chậm, dừng ở góc hero low-angle | Goku đứng yên, aura cháy, tóc phất, ánh mắt lạnh |
| 6 | 8.5–10.0 (510–599) | Frieza ra đòn | Dolly zoom vào mặt Frieza, cắt sang góc qua vai Frieza | Frieza sững người, giơ ngón tay bắn loạt Death Beam |
| 7 | 10.0–13.0 (600–779) | Né | Bullet-time orbit 90° (tốc độ 1 → 0.25 → 1), kết bằng whip pan | Goku né tia chỉ bằng nghiêng đầu, xoay người; Frieza lao vào tung combo, Goku né bằng tàn ảnh (zanzoken) |
| 8 | 13.0–16.5 (780–989) | Truy đuổi trên không | Bám đuôi theo đường cong luồn qua các cột đá, nghiêng theo cua, 2 whip pan | Frieza bắn ki blast, Goku lộn vòng né, cột đá nổ tung |
| 9 | 16.5–18.5 (990–1109) | Phản đòn | Cut khi Goku biến mất, freeze 0.25s, crash zoom vào điểm va chạm | Goku hiện sau lưng Frieza, một cú đấm vào bụng |
| 10 | 18.5–20.0 (1110–1199) | Kết | Pull-out chậm ra toàn cảnh, freeze frame | Frieza văng xuống biển, cột nước bắn lên; Goku lơ lửng, aura dịu; hiện title |

Lớp hiệu ứng theo shot (âm thanh mix sẵn trong video):

| # | Skia (real-time) | Camera ảo (Reanimated) | Haptic | Âm thanh |
|---|---|---|---|---|
| 1 | Sét tím 2–3 tia trên trời, bụi bay ngang, vignette đậm dần, màu lạnh | | | gió, sấm xa, nhạc trầm |
| 2 | Bụi và đá nhỏ bay lên, heat haze quanh người, tia điện nhỏ dưới chân | rung 0 → 0.35 | tick nhẹ, dày dần (140 → 50ms) | rumble tăng dần, tiếng gồng |
| 3 | Chromatic aberration và flash vàng 2 frame mỗi nhịp tóc chớp | punch-in nhẹ mỗi nhịp | 3 lần `Rigid` | nhịp tim |
| 4 | Impact frame 3 frame (đen trắng đảo màu) → flash trắng → vòng shockwave → aura nổ (vọt lên 1.4 rồi về 1) → god rays → speed lines toả tròn | rung 1.0, tắt dần trong 0.6s | 2 lần `Heavy` | tiếng nổ lớn, tiếng thét |
| 5 | Aura 3 dải màu cháy liên tục, tia lửa vàng bay lên, rim vàng, màu chuyển ấm | | | aura hum, nhạc lên |
| 6 | Death Beam hồng tím từ ngón tay Frieza, loé tím ở viền màn hình | punch-in nhỏ mỗi phát | `Light` mỗi tia | tiếng beam, nhạc căng |
| 7 | Beam lướt qua camera, vệt chuyển động, hạt và lửa chậm lại theo slow-mo | | `Soft` khi né, `Rigid` khi đỡ | whoosh slow-mo |
| 8 | Speed lines theo hướng bay, ki blast, vụ nổ cel-shaded tại điểm trúng | rung theo vụ nổ | `Medium` mỗi vụ nổ | gió tốc độ, tiếng nổ |
| 9 | Lúc freeze: mất màu trừ màu vàng; impact frame 2 frame, shockwave, speed lines từ điểm va chạm | punch-in 1.0 → 1.12, rung 1.0 | 3 lần `Heavy` liền nhau | im 0.25s rồi nổ |
| 10 | Aura dịu, hạt bay chậm, letterbox trượt vào, title "SUPER SAIYAN" vàng kim có vệt sáng quét | spring scale cho title | `Success` | nhạc kết |

Nhịp tổng: dồn nén (0–5s) → bùng nổ (5–6.5s) → phô sức mạnh (6.5–8.5s) → hành động (8.5–18.5s) → lắng (18.5–20s).

---

## 3. Art direction

Phong cách: 3D anime cel-shading giống Dragon Ball FighterZ. Nên xem talk GDC 2015 "GuiltyGear Xrd's Art Style: The X Factor Between 2D and 3D" của Arc System Works, studio làm FighterZ.

| Thành phần | Màu |
|---|---|
| Trời Namek → giông | `#8FD18A` → `#24382E` |
| Cỏ/đất · nước · cột đá | `#5FA38F` · `#3E9C9A` · `#7E9F86` |
| Sét | lõi `#F1E6FF`, viền `#A27BFF` |
| Aura SSJ | lõi `#FFF6C8`, giữa `#FFD23F`, viền `#FF9F1C` |
| Tóc SSJ · mắt SSJ | `#FFD54A` (bóng `#E2A21B`) · `#2EC4B6` |
| Võ phục Goku | cam `#F28C28`, xanh `#1F3A93` |
| Frieza · Death Beam | trắng `#F4F1F8`, tím `#8E3FBF`, mắt `#D7263D` · lõi trắng, viền `#FF5FD2` |

Nguyên tắc:

- Bóng đổ có màu (da ngả hồng cam, áo cam ngả nâu đỏ), không dùng đen. Outline màu nâu sẫm, nét ngoài dày, nét trong mảnh.
- Aura và vụ nổ tô 2–3 dải màu cứng như anime; glow mềm chỉ dùng ở lõi.
- Va chạm lớn có impact frame đen trắng 2–3 frame.
- Mượt hay "chất anime": mặc định chuyển động nhân vật nội suy 60fps cho mượt; ở va chạm thì giữ pose 2–4 frame (hit-stop). Có thể thử giữ mỗi pose 2 frame như FighterZ ở vài khoảnh khắc. Camera và FX lúc nào cũng mượt.

---

## 4. Kiến trúc kỹ thuật

### 4.1 Pipeline

```
Codex (concept, storyboard) ──► Blender 5.2: model · rig · animation · camera · EEVEE toon
                                   │
                                   ├─ render_passes.py ─► PNG beauty / matte / energy (1152×2496, 60fps)
                                   ├─ bake_timeline.py ─► timeline.json (anchor 2D + track FX + marker)
                                   └─ VSE hoặc DAW ─────► mix.wav (nhạc + SFX)
                                              │
                        tools/pack.sh (FFmpeg) ─► cinematic.mp4 (HEVC Main10, 1728×2496, 60fps, BT.709)
                                              │
iPhone app (Expo SDK 58, dev build) ◄─────────┘
  react-native-webgpu   createVideoPlayer → copyExternalImageToTexture → GPUTexture
  react-native-skia v3  MakeFromGPUTexture → shader composite (tách tile, aura, grade…) + lớp FX
  Reanimated 4          đồng hồ 120Hz khoá theo video · camera ảo · UI · marker → haptic
```

### 4.2 Việc nào làm ở đâu

| Hiệu ứng | Làm ở | Lý do |
|---|---|---|
| Model, cel-shading, outline, motion blur, DOF | Blender | cần hình học 3D |
| Ánh sáng aura hắt lên người và mặt đất | Blender (light vàng, cường độ theo `FX.aura`) | chỉ 3D mới chiếu sáng đúng |
| Tóc đen → vàng, mắt đen → xanh ngọc, nhịp chớp | Blender (keyframe material, đổi mesh) | Skia chỉ thêm flash và chromatic |
| Đá bay, đất nứt, cột nước, tàn ảnh | Blender | gắn với hình học |
| Mọi góc máy (orbit, crash zoom, dolly zoom, whip pan) | Blender | phối cảnh thật, motion blur thật |
| Aura lửa vàng | Skia, shader đọc matte | sống động, nét ở mọi độ phân giải, không bị nén vỡ |
| Sét, tia điện, speed lines, shockwave, impact frame, flash, chỉnh màu, grain | Skia | chi tiết nhỏ hoặc thuần hậu kỳ |
| Death Beam, ki blast, vụ nổ | Skia theo anchor, kèm light flash trong Blender | |
| Bụi, tia lửa, mảnh vụn nhỏ | Skia (`Atlas` ≤ 300 sprite; bụi mịn vẽ trong shader) | |
| Rung, punch-in | Reanimated (camera ảo) | đồng bộ với haptic |
| Haptic | `expo-haptics` theo marker | |
| Âm thanh | Mix sẵn trong video | player tự giữ hình và tiếng khớp nhau |

### 4.3 Video "pack"

```
           1152 px              576 px
  ┌─────────────────────┬────────────────┐
  │                     │ MATTE Goku     │ 1248
  │  BEAUTY (màu)       │ (xám, ½ res)   │
  │  1152 × 2496        ├────────────────┤
  │  vùng hiển thị      │ ENERGY         │ 1248
  │  1080 × 2340 + lề   │ (xám, ½ res)   │
  └─────────────────────┴────────────────┘
     Frame 1728 × 2496 · 60fps · HEVC Main10 · BT.709
```

- Beauty 1152×2496 (tỉ lệ 9:19.5 như iPhone đời mới). Phần hiển thị là 1080×2340 ở giữa; lề khoảng 3.3% mỗi phía để camera ảo rung hay punch-in không lộ mép.
- Matte và energy lưu dưới dạng ảnh xám (luma) ở ½ độ phân giải. HEVC 4:2:0 giảm độ phân giải phần màu xuống một nửa: nếu nhét mỗi matte vào một kênh R/G/B thì chúng lem sang nhau, còn luma thì giữ nguyên.
- Mọi kích thước là bội số của 16 để khớp khối mã hoá. Shader kẹp toạ độ trong từng tile để không lấy nhầm pixel của tile bên cạnh.
- Mỗi frame 4.3 MP, nhỏ hơn 4K (8.3 MP), nên decoder phần cứng của iPhone chạy 60fps thoải mái. Dung lượng ước tính 25–45 MB cho 20 giây (CRF 17).
- Muốn khung ngang thì xoay spec: beauty 2496×1152, hai tile 1248×576 xếp bên dưới.

### 4.4 `timeline.json`

```jsonc
{
  "fps": 60, "frames": 1200, "plate": [1152, 2496],
  "anchors": {               // mỗi frame 3 số: x, y (px trên plate, gốc trên-trái), z (độ sâu tới camera)
    "goku_chest": [576.2, 1320.5, 6.41 /* … */],
    "goku_head": [], "goku_fist_r": [], "frieza_finger": [], "beam_target": []
  },
  "tracks": {                // custom prop của Empty "FX" trong Blender, 1 số mỗi frame
    "aura": [], "flash": [], "shake": [], "punch": [], "speedlines": [], "impact": [],
    "grade": [], "lightning": [], "shock_r": [], "shock_k": [], "title": [],
    "fxclock": []            // cộng dồn FX.timescale: lúc slow-mo thì FX trong app cũng chậm lại
  },
  "markers": [ { "f": 300, "name": "haptic:heavy" }, { "f": 390, "name": "cut" } ]
}
```

Khoảng 35 nghìn số, cỡ 200 KB, `require` thẳng vào bundle.

### 4.5 Các lớp vẽ mỗi frame

```
<Canvas>  (Graphite · 120Hz trên iPhone Pro)
 ├─ Fill + Shader composite    frame video + uniform từ timeline
 │    camera ảo → shockwave → beauty → aura sau lưng (matte) → rim → beam/ki blast (SDF)
 │    → glow energy → chỉnh màu → impact frame → grain
 ├─ Lightning                  Path + BlurMask, neo theo anchor hoặc vùng trời
 ├─ Sparks / debris            Atlas ≤ 300 sprite, chạy theo fxclock
 ├─ SpeedLines                 SkSL, tâm là anchor hoặc giữa màn
 ├─ Flash · vignette · letterbox
 └─ TitleCard                  Text + LinearGradient + spring
```

### 4.6 Đồng hồ và đồng bộ

- Video là đồng hồ chính. Tiếng nằm trong video nên player tự giữ hình và tiếng khớp nhau.
- Vòng lặp lấy frame chạy trên JS (`requestAnimationFrame`, 60Hz): lấy frame mới cùng `player.currentTime`, ghi vào shared value `videoTime`.
- UI thread (`useFrameCallback`, 120Hz) giữ biến `t`: mỗi frame cộng thêm dt rồi kéo nhẹ về `videoTime`. Lệch quá 2 frame (seek, giật) thì nhảy thẳng tới `videoTime`.
- FX bám nhân vật (tâm aura, beam, sét quanh người) đọc anchor theo đúng frame video đang hiển thị (`round(videoTime × 60)`). Màn hình chạy 120Hz mà video chỉ 60fps, nên nội suy anchor sẽ làm FX trượt nửa frame so với người. FX tự do (noise lửa, hạt, rung) thì dùng `t` cho mượt.

---

## 5. Blender (5.2 LTS)

### 5.0 Kết nối Blender MCP

Mở Blender 5.2.2 và bật addon MCP (nếu chưa cài thì chạy `uvx mcp-for-blender install-addon`, rồi bật lại addon). Khi đó dựng scene, camera, material, view layer, chạy render và bake được bằng script. Lúc viết plan này MCP chưa kết nối được tới Blender vì Blender chưa mở.

### 5.1 Cấu trúc file

```
goku_vs_frieza.blend   60fps · 1152×2496 · frame 0–1199
├─ CHARS/   GOKU_RIG (body, hair_base, hair_ssj, eyes) · FRIEZA_RIG (body, tail)
├─ ENV/     terrain, spires, ajisa_trees, sea, sky_dome, clouds, debris
├─ LIGHTS/  key_sun, rim, aura_lights (driver theo FX.aura)
├─ CAMS/    CAM_01 … CAM_10 (bind vào marker)
└─ CTRL/    FX (Empty, custom props), BEAM_TARGET
```

### 5.2 Asset

Goku, theo thứ tự ưu tiên:

1. Model trên Sketchfab đã rig, tải được, license cho phép (lọc bằng `search_assets` khi MCP chạy).
2. Codex vẽ turnaround T-pose → `generate_3d` (image → 3D, 1–3 phút, có thể tốn credit) → remesh, dọn mesh, rig.
3. Tự dựng.

Nguồn nào cũng phải:

- Tách tóc thành mesh riêng: `hair_base` (đen) và `hair_ssj` (vàng, dựng ngược). Biến hình là đổi mesh kèm shape key.
- Mắt và lông mày dùng material riêng để đổi màu.
- Có shape key `ssj_bulk` (cơ to hơn chút), `angry`, `scream`. Áo rách kiểu Namek là tuỳ chọn.

Frieza (dạng cuối): khối đơn giản, thân trắng với các mảng tím, dễ tự dựng nhất. Đuôi rig bằng chuỗi bone + Spline IK.

Namek: dựng procedural bằng script hoặc Geometry Nodes. Gồm mặt đất có vết nứt (mask animate), cột đá đỉnh phẳng, cây Ajisa (thân mảnh, tán tròn), biển, bầu trời gradient, mây toon. Cần thêm chút chi tiết thì lấy texture CC0 từ Poly Haven.

Số poly không ảnh hưởng iPhone vì video render sẵn; chỉ cần rig sạch và render nhanh.

### 5.3 Toon trong EEVEE

1. Material nhân vật: `Diffuse BSDF → Shader to RGB → ColorRamp (Constant, 2–3 nấc)` nhân màu gốc → `Emission`. Thêm `Layer Weight → ColorRamp` cho rim.
2. Đèn: 1 Sun làm key, chỉnh hướng riêng cho từng shot (được phép ăn gian theo góc máy); world màu phẳng.
3. Outline kiểu inverted hull: modifier `Solidify` (offset âm, Flip Normals, Material Offset trỏ tới material outline nâu sẫm, bật Backface Culling), độ dày theo vertex group. Cần nét bên trong thì thêm Grease Pencil Line Art.
4. Mặt: custom normals (Data Transfer từ một khối ellipsoid) để bóng trên mặt gọn kiểu anime, đúng kỹ thuật của Guilty Gear Xrd và FighterZ.
5. Color Management: View Transform **Standard** (AgX mặc định làm nhạt màu anime), Look None, giữ Dither 1.0; Film Filter khoảng 1.0px cho nét sắc.
6. Đèn aura: point/area light vàng quanh Goku, cường độ driver theo `FX["aura"]`. Nhờ vậy aura do Skia vẽ trong app và ánh sáng hắt lên người, mặt đất trong Blender luôn khớp nhau.

### 5.4 Rig và animation

- Rig: auto-rig của Mixamo (nhanh) hoặc Rigify. Lấy clip nền trên Mixamo (thế thủ, đấm, né, lơ lửng, trúng đòn) → retarget → chỉnh tay theo animatic.
- Pose phải mạnh khi nhìn từ camera của shot đó; được phép chỉnh pose riêng cho từng shot. Va chạm có hit-stop 2–4 frame; động tác nhanh dựa vào motion blur.
- Keyframe biến hình:
  - f240–299: `hair_base` và `hair_ssj` thay nhau hiện 3 lần (mỗi lần 3–4 frame), mắt đổi màu cùng nhịp.
  - f300: chuyển hẳn sang `hair_ssj`; shape key `grow` 0 → 1 trong 6 frame (tóc dựng lên); `ssj_bulk` 0 → 1; emission tóc 3 → 1 (loé rồi dịu); đèn aura 0 → max.
  - f300–330: đá văng (rigid body bake hoặc keyframe), vết nứt lan rộng.
- Zanzoken (shot 7): nhân bản mesh Goku tại chỗ cũ, material trong suốt mờ dần trong 8–10 frame.
- Slow-mo (shot 7): animate chậm trực tiếp, không dùng Time Stretching vì nó áp cho cả file. Keyframe `FX.timescale` 1 → 0.25 → 1 để FX trong app chậm theo.

### 5.5 Camera

- Mỗi shot một camera `CAM_xx`. Đặt marker ở đầu shot rồi **Bind Camera to Markers** (Ctrl+B trên timeline): render một lần cả 20 giây, cut tự động.
- Crash zoom: animate focal length (ví dụ 135 → 24mm trong 6–8 frame, ease-in mạnh) kèm dịch nhẹ.
- Dolly zoom: lùi camera đồng thời tăng focal để chủ thể giữ nguyên kích thước, driver `focal = focal0 × distance / distance0`.
- Orbit: camera làm con của một Empty đặt tại Goku, xoay Empty quanh trục Z; `Track To` vào bone ngực.
- Truy đuổi: `Follow Path` theo đường Bezier luồn qua cột đá, `Track To` vào Goku, nghiêng (roll) theo cua.
- Whip pan: xoay 60–90° trong 4–6 frame, bật motion blur; đặt cut ở giữa cú lia.
- Rung tay: Noise modifier rất nhẹ trên F-curve rotation. Rung mạnh để app làm, tránh rung hai lần.
- DOF nhẹ cho cận cảnh; motion blur EEVEE (shutter 0.5) cho cả clip.

### 5.6 Track FX và marker

- Empty `FX` có các custom prop dạng float: `aura, flash, shake, punch, speedlines, impact, grade, lightning, shock_r, shock_k, timescale, title`. Keyframe trong Graph Editor như animate bình thường, nên chỉnh timing hiệu ứng ngay cạnh animatic.
- Marker đặt tên theo quy ước: `haptic:heavy`, `haptic:rigid`, `cut`, `beam`, `explode`. Marker bind camera thì giữ tên shot.

### 5.7 Render

- EEVEE, 1152×2496, 60fps, frame 0–1199, bật motion blur.
- View layer `BEAUTY` (đầy đủ) và `MATTE_GOKU` (collection ENV và Frieza đặt Holdout, material override màu trắng phẳng, lấy kênh Alpha). Cách này cho matte có motion blur và DOF giống hệt beauty.
- Energy: Emission pass của `BEAUTY`, đổi sang ảnh xám trong compositor.
- Xuất PNG 16-bit qua node File Output: `render/beauty/####.png`, `render/matte/####.png`, `render/energy/####.png`.
- Ước tính trên M5 Pro: 1–2 giây mỗi frame mỗi layer, render đủ mất khoảng 1 giờ. Bản preview 50% không motion blur khoảng 10 phút.

### 5.8 `bake_timeline.py`

```python
# Chạy: /Applications/Blender.app/Contents/MacOS/Blender -b blender/goku_vs_frieza.blend -P blender/scripts/bake_timeline.py
import bpy, json
from bpy_extras.object_utils import world_to_camera_view

scene = bpy.context.scene
W, H = scene.render.resolution_x, scene.render.resolution_y        # 1152 × 2496
FPS = scene.render.fps
ANCHORS = {                                                         # đổi tên bone theo rig thật
    "goku_chest":    ("GOKU_RIG", "mixamorig:Spine2"),
    "goku_head":     ("GOKU_RIG", "mixamorig:Head"),
    "goku_fist_r":   ("GOKU_RIG", "mixamorig:RightHand"),
    "frieza_finger": ("FRIEZA_RIG", "mixamorig:RightHandIndex3"),
    "beam_target":   ("BEAM_TARGET", None),
}
TRACKS = ["aura", "flash", "shake", "punch", "speedlines", "impact", "grade",
          "lightning", "shock_r", "shock_k", "title"]
fx = bpy.data.objects["FX"]

out = {"fps": FPS, "frames": 0, "plate": [W, H],
       "anchors": {k: [] for k in ANCHORS}, "tracks": {k: [] for k in TRACKS + ["fxclock"]}}
clock = 0.0
for f in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(f)                                              # camera bind theo marker cũng đổi ở đây
    for name, (obj, bone) in ANCHORS.items():
        ob = bpy.data.objects[obj]
        world = ob.matrix_world @ ob.pose.bones[bone].head if bone else ob.matrix_world.translation
        v = world_to_camera_view(scene, scene.camera, world)       # x, y ∈ [0, 1] gốc dưới-trái; z = độ sâu
        out["anchors"][name] += [round(v.x * W, 1), round((1 - v.y) * H, 1), round(v.z, 2)]
    for k in TRACKS:
        out["tracks"][k].append(round(float(fx[k]), 4))
    out["tracks"]["fxclock"].append(round(clock, 4))
    clock += float(fx["timescale"]) / FPS                           # slow-mo thì FX trong app chậm theo
    out["frames"] += 1

out["markers"] = sorted(({"f": m.frame, "name": m.name} for m in scene.timeline_markers),
                        key=lambda m: m["f"])
with open(bpy.path.abspath("//../app/assets/cinematic/timeline.json"), "w") as fp:
    json.dump(out, fp, separators=(",", ":"))
```

### 5.9 Pack và encode

```bash
# tools/pack.sh: 3 chuỗi PNG + tiếng → 1 video pack
ffmpeg -y \
  -framerate 60 -i render/beauty/%04d.png \
  -framerate 60 -i render/matte/%04d.png \
  -framerate 60 -i render/energy/%04d.png \
  -i render/audio/mix.wav \
  -filter_complex "
    [1:v]format=gray16le,scale=576:1248:flags=area,format=gbrp16le[m];
    [2:v]format=gray16le,scale=576:1248:flags=area,format=gbrp16le[e];
    [m][e]vstack=inputs=2[data];
    [0:v]format=gbrp16le[b];
    [b][data]hstack=inputs=2,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le[v]" \
  -map "[v]" -map 3:a \
  -c:v libx265 -preset slow -crf 17 -x265-params keyint=60:min-keyint=60 \
  -tag:v hvc1 -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
  app/assets/cinematic/cinematic.mp4
```

- `-tag:v hvc1`: thiếu cái này thì iOS không nhận file HEVC.
- `out_color_matrix=bt709`: không ép thì FFmpeg có thể đổi màu bằng ma trận BT.601, lên iPhone màu bị lệch.
- Keyframe mỗi giây để tua và "Xem lại" nhanh.
- Bản preview thì đổi sang encoder phần cứng `hevc_videotoolbox` của Mac cho nhanh.

### 5.10 Âm thanh

Nhạc và SFX lấy từ nguồn miễn phí bản quyền (Freesound CC0, Pixabay). Mix trong Blender VSE để nghe cùng animatic, hoặc trong DAW, rồi xuất `render/audio/mix.wav` 48kHz. Không dùng nhạc và giọng gốc của anime.

---

## 6. App

### 6.1 Khởi tạo

```bash
cd ~/Documents/git/personal-repo/goku-vs-frieza
npx create-expo-app@latest app --template blank-typescript        # Expo SDK 58
cd app
npx expo install react-native-reanimated react-native-worklets react-native-gesture-handler \
  expo-haptics expo-asset expo-font expo-dev-client
npm i react-native-skia@^3.8.1 react-native-webgpu@^0.19.2
npm ls react-native-webgpu-dawn       # chỉ được có 1 phiên bản (Skia và WebGPU dùng chung Dawn)
npx expo run:ios --device              # dev build lên iPhone thật
```

- Expo SDK 58 vẫn ghim `@shopify/react-native-skia@2.14` (v2), nên cài `react-native-skia` v3 thủ công như trên. Không cài song song hai gói vì chúng cùng một native module.
- Cài lên iPhone: Apple ID miễn phí ký được bản dev (hết hạn sau 7 ngày); TestFlight cần tài khoản developer trả phí.

`app.json`:

```json
{
  "expo": {
    "orientation": "portrait",
    "ios": {
      "supportsTablet": false,
      "infoPlist": { "CADisableMinimumFrameDurationOnPhone": true }
    }
  }
}
```

`CADisableMinimumFrameDurationOnPhone` mở khoá 120Hz trên iPhone ProMotion; thiếu nó thì animation bị giới hạn 60Hz.

### 6.2 Cấu trúc thư mục

```
goku-vs-frieza/
├─ PLAN.md
├─ blender/
│  ├─ goku_vs_frieza.blend
│  └─ scripts/   setup_scene.py · toon_materials.py · render_passes.py · bake_timeline.py
├─ render/       (không commit) beauty/ · matte/ · energy/ · audio/mix.wav
├─ tools/        pack.sh · preview.sh (render 50% → pack → copy vào app)
└─ app/          Expo
   ├─ assets/cinematic/   cinematic.mp4 · timeline.json · sparks.png · fonts/
   └─ src/
      ├─ screens/CinematicScreen.tsx
      ├─ cinematic/
      │  ├─ useCinematicVideo.ts    video → SkImage
      │  ├─ timeline.ts             đọc track và anchor (worklet)
      │  ├─ haptics.ts              marker → expo-haptics
      │  ├─ shaders/                composite · speedLines · explosion
      │  └─ layers/                 Lightning · Sparks · SpeedLines · Flash · TitleCard
      ├─ ui/                        KiChargeIntro · ReplayButton
      └─ dev/Scrubber.tsx           tua frame, bật tắt từng lớp FX
```

### 6.3 Video → Skia

```ts
// src/cinematic/useCinematicVideo.ts
import { useEffect, useRef } from "react";
import { useSharedValue } from "react-native-reanimated";
import { Skia, type SkImage } from "react-native-skia";
import { createVideoPlayer, importDevice, type VideoPlayer } from "react-native-webgpu";

// Decode bằng phần cứng → texture trên GPU device của Skia → SkImage, không đi qua CPU
export function useCinematicVideo(uri: string | null) {
  const frame = useSharedValue<SkImage | null>(null);
  const videoTime = useSharedValue(0);
  const player = useRef<VideoPlayer | null>(null);

  useEffect(() => {
    if (!uri) return;
    const device = importDevice(Skia.getNativeDevice());
    const p = createVideoPlayer(uri);
    p.loop = false;    // mặc định là true
    p.volume = 1;
    p.currentTime = 0; // đang pause vẫn trả về frame đầu cho màn intro
    player.current = p;

    let texture: GPUTexture | null = null;
    let raf = 0;
    const pump = () => {
      const f = p.copyLatestFrame();
      if (f) {
        if (!texture || texture.width !== f.width || texture.height !== f.height) {
          const old = frame.value;
          frame.value = null;
          old?.dispose();
          texture?.destroy();
          texture = device.createTexture({
            size: [f.width, f.height],
            format: navigator.gpu.getPreferredCanvasFormat(),
            usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING,
          });
        }
        // YUV → RGB làm trên GPU; video encode đứng sẵn nên không cần đảo rộng/cao
        device.queue.copyExternalImageToTexture(
          { source: f, rotation: p.rotation },
          { texture },
          [f.width, f.height],
        );
        f.release(); // trả buffer cho decoder ngay
        const old = frame.value;
        frame.value = Skia.Image.MakeFromGPUTexture(texture); // ảnh mới làm Canvas vẽ lại
        old?.dispose();
        videoTime.value = p.currentTime;
      }
      raf = requestAnimationFrame(pump);
    };
    raf = requestAnimationFrame(pump);

    return () => {
      cancelAnimationFrame(raf);
      p.release();
      const last = frame.value;
      frame.value = null;
      last?.dispose();
      texture?.destroy();
    };
  }, [uri, frame, videoTime]);

  return { frame, videoTime, player };
}
```

- `requestAnimationFrame` trên JS bị giới hạn 60Hz, vừa đúng 60fps của video. Spike P1 thử chạy vòng lấy frame trong worklet trên UI thread (120Hz, không bị JS thread làm giật). Làm được hay không tuỳ `VideoPlayer` có truyền vào worklet được không.
- Đường dẫn file: `useAssets(require("../../assets/cinematic/cinematic.mp4"))` của `expo-asset` → `localUri`.

### 6.4 Shader composite (phác thảo, các hằng số sẽ chỉnh trên máy)

```ts
// src/cinematic/shaders/composite.ts
import { Skia } from "react-native-skia";

export const composite = Skia.RuntimeEffect.Make(`
uniform shader video;    // frame pack 1728×2496
uniform float2 view;     // kích thước canvas (pt)
uniform float  pxScale;  // số px plate trên mỗi pt màn hình (cover)
uniform float4 cam;      // xy: pan (px plate), z: zoom, w: xoay (rad)
uniform float  t;        // fxclock (giây)
uniform float2 chest;    // anchor ngực Goku (px plate)
uniform float  aura;     // 0..1.4
uniform float  grade;    // 0: Namek lạnh → 1: vàng SSJ
uniform float  impact;   // 1: impact frame đen trắng
uniform float4 shock;    // xy: tâm, z: bán kính, w: cường độ

const float2 PLATE  = float2(1152.0, 2496.0);
const float2 MATTE  = float2(1152.0, 0.0);
const float2 ENERGY = float2(1152.0, 1248.0);

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
// Tile ½ độ phân giải; kẹp toạ độ để không lấy lấn sang tile bên cạnh
float tile(float2 origin, float2 p) {
  return video.eval(origin + clamp(p * 0.5, float2(0.5), PLATE * 0.5 - 0.5)).r;
}

half4 main(float2 xy) {
  // 1. Màn hình → plate qua camera ảo (rung, punch-in, xoay)
  float2 c = xy - 0.5 * view;
  float s = sin(cam.w); float k = cos(cam.w);
  c = float2(c.x * k - c.y * s, c.x * s + c.y * k) / cam.z;
  float2 p = 0.5 * PLATE + c * pxScale + cam.xy;

  // 2. Shockwave: đẩy điểm lấy mẫu quanh vòng sóng
  float2 d = p - shock.xy;
  float r = length(d);
  float x = (r - shock.z) / 40.0;
  p -= d / max(r, 1.0) * exp(-x * x) * shock.w * 30.0;

  half4 col = video.eval(clamp(p, float2(0.5), PLATE - 0.5));
  float m = tile(MATTE, p);

  // 3. Aura sau lưng Goku: halo từ matte bị noise kéo lên trên, cộng "quả trứng" quanh ngực,
  //    tô 3 dải màu cứng kiểu anime
  if (aura > 0.001) {
    float2 flow = float2(0.0, t * 1.6);
    float n = fbm(p / 90.0 + flow);
    float2 q = p + (float2(fbm(p / 60.0 + flow + 7.0), n) - 0.5) * float2(70.0, 160.0);
    float halo = 0.0;
    for (int i = 0; i < 8; i++) {
      float ang = float(i) * 0.785398;
      halo += tile(MATTE, q + float2(cos(ang), sin(ang) * 1.4 + 0.6) * 44.0);
    }
    float2 e = (p - chest) / float2(260.0, 430.0);
    float egg = smoothstep(1.0, 0.6, length(e) + (n - 0.5) * 0.6);
    float a = max(halo / 8.0, egg * 0.8) * aura * (1.0 - m);
    float band = a > 0.75 ? 1.0 : (a > 0.45 ? 0.66 : (a > 0.2 ? 0.33 : 0.0));
    col.rgb = mix(col.rgb, mix(half3(1.0, 0.62, 0.11), half3(1.0, 0.96, 0.78), band), band * 0.85);
    // rim vàng ở mép trên người Goku
    col.rgb += half3(1.0, 0.82, 0.3) * m * (1.0 - tile(MATTE, p - float2(0.0, 8.0))) * aura;
  }

  // 4. Glow từ lớp energy (ki, mắt) render trong Blender
  col.rgb += half3(1.0, 0.9, 0.6) * tile(ENERGY, p) * 0.5;

  // 5. Chỉnh màu theo shot
  float l = dot(col.rgb, half3(0.299, 0.587, 0.114));
  half3 cold = mix(half3(l), col.rgb, 0.7) * half3(0.92, 1.0, 1.05);
  col.rgb = mix(cold, col.rgb * half3(1.08, 1.02, 0.9), grade);

  // 6. Impact frame: chỗ tối thành trắng, chỗ sáng thành đen
  if (impact > 0.5) { col.rgb = half3(step(l, 0.45)); }

  // 7. Grain nhẹ chống banding
  col.rgb += (hash(xy + fract(t) * 91.7) - 0.5) * 0.008;
  return col;
}`)!;
```

Sẽ thêm vào cùng shader này: beam và ki blast vẽ bằng SDF đoạn thẳng hoặc hình tròn (tối đa 4 cái, truyền qua uniform), nên khi bay sau lưng Goku sẽ bị che đúng chỗ nhờ matte; heat haze (lệch toạ độ bằng noise quanh halo); god rays (lấy mẫu tile energy dọc hướng về tâm ngực).

### 6.5 Đồng hồ, timeline, camera ảo, haptic (phác thảo)

```tsx
// src/cinematic/timeline.ts
import data from "../../assets/cinematic/timeline.json";

export const FPS = data.fps;
export const TR = data.tracks as Record<string, number[]>;
export const AN = data.anchors as Record<string, number[]>;
export const HAPTICS = data.markers
  .filter((m) => m.name.startsWith("haptic:"))
  .map((m) => ({ t: m.f / FPS, style: m.name.slice(7) }));

// Nội suy tuyến tính một track theo thời gian (giây)
export const track = (arr: number[], t: number) => {
  "worklet";
  const f = Math.min(Math.max(t * FPS, 0), arr.length - 1);
  const i = Math.floor(f);
  const j = Math.min(i + 1, arr.length - 1);
  return arr[i] + (arr[j] - arr[i]) * (f - i);
};

// Anchor theo đúng frame video đang hiển thị, để FX dính chặt nhân vật
export const anchor = (arr: number[], frame: number): [number, number] => {
  "worklet";
  const i = Math.min(Math.max(frame, 0), arr.length / 3 - 1) * 3;
  return [arr[i], arr[i + 1]];
};

// Value noise 1D trong khoảng -1..1, dùng cho rung màn hình
export const n1 = (x: number) => {
  "worklet";
  const i = Math.floor(x);
  const u = (x - i) * (x - i) * (3 - 2 * (x - i));
  const h = (k: number) => {
    const s = Math.sin(k * 127.1) * 43758.5453;
    return s - Math.floor(s);
  };
  return (h(i) + (h(i + 1) - h(i)) * u) * 2 - 1;
};
```

```tsx
// src/cinematic/haptics.ts
import * as Haptics from "expo-haptics";

const IMPACT: Record<string, Haptics.ImpactFeedbackStyle> = {
  light: Haptics.ImpactFeedbackStyle.Light,
  medium: Haptics.ImpactFeedbackStyle.Medium,
  heavy: Haptics.ImpactFeedbackStyle.Heavy,
  rigid: Haptics.ImpactFeedbackStyle.Rigid,
  soft: Haptics.ImpactFeedbackStyle.Soft,
};

export const fireHaptic = (style: string) =>
  style === "success"
    ? Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
    : Haptics.impactAsync(IMPACT[style] ?? Haptics.ImpactFeedbackStyle.Medium);
```

```tsx
// src/screens/CinematicScreen.tsx (trích)
const { frame, videoTime, player } = useCinematicVideo(uri);
const { size, onLayout } = useCanvasSize();
const t = useSharedValue(0);
const lastT = useSharedValue(0);
const playing = useSharedValue(false);

useFrameCallback(({ timeSincePreviousFrame }) => {
  "worklet";
  if (!playing.value) return;
  const next = t.value + (timeSincePreviousFrame ?? 0) / 1000;
  const err = videoTime.value - next;
  // Lệch quá 2 frame (seek, giật) thì nhảy thẳng; còn lại kéo nhẹ về video cho mượt
  t.value = Math.abs(err) > 2 / FPS ? videoTime.value : next + err * 0.1;
  for (const h of HAPTICS) {
    if (lastT.value < h.t && t.value >= h.t) scheduleOnRN(fireHaptic, h.style);
  }
  lastT.value = t.value;
});

const uniforms = useDerivedValue(() => {
  const ft = track(TR.fxclock, t.value);
  const trauma = track(TR.shake, t.value) ** 2; // rung theo trauma² cho cảm giác tự nhiên
  const [cx, cy] = anchor(AN.goku_chest, Math.round(videoTime.value * FPS));
  return {
    view: [size.width, size.height],
    pxScale: Math.min(1080 / size.width, 2340 / size.height),
    // tổng biên độ rung + xoay phải nằm trong lề overscan (36/78 px)
    cam: [
      trauma * 24 * n1(ft * 23),
      trauma * 24 * n1(ft * 23 + 7.3),
      1 + track(TR.punch, t.value),
      trauma * 0.01 * n1(ft * 17 + 3.1),
    ],
    t: ft,
    chest: [cx, cy],
    aura: track(TR.aura, t.value),
    grade: track(TR.grade, t.value),
    impact: track(TR.impact, t.value),
    shock: [cx, cy, track(TR.shock_r, t.value), track(TR.shock_k, t.value)],
  };
});

return (
  <Canvas style={StyleSheet.absoluteFill} onLayout={onLayout}>
    <Fill>
      <Shader source={composite} uniforms={uniforms}>
        <ImageShader image={frame} />
      </Shader>
    </Fill>
    {/* Lightning, Sparks, SpeedLines, Flash, TitleCard… */}
  </Canvas>
);
```

### 6.6 Các lớp FX còn lại

- Sét: `usePathValue` sinh tia bằng midpoint displacement, đổi seed mỗi khoảng 70ms. Vẽ 2 lớp: nét dày có `BlurMask` làm glow và lõi trắng mảnh.
- Tia lửa, mảnh vụn: `Atlas` + `useRSXformBuffer`, tối đa khoảng 300 sprite (Graphite vẽ atlas từng sprite một, vài trăm vẫn ổn). Vị trí tính thẳng từ seed và `fxclock` nên không cần lưu state; qua marker `cut` thì đổi seed. Bụi mịn số lượng lớn vẽ trong shader.
- Speed lines: SkSL theo góc (`atan2`) cộng noise, che theo bán kính; tâm là anchor cú đấm hoặc giữa màn.
- Vụ nổ: SkSL quả cầu noise tô 3 dải cel kèm vòng khói, đặt theo anchor; Blender có light flash cùng frame.
- Flash, vignette, letterbox: `Fill` với blend mode; letterbox là 2 `Rect` trượt vào.
- Title: font đậm (Bangers hoặc Anton, Google Fonts, giấy phép OFL), tô `LinearGradient` vàng kim, vệt sáng quét ngang, scale bằng `withSpring`, dòng phụ "スーパーサイヤ人".
- Dev scrubber (chỉ bản dev): kéo để tua `currentTime`, hiện số frame và tên shot, bật tắt từng lớp FX. Đây là công cụ chính để chỉnh timing.

### 6.7 Màn "giữ để gồng Ki"

- Hiện frame đầu (player đang pause, gán `currentTime = 0` là có frame), làm tối đi, kèm chữ "Giữ để gồng Ki".
- Khi giữ tay: thanh Ki (Skia, gradient vàng) đầy trong khoảng 1.5 giây, màn hình rung và haptic dày dần. Thả tay sớm thì thanh tụt về.
- Trong lúc đó chuẩn bị sẵn: player đã tạo và đang pause; mọi shader đã vẽ thử một lần ở cường độ 0 để Graphite biên dịch pipeline trước (tránh giật ở frame đầu); font và texture đã load.
- Thanh đầy → flash trắng → `player.play()` → chạy cinematic. Hết 20 giây thì hiện title và nút "Xem lại" (`currentTime = 0`).

### 6.8 Hiệu năng

- Mục tiêu: lớp FX chạy 120fps trên iPhone Pro (13 Pro trở lên), 60fps ổn định từ iPhone 12; video 60fps.
- Ngân sách GPU khoảng 6ms mỗi frame ở 120Hz: 1 pass composite (khoảng 10 lần lấy mẫu), aura fbm 4 octave, tối đa 300 sprite, 1 lớp blur nhỏ.
- Khi đang chạy không `setState`, không re-render React; mọi giá trị đi qua shared value.
- Hai mức chất lượng `full` và `lite` (giảm octave noise, số hạt, tắt god rays), giống pattern `fx-budget` trong Pastel Studio.
- Đo bằng Xcode Instruments (Animation Hitches, Metal System Trace) và GPU frame capture; log những frame có `timeSincePreviousFrame` lớn hơn 9ms.
- Bộ nhớ: một texture 1728×2496 BGRA khoảng 17 MB, tạo một lần rồi dùng lại.

---

## 7. Lộ trình

| Giai đoạn | Việc | Kết quả | Ước lượng |
|---|---|---|---|
| P0 Kịch bản | Storyboard 10 khung bằng Codex; animatic trong Blender VSE với nhạc tạm; khoá timing 20 giây | `animatic.mp4`, shot list chốt | 1–2 ngày |
| P1 Spike (quan trọng nhất) | Blender render scene giả (khối capsule + camera) ra 3 pass và `timeline.json` → pack → app: video qua WebGPU vào Skia, tách tile, aura quanh matte, 120Hz, haptic theo marker, có tiếng | Pipeline chạy từ đầu tới cuối trên iPhone thật | 2 ngày |
| P2 Asset và look | Goku (thường + SSJ), Frieza, Namek; toon material, outline, rig | Render xoay 360° hai nhân vật | 4–6 ngày |
| P3 Animation và camera | Blocking theo animatic → spline → polish; 10 camera + marker; keyframe FX | Bản preview đủ 20 giây | 6–10 ngày |
| P4 Pipeline render | `render_passes.py`, `bake_timeline.py`, `pack.sh`, `preview.sh` | Một lệnh: render → pack → copy vào app | 1–2 ngày, làm song song P2 |
| P5 FX và UI | Đủ các lớp Skia, màu theo shot, intro gồng Ki, title, haptic, dev scrubber | Bản hoàn chỉnh | 4–6 ngày |
| P6 Polish trên máy | Đo Instruments, mức `lite`, căn sync, mix âm | Bản final | 2 ngày |

Spike P1 đạt khi:

- Video pack 1728×2496 HEVC Main10 chạy trên iPhone thật, shader đọc đúng tile matte, không lem.
- Lớp FX chạy 120Hz không hitch (theo Instruments) trong khi video 60fps.
- Có tiếng, tức `createVideoPlayer` phát được audio. Nếu không thì chuyển sang `expo-audio` và căn hình theo tiếng.
- FX lệch video không quá 1 frame: burn-in số frame trong Blender, Skia vẽ số frame nó tính ra, quay màn hình rồi so.
- Đã thử vòng lấy frame trong worklet.

Bản 1 xong khi: chạy đủ 20 giây; mở app tới màn intro dưới 1.5 giây; 3 lần chạy liên tiếp trên iPhone Pro không hitch; app dưới 60 MB; "Xem lại" chạy đúng; tiếng và haptic đúng nhịp.

Phần làm được hoàn toàn bằng code: toàn bộ code app; các script Blender (dựng scene, toon material, view layer, render, bake, pack); dựng Namek procedural, đặt camera và marker qua Blender MCP; storyboard và concept bằng Codex. Phần cần bạn: chọn và duyệt model, polish animation (block pose thô bằng script được nhưng chỉnh tay vẫn đẹp hơn), duyệt âm thanh, test trên iPhone thật.

---

## 8. Rủi ro

| Rủi ro | Mức | Cách giảm |
|---|---|---|
| Animation 20 giây tốn hơn dự kiến | Cao | Mixamo làm nền; cắt cảnh nhanh, motion blur và FX che bớt; nếu trễ thì rút shot 8 còn 2 giây |
| Model Goku/Frieza không đạt (license, chất lượng) | Trung bình | 3 nguồn theo thứ tự ở mục 5.2; tóc luôn tự làm |
| Skia v3 mới ra (10/2026), gặp bug | Trung bình | Lùi về `react-native-skia@2`, bản này còn `useVideo`; shader và các lớp FX giữ nguyên, chỉ đổi phần lấy frame |
| `createVideoPlayer` không phát tiếng, hoặc frame ra không đều | Trung bình | Kiểm ở spike P1; dự phòng `expo-audio` và căn hình theo tiếng; lấy frame trong worklet |
| Giật frame đầu do biên dịch pipeline | Thấp | Warm-up ở màn intro |
| Màu trong Blender khác màu trên iPhone | Thấp | View Transform Standard, gắn tag BT.709, ép ma trận bt709 khi encode, so trên máy thật |
| Matte bị nén lem | Thấp | Tile luma, CRF 16–18, kích thước bội số 16, kẹp toạ độ |
| Video nặng | Thấp | Chỉnh CRF, hoặc tải video ở lần mở đầu tiên |

---

## 9. Bản 2 (tuỳ chọn): 3D real-time, có tương tác

- Skia v3 và `react-native-webgpu` dùng chung GPU device. three.js (`three/webgpu`, r186) render offscreen vào texture, `Skia.Image.MakeFromGPUTexture` bọc lại, rồi đi qua đúng shader composite và các lớp FX của bản 1. Matte lấy từ render target thứ hai (MRT); anchor tính bằng `Vector3.project(camera)` thay vì đọc JSON.
- Asset: export GLB từ cùng file Blender (nén Draco hoặc meshopt, texture KTX2), giữ nguyên animation và shape key. Toon dùng `MeshToonNodeMaterial` với gradient 3 nấc, outline inverted hull.
- Được: tương tác (vuốt xoay camera lúc freeze, chạm để né), app nhẹ, nét ở mọi độ phân giải, 3D thật ở 120Hz.
- Mất: motion blur và DOF chất lượng offline; tốn thêm khoảng 2–3 tuần; muốn giữ 120Hz thì phải chạy three.js trên worklet runtime (Bundle Mode của react-native-worklets, còn thử nghiệm).
- `react-native-filament` (1.11) cũng load được GLB bằng renderer native, nhưng không chung device với Skia nên không áp shader lên hình 3D được.

---

## 10. Quyết định cần chốt

Plan đang viết theo lựa chọn in đậm.

1. Khung hình: **dọc 9:19.5**, hoặc ngang.
2. Phong cách: **anime cel-shading kiểu FighterZ**, hoặc 3D bán thực kiểu Sparking! Zero.
3. Nguồn model: **Sketchfab trước, rồi `generate_3d`, cuối cùng tự dựng**.
4. Màn "giữ để gồng Ki" trước cinematic: **có**, hoặc vào thẳng.
5. Nhịp chuyển động nhân vật: **mượt 60fps**, hoặc giữ pose 2 frame kiểu anime ở vài cảnh.

---

## 11. Bản quyền

Goku và Frieza thuộc bản quyền của Bird Studio, Shueisha và Toei Animation. Làm demo cá nhân hay portfolio thì được, nhưng đừng phát hành lên App Store (Apple sẽ từ chối theo Guideline 5.2 về sở hữu trí tuệ) và đừng dùng nhạc hay giọng gốc. Model tải về phải đọc license: nhiều model fan-made là CC BY-NC hoặc cấm phân phối lại. Muốn phát hành thì thay bằng nhân vật tự thiết kế; pipeline giữ nguyên.

---

## 12. Tham khảo

- React Native Skia v3, chuyển từ v2: https://wcandillon.github.io/react-native-skia/docs/getting-started/migration
- React Native Skia và WebGPU (video, three.js, chia sẻ texture): https://wcandillon.github.io/react-native-skia/docs/webgpu
- React Native WebGPU, Video Player API: https://wcandillon.github.io/react-native-webgpu/api/video-player
- React Native WebGPU, chạy trên worklet: https://wcandillon.github.io/react-native-webgpu/docs/integrations/worklets
- Reanimated, hiệu năng và 120fps: https://docs.swmansion.com/react-native-reanimated/docs/guides/performance
- Blender 5.2 LTS: https://www.blender.org/download/
- GDC 2015, "GuiltyGear Xrd's Art Style: The X Factor Between 2D and 3D" (Junya C. Motomura, Arc System Works)
- GDC 2016, "Math for Game Programmers: Juicing Your Cameras With Math" (Squirrel Eiserloh): rung màn hình theo trauma²
