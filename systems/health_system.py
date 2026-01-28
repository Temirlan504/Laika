class HealthSystem:
    def __init__(self):
        self.regen_rate = 1  # per second

    def update(self, player, dt):
        if player.hunger > 20 and player.health < player.max_health:
            player.heal(self.regen_rate * dt)

        print(f"Health: {player.health:.2f}")
