import { writable, derived } from 'svelte/store';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
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

export interface SyncState {
  status: 'idle' | 'syncing' | 'error';
  lastSync: string | null;
  pendingChanges: number;
}

export interface Plugin {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  version: string;
}

export interface AppState {
  conversations: Conversation[];
  currentConversationId: string | null;
  notifications: Notification[];
  syncState: SyncState;
  plugins: Plugin[];
  serverUrl: string;
  isLoading: boolean;
}

const defaultState: AppState = {
  conversations: [],
  currentConversationId: null,
  notifications: [],
  syncState: {
    status: 'idle',
    lastSync: null,
    pendingChanges: 0,
  },
  plugins: [],
  serverUrl: 'http://localhost:8080',
  isLoading: false,
};

function createAppStore() {
  const { subscribe, set, update } = writable<AppState>(defaultState);

  return {
    subscribe,
    set,
    update,
    
    setServerUrl: (url: string) => update(s => ({ ...s, serverUrl: url })),
    
    setLoading: (loading: boolean) => update(s => ({ ...s, isLoading: loading })),
    
    addConversation: (conversation: Conversation) => 
      update(s => ({ ...s, conversations: [conversation, ...s.conversations] })),
    
    setCurrentConversation: (id: string | null) =>
      update(s => ({ ...s, currentConversationId: id })),
    
    addMessage: (conversationId: string, message: Message) =>
      update(s => ({
        ...s,
        conversations: s.conversations.map(c => 
          c.id === conversationId 
            ? { ...c, messages: [...c.messages, message], updatedAt: new Date().toISOString() }
            : c
        ),
      })),
    
    setNotifications: (notifications: Notification[]) =>
      update(s => ({ ...s, notifications })),
    
    markNotificationRead: (id: string) =>
      update(s => ({
        ...s,
        notifications: s.notifications.map(n => 
          n.id === id ? { ...n, read: true } : n
        ),
      })),
    
    setSyncState: (syncState: SyncState) =>
      update(s => ({ ...s, syncState })),
    
    setPlugins: (plugins: Plugin[]) =>
      update(s => ({ ...s, plugins })),
    
    togglePlugin: (id: string) =>
      update(s => ({
        ...s,
        plugins: s.plugins.map(p => 
          p.id === id ? { ...p, enabled: !p.enabled } : p
        ),
      })),
    
    reset: () => set(defaultState),
  };
}

export const appStore = createAppStore();

export const currentConversation = derived(
  appStore,
  $store => $store.conversations.find(c => c.id === $store.currentConversationId) || null
);

export const unreadNotifications = derived(
  appStore,
  $store => $store.notifications.filter(n => !n.read).length
);
