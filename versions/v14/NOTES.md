# v14: sửa shot hỏng + đá 3D + chỉnh lại đầu Goku và Frieza (3 agent song song)

Cảnh + camera (`build_scene.py`: `cam_for`, `build_env`; `extras/env_details.py`)
- Shot zoom-out ngay sau biến hình (frame 300–390): v1–v13 camera chui xuống dưới mặt đất, nên nửa khung là mặt
  dưới tấm đất màu xanh đục, Goku chỉ lộ đế giày, còn hạt ki vàng thì lơ lửng giữa không trung. Giờ camera ở thấp
  ngang gối (góc hùng tráng), thấy rõ đường chân trời, cột đá, Goku SSJ trọn người đứng trên khe nứt.
- Cận mặt Goku hét lúc gồng (frame 240–300): trước đẩy sát tới mức cả màn hình là mảng da phẳng với cái miệng ở
  dưới; giờ dừng ở khoảng thấy rõ mắt nhắm chặt + miệng hét, 4 frame cuối mới giật zoom.
- Đá vụn trên cỏ: trước là các mảng nâu phẳng như vết bẩn; giờ là cục đá 3D méo tự nhiên, 3 tông xanh xám có viền,
  sáng mặt trên tối mặt dốc, mờ theo khoảng cách như mặt đất; bớt còn ~40% số đá rải và gom thành cụm nhỏ.
- Shot quay thấp vòng quanh Goku lúc gồng (frame 120–240): đá vụn bay lên ngay trước ống kính che nửa người Goku;
  giờ hòn nào có lúc cách camera < 2.4 m bị dời ra xa (`extras/debris_clear.py`), đá vẫn bay lên quanh Goku ở phía sau.

Goku (`build_goku`, `face_textures.py`)
- Tóc cả hai dạng dựng lại: lớp tóc ôm đầu có chân tóc thật (trước là quả cầu úp lên đầu, nhìn 3/4 thủng một lỗ).
- Goku tóc đen: mái là các lọn nhọn nằm trên trán (lọn giữa dài, hai lọn ngắn dừng trên lông mày, lọn thái dương,
  tóc mai) chừa khe để thấy trán và lông mày; v13 tóc trùm kín trán như đội mũ bảo hiểm. Gai bên trước che tai giờ
  chĩa ra ngoài phía trên tai.
- SSJ: một lọn mái đặc trưng giữa trán + một lọn ngắn, lộ trán nhiều hơn.
- Bỏ mảng sáng hình bầu dục quanh miệng SSJ (nhìn như mõm chó): là dải highlight của chất liệu da, giờ đầu dùng
  chất liệu da riêng không có dải đó.
- Có tai nhỏ tròn hai bên (lòng tai tối), lông mày đậm hơn (đầu trong dày, đuôi nhọn), miệng cười/nhếch to hơn ~35%.

Frieza (`build_frieza`, `extras/frieza_form.py`, `extras/frieza_details.py`)
- Vòm tím trên đầu dựng lại thành chỏm lớn đúng dạng cuối: mép trước ngay trên lông mày, hai bên xuống sát lỗ tai,
  sau gáy xuống thấp; viền mép liền một đường sạch (v1–v13 chỉ là một dải tím mỏng ở chân tóc).
- Thân chibi chắc hơn: hông rõ, ngực nở thon về eo, cổ và đùi dày thon về gối, gối/giáp ống chân/bàn chân to hơn,
  bắp tay + giáp tay + bàn tay + vòm vai to hơn; đuôi gốc to vuốt nhọn. Ngọc ngực dời ra trước theo ngực mới.
- Lỗ tai nổi khối (vành nổi + lòng tối). Dấu gân giận nằm trên vòm, giọt mồ hôi dời xuống thái dương.
- Sửa lỗi: các chi tiết thêm (vệt bóng, múi bụng, ngón chân, viền vai) không tắt theo Frieza ở frame 1151.

App
- Bản quay demo tắt tiếng trong simulator (clip promo vẫn lấy tiếng từ mix.wav).
