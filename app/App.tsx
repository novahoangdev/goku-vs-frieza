import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { CinematicScreen } from "./src/screens/CinematicScreen";

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: "#000" }}>
      <StatusBar hidden />
      <CinematicScreen />
    </GestureHandlerRootView>
  );
}
