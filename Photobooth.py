import random

import json
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from threading import *
import tkinter as tk
from random import randint
import numpy as np
import shutil

import skimage.io
from skimage.transform import rescale

import libcamera

from PyQt5 import QtGui
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QLabel, QWidget, QStackedWidget)

from picamera2 import Picamera2
from picamera2.previews.qt import QGlPicamera2,QPicamera2


from PIL import Image

from gpiozero import Button, LED

from Uploader import Uploader
from StatusDisplay import StatusDisplay


class Photobooth():
    rawConfig = None

    fullScreen = False
    uploadIntervalCheckConnection = 10
    cameraResolutionWidth = 2592
    cameraResolutionHeight = 1944
    cameraEnableFrameOverlayInPreview = False
    shutterButtonPin = 14
    buttonLEDPin = 20
    flashLightPin = 21
    countdownStepLength = 1
    gDriveEndPointFullResolution = None
    gDriveEndPointThumbnail = None
    uploadJSONEndPoint = None
    uploadJSONApikey = None
    uploadMode = ""
    picturesDirectoryFullResolution = "photos_full"
    picturesDirectoryThumbnail = "photos_thumb"
    picturesOverlayedDirectory = "photos_overlayed"
    picturesBaseFilename = "picture"
    picturesSaveOverlayed = False
    picturesUploadEnabled = False
    resourcesDirectory = "resources"
    framePictureOverlay = "frame.jpg"
    countDownPicturesArray = []
    isFunnyModeEnabled = False
    funnyModeProbabilityPercent = 50
    funnyPicturesArray = []

    frame_overlay = None
    event_execution_ongoing = False

    funOverlay = None

    run_event = threading.Event()
    run_event.set()
    
    uploadsQueue = queue.Queue(maxsize=0)


    if not os.path.exists('debug.log'):
        open('debug.log', "x").close()

    logging.basicConfig(
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.DEBUG, format='%(asctime)s - [%(levelname)s] (%(threadName)-9s) %(message)s', )

    def __init__(self):

        self.LoadConfiguration()

        self.camera = Picamera2()
        self.app = QApplication([])

        imgW = self.camera.sensor_resolution[0]
        imgH = self.camera.sensor_resolution[1]

        if self.rawConfig["camera"]["cameraResolutionWidth"] != "" and self.rawConfig["camera"]["cameraResolutionHeight"] != "":
            imgH = self.rawConfig["camera"]["cameraResolutionHeight"]
            imgW = self.rawConfig["camera"]["cameraResolutionWidth"]

        pic_config = self.camera.create_still_configuration(main={"size": (imgW, imgH)}, lores={"size": (1280, 720)}, transform=libcamera.Transform(vflip=1), display="lores")
        self.camera.configure(pic_config)

        self.window = QWidget()
        self.qpicamera2 = QPicamera2(self.camera, width=1280, height=720, keep_ar=True)

        layout_h = QHBoxLayout()
        self.layout_s = QStackedWidget()

        self.layout_s.addWidget(self.qpicamera2)

        self.pic = QLabel()
        self.pic.setAlignment(Qt.AlignCenter)

        self.pic.show()

        self.layout_s.addWidget(self.pic)

        layout_h.addWidget(self.layout_s)
        self.window.setLayout(layout_h)
        self.window.setStyleSheet("background-color: black;")
        

        self.FilesUploader = Uploader(self.rawConfig["upload"])
        self.StatusDisplay = StatusDisplay(self.uploadsQueue, self.uploadIntervalCheckConnection)
        
        os.putenv("DISPLAY", ":0.0")
        self.button = Button(self.shutterButtonPin, pull_up=False)
        self.flash = LED(self.flashLightPin)
        self.buttonLED = LED(self.buttonLEDPin)

    def Start(self):
        try:
            logging.info("Starting...")
            self.camera.start()
            self.camera.set_controls({"AfMode": libcamera.controls.AfModeEnum.Auto})
            self.camera.set_controls({"FrameRate": 10})

            self.StartListeningButtonPush()
            logging.info("Start finished")

            #threadStatusDisplay = Thread(name="StatusDisplayThread", target=self.StartStatusDisplay, args=(
            #    self.run_event,))
            #threadStatusDisplay.start()

            threadUploader = Thread(name="UploaderThread", target=self.ProcessFilesToUploadQueue, args=(
                self.uploadsQueue, self.run_event,))
            threadUploader.start()
            self.buttonLED.on()

            if (self.fullScreen):
                self.window.showFullScreen()
            self.window.show()

            self.app.exec()

        except:
            e = sys.exc_info()[0]
            logging.error(e)

    

    def LoadConfiguration(self):

        with open('json/config.json', 'r') as configFile:
            config = json.load(configFile)
            self.rawConfig = config

            self.fullScreen = config["fullScreen"]
            self.cameraResolutionWidth = config["camera"]["cameraResolutionWidth"]
            self.cameraResolutionHeight = config["camera"]["cameraResolutionHeight"]
            self.shutterButtonPin = config["pins"]["shutterButtonPin"]
            self.buttonLEDPin = config["pins"]["buttonLEDPin"]
            self.flashLightPin = config["pins"]["flashLightPin"]
            self.countdownStepLength = config["countdown"]["countdownStepLength"]
            self.uploadIntervalCheckConnection = config["uploadIntervalCheckConnection"]
            self.gDriveEndPointFullResolution = config[
                "upload"]["uploadGDrive"]["gDriveEndPointFullResolution"]
            self.gDriveEndPointThumbnail = config[
                "upload"]["uploadGDrive"]["gDriveEndPointThumbnail"]
            self.uploadJSONEndPoint = config["upload"]["uploadGDrive"]["uploadJSONEndPoint"]
            self.uploadJSONApikey = config["upload"]["uploadGDrive"]["uploadJSONApikey"]
            self.uploadMode = config["upload"]["uploadMode"]
            self.picturesDirectoryFullResolution = config[
                "pictures"]["picturesDirectoryFullResolution"]
            self.picturesDirectoryThumbnail = config["pictures"]["picturesDirectoryThumbnail"]
            self.picturesOverlayedDirectory = config["pictures"]["picturesOverlayedDirectory"]
            self.picturesBaseFilename = config["pictures"]["picturesBaseFilename"]
            self.picturesSaveOverlayed = config["pictures"]["picturesSaveOverlayed"]
            self.picturesUploadEnabled = config["pictures"]["picturesUploadEnabled"]
            self.usbPictureCopyPath = config["pictures"]["usbPictureCopyPath"]
            self.isFunnyModeEnabled = config["funnyMode"]["enabled"]
            self.funnyModeProbabilityPercent = config["funnyMode"]["funnyModeProbabilityPercent"]
            self.funnyPicturesArray = config["funnyMode"]["funnyPicturesArray"]
            self.resourcesDirectory = config["resources"]["resourcesDirectory"]
            self.framePictureOverlay = config["resources"]["framePictureOverlay"]
            self.countDownPicturesArray = config["resources"]["countDownPicturesArray"]

    def StartListeningButtonPush(self):
        self.button.when_pressed = self.WhenButtonPushed

    def StopListeningButtonPush(self):
        self.button.when_pressed = self.DoNothing()

    def WhenButtonPushed(self):
    
        if self.event_execution_ongoing:
            logging.info("event ongoing, returning")
            return
        self.event_execution_ongoing = True
        
        self.camera.set_controls({"AfMode": libcamera.controls.AfModeEnum.Continuous})

        logging.info("Button pushed")

        self.StopListeningButtonPush()

        logging.info("loading")
        #overlay = cv2.imread("resources/number_1.png", cv2.IMREAD_UNCHANGED)
        logging.info("loaded")
        #self.qpicamera2.set_overlay(overlay)
        logging.info("loading")
        self.TakePicture()

        if(os.path.exists(self.usbPictureCopyPath)):
            logging.info("copy pictures")
            self.CopyFilesToUSB()
        else:
            logging.info("no copy")

        self.StartListeningButtonPush()
        self.event_execution_ongoing = False

    def ShowCountDown(self):
        self.CameraCountDownOverlay()

    def GetFilename(self):
        filename = self.picturesBaseFilename + "_" + \
                   datetime.now().strftime('%Y%m%d%H%M%S') + '.jpg'
        logging.info("filename is " + filename)
        return filename

    def TakePicture(self):
        try:
            pictureName = self.GetFilename()
            path_full = os.path.join(
                self.picturesDirectoryFullResolution, pictureName)
            path_thumb = os.path.join(
                self.picturesDirectoryThumbnail, pictureName)
            self.buttonLED.blink(0.3, 0.3, None, True)
            self.camera.set_controls({"AfMode": libcamera.controls.AfModeEnum.Continuous})
            self.camera.set_controls({"AfMode": libcamera.controls.AfModeEnum.Auto, "AfSpeed": libcamera.controls.AfSpeedEnum.Fast})
            #job = self.camera.autofocus_cycle(wait=False)
            self.ShowCountDown()
            job = self.camera.autofocus_cycle(wait=False)
            self.GenerateOverlay("camera.png")
            self.camera.wait(job)
            #time.sleep(0.1)
            self.GenerateOverlay("cameraFlash.png")

            
            self.buttonLED.off()
            self.flash.on()
            
            self.camera.capture_file(path_full)
            self.flash.off()
            self.RemoveOverlay()


            image = QtGui.QImage(path_full)
            overlay = QtGui.QImage("resources/roll.png")
            painter = QtGui.QPainter()
            painter.begin(image)
            painter.drawImage(0, 0, overlay)
            painter.end()

            #self.GenerateOverlay("roll.png")
            #self.pic.setPixmap(QtGui.QPixmap(path_full).scaled(1216,684))  #*0.9
            self.pic.setPixmap(QtGui.QPixmap.fromImage(image).scaled(1216,684))  #*0.9  original is 1280,720
            self.layout_s.setCurrentIndex(1)

            time.sleep(6)
            
            self.RemoveOverlay()

            self.layout_s.setCurrentIndex(0)

            

            isThisAFunnyRound = self.IsFunTime()
            if self.isFunnyModeEnabled and isThisAFunnyRound:
                logging.info("Is fun time!")
                chosenFunnyPicture = random.choice(self.funnyPicturesArray)
                logging.info("Adding funny overlay: " + chosenFunnyPicture)
                self.funOverlay = self.GenerateOverlay(chosenFunnyPicture)

            
            logging.info("Image picture captured")
#
            self.GenerateThumbnail(path_full, path_thumb)
#
            if self.picturesUploadEnabled:
                self.EnqueueFilesForUpload(path_full, path_thumb)
#
            if self.funOverlay is not None:
                time.sleep(1)
                logging.info("Removing funny overlay")
                self.RemoveOverlay()
                self.funOverlay = None
            self.buttonLED.on()


            if self.picturesSaveOverlayed:
                self.SaveWithOverlay(path_full, pictureName)



        except:
            e = sys.exc_info()[0]
            logging.error(e)

    def EnqueueFilesForUpload(self, path_full, path_thumb):
        logging.info("Adding paths to uploader's queue")
        filepaths = [path_full, path_thumb]
        self.uploadsQueue.put(filepaths)

    def ProcessFilesToUploadQueue(self, filepaths, run_event):
        logging.info("Started upload processor")
        try:
            while run_event.is_set():
                if not self.uploadsQueue.empty() and not self.StatusDisplay.isInternetOnline:
                    logging.info("No internet available. Will not upload.")
                elif not self.uploadsQueue.empty() and self.StatusDisplay.isInternetOnline:
                    filepaths = self.uploadsQueue.get()
                    logging.info("Processing paths for " +
                                 filepaths[0] + " and " + filepaths[1])
                    self.FilesUploader.UploadFile(filepaths[0], filepaths[1])
        except:
            e = sys.exc_info()[0]
            logging.error(e)

    def StartStatusDisplay(self, run_event):
        try:
            self.StatusDisplay.Start(run_event)
        except:
            e = sys.exc_info()[0]
            logging.error(e)

    def GenerateThumbnail(self, path_full, path_thumb):
        try:
            img = Image.open(path_full)
            thumbnail_size = (250, 250)
            img.thumbnail(thumbnail_size)
            img.save(path_thumb)
        except:
            e = sys.exc_info()[0]
            logging.error(e)

    def SaveWithOverlay(self, path, filename):
        try:
            background = Image.open(path)
            frame = os.path.join(self.resourcesDirectory, self.framePictureOverlay)
            overlayedImage = os.path.join(
                self.picturesDirectoryFullResolution, self.picturesOverlayedDirectory, filename)
            logging.info(overlayedImage)
            imgFrame = Image.open(frame)
            background.paste(imgFrame, (0, 0), imgFrame)
            background.save(overlayedImage)
        except:
            e = sys.exc_info()[0]
            logging.error(e)

    def GenerateOverlay(self, filename, scale = 1):
        try:
            logging.info("generating overlay")
            overlayFile = os.path.join(self.resourcesDirectory, filename)
            logging.info(overlayFile)
            overlay = skimage.io.imread(overlayFile)
            logging.info("read")
            self.qpicamera2.set_overlay(overlay)

        except:
            e = sys.exc_info()[0]
            logging.error(e)

        return overlay

    def RemoveOverlay(self):
        self.GenerateOverlay("noOverlay.png")
        
    def IsFunTime(self):
        funNumber = randint(0, 100)
        logging.info("Funny number is: " + str(funNumber))
        logging.info("Probability is: " + str(self.funnyModeProbabilityPercent))
        return funNumber <= self.funnyModeProbabilityPercent

    def CameraCountDownOverlay(self):
        countDownPictures = self.countDownPicturesArray
        counter = 0

        logging.info(countDownPictures)
        
        for picture in countDownPictures:
            counter = counter + 1            
            countDownOverlay = self.GenerateOverlay(picture, 0.9)
            time.sleep(self.countdownStepLength)
            self.RemoveOverlay()

    def CameraFrameOverlay(self, filename):
        self.frame_overlay = self.GenerateOverlay(filename)

    def DoNothing(self):
        return
    
    def CopyFilesToUSB(self):
         for file in os.listdir(self.picturesDirectoryFullResolution):
            # check if current path is a file
            sourceFilePath = os.path.join(self.picturesDirectoryFullResolution, file)
            targetFilePath = os.path.join(self.usbPictureCopyPath,file)
            if os.path.isfile(sourceFilePath) and not os.path.exists(targetFilePath):
                logging.info("Copying " + sourceFilePath + " to " + targetFilePath)
                shutil.copyfile(sourceFilePath, targetFilePath)
            else:
                logging.info("Skipping " + sourceFilePath)

