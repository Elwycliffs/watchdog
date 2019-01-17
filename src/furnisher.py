from deps.africasTalking import instantMessage
from etc.logger import transLogger
from deps.dbEngine import dbConnection
import os
import sys
import re
import datetime
import subprocess
import time
import csv

# adding root path
root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root)


# Module: Worker -> decodes, furnishes and transmits Messages
class Worker:
    def __init__(self, path):
        self.transaction = path
        self.logFile = str(os.path.basename(path)[:-4])+'.log'
        self.logger = transLogger(self.logFile)

    def miner(self, userID):  # Mines user data from core database
        try:
            # Fetching Member ID, Member Name, and the Receipt Ref Number.
            values = {}
            self.logger.info('User: %s' % userID)

            # Fetching Members Phone Number from database
            if userID:
                database = dbConnection("SELECT FirstName, Mobile FROM tblPvxMembers "
                                        "WHERE MemberCode='" + userID + "';")  # sql statement
                data = database.data()

                for item in data:
                    phnNo = item[1]

                    # stripping whitespaces at the beginning and the end of the value
                    phnNo = str(phnNo).strip(' ')
                    # replacing inner whitespaces with a no space
                    phnNo = phnNo.replace(' ', '')
                    # eliminating non-numeric chars in the value
                    phnNo = re.sub("[^0-9]", "", phnNo)
                    phnNo = str(phnNo)  # converting to string

                    if len(phnNo) > 0:
                        if phnNo.startswith('+'):
                            mobile = phnNo
                        elif phnNo.startswith('254'):
                            mobile = '+' + phnNo
                        elif phnNo.startswith('07'):
                            mobile = '+254' + phnNo[1:]
                        elif phnNo.startswith('7'):
                            mobile = '+254' + phnNo
                        else:
                            mobile = 'N/A'
                            self.logger.info(
                                '-----------------------------------------------')
                            self.logger.info(
                                '[PASS] Member %s should register their Mobile Numbers' % userID)
                            self.logger.info(
                                '-----------------------------------------------')
                    else:
                        mobile = 'N/A'
                        self.logger.info(
                            '-----------------------------------------------')
                        self.logger.info(
                            '[PASS] Member %s should register their Mobile Numbers' % userID)
                        self.logger.info(
                            '-----------------------------------------------')

                    values.update(mobile=mobile)

            return values
        except Exception as e:
            self.logger.error(
                '-----------------------------------------------')
            self.logger.error('[FAILED] Mining Failed at %s' %
                              (str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]"))))
            self.logger.error(
                '-----------------------------------------------')
            self.logger.error(str(e))

    def transpile(self, file):
        # Read CSV file line by line
        # 1. Fetch Member Number and read from database
        # 2. Prepare Message based on transaction information
        # 3. Transmit message

        rows = []

        with open(file, 'r') as fileStream:
            stream = csv.reader(fileStream, delimiter=',')
            for row in stream:
                rows.append(row)

        if(len(rows) > 0):
            source = rows[0]

            if(len(source) == 8):
                data = dict(ttype="topup", name=source[0], userID=source[2], reference=source[3],
                            total=source[5], openingBal=source[-2], closingBal=source[-1])
            elif(len(source) == 12):
                data = dict(ttype="debit", name=source[0], userID=source[2], reference=source[3], total=source[
                            8], openingBal=source[-2], closingBal=source[-1])

        return data

        # -------------------

    def transmit(self, transmission):
        try:
            smsHandler = instantMessage(
                transmission['destination'], transmission['message'])
            smsHandler.transmit()

        except Exception as e:
            self.logger.error(
                '-----------------------------------------------')
            self.logger.error('[FAILED] Transmission Failed         ' +
                              str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]")))
            self.logger.error(
                '-----------------------------------------------')
            self.logger.error(str(e))

        # --------------------

    def process(self):
        try:
            refNo = os.path.basename(self.transaction)[:-4]

            # Fetch source directory for 'path' here to identify POS Data.
            # source = os.path.basename(os.path.dirname(self.transaction))
            print("Calling Transpile")
            data = self.transpile(self.transaction)

            # Fetch Member information
            info = self.miner(data["userID"])

            print("Sending Message")
            if(info["mobile"] != "N/A"):
                data.update(mobile=info["mobile"])
                self.logger.info(
                    "-------------------------------------------------------------")
                self.logger.info('''Transaction Type: %s\nReference: %s\nMember Number: %s\nMember Name: %s\nPhone Number: %s\nTotal: %s''' % (
                    data["ttype"], data["reference"], data["userID"], data["name"], data["mobile"], data["total"]))

                # Transmit here
                if(data["ttype"] == "topup"):
                    print("Found Topup")
                    message = '''Hello %s, Kshs %s has been received on your account %s, Ref: %s.\nOpening Bal: Kshs %s\nClosing Bal: Kshs %s.\nContact +254704100191.''' % (
                        data['name'], data['total'], data['userID'], data['reference'], data["openingBal"], data["closingBal"])

                elif(data["ttype"] == "debit"):
                    print("Found Debit")
                    message = '''Hello %s, Kshs %s has been charged on your account %s, Ref: %s.\nOpening Bal: Kshs %s\nClosing Bal: Kshs %s.\nContact +254704100191.''' % (data['name'], data['total'], data['userID'],
                                                                                                                                                                            data['reference'], data["openingBal"], data["closingBal"])

                transmission = dict(
                    destination=data["mobile"], message=message)
                self.logger.info(
                    "-------------------------------------------------------------")
                self.transmit(transmission)
                self.logger.info("Destination: %s\nMessage: %s" %
                                 (data["mobile"], message))
                self.logger.info(
                    "-------------------------------------------------------------")

        except Exception as e:
            refNo = os.path.basename(self.transaction)[:-4]
            self.logger.error(
                '-----------------------------------------------')
            self.logger.error('[FAILED] Processing %s Failed at %s' %
                              (refNo, str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]"))))
            self.logger.error(
                '-----------------------------------------------')
            self.logger.error(str(e))

        # --------------------


if __name__ == '__main__':
    worker = Worker(sys.argv[1])
    worker.process()
