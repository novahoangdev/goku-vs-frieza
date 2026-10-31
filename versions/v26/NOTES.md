# v26: chi tiết nhỏ (làm đêm)

- Frieza có mũi: hai lỗ mũi nhỏ xếch tím sẫm + bóng mềm dưới sống mũi (decal `frieza_nose`), trước mặt trơn như mặt nạ.
- Chuyển động thứ cấp có quán tính (`secondary.py`, chạy cuối build sau retime + Kamehameha): lò xo – giảm chấn
  (tần số riêng ~0.5 s, tắt sau ~2 nhịp) theo gia tốc của đầu/hông trong hệ toạ độ của chính nó.
  - Đuôi Frieza: tăng tốc lên → đuôi trễ xuống, rẽ ngang → đuôi văng ngược phía; chóp quất mạnh hơn gốc, sóng lan
    dọc đuôi (trễ 1.5 frame/đốt). Tối đa ±22°.
  - Lực cản: bay càng nhanh đuôi càng bị kéo thẳng ra sau (bỏ tới 80% độ cong chữ S sẵn có khi ~18 m/s, lọc mượt),
    đứng yên thì cong lại như cũ.
  - Tóc Goku (đen + SSJ): lao tới → tóc ngả ra sau, rẽ → tóc lệch ngược phía, rồi đung đưa về. Tối đa ±11°.
  - Cộng vào key sẵn có (rung trong luồng khí, lắc đuôi); reset ở mỗi cut và khi nhân vật dịch chuyển tức thời giữa
    hai shot (> 0.9 m/frame) để không quất giả.
- Cỏ ngả theo gió khí: shape key `ki_wind` trên `grass_tufts` + `env_grass_clumps` uốn mỗi ngọn ra ngoài xuyên tâm từ
  chỗ Goku gồng (cong theo độ cao ngọn, yếu dần theo khoảng cách, tối đa ~66° sát Goku); phập phồng khi tụ khí, rạp
  hẳn lúc nổ biến hình, dịu lại tới khi bay đi.
- Tóc đen: thêm tông sáng thứ 3 xám lam ở mặt đón đèn (`hi` 1.35 → 0.82, trước không bao giờ chạm) + đốm bóng rõ hơn
  → các lọn đen tách khối như tóc đen anime, không thành một mảng đen.
- Tia Kamehameha: thân tia có vệt khí cuồn cuộn trôi từ tay ra phía trước (nhiễu kéo dài dọc tia cộng vào hệ số
  Facing của ramp cel, trôi ~70 m/s), không còn là ống nhựa trơn.
- Tiếng đá rơi: mỗi hòn đá vụn chạm đất (frame lấy từ mô phỏng đường đạn, marker `sfx:thud`) có một tiếng bịch trầm
  + lạo xạo nhỏ, âm sắc/âm lượng/pan khác nhau (~-33 dB dưới nhạc, 46 tiếng trong ~1.5 s sau biến hình).
- Kamehameha shot F (toàn cảnh sau lưng): lùi máy ra sau-phải → Goku trọn lưng ở 1/3 dưới-trái, tia dẫn mắt tới
  khối nổ + vương miện nước (trước Goku bị cắt ở mép trái, chỉ thấy một mảng tóc).
- Hơi nước: năng lượng nổ sát mặt biển làm nước bốc hơi → 9 cụm mây cel xám trắng (gồ ghề bằng noise) phồng lên
  quanh chân khối nổ, toả ra và bay lên chậm dần tới hết đoạn.
- Cầu Kamehameha: vật liệu riêng — lõi trắng nhỏ, các lớp xanh ngọc → lam → lam đậm ra mép (trước gần như trắng
  toàn khối, nhìn như nắm cơm trong tay Goku).
- Kamehameha shot E (tia trúng Frieza): lùi máy cách khối nổ ~5 m thay vì 2.6 m — trước cầu nổ + glow phủ trắng
  cả khung ~0.5 s, giờ thấy trọn khối nổ, vòng sóng, vương miện nước.

## App (shader)
- Sét trời vẽ trong composite thay cho lớp `Lightning` phủ trên cùng: chỉ hiện ở chỗ depth là trời (> ~120 m) nên
  nằm sau cột đá, tóc, người, mặt đất (trước sét vẽ đè qua đầu Goku). Lúc loé cả cảnh sáng lên một thoáng như sét rọi.
- Vụ nổ ki blast: khí nóng nổi lên (quả cầu lửa → khói trôi dần lên trên khi nguội), lửa còn nóng rọi sáng người Goku
  (cam ấm, yếu dần theo khoảng cách và khi lửa tàn).
- Ánh sáng tràn: vật phát sáng không thuộc Goku (cầu khí, tia Kamehameha / Death Beam, vụ nổ dựng trong Blender) rọi
  màu của nó lên người Goku (16 mẫu quanh điểm ảnh, gần sáng hơn xa); tóc SSJ là matte nên không tự rọi chính mình.
- Hạt khí (Sparks): tia lửa vàng bốc dọc hai mép người như lửa aura, không còn rải đều lên mặt/thân (cận cảnh trước
  nhìn như tuyết lấm tấm trên mặt Goku).
- Glow lớp energy sáng theo chính màu vật phát sáng (70%) thay vì cộng màu vàng ấm cố định → mống mắt SSJ vẫn xanh
  ngọc khi loé, không ngả xanh lục nhạt.
