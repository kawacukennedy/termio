import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Switch,
  ScrollView,
  SafeAreaView,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useAppStore } from '../store/appStore';

export default function SettingsScreen({ navigation }: any) {
  const serverUrl = useAppStore((state) => state.serverUrl);
  const setServerUrl = useAppStore((state) => state.setServerUrl);
  const [url, setUrl] = useState(serverUrl);
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [voiceInput, setVoiceInput] = useState(true);

  const handleSave = () => {
    setServerUrl(url);
    Alert.alert('Settings saved', 'Your settings have been updated.');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Server</Text>
          
          <View style={styles.settingItem}>
            <Icon name="server-outline" size={24} color="#A3A3A3" />
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Server URL</Text>
              <TextInput
                style={styles.input}
                value={url}
                onChangeText={setUrl}
                placeholder="http://localhost:8080"
                placeholderTextColor="#525252"
              />
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          
          <View style={styles.settingItem}>
            <Icon name="notifications-outline" size={24} color="#A3A3A3" />
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Push Notifications</Text>
            </View>
            <Switch
              value={notifications}
              onValueChange={setNotifications}
              trackColor={{ false: '#404040', true: '#0EA5E9' }}
              thumbColor={notifications ? '#FFFFFF' : '#737373'}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Appearance</Text>
          
          <View style={styles.settingItem}>
            <Icon name="moon-outline" size={24} color="#A3A3A3" />
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Dark Mode</Text>
            </View>
            <Switch
              value={darkMode}
              onValueChange={setDarkMode}
              trackColor={{ false: '#404040', true: '#0EA5E9' }}
              thumbColor={darkMode ? '#FFFFFF' : '#737373'}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Voice</Text>
          
          <View style={styles.settingItem}>
            <Icon name="mic-outline" size={24} color="#A3A3A3" />
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Voice Input</Text>
            </View>
            <Switch
              value={voiceInput}
              onValueChange={setVoiceInput}
              trackColor={{ false: '#404040', true: '#0EA5E9' }}
              thumbColor={voiceInput ? '#FFFFFF' : '#737373'}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          
          <View style={styles.settingItem}>
            <Icon name="information-circle-outline" size={24} color="#A3A3A3" />
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Version</Text>
              <Text style={styles.settingValue}>2.0.0</Text>
            </View>
          </View>
          
          <TouchableOpacity style={styles.settingItem}>
            <Icon name="document-text-outline" size={24} color="#A3A3A3" />
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Terms of Service</Text>
            </View>
            <Icon name="chevron-forward" size={20} color="#525252" />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.settingItem}>
            <Icon name="shield-checkmark-outline" size={24} color="#A3A3A3" />
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Privacy Policy</Text>
            </View>
            <Icon name="chevron-forward" size={20} color="#525252" />
          </TouchableOpacity>
        </View>
      </ScrollView>

      <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
        <Text style={styles.saveButtonText}>Save Settings</Text>
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
  content: {
    flex: 1,
  },
  section: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#262626',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#737373',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  settingInfo: {
    flex: 1,
    marginLeft: 12,
  },
  settingLabel: {
    fontSize: 16,
    color: '#FAFAFA',
  },
  settingValue: {
    fontSize: 14,
    color: '#737373',
    marginTop: 2,
  },
  input: {
    marginTop: 4,
    padding: 8,
    backgroundColor: '#262626',
    borderRadius: 6,
    color: '#FAFAFA',
    fontSize: 14,
  },
  saveButton: {
    margin: 16,
    padding: 14,
    backgroundColor: '#0EA5E9',
    borderRadius: 8,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
