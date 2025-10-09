import time

class PerformanceOptimizerModule:
    def __init__(self):
        self.idle_threshold = 30  # seconds
        self.last_activity = time.time()
        self.lazy_loaded = {}

    def update_activity(self):
        self.last_activity = time.time()

    def is_idle(self):
        return time.time() - self.last_activity > self.idle_threshold

    def lazy_load(self, module_name, load_func):
        if module_name not in self.lazy_loaded:
            self.lazy_loaded[module_name] = load_func()
        return self.lazy_loaded[module_name]

    def optimize(self):
        # Sleep if idle
        if self.is_idle():
            time.sleep(1)