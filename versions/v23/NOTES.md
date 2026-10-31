# v23: Kamehameha + hiệu ứng nằm đúng lớp + chữ tiếng Anh

## Đoạn Kamehameha (5.5 s, chèn trước shot kết)
`blender/scripts/kamehameha.py`. `retime.py` mở một khoảng trống 330 frame ngay sau cú đấm sau lưng (bước nhảy dọc
trong bản đồ retime ở frame gốc 1109.8); mọi kênh có key hai bên được giữ nguyên trạng thái, file mới key đè các kênh
cần diễn trong khoảng đó. Phim 28.7 s → 34.2 s.

| shot | dài | nội dung |
|---|---|---|
| A | 1.5 s | "Ka…me…": Goku lơ lửng trên biển, rút hai tay về hông phải, quả cầu xanh nhú giữa hai lòng bàn tay |
| B | 1.2 s | "Ha…me…": cận hai bàn tay + mặt nghiến răng, quả cầu lớn dần, tia điện lách tách, ánh xanh hắt lên người |
| C | 0.6 s | Frieza sững người (mắt trợn, há miệng) |
| D | 0.6 s | "HA!": qua vai Goku, đẩy hai tay, tia xanh lao ra biển (giật lùi, sóng xung kích, speedline) |
| E | 0.9 s | tia ập vào Frieza đang khoanh tay đỡ → impact frame trắng đen → cầu nổ nuốt Frieza, vòng sóng |
| F | 0.7 s | toàn cảnh sau lưng Goku: cầu nổ phình trên biển, tia tắt dần, chớp trắng sang shot kết |

- Bàn tay xoè hơi khum (thay nắm đấm suốt đoạn), IK 2 khớp cho vai/khuỷu để hai cổ tay chụm đúng chỗ, xoay cổ tay
  để lòng bàn tay úp vào quả cầu (tụ khí) rồi hướng ra trước (bắn).
- Năng lượng cel 4 tông theo góc nhìn (lõi trắng → xanh băng → xanh dương → viền lam), tự phát sáng → lớp energy
  trong app cho glow. Cầu nổ gồ ghề cuộn theo thời gian + tia điện chớp quanh.
- Nhạc: 4 nhịp "Ka–me–ha–me" (taiko + kèn + đồng ca, vòng Dm–Bb–C–A) trên tiếng khí ù dâng, nín một nhịp, "HA!" Rê
  trưởng cả dàn; tia gầm suốt lúc bắn; nổ cực lớn; kèn chủ đề kết vào đúng cut sang shot kết.
- Promo: đoạn nền xanh + chữ KAMEHAMEHA, máy zoom sát lúc "HA!", rung khi nổ.

## Hiệu ứng app nằm đúng lớp (pass depth)
- `render_passes.py` thêm pass depth: độ sâu theo trục nhìn, log chuẩn hoá 0.05–400 m, nửa độ phân giải, không AA,
  không motion blur. Video pack rộng 1728 → 2304 (cột mới: depth trên, đen dưới).
- `composite.ts` so độ sâu từng điểm ảnh với độ sâu của hiệu ứng (anchor z): aura theo ngực Goku, Death Beam nội suy
  1/z từ ngón tay Frieza tới đích, ki blast theo đầu đạn, vụ nổ theo điểm nổ. Vật gần camera hơn thì che hiệu ứng:
  tia Death Beam chui sau đầu Frieza (qua vai) và sau tóc Goku, aura không còn đè lên giáp vai Frieza ở tiền cảnh.
- Aura không phủ lên phần người Goku bị nhoè (matte một phần), motion blur ngắn lại (shutter 0.5 → 0.3).
- Aura toé ngược hướng bay: anchor mới `goku_trail` (chỗ Goku ở 0.25 s trước) → hướng lửa trong shader.

## Chữ tiếng Anh
App: HOLD TO CHARGE KI / LOADING… / REPLAY, phụ đề title "THE LEGENDARY WARRIOR", tên shot ở thanh tua (dev).
Clip promo vốn đã tiếng Anh, thêm KAMEHAMEHA.
