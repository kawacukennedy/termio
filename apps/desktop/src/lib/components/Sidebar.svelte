<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { appStore, currentConversation } from '$lib/stores/app';
  import { Plus, MessageSquare, Trash2, Search } from 'lucide-svelte';

  const dispatch = createEventDispatcher();
  
  let searchQuery = '';
  
  $: filteredConversations = $appStore.conversations.filter(c => 
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  function selectConversation(id: string) {
    appStore.setCurrentConversation(id);
  }

  function deleteConversation(id: string, e: Event) {
    e.stopPropagation();
    const updated = $appStore.conversations.filter(c => c.id !== id);
    appStore.update(s => ({ ...s, conversations: updated }));
    if ($appStore.currentConversationId === id) {
      appStore.setCurrentConversation(null);
    }
  }
</script>

<aside class="w-64 bg-[var(--color-bg-secondary)] border-r border-[var(--color-surface-tertiary)] flex flex-col">
  <div class="p-3">
    <button 
      class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-lg transition-colors"
      on:click={() => dispatch('newConversation')}
    >
      <Plus class="w-4 h-4" />
      <span class="text-sm font-medium">New Chat</span>
    </button>
  </div>
  
  <div class="px-3 pb-3">
    <div class="relative">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-tertiary)]" />
      <input 
        type="text" 
        placeholder="Search conversations..." 
        bind:value={searchQuery}
        class="w-full pl-9 pr-3 py-2 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] focus:outline-none focus:border-[var(--color-accent)]"
      />
    </div>
  </div>
  
  <div class="flex-1 overflow-y-auto px-2">
    {#each filteredConversations as conv (conv.id)}
      <button
        class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors {$appStore.currentConversationId === conv.id ? 'bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-primary)]'}"
        on:click={() => selectConversation(conv.id)}
      >
        <MessageSquare class="w-4 h-4 flex-shrink-0" />
        <span class="flex-1 truncate text-sm">{conv.title}</span>
        <button 
          class="p-1 hover:bg-[var(--color-surface-tertiary)] rounded opacity-0 group-hover:opacity-100 transition-opacity"
          on:click={(e) => deleteConversation(conv.id, e)}
        >
          <Trash2 class="w-3 h-3" />
        </button>
      </button>
    {/each}
    
    {#if filteredConversations.length === 0}
      <div class="text-center py-8 text-[var(--color-text-tertiary)] text-sm">
        No conversations yet
      </div>
    {/if}
  </div>
</aside>
