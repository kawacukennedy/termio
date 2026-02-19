import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  SafeAreaView,
  Modal,
  Animated,
  PanResponder,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

export default function ScanScreen({ navigation }: any) {
  const [mode, setMode] = useState<'pair' | 'vision'>('vision');
  const [pairingCode] = useState('TERMIO-ABCD-1234');
  const [scanned, setScanned] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [detectedObject, setDetectedObject] = useState('');
  const slideAnim = useRef(new Animated.Value(300)).current;

  // Demo detected objects
  const demoResults = [
    { name: 'Laptop', description: 'MacBook Pro 14-inch, 2023', confidence: 98 },
    { name: 'Coffee Cup', description: 'Ceramic mug with coffee', confidence: 95 },
    { name: 'Notebook', description: 'Leather-bound journal', confidence: 92 },
  ];

  const handleScan = () => {
    setScanned(true);
    setDetectedObject(demoResults[0].name);
    setShowResult(true);
    Animated.spring(slideAnim, {
      toValue: 0,
      useNativeDriver: true,
    }).start();
  };

  const handleObjectSelect = (obj: typeof demoResults[0]) => {
    setDetectedObject(obj.name);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Scan</Text>
        <View style={styles.modeToggle}>
          <TouchableOpacity 
            style={[styles.modeButton, mode === 'pair' && styles.modeButtonActive]}
            onPress={() => setMode('pair')}
          >
            <Text style={[styles.modeButtonText, mode === 'pair' && styles.modeButtonTextActive]}>
              Pair
            </Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.modeButton, mode === 'vision' && styles.modeButtonActive]}
            onPress={() => setMode('vision')}
          >
            <Text style={[styles.modeButtonText, mode === 'vision' && styles.modeButtonTextActive]}>
              Vision
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {mode === 'pair' ? (
        <View style={styles.content}>
          <View style={styles.qrContainer}>
            <View style={styles.qrPlaceholder}>
              <Icon name="qr-code" size={120} color="#0EA5E9" />
            </View>
            <Text style={styles.qrText}>Scan QR code from desktop app</Text>
          </View>

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>OR</Text>
            <View style={styles.dividerLine} />
          </View>

          <View style={styles.codeContainer}>
            <Text style={styles.codeLabel}>Enter pairing code</Text>
            <TextInput
              style={styles.codeInput}
              placeholder="XXXX-XXXX-XXXX"
              placeholderTextColor="#737373"
              value={pairingCode}
              editable={false}
            />
            <TouchableOpacity style={styles.connectButton} onPress={handleScan}>
              <Icon name="link" size={20} color="#FFFFFF" />
              <Text style={styles.connectButtonText}>Connect</Text>
            </TouchableOpacity>
          </View>

          {scanned && (
            <View style={styles.success}>
              <Icon name="checkmark-circle" size={24} color="#10B981" />
              <Text style={styles.successText}>Device paired successfully!</Text>
            </View>
          )}
        </View>
      ) : (
        <View style={styles.visionContainer}>
          {/* Camera View Placeholder */}
          <View style={styles.cameraView}>
            <View style={styles.cameraOverlay}>
              {/* Scan frame */}
              <View style={styles.scanFrame}>
                <View style={[styles.corner, styles.topLeft]} />
                <View style={[styles.corner, styles.topRight]} />
                <View style={[styles.corner, styles.bottomLeft]} />
                <View style={[styles.corner, styles.bottomRight]} />
              </View>
              
              <Text style={styles.scanHint}>Point camera at object</Text>
            </View>
            
            {/* Demo detection boxes */}
            <View style={styles.detectionBox}>
              <Text style={styles.detectionLabel}>Laptop</Text>
              <Text style={styles.detectionConfidence}>98%</Text>
            </View>
          </View>

          {/* Bottom Controls */}
          <View style={styles.visionControls}>
            <TouchableOpacity style={styles.galleryButton}>
              <Icon name="images-outline" size={24} color="#FAFAFA" />
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.captureButton} onPress={handleScan}>
              <View style={styles.captureButtonInner} />
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.flashButton}>
              <Icon name="flashlight-outline" size={24} color="#FAFAFA" />
            </TouchableOpacity>
          </View>

          {/* Result Panel */}
          <Animated.View 
            style={[
              styles.resultPanel,
              { transform: [{ translateY: slideAnim }] }
            ]}
          >
            <View style={styles.resultHandle} />
            <Text style={styles.resultTitle}>Detected Objects</Text>
            
            {demoResults.map((obj, index) => (
              <TouchableOpacity 
                key={index}
                style={[
                  styles.resultItem,
                  detectedObject === obj.name && styles.resultItemActive
                ]}
                onPress={() => handleObjectSelect(obj)}
              >
                <View style={styles.resultItemInfo}>
                  <Text style={styles.resultItemName}>{obj.name}</Text>
                  <Text style={styles.resultItemDesc}>{obj.description}</Text>
                </View>
                <Text style={styles.resultItemConfidence}>{obj.confidence}%</Text>
              </TouchableOpacity>
            ))}
            
            <View style={styles.resultActions}>
              <TouchableOpacity style={styles.resultActionButton}>
                <Icon name="book-outline" size={20} color="#0EA5E9" />
                <Text style={styles.resultActionText}>Show repair guide</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.resultActionButton}>
                <Icon name="list-outline" size={20} color="#0EA5E9" />
                <Text style={styles.resultActionText}>Add to list</Text>
              </TouchableOpacity>
            </View>
          </Animated.View>
        </View>
      )}
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  modeToggle: {
    flexDirection: 'row',
    backgroundColor: '#262626',
    borderRadius: 8,
    padding: 2,
  },
  modeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  modeButtonActive: {
    backgroundColor: '#0EA5E9',
  },
  modeButtonText: {
    color: '#737373',
    fontSize: 14,
    fontWeight: '600',
  },
  modeButtonTextActive: {
    color: '#FFFFFF',
  },
  content: {
    flex: 1,
    padding: 24,
  },
  qrContainer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  qrPlaceholder: {
    width: 200,
    height: 200,
    backgroundColor: '#171717',
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  qrText: {
    marginTop: 16,
    color: '#737373',
    fontSize: 14,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#262626',
  },
  dividerText: {
    marginHorizontal: 16,
    color: '#737373',
    fontSize: 14,
  },
  codeContainer: {
    padding: 16,
    backgroundColor: '#171717',
    borderRadius: 12,
  },
  codeLabel: {
    fontSize: 14,
    color: '#A3A3A3',
    marginBottom: 8,
  },
  codeInput: {
    backgroundColor: '#262626',
    borderRadius: 8,
    padding: 12,
    fontSize: 18,
    color: '#0EA5E9',
    textAlign: 'center',
    letterSpacing: 2,
    marginBottom: 16,
  },
  connectButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#0EA5E9',
    padding: 14,
    borderRadius: 8,
  },
  connectButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  success: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 24,
    padding: 16,
    backgroundColor: '#10B98120',
    borderRadius: 8,
  },
  successText: {
    color: '#10B981',
    fontSize: 16,
    fontWeight: '600',
  },
  visionContainer: {
    flex: 1,
  },
  cameraView: {
    flex: 1,
    backgroundColor: '#000000',
    position: 'relative',
  },
  cameraOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanFrame: {
    width: 250,
    height: 250,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderColor: '#0EA5E9',
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 3,
    borderLeftWidth: 3,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 3,
    borderRightWidth: 3,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 3,
    borderRightWidth: 3,
  },
  scanHint: {
    marginTop: 24,
    color: '#FAFAFA',
    fontSize: 16,
  },
  detectionBox: {
    position: 'absolute',
    top: 80,
    right: 16,
    backgroundColor: '#0EA5E980',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  detectionLabel: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  detectionConfidence: {
    color: '#FFFFFF',
    fontSize: 12,
  },
  visionControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 20,
    backgroundColor: '#171717',
  },
  galleryButton: {
    padding: 12,
  },
  captureButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#262626',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: '#0EA5E9',
  },
  captureButtonInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#FFFFFF',
  },
  flashButton: {
    padding: 12,
  },
  resultPanel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#171717',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 16,
    maxHeight: 350,
  },
  resultHandle: {
    width: 40,
    height: 4,
    backgroundColor: '#404040',
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 16,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FAFAFA',
    marginBottom: 16,
  },
  resultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#262626',
    borderRadius: 12,
    marginBottom: 8,
  },
  resultItemActive: {
    borderWidth: 1,
    borderColor: '#0EA5E9',
  },
  resultItemInfo: {
    flex: 1,
  },
  resultItemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  resultItemDesc: {
    fontSize: 14,
    color: '#737373',
    marginTop: 2,
  },
  resultItemConfidence: {
    fontSize: 14,
    color: '#10B981',
    fontWeight: '600',
  },
  resultActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  resultActionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 12,
    backgroundColor: '#0EA5E920',
    borderRadius: 8,
  },
  resultActionText: {
    color: '#0EA5E9',
    fontSize: 14,
    fontWeight: '600',
  },
});
