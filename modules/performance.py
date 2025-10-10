import psutil
import time
import gc

class PerformanceOptimizerModule:
    def __init__(self, config):
        self.config = config
        self.optimizations = config['performance_optimizations']
        self.last_activity = time.time()

    def monitor_cpu(self):
        return psutil.cpu_percent(interval=1)

    def monitor_memory(self):
        return psutil.virtual_memory().percent

    def lazy_load_module(self, module_name):
        # Placeholder for lazy loading
        pass

    def unload_inactive_models(self, nlp_module=None, stt_module=None, tts_module=None):
        if time.time() - self.last_activity > 300:  # 5 minutes
            # Unload models
            if nlp_module:
                nlp_module.unload_if_inactive()
            if stt_module:
                stt_module.unload_if_inactive()
            if tts_module:
                tts_module.unload_if_inactive()
            gc.collect()

    def optimize_inference(self):
        # Enable optimizations
        pass

    def update_activity(self):
        self.last_activity = time.time()

    def get_status(self):
        """Get comprehensive system status"""
        status = {
            'cpu_percent': self.monitor_cpu(),
            'memory_percent': self.monitor_memory(),
            'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
            'active_time_seconds': time.time() - self.last_activity,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections())
        }

        # Add GPU info if available
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                status['gpu_percent'] = gpus[0].load * 100
                status['gpu_memory_percent'] = gpus[0].memoryUtil * 100
            else:
                status['gpu_percent'] = 0
                status['gpu_memory_percent'] = 0
        except ImportError:
            status['gpu_percent'] = 'N/A'
            status['gpu_memory_percent'] = 'N/A'

        return status

    def format_status_display(self):
        """Format status for display in status bar"""
        status = self.get_status()

        cpu = f"CPU:{status['cpu_percent']:.1f}%"
        mem = f"MEM:{status['memory_percent']:.1f}%"
        gpu = f"GPU:{status['gpu_percent']:.1f}%" if status['gpu_percent'] != 'N/A' else "GPU:N/A"

        return f"{cpu} {mem} {gpu}"