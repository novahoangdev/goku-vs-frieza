import { useEffect, useRef, useState } from "react";
import { useSharedValue } from "react-native-reanimated";
import { Skia, type SkImage } from "react-native-skia";
import { createVideoPlayer, importDevice, type VideoPlayer } from "react-native-webgpu";

/**
 * Hardware video decode → texture on Skia's GPU device → SkImage, never touching the CPU.
 * `frame` is an image wrapping the texture (stable across frames); `videoTime` is the time of the frame last copied into it.
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
    p.loop = false; // defaults to true
    // muted in demo recordings: the promo clip takes audio straight from mix.wav; simulator playback only adds noise
    p.volume = process.env.EXPO_PUBLIC_DEMO === "1" ? 0 : 1;
    p.currentTime = 0; // still returns the first frame for the intro screen while paused
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
          // The SkImage wraps the texture directly (contents are read at draw time), so create it once per texture.
          // Creating a new image every frame and assigning it via a shared value from JS leaves the UI runtime holding thousands
          // of old images awaiting JS GC, and Hermes runs out of memory mid-film (the 29 s film crashed at ~20 s).
          frame.value = Skia.Image.MakeFromGPUTexture(texture);
        }
        // YUV → RGB on the GPU; the video is encoded in portrait, so no width/height swap is needed
        device.queue.copyExternalImageToTexture({ source: f, rotation: p.rotation }, { texture }, [
          f.width,
          f.height,
        ]);
        f.release(); // hand the buffer back to the decoder right away
        videoTime.value = p.currentTime; // uniform change → Canvas redraws with the new texture contents
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

  /** Plays from the start (or from `at` seconds). */
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
