# v13: không khí rung quanh aura + bloom (chỉ app, render giữ nguyên v11)

App (`app/src/cinematic/shaders/composite.ts`)
- Heat haze: khi aura cháy, nền quanh Goku (cỏ, chân trời, bầu trời) rung nhẹ như không khí nóng, noise trôi lên
  trên theo nhịp lửa; tắt dần ra ngoài theo kích thước nhân vật trên màn hình và không méo chính Goku (chặn bằng
  matte) nên nét mặt vẫn sắc. Ở cảnh rộng nhân vật nhỏ thì vùng rung cũng nhỏ theo, không làm méo cả khung.
- Bloom mềm cho lớp energy (tóc vàng, mắt loé): lấy thêm 4 mẫu lệch ra xung quanh, quầng sáng loang rộng và ấm
  hơn thay vì chỉ sáng đúng mép tóc.
