import logging
from logging.handlers import RotatingFileHandler


class Log:

    logger = None

    @staticmethod
    def init(logFilePath):
        logging.basicConfig(filename=logFilePath, filemode='a', level=logging.INFO)

        handler = RotatingFileHandler(logFilePath, maxBytes=37500, backupCount=100)
        Log.logger = logging.getLogger('Rotating Log')
        formatter = logging.Formatter('%(asctime)s.%(msecs)03d,%(message)s', '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        Log.logger.propagate = False
        Log.logger.addHandler(handler)
        print('done')

    @staticmethod
    def getLogger():
        return Log.logger
