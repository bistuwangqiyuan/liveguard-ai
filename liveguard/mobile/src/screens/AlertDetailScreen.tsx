import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import * as Haptics from "expo-haptics";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import type { RootStackParamList } from "../../App";

type Props = NativeStackScreenProps<RootStackParamList, "AlertDetail">;

export default function AlertDetailScreen({ route, navigation }: Props) {
  const { alertId } = route.params;

  async function ack() {
    await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    navigation.goBack();
  }

  return (
    <View style={styles.root}>
      <Text style={styles.id}>{alertId}</Text>
      <Text style={styles.heading}>告警详情</Text>
      <Text style={styles.body}>
        此骨架展示页将在生产版本中接入：
        {"\n"}· 直播间 WHEP 低延迟预览（1s 内首帧）
        {"\n"}· 关键事件时间线（FSM 状态迁移 + 反作弊 flags）
        {"\n"}· 一键 ACK / RESOLVE / 升级 · 可选生物识别确认
        {"\n"}· 责任人 On-Call 切换 & 备注
      </Text>
      <TouchableOpacity style={styles.btn} onPress={ack}>
        <Text style={styles.btnText}>确认 ACK</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, padding: 20, backgroundColor: "#0B0F1A" },
  id: { color: "#64748B", fontFamily: "Courier", marginBottom: 6 },
  heading: { color: "#F8FAFC", fontSize: 22, fontWeight: "700" },
  body: { color: "#94A3B8", lineHeight: 22, marginTop: 12 },
  btn: {
    marginTop: 24,
    backgroundColor: "#1F6FFF",
    padding: 14,
    borderRadius: 12,
    alignItems: "center",
  },
  btnText: { color: "#fff", fontWeight: "700" },
});
