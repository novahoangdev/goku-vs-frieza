# v28: làm đẹp + vật lý tiếp (làm đêm)

- Tia Kamehameha lõi trắng/xanh băng rộng hơn (Layer Weight blend 0.42 → 0.3): nhìn từ sau lưng Goku hết như ống nhựa xanh.
- Vòng sóng xung kích của vụ nổ kame hết như vòng hula xanh đặc: ống mảnh 0.035 → 0.014 (scale lên 4.6 lần không còn dày 16 cm), vật liệu vỡ vụn theo nhiễu như bọt sóng v27, tan dần trong 32 frame.
- Cây đung đưa (`secondary.py: tree_wind`, 54 cây kể cả cây trên đỉnh cột đá): thân + tán gắn vào một empty ở gốc thân rồi
  xoay. Gió giông cùng hướng + cùng cơn giật với cỏ (cơn giật lan qua rừng ~9 m/s nên mỗi cây trễ một nhịp), cây cao ngả ít
  hơn; gió khí lúc gồng đẩy cây gần Goku ngả ra ngoài; sóng xung kích lúc nổ biến hình quật cây ra ngoài rồi bật lại dao động
  tắt dần, tới cây xa trễ theo khoảng cách (~340 m/s).
- Vòng bụi sóng xung kích lúc nổ biến hình: 18 cụm bụi toả ra ngoài từ chân Goku, chậm dần vì lực cản không khí
  (r = r0 + R·(1 − e^(−t/τ))), bốc lên nhẹ, rồi vỡ vụn tan đi (vật liệu `burst_dust` 2 tông phẳng, không viền, ngưỡng nhiễu
  theo alpha màu object). RNG riêng (seed 4242) để không xô lệch chuỗi random chung.
- Cận cảnh vụ nổ kame (shot E) hết cháy trắng cả khung: vương miện nước có vật liệu riêng `kame_crown_m` tông nước biển
  (xanh băng nhạt → xanh ngọc → mép xanh lam) thay bọt trắng; app chừa khoảng sáng khi cộng glow lớp energy
  (`headroom`: chỗ đã gần trắng cộng ít đi 60 %) → mép xanh của khối nổ hiện lại, quầng loang ra nền tối vẫn giữ.
- Tóc đen Goku đen trung tính như ảnh mẫu 3D (trước ngả xanh navy): nền #1F1F25, bóng #08080B, mặt sáng #3E3F49, đốm bóng xám #767986.
