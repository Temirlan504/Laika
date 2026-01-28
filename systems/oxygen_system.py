class OxygenSystem:
    def __init__(self):
        self.drain_rate = 12      # oxygen per second
        self.drown_damage = 20    # health per second when oxygen = 0

    def update(self, player, dt):
        # Always drain oxygen in space
        player.oxygen -= self.drain_rate * dt
        player.oxygen = max(0, player.oxygen)

        # Suffocation damage
        if player.oxygen == 0:
            player.take_damage(self.drown_damage * dt)

        print(f"Oxygen: {player.oxygen:.2f}")
