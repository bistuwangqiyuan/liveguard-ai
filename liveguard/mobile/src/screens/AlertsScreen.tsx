import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { useEffect, useState } from "react";
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import type { RootStackParamList } from "../../App";
import { fetchAlerts, type AlertItem } from "../api";

type Props = NativeStackScreenProps<RootStackParamList, "Alerts">;

const SEV_COLOR: Record<string, string> = {
  P0: "#E4000F",
  P1: "#F97316",
  P2: "#F59E0B",
  INFO: "#10B981",
};

export default function AlertsScreen({ navigation }: Props) {
  const [items, setItems] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setItems(await fetchAlerts());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <FlatList
      data={items}
      keyExtractor={(x) => x.id}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={load} tintColor="#4d95ff" />}
      contentContainerStyle={{ padding: 16 }}
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.card}
          onPress={() => navigation.navigate("AlertDetail", { alertId: item.id })}
        >
          <View style={styles.row}>
            <View style={[styles.sev, { backgroundColor: SEV_COLOR[item.severity] }]}>
              <Text style={styles.sevText}>{item.severity}</Text>
            </View>
            <Text style={styles.time}>
              {new Date(item.first_seen_at).toLocaleString("zh-CN")}
            </Text>
          </View>
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.summary} numberOfLines={2}>
            {item.summary}
          </Text>
          <Text style={styles.stream}>stream: {item.stream_id}</Text>
        </TouchableOpacity>
      )}
      ListEmptyComponent={
        <View style={{ padding: 40, alignItems: "center" }}>
          <Text style={{ color: "#94A3B8" }}>暂无告警 · 一切平稳</Text>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#111727",
    borderColor: "#1F2B4C",
    borderWidth: 1,
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
  },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  sev: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 },
  sevText: { color: "#fff", fontSize: 11, fontWeight: "700" },
  time: { color: "#64748B", fontSize: 11 },
  title: { color: "#F1F5F9", fontSize: 15, fontWeight: "600", marginTop: 8 },
  summary: { color: "#94A3B8", fontSize: 13, marginTop: 4, lineHeight: 18 },
  stream: { color: "#64748B", fontSize: 11, marginTop: 6, fontFamily: "Courier" },
});
