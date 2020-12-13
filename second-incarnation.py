from functools import partial
import time

import serial

import pygame
from pygame.locals import Color

from common.Config import Config
from common.Button import Button
from common.TouchScreen import TouchScreen
from common.LanguageButton import LanguageButton
from common.Log import Log

#TODO: Preload all images

class SecondIncarnation:

    CONFIG_FILENAME = 'assets/config/config.json'
    LOG_FILE_PATH = 'timeline.log'

    HOME_BUTTON_X = 50
    HOME_BUTTON_Y = 1038

    PLAY_BUTTON_X = 959
    PLAY_BUTTON_Y = 300

    EMERGENCY_STOP_RESPONSE = b'2'
    STOP_RESPONSE = b'0'

    START_COMMAND = b'1'

    MACHINE_CHECK_INTERVAL = 1
    WAIT_FOR_START_INTERVAL = 0.1

    MACHINE_PORT_NAME = '/dev/ttyUSB0'

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
        self.playButton = None
        self.blitCursor = True
        self.touchScreen = None
        self.background = None
        self.mainBackground = None
        self.isMainScreen = True
        self.screenImage = None
        self.serialPort = None
        self.machinePlaying = False

    def openSerialPort(self):
        if self.serialPort is None:
            try:
                self.serialPort = serial.Serial(self.MACHINE_PORT_NAME, 115200, timeout=0)
            except Exception as e:
                print(str(e))
                self.serialPort = None

    # Try to send to serial, and if an error occurs, open serial port again for X retries
    def sendToSerialPort(self, originalCommand):
        print("Attempting sending " + str(originalCommand) + "...")
        command = originalCommand + b'\n'
        commandSent = False

        retriesNum = 0

        self.openSerialPort()

        if self.serialPort is None:
            print("Failed to open serial port, returning...")
            return False

        while (not commandSent):
            try:
                self.serialPort.write(command)
                print("Send Successful!")
                commandSent = True
            except Exception as e:
                print(str(e))
                if retriesNum == 1:
                    print("Failed to write on retrying, returning...")
                    break

                try:
                    self.serialPort = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
                    retriesNum += 1
                except Exception as e:
                    print(str(e))
                    self.serialPort = None
                    print("Failed to open serial port, returning...")
                    break

        return commandSent

    def checkMachineStop(self):
        readByte = self.serialPort.read(1)
        if readByte == self.EMERGENCY_STOP_RESPONSE or readByte == self.STOP_RESPONSE:
            self.machinePlaying = False
            self.isMainScreen = True
            self.background = self.mainStartBackground

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

        self.loadBackground()

        self.subscreenButtons.append(Button(self.screen, (self.HOME_BUTTON_X, self.HOME_BUTTON_Y),
                                            pygame.image.load('assets/images/home.png').convert_alpha(),
                                            pygame.image.load('assets/images/home-tapped.png').convert_alpha(),
                                            None, None, None, None, self.onHomeClicked))

        self.loadMainButtons()
        self.loadPlayButton()

        for i in range(len(self.config.getLanguages())):
            language = self.config.getLanguages()[i]

            prefix = language['prefix']
            languageButtonImage = pygame.image.load('assets/images/' + prefix + '.png').convert_alpha()
            languageButtonTappedImage = pygame.image.load('assets/images/' + prefix + '-tapped.png').convert_alpha()

            #TODO: Constants
            languageButton = LanguageButton(self.screen, (i * 160 + 1520, 1040),
                                            languageButtonImage, languageButtonTappedImage, languageButtonTappedImage,
                                            None, None, None, None, None, partial(self.languageClicked, i))
            if language['prefix'] == self.config.languagePrefix:
                languageButton.visible = False

            self.languageButtons.append(languageButton)

        Log.getLogger().info('INIT')

        self.loop()

    def onPlayClicked(self):
        self.sendToSerialPort(self.START_COMMAND)
        response = b''
        while response == b'':
            response = self.serialPort.read(1) # Read response
            time.sleep(self.WAIT_FOR_START_INTERVAL)
        if response == self.START_COMMAND:
            self.machinePlaying = True
            self.background = self.mainBackground

    def onHomeClicked(self):
        self.background = self.mainBackground if self.machinePlaying else self.mainStartBackground
        self.isMainScreen = True

    def onButtonClicked(self, button):
        self.screenImage = button['screenImage']
        self.background = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + self.screenImage)
        self.isMainScreen = False

    #TODO: Reuse in init
    def loadBackground(self):
        if self.isMainScreen:
            self.mainBackground = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/main.png').convert_alpha()
            self.mainStartBackground = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/main-start.png').convert_alpha()
            self.background = self.mainBackground if self.machinePlaying else self.mainStartBackground
            self.loadMainButtons()
            self.loadPlayButton()
        else:
            self.background = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + self.screenImage)

    def loadMainButtons(self):
        self.mainButtons = []
        for button in self.config.getSubscreenButtons():
            buttonImage = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['image']).convert_alpha()
            buttonTappedImage = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + button['tappedImage']).convert_alpha()
            buttonInstance = Button(self.screen, (button['x'], button['y']),
                                    buttonImage, buttonTappedImage, None, None, None, None, partial(self.onButtonClicked, button))
            self.mainButtons.append(buttonInstance)

    def loadPlayButton(self):
        playButtonImage = pygame.image.load('assets/images/play.png').convert_alpha()
        playButtonTappedImage = pygame.image.load('assets/images/play-tapped.png').convert_alpha()

        self.playButton = Button(self.screen, (self.PLAY_BUTTON_X, self.PLAY_BUTTON_Y), playButtonImage, playButtonTappedImage,
            None, None, None, None, self.onPlayClicked)

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
            return self.languageButtons + (self.mainButtons if self.machinePlaying else [self.playButton])

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
            lastMachineCheckTime = time.time()
            isGameRunning = True
            clock = pygame.time.Clock()
            lastTime = pygame.time.get_ticks()
            font = pygame.font.Font(None, 30)
            self.openSerialPort()

            while isGameRunning:
                if time.time() - lastMachineCheckTime > self.MACHINE_CHECK_INTERVAL:
                    self.checkMachineStop()
                    lastMachineCheckTime = time.time()

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
