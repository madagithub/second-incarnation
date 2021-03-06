from functools import partial
import time

import serial
import math

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
    LOG_FILE_PATH = 'second-incarnation.log'

    HOME_BUTTON_X = 50
    HOME_BUTTON_Y = 1038

    PLAY_BUTTON_X = 959
    PLAY_BUTTON_Y = 300

    EMERGENCY_STOP_RESPONSE = b'2'
    STOP_RESPONSE = b'0'

    START_COMMAND = b'1'

    MACHINE_CHECK_INTERVAL = 0.04
    WAIT_FOR_START_INTERVAL = 0.1
    MACHINE_START_TIMEOUT = 0.1

    BACK_TO_HOME_TIMEOUT = 300

    MACHINE_RUN_TIME = 15 * 60
    MACHINE_COOLING_TIME = 3 * 60

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
        self.machineCooling = False
        self.machineStarting = False
        self.machineStartTime = None
        self.lastInteractionTime = None

    def openSerialPort(self):
        if self.serialPort is None:
            try:
                self.serialPort = serial.Serial(self.MACHINE_PORT_NAME, 115200, timeout=0)
            except Exception as e:
                Log.getLogger().exception('ERROR,Failed to open serial port')
                self.serialPort = None

    # Try to send to serial, and if an error occurs, open serial port again for X retries
    def sendToSerialPort(self, command):
        commandSent = False

        retriesNum = 0

        if self.serialPort is None:
            self.openSerialPort()

            if self.serialPort is None:
                Log.getLogger().exception('ERROR,Failed to open serial port')
                return False

        while (not commandSent):
            try:
                self.serialPort.write(command)
                commandSent = True
            except Exception as e:
                Log.getLogger().exception('ERROR,Failed to write to serial port')
                if retriesNum == 1:
                    break

                try:
                    self.serialPort = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
                    retriesNum += 1
                except Exception as e:
                    Log.getLogger().exception('ERROR,Failed to open serial port')
                    self.serialPort = None
                    break

        return commandSent

    def checkMachineState(self):
        if self.serialPort is not None:
            if self.machineCooling and time.time() - self.machineEndTime >= self.MACHINE_COOLING_TIME:
                self.machineCooling = False
                self.background = self.mainStartBackground
                self.machineEndTime = None

            if self.machinePlaying and self.machineStartTime is not None and time.time() - self.machineStartTime >= self.MACHINE_RUN_TIME:
                self.machinePlaying = False
                self.machineStarting = False
                self.machineCooling = True
                self.machineEndTime = time.time()
                self.isMainScreen = True
                self.background = self.clockBackground
                self.machineStartTime = None
                self.loadBackground()

            try:
                readByte = self.serialPort.read(1)
            except Exception as e:
                Log.getLogger().exception('ERROR,Failed to read from serial port')
                self.SerialPort = None
                self.openSerialPort()
                return

            if self.machineStarting and readByte == self.START_COMMAND:
                self.machinePlaying = True
                self.machineStarting = False
                self.background = self.mainBackground
            elif readByte == self.EMERGENCY_STOP_RESPONSE or readByte == self.STOP_RESPONSE:
                self.machinePlaying = False
                self.machineStarting = False
                self.isMainScreen = True
                self.background = self.clockBackground
                self.machineCooling = True
                self.machineEndTime = time.time()
                self.loadBackground()

            if self.machineStarting and time.time() - self.machineStartTime > self.MACHINE_START_TIMEOUT:
                self.machineStarting = False
        else:
            self.machinePlaying = False

    def start(self):
        self.config = Config(self.CONFIG_FILENAME)

        self.openSerialPort()
        time.sleep(3)

        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.mouse.set_visible(False)

        self.clockFont = pygame.font.Font('assets/fonts/RobotoMono-Medium.ttf', 300)

        self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN | pygame.SCALED)
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

    def checkInactive(self):
        if self.lastInteractionTime is not None and time.time() - self.lastInteractionTime > self.BACK_TO_HOME_TIMEOUT:
            Log.getLogger().info('RESET')
            self.lastInteractionTime = time.time()
            self.moveToHome()

    def onPlayClicked(self):
        self.lastInteractionTime = time.time()
        Log.getLogger().info('PLAY')
        if self.serialPort is not None:
            self.sendToSerialPort(self.START_COMMAND)
            self.machineStarting = True
            self.machineStartTime = time.time()
        else:
            self.openSerialPort()

    def onHomeClicked(self):
        self.lastInteractionTime = time.time()
        Log.getLogger().info('HOME')
        self.moveToHome()

    def moveToHome(self):
        self.background = self.mainBackground if self.machinePlaying else self.mainStartBackground
        self.isMainScreen = True

    def onButtonClicked(self, button):
        self.lastInteractionTime = time.time()
        screenName = button['name']
        Log.getLogger().info(f'SUBSCREEN,{screenName}')
        self.screenImage = button['screenImage']
        self.background = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/' + self.screenImage)
        self.isMainScreen = False

    def loadBackground(self):
        if self.isMainScreen:
            self.mainBackground = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/main.png').convert_alpha()
            self.mainStartBackground = pygame.image.load('assets/images/' + self.config.getLanguagePrefix() + '/main-start.png').convert_alpha()
            self.clockBackground = pygame.image.load('assets/images/clock.png').convert_alpha()
            self.background = self.clockBackground if self.machineCooling else (self.mainBackground if self.machinePlaying else self.mainStartBackground)

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
        self.lastInteractionTime = time.time()
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
        if self.machineCooling:
            return []

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

        self.drawCoolingTimer()

    def drawCoolingTimer(self):
        if self.machineCooling:
            totalSecondsPassed = time.time() - self.machineEndTime
            totalSecondsLeft = self.MACHINE_COOLING_TIME - totalSecondsPassed
            if totalSecondsLeft < 0:
                totalSecondsLeft = 0

            minutesLeft = math.floor(totalSecondsLeft / 60)
            secondsLeft = math.floor(totalSecondsLeft % 60)

            text = self.clockFont.render(f'{minutesLeft:02}:{secondsLeft:02}', True, (255, 255, 255)) 
            textRect = text.get_rect()  
            textRect.center = (1920 // 2, 1080 // 2)
            self.screen.blit(text, textRect)

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

            while isGameRunning:
                self.checkInactive()

                if time.time() - lastMachineCheckTime > self.MACHINE_CHECK_INTERVAL:
                    self.checkMachineState()
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
