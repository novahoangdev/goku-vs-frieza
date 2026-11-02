import React, { useState } from "react";
import { StyleSheet, Text, View, type LayoutChangeEvent } from "react-native";
import { Gesture, GestureDetector } from "react-native-gesture-handler";
import { useAnimatedReaction, type SharedValue } from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";
import { DURATION, FPS, SHOTS } from "../cinematic/timeline";

/** Dev builds only: drag to scrub; shows the frame number and shot name. */
export function Scrubber({ t, onSeek }: { t: SharedValue<number>; onSeek: (sec: number) => void }) {
  const [width, setWidth] = useState(1);
  const [label, setLabel] = useState("f0000");
  const [pos, setPos] = useState(0);

  const update = (sec: number) => {
    const f = Math.round(sec * FPS);
    const shot = [...SHOTS].reverse().find((s) => s.f <= f);
    setLabel(`f${String(f).padStart(4, "0")} · ${shot?.name ?? ""}`);
    setPos(sec / DURATION);
  };
  useAnimatedReaction(
    () => Math.floor(t.get() * 10),
    (v, prev) => {
      if (v !== prev) scheduleOnRN(update, t.get());
    },
  );

  const seek = (x: number) => onSeek(Math.max(0, Math.min(1, x / width)) * DURATION);
  const pan = Gesture.Pan()
    .runOnJS(true)
    .minDistance(0)
    .onBegin((e) => seek(e.x))
    .onUpdate((e) => seek(e.x));

  return (
    <View style={styles.wrap} pointerEvents="box-none">
      <Text style={styles.label}>{label}</Text>
      <GestureDetector gesture={pan}>
        <View style={styles.bar} onLayout={(e: LayoutChangeEvent) => setWidth(e.nativeEvent.layout.width)}>
          {SHOTS.map((s) => (
            <View key={s.f} style={[styles.tick, { left: `${(s.f / FPS / DURATION) * 100}%` }]} />
          ))}
          <View style={[styles.head, { left: `${pos * 100}%` }]} />
        </View>
      </GestureDetector>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { position: "absolute", left: 16, right: 16, top: 58 },
  label: { color: "#fff", fontSize: 11, fontVariant: ["tabular-nums"], marginBottom: 4, opacity: 0.8 },
  bar: { height: 22, borderRadius: 4, backgroundColor: "#0006", justifyContent: "center" },
  tick: { position: "absolute", width: 1, top: 4, bottom: 4, backgroundColor: "#fff6" },
  head: { position: "absolute", width: 3, top: 0, bottom: 0, backgroundColor: "#FFD23F" },
});
