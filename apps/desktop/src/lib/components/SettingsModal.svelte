<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { appStore } from '$lib/stores/app';
  import { X, Server, Bell, Moon, Globe, Shield, Cpu, Plug, RefreshCw, User, Key, Save } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  type Tab = 'general' | 'ai' | 'privacy' | 'plugins' | 'sync' | 'notifications';
  let activeTab: Tab = 'general';

  let serverUrl = $appStore.serverUrl;
  let theme = 'dark';
  let language = 'en';
  let startOnBoot = false;
  let minimizeToTray = true;
  
  // AI Settings
  let model = 'llama3-8b';
  let offlineMode = true;
  let cloudAugmentation = false;
  let temperature = 0.7;
  
  // Privacy Settings
  let dataRetention = '90';
  let encryptionEnabled = true;
  let exportData = false;
  
  // Notification Settings
  let notificationsEnabled = true;
  let quietHoursEnabled = false;
  let quietHoursStart = '22:00';
  let quietHoursEnd = '08:00';
  let soundEnabled = true;
  
  // Sync Settings
  let autoSync = true;
  let wifiOnly = true;
  let syncInterval = '5';

  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: 'general', label: 'General', icon: User },
    { id: 'ai', label: 'AI', icon: Cpu },
    { id: 'privacy', label: 'Privacy', icon: Shield },
    { id: 'plugins', label: 'Plugins', icon: Plug },
    { id: 'sync', label: 'Sync', icon: RefreshCw },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ];

  function save() {
    appStore.setServerUrl(serverUrl);
    dispatch('close');
  }
</script>

<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" on:click|self={() => dispatch('close')}>
  <div class="bg-[var(--color-bg-secondary)] rounded-xl w-[700px] max-h-[80vh] overflow-hidden shadow-2xl">
    <div class="flex items-center justify-between p-4 border-b border-[var(--color-surface-tertiary)]">
      <h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Settings</h2>
      <button 
        class="p-1 hover:bg-[var(--color-surface-primary)] rounded-lg transition-colors"
        on:click={() => dispatch('close')}
      >
        <X class="w-5 h-5 text-[var(--color-text-secondary)]" />
      </button>
    </div>
    
    <div class="flex h-[500px]">
      <nav class="w-48 bg-[var(--color-bg-primary)] border-r border-[var(--color-surface-tertiary)] p-2">
        {#each tabs as tab}
          <button
            class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors {activeTab === tab.id ? 'bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-primary)]'}"
            on:click={() => activeTab = tab.id}
          >
            <svelte:component this={tab.icon} class="w-4 h-4" />
            <span class="text-sm">{tab.label}</span>
          </button>
        {/each}
      </nav>
      
      <div class="flex-1 overflow-y-auto p-6">
        {#if activeTab === 'general'}
          <div class="space-y-6">
            <div>
              <h3 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">Server</h3>
              <input 
                type="text" 
                bind:value={serverUrl}
                placeholder="http://localhost:8080"
                class="w-full px-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] focus:outline-none focus:border-[var(--color-accent)]"
              />
              <p class="text-xs text-[var(--color-text-tertiary)] mt-1">TERMIO server URL</p>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">Appearance</h3>
              <select 
                bind:value={theme}
                class="w-full px-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-[var(--color-text-primary)] focus:outline-none"
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
                <option value="system">System</option>
              </select>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">Language</h3>
              <select 
                bind:value={language}
                class="w-full px-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-[var(--color-text-primary)] focus:outline-none"
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="zh">中文</option>
              </select>
            </div>
            
            <div class="space-y-3">
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={startOnBoot} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Start on system boot</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={minimizeToTray} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Minimize to system tray</span>
              </label>
            </div>
          </div>
          
        {:else if activeTab === 'ai'}
          <div class="space-y-6">
            <div>
              <h3 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">Model</h3>
              <select 
                bind:value={model}
                class="w-full px-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-[var(--color-text-primary)] focus:outline-none"
              >
                <option value="llama3-8b">LLaMA 3 8B (Recommended)</option>
                <option value="llama3-70b">LLaMA 3 70B</option>
                <option value="mixtral-8x7b">Mixtral 8x7B</option>
                <option value="phi-3">Phi-3 Mini</option>
              </select>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">Temperature: {temperature}</h3>
              <input 
                type="range" 
                min="0" max="1" step="0.1" 
                bind:value={temperature}
                class="w-full"
              />
              <div class="flex justify-between text-xs text-[var(--color-text-tertiary)]">
                <span>Precise</span>
                <span>Creative</span>
              </div>
            </div>
            
            <div class="space-y-3">
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={offlineMode} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Offline mode (local inference only)</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={cloudAugmentation} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Cloud augmentation (requires consent)</span>
              </label>
            </div>
          </div>
          
        {:else if activeTab === 'privacy'}
          <div class="space-y-6">
            <div>
              <h3 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">Data Retention</h3>
              <select 
                bind:value={dataRetention}
                class="w-full px-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-[var(--color-text-primary)] focus:outline-none"
              >
                <option value="30">30 days</option>
                <option value="90">90 days</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
                <option value="0">Forever</option>
              </select>
            </div>
            
            <div class="space-y-3">
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={encryptionEnabled} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Enable encryption at rest</span>
              </label>
            </div>
            
            <div>
              <button 
                class="px-4 py-2 bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] rounded-lg hover:bg-[var(--color-surface-tertiary)] transition-colors"
                on:click={exportData}
              >
                Export My Data
              </button>
            </div>
          </div>
          
        {:else if activeTab === 'plugins'}
          <div class="space-y-4">
            <p class="text-sm text-[var(--color-text-secondary)]">
              Manage installed plugins and browse the marketplace.
            </p>
            <div class="grid gap-2">
              {#each $appStore.plugins as plugin}
                <div class="flex items-center justify-between p-3 bg-[var(--color-surface-primary)] rounded-lg">
                  <div>
                    <p class="text-sm font-medium text-[var(--color-text-primary)]">{plugin.name}</p>
                    <p class="text-xs text-[var(--color-text-tertiary)]">{plugin.description}</p>
                  </div>
                  <input type="checkbox" bind:checked={plugin.enabled} class="w-4 h-4" />
                </div>
              {/each}
            </div>
            <button class="w-full py-2 bg-[var(--color-accent)] text-white rounded-lg">
              Browse Marketplace
            </button>
          </div>
          
        {:else if activeTab === 'sync'}
          <div class="space-y-6">
            <div class="space-y-3">
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={autoSync} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Auto-sync</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={wifiOnly} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Sync on WiFi only</span>
              </label>
            </div>
            
            <div>
              <h3 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">Sync Interval</h3>
              <select 
                bind:value={syncInterval}
                class="w-full px-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-[var(--color-text-primary)] focus:outline-none"
              >
                <option value="1">Every minute</option>
                <option value="5">Every 5 minutes</option>
                <option value="15">Every 15 minutes</option>
                <option value="30">Every 30 minutes</option>
              </select>
            </div>
            
            <div>
              <button class="px-4 py-2 bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] rounded-lg">
                Manage Devices
              </button>
            </div>
          </div>
          
        {:else if activeTab === 'notifications'}
          <div class="space-y-6">
            <div class="space-y-3">
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={notificationsEnabled} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Enable notifications</span>
              </label>
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={soundEnabled} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Notification sound</span>
              </label>
            </div>
            
            <div class="space-y-3">
              <label class="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" bind:checked={quietHoursEnabled} class="w-4 h-4 rounded" />
                <span class="text-sm text-[var(--color-text-secondary)]">Quiet hours</span>
              </label>
              {#if quietHoursEnabled}
                <div class="flex gap-4 ml-7">
                  <div>
                    <label class="text-xs text-[var(--color-text-tertiary)]">Start</label>
                    <input type="time" bind:value={quietHoursStart} class="block mt-1 px-2 py-1 bg-[var(--color-surface-primary)] rounded" />
                  </div>
                  <div>
                    <label class="text-xs text-[var(--color-text-tertiary)]">End</label>
                    <input type="time" bind:value={quietHoursEnd} class="block mt-1 px-2 py-1 bg-[var(--color-surface-primary)] rounded" />
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>
    </div>
    
    <div class="flex justify-end gap-3 p-4 border-t border-[var(--color-surface-tertiary)]">
      <button 
        class="px-4 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        on:click={() => dispatch('close')}
      >
        Cancel
      </button>
      <button 
        class="px-4 py-2 text-sm bg-[var(--color-accent)] text-white rounded-lg hover:bg-[var(--color-accent-hover)] transition-colors flex items-center gap-2"
        on:click={save}
      >
        <Save class="w-4 h-4" />
        Save
      </button>
    </div>
  </div>
</div>
