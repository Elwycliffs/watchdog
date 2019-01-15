import os
import sys

# adding root path
root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, root)

from globalObjects import Globs
from africastalking import AfricasTalkingGateway as ATG


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
            gateway = ATG.AfricasTalkingGateway(APINAME, APIKEY)
            results = gateway.sendMessage(self.destination, self.message, self.sender)
            return results

    except ATG.AfricasTalkingGatewayException as e:
        print('Encountered an error while sending: %s ' % str(e))


if __name__ == '__main__':
    handler = instantMessage('+254702462698', 'Unit Test Complete: Component alive.')
    handler.transmit()
