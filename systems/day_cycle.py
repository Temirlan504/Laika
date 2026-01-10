class DayCycle:
    def __init__(self):
        self.day = 0
        self.day_advanced = False
        self.subscribers = []

    def on_midnight(self):
        self.next_day()

    def sleep(self):
        if getattr(self, "is_sleeping", False):
            return
        self.is_sleeping = True
        self.next_day()
        self.is_sleeping = False

    def next_day(self):
        if self.day_advanced:
            return

        self.day += 1
        self.day_advanced = True
        print(f"SOL {self.day}")

        for sub in self.subscribers:
            if hasattr(sub, "on_new_day"):
                sub.on_new_day(self.day)
    
    def start_new_day(self):
        self.day_advanced = False

    def subscribe(self, obj):
        if obj not in self.subscribers:
            self.subscribers.append(obj)
