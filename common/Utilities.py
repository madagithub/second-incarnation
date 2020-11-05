import pygame
from pygame.locals import *


class Utilities:

    @staticmethod
    def drawTextOnCenter(screen, textBox, centerPoint):
        screen.blit(textBox, (centerPoint[0] - textBox.get_width() // 2, centerPoint[1] - textBox.get_height() // 2))

    @staticmethod
    def drawTextsOnCenter(screen, textBoxes, centerPoint, lineGap):
        totalHeight = 0
        for textBox in textBoxes:
            totalHeight += textBox.get_height()
        if len(textBoxes) > 1:
            totalHeight += lineGap * (len(textBoxes) - 1)

        currY = centerPoint[1] - totalHeight // 2

        for textBox in textBoxes:
            Utilities.drawTextOnCenterX(screen, textBox, (centerPoint[0], currY))
            currY += lineGap

    @staticmethod
    def drawTextOnCenterX(screen, textBox, centerPoint):
        screen.blit(textBox, (centerPoint[0] - textBox.get_width() // 2, centerPoint[1]))

    @staticmethod
    def drawTextOnLeftX(screen, textBox, centerPoint):
        screen.blit(textBox, (centerPoint[0], centerPoint[1]))

    @staticmethod
    def drawTextsOnCenterX(screen, textBoxes, position, lineGap):
        for i in range(len(textBoxes)):
            textBox = textBoxes[i]
            Utilities.drawTextOnCenterX(screen, textBox, (position[0], position[1] + i * lineGap))

    @staticmethod
    def drawTextsOnLeftX(screen, textBoxes, position, lineGap):
        for i in range(len(textBoxes)):
            textBox = textBoxes[i]
            Utilities.drawTextOnLeftX(screen, textBox, (position[0], position[1] + i * lineGap))

    @staticmethod
    def drawTextsOnRightX(screen, textBoxes, position, lineGap):
        for i in range(len(textBoxes)):
            textBox = textBoxes[i]
            Utilities.drawTextOnLeftX(screen, textBox, (position[0] - textBox.get_width(), position[1] + i * lineGap))

    @staticmethod
    def renderTextList(config, font, key, color=(255, 255, 255)):
        textBoxes = []
        for text in config.getTextList(key):
            textBoxes.append(font.render(text, True, color))

        return textBoxes
