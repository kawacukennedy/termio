import psutil
import time
import gc
import threading
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Performance monitoring limited.")

class PerformanceOptimizerModule:
    def __init__(self, config):
        self.config = config
        self.optimizations = config['performance_optimizations']
        self.last_activity = time.time()
        self.idle_sleep_enabled = self.optimizations.get('idle_sleep', True)
        self.memory_cache = {}
        self.chunked_inference_enabled = True
        self.active_models = {}
        self.start_time = time.time()

    def monitor_cpu(self):
        if PSUTIL_AVAILABLE:
            return psutil.cpu_percent(interval=1)
        return 0.0

    def monitor_memory(self):
        if PSUTIL_AVAILABLE:
            return psutil.virtual_memory().percent
        return 0.0

    def lazy_load_module(self, module_name):
        """Lazy load a module when first accessed"""
        if module_name not in self.memory_cache:
            # Import and cache the module
            try:
                module = __import__(f'modules.{module_name}', fromlist=[module_name])
                self.memory_cache[module_name] = module
                return module
            except ImportError:
                return None
        return self.memory_cache[module_name]

    def unload_inactive_models(self, nlp_module=None, stt_module=None, tts_module=None):
        """Unload models after inactivity period"""
        inactive_threshold = self.config['model_loading_policy']['unload_triggers'][0].split()[0]  # "inactive for 5 minutes"
        inactive_seconds = int(inactive_threshold) * 60

        if time.time() - self.last_activity > inactive_seconds:
            # Unload models
            if nlp_module and hasattr(nlp_module, 'unload_model'):
                nlp_module.unload_model()
            if stt_module and hasattr(stt_module, 'unload_model'):
                stt_module.unload_model()
            if tts_module and hasattr(tts_module, 'unload_model'):
                tts_module.unload_model()
            gc.collect()

    def optimize_inference(self):
        """Enable inference optimizations"""
        # Set environment variables for optimization
        os.environ.setdefault('OMP_NUM_THREADS', '1')  # Limit OpenMP threads
        os.environ.setdefault('MKL_NUM_THREADS', '1')  # Limit MKL threads

        # Enable memory efficient caching
        if self.optimizations.get('memory_efficient_caching', True):
            self._setup_memory_caching()

    def _setup_memory_caching(self):
        """Setup memory-efficient caching for embeddings"""
        self.embedding_cache = {}
        self.cache_max_size = 100  # Max cached embeddings

    def cache_embedding(self, text, embedding):
        """Cache text embeddings with LRU eviction"""
        if len(self.embedding_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = min(self.embedding_cache.keys(), key=lambda k: self.embedding_cache[k]['timestamp'])
            del self.embedding_cache[oldest_key]

        self.embedding_cache[text] = {
            'embedding': embedding,
            'timestamp': time.time()
        }

    def get_cached_embedding(self, text):
        """Retrieve cached embedding if available"""
        if text in self.embedding_cache:
            self.embedding_cache[text]['timestamp'] = time.time()  # Update LRU
            return self.embedding_cache[text]['embedding']
        return None

    def chunked_inference(self, data, chunk_size=512):
        """Process data in chunks to manage memory"""
        if not self.chunked_inference_enabled:
            return data

        chunks = []
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunks.append(chunk)
        return chunks

    def idle_sleep(self):
        """Put system to idle sleep when inactive"""
        if self.idle_sleep_enabled and time.time() - self.last_activity > 600:  # 10 minutes
            # Reduce CPU usage
            time.sleep(1)  # Brief sleep to reduce activity

    def update_activity(self):
        self.last_activity = time.time()

    def get_status(self):
        """Get current performance status"""
        try:
            if not PSUTIL_AVAILABLE:
                return {
                    'cpu_percent': 0,
                    'memory_percent': 0,
                    'memory_used_mb': 0,
                    'disk_percent': 0,
                    'network_sent_mb': 0,
                    'network_recv_mb': 0,
                    'network_connections': 0,
                    'active_models': len(self.active_models),
                    'total_memory_mb': sum(model.get('memory_mb', 0) for model in self.active_models.values()),
                    'uptime_seconds': time.time() - self.start_time
                }

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            # Network connections may require permissions on some systems
            try:
                network_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                network_connections = 0

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'disk_percent': disk.percent,
                'network_sent_mb': network.bytes_sent / (1024 * 1024),
                'network_recv_mb': network.bytes_recv / (1024 * 1024),
                'network_connections': network_connections,
                'active_models': len(self.active_models),
                'total_memory_mb': sum(model.get('memory_mb', 0) for model in self.active_models.values()),
                'uptime_seconds': time.time() - self.start_time
            }
        except Exception as e:
            print(f"Performance monitoring error: {e}")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_used_mb': 0,
                'disk_percent': 0,
                'network_sent_mb': 0,
                'network_recv_mb': 0,
                'network_connections': 0,
                'active_models': 0,
                'total_memory_mb': 0,
                'uptime_seconds': time.time() - self.start_time
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

        return f"{cpu} {mem}"