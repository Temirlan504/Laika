class HungerSystem:
    def __init__(self):
        self.drain_rate = 2      # hunger per second
        self.starve_damage = 5  # health per second

    def update(self, player, dt):
        # Drain hunger
        player.hunger -= self.drain_rate * dt
        player.hunger = max(0, player.hunger)

        # Starvation damage
        if player.hunger == 0:
            player.take_damage(self.starve_damage * dt)

        print(f"Hunger: {player.hunger:.2f}")
