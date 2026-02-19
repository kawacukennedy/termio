<script lang="ts">
  import { appStore, currentConversation } from '$lib/stores/app';
  import { Send, Mic, MicOff, Loader2, Smile, Paperclip } from 'lucide-svelte';

  let input = '';
  let isRecording = false;
  let isLoading = false;
  let showEmojiPicker = false;

  const emojis = ['😀', '😂', '🤔', '👍', '👎', '❤️', '🎉', '🔥', '💡', '✨', '😊', '🙄', '😢', '😮', '🤯', '🥳'];

  async function sendMessage() {
    if (!input.trim() || !$currentConversation || isLoading) return;
    
    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user' as const,
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    
    appStore.addMessage($currentConversation.id, userMessage);
    input = '';
    isLoading = true;
    
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      
      const response = await invoke('send_message', {
        message: userMessage.content,
        serverUrl: $appStore.serverUrl,
      });
      
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: response as string,
        timestamp: new Date().toISOString(),
      };
      
      appStore.addMessage($currentConversation.id, assistantMessage);
    } catch (e) {
      console.error('Failed to send message:', e);
      
      const assistantMessage = {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: `Demo mode: You said "${userMessage.content}". Connect to a TERMIO server to enable AI responses.`,
        timestamp: new Date().toISOString(),
      };
      
      appStore.addMessage($currentConversation.id, assistantMessage);
    } finally {
      isLoading = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function toggleRecording() {
    isRecording = !isRecording;
  }

  function toggleEmojiPicker() {
    showEmojiPicker = !showEmojiPicker;
  }

  function insertEmoji(emoji: string) {
    input += emoji;
    showEmojiPicker = false;
  }

  function handleAttachment() {
    // File attachment placeholder
    console.log('Attachment clicked');
  }
</script>

<div class="border-t border-[var(--color-surface-tertiary)] bg-[var(--color-bg-secondary)] p-4">
  <div class="max-w-3xl mx-auto">
    <div class="flex items-end gap-3">
      <button
        class="p-3 rounded-full bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
        on:click={handleAttachment}
        title="Attach file"
      >
        <Paperclip class="w-5 h-5" />
      </button>
      
      <div class="flex-1 relative">
        <textarea
          bind:value={input}
          on:keydown={handleKeydown}
          placeholder="Type your message..."
          rows="1"
          class="w-full px-4 py-3 bg-[var(--color-surface-primary)] border border-[var(--color-surface-tertiary)] rounded-2xl text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)] resize-none focus:outline-none focus:border-[var(--color-accent)]"
        ></textarea>
      </div>
      
      <div class="relative">
        <button
          class="p-3 rounded-full bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] transition-colors"
          on:click={toggleEmojiPicker}
          title="Emoji"
        >
          <Smile class="w-5 h-5" />
        </button>
        
        {#if showEmojiPicker}
          <div class="absolute bottom-full right-0 mb-2 bg-[var(--color-surface-secondary)] border border-[var(--color-surface-tertiary)] rounded-lg shadow-lg p-2">
            <div class="grid grid-cols-8 gap-1">
              {#each emojis as emoji}
                <button 
                  class="p-1 text-xl hover:bg-[var(--color-surface-tertiary)] rounded"
                  on:click={() => insertEmoji(emoji)}
                >
                  {emoji}
                </button>
              {/each}
            </div>
          </div>
        {/if}
      </div>
      
      <button
        class="p-3 rounded-full transition-colors {isRecording ? 'bg-[var(--color-error)] text-white' : 'bg-[var(--color-surface-secondary)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)]'}"
        on:click={toggleRecording}
        title={isRecording ? 'Stop recording' : 'Start voice input'}
      >
        {#if isRecording}
          <MicOff class="w-5 h-5" />
        {:else}
          <Mic class="w-5 h-5" />
        {/if}
      </button>
      
      <button
        class="p-3 rounded-full bg-[var(--color-accent)] text-white hover:bg-[var(--color-accent-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        on:click={sendMessage}
        disabled={!input.trim() || isLoading}
      >
        {#if isLoading}
          <Loader2 class="w-5 h-5 animate-spin" />
        {:else}
          <Send class="w-5 h-5" />
        {/if}
      </button>
    </div>
    
    <p class="text-center text-xs text-[var(--color-text-tertiary)] mt-2">
      Press Enter to send, Shift+Enter for new line
    </p>
  </div>
</div>
