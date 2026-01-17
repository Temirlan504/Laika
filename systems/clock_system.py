class ClockSystem:
    def __init__(self, day_cycle):
        self.minutes = 6 * 60  # start at 06:00
        self.speed = 1
        self.day_cycle = day_cycle
        self.subscribers = []

    def update(self, dt):
        previous_hour = self.hour

        self.minutes += self.speed * dt

        # Midnight rollover
        if self.minutes >= 24 * 60:
            self.minutes = 0
            self._notify_midnight()

        if self.hour != previous_hour:
            self._notify_time_change()

    # ---- Time helpers ----
    @property
    def hour(self):
        return int(self.minutes // 60)

    @property
    def minute(self):
        return int(self.minutes % 60)

    def time_string(self):
        return f"{self.hour:02d}:{self.minute:02d}"

    # ---- Sleeping rules ----
    def can_sleep(self):
        return self.hour >= 20 or self.hour < 4
    
    def set_time(self, hour, minute=0):
        self.minutes = hour * 60 + minute
        self._notify_time_change()

    # ---- Observer pattern ----
    def subscribe(self, obj):
        if obj not in self.subscribers:
            self.subscribers.append(obj)

    def _notify_midnight(self):
        for sub in self.subscribers:
            if hasattr(sub, "on_midnight"):
                sub.on_midnight()

    def _notify_time_change(self):
        for sub in self.subscribers:
            if hasattr(sub, "on_time_change"):
                sub.on_time_change(self.hour, self.minute)
