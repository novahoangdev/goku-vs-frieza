# v25: vật lý cho hiệu ứng (nước, đá văng, khe nứt nguội) + tiếng nước

## Kamehameha trên mặt biển
- Goku và Frieza hạ xuống lướt sát mặt biển (chân Goku cách nước 1.3 m, trước là ~6.5 m: mọi phản ứng của nước đều nằm
  ngoài khung hình). Đoạn chèn bắt đầu và kết thúc bằng cut nên không lệch với shot trước/sau.
- Shot A hạ máy nhìn chếch xuống để thấy mặt nước dưới chân.
- Tụ khí: áp lực khí đẩy nước thành các vòng sóng loang dồn dập dần (vòng càng rộng khi khí càng mạnh); bọt nước bị
  hất lên rơi theo đường đạn thật (g = 9.8 m/s² ở 60 fps), giọt kéo dài theo vận tốc.
- Vòng sóng gợn méo, bản bọt dày mỏng không đều (không tròn như vẽ compa).
- "HA!": phản lực đẩy một vòng sóng lớn loang nhanh dưới chân. Goku bị đẩy lùi suốt lúc tia còn bắn (0.47 m, trước
  0.22 m rồi đứng yên), gốc tia bám theo hai bàn tay từng frame (trước gốc tia đứng yên giữa không trung, lệch khỏi tay).
- Ánh tia phản chiếu trên mặt nước: dải sáng thuôn chạy theo đầu tia; vụ nổ rọi xuống thành vũng sáng tròn trên mặt
  biển, to theo khối nổ rồi tắt.
- Tia chạy trên mặt nước: hai vách bọt răng cưa dạt ra hai bên dưới đường tia, chạy theo đầu tia (trễ 3 frame), sụp khi tia tắt.
- Trúng Frieza: sóng xung kích chạm mặt nước sau ~3 frame → vương miện nước (vách thấp loe + tia nước nhọn toả ra
  ngoài) phun cao rồi sụp dần; sóng tròn lớn loang ra xa 15 m.
- Tiếng: bọt nước lách tách + sóng vỗ trầm dày dần theo lúc tụ khí, xé nước lúc bắn, ầm nước đổ khi nổ, mưa giọt rơi lộp độp sau đó.

## Biến hình
- Đá vụn: khí nhấc lơ lửng như cũ, vụ nổ biến hình hất văng theo đường đạn, chạm đất nảy (hồi phục 0.35, ma sát cỏ
  hãm trượt và xoay) rồi nằm yên trên cỏ; lần chạm đất đầu bung một cụm bụi đất (to theo cỡ đá và tốc độ rơi). Trước: key tay, đá cắm xuống dưới mặt đất. Giữ đúng số lần gọi `random`
  để các vật ngẫu nhiên khác không đổi.
- Khe nứt: rực vàng lúc gồng, loé trắng lúc nổ biến hình, nguội dần thành cam rồi thành khe tối ánh than hồng
  (trước: sáng vàng mãi đến hết phim). Lớp energy cho glow cũng tắt theo.

## Frieza
- Cổ thon phía trên và dẹt trước-sau, cằm nhô ra trước cổ: trước đó mặt trước cổ nhô hơn cằm (0.079 so với 0.048) nên
  đầu liền cổ như con ki bowling, không thấy đường hàm; giờ có viền cằm tròn rõ.

Render lại cả phim (Frieza có mặt hầu hết các shot).

## Chi tiết khác
- Mặt Goku SSJ không còn bị phủ mảng mờ trắng: lỗi cũ trong `tex_mat` (so node bằng `is not`, mà wrapper Python của
  node bpy tạo mới mỗi lần truy cập → luôn đúng) làm lớp energy của miếng dán mắt không theo alpha, cả miếng chữ nhật
  sáng lên và app bloom thành mảng trắng che nửa mặt, mắt nhạt màu. Giờ so theo tên; thêm nữa chỉ mống mắt (phần màu
  xanh) phát sáng, tròng trắng + mi đen không vào lớp energy.
- Hạt khí aura (app) toả quanh người, không còn lấm tấm như tuyết trên mặt/thân Goku.
- Vệt bay truy đuổi: lõi nón mảnh hơn + 7 vệt khí dài ngắn toả quanh (trước một khối nón trơn như cái phễu tím/vàng).
- Khe nứt nguội về màu nâu sẫm gần mép → một khe tối mảnh, không thành vạch nâu tô đậm.
