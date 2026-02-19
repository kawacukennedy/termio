<script lang="ts">
  import { appStore, unreadNotifications } from '$lib/stores/app';
  import { Bell, Wifi, WifiOff, HardDrive } from 'lucide-svelte';

  $: serverStatus = $appStore.serverUrl ? 'connected' : 'disconnected';
</script>

<footer class="h-8 bg-[var(--color-bg-secondary)] border-t border-[var(--color-surface-tertiary)] flex items-center justify-between px-4 text-xs">
  <div class="flex items-center gap-4">
    <div class="flex items-center gap-2">
      {#if serverStatus === 'connected'}
        <Wifi class="w-3 h-3 text-[var(--color-success)]" />
        <span class="text-[var(--color-text-tertiary)]">Connected</span>
      {:else}
        <WifiOff class="w-3 h-3 text-[var(--color-error)]" />
        <span class="text-[var(--color-text-tertiary)]">Offline</span>
      {/if}
    </div>
    
    <div class="flex items-center gap-2">
      <HardDrive class="w-3 h-3 text-[var(--color-text-tertiary)]" />
      <span class="text-[var(--color-text-tertiary)]">Local</span>
    </div>
  </div>
  
  <div class="flex items-center gap-4">
    <button class="flex items-center gap-2 hover:text-[var(--color-text-primary)] transition-colors">
      <Bell class="w-3 h-3" />
      <span class="text-[var(--color-text-tertiary)]">
        {#if $unreadNotifications > 0}
          {$unreadNotifications} notifications
        {:else}
          No notifications
        {/if}
      </span>
    </button>
    
    <span class="text-[var(--color-text-tertiary)]">TERMIO v2.0.0</span>
  </div>
</footer>
