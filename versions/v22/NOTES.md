# v22: tay chân liền mạch (hết khớp ma-nơ-canh)

`skin_limb` (build_scene.py): mỗi tay/chân là MỘT khối liền từ vai/hông qua khuỷu/gối tới cổ tay/cổ chân, thay cho
2 khúc cứng gắn vào 2 khớp. Phần trên đi theo khớp trên (vật là con của khớp vai/hông), phần dưới bẻ theo khớp
khuỷu/gối qua modifier Hook có trọng số chuyển mượt ±4–4.5 cm quanh khớp (skinning kiểu linear blend, giữ nguyên
vũ đạo vì Hook bám đúng các Empty khớp đang có key xoay).

- Goku: cả cánh tay da liền (bắp tay trước + tam đầu + cơ cẳng tay giữ như v19). Trước khi gập khuỷu (thủ thế, đấm)
  2 khúc cắm vào nhau thành một nếp gãy + mép hở ở góc khuỷu; giờ khuỷu cong tròn liền như tay thật.
- Frieza: tay trắng liền từ dưới giáp vai tới cổ tay, chạy dưới giáp cẳng tay tím (trước bắp tay mảnh cắm thẳng vào
  ống giáp như 2 ống ghép). Chân trắng liền từ hông qua gối tới cổ chân, bỏ quả cầu gối rời; giáp ống chân tím giữ
  nguyên bọc ngoài → đùi chảy mượt vào ống chân khi co gối (bay, né, trúng đòn).
- Kiểm tra: gập thử khuỷu 110° / gối 75° so với bản cũ cùng góc máy; quét các shot hành động 250–1150 không lỗi,
  không vật nào bị ẩn sai (vischeck).

Nhịp phim chậm lại: 20 s → 28.7 s (`retime.py`, chạy cuối build_scene)
- Phim cũ 14 shot trong 20 s (~1.4 s/shot) nên cảm giác cụt ngủn. Ánh xạ frame cũ → mới tuyến tính từng đoạn theo
  shot, áp lên mọi keyframe (vật, material, node, camera, FX) và marker: mở màn ×1.6, gồng ×1.4, đôi mắt ×1.3,
  bùng nổ ×1.6, Super Saiyan ×1.5, Frieza ×1.4, né ×1.25, combo ×1.2 (giữ dồn dập), rượt đuổi ×1.25,
  phản đòn ×1.3, cú đấm ×1.5 (slow-mo), cảnh kết ×2.0 (đọng lại với title).
- Bản đồ ghi vào timeline.json ("retime"); app (mốc tia lửa trúng đòn, tâm speedline, tint, bụi), promo clip
  (camera máy, chữ lớn, nền, end card "29s"), capture (khung still, poster), compare, fx-preview, audio đều quy đổi
  theo đó (`tools/rt.py`). Đồng hồ FX trong app vẫn chạy thời gian thật nên lửa/khói không bị chậm theo.

Âm thanh mới (`synth_audio.py` viết lại) — nhạc phim kiểu anime, khớp từng nhịp hình
- Nhạc cụ tổng hợp: kèn đồng (cộng hưởng, sáng dần khi tấn công), dàn dây (siêu răng cưa, tremolo), đồng ca
  formant "aah/ooh", timpani + cuộn, taiko, trống dàn (kick/snare/hi-hat/crash), bass, power chord; vang hội trường.
- Bố cục: bão mở màn Rê thứ (dây trầm + đồng ca) → gồng (dây tremolo dâng Dm–Bb–C–A, timpani cuộn, riser) →
  3 nhịp chớp SSJ (đánh dàn + đảo cymbal) → lặng 0.12 s → BÙNG NỔ (hợp âm kèn Rê trưởng + đồng ca + crash) →
  chủ đề anh hùng (kèn) → Frieza (dây trầm Si giáng thứ, kèn tritone, pizzicato) → chiến đấu 150 BPM →
  phản đòn (rút trống, dây cao rung + riser, nín thở 0.3 s) → CÚ ĐẤM (stinger cả dàn, vang dài) → kèn chủ đề nhắc lại
  + hợp âm Rê trưởng cuối + chuông title.
- Tiếng động: sấm theo từng tia chớp, đất rung khi gồng, tia điện lúc chớp SSJ, lửa khí aura theo track, Death Beam
  (tụ khí + rít chói, pan trái/phải), "shun" dịch chuyển khi né, đấm nhiều lớp (vút + thịch + nứt), gió lùa khi bay
  theo speedlines, ki blast + nổ có mảnh vỡ, 3 cú đấm cuối, cột nước, chuông title.
- Trộn: nhạc chuẩn theo RMS + tự hạ (duck) khi có tiếng động lớn; tiếng động nén mềm để cú đấm / tia / dịch chuyển
  không bị cú nổ biến hình lấn át. Mở màn ~-30 dB → nổ biến hình ~-12 dB → chiến đấu ~-16..-19 dB.
- Nhạc riêng (tuỳ chọn): đặt `render/audio/bgm.mp3|m4a|wav|…` → build tự đổi sang bgm.wav và dùng thay phần nhạc
  tổng hợp (tiếng động vẫn giữ, nhạc tự hạ dưới tiếng động).

## Sửa crash khi phim dài hơn
- Bản quay đầu tiên của v22 bị văng app ở giây ~20 của phim: Hermes trên UI thread hết bộ nhớ (`HadesGC::oom`).
  Nguyên nhân: `useCinematicVideo` tạo một `SkImage` mới cho mỗi frame video rồi gán qua shared value từ JS,
  UI runtime giữ các ảnh cũ chờ GC bên JS. Phim 20 s vừa đủ chịu, phim 29 s thì tràn.
- Sửa: `SkImage` bọc thẳng texture GPU (đọc nội dung lúc vẽ), nên chỉ tạo một lần cho mỗi texture; mỗi frame
  chỉ cập nhật `videoTime` để Canvas vẽ lại.
