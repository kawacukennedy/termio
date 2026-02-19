<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { appStore } from '$lib/stores/app';
  import { X, Search, ExternalLink, Download, ToggleLeft, ToggleRight } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  let searchQuery = '';
  let loading = true;
  let plugins: any[] = [];

  onMount(async () => {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const result = await invoke('list_plugins', { serverUrl: $appStore.serverUrl });
      plugins = (result as any)?.plugins || [];
    } catch (e) {
      // Demo plugins
      plugins = [
        { id: '1', name: 'Weather', description: 'Get weather updates', enabled: true, version: '1.0.0' },
        { id: '2', name: 'Calculator', description: 'Mathematical operations', enabled: false, version: '1.0.0' },
        { id: '3', name: 'Translate', description: 'Multi-language translation', enabled: true, version: '1.0.0' },
      ];
    } finally {
      loading = false;
    }
  });

  $: filteredPlugins = plugins.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  function togglePlugin(id: string) {
    plugins = plugins.map(p => 
      p.id === id ? { ...p, enabled: !p.enabled } : p
    );
    appStore.togglePlugin(id);
  }
</script>

<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" on:click|self={() => dispatch('close')}>
  <div class="bg-[var(--color-bg-secondary)] rounded-xl w-[600px] max-h-[80vh] overflow-hidden shadow-2xl">
    <div class="flex items-center justify-between p-4 border-b border-[var(--color-surface-tertiary)]">
      <h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Plugin Marketplace</h2>
      <button 
        class="p-1 hover:bg-[var(--color-surface-primary)] rounded-lg transition-colors"
        on:click={() => dispatch('close')}
      >
        <X class="w-5 h-5 text-[var(--color-text-secondary)]" />
      </button>
    </div>
    
    <div class="p-4 border-b border-[var(--color-surface-tertiary)]">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-tertiary)]" />
        <input 
          type="text" 
          bind:value={searchQuery}
          placeholder="Search plugins..."
          class="w-full pl-10 pr-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] focus:outline-none focus:border-[var(--color-accent)]"
        />
      </div>
    </div>
    
    <div class="p-4 overflow-y-auto max-h-[400px]">
      {#if loading}
        <div class="text-center py-8 text-[var(--color-text-tertiary)]">Loading plugins...</div>
      {:else if filteredPlugins.length === 0}
        <div class="text-center py-8 text-[var(--color-text-tertiary)]">No plugins found</div>
      {:else}
        <div class="space-y-3">
          {#each filteredPlugins as plugin (plugin.id)}
            <div class="flex items-center justify-between p-3 bg-[var(--color-surface-primary)] rounded-lg">
              <div class="flex-1">
                <h4 class="text-sm font-medium text-[var(--color-text-primary)]">{plugin.name}</h4>
                <p class="text-xs text-[var(--color-text-tertiary)] mt-1">{plugin.description}</p>
                <span class="text-xs text-[var(--color-text-tertiary)]">v{plugin.version}</span>
              </div>
              
              <div class="flex items-center gap-2">
                <button 
                  class="p-2 hover:bg-[var(--color-surface-secondary)] rounded-lg transition-colors"
                  title="View in marketplace"
                >
                  <ExternalLink class="w-4 h-4 text-[var(--color-text-tertiary)]" />
                </button>
                
                <button 
                  class="p-2 hover:bg-[var(--color-surface-secondary)] rounded-lg transition-colors"
                  title="Download"
                >
                  <Download class="w-4 h-4 text-[var(--color-text-tertiary)]" />
                </button>
                
                <button 
                  class="p-2 hover:bg-[var(--color-surface-secondary)] rounded-lg transition-colors"
                  on:click={() => togglePlugin(plugin.id)}
                  title={plugin.enabled ? 'Disable' : 'Enable'}
                >
                  {#if plugin.enabled}
                    <ToggleRight class="w-6 h-6 text-[var(--color-success)]" />
                  {:else}
                    <ToggleLeft class="w-6 h-6 text-[var(--color-text-tertiary)]" />
                  {/if}
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
