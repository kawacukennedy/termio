/**
 * TERMIO Mobile Application
 * 
 * A next-generation agentic AI assistant mobile app.
 * 
 * # Features
 * 
 * - Home Screen: Quick actions, suggestions, recent conversations
 * - Assistant: Full-duplex conversational AI
 * - Scan: Visual intelligence with camera
 * - Plugins: Manage WASM plugins
 * - Settings: App configuration
 * - Subscription: Plan management
 * - Smart Home: Matter/Thread device control
 * 
 * # Architecture
 * 
 * The app uses React Navigation for routing and Zustand for state management.
 * 
 * ## Navigation Structure
 * 
 * ```
 * Stack Navigator
 * ├── Tab Navigator (Main)
 * │   ├── Home Screen
 * │   ├── Assistant Screen
 * │   ├── Scan Screen
 * │   ├── Plugins Screen
 * │   └── Settings Screen
 * ├── Subscription Screen (Modal)
 * └── SmartHome Screen (Modal)
 * ```
 * 
 * # Running
 * 
 * ```bash
 * cd apps/mobile
 * npm install
 * npm run android   # or: npm run ios
 * ```
 */

import React from 'react';
import { StatusBar } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import AppNavigator from './src/navigation/AppNavigator';

export default function App() {
  return (
    // GestureHandlerRootView is required for React Navigation
    <GestureHandlerRootView style={{ flex: 1 }}>
      // StatusBar configuration - dark content on dark background
      <StatusBar barStyle="light-content" backgroundColor="#0C0C0C" />
      <AppNavigator />
    </GestureHandlerRootView>
  );
}
