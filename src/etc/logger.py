import logging
import os


class transLogger:
    def __init__(self, file):
        self.logDir = os.path.join('/mnt', 'Jonas', 'Notifier')
        self.errorDir = os.path.join(self.logDir, 'Error')
        self.infoDir = os.path.join(self.logDir, 'Info')
        self.logFile = file

        if not os.path.exists(self.logDir):
            os.mkdir(self.logDir)

        if not os.path.exists(self.errorDir):
            os.mkdir(self.errorDir)

        if not os.path.exists(self.infoDir):
            os.mkdir(self.infoDir)

    def info(self, logInfo):
        logInfo = logInfo
        logging.basicConfig(filename=os.path.join(self.infoDir, self.logFile), level=logging.INFO, format='')
        logging.info(logInfo)

    def error(self, logInfo):
        logInfo = logInfo
        logging.basicConfig(filename=os.path.join(self.errorDir, self.logFile),
                            level=logging.ERROR, format='%(levelname)s')
        logging.error(logInfo)
