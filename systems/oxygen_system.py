class OxygenSystem:
    def __init__(self):
        self.drain_rate = 12
        self.drown_damage = 20

    def update(self, player, dt):
        player.current_oxygen -= self.drain_rate * dt
        player.current_oxygen = max(0, player.current_oxygen)

        if player.current_oxygen == 0:
            player.take_damage(self.drown_damage * dt)
