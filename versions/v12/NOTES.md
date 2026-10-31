# v12: color grade phim + hạt phim (chỉ app, không render lại Blender)

App (`app/src/cinematic/shaders/overlay.ts`)
- Vignette đổi từ đen tuyền sang xanh navy sâu: góc màn hình lạnh lại trong khi aura, beam, flash vẫn ấm; nhìn
  như color grade anime thay vì lớp tối đè lên hình.
- Hạt phim mịn (2 px, đổi 24 lần/giây) phủ cả khung, đậm hơn ở vùng tối rìa màn hình; hash theo toạ độ đã mod
  nên không lộ dải/moiré khi toạ độ lớn.
- Bản quay giữ nguyên render Blender của v11, nên so sánh v11 ↔ v12 chỉ thấy khác ở lớp phủ màn hình.
