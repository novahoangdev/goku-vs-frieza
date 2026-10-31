# v30: làm đẹp + vật lý tiếp (làm đêm)

- Death Beam trượt Goku giờ trúng đất phía sau (`secondary.py: beam_impacts`): bắn tia từ ngón tay Frieza qua đích rồi
  ray-cast tìm điểm chạm đất (~5 m sau lưng Goku) → loé hồng trắng (lớp energy cho app glow), 7 cục đất văng theo đường
  đạn g thật, cụm bụi bốc lên vỡ vụn tan dần, vết cháy sém để lại trên đất; marker `sfx:pop` → tiếng nổ đất nhỏ
  (bục trầm + đất rơi rào rào) đúng frame trúng.
- Cổ Goku tông bóng như anime (cằm đổ bóng xuống cổ, vật liệu riêng `goku_neck_skin` sẫm hơn mặt): trước cùng màu mặt nên cổ sáng như khúc gỗ dưới cằm.
- Đá bị khí nâng lên trước lúc biến hình không còn bay êm: rung lắc + nhấp nhô trong trường khí, càng gần lúc nổ càng dữ (RNG riêng, đường đạn sau nổ giữ nguyên).
- App: Goku tóc đen hết mặt nạ trắng xám — chỉnh màu "Namek giông lạnh" (khử màu 28 % + ám xanh) giờ chỉ áp nhẹ lên người Goku (matte: giữ 93 % độ bão hoà, ám xanh rất nhẹ); cảnh vẫn lạnh u ám như cũ, da mặt + áo cam giữ màu ấm.
- Tiếng cỏ + lá xào xạc theo cơn giật (cùng gust với cỏ/cây/lá bay trên hình): lạo xạo cao tần chỉ rõ khi giật mạnh, nhỏ dần sau nổ biến hình khi giông dịu.
- Mây giông trên trời trôi nhanh lúc giông đầu phim (gió mạnh, ~0.65°/s — gấp 3 lần trước), chậm hẳn sau nổ biến hình (trước trôi đều ~0.2°/s cả phim).
- Cổ Frieza tông bóng nhẹ (`fr_neck_skin` trắng ngả tím hơn đầu) để tách cằm khỏi cổ ở các góc nhìn thấy cổ.
