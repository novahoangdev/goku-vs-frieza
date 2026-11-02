import * as Haptics from "expo-haptics";

const IMPACT: Record<string, Haptics.ImpactFeedbackStyle> = {
  light: Haptics.ImpactFeedbackStyle.Light,
  medium: Haptics.ImpactFeedbackStyle.Medium,
  heavy: Haptics.ImpactFeedbackStyle.Heavy,
  rigid: Haptics.ImpactFeedbackStyle.Rigid,
  soft: Haptics.ImpactFeedbackStyle.Soft,
};

/** Called from a worklet via scheduleOnRN when the clock passes a `haptic:<style>` marker. */
export const fireHaptic = (style: string) => {
  const p =
    style === "success"
      ? Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
      : Haptics.impactAsync(IMPACT[style] ?? Haptics.ImpactFeedbackStyle.Medium);
  p.catch(() => {});
};
