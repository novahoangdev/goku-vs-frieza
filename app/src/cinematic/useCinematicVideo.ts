import { useEffect, useRef, useState } from "react";
import { useSharedValue } from "react-native-reanimated";
import { Skia, type SkImage } from "react-native-skia";
import { createVideoPlayer, importDevice, type VideoPlayer } from "react-native-webgpu";

/**
 * Decode video bằng phần cứng → texture trên GPU device của Skia → SkImage, không đi qua CPU.
 * `frame` là ảnh bọc texture (giữ nguyên giữa các frame); `videoTime` là thời gian của frame vừa chép vào texture.
 */
export function useCinematicVideo(uri: string | null) {
  const frame = useSharedValue<SkImage | null>(null);
  const videoTime = useSharedValue(0);
  const player = useRef<VideoPlayer | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!uri) return;
    const device = importDevice(Skia.getNativeDevice());
    const p = createVideoPlayer(uri);
    p.loop = false; // mặc định là true
    // bản quay demo tắt tiếng: clip promo lấy tiếng thẳng từ mix.wav, tiếng phát trong simulator chỉ gây ồn
    p.volume = process.env.EXPO_PUBLIC_DEMO === "1" ? 0 : 1;
    p.currentTime = 0; // đang pause vẫn trả về frame đầu cho màn intro
    player.current = p;

    let texture: GPUTexture | null = null;
    let raf = 0;
    let first = true;
    const pump = () => {
      const f = p.copyLatestFrame();
      if (f) {
        if (!texture || texture.width !== f.width || texture.height !== f.height) {
          const old = frame.value;
          frame.value = null;
          old?.dispose();
          texture?.destroy();
          texture = device.createTexture({
            size: [f.width, f.height],
            format: navigator.gpu.getPreferredCanvasFormat(),
            usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING,
          });
          // SkImage bọc thẳng texture (đọc nội dung lúc vẽ) nên chỉ tạo một lần cho mỗi texture.
          // Tạo ảnh mới mỗi frame rồi gán qua shared value từ JS thì UI runtime giữ hàng nghìn ảnh cũ
          // chờ GC bên JS và Hermes hết bộ nhớ giữa phim (phim 29 s crash ở giây ~20).
          frame.value = Skia.Image.MakeFromGPUTexture(texture);
        }
        // YUV → RGB làm trên GPU; video encode đứng sẵn nên không cần đảo rộng/cao
        device.queue.copyExternalImageToTexture({ source: f, rotation: p.rotation }, { texture }, [
          f.width,
          f.height,
        ]);
        f.release(); // trả buffer cho decoder ngay
        videoTime.value = p.currentTime; // đổi uniform → Canvas vẽ lại với nội dung texture mới
        if (first) {
          first = false;
          setReady(true);
        }
      }
      raf = requestAnimationFrame(pump);
    };
    raf = requestAnimationFrame(pump);

    return () => {
      cancelAnimationFrame(raf);
      p.release();
      player.current = null;
      const last = frame.value;
      frame.value = null;
      last?.dispose();
      texture?.destroy();
    };
  }, [uri, frame, videoTime]);

  /** Chạy từ đầu (hoặc từ `at` giây). */
  const play = (at = 0) => {
    const p = player.current;
    if (!p) return;
    p.currentTime = at;
    p.play();
  };
  const seek = (sec: number) => {
    const p = player.current;
    if (!p) return;
    p.currentTime = sec;
    videoTime.set(sec);
  };

  return { frame, videoTime, ready, play, seek };
}
