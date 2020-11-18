from functools import partial

import pygame
from pygame.locals import Rect, Color

from common.Config import Config
from common.Button import Button
from common.TouchScreen import TouchScreen
from common.LanguageButton import LanguageButton
from common.Log import Log

#TODO: Preload all images

class SecondIncarnation:

    CONFIG_FILENAME = 'assets/config/config.json'
    LOG_FILE_PATH = 'timeline.log'

    HOME_BUTTON_X = 1038
    HOME_BUTTON_Y = 50

    def __init__(self):
        Log.init(self.LOG_FILE_PATH)
        Log.getLogger().info('START')
        self.touchPos = (0, 0)
        self.screen = None
        self.cursor = None
        self.config = None
        self.mainButtons = []
        self.languageButtons = []
        self.subscreenButtons = []
        self.blitCursor = True
        self.touchScreen = None
        self.background = None
        self.mainBackground = None
        self.isMainScreen = True

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

        self.mainBackground = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/main.png').convert_alpha()
        self.background = self.mainBackground

        self.subscreenButtons.append(Button(self.screen, (self.HOME_BUTTON_X, self.HOME_BUTTON_Y), 
            pygame.image.load('assets/images/home.png').convert_alpha(), pygame.image.load('assets/images/home.png').convert_alpha(), None, None, None, None, self.onHomeClicked))

        self.loadMainButtons()

        for i in range(len(self.config.getLanguages())):
            language = self.config.getLanguages()[i]

            prefix = language['prefix']
            languageButtonImage = pygame.image.load('assets/images/' + prefix + '.png').convert_alpha()
            languageButtonTappedImage = pygame.image.load('assets/images/' + prefix + '-tapped.png').convert_alpha()

            languageButton = LanguageButton(self.screen, (i * 200 + 15, 100),#1010),
                languageButtonImage, languageButtonTappedImage, languageButtonTappedImage, None, None, None, None, None, partial(self.languageClicked, i))
            if language['prefix'] == self.config.languagePrefix:
                languageButton.visible = False

            self.languageButtons.append(languageButton)

        Log.getLogger().info('INIT')

        self.loop()

    def onHomeClicked(self):
        self.background = self.mainBackground
        self.isMainScreen = True;

    def onButtonClicked(self, button):
        self.background = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['screenImage'])
        self.isMainScreen = False

    #TODO: Reuse in init
    def loadBackground(self):
        if self.isMainScreen:
            self.mainBackground = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/main.png').convert_alpha()
            self.background = self.mainBackground
            self.loadMainButtons()
        else:
            self.background = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['screenImage'])

    def loadMainButtons(self):
        self.mainButtons = []
        for button in self.config.getSubscreenButtons():
            buttonImage = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['image']).convert_alpha()
            buttonTappedImage = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['tappedImage']).convert_alpha()
            buttonInstance = Button(self.screen, (button['x'], button['y']),
                                    buttonImage, buttonTappedImage, None, None, None, None, partial(self.onButtonClicked, button));
            self.mainButtons.append(buttonInstance)

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
        self.loadBackground()

    def getButtons(self):
        if self.isMainScreen:
            return self.mainButtons + self.languageButtons
        else:
            return self.subscreenButtons + self.languageButtons

    def onMouseDown(self, pos):
        for button in self.getButtons():
            button.onMouseDown(pos)

    def onMouseUp(self, pos):
        for button in self.getButtons():
            button.onMouseUp(pos)

    def onMouseMove(self, pos):
        pass

    def draw(self, _):
        self.screen.blit(self.background, (0, 0))

        for button in self.getButtons():
            button.draw()

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
