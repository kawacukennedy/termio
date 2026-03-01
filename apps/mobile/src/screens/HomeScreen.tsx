/**
 * Home Screen
 * 
 * The main dashboard for TERMIO, showing:
 * - Header with title and notifications
 * - Quick Actions: New Chat, Voice Mode, Scan, Smart Home
 * - Suggestions: AI-generated proactive suggestions
 * - Recent Conversations: List of past conversations
 * - Floating Action Button: Quick access to new chat
 * 
 * # Design
 * 
 * - Dark theme per iOS 26 specification
 * - Uses iOS-style navigation patterns
 * - Zustand for state management
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  SafeAreaView,
  ScrollView,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useAppStore } from '../store/appStore';

export default function HomeScreen({ navigation }: any) {
  // Zustand store selectors
  const conversations = useAppStore((state) => state.conversations);
  const setCurrentConversation = useAppStore((state) => state.setCurrentConversation);
  const addConversation = useAppStore((state) => state.addConversation);

  // Quick action buttons shown as horizontal chips
  const quickActions = [
    { id: 'new', title: 'New Chat', icon: 'chatbubbles', color: '#0EA5E9' },
    { id: 'voice', title: 'Voice Mode', icon: 'mic', color: '#10B981' },
    { id: 'scan', title: 'Scan', icon: 'qr-code', color: '#F59E0B' },
    { id: 'home', title: 'Smart Home', icon: 'home', color: '#8B5CF6' },
  ];

  // Proactive AI suggestions shown as cards
  const suggestions = [
    { id: '1', title: 'Check weather', description: 'It might rain today', action: 'Check' },
    { id: '2', title: 'Meeting in 30 min', description: 'Prepare agenda', action: 'View' },
    { id: '3', title: 'Weekly summary', description: 'View your week at a glance', action: 'Show' },
  ];

  // Handle new chat button press
  const handleNewChat = () => {
    // Generate unique ID from timestamp
    const id = Date.now().toString();
    const conversation = {
      id,
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    // Add to store and navigate
    addConversation(conversation);
    setCurrentConversation(id);
    navigation.navigate('Assistant');
  };

  // Handle quick action button press
  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'new':
        handleNewChat();
        break;
      case 'voice':
        navigation.navigate('Assistant');
        break;
      case 'scan':
        navigation.navigate('Scan');
        break;
      case 'home':
        navigation.navigate('SmartHome');
        break;
    }
  };

  return (
    // Safe area handling for notched devices
    <SafeAreaView style={styles.container}>
      {/* Header Section */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.title}>TERMIO</Text>
        </View>
        {/* Notification bell */}
        <TouchableOpacity style={styles.notificationButton}>
          <Icon name="notifications-outline" size={24} color="#FAFAFA" />
        </TouchableOpacity>
      </View>

      {/* Main Content */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Quick Actions Section - Horizontal scroll */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.quickActions}>
            {quickActions.map((action) => (
              <TouchableOpacity
                key={action.id}
                style={[styles.quickAction, { backgroundColor: action.color + '20' }]}
                onPress={() => handleQuickAction(action.id)}
              >
                <View style={[styles.quickActionIcon, { backgroundColor: action.color }]}>
                  <Icon name={action.icon} size={20} color="#FFFFFF" />
                </View>
                <Text style={styles.quickActionText}>{action.title}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Proactive Suggestions Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Suggestions for you</Text>
          {suggestions.map((suggestion) => (
            <TouchableOpacity key={suggestion.id} style={styles.suggestionCard}>
              <View style={styles.suggestionContent}>
                <Text style={styles.suggestionTitle}>{suggestion.title}</Text>
                <Text style={styles.suggestionDescription}>{suggestion.description}</Text>
              </View>
              <TouchableOpacity style={styles.suggestionAction}>
                <Text style={styles.suggestionActionText}>{suggestion.action}</Text>
              </TouchableOpacity>
            </TouchableOpacity>
          ))}
        </View>

        {/* Recent Conversations Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent</Text>
          {conversations.length === 0 ? (
            // Empty state
            <View style={styles.empty}>
              <Icon name="chatbubbles-outline" size={48} color="#404040" />
              <Text style={styles.emptyText}>No conversations yet</Text>
              <TouchableOpacity style={styles.startButton} onPress={handleNewChat}>
                <Text style={styles.startButtonText}>Start a chat</Text>
              </TouchableOpacity>
            </View>
          ) : (
            // Conversation list
            conversations.map((conv) => (
              <TouchableOpacity
                key={conv.id}
                style={styles.conversationItem}
                onPress={() => {
                  setCurrentConversation(conv.id);
                  navigation.navigate('Assistant');
                }}
              >
                <View style={styles.conversationAvatar}>
                  <Icon name="chatbubbles" size={20} color="#0EA5E9" />
                </View>
                <View style={styles.conversationInfo}>
                  <Text style={styles.conversationTitle}>{conv.title}</Text>
                  <Text style={styles.conversationPreview} numberOfLines={1}>
                    {conv.messages.length > 0 ? conv.messages[conv.messages.length - 1].content : 'No messages yet'}
                  </Text>
                </View>
                <Text style={styles.conversationTime}>
                  {new Date(conv.updatedAt).toLocaleDateString()}
                </Text>
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>

      {/* Floating Action Button for new chat */}
      <TouchableOpacity style={styles.fab} onPress={handleNewChat}>
        <Icon name="add" size={28} color="#FFFFFF" />
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  // Main container - full screen with dark background
  container: {
    flex: 1,
    backgroundColor: '#0C0C0C',
  },
  // Header bar with title and notification
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#262626',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FAFAFA',
  },
  notificationButton: {
    padding: 4,
  },
  // Scrollable content area
  content: {
    flex: 1,
  },
  // Section container with title
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#A3A3A3',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  // Quick action chips - horizontal scroll
  quickActions: {
    flexDirection: 'row',
  },
  quickAction: {
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    marginRight: 12,
    width: 80,
  },
  quickActionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  quickActionText: {
    fontSize: 12,
    color: '#FAFAFA',
    textAlign: 'center',
  },
  // Suggestion cards
  suggestionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#171717',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  suggestionDescription: {
    fontSize: 14,
    color: '#737373',
    marginTop: 2,
  },
  suggestionAction: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#0EA5E9',
    borderRadius: 6,
  },
  suggestionActionText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  // Conversation list items
  conversationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#171717',
    borderRadius: 12,
    marginBottom: 8,
  },
  conversationAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#0EA5E920',
    justifyContent: 'center',
    alignItems: 'center',
  },
  conversationInfo: {
    flex: 1,
    marginLeft: 12,
  },
  conversationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  conversationPreview: {
    fontSize: 14,
    color: '#737373',
    marginTop: 2,
  },
  conversationTime: {
    fontSize: 12,
    color: '#525252',
  },
  // Empty state
  empty: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
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
    fontWeight: '600',
  },
  // Floating action button
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#0EA5E9',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#0EA5E9',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
});
