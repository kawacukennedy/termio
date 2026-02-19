<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { appStore } from '$lib/stores/app';
  import { 
    Settings, 
    Puzzle, 
    Smartphone, 
    Cloud, 
    CloudOff,
    RefreshCw
  } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  async function triggerSync() {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      appStore.setSyncState({ ...$appStore.syncState, status: 'syncing' });
      
      await invoke('trigger_sync', { serverUrl: $appStore.serverUrl });
      
      appStore.setSyncState({ 
        status: 'idle', 
        lastSync: new Date().toISOString(),
        pendingChanges: 0 
      });
    } catch (e) {
      console.error('Sync failed:', e);
      appStore.setSyncState({ ...$appStore.syncState, status: 'error' });
    }
  }
</script>

<header class="h-12 bg-[var(--color-bg-secondary)] border-b border-[var(--color-surface-tertiary)] flex items-center justify-between px-4">
  <div class="flex items-center gap-3">
    <div class="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center">
      <span class="text-white font-bold text-sm">T</span>
    </div>
    <span class="text-lg font-semibold text-[var(--color-text-primary)]">TERMIO</span>
  </div>
  
  <div class="flex items-center gap-2">
    <button 
      class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors"
      title="Sync"
      on:click={triggerSync}
      disabled={$appStore.syncState.status === 'syncing'}
    >
      {#if $appStore.syncState.status === 'syncing'}
        <RefreshCw class="w-5 h-5 animate-spin" />
      {:else if $appStore.syncState.status === 'error'}
        <CloudOff class="w-5 h-5 text-[var(--color-error)]" />
      {:else}
        <Cloud class="w-5 h-5" />
      {/if}
    </button>
    
    <button 
      class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors"
      title="Plugins"
      on:click={() => dispatch('plugins')}
    >
      <Puzzle class="w-5 h-5" />
    </button>
    
    <button 
      class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors"
      title="Device Pairing"
      on:click={() => dispatch('pairing')}
    >
      <Smartphone class="w-5 h-5" />
    </button>
    
    <button 
      class="p-2 rounded-lg hover:bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] transition-colors"
      title="Settings"
      on:click={() => dispatch('settings')}
    >
      <Settings class="w-5 h-5" />
    </button>
  </div>
</header>
