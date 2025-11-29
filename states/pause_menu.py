import pygame
from utils.settings import *

class PauseMenuState:
    def __init__(self, state_machine, game):
        self.state_machine = state_machine
        self.game = game
        self.screen = game.screen

        # --- Menu options ---
        self.options = ["Continue", "Quit"]
        self.selected_index = 0

        # --- Tint overlay ---
        self.tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.tint.set_alpha(150)  # 0 = fully transparent, 255 = fully opaque
        self.tint.fill((0, 0, 0))  # black tint

        # --- Font ---
        self.font = pygame.font.SysFont(None, 48)

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_machine.change_state("level")
                elif event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()

    def confirm_selection(self):
        selected = self.options[self.selected_index]
        if selected == "Continue":
            self.state_machine.change_state("level")
        elif selected == "Quit":
            pygame.quit()
            exit()

    def run(self, dt):
        # --- Draw the level behind the menu ---
        # Run the level state's draw/update without processing input
        self.game.state_machine.states["level"](self.state_machine, self.game).all_sprites.draw(self.screen)

        # --- Draw the tinted overlay ---
        self.screen.blit(self.tint, (0, 0))

        # --- Draw menu options ---
        for i, option in enumerate(self.options):
            text = option
            if i == self.selected_index:
                text = "> " + text  # show selection
                

            surf = self.font.render(text, True, (255, 255, 255))
            x = SCREEN_WIDTH // 2 - surf.get_width() // 2
            y = SCREEN_HEIGHT // 2 + i * 60
            self.screen.blit(surf, (x, y))
