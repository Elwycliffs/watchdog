
"""
Module: Transaction Handler
Version: 1.0
Author: Wycliff, CODE ROOT SYSTEMS

Description
------------
This module is responsible for monitoring debit transactions from Jonas and pushing notifications
to users by implementing Africa's Talking Bulk SMS api.

Dependencies
------------
* chtdecoder.jar       -> Decodes *.CHT files to unicode
* dbEngine.py          -> Connects and extracts prerequisites from the user database
* africasTalking.py    -> Connects to AfricasTalking BulkSMS api to route SMS'
"""

import os
import sys
import time
import datetime
import subprocess
from globalObjects import Globs
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
from deps.africasTalking import instantMessage


# adding root path
root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root)


# Module: Watchdog -> monitoring on_created events for *.CHT files
class Watchdog(FileSystemEventHandler, object):

    def on_created(self, event):
        source = ''
        if not event.is_directory:
            source = event.src_path

        if str(source).endswith('.CSV'):
            path = source
            print('Found %s' % path)
            furnisher = os.path.join(root, 'furnisher.py')
            subprocess.Popen(['python3 %s %s' % (furnisher, path)], shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # --------------------


if __name__ == "__main__":
    WATCHDOG = PollingObserver()
    EVENTHANDLER = Watchdog()
    GLOBALVARS = Globs()
    configuration = GLOBALVARS.fetchConfig()
    target = configuration['TransactionHandler']['TARGETPATH']
    WATCHDOG.schedule(EVENTHANDLER, path=target, recursive=True)

    try:
        print(
            '''Module: Transaction Handler\nVersion: 1.0 alpha\nAuthor: CODE ROOT SYSTEMS''')
        print('--------------------------')
        WATCHDOG.start()
        print('[OK] Transaction Handler Initialized        ' +
              str(datetime.datetime.now().strftime("%H:%M:%S [%Y-%m-%d]")))
        print('--------------------------------------------------------------')

        while True:
            time.sleep(1)

            # --------------------

    except SystemError:
        alert = "SystemError\n" \
            "Unit: 'Transaction Module' !!FAILED"
        messenger = instantMessage('+254702462698', alert)
        messenger.transmit()

        sys.exit("SystemError\n"
                 "Unit: 'Transaction Module' !!FAILED")

        # --------------------

    except RuntimeError:
        alert = "RuntimeError\n" \
                "Unit: 'Transaction Module' !!FAILED"
        messenger = instantMessage('+254702462698', alert)
        messenger.transmit()

        sys.exit("RuntimeError\n"
                 "Unit: 'Transaction Module' !!FAILED")

        # --------------------

    except KeyboardInterrupt:
        sys.exit('Sys Exit Invoked')

        # --------------------
