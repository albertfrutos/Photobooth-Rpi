from tabnanny import check
import requests
import queue
import sys

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
from time import sleep
import socket
import logging

class StatusDisplay:
    
    def __init__(self, uploadQueue = "", updateInterval = 5):
        self.uploadQueue = uploadQueue
        self.updateInterval = updateInterval
        self.isInternetOnline = self.checkInternetConnection()
        self.ipAddress = self.getInterfaceIP()
        #serial = i2c(port=1, address=0x3C)
        #self.device = ssd1306(serial, width=128, height=64, rotate=0)
        
        

        
    
    def Start(self, run_event):
        try:
            serial = i2c(port=1, address=0x3C)
            device = ssd1306(serial, width=128, height=64, rotate=0)
            device.clear()
            
            while run_event.is_set():
                with canvas(device) as draw:            
                    self.ipAddress = self.getInterfaceIP()
                    self.isInternetOnline = self.checkInternetConnection()
                    internetStatus = "Online" if self.isInternetOnline else "Offline"
                    device.clear()
                    draw.text((10, 10), self.ipAddress, fill="white")
                    draw.text((10, 20), "UpQueue: " + str(self.getQueueSize(self.uploadQueue)), fill = "white")
                    draw.text((10,30), "Netw. stat.: " + internetStatus, fill = "white")
                sleep(self.updateInterval)
        except:
            e = sys.exc_info()[0]
            logging.error(e)
                  
    def checkInternetConnection(self):
        url = "http://google.es"
        timeout = 5
        try:
            request = requests.get(url, timeout=timeout)
            logging.info("Connected to the Internet. Uploads unblocked.")
            return True
        except (requests.ConnectionError, requests.Timeout) as exception:
            logging.info("No internet connection. Uploads blocked")
            return False
            
    def getInterfaceIP(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_addr = s.getsockname()[0]
        logging.info("IP Address is: " + ip_addr)
        return ip_addr
    
    def getQueueSize(self, queue):
        size = queue.qsize()
        logging.info("Upload Queue is: " + str(size))
        return size

#_queue = queue.Queue(maxsize=0)
#print("lalalalalala")
#a = StatusDisplay(_queue, 5)
#print("lalalalalala333")
#a.Start()
