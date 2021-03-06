import sys
import os
import africastalking as ATG

# adding root path
root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, root)
from globalObjects import Globs


class instantMessage:
    # Values of the following variables will be captured from an external class
    def __init__(self, destination, message):
        # Message details
        self.destination = destination
        self.message = message
        self.sender = 'ParklandSC'

    try:
        def transmit(self):
            GLOBALVARS = Globs()
            config = GLOBALVARS.fetchConfig()
            APINAME = config['AfricasTalking']['USERNAME']
            APIKEY = config['AfricasTalking']['API_KEY']
            ATG.initialize(APINAME, APIKEY)
            ENGINE = ATG.SMS
            response = ENGINE.send(
                self.message, [self.destination], self.sender)
            return response

    except:
        print('Encountered an error while sending')


if __name__ == '__main__':
    handler = instantMessage(
        '+254702462698', 'Unit Test Complete: Component alive.')
    handler.transmit()
