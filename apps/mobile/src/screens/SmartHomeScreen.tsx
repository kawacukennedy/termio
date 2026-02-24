import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Modal,
  TextInput,
  Switch,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useAppStore } from '../store/appStore';

interface Device {
  id: string;
  name: string;
  device_type: string;
  protocol: string;
  is_online: boolean;
  state: Record<string, any>;
}

interface Scene {
  id: string;
  name: string;
  description?: string;
  actions: any[];
}

export default function SmartHomeScreen({ navigation }: any) {
  const serverUrl = useAppStore((state) => state.serverUrl);
  const [devices, setDevices] = useState<Device[]>([]);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [showAddDevice, setShowAddDevice] = useState(false);
  const [showAddScene, setShowAddScene] = useState(false);
  const [newDeviceName, setNewDeviceName] = useState('');
  const [newDeviceType, setNewDeviceType] = useState('light');
  const [newSceneName, setNewSceneName] = useState('');
  const [newSceneDescription, setNewSceneDescription] = useState('');

  useEffect(() => {
    fetchDevices();
    fetchScenes();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await fetch(`${serverUrl}/api/smart-home/devices`);
      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      }
    } catch (error) {
      console.log('Error fetching devices:', error);
    }
  };

  const fetchScenes = async () => {
    try {
      const response = await fetch(`${serverUrl}/api/smart-home/scenes`);
      if (response.ok) {
        const data = await response.json();
        setScenes(data);
      }
    } catch (error) {
      console.log('Error fetching scenes:', error);
    }
  };

  const toggleDevice = async (device: Device) => {
    const newState = { ...device.state, on: !device.state.on };
    try {
      await fetch(`${serverUrl}/api/smart-home/devices/${device.id}/state`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newState),
      });
      fetchDevices();
    } catch (error) {
      console.log('Error toggling device:', error);
    }
  };

  const addDevice = async () => {
    if (!newDeviceName.trim()) return;
    
    try {
      await fetch(`${serverUrl}/api/smart-home/devices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newDeviceName,
          device_type: newDeviceType,
          protocol: 'matter',
          state: { on: false },
        }),
      });
      setNewDeviceName('');
      setShowAddDevice(false);
      fetchDevices();
    } catch (error) {
      console.log('Error adding device:', error);
    }
  };

  const addScene = async () => {
    if (!newSceneName.trim()) return;
    
    try {
      await fetch(`${serverUrl}/api/smart-home/scenes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newSceneName,
          description: newSceneDescription,
          actions: [],
        }),
      });
      setNewSceneName('');
      setNewSceneDescription('');
      setShowAddScene(false);
      fetchScenes();
    } catch (error) {
      console.log('Error adding scene:', error);
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'light':
        return 'bulb';
      case 'thermostat':
        return 'thermometer';
      case 'lock':
        return 'lock-closed';
      case 'camera':
        return 'videocam';
      case 'sensor':
        return 'radio-button-on';
      case 'speaker':
        return 'volume-high';
      default:
        return 'help-circle';
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="chevron-back" size={24} color="#FAFAFA" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Smart Home</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content}>
        {/* Devices Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Devices</Text>
            <TouchableOpacity 
              style={styles.addButton}
              onPress={() => setShowAddDevice(true)}
            >
              <Icon name="add" size={20} color="#0EA5E9" />
            </TouchableOpacity>
          </View>

          {devices.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="home-outline" size={48} color="#404040" />
              <Text style={styles.emptyText}>No devices found</Text>
              <Text style={styles.emptySubtext}>
                Add your first smart device to get started
              </Text>
            </View>
          ) : (
            <View style={styles.devicesGrid}>
              {devices.map((device) => (
                <TouchableOpacity 
                  key={device.id} 
                  style={styles.deviceCard}
                  onPress={() => toggleDevice(device)}
                >
                  <View style={[
                    styles.deviceIcon,
                    device.state?.on && styles.deviceIconActive
                  ]}>
                    <Icon 
                      name={getDeviceIcon(device.device_type)} 
                      size={24} 
                      color={device.state?.on ? '#FFFFFF' : '#A3A3A3'} 
                    />
                  </View>
                  <Text style={styles.deviceName} numberOfLines={1}>
                    {device.name}
                  </Text>
                  <View style={styles.deviceStatus}>
                    <View style={[
                      styles.statusDot,
                      device.is_online ? styles.statusOnline : styles.statusOffline
                    ]} />
                    <Text style={styles.statusText}>
                      {device.is_online ? 'Online' : 'Offline'}
                    </Text>
                  </View>
                  <Switch
                    value={device.state?.on || false}
                    onValueChange={() => toggleDevice(device)}
                    trackColor={{ false: '#404040', true: '#0EA5E9' }}
                    thumbColor={device.state?.on ? '#FFFFFF' : '#737373'}
                  />
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {/* Scenes Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Scenes</Text>
            <TouchableOpacity 
              style={styles.addButton}
              onPress={() => setShowAddScene(true)}
            >
              <Icon name="add" size={20} color="#0EA5E9" />
            </TouchableOpacity>
          </View>

          {scenes.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="layers-outline" size={48} color="#404040" />
              <Text style={styles.emptyText}>No scenes created</Text>
              <Text style={styles.emptySubtext}>
                Create scenes to control multiple devices at once
              </Text>
            </View>
          ) : (
            <View style={styles.scenesList}>
              {scenes.map((scene) => (
                <TouchableOpacity key={scene.id} style={styles.sceneCard}>
                  <View style={styles.sceneIcon}>
                    <Icon name="color-palette" size={20} color="#0EA5E9" />
                  </View>
                  <View style={styles.sceneInfo}>
                    <Text style={styles.sceneName}>{scene.name}</Text>
                    {scene.description && (
                      <Text style={styles.sceneDescription} numberOfLines={1}>
                        {scene.description}
                      </Text>
                    )}
                  </View>
                  <TouchableOpacity style={styles.playButton}>
                    <Icon name="play" size={20} color="#FAFAFA" />
                  </TouchableOpacity>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      </ScrollView>

      {/* Add Device Modal */}
      <Modal
        visible={showAddDevice}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAddDevice(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Device</Text>
              <TouchableOpacity onPress={() => setShowAddDevice(false)}>
                <Icon name="close" size={24} color="#FAFAFA" />
              </TouchableOpacity>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Device Name</Text>
              <TextInput
                style={styles.input}
                value={newDeviceName}
                onChangeText={setNewDeviceName}
                placeholder="e.g., Living Room Light"
                placeholderTextColor="#525252"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Device Type</Text>
              <View style={styles.typeSelector}>
                {['light', 'thermostat', 'lock', 'camera', 'sensor', 'speaker'].map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.typeOption,
                      newDeviceType === type && styles.typeOptionActive
                    ]}
                    onPress={() => setNewDeviceType(type)}
                  >
                    <Icon 
                      name={getDeviceIcon(type)} 
                      size={20} 
                      color={newDeviceType === type ? '#FFFFFF' : '#A3A3A3'} 
                    />
                    <Text style={[
                      styles.typeOptionText,
                      newDeviceType === type && styles.typeOptionTextActive
                    ]}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <TouchableOpacity 
              style={styles.submitButton}
              onPress={addDevice}
            >
              <Text style={styles.submitButtonText}>Add Device</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Add Scene Modal */}
      <Modal
        visible={showAddScene}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowAddScene(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Create Scene</Text>
              <TouchableOpacity onPress={() => setShowAddScene(false)}>
                <Icon name="close" size={24} color="#FAFAFA" />
              </TouchableOpacity>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Scene Name</Text>
              <TextInput
                style={styles.input}
                value={newSceneName}
                onChangeText={setNewSceneName}
                placeholder="e.g., Movie Night"
                placeholderTextColor="#525252"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Description (optional)</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={newSceneDescription}
                onChangeText={setNewSceneDescription}
                placeholder="e.g., Dim lights and lower thermostat"
                placeholderTextColor="#525252"
                multiline
                numberOfLines={3}
              />
            </View>

            <TouchableOpacity 
              style={styles.submitButton}
              onPress={addScene}
            >
              <Text style={styles.submitButtonText}>Create Scene</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0C0C0C',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#262626',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  content: {
    flex: 1,
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#737373',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  addButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#0EA5E920',
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#FAFAFA',
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#737373',
    marginTop: 4,
    textAlign: 'center',
  },
  devicesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  deviceCard: {
    width: '47%',
    backgroundColor: '#171717',
    borderRadius: 16,
    padding: 16,
  },
  deviceIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#262626',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  deviceIconActive: {
    backgroundColor: '#0EA5E9',
  },
  deviceName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FAFAFA',
    marginBottom: 4,
  },
  deviceStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusOnline: {
    backgroundColor: '#10B981',
  },
  statusOffline: {
    backgroundColor: '#EF4444',
  },
  statusText: {
    fontSize: 12,
    color: '#737373',
  },
  scenesList: {
    gap: 12,
  },
  sceneCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#171717',
    borderRadius: 12,
    padding: 16,
  },
  sceneIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#0EA5E920',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  sceneInfo: {
    flex: 1,
  },
  sceneName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  sceneDescription: {
    fontSize: 14,
    color: '#737373',
    marginTop: 2,
  },
  playButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#0EA5E9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#171717',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    color: '#A3A3A3',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#262626',
    borderRadius: 10,
    padding: 14,
    color: '#FAFAFA',
    fontSize: 16,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  typeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#262626',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  typeOptionActive: {
    backgroundColor: '#0EA5E9',
    borderColor: '#0EA5E9',
  },
  typeOptionText: {
    color: '#A3A3A3',
    fontSize: 14,
  },
  typeOptionTextActive: {
    color: '#FFFFFF',
  },
  submitButton: {
    backgroundColor: '#0EA5E9',
    padding: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
