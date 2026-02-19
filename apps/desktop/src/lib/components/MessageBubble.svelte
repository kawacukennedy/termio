<script lang="ts">
  import type { Message } from '$lib/stores/app';
  import { appStore } from '$lib/stores/app';
  import { Bot, User, Copy, ThumbsUp, ThumbsDown } from 'lucide-svelte';

  export let message: Message;

  let copied = false;

  async function copyToClipboard() {
    await navigator.clipboard.writeText(message.content);
    copied = true;
    setTimeout(() => copied = false, 2000);
  }
</script>

<div class="flex gap-4 {message.role === 'user' ? 'flex-row-reverse' : ''}">
  <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 {message.role === 'user' ? 'bg-[var(--color-surface-tertiary)]' : 'bg-[var(--color-accent)]'}">
    {#if message.role === 'user'}
      <User class="w-4 h-4 text-[var(--color-text-secondary)]" />
    {:else}
      <Bot class="w-4 h-4 text-white" />
    {/if}
  </div>
  
  <div class="flex-1 max-w-[70%] {message.role === 'user' ? 'text-right' : ''}">
    <div class="inline-block px-4 py-3 rounded-2xl text-left {message.role === 'user' ? 'bg-[var(--color-accent)] text-white' : 'bg-[var(--color-surface-secondary)] text-[var(--color-text-primary)]'}">
      <p class="text-sm whitespace-pre-wrap">{message.content}</p>
    </div>
    
    <div class="flex items-center gap-2 mt-2 {message.role === 'user' ? 'justify-end' : ''}">
      <span class="text-xs text-[var(--color-text-tertiary)]">
        {new Date(message.timestamp).toLocaleTimeString()}
      </span>
      
      {#if message.role === 'assistant'}
        <button 
          class="p-1 hover:bg-[var(--color-surface-primary)] rounded transition-colors"
          on:click={copyToClipboard}
          title="Copy"
        >
          {#if copied}
            <span class="text-xs text-[var(--color-success)]">Copied!</span>
          {:else}
            <Copy class="w-3 h-3 text-[var(--color-text-tertiary)]" />
          {/if}
        </button>
        
        <button 
          class="p-1 hover:bg-[var(--color-surface-primary)] rounded transition-colors"
          title="Good response"
        >
          <ThumbsUp class="w-3 h-3 text-[var(--color-text-tertiary)]" />
        </button>
        
        <button 
          class="p-1 hover:bg-[var(--color-surface-primary)] rounded transition-colors"
          title="Bad response"
        >
          <ThumbsDown class="w-3 h-3 text-[var(--color-text-tertiary)]" />
        </button>
      {/if}
    </div>
  </div>
</div>
