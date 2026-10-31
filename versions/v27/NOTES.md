# v27: chi tiết tiếp (làm đêm)

- Gió giông: cả bãi cỏ ngả theo một hướng và dập dềnh theo từng cơn giật (shape key `storm`, cộng với gió khí
  `ki_wind`), mạnh lúc giông đầu phim, dịu sau biến hình, gần lặng khi đánh nhau trên không.
- Tiếng gió mở màn lên xuống theo đúng cơn giật làm cỏ dập dềnh (cùng công thức với shape key `storm`).
- Sấm theo từng tia sét app vẽ: `synth_audio.py` dựng lại lịch tia sét giống hệt app (mỗi 0.32 s, seed theo cut, cùng
  hàm hash) → ~1/3 số tia có tiếng rền xa vọng lại sau 0.4–1.1 s (sét ở xa), nhỏ hơn tiếng sấm chính (10 tiếng).
- Đuôi đai vải của Goku thành con lắc mềm (`secondary.py: belt_tails`): rủ theo trọng lực thật (Goku nằm ngang bay đi thì
  đuôi đai rủ xuống đất chứ không chĩa ngang như que), bị gió kéo ngược hướng bay, văng tới khi dừng gấp; 2 đuôi lệch
  nhau 1 frame. Gốc xoay dời về điểm buộc ở nút thắt.
- Vòng sóng bọt dưới chân lúc gồng kame hết giống ống trắng vẽ bút dạ: mảnh hơn (0.06 → 0.035), vật liệu mới
  `kame_ripple` vỡ bọt theo nhiễu, và khi vòng loang ra thì ngưỡng nhiễu tăng theo alpha màu object (key 1 → 0) nên
  bọt tan dần thành vụn rồi mất. Sóng phản lực lúc bắn và sóng lớn dưới vụ nổ dùng cùng kiểu tan.
- Giọt nước hất lên nhỏ lại (0.024–0.05 → 0.016–0.034) và kéo dài theo vận tốc ít hơn (×34 → ×26): hết như quả trứng.
- App: không khí nóng rung quanh mọi vật phát sáng dựng trong Blender (cầu khí, tia Kamehameha, vụ nổ) — shader
  composite mục 2c lấy 4 mẫu lớp energy lệch quanh điểm, gần nguồn sáng thì lắc điểm lấy mẫu bằng nhiễu trôi lên
  (khí nóng bốc), không lắc Goku. Trước chỉ có haze quanh aura của Goku.
- Mặt Goku tóc đen hết mảng loang ngang má: đèn key cao nên nửa mặt chibi dưới mắt rơi vào vùng tối (ngưỡng 0.1) + tông
  thứ 3 (mặt úp xuống) → cả nửa dưới mặt sẫm hơn thành mảng. `goku_skin_face`: bỏ tông thứ 3, ngưỡng tối 0.1 → 0.025,
  viền sáng 0.4 → 0.12 (quay từ dưới lên viền sáng phủ cả quai hàm + cổ thành mảng nhạt).
- Nước bị vụ nổ kame hất tung rơi trở lại: 36 giọt lớn văng ra từ thành vương miện nước (cao 1.2–3.6 m) theo đường đạn
  với g thật, kéo dài theo vận tốc, rơi xuống biển (trước vương miện chỉ co lại, nước "biến mất" trên không).
- App: Death Beam sượt qua rọi ánh hồng lên người Goku (má, tóc sát tia), mạnh ở sát tia, tắt dần ra ~120 px.
- Frieza hết đường chấm trắng dọc mép vòm đầu: mặt trong vòm (1.035 r) gần trùng vỏ viền của đầu (r + 0.007) → nhìn từ
  xa z-fight thành đường chấm. Vòm nới ra `FR_DOME_RD = 1.048` (gân giận dán trên vòm theo cùng hằng số).
- Tiếng tõm của từng giọt nước rơi lại xuống biển: `kamehameha.py` đặt marker `sfx:plop` đúng frame giọt chạm mặt biển
  (34 giọt trước khi cắt cảnh), `synth_audio.py` phát tiếng bọt "bloop" ngắn + xèo nhỏ, mỗi giọt một cao độ, panning ngẫu nhiên.
