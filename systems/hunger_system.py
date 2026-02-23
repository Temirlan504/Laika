class HungerSystem:
    def __init__(self):
        self.drain_rate = 2     # hunger per second
        self.starve_damage = 5  # health per second

    def update(self, player, dt):
        # Drain hunger
        player.current_hunger -= self.drain_rate * dt
        player.current_hunger = max(0, player.current_hunger)

        # Starvation damage
        if player.current_hunger == 0:
            player.take_damage(self.starve_damage * dt)
