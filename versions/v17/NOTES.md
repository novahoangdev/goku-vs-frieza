# v17: tập trung vào hai nhân vật (dáng Frieza, đầu Goku, shading + nét vẽ)

Frieza (`build_frieza`, `fr_head_surf`, `fr_body`, `extras/frieza_*.py`)
- Thân dựng lại bằng khối tiện trơn (trước ghép cầu + viên nang nên thành dáng quả lê / chai bowling): ngực nở có
  cơ ngực, eo thon, hông gọn, đùi mảnh thuôn vào giáp ống chân tím có bắp chân, gối nhỏ, bàn chân nhỏ hai ngón.
- Đầu dạng cuối: sọ tròn dưới vòm tím, nửa dưới mặt thu hẹp về cằm nhỏ mềm, gò má rất nhẹ; vòm, mắt, vạch má,
  miệng, tai, giọt mồ hôi, dấu gân giận đều bám theo mặt đầu mới (không nổi, không chớp nháy).
- Cổ thuôn loe ở gốc, nét xương quai xanh; múi bụng/cơ ngực dời theo ngực mới; ngọc ngực nhỏ lại.
- Đuôi gốc dày vuốt nhọn, uốn chữ S (rủ ra sau, quét ra ngoài, chóp hất lên) cộng thêm lên chuyển động vẫy cũ.

Goku (`build_goku`, `goku_face_shape`, `extras/goku_outfit.py`, `face_textures.py`)
- Sửa lỗi của v16: cổ áo lót xanh trồi lên che cằm và miệng như khẩu trang ở các cảnh cận. Vai dốc xuống, cổ áo
  xanh hạ về chân cổ, đỉnh V áo lót hạ thấp; có một đoạn cổ ngắn giữa cằm và cổ áo, với vệt bóng cel dưới cằm.
- Đầu không còn là quả cầu tròn: má đầy ngay dưới mắt thuôn về cằm nhỏ mềm hơi nhô, rõ ở góc 3/4 và nhìn từ dưới.
  Tóc và nét chân tóc uốn theo, mọi decal mặt (mắt, mày, má hồng, 3 kiểu miệng, mũi) chiếu lại lên đầu mới.
- Mũi anime nhỏ: nét bóng xiên + bóng mờ dưới + gờ da rất nhỏ. Miệng cười / nhếch to hơn ~1.2 lần, nét giữa dày hơn
  có bóng môi dưới; miệng há khi thét to hơn, viền dày hơn.

Shading + nét vẽ cả hai nhân vật (`char_key_light`, `char_shading`, `CHAR_SHADE`)
- Sửa lỗi có từ v1: vỏ viền (inverted hull) bao quanh nhân vật đổ bóng lên chính nhân vật, nên đèn key không bao
  giờ chiếu tới; Frieza chỉ một màu tím nhạt đều, Goku phẳng lì trong tông tối. Giờ có mảng sáng / tối thật: đường
  ranh chéo sắc trên mặt và thân Frieza, áo cam có mặt sáng mặt tối.
- Đèn key chỉ bị chính nhân vật che (cây, mây, cột đá không làm tối nhân vật nữa), chiếu từ trên-trái chếch về
  phía camera nên mặt luôn sáng, bóng nằm phía xa.
- Tông thứ 3 sẫm hơn trong bóng ở chỗ úp xuống và khe sâu (dưới cằm, nách, dưới tóc, dưới đai) theo màu từng chất
  liệu (nâu cam trên áo, tím sẫm trên giáp...).
- Viền sáng mảnh ở mép tối của bóng dáng: Goku tóc đen viền lạnh, chuyển vàng ấm khi SSJ; Frieza viền tím nhạt.
- Đốm bóng sắc trên tóc vàng, tóc đen, giày (toon cũ có `spec` nhưng sai dấu trục Z nên chưa bao giờ hiện).
- Dải sáng nhạt chỉ hiện khi ánh khí hắt mạnh nên tóc vàng và áo không bị bạc màu. Tóc đen chỉnh lại gần đen (bớt
  ánh xanh), bóng trên mặt Goku dịu hơn để nhìn từ dưới lên bóng cằm không thành mảng loang.
