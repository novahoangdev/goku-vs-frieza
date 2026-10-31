# v15: mặt Frieza sắc hơn, bàn tay có ngón, chân chibi ngắn (+ Goku và hiệu ứng app, 3 agent song song)

Frieza (`build_frieza`, `face_textures.py`, `extras/frieza_details.py`)
- Mắt hạnh nhân: mí trên dày sẫm xếch xuống phía sống mũi, hất lên ở đuôi; tròng đỏ bị mí che nửa, đồng tử dọc hẹp;
  gờ chân mày mờ (Frieza không có lông mày). Nhìn tự tin, nham hiểm thay vì lờ đờ như v1–v14.
- Vạch tím dưới mắt đúng nguyên tác (decal riêng, giữ nguyên khi đổi biểu cảm); môi tím sẫm nhếch một bên lúc
  đứng yên; miệng há / cười lớn có viền môi tím dày. Mắt hoảng hốt vẽ lại mở to tròng nhỏ, chớp mắt thành cong tự mãn.
- Bàn tay có 3 ngón + ngón cái (trước là cục tròn): tay thả lỏng / co hờ, tay xoè lúc hoảng sau biến hình và lúc mất
  dấu Goku rồi bị đánh; ngón trỏ co lại khi ngón bắn Death Beam duỗi ra.
- Chân ngắn lại kiểu chibi (đùi 0.26 → 0.21), thân, đầu và các anchor giữ nguyên chỗ nên hiệu ứng app không lệch.

Goku (`build_goku`, `choreograph`)
- Sửa lỗi có từ các bản đầu: Goku tóc đen không có miệng suốt đoạn mở đầu (frame 0–292, cả cảnh cận mặt lúc gồng)
  vì key ẩn/hiện đầu tiên của miệng là "ẩn" ở frame 292. Đã quét mọi object khác, không còn chỗ nào bị như vậy.
- Bàn tay thành nắm đấm chibi thật (trước là quả bóng tròn): bốn ngón cuộn có gờ đốt tay ở mu, nét mực giữa các
  ngón ở lòng, ngón cái dày ốp ngang ngón trỏ + giữa; cú đấm là nắm đấm dọc.
- Tóc đen thêm 3 gai phía trước đỉnh đầu nên nhìn từ dưới lên vẫn thấy hàng gai (trước như cái mũ trơn có hai gai);
  nét mực dọc chân tóc cho cả hai dạng (rõ nhất ở tóc vàng).

App (`composite.ts`, `useFxUniforms.ts`)
- Tia lửa va chạm kiểu anime ở 3 cú đấm trúng (frame 719, 747, 1030): sao 9 cánh nhọn bật ra trong 2 frame rồi co
  lại, 4 dải màu cứng (viền mực → cam → vàng → lõi trắng), vòng trắng mảnh nở ra, vệt trắng bắn tung; đứng yên ở
  chỗ nắm đấm chạm chứ không chạy theo tay. Ở impact frame đen trắng thì thành bóng sao đen.
- Aura: lưỡi lửa liếm lên thành từng ngọn nhọn tách rời (trước là viền cam mềm), viền ngoài đỏ cam mảnh, lõi sáng hơn.
- Vụ nổ: khói cel 3 tông có viền mực và đường than hồng chỗ giáp lửa, bị gặm lỗ rồi tan dần; 16 mảnh đá văng xoay ra.
- Bản quay demo tắt tiếng trong simulator.
