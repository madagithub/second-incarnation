from pygame.locals import Rect

from common.Utilities import Utilities


class Button:
    def __init__(self, screen, rect, image, tappedImage, text, color, selectedColor, font, onClickCallback, sensitivityFactor=1.0):
        self.screen = screen
        self.rect = rect
        self.image = image
        self.tappedImage = tappedImage
        self.color = color
        self.selectedColor = selectedColor
        self.text = text
        self.font = font
        self.visible = True

        self.createText(text, font)

        self.onClickCallback = onClickCallback
        self.isMouseDownOnButton = False
        self.sensitivityFactor = sensitivityFactor

        self.updateTapRect()

    def updateTapRect(self):
        self.tapRect = Rect(self.rect.center[0] - self.rect.width * self.sensitivityFactor // 2, self.rect.center[1] - self.rect.height * self.sensitivityFactor // 2, self.rect.width * self.sensitivityFactor, self.rect.height * self.sensitivityFactor)

    def createText(self, text, font):
        if text is not None:
            self.textBox = font.render(text, True, self.color)
            self.selectedTextBox = font.render(text, True, self.selectedColor)
        else:
            self.textBox = None

    def draw(self):
        if self.visible:
            self.screen.blit(self.tappedImage if self.isMouseDownOnButton else self.image, (self.rect.left, self.rect.top))

            if self.textBox is not None:
                Utilities.drawTextOnCenter(self.screen, self.selectedTextBox if self.isMouseDownOnButton else self.textBox, self.rect.center)

    def onMouseDown(self, position):
        if self.visible:
            self.isMouseDownOnButton = self.tapRect.collidepoint(position)

    def onMouseUp(self, position):
        if self.visible:
            if self.tapRect.collidepoint(position) and self.isMouseDownOnButton:
                self.onClickCallback()

            self.isMouseDownOnButton = False
