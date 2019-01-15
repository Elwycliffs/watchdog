import os
import sys
import re
import datetime
import subprocess
import time

# adding root path
root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root)

from deps.dbEngine import dbConnection
from etc.logger import transLogger
from deps.africasTalking import instantMessage


# Module: Worker -> decodes, furnishes and transmits Messages
class Worker:
    def __init__(self, path):
        self.transaction = path
        self.logFile = str(os.path.basename(path)[:-4])+'.log'
        self.logger = transLogger(self.logFile)

    def decode(self, file):
        try:
            # path to java *.CHT file decoder
            resource = os.path.join(root, 'deps', 'chtdecoder-2.1-java1.4', 'chtdecoder.jar')
            process = subprocess.run(['java -jar %s %s' % (resource, file)],
                                     shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = process.stdout.decode('utf-8')
            rawfurnished = str(output).split('\n')
            minified = []

            # Extracting necessary data to include in SMS (User ID and Debit amount)
            for blob in rawfurnished:
                if not str(blob).startswith('0000'):
                    brace = blob.find('(')
                    data = blob[brace + 1:-1]
                    data = data.split(' ')
                    data = list(filter(None, data))

                    if len(data) > 0:
                        minified.append(data)
            return minified

        except Exception as e:
            refNo = os.path.basename(file)[:-4]
            self.logger.error('-----------------------------------------------')
            self.logger.error('[FAILED] Decoding %s Failed at %s' %
                              (refNo, str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]"))))
            self.logger.error('-----------------------------------------------')
            self.logger.error(str(e))

        # --------------------

    def miner(self, data):  # Fetches values data variables from the specific areas.
        try:
            userID = None
            values = {}
            data = data

            # Fetching Member ID, Member Name, and the Receipt Ref Number.
            if len(data[1]) > 2:
                userID = data[1][1]  # User's Member Number.
                values.update(dict(user=userID))

            self.logger.info('User: %s' % userID)
            # Fetching Members Phone Number from database
            if userID is not None:
                database = dbConnection("SELECT FirstName, Mobile FROM tblPvxMembers "
                                        "WHERE MemberCode='" + userID + "';")  # sql statement
                data = database.data()

                for item in data:
                    userName = item[0]
                    phnNo = item[1]
                    userName = str(userName).split(' ')

                    if len(userName) > 2:
                        firstName = str.title(userName[0])
                        secondName = str.title(userName[1])
                        surName = str.title(userName[2])
                        userName = firstName + ' ' + secondName + ' ' + surName
                    elif len(userName) == 2:
                        firstName = str.title(userName[0])
                        secondName = str.title(userName[1])
                        userName = firstName + ' ' + secondName
                    elif len(userName) == 1:
                        firstName = str.title(userName[0])
                        userName = firstName
                    else:
                        firstName = 'John Doe'
                        userName = firstName

                    phnNo = str(phnNo).strip(' ')  # stripping whitespaces at the beginning and the end of the value
                    phnNo = phnNo.replace(' ', '')  # replacing inner whitespaces with a no space
                    phnNo = re.sub("[^0-9]", "", phnNo)  # eliminating non-numeric chars in the value
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
                            self.logger.info('-----------------------------------------------')
                            self.logger.info('[PASS] Member %s should register their Mobile Numbers' % userID)
                            self.logger.info('-----------------------------------------------')
                    else:
                        mobile = 'N/A'
                        self.logger.info('-----------------------------------------------')
                        self.logger.info('[PASS] Member %s should register their Mobile Numbers' % userID)
                        self.logger.info('-----------------------------------------------')

                    values.update(name=userName, mobile=mobile)

            return values
        except Exception as e:
            self.logger.error('-----------------------------------------------')
            self.logger.error('[FAILED] Mining Failed at %s' %
                              (str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]"))))
            self.logger.error('-----------------------------------------------')
            self.logger.error(str(e))

    def furnish(self, data, refNo):
        try:
            data = data
            refNo = refNo

            # Validation to filter out guest transactions
            if data[1][1] == 'GUEST':
                destination = None
                message = None
                self.logger.info('-----------------------------------------------')
                self.logger.info('[PASS] Currently not tracking Guests')
                self.logger.info('-----------------------------------------------')

                transmission = {}
                transmission.update(destination=destination, message=message)

                return transmission

            else:
                resources = self.miner(data)
                __type = None
                destination = None
                message = None

                if resources['mobile'] != 'N/A':

                    # Validation to filter Subs & Topup Credit Transactions
                    for objects in data:
                        for obj in objects:
                            if str(obj) == 'ZCLBCD':
                                __type = 'Topup'
                                self.logger.info('Type: %s' % __type)
                                amount = data[data.index(objects)][1]
                                resources.update(dict(ref=refNo, amount=amount[:-3]))

                                if int(resources['amount']) > 0:
                                    destination = resources['mobile']
                                    message = 'Hello %s, Kshs %s.00 has been received on your account %s, ' \
                                              'ref receipt number %s. Any Query? Contact +254704100191.' \
                                              % (resources['name'], resources['amount'], resources['user'],
                                                 resources['ref'])
                                else:
                                    destination = None
                                    message = None
                                    self.logger.info('-----------------------------------------------')
                                    self.logger.info('[SKIPPING] Skipping transmission for Zero valued transaction')
                                    self.logger.info('-----------------------------------------------')

                                break

                            elif str(obj) == 'ONACCT':
                                __type = 'Subs'
                                self.logger.info('Type: %s' % __type)
                                amount = data[data.index(objects)][1]
                                resources.update(dict(ref=refNo, amount=amount[:-3]))

                                if int(resources['amount']) > 0:
                                    destination = resources['mobile']
                                    message = 'Hello %s, Kshs %s.00 in Subs has been received on your account %s, ' \
                                              'ref receipt number %s. Any Query? Contact +254704100191.' \
                                              % (resources['name'], resources['amount'], resources['user'],
                                                 resources['ref'])
                                else:
                                    destination = None
                                    message = None
                                    self.logger.info('-----------------------------------------------')
                                    self.logger.info('[SKIPPING] Skipping transmission for Zero valued transaction')
                                    self.logger.info('-----------------------------------------------')

                                break

                        if __type is not None:
                            transmission = dict(destination=destination, message=message)
                            return transmission

                    # Identification of Debit transactions
                    if __type is None:
                        self.logger.info('Type: Debit')
                        resources.update(dict(ref=refNo))

                        # Fetching debited amount
                        values = []
                        for item in data:
                            for subitem in item:
                                if str(subitem).find('.00') != -1:
                                    subitem = subitem[:str(subitem).find('.')]
                                    subitem = str(subitem).strip('-')

                                    if subitem is not '':
                                        subitem = int(subitem)
                                        values.append(subitem)

                        if len(values) > 0:
                            debit = max(values)  # Greatest value within the list is the TOTAL
                        else:
                            debit = 0

                        resources.update(dict(amount=debit))

                        # Formatting message
                        if int(resources['amount']) > 0:
                            destination = resources['mobile']
                            message = 'Hello %s, Kshs %s.00 has been charged on your account %s, ' \
                                      'ref receipt number %s. Any Query? Contact +254704100191.' \
                                      % (resources['name'], resources['amount'], resources['user'],
                                         resources['ref'])
                        else:
                            destination = None
                            message = None
                            self.logger.info('-----------------------------------------------')
                            self.logger.info('[SKIPPING] Skipping transmission for Zero valued transaction')
                            self.logger.info('-----------------------------------------------')

                        transmission = dict(destination=destination, message=message)

                        return transmission
                else:
                    transmission = dict(destination=destination, message=message)
                    return transmission

        except Exception as e:
            refNo = refNo
            self.logger.error('-----------------------------------------------')
            self.logger.error('[FAILED] Furnishing %s Failed at %s' %
                              (refNo, str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]"))))
            self.logger.error('-----------------------------------------------')
            self.logger.error(str(e))

        # --------------------

    def transmit(self, transmission):
        try:
            smsHandler = instantMessage(transmission['destination'], transmission['message'])
            results = smsHandler.transmit()
            status = None

            for result in results:
                status = result['status']

            self.logger.info('Destination: %s' % transmission['destination'])
            self.logger.info('Status: %s' % status)
            self.logger.info('Time: %s ' %
                             str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]")))
            self.logger.info('\n%s\n' % transmission['message'])

        except Exception as e:
            self.logger.error('-----------------------------------------------')
            self.logger.error('[FAILED] Transmission Failed         ' +
                              str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]")))
            self.logger.error('-----------------------------------------------')
            self.logger.error(str(e))

        # --------------------

    def process(self):
        try:
            refNo = os.path.basename(self.transaction)[:-4]

            # Fetch source directory for 'path' here to identify POS Data.
            source = os.path.basename(os.path.dirname(self.transaction))

            if source.startswith('POSDATA'):
                if source.endswith('FB'):
                    time.sleep(180)
                    sys.exit(0)
                elif source.endswith('HF'):
                    data = self.decode(self.transaction)
                    delay = None

                    for item in data:
                        for obj in item:
                            if str(obj) == 'ZCLBCD':
                                delay = 0
                                break
                            elif str(obj) == 'ONACCT':
                                delay = 0
                                break

                        if delay == 0:
                            break

                    if delay is None:
                        time.sleep(180)

                decoded = self.decode(self.transaction)
                self.logger.info(decoded)
                self.logger.info('****************************************************'
                                 '*******************************************')
                self.logger.info('\nTransaction: %s' % refNo)
                transmission = self.furnish(decoded, refNo)

                if transmission['destination'] is not None:
                    if transmission['destination'] != 'N/A':
                        self.transmit(transmission)

        except Exception as e:
            refNo = os.path.basename(self.transaction)[:-4]
            self.logger.error('-----------------------------------------------')
            self.logger.error('[FAILED] Processing %s Failed at %s' %
                              (refNo, str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]"))))
            self.logger.error('-----------------------------------------------')
            self.logger.error(str(e))

        # --------------------


if __name__ == '__main__':
    worker = Worker(sys.argv[1])
    worker.process()

