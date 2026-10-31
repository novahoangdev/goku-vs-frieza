import * as Haptics from "expo-haptics";

const IMPACT: Record<string, Haptics.ImpactFeedbackStyle> = {
  light: Haptics.ImpactFeedbackStyle.Light,
  medium: Haptics.ImpactFeedbackStyle.Medium,
  heavy: Haptics.ImpactFeedbackStyle.Heavy,
  rigid: Haptics.ImpactFeedbackStyle.Rigid,
  soft: Haptics.ImpactFeedbackStyle.Soft,
};

/** Gọi từ worklet qua scheduleOnRN khi đồng hồ vượt qua marker `haptic:<style>`. */
export const fireHaptic = (style: string) => {
  const p =
    style === "success"
      ? Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
      : Haptics.impactAsync(IMPACT[style] ?? Haptics.ImpactFeedbackStyle.Medium);
  p.catch(() => {});
};
