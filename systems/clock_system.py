class ClockSystem:
    def __init__(self, day_cycle):
        self.minutes = 6 * 60
        self.speed = 1
        self.day_cycle = day_cycle
        self.subscribers = []

    def update(self, dt):
        prev_day_minute = int(self.minutes)
        self.minutes += self.speed * dt

        if self.minutes >= 24 * 60:
            self.minutes -= 24 * 60
            self._notify_midnight()

        if int(self.minutes // 60) != int(prev_day_minute // 60):
            self._notify_time_change()

    @property
    def hour(self):
        return int(self.minutes // 60)

    @property
    def minute(self):
        return int(self.minutes % 60)

    def time_string(self):
        return f"{self.hour:02d}:{self.minute:02d}"

    def can_sleep(self):
        return self.hour >= 20

    def set_time(self, hour, minute=0):
        self.minutes = hour * 60 + minute
        self._notify_time_change()

    def subscribe(self, obj):
        if obj not in self.subscribers:
            self.subscribers.append(obj)

    def _notify_midnight(self):
        self.day_cycle.reset_cycle()
        self.day_cycle.try_advance_day("midnight")
        for sub in self.subscribers:
            if hasattr(sub, "on_midnight"):
                sub.on_midnight()

    def _notify_time_change(self):
        for sub in self.subscribers:
            if hasattr(sub, "on_time_change"):
                sub.on_time_change(self.hour, self.minute)
