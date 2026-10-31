import React, { useEffect, useState } from "react";
import { Image as RNImage, Pressable, StyleSheet, Text, View } from "react-native";
import { useAssets } from "expo-asset";
import { Canvas, Fill, Group, ImageShader, Shader, useCanvasSize } from "react-native-skia";
import Animated, { useAnimatedStyle, useDerivedValue, useSharedValue, withTiming } from "react-native-reanimated";
import { composite } from "../cinematic/shaders/composite";
import { overlay } from "../cinematic/shaders/overlay";
import { useCinematicVideo } from "../cinematic/useCinematicVideo";
import { useCinematicClock } from "../cinematic/useCinematicClock";
import { useFxUniforms } from "../cinematic/useFxUniforms";
import { Sparks } from "../cinematic/layers/Sparks";
import { TitleCard } from "../cinematic/layers/TitleCard";
import { n1 } from "../cinematic/timeline";
import { KiChargeIntro } from "../ui/KiChargeIntro";
import { Scrubber } from "../dev/Scrubber";

type Phase = "intro" | "playing" | "ended";

/** EXPO_PUBLIC_DEMO=1: bản quay clip demo, tự gồng Ki, ẩn công cụ dev. */
const DEMO = process.env.EXPO_PUBLIC_DEMO === "1";

export function CinematicScreen() {
  const [assets] = useAssets([require("../../assets/cinematic/cinematic.mp4")]);
  const uri = assets?.[0]?.localUri ?? null;
  const { frame, videoTime, ready, play, seek } = useCinematicVideo(uri);
  const { size, onLayout } = useCanvasSize();
  const [phase, setPhase] = useState<Phase>("intro");
  const playing = useSharedValue(false);
  const charge = useSharedValue(0);
  // poster (khung anh hùng cuối phim) che màn hình từ lúc mở app tới khi phim chạy (video chưa giải mã xong thì
  // Canvas còn đen), tối dần theo `charge` giống lớp dim, rồi mờ đi khi phim bắt đầu
  const posterA = useSharedValue(1);
  const posterStyle = useAnimatedStyle(() => {
    const a = charge.value * charge.value * 7;          // rung theo lực gồng, giống Canvas
    return {
      opacity: posterA.value,
      transform: [{ translateX: a * n1(Date.now() / 30) }, { translateY: a * n1(Date.now() / 30 + 9) }, { scale: 1.04 }],
    };
  });
  const posterDim = useAnimatedStyle(() => ({ opacity: 0.45 - charge.value * 0.3 }));

  const t = useCinematicClock(videoTime, playing, () => setPhase("ended"));
  const { cam, composite: cu, overlay: ou } = useFxUniforms(t, videoTime, size);

  const start = (at = 0) => {
    play(at);
    playing.set(true);
    posterA.set(withTiming(0, { duration: 420 }));
    setPhase("playing");
  };
  const replay = () => {
    charge.set(0);
    start();
  };

  // Chỉ bản dev: EXPO_PUBLIC_AUTOPLAY=1 bỏ qua màn gồng Ki, EXPO_PUBLIC_START_AT=<giây> chạy từ giữa phim
  useEffect(() => {
    if (!__DEV__ || !ready || process.env.EXPO_PUBLIC_AUTOPLAY !== "1") return;
    const id = requestAnimationFrame(() => start(Number(process.env.EXPO_PUBLIC_START_AT ?? 0)));
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  // Lúc gồng Ki: màn hình rung và tối dần theo `charge`
  const introShake = useDerivedValue(() => {
    const c = playing.get() ? 0 : charge.get();
    const a = c * c * 7;
    return [{ translateX: a * n1(Date.now() / 30) }, { translateY: a * n1(Date.now() / 30 + 9) }];
  });
  const introDim = useDerivedValue(() => (playing.get() || phase !== "intro" ? 0 : 0.45 - charge.get() * 0.3));

  return (
    <View style={styles.root}>
      <Canvas style={StyleSheet.absoluteFill} onLayout={onLayout}>
        <Group transform={introShake}>
          <Fill>
            <Shader source={composite} uniforms={cu}>
              <ImageShader image={frame} tx="clamp" ty="clamp" />
            </Shader>
          </Fill>
          <Sparks t={t} videoTime={videoTime} cam={cam} size={size} />
          <Fill>
            <Shader source={overlay} uniforms={ou} />
          </Fill>
          <Fill color="black" opacity={introDim} />
          <TitleCard t={t} size={size} />
        </Group>
      </Canvas>

      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, posterStyle]}>
        <RNImage source={require("../../assets/cinematic/poster.jpg")} style={styles.poster} resizeMode="cover" />
        <Animated.View style={[StyleSheet.absoluteFill, styles.dim, posterDim]} />
      </Animated.View>
      {phase === "intro" && <KiChargeIntro charge={charge} enabled={ready} autoHold={DEMO} onCharged={() => start()} />}
      {phase === "ended" && (
        <Pressable style={styles.replay} onPress={replay}>
          <Text style={styles.replayText}>REPLAY</Text>
        </Pressable>
      )}
      {__DEV__ && !DEMO && phase !== "intro" && <Scrubber t={t} onSeek={seek} />}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#000" },
  dim: { backgroundColor: "#000" },
  poster: { width: "100%", height: "100%" },
  replay: {
    position: "absolute",
    alignSelf: "center",
    bottom: 70,
    paddingHorizontal: 28,
    paddingVertical: 12,
    borderRadius: 24,
    borderWidth: 1.5,
    borderColor: "#FFD23F",
    backgroundColor: "#0008",
  },
  replayText: { color: "#FFD23F", fontWeight: "900", letterSpacing: 3, fontSize: 16 },
});
