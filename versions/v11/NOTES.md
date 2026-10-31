# v11: chăm chút chi tiết (4 agent làm song song)

Mỗi agent làm một file riêng trong `blender/scripts/extras/` (build_scene chạy chúng sau cùng), tự dựng thử ra file
tạm, soi ảnh trước/sau rồi mới chép vào, nên không đụng nhau và không làm hỏng bản đang render.

Goku (`extras/goku_details.py`)
- Vòng tròn chữ 悟 lớn sau lưng võ phục (rõ nhất ở các shot qua vai Goku), nút thắt đai lưng phía trước.
- Viền gờ trên dưới băng cổ tay, viền gấu tay áo, đường may dọc mũi giày.
- Nếp gấp vải bằng nét mực thon hai đầu ở lưng, ngực, đùi.
- Sợi tóc sáng / tối trên tóc SSJ và tóc đen (ẩn hiện theo dạng, ẩn lúc dịch chuyển tức thời).

Frieza (`extras/frieza_details.py`)
- Vệt bóng lưỡi liềm + chấm trên vòm đầu, giáp vai, giáp tay, giáp ống chân; viền tím nhạt chân giáp vai.
- Ngọc ngực tím hồng bóng hơn có điểm sáng; nét cơ ngực + múi bụng mờ; hai ngón chân tròn mỗi bàn chân.

Cảnh Namek (`extras/env_details.py`)
- Nhà vòm: viền cửa sổ tròn, khung cửa chữ U, đế, chóp có cổ + bầu tròn + ăng-ten; thêm nhà vòm phụ và 4 nhà ở xa.
- Cây Ajisa tán nhiều tầng bồng hơn; cụm đá + bụi cỏ quanh chỗ nhân vật đứng (4–16 m), mesa và cột đá mảnh ở xa.
- Kiểm tra camera không xuyên vật mới ở cả 1200 frame.

Hiệu ứng màn hình (`app/src/cinematic/shaders/overlay.ts`)
- Speed lines kiểu manga: vạch hình nêm nhọn ở trong, phình ra mép, dày mỏng ngẫu nhiên, viền tách màu nhẹ; chấm
  halftone mực ở rìa màn hình khi đang tăng tốc.
- Khung "focus burst" lúc flash mạnh (biến hình, đòn kết liễu): tia mực toả ra trên nền trắng + vòng nét cọ nở dần.
