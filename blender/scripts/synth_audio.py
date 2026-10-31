# Nhạc + tiếng động cho phim, tổng hợp bằng numpy (không dùng tài nguyên có bản quyền). v22: viết lại thành một
# bản nhạc phim kiểu anime chiến đấu, khớp từng nhịp hình: dàn dây + kèn đồng + đồng ca + timpani/taiko + trống dàn,
# vang (reverb) chung, nén/duck nhạc dưới tiếng động. Mọi mốc lấy từ timeline.json (marker, track, bản đồ retime).
#
#   mở màn bão (Rê thứ, dây trầm + đồng ca "ooh" + sấm) → gồng (timpani cuộn, dây tremolo dâng, riser) →
#   chớp SSJ (đánh nhịp + đảo cymbal) → BÙNG NỔ (hợp âm kèn Rê trưởng + đồng ca "aah") → chủ đề anh hùng (kèn) →
#   Frieza (dây thấp nghịch, kèn trầm tritone) → chiến đấu 150 BPM (trống dàn, bass móc, power chord, dây 16 nốt) →
#   lặng trước cú đấm → CÚ ĐẤM (stinger cả dàn, vang dài) → KAMEHAMEHA (v23: 4 nhịp "Ka–me–ha–me" dâng theo vòng
#   Dm–Bb–C–A trên tiếng khí ù dâng cao, lặng, "HA!" Rê trưởng cả dàn + tia gầm, nổ lớn) → kết anh hùng (kèn chủ đề
#   + hợp âm cuối + chuông title).
#
# Nhạc riêng: đặt render/audio/bgm.wav (tools/build.sh tự đổi mp3/m4a/flac → bgm.wav 48 kHz) thì dùng file đó làm
# nhạc nền thay phần nhạc tổng hợp (tiếng động vẫn tổng hợp, nhạc tự hạ khi có tiếng động lớn).
#
# Chạy bằng Python của Blender (có sẵn numpy):
#   Blender -b --factory-startup --python blender/scripts/synth_audio.py
import json, os, wave
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TL = json.load(open(os.path.join(ROOT, "app", "assets", "cinematic", "timeline.json")))
OUT = os.path.join(ROOT, "render", "audio", "mix.wav")
BGM = os.path.join(ROOT, "render", "audio", "bgm.wav")
SR, FPS = 48000, TL["fps"]
DUR = TL["frames"] / FPS
N = int(SR * DUR)
rng = np.random.default_rng(7)
RT = TL.get("retime", [[0, 0], [1200, 1200]])


def T(f_old):
    """frame của phim 20 s gốc → giây trong phim đã giãn nhịp"""
    for (a, na), (b, nb) in zip(RT, RT[1:]):
        if f_old <= b or [b, nb] == RT[-1]:
            return (na + (f_old - a) * (nb - na) / (b - a)) / FPS
    return f_old / FPS


markers = TL["markers"]
haptic = lambda style, lo=0, hi=1e9: [m["f"] / FPS for m in markers if m["name"] == f"haptic:{style}" and lo <= m["f"] / FPS < hi]
t_all = np.arange(N) / SR


def track(name):
    v = np.array(TL["tracks"][name])
    return np.interp(t_all, np.arange(len(v)) / FPS, v)


# ───────────────────────── DSP cơ bản ─────────────────────────
def band(x, lo, hi):
    """Lọc dải tần bằng FFT (mềm ở hai mép)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))


def env(n, a, d, shape=4.0):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-np.maximum(t - a, 0) * shape / max(d, 1e-4))


def adsr(n, a, r, sus=1.0):
    t = np.arange(n) / SR
    dur = n / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.clip((dur - t) / max(r, 1e-4), 0, 1) * sus


def noise(sec):
    return rng.standard_normal(int(sec * SR))


def sweep(f0, f1, sec, fn=np.sin):
    t = np.arange(int(sec * SR)) / SR
    ph = 2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / sec)) / SR
    return fn(ph)


def saw(ph):
    return 2 * ((ph / (2 * np.pi)) % 1) - 1


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


class Bus:
    def __init__(self):
        self.L = np.zeros(N)
        self.R = np.zeros(N)

    def put(self, sig, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        if i >= N or i + len(sig) <= 0:
            return
        s = sig * gain
        if i < 0:
            s, i = s[-i:], 0
        s = s[: N - i]
        self.L[i:i + len(s)] += s * np.sqrt((1 - pan) / 2) * 1.414
        self.R[i:i + len(s)] += s * np.sqrt((1 + pan) / 2) * 1.414

    def stereo(self):
        return np.stack([self.L, self.R], 1)


def reverb(x, sec=2.4, damp=5000, seed=1):
    """Vang hội trường: tích chập với nhiễu suy giảm theo hàm mũ (2 kênh khác nhau → rộng)."""
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = r.standard_normal(n) * np.exp(-t * 6.9 / sec)
        ir = band(ir, 120, damp)
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))      # pre-delay mềm
        ir /= np.sqrt((ir ** 2).sum())
        L = len(x) + n
        out[:, ch] = np.fft.irfft(np.fft.rfft(x[:, ch], L) * np.fft.rfft(ir, L), L)[: len(x)]
    return out


# ───────────────────────── nhạc cụ ─────────────────────────
def brass(midi, sec, vel=1.0):
    """Kèn đồng: cộng hưởng hài với độ sáng tăng theo attack (nổ "pah"), rung giọng sau 0.25 s."""
    n = int(sec * SR)
    t = np.arange(n) / SR
    f0 = hz(midi) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.25) / 0.3, 0, 1))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    bright = (0.25 + 0.6 * vel) * np.minimum(t / 0.07, 1) * (1 - 0.25 * np.clip((t - 0.1) / 0.6, 0, 1))
    x = np.zeros(n)
    for k in range(1, 18):
        if k * hz(midi) > 9000:
            break
        x += np.sin(k * ph) * bright ** (k - 1) / k ** 0.9
    return x * adsr(n, 0.035, 0.12) * vel / 3


def strings(midis, sec, att=0.25, rel=0.4, trem=0.0):
    """Dàn dây: siêu răng cưa nhiều bè lệch cent, tấn công chậm, lọc mềm; trem>0 → tremolo (Hz)."""
    n = int(sec * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in midis:
        for d in (-0.009, -0.004, 0.0, 0.005, 0.01):
            ph0 = rng.uniform(0, 6.28)
            x += saw(2 * np.pi * hz(m) * (1 + d) * t * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * t + ph0)) + ph0)
    x = band(x, 60, 3200) / (len(midis) * 5)
    e = adsr(n, att, rel)
    if trem:
        e = e * (0.55 + 0.45 * np.abs(np.sin(np.pi * trem * t)))
    return x * e


def choir(midis, sec, vowel="aah", att=0.6, rel=0.8):
    """Đồng ca: hài âm nhân phổ formant (aah / ooh), nhiều giọng lệch + rung giọng."""
    F = {"aah": ((730, 90), (1090, 110), (2440, 160)), "ooh": ((300, 60), (870, 90), (2240, 140))}[vowel]
    n = int(sec * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in midis:
        for v in range(3):
            f = hz(m) * (1 + rng.uniform(-0.006, 0.006))
            vib = 1 + 0.006 * np.sin(2 * np.pi * (5.0 + v * 0.4) * t + v)
            ph = 2 * np.pi * np.cumsum(f * vib) / SR
            for k in range(1, 40):
                fk = k * f
                if fk > 5000:
                    break
                w = sum(np.exp(-((fk - c) / bw) ** 2) for c, bw in F) + 0.02
                x += np.sin(k * ph) * w / k ** 0.3
    x = band(x, 100, 4500) / (len(midis) * 3 * 3)
    return x * adsr(n, att, rel)


def timpani(midi, sec=1.6, vel=1.0):
    n = int(sec * SR)
    t = np.arange(n) / SR
    f = hz(midi) * (1 + 0.04 * np.exp(-t * 25))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.35 * np.sin(1.5 * ph) + 0.2 * np.sin(1.98 * ph)
    x = x * env(n, 0.003, sec * 0.7, 3.5) + band(noise(sec), 60, 900) * env(n, 0.001, 0.08, 6) * 0.6
    return x * vel


def timp_roll(midi, sec, v0=0.1, v1=1.0):
    n = int(sec * SR)
    out = np.zeros(n + int(1.2 * SR))
    hits = np.arange(0, sec, 0.055)
    for h in hits:
        g = v0 + (v1 - v0) * (h / sec) ** 2
        s = timpani(midi, 1.0, g * rng.uniform(0.75, 1.0))
        i = int(h * SR)
        out[i:i + len(s)] += s[: len(out) - i] * 0.45
    return out


def taiko(sec=0.7, f0=95, vel=1.0):
    n = int(sec * SR)
    x = sweep(f0, f0 * 0.55, sec) * env(n, 0.002, sec * 0.6, 5) + band(noise(sec), 80, 1200) * env(n, 0.001, 0.05, 6) * 0.7
    return x * vel


def kick():
    n = int(0.35 * SR)
    return sweep(130, 42, 0.35) * env(n, 0.001, 0.3, 6) + band(noise(0.35), 1500, 7000) * env(n, 0.0005, 0.01, 8) * 0.4


def snare(vel=1.0):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 185 * t) * env(n, 0.001, 0.08, 6)
    return (body * 0.7 + band(noise(0.3), 1200, 9000) * env(n, 0.001, 0.18, 5)) * vel


def hat(open_=False):
    sec = 0.25 if open_ else 0.06
    return band(noise(sec), 7000, 16000) * env(int(sec * SR), 0.0005, sec * 0.8, 5)


def crash(sec=3.0, vel=1.0):
    n = int(sec * SR)
    x = band(noise(sec), 2500, 15000) * env(n, 0.002, sec * 0.8, 3.2)
    x += band(noise(sec), 400, 3000) * env(n, 0.001, 0.25, 5) * 0.5
    return x * vel


def rev_cymbal(sec=1.2):
    return crash(sec)[::-1] * np.linspace(0, 1, int(sec * SR)) ** 2


def riser(sec, f0=200, f1=3000):
    n = int(sec * SR)
    x = band(noise(sec), 300, 8000) * np.linspace(0, 1, n) ** 2.5
    x += sweep(f0, f1, sec, saw) * np.linspace(0, 1, n) ** 3 * 0.25
    return band(x, 150, 9000)


def bass(midi, sec, vel=1.0):
    n = int(sec * SR)
    t = np.arange(n) / SR
    x = saw(2 * np.pi * hz(midi) * t) + 0.6 * np.sin(2 * np.pi * hz(midi) * 0.5 * t)
    return band(np.tanh(x * 1.5), 30, 900) * adsr(n, 0.004, 0.03) * vel


def power(midi, sec, vel=1.0):
    """Power chord guitar méo (gốc + quãng 5 + quãng 8)."""
    n = int(sec * SR)
    t = np.arange(n) / SR
    x = sum(saw(2 * np.pi * hz(m) * (1 + d) * t) for m in (midi, midi + 7, midi + 12) for d in (-0.003, 0.003))
    x = band(np.tanh(x * 3.5), 80, 4200)
    return x * adsr(n, 0.004, 0.06) * vel * 0.35


# ───────────────────────── tiếng động ─────────────────────────
def whoosh(sec, lo, hi):
    x = noise(sec)
    out = np.zeros_like(x)
    seg = max(len(x) // 10, 1)
    for k in range(10):
        c = lo * (hi / lo) ** (k / 9)
        out[k * seg:(k + 1) * seg] = band(x, c * 0.6, c * 1.6)[k * seg:(k + 1) * seg]
    return out * np.sin(np.linspace(0, np.pi, len(x))) ** 2


def teleport():
    """"Shun!" dịch chuyển kiểu anime: vút cao rất nhanh + rung kim loại ngắn."""
    a = band(sweep(900, 5200, 0.12, saw), 600, 9000) * env(int(0.12 * SR), 0.003, 0.1, 3)
    b = whoosh(0.22, 1500, 7000)
    out = np.zeros(int(0.3 * SR)); out[: len(a)] += a * 0.5; out[: len(b)] += b
    return out


def punch(vel=1.0, big=False):
    sec = 1.4 if big else 0.6
    n = int(sec * SR)
    thump = sweep(150 if big else 180, 38, sec) * env(n, 0.001, sec * 0.6, 4)
    crack = band(noise(sec), 1200, 9000) * env(n, 0.0005, 0.04, 6)
    body = band(noise(sec), 120, 1500) * env(n, 0.001, 0.15 if big else 0.08, 5)
    return (thump * 1.1 + crack * 0.9 + body * 0.7) * vel


def explosion(sec=2.5, vel=1.0):
    n = int(sec * SR)
    low = band(noise(sec), 25, 300) * env(n, 0.01, sec * 0.7, 3)
    mid = band(noise(sec), 300, 4000) * env(n, 0.003, sec * 0.35, 4)
    sub = sweep(70, 25, sec) * env(n, 0.004, sec * 0.6, 3)
    deb = band(noise(sec), 2000, 9000) * (rng.random(n) < 0.004) * env(n, 0.2, sec * 0.8, 3) * 6
    return (low * 1.3 + mid * 0.8 + sub + deb) * vel


def beam_zap(sec=0.9):
    """Death Beam: tiếng rít điện chói, rè, tắt nhanh."""
    n = int(sec * SR)
    t = np.arange(n) / SR
    f = 1300 * (1 + 0.3 * np.exp(-t * 18))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.tanh(3 * (np.sin(ph) + 0.6 * saw(ph * 0.5))) * (0.6 + 0.4 * np.sin(2 * np.pi * 70 * t))
    x = band(x, 300, 8000) + band(noise(sec), 3000, 10000) * 0.4
    return x * env(n, 0.002, sec * 0.5, 4)


def charge(sec=0.6, f0=300, f1=1800):
    """Tụ khí: tiếng rít dâng + lách tách."""
    n = int(sec * SR)
    x = sweep(f0, f1, sec) * 0.6 + band(noise(sec), 2500, 9000) * (rng.random(n) < 0.03) * 3
    return x * np.linspace(0.1, 1, n) ** 2 * adsr(n, 0.02, 0.03)


# ───────────────────────── mốc thời gian (giây, phim đã giãn) ─────────────────────────
S_POWER, S_EYES, S_BOOM, S_SSJ = T(120), T(240), T(300), T(390)
S_FRIEZA, S_DODGE, S_COMBO, S_CHASE = T(510), T(600), T(690), T(780)
S_COUNTER, S_HIT, S_END = T(990), T(1030), T(1110)
mk_t = lambda name, d=None: next((m["f"] / FPS for m in markers if m["name"] == name), d)
K_S = mk_t("kame:start", S_END)                       # đoạn Kamehameha (không có: bản cũ, bỏ qua)
K_C, K_F, K_H = mk_t("kame:charge"), mk_t("kame:fire"), mk_t("kame:hit")
KAME = K_C is not None and K_F is not None and K_H is not None
music, sfx = Bus(), Bus()

# 1) Mở màn: Namek nổi giông — dây trầm Rê thứ + đồng ca "ooh" + timpani cuộn nhẹ
music.put(strings([38, 45, 50], S_POWER + 0.6, att=1.6, rel=0.8), 0.0, 0.55)
music.put(choir([50, 53, 57], S_POWER + 0.4, "ooh", att=1.8, rel=0.6), 0.6, 0.5)
music.put(timp_roll(38, 2.2, 0.05, 0.5), S_POWER - 2.3, 0.6)
music.put(taiko(1.2, 70, 1.0), 0.15, 0.8)
# 2) Gồng Ki: dây tremolo dâng theo vòng Dm–Bb–C–A, timpani cuộn lớn dần, đồng ca dâng, riser
seg = (S_EYES - S_POWER) / 4
for i, ch in enumerate(([50, 53, 57, 62], [46, 50, 53, 58], [48, 52, 55, 60], [45, 49, 52, 57])):
    music.put(strings(ch, seg + 0.3, att=0.15, rel=0.3, trem=12), S_POWER + i * seg, 0.45 + 0.12 * i)
    music.put(strings([ch[0] - 12], seg + 0.3, att=0.1, rel=0.3), S_POWER + i * seg, 0.5)
music.put(choir([62, 65, 69], S_EYES - S_POWER + 0.3, "aah", att=2.5, rel=0.3), S_POWER, 0.45)
music.put(timp_roll(38, S_EYES - S_POWER, 0.1, 0.9), S_POWER, 0.8)
# 3) Đôi mắt: 3 nhịp chớp SSJ = đánh dàn + đảo cymbal; dây cao rung dâng; riser vào cú nổ; lặng 0.12 s trước nổ
for f in haptic("rigid", S_EYES - 0.1, S_BOOM):
    music.put(taiko(0.9, 80, 1.0) + timpani(38, 0.9, 0.8)[: int(0.9 * SR)], f, 0.9)
    music.put(power(38, 0.35, 1.0), f, 0.5)
music.put(strings([74, 77, 81], S_BOOM - S_EYES, att=0.3, rel=0.05, trem=16), S_EYES, 0.5)
music.put(riser(S_BOOM - S_EYES - 0.12), S_EYES, 0.5)
music.put(rev_cymbal(min(1.4, S_BOOM - S_EYES - 0.12)), S_BOOM - 0.12 - min(1.4, S_BOOM - S_EYES - 0.12), 0.6)
# 4) BÙNG NỔ: hợp âm kèn Rê trưởng fortissimo + đồng ca + timpani + crash, rồi chủ đề anh hùng (kèn) trên dây
music.put(crash(4.0, 1.0), S_BOOM, 0.9)
music.put(timpani(38, 2.5, 1.0), S_BOOM, 1.0)
for m in (50, 57, 62, 66, 69):
    music.put(brass(m, 2.6, 1.0), S_BOOM, 0.55)
music.put(choir([62, 66, 69, 74], 3.0, "aah", att=0.08, rel=1.2), S_BOOM, 0.75)
BEAT = 60 / 112
t0 = S_BOOM + 2.2
theme = [(0, 1.5, 69), (1.5, 0.5, 74), (2, 2, 78), (4, 1, 76), (5, 1, 74), (6, 1, 73), (7, 1, 74), (8, 3, 76)]
for b, d, m in theme:
    if t0 + b * BEAT < S_FRIEZA - 0.2:
        music.put(brass(m, min(d * BEAT + 0.1, S_FRIEZA - t0 - b * BEAT), 0.85), t0 + b * BEAT, 0.65, -0.15)
        music.put(brass(m - 12, min(d * BEAT + 0.1, S_FRIEZA - t0 - b * BEAT), 0.6), t0 + b * BEAT, 0.35, 0.15)
for i, ch in enumerate(([50, 57, 62, 66], [43, 55, 59, 62], [45, 57, 61, 64], [50, 57, 62, 66])):
    st = t0 + i * 2 * BEAT
    if st < S_FRIEZA:
        music.put(strings(ch, min(2 * BEAT + 0.4, S_FRIEZA - st + 0.2), att=0.2, rel=0.35), st, 0.55)
        music.put(timpani(ch[0], 1.0, 0.6), st, 0.6)
music.put(strings([50, 57, 62], t0 - S_BOOM, att=0.4, rel=0.4), S_BOOM + 0.3, 0.45)
# 5) Frieza: dây trầm Si giáng thứ tremolo + kèn trầm quãng tritone (đe doạ) + pizzicato
music.put(strings([34, 41, 46, 49], S_DODGE - S_FRIEZA + 0.3, att=0.3, rel=0.3, trem=9), S_FRIEZA, 0.6)
music.put(brass(34, S_DODGE - S_FRIEZA, 0.7) + brass(40, S_DODGE - S_FRIEZA, 0.6), S_FRIEZA + 0.2, 0.5)
for k, m in enumerate((58, 61, 58, 64, 58, 61, 65, 64)):
    at = S_FRIEZA + 0.3 + k * 0.45
    if at < S_DODGE - 0.2:
        music.put(strings([m], 0.22, att=0.004, rel=0.18), at, 0.5, 0.3)
# 6) Chiến đấu 150 BPM: Dm–Bb–C–A, trống dàn, bass móc 16 nốt, power chord, dây 16 nốt, kèn đánh nhấn
BPM = 150
B = 60 / BPM
prog = [50, 46, 48, 45]
bassline = [0, 0, 12, 0, 0, 12, 0, 7, 0, 0, 12, 0, 7, 0, 12, 7]   # chỉ gốc / quãng 5 / quãng 8: hợp mọi hợp âm
t = S_DODGE
bar = 0
while t < S_COUNTER - 0.05:
    root = prog[bar % 4]
    for s in range(16):
        st = t + s * B / 4
        if st >= S_COUNTER:
            break
        music.put(bass(root - 12 + bassline[s], B / 4 * 0.95, 0.9), st, 0.55)
        music.put(hat(open_=(s % 8 == 6)), st, 0.18 if s % 2 else 0.28, 0.35)
        if s in (0, 6, 8, 11):
            music.put(kick(), st, 0.95)
        if s in (4, 12):
            music.put(snare(), st, 0.7, -0.1)
    music.put(power(root - 12, 1.5 * B, 1.0), t, 0.55, -0.4)
    music.put(power(root - 12, 1.0 * B, 0.9), t + 1.5 * B, 0.45, -0.4)
    music.put(power(root - 12, 1.5 * B, 1.0), t + 2.5 * B, 0.5, -0.4)
    chord = [root + 12, root + 12 + (3 if root == 50 else 4), root + 19]   # Rê thứ, các hợp âm còn lại trưởng
    music.put(strings(chord, 4 * B + 0.15, att=0.02, rel=0.1, trem=BPM / 60 * 4), t, 0.5, 0.35)
    if bar % 2 == 1:                                            # đoạn fill tom cuối mỗi 2 nhịp
        for k in range(4):
            music.put(taiko(0.4, 140 - k * 18, 0.8), t + 3 * B + k * B / 4, 0.55, 0.3 - k * 0.2)
    t += 4 * B
    bar += 1
for at in haptic("rigid", S_COMBO, S_CHASE) + haptic("medium"):
    for m in (62, 65, 69):
        music.put(brass(m, 0.45, 1.0), at, 0.4)
    music.put(crash(1.8, 0.7), at, 0.4)
# 7) Phản đòn: rút trống, dây cao rung + riser, lặng hẳn 0.3 s trước cú đấm
music.put(strings([74, 81, 86], S_HIT - S_COUNTER, att=0.2, rel=0.05, trem=18), S_COUNTER, 0.55)
music.put(strings([38], S_HIT - S_COUNTER, att=0.3, rel=0.05), S_COUNTER, 0.6)
music.put(riser(S_HIT - S_COUNTER - 0.3, 150, 4000), S_COUNTER, 0.6)
# 8) CÚ ĐẤM: stinger cả dàn + crash + timpani, vang dài theo slow-mo
music.put(crash(5.0, 1.0), S_HIT, 1.0)
music.put(timpani(38, 3.0, 1.0), S_HIT, 1.0)
for m in (38, 45, 50, 57, 62, 65):
    music.put(brass(m, 1.2, 1.0), S_HIT, 0.5)
music.put(choir([62, 65, 69, 74], 2.0, "aah", att=0.05, rel=1.4), S_HIT, 0.6)
music.put(strings([50, 57, 62, 65], K_S - S_HIT + 0.5, att=0.6, rel=0.8), S_HIT + 0.6, 0.35)
# 8b) KAMEHAMEHA: nền Rê trầm + dây tremolo dâng + đồng ca phồng; 4 nhịp "Ka–me–ha–me" (taiko + kèn trầm + hợp âm
#     dâng Dm → Bb → C → A), riser vào "HA!"; HA = Rê trưởng cả dàn + crash; tia: kèn giữ âm + dây cao; trúng: stinger 2
if KAME:
    ch_len = K_F - K_C
    music.put(strings([38, 45], K_F - K_S, att=0.8, rel=0.1), K_S, 0.5)
    music.put(strings([62, 69, 74], ch_len, att=ch_len * 0.8, rel=0.05, trem=14), K_C, 0.5)
    music.put(choir([50, 57, 62], ch_len, "ooh", att=ch_len * 0.7, rel=0.1), K_C, 0.45)
    music.put(timp_roll(38, ch_len - 0.2, 0.05, 1.0), K_C, 0.55)
    stabs = [(0.0, [38, 50, 53, 57]), (0.27, [34, 46, 50, 53]), (0.52, [36, 48, 52, 55]), (0.74, [33, 45, 49, 52])]
    for frac, chord in stabs:
        at = K_C + frac * ch_len
        music.put(taiko(0.9, 85, 1.0), at, 0.9)
        for m in chord:
            music.put(brass(m + 12, 0.55, 0.9), at, 0.32)
        music.put(choir([m + 24 for m in chord[1:]], 0.7, "aah", att=0.04, rel=0.5), at, 0.35)
    music.put(riser(ch_len * 0.3, 200, 5000), K_F - ch_len * 0.3 - 0.12, 0.6)
    music.put(rev_cymbal(1.0), K_F - 1.0, 0.6)
    music.put(crash(4.0, 1.0), K_F, 1.0)
    music.put(timpani(38, 2.5, 1.0), K_F, 1.0)
    for m in (38, 50, 57, 62, 66, 69):
        music.put(brass(m, K_H - K_F + 0.3, 1.0), K_F, 0.42)
    music.put(choir([62, 66, 69, 74], K_H - K_F + 0.4, "aah", att=0.03, rel=0.6), K_F, 0.6)
    music.put(strings([74, 78, 81, 86], K_H - K_F, att=0.05, rel=0.3, trem=20), K_F, 0.5)
    music.put(crash(5.0, 1.0), K_H, 1.0)
    music.put(timpani(38, 3.0, 1.0), K_H, 1.0)
    for m in (38, 45, 50, 57, 62, 64, 69):
        music.put(brass(m, 1.4, 1.0), K_H, 0.45)
    music.put(strings([50, 57, 62, 69], S_END - K_H + 0.6, att=0.4, rel=0.6), K_H + 0.5, 0.4)
# 9) Kết: kèn chủ đề anh hùng nhắc lại (vào từ cuối đoạn vang cú đấm) → hợp âm Rê trưởng cuối giữ tới hết phim
BEAT = 0.42
t0 = S_END + 0.05 if KAME else S_END - 4 * BEAT + 0.3      # có Kamehameha: kèn vào đúng cut sang shot kết
fan = [(0, 1, 69), (1, 1, 74), (2, 1, 78), (3, 1.2, 76)]
for b, d, m in fan:
    music.put(brass(m, d * BEAT + 0.12, 0.95), t0 + b * BEAT, 0.6)
    music.put(brass(m - 12, d * BEAT + 0.12, 0.7), t0 + b * BEAT, 0.32)
for i, ch in enumerate(([43, 55, 59, 62], [45, 57, 61, 64])):
    music.put(strings(ch, 2 * BEAT + 0.3, att=0.12, rel=0.3), t0 + i * 2 * BEAT, 0.55)
fin = t0 + 4 * BEAT + 0.05
music.put(timp_roll(38, 4 * BEAT, 0.1, 0.9), t0, 0.7)
music.put(crash(4.0, 0.9), fin, 0.8)
hold = max(0.8, DUR - fin + 0.2)
for m in (38, 50, 57, 62, 66, 69, 74):
    music.put(brass(m, hold, 0.9), fin, 0.4)
music.put(choir([62, 66, 69, 74], hold, "aah", att=0.1, rel=1.0), fin, 0.7)
music.put(strings([50, 57, 62, 66, 74], hold, att=0.1, rel=1.0), fin, 0.55)
music.put(timpani(38, 2.0, 1.0), fin, 0.9)

# ───────────────────────── tiếng động theo hình ─────────────────────────
# gió + sấm (theo track lightning: mỗi lần chớp → sấm sau ~0.3 s)
w = band(noise(S_POWER + 1.5), 200, 1800)
# v27 gió theo đúng cơn giật làm cỏ dập dềnh (cùng công thức với shape key "storm" trong secondary.py, frame gốc)
fo = np.interp(np.arange(len(w)) / SR * FPS, [b for a_, b in RT], [a_ for a_, b in RT])
gust = 0.5 + 0.3 * np.sin(fo * 0.11) + 0.2 * np.sin(fo * 0.37 + 1.3)
sfx.put(w * adsr(len(w), 1.0, 1.2) * (0.55 + 0.75 * gust), 0.0, 0.06)
# v30 cỏ + lá xào xạc theo cơn giật (cùng gust với cỏ/cây/lá bay): lạo xạo cao tần, chỉ rõ khi giật mạnh; giông dịu sau
# nổ biến hình (frame gốc 296) nên tiếng xào xạc nhỏ dần
storm_a = np.clip(1.0 - (fo - 240) / 300, 0.25, 1.0)
rus = band(noise(len(w) / SR), 3000, 9000) * (0.4 + 0.6 * (rng.random(len(w)) < 0.08))
sfx.put(rus * np.clip(gust - 0.45, 0, None) ** 1.5 * storm_a * adsr(len(w), 1.0, 1.2), 0.0, 0.05)
lt = track("lightning")
on = np.flatnonzero((lt[1:] > 0.5) & (lt[:-1] <= 0.5)) / SR
for at in on[:8]:
    th = band(noise(2.6), 25, 500) * env(int(2.6 * SR), 0.03, 2.0, 3)
    th[: int(0.25 * SR)] += band(noise(0.25), 1500, 8000) * env(int(0.25 * SR), 0.001, 0.08, 5) * 0.5   # tiếng nứt đầu sấm
    sfx.put(th, at + 0.05, 0.5, rng.uniform(-0.6, 0.6))
# v27 sấm theo từng tia sét app vẽ (cùng lịch: mỗi 0.32 s, seed theo cut, hash như timeline.ts): ~1/3 số tia có tiếng
# rền xa vọng lại sau 0.4–1.1 s (sét ở xa), nhỏ hơn tiếng sấm chính
CUT_F = [0] + [m["f"] for m in markers if m["name"] == "cut"]
jhash = lambda x: (np.sin(x * 127.1 + 311.7) * 43758.5453) % 1.0
n_b = 0
for i in range(int(DUR / 0.32)):
    tt = i * 0.32
    seed = np.floor(tt / 0.32) + max(c for c in CUT_F if c <= tt * FPS) * 0.37
    k = lt[min(int(tt * SR), len(lt) - 1)]
    if jhash(seed * 3.1) > k or jhash(seed * 5.7) > 0.36:
        continue
    d = 0.4 + 0.7 * jhash(seed * 9.3)
    n = int(1.8 * SR)
    rum = band(noise(1.8), 30, 380) * env(n, 0.06, 1.5, 3)
    sfx.put(rum, tt + d, 0.16 + 0.12 * jhash(seed * 2.2), rng.uniform(-0.7, 0.7))
    n_b += 1
print("THUNDER bolts", n_b)
# rung đất lúc gồng: rumble liên tục + đá lăn lách tách theo haptic light
rb_len = S_BOOM - S_POWER
rb = band(np.cumsum(noise(rb_len)) / 300, 20, 160) * np.linspace(0.2, 1.0, int(rb_len * SR)) ** 2
sfx.put(rb, S_POWER, 0.9)
for at in haptic("light", S_POWER, S_EYES)[::3]:
    sfx.put(band(noise(0.08), 1500, 6000) * env(int(0.08 * SR), 0.001, 0.05, 5), at, 0.2, rng.uniform(-0.7, 0.7))
for at in haptic("rigid", S_EYES - 0.1, S_BOOM):                       # chớp SSJ: tia điện
    z = band(noise(0.35), 2000, 10000) * (rng.random(int(0.35 * SR)) < 0.08) * env(int(0.35 * SR), 0.001, 0.25, 4) * 4
    sfx.put(z + sweep(500, 2400, 0.35) * env(int(0.35 * SR), 0.002, 0.3, 4) * 0.4, at, 0.5)
# nổ biến hình
sfx.put(explosion(4.0, 1.2), S_BOOM, 1.0)
sfx.put(sweep(90, 26, 3.0) * env(int(3.0 * SR), 0.005, 2.6, 2.5), S_BOOM, 0.9)
# aura: tiếng lửa khí cháy rừng rực + ù trầm theo track aura
aura = track("aura")
roar = band(noise(DUR), 150, 1400) * (0.65 + 0.35 * np.sin(2 * np.pi * 9 * t_all) * np.sin(2 * np.pi * 2.3 * t_all))
hum = np.sin(2 * np.pi * 73.4 * t_all) + 0.5 * np.sin(2 * np.pi * 110 * t_all)
crk = band(rng.standard_normal(N), 2500, 9000) * (rng.random(N) < 0.012) * 3
a_sig = (roar * 0.6 + hum * 0.35 + crk) * np.clip(aura, 0, 2)
sfx.L += a_sig * 0.08
sfx.R += a_sig * 0.08
# Death Beam: tụ khí + rít chói (pan trái phải xen kẽ)
for i, at in enumerate(haptic("light", S_FRIEZA, S_COMBO)):
    sfx.put(charge(0.35, 600, 2400), at - 0.35, 0.25)
    sfx.put(beam_zap(0.8), at, 0.45, -0.45 if i % 2 else 0.45)
# né: "shun" dịch chuyển
for at in haptic("soft"):
    sfx.put(teleport(), at - 0.06, 0.55, rng.uniform(-0.3, 0.3))
# combo: đấm + vút
for at in haptic("rigid", S_COMBO, S_CHASE):
    sfx.put(whoosh(0.25, 600, 4000), at - 0.22, 0.5)
    sfx.put(punch(1.0), at, 0.9)
# bay rượt: gió lùa theo track speedlines
sp = track("speedlines")
wind = band(noise(DUR), 250, 3000) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t_all))
sfx.L += wind * np.clip(sp, 0, 1) * 0.12
sfx.R += np.roll(wind, 900) * np.clip(sp, 0, 1) * 0.12
# ki blast + nổ
for at in haptic("medium"):
    sfx.put(charge(0.3, 800, 3000), at - 0.32, 0.3)
    sfx.put(explosion(2.6, 1.0), at, 0.9, rng.uniform(-0.5, 0.5))
# cú đấm cuối: vút dài + 3 cú dồn
sfx.put(whoosh(0.5, 300, 5000), S_HIT - 0.45, 0.6)
for k, at in enumerate(haptic("heavy", S_HIT - 0.05, K_S)):
    sfx.put(punch(1.2 if k == 0 else 0.8, big=(k == 0)), at, 1.1 if k == 0 else 0.7)
sfx.put(explosion(3.5, 0.9), S_HIT, 0.7)
# Kamehameha: khí ù dâng (cao độ + độ dày tăng dần) + điện lách tách dày dần → "HA!" (bùm trầm + xé gió) →
# tia gầm suốt lúc bắn → nổ cực lớn khi trúng
if KAME:
    ln = K_F - K_C
    n = int(ln * SR)
    tt = np.arange(n) / SR
    f = 110 * 2 ** (1.6 * (tt / ln) ** 1.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    hum_k = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * saw(ph * 3) * (tt / ln)) * (0.25 + 0.75 * (tt / ln) ** 2)
    zap = band(noise(ln), 2500, 10000) * (rng.random(n) < 0.004 + 0.05 * (tt / ln) ** 2) * 3
    sfx.put(hum_k * 0.55 + zap, K_C, 0.6)
    sfx.put(charge(1.2, 500, 3200), K_F - 1.25, 0.35)
    sfx.put(sweep(95, 28, 2.5) * env(int(2.5 * SR), 0.003, 2.0, 2.5), K_F, 1.0)
    sfx.put(band(noise(0.6), 400, 9000) * env(int(0.6 * SR), 0.002, 0.4, 3), K_F, 0.7)
    bl = K_H - K_F + 1.4
    nb = int(bl * SR)
    tb = np.arange(nb) / SR
    roar_k = band(noise(bl), 90, 2600) * (0.75 + 0.25 * np.sin(2 * np.pi * 11 * tb))
    whine = np.sin(2 * np.pi * np.cumsum(1500 + 120 * np.sin(2 * np.pi * 6 * tb)) / SR) * 0.15
    sfx.put((roar_k + whine) * adsr(nb, 0.03, 0.9), K_F + 0.02, 0.55)
    sfx.put(explosion(5.0, 1.3), K_H, 1.1)
    sfx.put(sweep(80, 22, 4.0) * env(int(4.0 * SR), 0.004, 3.4, 2.5), K_H, 1.0)
    # v25 nước: bọt nước bắn lách tách + sóng vỗ trầm dưới chân lúc tụ khí (dày dần), xé nước lúc bắn,
    # vụ nổ chạm mặt biển → ầm nước đổ + mưa giọt rơi lộp độp
    lw = K_F - K_S
    nw = int(lw * SR)
    tw = np.arange(nw) / SR
    grow = np.clip((tw - (K_C - K_S)) / max(K_F - K_C, 0.1), 0, 1)
    spray = band(noise(lw), 1800, 9000) * (rng.random(nw) < 0.0015 + 0.02 * grow ** 1.5) * 2.2
    lap = band(noise(lw), 70, 420) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.6 * tw))) * (0.12 + 0.88 * grow)
    sfx.put(band(spray, 1500, 9000) * 0.6 + lap * 0.5, K_S, 0.26)
    sfx.put(band(noise(1.4), 300, 6000) * env(int(1.4 * SR), 0.01, 1.1, 3), K_F + 0.05, 0.4)
    sfx.put(band(noise(3.0), 150, 7000) * env(int(3.0 * SR), 0.008, 2.4, 2.2), K_H + 0.05, 0.6)
    nr = int(2.6 * SR)
    rain = band(noise(2.6), 2000, 8000) * (rng.random(nr) < 0.006) * 2.5 * env(nr, 0.3, 2.2, 2)
    sfx.put(rain, K_H + 0.6, 0.3)
# v30 Death Beam trượt Goku trúng đất phía sau (marker sfx:pop): tiếng nổ đất nhỏ — bục trầm + rào rào đất rơi
for at in (m["f"] / FPS for m in markers if m["name"] == "sfx:pop"):
    n = int(0.9 * SR)
    bang = band(noise(0.9), 60, 1800) * env(n, 0.002, 0.35, 3.5)
    grit = band(noise(0.9), 2500, 8000) * (rng.random(n) < 0.01) * 2.0 * env(n, 0.15, 0.7, 2)
    sfx.put(bang + grit * 0.5, at, 0.32 + 0.08 * rng.random(), rng.uniform(-0.4, 0.4))
# v27 giọt nước lớn bị vụ nổ kame hất lên rơi lại xuống biển: tiếng tõm ngắn đúng frame chạm nước (marker sfx:plop)
for at in (m["f"] / FPS for m in markers if m["name"] == "sfx:plop"):
    n = int(0.18 * SR)
    tt = np.arange(n) / SR
    f0 = 380 + 260 * rng.random()
    blip = np.sin(2 * np.pi * (f0 + 900 * tt) * tt) * env(n, 0.001, 0.07, 5)     # bọt khí ngân lên kiểu "bloop"
    sfx.put(band(noise(0.18), 900, 6000) * env(n, 0.001, 0.05, 6) * 0.6 + blip * 0.5, at, 0.12 + 0.1 * rng.random(),
            rng.uniform(-0.7, 0.7))
# v26 đá vụn biến hình chạm đất: tiếng bịch trầm + lạo xạo nhỏ đúng frame mô phỏng (marker sfx:thud), mỗi hòn một âm sắc
for i, at in enumerate(m["f"] / FPS for m in markers if m["name"] == "sfx:thud"):
    n = int(0.3 * SR)
    th = band(noise(0.3), 45 + 25 * rng.random(), 500) * env(n, 0.002, 0.16, 4)
    cr = band(noise(0.3), 1400, 5000) * env(n, 0.001, 0.04, 6) * 0.35
    sfx.put(th + cr, at, 0.45 + 0.3 * rng.random(), rng.uniform(-0.6, 0.6))
# cột nước + chuông title
sfx.put(band(noise(1.8), 400, 9000) * env(int(1.8 * SR), 0.01, 1.4, 3), T(1150), 0.45, 0.3)
title = next((m["f"] / FPS for m in markers if m["name"] == "haptic:success"), DUR - 1.2)
for f, g in ((1174.7, 0.22), (1760.0, 0.16), (2349.3, 0.1), (2637.0, 0.07)):
    n = int(2.4 * SR)
    sfx.put(np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, 0.003, 2.2, 3), title, g, 0.2)

# ───────────────────────── trộn ─────────────────────────
mus = music.stereo()
if os.path.exists(BGM):                                         # nhạc người dùng thay phần nhạc tổng hợp
    with wave.open(BGM) as w_:
        raw = np.frombuffer(w_.readframes(w_.getnframes()), "<i2").astype(float) / 32768
        ch = w_.getnchannels()
    raw = raw.reshape(-1, ch)[:, :2] if ch > 1 else np.repeat(raw[:, None], 2, 1)
    mus = np.zeros((N, 2))
    mus[: min(N, len(raw))] = raw[:N] * 0.8
    print("BGM", BGM)
mus = mus * 0.82 + reverb(mus, 2.6, 6000, 1) * 0.35
fx = sfx.stereo()
fx = fx + reverb(fx, 1.6, 7000, 2) * 0.18
# duck: nhạc hạ xuống khi tiếng động lớn (bao năng lượng tiếng động, mượt 120 ms)
e = np.abs(fx).max(1)
k = int(0.12 * SR)
e = np.convolve(e, np.ones(k) / k, "same")
duck = 1 - 0.55 * np.clip(e / (np.percentile(e, 99) + 1e-6), 0, 1)
# nhạc chuẩn theo RMS (không theo đỉnh) → đoạn chiến đấu không lấn cú nổ / cú đấm; tiếng động giữ đỉnh lớn
mus_n = mus / (np.sqrt((mus ** 2).mean()) + 1e-9) * 0.05
# tiếng động nén mềm: cú nổ biến hình không còn quá to so với cú đấm / tia / dịch chuyển (trước bị chuẩn theo nó)
fx_n = fx / (np.percentile(np.abs(fx), 99.97) + 1e-6)
fx_n = np.tanh(fx_n * 0.9) * 0.75
mix = mus_n * duck[:, None] + fx_n
# lặng hẳn ngay trước cú đấm (nín thở) rồi bùng; Kamehameha cũng nín một nhịp ngắn trước "HA!"
for hit_at, gap in ((S_HIT, 0.3),) + (((K_F, 0.16),) if KAME else ()):
    i0, i1 = int((hit_at - gap) * SR), int(hit_at * SR)
    mix[i0:i1] *= np.linspace(1, 0.06, i1 - i0)[:, None]
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix *= 0.9 / max(np.abs(mix).max(), 1e-6)
fade = np.minimum(np.minimum(np.arange(N) / (0.05 * SR), 1), np.minimum((N - np.arange(N)) / (0.6 * SR), 1))
mix *= fade[:, None]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "wb") as w_:
    w_.setnchannels(2)
    w_.setsampwidth(2)
    w_.setframerate(SR)
    w_.writeframes((mix * 32767).astype("<i2").tobytes())
print("AUDIO", OUT, f"{DUR:.1f}s")
