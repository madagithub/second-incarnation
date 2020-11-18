from functools import partial

import pygame
from pygame.locals import Rect, Color

from common.Config import Config
from common.Button import Button
from common.TouchScreen import TouchScreen
from common.LanguageButton import LanguageButton
from common.Log import Log


class SecondIncarnation:

    CONFIG_FILENAME = 'assets/config/config.json'
    LOG_FILE_PATH = 'timeline.log'

    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 100

    def __init__(self):
        Log.init(self.LOG_FILE_PATH)
        Log.getLogger().info('START')
        self.touchPos = (0, 0)
        self.screen = None
        self.cursor = None
        self.config = None
        self.buttons = []
        self.mainButtons = []
        self.blitCursor = True
        self.touchScreen = None
        self.background = None
        self.languageButtons = []

    def start(self):
        self.config = Config(self.CONFIG_FILENAME)

        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.mouse.set_visible(False)

        self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
        self.cursor = pygame.image.load('assets/images/cursor.png').convert_alpha()

        if self.config.isTouch():
            print('Loading touch screen...')
            self.touchScreen = TouchScreen(self.config.getTouchDevicePartialName(), (self.config.getTouchScreenMaxX(), self.config.getTouchScreenMaxY()))

            if not self.touchScreen.setup():
                self.config.setTouch(False)

        self.background = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/main.png').convert_alpha()
        self.isMainScreen = True

        for button in self.config.getSubscreenButtons():
            print(button)
            buttonImage = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['image']).convert_alpha()
            buttonTappedImage = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['tappedImage']).convert_alpha()
            buttonInstance = Button(self.screen, (button['x'], button['y']),
                                    buttonImage, buttonTappedImage, None, None, None, None, partial(self.onButtonClicked, button));
            self.buttons.append(buttonInstance)
            self.mainButtons.append(buttonInstance)


        # for i in range(len(self.config.getLanguages())):
        #     language = self.config.getLanguages()[i]

        #     languageButton = LanguageButton(self.screen, Rect(i * 63 + 15, 1010, languageButtonImage.get_width(), languageButtonImage.get_height()), 
        #         languageButtonImage, languageButtonTappedImage, languageButtonSelectedImage, language['buttonText'], DOT_TEXT_COLOR, DOT_SELECTED_TEXT_COLOR, DOT_SELECTED_TEXT_COLOR, languageFont, partial(self.languageClicked, i))
        #     if language['prefix'] == self.config.languagePrefix:
        #         languageButton.visible = False

        #     self.languageButtons.append(languageButton)
        #     self.buttons.append(languageButton)

        Log.getLogger().info('INIT')

        self.loop()

    def onButtonClicked(self, button):
        self.background = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['screenImage'])
        self.isMainScreen = False

    def languageClicked(self, index):
        self.config.changeLanguage(index)
        Log.getLogger().info('LANGUAGE_CHANGED,' + self.config.languagePrefix)
        self.onLanguageChanged()

    def onLanguageChanged(self):
        languages = self.config.getLanguages()
        for i in range(len(languages)):
            if i == self.config.languageIndex:
                self.languageButtons[i].visible = False
            else:
                self.languageButtons[i].visible = True

    def onMouseDown(self, pos):
        for button in self.buttons:
            button.onMouseDown(pos)

    def onMouseUp(self, pos):
        for button in self.buttons:
            button.onMouseUp(pos)

    def onMouseMove(self, pos):
        pass

    def draw(self, _):
        self.screen.blit(self.background, (0, 0))

        if self.isMainScreen:
            for button in self.mainButtons:
                button.draw()
        else:
            pass

    def handleEvents(self):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self.config.isTouch():
                    self.onMouseDown(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if not self.config.isTouch():
                    self.onMouseUp(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        return True

    def loop(self):
        try:
            isGameRunning = True
            clock = pygame.time.Clock()
            lastTime = pygame.time.get_ticks()
            font = pygame.font.Font(None, 30)

            while isGameRunning:
                isGameRunning = self.handleEvents()

                if self.config.isTouch():
                    event = self.touchScreen.readUpDownEvent()
                    while event is not None:
                        if event['type'] == TouchScreen.DOWN_EVENT:
                            self.onMouseDown(event['pos'])
                        elif event['type'] == TouchScreen.UP_EVENT:
                            self.onMouseUp(event['pos'])
                        event = self.touchScreen.readUpDownEvent()

                if not self.config.isTouch():
                    self.onMouseMove(pygame.mouse.get_pos())
                else:
                    pos = self.touchScreen.getPosition()
                    self.onMouseMove(pos)

                self.screen.fill([0, 0, 0])
                currTime = pygame.time.get_ticks()
                dt = currTime - lastTime
                lastTime = currTime

                self.draw(dt / 1000)

                if not self.config.isTouch() and self.blitCursor:
                    self.screen.blit(self.cursor, (pygame.mouse.get_pos()))

                if self.config.showFPS():
                    fps = font.render(str(int(clock.get_fps())), True, Color('white'))
                    self.screen.blit(fps, (50, 50))

                pygame.display.flip()
                clock.tick(60)

            pygame.quit()

        except Exception:
            Log.getLogger().exception('ERROR,Error occured!')


if __name__ == '__main__':
    SecondIncarnation().start()
