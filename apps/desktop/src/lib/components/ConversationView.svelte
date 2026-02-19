<script lang="ts">
  import { currentConversation, appStore } from '$lib/stores/app';
  import MessageBubble from './MessageBubble.svelte';
  import { MessageSquare, Bot } from 'lucide-svelte';

  let messagesContainer: HTMLElement;
  let isTyping = false;

  $: if ($currentConversation?.messages && messagesContainer) {
    setTimeout(() => {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 0);
  }

  // Simulate typing indicator when there's a recent user message
  $: if ($currentConversation?.messages) {
    const lastMessage = $currentConversation.messages[$currentConversation.messages.length - 1];
    if (lastMessage?.role === 'user') {
      isTyping = true;
      setTimeout(() => isTyping = false, 1500);
    }
  }
</script>

<div class="flex-1 overflow-y-auto" bind:this={messagesContainer}>
  {#if $currentConversation}
    <div class="max-w-3xl mx-auto py-6 px-4 space-y-4">
      {#each $currentConversation.messages as message (message.id)}
        <MessageBubble {message} />
      {/each}
      
      {#if isTyping}
        <div class="flex gap-4">
          <div class="w-8 h-8 rounded-full bg-[var(--color-accent)] flex items-center justify-center flex-shrink-0">
            <Bot class="w-4 h-4 text-white" />
          </div>
          <div class="bg-[var(--color-surface-secondary)] rounded-2xl px-4 py-3">
            <div class="flex gap-1">
              <span class="w-2 h-2 bg-[var(--color-text-tertiary)] rounded-full animate-bounce" style="animation-delay: 0ms"></span>
              <span class="w-2 h-2 bg-[var(--color-text-tertiary)] rounded-full animate-bounce" style="animation-delay: 150ms"></span>
              <span class="w-2 h-2 bg-[var(--color-text-tertiary)] rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </div>
          </div>
        </div>
      {/if}
      
      {#if $currentConversation.messages.length === 0}
        <div class="text-center py-20">
          <MessageSquare class="w-12 h-12 mx-auto text-[var(--color-text-tertiary)] mb-4" />
          <p class="text-[var(--color-text-secondary)]">Start a conversation</p>
          <p class="text-[var(--color-text-tertiary)] text-sm mt-1">Send a message to begin</p>
        </div>
      {/if}
    </div>
  {:else}
    <div class="h-full flex items-center justify-center">
      <div class="text-center">
        <MessageSquare class="w-16 h-16 mx-auto text-[var(--color-text-tertiary)] mb-4" />
        <p class="text-[var(--color-text-secondary)] text-lg">Welcome to TERMIO</p>
        <p class="text-[var(--color-text-tertiary)] text-sm mt-1">Select a conversation or start a new one</p>
      </div>
    </div>
  {/if}
</div>
