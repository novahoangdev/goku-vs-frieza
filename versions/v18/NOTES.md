# v18: chăm chút nhân vật (nét viền, tóc SSJ nhìn từ sau, mắt + biểu cảm)

Nét viền nhân vật (`char_outlines.py`, gọi sau `char_shading`)
- Độ dày theo khoảng cách camera và tiêu cự: cận cảnh không còn dải đen dày (rõ ở cảnh qua vai thấy vòm đầu Frieza
  frame 560), cảnh rộng không mất nét.
- Bộ phận lớn (đầu, tóc, thân, chân) nét dày hơn, chi tiết nhỏ (viền, nút, dây) nét mảnh; mặt quay vào trong thân
  (đùi trong, tay trong, đai trên áo) nét mảnh hơn viền ngoài bóng dáng.
- Nét vuốt nhọn ở chỗ mỏng: đầu lọn tóc SSJ thành mũi nhọn thay vì cục nét tù, ngón tay, tai, đầu dây thừng mảnh lại.
- Màu nét: viền tay áo / cổ tay Goku dùng nét xanh navy, viền vai và ngọc ngực Frieza dùng nét tím sẫm.

Tóc SSJ nhìn từ sau và bên hông (`goku_hair_forms`, `goku_blade`, `char_shading`)
- Gáy dựng lại thành các hàng lọn so le (hàng đỉnh vuốt ra sau, hàng giữa, hàng dưới ôm sọ rồi hất lên, 3 lọn gáy
  chĩa xuống hất mũi ra ngoài), dài ngắn và góc lệch nhẹ; v16–v17 mọi lọn toả từ một điểm nên nhìn từ sau như bông
  sen vàng nhạt phẳng (lộ rõ ở các shot qua vai frame 560, 700, 870, 1060).
- Tông bóng cam hổ phách ở gốc mỗi lọn và chỗ lọn chồng lên nhau → có chiều sâu từng lớp như mẫu FighterZ; đốm bóng
  trắng to giữa gáy (tâm "bông sen") giảm đi.
- Nhìn ngang: hai lọn đỉnh xoắn nhẹ nên vẫn thấy bản rộng, bóng dáng vẫn là ngọn lửa.

Mắt + biểu cảm (`face_textures.py`, decal + key trong `build_scene.py`)
- Tròng mắt anime chung cho cả hai: trên sẫm chuyển sáng dần xuống dưới, vân toả, vầng sáng quanh đồng tử, bóng mí
  đổ trên tròng, một điểm sáng chính sắc + điểm phụ + chấm nhỏ. Mí trên Goku có độ đậm nhạt (mảnh đầu trong, dày
  đuôi, hất nhẹ), nếp mí và mí dưới mảnh. SSJ hẹp và gắt kiểu FighterZ (mí che đỉnh tròng, mí dưới nâng, đồng tử nhỏ).
- Goku: lông mày giận lúc gồng (236–300), miệng thét vẽ lại có răng trên + lưỡi + lòng miệng đỏ sẫm, nghiến răng và
  hét trong đoạn combo (705–780) và cú đấm cuối (1012–1048) với mắt SSJ hẹp gắt, nhếch mép tự tin ở cuối (1118–hết).
  Má hồng chỉ còn ở dạng thường lúc bình thản.
- Frieza: nhắm mắt tự mãn khi "ho ho ho" (501–521), giật mình khi Goku biến hình (521–532), mắt giận gắt + gờ mày
  nặng + nếp trán + nhe răng gầm gừ (532–700), há hốc khi mất dấu Goku (1000–1030), trúng đòn nhắm tịt mắt có giọt
  nước mắt + miệng méo đau (1030–). Sửa: frame 1150 trước đó mọi mặt của Frieza hiện chồng lên nhau.
