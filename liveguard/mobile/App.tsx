import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import AlertsScreen from "./src/screens/AlertsScreen";
import AlertDetailScreen from "./src/screens/AlertDetailScreen";

export type RootStackParamList = {
  Alerts: undefined;
  AlertDetail: { alertId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerStyle: { backgroundColor: "#0B0F1A" },
            headerTintColor: "#F8FAFC",
            headerTitleStyle: { fontWeight: "600" },
            contentStyle: { backgroundColor: "#0B0F1A" },
          }}
        >
          <Stack.Screen
            name="Alerts"
            component={AlertsScreen}
            options={{ title: "守播 · 告警" }}
          />
          <Stack.Screen
            name="AlertDetail"
            component={AlertDetailScreen}
            options={{ title: "告警详情" }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
