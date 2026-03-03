class OxygenSystem:
    def __init__(self):
        self.drain_rate = 0.5  # Oxygen drained per second
        self.drown_damage = 1

    def update(self, player, dt):
        player.current_oxygen -= self.drain_rate * dt
        player.current_oxygen = max(0, player.current_oxygen)

        if player.current_oxygen == 0:
            player.take_damage(self.drown_damage * dt)
