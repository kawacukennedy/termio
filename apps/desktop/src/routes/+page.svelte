<script lang="ts">
  import '../app.css';
  import { appStore } from '$lib/stores/app';
  import TitleBar from '$lib/components/TitleBar.svelte';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import ConversationView from '$lib/components/ConversationView.svelte';
  import InputArea from '$lib/components/InputArea.svelte';
  import StatusBar from '$lib/components/StatusBar.svelte';
  import SettingsModal from '$lib/components/SettingsModal.svelte';
  import PluginModal from '$lib/components/PluginModal.svelte';
  import DevicePairingModal from '$lib/components/DevicePairingModal.svelte';
  import { onMount } from 'svelte';

  let showSettings = false;
  let showPlugins = false;
  let showDevicePairing = false;

  onMount(async () => {
    // Load initial data from server
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      
      // Load conversations
      const conversations = await invoke('get_conversations', { 
        serverUrl: $appStore.serverUrl 
      });
      console.log('Loaded conversations:', conversations);
    } catch (e) {
      console.log('Running in browser mode or server not available');
    }
  });

  function handleNewConversation() {
    const id = crypto.randomUUID();
    const conversation = {
      id,
      title: 'New Conversation',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    appStore.addConversation(conversation);
    appStore.setCurrentConversation(id);
  }
</script>

<div class="h-screen flex flex-col bg-[var(--color-bg-primary)]">
  <TitleBar 
    on:settings={() => showSettings = true}
    on:plugins={() => showPlugins = true}
    on:pairing={() => showDevicePairing = true}
  />
  
  <div class="flex-1 flex overflow-hidden">
    <Sidebar 
      on:newConversation={handleNewConversation}
    />
    
    <main class="flex-1 flex flex-col">
      <ConversationView />
      <InputArea />
    </main>
  </div>
  
  <StatusBar />
</div>

{#if showSettings}
  <SettingsModal on:close={() => showSettings = false} />
{/if}

{#if showPlugins}
  <PluginModal on:close={() => showPlugins = false} />
{/if}

{#if showDevicePairing}
  <DevicePairingModal on:close={() => showDevicePairing = false} />
{/if}
