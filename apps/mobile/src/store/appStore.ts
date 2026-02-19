import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  body: string;
  read: boolean;
  timestamp: string;
}

export interface Plugin {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  version: string;
}

interface AppState {
  conversations: Conversation[];
  currentConversationId: string | null;
  notifications: Notification[];
  plugins: Plugin[];
  serverUrl: string;
  isLoading: boolean;
  
  setServerUrl: (url: string) => void;
  setLoading: (loading: boolean) => void;
  addConversation: (conversation: Conversation) => void;
  setCurrentConversation: (id: string | null) => void;
  addMessage: (conversationId: string, message: Message) => void;
  setNotifications: (notifications: Notification[]) => void;
  markNotificationRead: (id: string) => void;
  setPlugins: (plugins: Plugin[]) => void;
  togglePlugin: (id: string) => void;
  reset: () => void;
}

const defaultState = {
  conversations: [] as Conversation[],
  currentConversationId: null as string | null,
  notifications: [] as Notification[],
  plugins: [
    { id: '1', name: 'Weather', description: 'Get weather updates', enabled: true, version: '1.0.0' },
    { id: '2', name: 'Calculator', description: 'Math operations', enabled: false, version: '1.0.0' },
  ],
  serverUrl: 'http://localhost:8080',
  isLoading: false,
};

export const useAppStore = create<AppState>((set, get) => ({
  ...defaultState,

  setServerUrl: (url) => {
    set({ serverUrl: url });
    AsyncStorage.setItem('serverUrl', url);
  },

  setLoading: (loading) => set({ isLoading: loading }),

  addConversation: (conversation) =>
    set((state) => ({ 
      conversations: [conversation, ...state.conversations] 
    })),

  setCurrentConversation: (id) =>
    set({ currentConversationId: id }),

  addMessage: (conversationId, message) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === conversationId
          ? { ...c, messages: [...c.messages, message], updatedAt: new Date().toISOString() }
          : c
      ),
    })),

  setNotifications: (notifications) => set({ notifications }),

  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
    })),

  setPlugins: (plugins) => set({ plugins }),

  togglePlugin: (id) =>
    set((state) => ({
      plugins: state.plugins.map((p) =>
        p.id === id ? { ...p, enabled: !p.enabled } : p
      ),
    })),

  reset: () => set(defaultState),
}));

export const useCurrentConversation = () => {
  const conversations = useAppStore((state) => state.conversations);
  const currentId = useAppStore((state) => state.currentConversationId);
  return conversations.find((c) => c.id === currentId) || null;
};

export const useUnreadNotifications = () => {
  return useAppStore((state) => state.notifications.filter((n) => !n.read).length);
};
