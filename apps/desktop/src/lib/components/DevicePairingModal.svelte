<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { X, Smartphone, QrCode, Copy, Check } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  let pairingCode = 'TERMIO-ABCD-1234';
  let copied = false;
  let scanned = false;

  async function copyCode() {
    await navigator.clipboard.writeText(pairingCode);
    copied = true;
    setTimeout(() => copied = false, 2000);
  }

  function simulateScan() {
    scanned = true;
    setTimeout(() => {
      dispatch('close');
    }, 2000);
  }
</script>

<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" on:click|self={() => dispatch('close')}>
  <div class="bg-[var(--color-bg-secondary)] rounded-xl w-[400px] overflow-hidden shadow-2xl">
    <div class="flex items-center justify-between p-4 border-b border-[var(--color-surface-tertiary)]">
      <h2 class="text-lg font-semibold text-[var(--color-text-primary)]">Device Pairing</h2>
      <button 
        class="p-1 hover:bg-[var(--color-surface-primary)] rounded-lg transition-colors"
        on:click={() => dispatch('close')}
      >
        <X class="w-5 h-5 text-[var(--color-text-secondary)]" />
      </button>
    </div>
    
    <div class="p-6">
      <div class="text-center mb-6">
        <div class="w-16 h-16 mx-auto bg-[var(--color-surface-primary)] rounded-full flex items-center justify-center mb-4">
          <Smartphone class="w-8 h-8 text-[var(--color-accent)]" />
        </div>
        <h3 class="text-lg font-medium text-[var(--color-text-primary)]">Pair a new device</h3>
        <p class="text-sm text-[var(--color-text-tertiary)] mt-1">
          Enter this code on your other device or scan the QR code
        </p>
      </div>
      
      <div class="bg-[var(--color-surface-primary)] rounded-lg p-4 mb-6">
        <div class="text-center">
          <span class="text-2xl font-mono font-bold text-[var(--color-accent)] tracking-wider">
            {pairingCode}
          </span>
        </div>
        
        <button 
          class="w-full flex items-center justify-center gap-2 mt-4 py-2 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
          on:click={copyCode}
        >
          {#if copied}
            <Check class="w-4 h-4 text-[var(--color-success)]" />
            <span class="text-[var(--color-success)]">Copied!</span>
          {:else}
            <Copy class="w-4 h-4" />
            <span>Copy code</span>
          {/if}
        </button>
      </div>
      
      <div class="text-center mb-6">
        <div class="w-32 h-32 mx-auto bg-white rounded-lg flex items-center justify-center">
          <QrCode class="w-24 h-24 text-black" />
        </div>
        <p class="text-xs text-[var(--color-text-tertiary)] mt-2">Scan with mobile app</p>
      </div>
      
      <button 
        class="w-full py-3 bg-[var(--color-accent)] text-white rounded-lg hover:bg-[var(--color-accent-hover)] transition-colors"
        on:click={simulateScan}
      >
        {#if scanned}
          Device Paired!
        {:else}
          Simulate Scan (Demo)
        {/if}
      </button>
    </div>
  </div>
</div>
