import pygame
from pygame.locals import *

from common.Utilities import Utilities
from common.Button import Button


class LanguageButton(Button):
    def __init__(self, screen, rect, image, tappedImage, notVisibleImage, text, color, tappedColor, selectedColor, font, onClickCallback):
        super().__init__(screen, rect, image, tappedImage, text, color, tappedColor, font, onClickCallback)

        self.selectedTextBox = font.render(text, True, selectedColor)
        self.notVisibleImage = notVisibleImage

    def draw(self):
        super().draw()

        if not self.visible:
            self.screen.blit(self.notVisibleImage, (self.rect.left, self.rect.top))
            if self.selectedTextBox is not None:
                Utilities.drawTextOnCenter(self.screen, self.selectedTextBox, self.rect.center)
