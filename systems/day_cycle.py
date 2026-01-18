class DayCycle:
    def __init__(self):
        self.day = 0
        self.day_advanced = False
        self.subscribers = []

    def try_advance_day(self, reason):
        if self.day_advanced:
            return

        self.day += 1
        self.day_advanced = True
        print(f"SOL {self.day} ({reason})")

        for sub in self.subscribers:
            if hasattr(sub, "on_new_day"):
                sub.on_new_day(self.day)

    def reset_cycle(self):
        self.day_advanced = False

    def subscribe(self, obj):
        if obj not in self.subscribers:
            self.subscribers.append(obj)
