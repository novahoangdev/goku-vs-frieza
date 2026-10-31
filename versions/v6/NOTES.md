# v6: va chạm kiểu anime

Hiệu ứng
- Ngôi sao va chạm 2 lớp (cam ngoài, trắng trong) bật ra rồi tắt trong 7 frame ở mỗi đòn chạm: cú đấm của Frieza
  vào thế đỡ (719), cú phản đòn của Goku (747), và to gấp rưỡi ở đòn kết liễu (1030). Luôn quay mặt về camera,
  có lớp energy nên app thêm quầng sáng; không tính vào matte của Goku.
- Vệt khí kéo sau lưng khi bay truy đuổi: vàng sau Goku, hồng tím sau Frieza, mờ dần về phía đuôi, chập chờn nhẹ;
  lớp energy theo độ trong suốt nên app thêm quầng sáng đúng hình vệt.

Cảnh
- Bầu trời vẽ tay trôi chậm sang ngang trong suốt 20 giây (mây không còn đứng yên).

Model
- Nét viền màu (colored lineart): viền mỗi phần là tông tối của chính nó (da nâu đỏ, võ phục nâu cam, tóc SSJ vàng
  đồng, Frieza tím than...) thay vì một màu nâu đen chung, nhìn mềm và tinh hơn.

App
- Hạt khí vàng bay lên quanh Goku SSJ (2 lớp hạt vệt dọc với quầng cam, chỉ trong vùng aura, tắt khi Goku bị che
  hoặc ra khỏi khung, mỏng đi ở cận cảnh).
