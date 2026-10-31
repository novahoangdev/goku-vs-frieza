# Vẽ texture mặt anime (mắt, miệng, má) bằng SDF + numpy, xuất PNG có alpha vào blender/textures/.
# Chạy bằng python của Blender (có numpy):
#   /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 blender/scripts/face_textures.py
import os, struct, zlib
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")
N = 512
ys, xs = np.mgrid[0:N, 0:N]
X = (xs + 0.5) / N * 2 - 1          # [-1, 1], +x = khoé mắt ngoài
Y = 1 - (ys + 0.5) / N * 2          # +y = lên
PX = N / 2                          # pixel trên 1 đơn vị


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def ell(cx, cy, rx, ry, rot=0.0):
    c, s = np.cos(rot), np.sin(rot)
    x, y = X - cx, Y - cy
    x, y = x * c + y * s, -x * s + y * c
    k = np.sqrt((x / rx) ** 2 + (y / ry) ** 2)
    return (k - 1) * min(rx, ry)


def seg(ax, ay, bx, by, r0, r1=None):
    """Nét bút từ a tới b, dày r0 → r1 (đầu nhọn khi r1 nhỏ)."""
    r1 = r0 if r1 is None else r1
    px, py, vx, vy = X - ax, Y - ay, bx - ax, by - ay
    t = np.clip((px * vx + py * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(px - vx * t, py - vy * t) - (r0 + (r1 - r0) * t)


def arc(cx, cy, rx, ry, a0, a1, w0, w1=None, n=24):
    w1 = w0 if w1 is None else w1
    d = np.full(X.shape, 9.0)
    pts = [(cx + rx * np.cos(a), cy + ry * np.sin(a)) for a in np.linspace(a0, a1, n + 1)]
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        d = np.minimum(d, seg(*pts[i], *pts[i + 1], w0 + (w1 - w0) * t0, w0 + (w1 - w0) * t1))
    return d


def cov(d):
    return np.clip(0.5 - d * PX, 0, 1)


class Canvas:
    def __init__(self):
        self.rgb = np.zeros((N, N, 3))
        self.a = np.zeros((N, N))

    def paint(self, d_or_cov, color, opacity=1.0, sdf=True, clip=None):
        k = (cov(d_or_cov) if sdf else d_or_cov) * opacity
        if clip is not None:
            k = k * clip
        col = color if np.ndim(color) == 3 else np.broadcast_to(np.asarray(color), (N, N, 3))
        self.rgb = self.rgb * (1 - k[..., None]) + col * k[..., None]
        self.a = self.a + k * (1 - self.a)

    def save(self, name, mirror=False):
        a = self.a
        rgb = np.where(a[..., None] > 1e-4, self.rgb / np.maximum(a, 1e-4)[..., None], 0)   # bỏ premultiply
        if mirror:
            rgb, a = rgb[:, ::-1], a[:, ::-1]
        img = np.dstack([rgb, a])
        data = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
        raw = b"".join(b"\x00" + data[y].tobytes() for y in range(N))

        def chunk(t, b):
            return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 6, 0, 0, 0)) \
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(png)
        print("wrote", name)


def vgrad(top, bottom, y0, y1):
    t = np.clip((Y - y1) / (y0 - y1), 0, 1)[..., None]
    return hexc(bottom) * (1 - t) + hexc(top) * t


def poly(pts, widths):
    """Nét bút qua nhiều điểm, độ dày nội suy theo từng điểm."""
    d = np.full(X.shape, 9.0)
    for (a, b), w0, w1 in zip(zip(pts, pts[1:]), widths, widths[1:]):
        d = np.minimum(d, seg(*a, *b, w0, w1))
    return d


def eye_shape(cx, cy, rx, ry, cut=None, low=None):
    """Lòng trắng = elip, có thể cắt mi trên theo đường Y = a + bX (cụp/xếch) và nâng mi dưới theo Y = c0 + c1X + c2X²."""
    def ytop(x):
        e = cy + ry * np.sqrt(np.clip(1 - ((x - cx) / rx) ** 2, 0, 1))
        return e if cut is None else np.minimum(e, cut[0] + cut[1] * x)

    def ybot(x):
        e = cy - ry * np.sqrt(np.clip(1 - ((x - cx) / rx) ** 2, 0, 1))
        return e if low is None else np.maximum(e, low[0] + low[1] * x + low[2] * x * x)
    white = ell(cx, cy, rx, ry)
    if cut is not None:
        white = np.maximum(white, (Y - (cut[0] + cut[1] * X)) * 0.7)
    if low is not None:
        white = np.maximum(white, -(Y - (low[0] + low[1] * X + low[2] * X * X)) * 0.7)
    xs_ = np.linspace(cx - rx, cx + rx, 600)
    ok = xs_[ytop(xs_) - ybot(xs_) > 0.004]
    return white, ytop, ybot, ok[0], ok[-1]


def paint_iris(c, inside, ytop, icx, icy, irx, iry, top, mid, bot, ring, pupil, prx, pry, glow,
               hl=1.0, streaks=22, shade=0.3):
    """Tròng anime: gradient tối trên → sáng dưới, vân tia mảnh, vầng sáng hình lưỡi liềm ở đáy, đồng tử,
    bóng mi đổ đậm ở mép trên (ngay dưới mi), viền tối, 1 điểm sáng chính sắc + 1 điểm phụ + chấm nhỏ."""
    ir = ell(icx, icy, irx, iry)
    k = cov(ir) * inside
    t = np.clip((Y - (icy - iry)) / (2 * iry), 0, 1)[..., None]           # 0 đáy → 1 đỉnh
    lo = hexc(bot) * (1 - t * 2) + hexc(mid) * (t * 2)
    hi = hexc(mid) * (1 - (t - 0.5) * 2) + hexc(top) * ((t - 0.5) * 2)
    c.paint(k, np.where(t < 0.5, lo, hi), sdf=False)
    rr = np.sqrt(((X - icx) / irx) ** 2 + ((Y - icy) / iry) ** 2)
    if streaks:
        ang = np.arctan2((Y - icy) / iry, (X - icx) / irx)
        st = (np.cos(ang * streaks) * 0.5 + 0.5) ** 5 * np.clip((rr - 0.3) / 0.25, 0, 1) * np.clip((0.97 - rr) / 0.12, 0, 1)
        c.paint(st * k, hexc(top), 0.32, sdf=False)
    g = np.clip(1 - ((X - icx) / (irx * 0.82)) ** 2 - ((Y - (icy - iry * 0.6)) / (iry * 0.42)) ** 2, 0, 1) ** 0.7
    c.paint(g * k, hexc(glow), 0.8, sdf=False)
    c.paint(ell(icx, icy + pry * 0.1, prx, pry), hexc(pupil), clip=k)
    c.paint(ell(icx, icy + pry * 0.1, prx * 1.35, pry * 1.2), hexc(pupil), 0.35, clip=k)   # quầng mờ quanh đồng tử
    yt = ytop(X)
    sh = np.clip(1 - (yt - Y) / shade, 0, 1) ** 1.3                    # bóng mi trên đổ xuống tròng
    c.paint(sh * k, hexc(ring), 0.92, sdf=False)
    c.paint(np.abs(ir) - 0.028, hexc(ring), clip=inside)
    # điểm sáng chính: luôn nằm dưới mép mi (mắt cụp vẫn thấy)
    hx, hy = icx - irx * 0.36, icy + iry * 0.3
    hry = iry * 0.24 * hl
    hy = min(hy, float(ytop(np.array(hx))) - hry * 1.25)
    c.paint(ell(hx, hy, irx * 0.27 * hl, hry, 0.35), hexc("#FFFFFF"), clip=inside)
    c.paint(ell(icx + irx * 0.4, icy - iry * 0.42, irx * 0.13 * hl, irx * 0.13 * hl), hexc("#FFFFFF"), 0.95, clip=inside)
    c.paint(ell(hx + irx * 0.34, hy - hry * 0.5, irx * 0.06 * hl, irx * 0.06 * hl), hexc("#FFFFFF"), 0.85, clip=inside)


def eye(name, iris_top, iris_mid, iris_bot, ring, pupil, lash, lid="#C9CFE6", sclera="#FFFFFF",
        lidcut=None, mark=None, iris_r=(0.46, 0.64), pupil_r=(0.19, 0.27), glow=None, low=None,
        iris_c=(0.03, -0.12), lash_w=(0.03, 0.085), wing=0.22, crease="#B9826A", hl=1.0):
    """Mắt phải (khoé ngoài ở +x); bản mắt trái lật ngang. Mi trên là một nét mực liền theo mép lòng trắng, mảnh ở
    khoé trong, dày dần ra khoé ngoài rồi vẩy đuôi; mi dưới mảnh, chỉ nửa ngoài; nếp mí mảnh phía trên."""
    c = Canvas()
    white, ytop, ybot, x0, x1 = eye_shape(0.0, -0.06, 0.6, 0.76, lidcut, low)
    inside = cov(white)
    c.paint(white, hexc(sclera))
    yt = ytop(X)
    c.paint(np.clip(1 - (yt - Y) / 0.32, 0, 1) ** 1.2, hexc(lid), 0.9, sdf=False, clip=inside)   # bóng mi trên đổ lên lòng trắng
    c.paint(np.clip(1 - (Y - ybot(X)) / 0.12, 0, 1), hexc(lid), 0.35, sdf=False, clip=inside)
    paint_iris(c, inside, ytop, *iris_c, *iris_r, iris_top, iris_mid, iris_bot, ring, pupil, *pupil_r,
               glow or iris_bot, hl=hl)
    # nếp mí
    cx_ = np.linspace(x0 + (x1 - x0) * 0.35, min(x1, 0.54) - 0.04, 8)
    c.paint(poly([(x, float(ytop(np.array(x))) + 0.15 + 0.03 * (x - cx_[0])) for x in cx_],
                 np.linspace(0.004, 0.014, 8)), hexc(crease), 0.7)
    # mi trên
    lx = np.linspace(x0 + 0.01, min(x1, 0.54), 16)          # dừng trước khi mép elip vòng xuống
    ws = np.linspace(lash_w[0], lash_w[1], 16) ** 1.0
    pts = [(x, float(ytop(np.array(x))) + w * 0.35) for x, w in zip(lx, ws)]
    c.paint(poly(pts, ws), hexc(lash))
    ex, ey_ = pts[-1]
    c.paint(poly([(ex - 0.04, ey_ - 0.01), (ex + wing * 0.5, ey_ + wing * 0.12), (ex + wing, ey_ + wing * 0.5)],
                 [lash_w[1], lash_w[1] * 0.6, 0.008]), hexc(lash))                                  # đuôi mi vẩy ra ngoài
    c.paint(seg(pts[0][0] + 0.02, pts[0][1], pts[0][0] - 0.05, pts[0][1] - 0.08, ws[0], 0.006), hexc(lash))  # móc khoé trong
    # mi dưới: nửa ngoài, mảnh, đậm dần ra khoé ngoài, hở ở khoé
    bx = np.linspace(0.02, x1 - 0.07, 10)
    c.paint(poly([(x, float(ybot(np.array(x))) - 0.012) for x in bx], np.linspace(0.004, 0.017, 10)), hexc(lash), 0.9)
    if mark:                                       # vạch tím dưới mắt của Frieza
        c.paint(seg(-0.3, -0.9, 0.32, -0.9, 0.035, 0.035), hexc(mark))
        c.paint(seg(0.32, -0.9, 0.6, -0.7, 0.035, 0.01), hexc(mark))
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def eye_shut(name, color):
    """Mắt nhắm tịt kiểu "> <" khi hét."""
    c = Canvas()
    c.paint(seg(0.55, 0.42, -0.42, 0.02, 0.085, 0.06), hexc(color))
    c.paint(seg(0.55, -0.38, -0.42, 0.02, 0.085, 0.06), hexc(color))
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def eye_blink(name, color, flat=False):
    """Mắt chớp: vệt mi cong nhẹ (Goku) hoặc gần thẳng, cụp (Frieza)."""
    c = Canvas()
    if flat:
        c.paint(seg(-0.6, -0.05, 0.62, -0.12, 0.09, 0.075), hexc(color))
    else:
        c.paint(arc(0.0, 0.35, 0.62, 0.5, -np.pi * 0.95, -np.pi * 0.05, 0.065, 0.05), hexc(color))
    c.paint(seg(0.55, -0.05, 0.82, 0.08, 0.05, 0.008), hexc(color))
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def anger_vein(name):
    """Dấu "giận nổi gân" 💢: 4 cung cong đỏ quay lưng vào nhau."""
    c = Canvas()
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        a0 = np.arctan2(sy, sx)
        d = arc(sx * 0.62, sy * 0.62, 0.42, 0.42, a0 + np.pi * 0.62, a0 + np.pi * 1.38, 0.11, 0.11)
        c.paint(d - 0.03, hexc("#5A0A12"))
        c.paint(d, hexc("#F0283C"))
    c.save(f"{name}.png")


def sweat_drop(name):
    """Giọt mồ hôi kiểu anime: giọt nước xanh nhạt, viền xanh đậm, chấm sáng."""
    c = Canvas()
    body = np.minimum(ell(0, -0.25, 0.42, 0.5), seg(0, -0.1, 0, 0.82, 0.38, 0.0))
    c.paint(body - 0.035, hexc("#2E6FB0"))
    c.paint(body, hexc("#BFE8FF"))
    c.paint(ell(-0.14, -0.2, 0.09, 0.16, 0.3), hexc("#FFFFFF"))
    c.save(f"{name}.png")


def brow(name, color, angry=False, bold=False, edge=None):
    c = Canvas()
    if angry:                                      # mày giận kiểu FighterZ: đầu trong dày, chúc mạnh, cong nhẹ, đuôi nhọn
        d = poly([(-0.78, -0.46), (-0.4, -0.2), (0.05, 0.08), (0.45, 0.28), (0.8, 0.36)], [0.26, 0.25, 0.2, 0.13, 0.03])
        d = np.maximum(d, -(Y - (-0.62 + 0.0 * X)))                         # đầu trong cắt thẳng (sắc)
        if edge:
            c.paint(d - 0.03, hexc(edge))
        c.paint(d, hexc(color))
    elif bold:                                     # Goku: lông mày đậm, đầu trong dày, đuôi nhọn (nhìn xa vẫn rõ)
        d = poly([(-0.8, -0.24), (-0.4, 0.0), (0.05, 0.14), (0.48, 0.16), (0.82, 0.02)], [0.27, 0.26, 0.22, 0.14, 0.03])
        c.paint(np.maximum(d, -(Y - (-0.44 + 0.0 * X))), hexc(color))     # mày rậm thẳng, xếch nhẹ, đầu trong cắt vuông
    else:
        c.paint(arc(0.0, -0.9, 0.85, 1.05, np.pi * 0.85, np.pi * 0.2, 0.14, 0.05), hexc(color))
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def mouth_smile(name, color, smirk=False):
    """Miệng Goku: nét cong đậm, đuôi thon, chấm khoé + bóng môi dưới nhạt để đọc được ở cỡ khung truyện."""
    c = Canvas()
    lip = hexc("#D98A6E")
    if smirk:
        c.paint(arc(-0.08, -0.08, 0.3, 0.15, np.pi * 1.2, np.pi * 1.8, 0.035), lip, 0.45)
        # cười nhếch tự tin: nét chạy chéo lên một bên, khoé nhếch dày + nếp má ngắn, khoé kia mảnh
        c.paint(poly([(-0.62, 0.02), (-0.3, -0.06), (0.05, -0.04), (0.38, 0.08), (0.62, 0.3)], [0.03, 0.05, 0.07, 0.085, 0.07]),
                hexc(color))
        c.paint(seg(0.6, 0.28, 0.8, 0.5, 0.06, 0.02), hexc(color))
        c.paint(seg(0.78, 0.18, 0.86, 0.4, 0.025, 0.008), hexc(color), 0.75)
    else:
        c.paint(arc(0.0, -0.08, 0.26, 0.14, np.pi * 1.2, np.pi * 1.8, 0.035), lip, 0.45)
        c.paint(arc(0.0, 0.42, 0.62, 0.55, -np.pi * 0.82, -np.pi * 0.5, 0.03, 0.068, n=20), hexc(color))
        c.paint(arc(0.0, 0.42, 0.62, 0.55, -np.pi * 0.5, -np.pi * 0.18, 0.068, 0.03, n=20), hexc(color))
    c.save(f"{name}.png")


def goku_nose(name):
    """Mũi anime: một nét bóng ngắn xiên + vệt bóng mềm phía dưới (không viền, hợp tông da)."""
    c = Canvas()
    soft = np.clip(1 - np.sqrt(((X + 0.12) / 0.38) ** 2 + ((Y + 0.28) / 0.22) ** 2), 0, 1) ** 1.5
    c.paint(soft, hexc("#D8876A"), 0.55, sdf=False)
    c.paint(seg(-0.02, 0.32, -0.16, -0.28, 0.055, 0.095), hexc("#A85A44"), 0.95)
    c.save(f"{name}.png")


def mouth_open(name, inside="#5A1620", rim="#3A1014", rim_w=0.025, deep="#240509", tongue="#E86A78",
               shape=None, teeth_y=0.33, lower_teeth=None):
    """Miệng há (hét/hoảng): lòng miệng gradient sẫm ở trên → đỏ ở dưới, lưỡi có điểm sáng, hàng răng trên,
    viền mực dày hơn ở hai khoé."""
    c = Canvas()
    if shape is None:
        shape = np.maximum(ell(0.0, -0.05, 0.72, 0.85), Y - 0.5)
    k = cov(shape)
    c.paint(k, vgrad(deep, inside, 0.45, -0.5), sdf=False)
    c.paint(ell(0.0, -0.78, 0.52, 0.36), hexc(tongue), clip=k)
    c.paint(ell(-0.12, -0.6, 0.16, 0.06), hexc("#FFB3BC"), 0.7, clip=k)
    c.paint(seg(0.0, -0.5, 0.0, -0.75, 0.012, 0.004), hexc(deep), 0.5, clip=k)
    c.paint(np.maximum(shape, -(Y - teeth_y)), hexc("#FFFFFF"))
    c.paint(np.maximum(shape, -(Y - teeth_y)) + 0.0, hexc("#C8C4D8"), 0.6,
            clip=np.clip(1 - (Y - teeth_y) / 0.05, 0, 1))                   # bóng dưới mép răng
    if lower_teeth is not None:
        c.paint(np.maximum(shape, Y - lower_teeth), hexc("#F2EEF6"))
    c.paint(np.abs(shape) - rim_w, hexc(rim))
    for sx in (-1, 1):                                                      # khoé miệng đậm
        c.paint(ell(sx * 0.66, 0.42, 0.1, 0.08), hexc(rim), clip=cov(shape + 0.08) * (1 - cov(shape + 0.0) * 0.0))
    c.save(f"{name}.png")


def mouth_grit(name, rim="#3A1014", lip=None, tilt=0.0, w=0.74, h=0.3, droop=0.2):
    """Nghiến răng: khung chữ nhật bo tròn, khoé trễ xuống, hai hàng răng trắng có khe giữa và vạch răng,
    viền mực dày; tilt > 0 nhếch khoé phải (nanh của Frieza)."""
    c = Canvas()
    yy = Y + droop * X * X - tilt * X
    qx, qy = np.abs(X) - (w - 0.12), np.abs(yy) - (h - 0.12)
    box = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - 0.12
    k = cov(box)
    c.paint(k, hexc("#FFFFFF"), sdf=False)
    c.paint(k * np.clip((np.abs(X) - w * 0.55) / (w * 0.45), 0, 1), hexc("#B8B2C8"), 0.8, sdf=False)   # răng tối dần vào khoé
    c.paint(np.maximum(np.abs(yy) - 0.035, box + 0.02), hexc("#4A1A22"), clip=k)                       # khe giữa hai hàng răng
    for x in (-0.46, -0.16, 0.16, 0.46):
        c.paint(np.maximum(seg(x, -h, x * 1.05, h, 0.012), -(np.abs(yy) - 0.035)), hexc("#8C8498"), 0.85, clip=k)
    c.paint(np.abs(box) - 0.045, hexc(rim))
    if lip:
        c.paint(seg(-0.3, -h - 0.13 - 0.0, 0.3, -h - 0.13, 0.03, 0.03) , hexc(lip), 0.6)
    for sx in (-1, 1):                                                      # nếp căng ở khoé
        y0 = -droop * w * w + tilt * sx * w
        c.paint(seg(sx * (w + 0.02), y0, sx * (w + 0.16), y0 - 0.16 + tilt * sx * 0.25, 0.03, 0.006), hexc(rim))
    c.save(f"{name}.png")


def blush(name):
    c = Canvas()
    soft = np.clip(1 - np.sqrt((X / 0.9) ** 2 + (Y / 0.6) ** 2), 0, 1) ** 1.2
    c.paint(soft, hexc("#FF8C90"), 0.6, sdf=False)
    for i, x in enumerate((-0.35, 0.0, 0.35)):
        c.paint(seg(x - 0.12, -0.25, x + 0.12, 0.25, 0.04, 0.03), hexc("#F0606A"), 0.85)
    c.save(f"{name}.png")


# ───────────── Frieza (final form): mắt hạnh nhân sắc, mi trên đậm xếch, vạch tím dưới mắt, môi tím sẫm ─────────────
FR_LASH, FR_LID, FR_RIDGE = "#1C0718", "#CDBFE0", "#9C88BC"


def frieza_eye(name, shock=False, angry=False):
    """Mắt phải Frieza (khoé ngoài +x). Thường: mi trên thẳng, xếch lên ở đuôi, che nửa trên tròng (vẻ khinh khỉnh,
    tự tin) + gờ mày nhạt chúc vào trong (đe doạ). shock: tròn mở to, tròng co nhỏ, gờ mày nhướng.
    angry: mi trên dốc mạnh vào trong, mi dưới nâng lên, tròng nhỏ, đồng tử dọc như kim, gờ mày đậm chúc xuống."""
    c = Canvas()
    if shock:
        white = ell(0.0, -0.08, 0.6, 0.74)
        ytop = lambda x: -0.08 + 0.74 * np.sqrt(np.clip(1 - (x / 0.6) ** 2, 0, 1))
        iris_c, iris_r, pupil_r = (0.02, -0.12), (0.25, 0.31), (0.06, 0.1)
    else:
        a, b = (0.2, 0.34) if angry else (0.3, 0.2)  # mi trên: Y = a + bX (khoé trong thấp, đuôi mắt cao)
        low = (-0.6 - 0.12 * X + 0.25 * (X - 0.05) ** 2) if angry else (-0.72 + 0.3 * (X - 0.05) ** 2)
        white = np.maximum(ell(0.04, -0.12, 0.66, 0.66), (Y - (a + b * X)) * 0.7)
        white = np.maximum(white, -(Y - low) * 0.7)   # mí dưới phẳng hơn: mắt dài, sắc
        ytop = lambda x, a=a, b=b: np.minimum(a + b * x, -0.12 + 0.66 * np.sqrt(np.clip(1 - ((x - 0.04) / 0.66) ** 2, 0, 1)))
        iris_c, iris_r, pupil_r = ((-0.06, -0.2), (0.32, 0.4), (0.05, 0.22)) if angry else ((-0.04, -0.17), (0.4, 0.5), (0.085, 0.24))
    inside = cov(white)
    c.paint(white, hexc("#FFFFFF"))
    c.paint(np.clip(1 - (ytop(X) - Y) / 0.34, 0, 1) ** 1.2, hexc(FR_LID), 0.9, sdf=False, clip=inside)   # bóng mi đổ lên lòng trắng
    paint_iris(c, inside, ytop, *iris_c, *iris_r, "#3A0210", "#D41A36", "#FF7A88", "#24010A", "#12010A", *pupil_r,
               "#FFC2C8", hl=0.8 if shock else 0.9, streaks=18, shade=0.26)
    if shock:
        c.paint(arc(0.0, -0.08, 0.62, 0.76, np.pi * 0.98, np.pi * 0.06, 0.03, 0.06), hexc(FR_LASH))
        c.paint(seg(0.52, 0.42, 0.8, 0.6, 0.05, 0.008), hexc(FR_LASH))
        c.paint(arc(0.0, -0.08, 0.6, 0.74, -np.pi * 0.1, -np.pi * 0.45, 0.014, 0.004), hexc(FR_LASH), 0.9)
        c.paint(arc(0.0, 0.5, 0.75, 0.42, np.pi * 0.85, np.pi * 0.2, 0.03, 0.012) + 0.0 * X, hexc(FR_RIDGE), 0.8)
    else:
        # mi trên: nét đậm thẳng, dày dần về đuôi, đuôi mi vẩy lên; móc nhỏ ở khoé trong
        c.paint(seg(-0.66, a - 0.66 * b - 0.01, 0.62, a + 0.62 * b + 0.02, 0.045, 0.085), hexc(FR_LASH))
        c.paint(seg(0.6, a + 0.6 * b + 0.02, 0.95, a + 0.95 * b + 0.2, 0.07, 0.01), hexc(FR_LASH))
        c.paint(seg(-0.66, a - 0.66 * b - 0.01, -0.76, a - 0.66 * b - 0.12, 0.04, 0.012), hexc(FR_LASH))
        if angry:
            bx = np.linspace(-0.05, 0.58, 10)                                              # mí dưới nâng, căng, bám mép
            by = np.maximum(-0.6 - 0.12 * bx + 0.25 * (bx - 0.05) ** 2,
                            -0.12 - 0.66 * np.sqrt(np.clip(1 - ((bx - 0.04) / 0.66) ** 2, 0, 1)))
            c.paint(poly(list(zip(bx, by - 0.014)), np.linspace(0.01, 0.026, 10)), hexc(FR_LASH), 0.9)
            c.paint(seg(-0.66, 0.42, 0.74, 0.86, 0.075, 0.018), hexc("#7A5A9E"))            # gờ mày đậm, chúc mạnh vào trong
            c.paint(seg(-0.72, 0.28, -0.6, 0.62, 0.016, 0.004), hexc("#7A5A9E"), 0.8)       # nếp nhăn giận giữa trán
        else:
            bx = np.linspace(0.1, 0.6, 10)                                                # mí dưới mảnh, nửa ngoài, bám mép
            by = np.maximum(-0.72 + 0.3 * (bx - 0.05) ** 2, -0.12 - 0.66 * np.sqrt(np.clip(1 - ((bx - 0.04) / 0.66) ** 2, 0, 1)))
            c.paint(poly(list(zip(bx, by - 0.012)), np.linspace(0.006, 0.022, 10)), hexc(FR_LASH), 0.85)
            c.paint(seg(-0.62, 0.66, 0.72, 0.92, 0.038, 0.012), hexc(FR_RIDGE), 0.85)       # gờ mày nhạt chúc vào trong
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def frieza_eye_hit(name):
    """Trúng đòn: mắt nhắm nghiến kiểu "> <" mực tím, gờ mày nhướng lên ở trong (đau), giọt nước mắt ở khoé."""
    c = Canvas()
    c.paint(poly([(0.66, 0.36), (0.1, 0.16), (-0.5, -0.02)], [0.07, 0.085, 0.03]), hexc(FR_LASH))
    c.paint(poly([(0.66, -0.4), (0.1, -0.2), (-0.5, -0.04)], [0.06, 0.075, 0.03]), hexc(FR_LASH))
    c.paint(seg(-0.62, 0.86, 0.74, 0.6, 0.05, 0.014), hexc("#7A5A9E"))                 # gờ mày cau lên giữa (đau)
    for i, (x, y) in enumerate(((0.82, 0.3), (0.9, 0.0), (0.82, -0.3))):              # vạch căng ở đuôi mắt
        c.paint(seg(x, y, x + 0.12, y + (0.08 - 0.08 * i), 0.016, 0.006), hexc(FR_LASH), 0.8)
    drop = np.minimum(ell(-0.5, -0.36, 0.09, 0.11), seg(-0.5, -0.3, -0.5, -0.12, 0.08, 0.0))
    c.paint(drop - 0.02, hexc("#2E6FB0"))
    c.paint(drop, hexc("#CFF0FF"))
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def frieza_blink(name):
    """Mắt nhắm khinh khỉnh: cung võng xuống, đuôi vẩy lên, gờ mày giữ nguyên."""
    c = Canvas()
    c.paint(arc(0.0, 0.32, 0.66, 0.36, -np.pi * 0.95, -np.pi * 0.06, 0.05, 0.075), hexc(FR_LASH))
    c.paint(seg(0.64, 0.25, 0.92, 0.42, 0.06, 0.008), hexc(FR_LASH))
    c.paint(seg(-0.62, 0.66, 0.72, 0.92, 0.038, 0.012), hexc(FR_RIDGE), 0.85)
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def frieza_cheek(name):
    """Vạch tím dưới mắt (final form): nét dày ngay dưới mắt, cong xuống thon dần về phía má ngoài."""
    c = Canvas()
    path = [(-0.7, 0.55), (-0.25, 0.42), (0.2, 0.18), (0.55, -0.2), (0.72, -0.62)]
    widths = [0.07, 0.11, 0.1, 0.07, 0.03, 0.006]
    d = np.full(X.shape, 9.0)
    for i in range(len(path) - 1):
        d = np.minimum(d, seg(*path[i], *path[i + 1], widths[i], widths[i + 1]))
    c.paint(d - 0.03, hexc("#4A1A6E"))
    c.paint(d, hexc("#8A47B8"))
    c.paint(seg(-0.55, 0.52, 0.1, 0.3, 0.025, 0.008), hexc("#B98BDD"), 0.8)   # vệt sáng mảnh
    c.save(f"{name}_R.png")
    c.save(f"{name}_L.png", mirror=True)


def frieza_nose(name):
    """v26 mũi Frieza: hai lỗ mũi nhỏ xếch (vệt tím sẫm thon) + bóng mềm dưới sống mũi, không viền."""
    c = Canvas()
    soft = np.clip(1 - np.sqrt((X / 0.55) ** 2 + ((Y + 0.05) / 0.32) ** 2), 0, 1) ** 1.6
    c.paint(soft, hexc("#CDBFE6"), 0.6, sdf=False)
    for sx in (-1, 1):
        c.paint(seg(sx * 0.12, -0.02, sx * 0.3, 0.16, 0.06, 0.03), hexc("#4A2266"), 0.95)
    c.save(f"{name}.png")


def frieza_smirk(name):
    """Cười nhếch khinh khỉnh: môi tím sẫm, khoé phải nhếch cao, khoé trái ngắn chúc xuống; vệt môi dưới."""
    c = Canvas()
    f = lambda x: -0.18 + 0.22 * x + 0.32 * x * x
    xs_ = np.linspace(-0.62, 0.72, 25)
    d = np.full(X.shape, 9.0)
    for i in range(len(xs_) - 1):
        x0, x1 = xs_[i], xs_[i + 1]
        t0, t1 = i / 24, (i + 1) / 24
        w = lambda t: 0.03 + 0.06 * np.sin(np.pi * min(max(t * 1.1, 0), 1)) ** 0.8
        d = np.minimum(d, seg(x0, f(x0), x1, f(x1), w(t0), w(t1)))
    c.paint(d - 0.025, hexc("#1E0626"))
    c.paint(d, hexc("#3E1452"))
    c.paint(seg(0.72, f(0.72), 0.82, f(0.72) + 0.16, 0.035, 0.01), hexc("#1E0626"))   # khoé nhếch
    c.paint(seg(-0.62, f(-0.62), -0.72, f(-0.62) - 0.06, 0.03, 0.01), hexc("#1E0626"))
    # v22 môi tím sẫm đặc trưng của Frieza: môi dưới đầy đặn hình lưỡi liềm (trước chỉ một vệt mờ)
    lip = np.maximum(ell(0.06, -0.36, 0.42, 0.17), -(Y - (f(X) - 0.05)))
    c.paint(lip - 0.02, hexc("#2A0A36"))
    c.paint(lip, hexc("#5E2A80"))
    c.paint(ell(0.14, -0.33, 0.14, 0.04), hexc("#8A55AA"), 0.8)                      # ánh bóng nhỏ trên môi
    c.save(f"{name}.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    # Goku thường: tròng đen (không phải xám tím), mi trên hơi phẳng + xếch nhẹ, đuôi mi ngắn (không vẩy cong kiểu mắt
    # con gái) → mắt to thân thiện nhưng vẫn là mắt con trai như Goku FighterZ
    eye("goku_eye", "#050408", "#17151F", "#24222E", "#020203", "#010102", "#120C0B", glow="#3A3C50",
        lidcut=(0.5, 0.14), low=(-0.8, 0.0, 0.18), iris_r=(0.45, 0.6), lash_w=(0.04, 0.1), wing=0.07)
    eye("goku_eye_angry", "#050408", "#17151F", "#24222E", "#020203", "#010102", "#120C0B", glow="#3A3C50",
        lidcut=(0.26, 0.34), low=(-0.64, 0.06, 0.3), iris_r=(0.4, 0.54), pupil_r=(0.15, 0.21), iris_c=(0.0, -0.14),
        lash_w=(0.05, 0.12), wing=0.05)   # gồng Ki: mi trên xếch gắt + mi dưới nâng, tròng nhỏ lại → quyết liệt, không "lo lắng"
    # SSJ (FighterZ): xanh ngọc rực, mi trên cụp sắc che đỉnh tròng, mi dưới nâng — mắt hẹp, quyết tâm
    eye("goku_eye_ssj", "#033A3C", "#0B958E", "#5CF2D6", "#012325", "#021617", "#120C0B", glow="#C8FFF2",
        iris_r=(0.42, 0.58), pupil_r=(0.1, 0.15), iris_c=(0.03, -0.16), lidcut=(0.3, 0.22), low=(-0.7, 0.04, 0.32),
        lash_w=(0.04, 0.1), wing=0.1, hl=0.85)
    # SSJ khi đánh/hét: hẹp hơn nữa, tròng nhỏ, đồng tử như chấm
    eye("goku_eye_ssj_fierce", "#033A3C", "#0B958E", "#5CF2D6", "#012325", "#021617", "#120C0B", glow="#C8FFF2",
        iris_r=(0.34, 0.46), pupil_r=(0.07, 0.1), iris_c=(0.0, -0.17), lidcut=(0.14, 0.3), low=(-0.58, 0.1, 0.3),
        lash_w=(0.05, 0.11), wing=0.08, hl=0.75)
    frieza_eye("frieza_eye")
    frieza_eye("frieza_eye_shock", shock=True)
    frieza_eye("frieza_eye_angry", angry=True)
    frieza_eye_hit("frieza_eye_hit")
    frieza_cheek("frieza_cheek")
    c = Canvas(); c.paint(ell(0, 0, 0.55, 0.8), hexc("#4A2C5E")); c.paint(ell(0.05, -0.05, 0.3, 0.5), hexc("#24122F")); c.save("frieza_ear.png")
    eye_shut("goku_eye_shut", "#16100F")
    eye_blink("goku_eye_blink", "#16100F")
    frieza_blink("frieza_eye_blink")
    brow("goku_brow", "#16100F", bold=True)
    brow("goku_brow_ssj", "#E6AE24", angry=True, edge="#9A5A0A")   # vàng nghệ hợp tóc SSJ nhạt (trước nâu vàng)
    brow("goku_brow_angry", "#16100F", angry=True)
    mouth_smile("goku_mouth", "#5A1E1E")
    mouth_smile("goku_mouth_smirk", "#5A1E1E", smirk=True)
    anger_vein("anger")
    sweat_drop("sweat")
    frieza_smirk("frieza_mouth")
    frieza_nose("frieza_nose")
    mouth_open("goku_mouth_open", "#8A2232", "#2A0A0E", rim_w=0.05, deep="#2A060C",
               shape=np.maximum(ell(0.0, 0.0, 0.76, 0.86), Y - 0.55), teeth_y=0.38)
    mouth_grit("goku_mouth_grit", "#2A0A0E")
    goku_nose("goku_nose")
    mouth_open("frieza_mouth_open", "#6A1640", "#2A0A3A", rim_w=0.05, deep="#24061C", tongue="#D8587E")
    mouth_grit("frieza_mouth_snarl", "#2A0A3A", tilt=0.16, w=0.78, h=0.36, droop=0.22)
    wob = 0.06 * np.sin(X * 9.0)                   # Frieza trúng đòn: miệng há méo, mép trên gợn
    mouth_open("frieza_mouth_pain", "#6A1640", "#2A0A3A", rim_w=0.055, deep="#1E0418", tongue="#D8587E",
               shape=np.maximum(ell(0.06, -0.06, 0.8, 0.8, 0.12), Y - (0.46 + wob - 0.1 * X)), teeth_y=0.3)
    c = Canvas()                                   # Frieza cười khẩy "ho ho ho": nửa vầng trăng há, răng trên
    sh = np.maximum(ell(0.0, 0.3, 0.8, 0.75), Y - 0.3)
    c.paint(sh, hexc("#3B0F2A"))
    c.paint(np.maximum(sh, -(Y - 0.12)), hexc("#FFFFFF"))
    c.paint(ell(0.0, -0.32, 0.38, 0.16), hexc("#C9506E"), clip=cov(sh))
    c.paint(np.abs(sh) - 0.05, hexc("#2A0A3A"))
    c.save("frieza_mouth_laugh.png")
    blush("blush")
    c = Canvas()                                   # v17 Frieza: nét xương quai xanh (mực tím nhạt như múi bụng)
    tt = np.linspace(0, 1, 25)
    pts = [(0.1 + 0.82 * t, -0.12 + 0.24 * np.sin(np.pi * 0.62 * t) - 0.05 * t ** 3) for t in tt]
    wid = [0.005 + 0.024 * np.sin(np.pi * t) ** 0.7 for t in tt]
    d = np.full(X.shape, 9.0)
    for sgn in (1, -1):
        for (ax, ay), (bx, by), w0, w1 in zip(pts, pts[1:], wid, wid[1:]):
            d = np.minimum(d, seg(sgn * ax, ay, sgn * bx, by, w0, w1))
    c.paint(d, hexc("#A08ED2"))
    c.save("frieza_collar.png")
