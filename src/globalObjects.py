"""
* This file defines global objects borrowed by the different modules within this system.
* It is also used to build the system's default configuration
"""

import os
import getpass
import json
import sys


class Globs:
    # Instance manager
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Globs, cls).__new__(cls)

        return cls.instance

        # --------------------

    # Object constructor
    def __init__(self):
        if sys.platform == 'linux' or sys.platform == 'linux2':
            self.root = os.path.join('/opt', 'Notifier')
        elif sys.platform == 'win32':
            self.root = os.path.join('C:\\Program Files', 'Notifier')

        if not os.path.exists(self.root):
            os.mkdir(self.root)

        self.defaults = dict(
            # Transaction Module defaults
            TransactionHandler=dict(
                MODULE='TransactionHandler',
                REPOPATH=os.path.join(self.root, 'Transactions'),
                TARGETPATH=''
            ),

            # Africas Talking API username and key
            AfricasTalking=dict(
                USERNAME='parklandsc',
                API_KEY='424e31d444d1f02b16cd0a8fa05b590e0b60ebcf9bf98923eb8cb08afb6c41a9'
            )
        )

        # --------------------

    def fetchConfig(self):
        configFile = os.path.join(self.root, 'config.json')

        if not os.path.exists(configFile):
            configuration = self.configure()
        else:
            config = open(configFile, 'r')
            configuration = json.load(config)

        return configuration

        # --------------------

    def configure(self):
        configFile = os.path.join(self.root, 'config.json')

        if not os.path.exists(configFile):
            defaults = self.defaults

            print('Below are the system defaults')
            print('----------------------------------')
            for item in defaults:
                print(item + '\n----------------')
                for subitem in defaults[item]:
                    if defaults[item][subitem] == '':
                        print('-------------------------------------------------')
                        print("configure %s's '%s' value to proceed \n" % (item, subitem))
                        self.defaults[item][subitem] = input(subitem + ': ')

                        if str(subitem).endswith('PATH'):
                            while not os.path.exists(self.defaults[item][subitem]):
                                print('That path is non-existent')
                                self.defaults[item][subitem] = input(subitem + ': ')

                        print('-------------------------------------------------')
                    print(subitem + ': ' + str(defaults[item][subitem]))
                print('\n')

            stream = open(configFile, 'w')
            json.dump(self.defaults, stream)
            return self.defaults

        # --------------------
