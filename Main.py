#!/usr/bin/env python3

import logging
import time
from Photobooth import Photobooth


def main():
    
    try:
        photobooth = Photobooth()
        photobooth.Start()
        while True:
            time.sleep(0.01)
    except KeyboardInterrupt:
        photobooth.run_event.clear()
        logging.info("Keyboard interrupt, will now exit.")
        
if __name__ == "__main__":
    main()

