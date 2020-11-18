import pygame
from pygame.locals import *

from common.Utilities import Utilities
from common.Button import Button


class LanguageButton(Button):
    def __init__(self, screen, center, image, tappedImage, notVisibleImage, text, color, tappedColor, selectedColor, font, onClickCallback):
        super().__init__(screen, center, image, tappedImage, text, color, tappedColor, font, onClickCallback)
        self.notVisibleImage = notVisibleImage

    def draw(self):
        super().draw()

        if not self.visible:
            self.screen.blit(self.notVisibleImage, (self.rect.center[0] - self.notVisibleImage.get_width() // 2, self.rect.center[1] - self.notVisibleImage.get_height() // 2))
