import json


class Config:

    def __init__(self, filename):
        with open(filename) as file:
            self.config = json.load(file)

        self.languagePrefix = self.config['defaultLanguage']
        self.languageIndex = next(index for index in range(len(self.config['languages'])) if self.config['languages'][index]['prefix'] == self.languagePrefix)

    def isTouch(self):
        return self.config['touch']

    def setTouch(self, value):
        self.config['touch'] = value

    def getTouchDevicePartialName(self):
        return self.config['touchDeviceName']

    def getTouchScreenMaxX(self):
        return self.config['touchMaxX']

    def getTouchScreenMaxY(self):
        return self.config['touchMaxY']

    def showFPS(self):
        return self.config['showFPS']

    def getLanguages(self):
        return self.config['languages']

    def getSubscreenButtons(self):
        return self.config['subscreenButtons']

    def isRtl(self):
        return self.getLanguage()['rtl']

    def changeLanguage(self, index):
        self.languageIndex = index
        self.languagePrefix = self.getLanguages()[self.languageIndex]['prefix']

    def getLanguage(self):
        return self.config['languages'][self.languageIndex]

    def getLanguagePrefix(self):
        return self.languagePrefix

    def getDefaultLanguagePrefix(self):
        return self.config['defaultLanguage']
