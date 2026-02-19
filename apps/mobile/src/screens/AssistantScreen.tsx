import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  Modal,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useAppStore, useCurrentConversation } from '../store/appStore';

export default function AssistantScreen({ navigation }: any) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showVoiceModal, setShowVoiceModal] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [transcription, setTranscription] = useState('');
  const flatListRef = useRef<FlatList>(null);
  const waveformAnim = useRef(new Animated.Value(0)).current;

  const conversation = useCurrentConversation();
  const addMessage = useAppStore((state) => state.addMessage);
  const serverUrl = useAppStore((state) => state.serverUrl);

  useEffect(() => {
    if (isRecording) {
      const animation = Animated.loop(
        Animated.sequence([
          Animated.timing(waveformAnim, {
            toValue: 1,
            duration: 300,
            useNativeDriver: true,
          }),
          Animated.timing(waveformAnim, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
          }),
        ])
      );
      animation.start();
      return () => animation.stop();
    }
  }, [isRecording]);

  const sendMessage = async (text?: string) => {
    const messageText = text || input;
    if (!messageText.trim() || !conversation || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: messageText.trim(),
      timestamp: new Date().toISOString(),
    };

    addMessage(conversation.id, userMessage);
    setInput('');
    if (text) setTranscription('');
    setIsLoading(true);
    setShowVoiceModal(false);

    try {
      const response = await fetch(`${serverUrl}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content }),
      });
      const data = await response.json();

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: data.response || 'No response',
        timestamp: new Date().toISOString(),
      };

      addMessage(conversation.id, assistantMessage);
    } catch (e) {
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'Demo mode: Connect to a TERMIO server for AI responses.',
        timestamp: new Date().toISOString(),
      };
      addMessage(conversation.id, assistantMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleVoice = () => {
    if (isRecording) {
      // Stop recording and send
      setIsRecording(false);
      if (transcription) {
        sendMessage(transcription);
      }
    } else {
      // Start recording
      setIsRecording(true);
      setTranscription('Listening...');
    }
  };

  const renderMessage = ({ item }: any) => (
    <View style={[styles.message, item.role === 'user' && styles.userMessage]}>
      <View style={[styles.bubble, item.role === 'user' && styles.userBubble]}>
        <Text style={[styles.messageText, item.role === 'user' && styles.userMessageText]}>
          {item.content}
        </Text>
      </View>
    </View>
  );

  if (!conversation) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.empty}>
          <Icon name="chatbubbles-outline" size={64} color="#404040" />
          <Text style={styles.emptyText}>Select a conversation</Text>
          <TouchableOpacity 
            style={styles.startButton}
            onPress={() => navigation.navigate('Home')}
          >
            <Text style={styles.startButtonText}>Go to Home</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.navigate('Home')}>
          <Icon name="chevron-back" size={24} color="#FAFAFA" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{conversation.title}</Text>
        <View style={{ width: 24 }} />
      </View>

      <FlatList
        ref={flatListRef}
        data={conversation.messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.messages}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
      />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={90}
      >
        <View style={styles.inputContainer}>
          <TouchableOpacity 
            style={styles.voiceButton}
            onPress={() => setShowVoiceModal(true)}
          >
            <Icon name="mic" size={24} color="#A3A3A3" />
          </TouchableOpacity>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Type a message..."
            placeholderTextColor="#737373"
            multiline
          />
          <TouchableOpacity
            style={[styles.sendButton, !input.trim() && styles.sendButtonDisabled]}
            onPress={() => sendMessage()}
            disabled={!input.trim() || isLoading}
          >
            <Icon 
              name={isLoading ? 'hourglass' : 'send'} 
              size={20} 
              color="#FFFFFF" 
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

      {/* Voice Modal */}
      <Modal
        visible={showVoiceModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowVoiceModal(false)}
      >
        <View style={styles.voiceModalOverlay}>
          <View style={styles.voiceModalContent}>
            <TouchableOpacity 
              style={styles.voiceModalClose}
              onPress={() => setShowVoiceModal(false)}
            >
              <Icon name="close" size={24} color="#FAFAFA" />
            </TouchableOpacity>

            <Text style={styles.voiceModalTitle}>
              {isRecording ? 'Listening...' : 'Voice Mode'}
            </Text>

            {/* Waveform Visualization */}
            <View style={styles.waveformContainer}>
              {[...Array(12)].map((_, i) => (
                <Animated.View
                  key={i}
                  style={[
                    styles.waveformBar,
                    {
                      transform: [
                        {
                          scaleY: isRecording 
                            ? waveformAnim.interpolate({
                                inputRange: [0, 1],
                                outputRange: [0.3 + Math.random() * 0.7, 1],
                              })
                            : 0.3
                        }
                      ],
                    },
                  ]}
                />
              ))}
            </View>

            {/* Live Transcription */}
            <View style={styles.transcriptionContainer}>
              <Text style={styles.transcriptionText}>
                {transcription || 'Tap the microphone to start speaking'}
              </Text>
            </View>

            {/* Controls */}
            <View style={styles.voiceControls}>
              <TouchableOpacity 
                style={styles.cancelButton}
                onPress={() => {
                  setShowVoiceModal(false);
                  setIsRecording(false);
                  setTranscription('');
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.recordButton, isRecording && styles.recordButtonActive]}
                onPress={toggleVoice}
              >
                <Icon 
                  name={isRecording ? 'send' : 'mic'} 
                  size={32} 
                  color="#FFFFFF" 
                />
              </TouchableOpacity>

              <View style={{ width: 80 }} />
            </View>
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
  messages: {
    padding: 16,
  },
  message: {
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  userMessage: {
    alignItems: 'flex-end',
  },
  bubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    backgroundColor: '#171717',
  },
  userBubble: {
    backgroundColor: '#0EA5E9',
  },
  messageText: {
    fontSize: 16,
    color: '#FAFAFA',
  },
  userMessageText: {
    color: '#FFFFFF',
  },
  empty: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    color: '#737373',
    fontSize: 16,
    marginTop: 16,
  },
  startButton: {
    marginTop: 16,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#0EA5E9',
    borderRadius: 8,
  },
  startButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#262626',
    backgroundColor: '#171717',
  },
  voiceButton: {
    padding: 8,
  },
  input: {
    flex: 1,
    marginHorizontal: 8,
    padding: 12,
    backgroundColor: '#262626',
    borderRadius: 20,
    color: '#FAFAFA',
    fontSize: 16,
    maxHeight: 100,
  },
  sendButton: {
    padding: 12,
    backgroundColor: '#0EA5E9',
    borderRadius: 24,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  voiceModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'flex-end',
  },
  voiceModalContent: {
    backgroundColor: '#171717',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    alignItems: 'center',
    minHeight: 400,
  },
  voiceModalClose: {
    position: 'absolute',
    top: 16,
    right: 16,
    padding: 8,
  },
  voiceModalTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FAFAFA',
    marginTop: 40,
    marginBottom: 40,
  },
  waveformContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 80,
    gap: 4,
  },
  waveformBar: {
    width: 4,
    height: 60,
    backgroundColor: '#0EA5E9',
    borderRadius: 2,
  },
  transcriptionContainer: {
    minHeight: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 24,
    paddingHorizontal: 20,
  },
  transcriptionText: {
    fontSize: 18,
    color: '#FAFAFA',
    textAlign: 'center',
  },
  voiceControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    paddingHorizontal: 20,
  },
  cancelButton: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  cancelButtonText: {
    color: '#737373',
    fontSize: 16,
  },
  recordButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#0EA5E9',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordButtonActive: {
    backgroundColor: '#10B981',
  },
});
