import React, { useEffect } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Animated, { useAnimatedStyle, useFrameCallback, useSharedValue, type SharedValue } from "react-native-reanimated";
import { scheduleOnRN } from "react-native-worklets";
import { fireHaptic } from "../cinematic/haptics";

const CHARGE_SECONDS = 1.5;

/**
 * "Hold to charge Ki" screen: while held, the Ki bar fills over 1.5s (haptics speed up, the screen shakes with
 * `charge`); releasing early drains it. Calls `onCharged` when full.
 */
export function KiChargeIntro({
  charge,
  enabled,
  autoHold = false,
  onCharged,
}: {
  charge: SharedValue<number>;
  enabled: boolean;
  /** Demo recording mode: auto-hold after 1.2s. */
  autoHold?: boolean;
  onCharged: () => void;
}) {
  const holding = useSharedValue(false);
  const nextTick = useSharedValue(0);
  const done = useSharedValue(false);

  useEffect(() => {
    if (!autoHold || !enabled) return;
    const id = setTimeout(() => holding.set(true), 1200);
    return () => clearTimeout(id);
  }, [autoHold, enabled, holding]);

  useFrameCallback(({ timeSincePreviousFrame, timeSinceFirstFrame }) => {
    "worklet";
    if (done.get()) return;
    const dt = (timeSincePreviousFrame ?? 0) / 1000;
    const hold = holding.get();
    const c = hold ? Math.min(1, charge.get() + dt / CHARGE_SECONDS) : Math.max(0, charge.get() - dt * 1.5);
    charge.set(c);
    if (hold && timeSinceFirstFrame >= nextTick.get()) {
      scheduleOnRN(fireHaptic, c > 0.7 ? "medium" : "light");
      nextTick.set(timeSinceFirstFrame + 150 - c * 110);
    }
    if (c >= 1) {
      done.set(true);
      scheduleOnRN(fireHaptic, "heavy");
      scheduleOnRN(onCharged);
    }
  });

  const barStyle = useAnimatedStyle(() => ({ width: `${charge.value * 100}%` }));
  const labelStyle = useAnimatedStyle(() => ({ opacity: 1 - charge.value * 0.6 }));

  return (
    <Pressable
      style={StyleSheet.absoluteFill}
      disabled={!enabled}
      onPressIn={() => holding.set(true)}
      onPressOut={() => holding.set(false)}
    >
      <View style={styles.top}>
        <Text style={styles.logo1}>SAIYAN</Text>
        <Text style={styles.logo2}>AWAKENING</Text>
      </View>
      <View style={styles.bottom}>
        <Animated.Text style={[styles.label, labelStyle]}>{enabled ? "HOLD TO CHARGE KI" : "LOADING…"}</Animated.Text>
        <View style={styles.track}>
          <Animated.View style={[styles.fill, barStyle]} />
        </View>
        <Text style={styles.hint}>Saiyan Awakening · Goku vs Frieza</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  top: { position: "absolute", left: 0, right: 0, top: 120, alignItems: "center" },
  logo1: {
    color: "#FFD23F", fontSize: 54, fontWeight: "900", fontStyle: "italic", letterSpacing: 2,
    textShadowColor: "#7A1F0B", textShadowOffset: { width: 3, height: 4 }, textShadowRadius: 0,
  },
  logo2: {
    color: "#FFF3B0", fontSize: 26, fontWeight: "900", fontStyle: "italic", letterSpacing: 8, marginTop: -4,
    textShadowColor: "#7A1F0B", textShadowOffset: { width: 2, height: 3 }, textShadowRadius: 0,
  },
  bottom: { position: "absolute", left: 32, right: 32, bottom: 90, alignItems: "center" },
  label: { color: "#FFF3B0", fontSize: 20, fontWeight: "900", letterSpacing: 3, marginBottom: 14, fontStyle: "italic" },
  track: {
    width: "100%",
    height: 14,
    borderRadius: 7,
    backgroundColor: "#0008",
    borderWidth: 1.5,
    borderColor: "#FFD23F88",
    overflow: "hidden",
  },
  fill: { height: "100%", backgroundColor: "#FFD23F", shadowColor: "#FFD23F", shadowOpacity: 1, shadowRadius: 8 },
  hint: { color: "#ffffff88", fontSize: 12, marginTop: 14, letterSpacing: 1 },
});
