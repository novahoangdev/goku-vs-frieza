# v2: mặt anime + dáng người + cảnh Namek đầy đủ

Model
- Mặt vẽ bằng texture (blender/scripts/face_textures.py, SDF + numpy): mắt to có mi dày, đuôi mi, tròng gradient 3 tông, viền tròng, 3 điểm sáng; má hồng gạch chéo; miệng cười / miệng hét có lưỡi và răng.
- Miếng dán mặt ôm sát hình elip của đầu (face_decal), đầu chibi má bầu, mắt hạ thấp và to hơn.
- SSJ: mắt ngọc lam, mi trên hạ xuống nhìn quyết tâm; tóc vàng đậm hơn, không còn trắng bệch.
- Toon shader thêm viền sáng (rim) và đốm bóng tính theo hướng camera, nên luôn thấy kiểu anime.
- Frieza: vòm đầu tím bóng, mép cong cao ở trán và thấp ra gáy; mắt đỏ cụp mi nhìn khinh khỉnh, vạch tím dưới mắt; môi tím nhếch.
- Dáng người: tay chân thon dần, quần võ phục ống rộng, cổ giày xanh; Frieza eo nhỏ, giáp vai dẹt.

Cảnh
- Namek: nhà mái vòm, bụi cỏ, thảm cỏ loang, đá cuội, cột đá có vân ngang, mây cụm, vết nứt mảnh hơn.

Góc máy
- Shot 7b: Frieza lao tới, máy đặt qua vai Goku (bản v1 không thấy ai).
- Shot 8 truy đuổi: máy bay trước mặt Goku nhìn lùi lại, thấy Goku né và Frieza đuổi phía sau.
- Shot 9c: máy qua vai Goku nhìn Frieza văng đi xa (bản v1 bị cắt ở mép khung).

Hiệu ứng trong app (Skia)
- Aura có lưỡi lửa cuộn lên; tắt "quả trứng" khi Goku bị cột đá che (v1 có đốm lửa lơ lửng).
- Death Beam kiểu anime: viền tím → hồng → lõi trắng, gợn rung, loé sáng ở đầu ngón tay.
