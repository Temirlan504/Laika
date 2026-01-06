class DayCycle:
    def __init__(self):
        self.day = 0
        self.subscribers = []

    # day_cycle.py
    def sleep(self):
        if getattr(self, "is_sleeping", False):
            return
        self.is_sleeping = True
        self.next_day()
        self.is_sleeping = False

    def next_day(self):
        self.day += 1
        print(f"SOL {self.day}")

        for subscriber in self.subscribers:
            subscriber.on_new_day(self.day)

    def subscribe(self, obj):
        if obj not in self.subscribers:
            self.subscribers.append(obj)

