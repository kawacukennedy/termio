/**
 * App Navigator
 * 
 * Main navigation configuration for the TERMIO mobile app.
 * Uses React Navigation with:
 * - Bottom Tab Navigator: Main app sections
 * - Native Stack Navigator: Modal screens
 * 
 * # Screen Structure
 * 
 * ## Tab Navigator (Main)
 * 1. **Home**: Dashboard with quick actions and recent conversations
 * 2. **Assistant**: Full chat interface with AI
 * 3. **Scan**: Camera-based visual intelligence
 * 4. **Plugins**: Plugin management
 * 5. **Settings**: App configuration
 * 
 * ## Stack Screens (Modal)
 * 1. **Subscription**: Plan selection and management
 * 2. **SmartHome**: Device and scene management
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/Ionicons';

import HomeScreen from '../screens/HomeScreen';
import AssistantScreen from '../screens/AssistantScreen';
import ScanScreen from '../screens/ScanScreen';
import PluginsScreen from '../screens/PluginsScreen';
import SettingsScreen from '../screens/SettingsScreen';
import SubscriptionScreen from '../screens/SubscriptionScreen';
import SmartHomeScreen from '../screens/SmartHomeScreen';

// Create navigators
const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

/**
 * Tab Navigator
 * 
 * Bottom tab navigation with icons.
 * Uses Ionicons for consistent iOS-style icons.
 */
function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        // Icon configuration based on route name
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Home':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Assistant':
              iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
              break;
            case 'Scan':
              iconName = focused ? 'qr-code' : 'qr-code-outline';
              break;
            case 'Plugins':
              iconName = focused ? 'extension-puzzle' : 'extension-puzzle-outline';
              break;
            case 'Settings':
              iconName = focused ? 'settings' : 'settings-outline';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        // Tab bar styling - dark theme per iOS 26 spec
        tabBarActiveTintColor: '#0EA5E9',  // Primary accent
        tabBarInactiveTintColor: '#A3A3A3', // Secondary text
        tabBarStyle: {
          backgroundColor: '#171717',       // Background
          borderTopColor: '#262626',        // Border
        },
        headerShown: false,  // Hide headers - custom headers in screens
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Assistant" component={AssistantScreen} />
      <Tab.Screen name="Scan" component={ScanScreen} />
      <Tab.Screen name="Plugins" component={PluginsScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

/**
 * Main App Navigator
 * 
 * Root navigator combining tabs and modal screens.
 */
export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Main" component={TabNavigator} />
        <Stack.Screen name="Subscription" component={SubscriptionScreen} />
        <Stack.Screen name="SmartHome" component={SmartHomeScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
