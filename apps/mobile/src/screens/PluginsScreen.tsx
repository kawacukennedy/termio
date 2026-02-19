import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Switch,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useAppStore } from '../store/appStore';

export default function PluginsScreen({ navigation }: any) {
  const plugins = useAppStore((state) => state.plugins);
  const togglePlugin = useAppStore((state) => state.togglePlugin);

  const renderPlugin = ({ item }: any) => (
    <View style={styles.pluginItem}>
      <View style={styles.pluginInfo}>
        <Text style={styles.pluginName}>{item.name}</Text>
        <Text style={styles.pluginDescription}>{item.description}</Text>
        <Text style={styles.pluginVersion}>v{item.version}</Text>
      </View>
      <Switch
        value={item.enabled}
        onValueChange={() => togglePlugin(item.id)}
        trackColor={{ false: '#404040', true: '#0EA5E9' }}
        thumbColor={item.enabled ? '#FFFFFF' : '#737373'}
      />
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Plugins</Text>
      </View>

      <FlatList
        data={plugins}
        keyExtractor={(item) => item.id}
        renderItem={renderPlugin}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Icon name="extension-puzzle-outline" size={48} color="#404040" />
            <Text style={styles.emptyText}>No plugins available</Text>
          </View>
        }
      />

      <TouchableOpacity style={styles.marketplaceButton}>
        <Icon name="storefront-outline" size={20} color="#FFFFFF" />
        <Text style={styles.marketplaceButtonText}>Browse Marketplace</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0C0C0C',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#262626',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FAFAFA',
    textAlign: 'center',
  },
  list: {
    padding: 16,
  },
  pluginItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#171717',
    borderRadius: 12,
    marginBottom: 8,
  },
  pluginInfo: {
    flex: 1,
  },
  pluginName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  pluginDescription: {
    fontSize: 14,
    color: '#737373',
    marginTop: 2,
  },
  pluginVersion: {
    fontSize: 12,
    color: '#525252',
    marginTop: 4,
  },
  empty: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
  },
  emptyText: {
    color: '#737373',
    fontSize: 16,
    marginTop: 16,
  },
  marketplaceButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    margin: 16,
    padding: 14,
    backgroundColor: '#0EA5E9',
    borderRadius: 8,
  },
  marketplaceButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
