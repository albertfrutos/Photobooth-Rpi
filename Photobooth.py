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

from PIL import Image
from grpclib import Status
from gpiozero import Button, LED
from picamera import PiCamera

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
    minimumImageAlphaValue = 0
    maximumImageAlphaValue = 255
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
        open('debug.log', "x").close();

    logging.basicConfig(
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.DEBUG, format='%(asctime)s - [%(levelname)s] (%(threadName)-9s) %(message)s', )

    def __init__(self):

        self.LoadConfiguration()

        self.camera = PiCamera()
        self.camera.resolution = (self.cameraResolutionWidth, self.cameraResolutionHeight)
        self.camera.framerate = 15
        self.FilesUploader = Uploader(self.rawConfig["upload"])
        self.StatusDisplay = StatusDisplay(self.uploadsQueue, self.uploadIntervalCheckConnection)

        os.putenv("DISPLAY", ":0.0")

        self.button = Button(self.shutterButtonPin, pull_up=True)
        self.flash = LED(self.flashLightPin)
        self.buttonLED = LED(self.buttonLEDPin)

    def Start(self):
        try:
            if (self.fullScreen):
                root = tk.Tk()
                root.attributes('-fullscreen', True)
                root.configure(bg='black')
                root.update()

            logging.info("Starting...")
            self.camera.start_preview()
            if self.cameraEnableFrameOverlayInPreview:
                self.CameraFrameOverlay("frame.png")
            self.StartListeningButtonPush()
            logging.info("Start finished")

            threadStatusDisplay = Thread(name="StatusDisplayThread", target=self.StartStatusDisplay, args=(
                self.run_event,))
            threadStatusDisplay.start()

            threadUploader = Thread(name="UploaderThread", target=self.ProcessFilesToUploadQueue, args=(
                self.uploadsQueue, self.run_event,))
            threadUploader.start()
            self.buttonLED.on()

            self.WhenButtonPushed()

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
            self.cameraEnableFrameOverlayInPreview = config["camera"]["cameraEnableFrameOverlayInPreview"]
            self.shutterButtonPin = config["pins"]["shutterButtonPin"]
            self.buttonLEDPin = config["pins"]["buttonLEDPin"]
            self.flashLightPin = config["pins"]["flashLightPin"]
            self.minimumImageAlphaValue = config["alpha_values"]["minimumImageAlphaValue"]
            self.maximumImageAlphaValue = config["alpha_values"]["maximumImageAlphaValue"]
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
            self.isFunnyModeEnabled = config["funnyMode"]["enabled"]
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

        logging.info("Button pushed")

        self.StopListeningButtonPush()

        self.TakePicture()

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
            self.ShowCountDown()
            self.buttonLED.off()
            self.flash.on()
            self.camera.capture(path_full)
            self.flash.off()
            logging.info("Image picture captured")

            self.GenerateThumbnail(path_full, path_thumb)

            if self.picturesUploadEnabled:
                self.EnqueueFilesForUpload(path_full, path_thumb)

            if self.funOverlay is not None:
                time.sleep(1)
                logging.info("Removing funny overlay")
                self.RemoveOverlay(self.funOverlay)
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

    def GenerateOverlay(self, filename, overlay_layer, alphaValue):
        try:
            overlayFile = os.path.join(self.resourcesDirectory, filename)
            img = Image.open(overlayFile)
            pad = Image.new('RGBA', (
                ((img.size[0] + 31) // 32) * 32,
                ((img.size[1] + 15) // 16) * 16,
            ))
            pad.paste(img, (0, 0), img)
            overlay = self.camera.add_overlay(pad.tobytes(), size=img.size)
            overlay.layer = overlay_layer
            overlay.alpha = 0
            overlay.alpha = alphaValue
        except:
            e = sys.exc_info()[0]
            logging.error(e)

        return overlay

    def RemoveOverlay(self, overlay):
        self.camera.remove_overlay(overlay)
        
    def IsFunTime(self):
        funNumber = randint(0, 100)
        return funNumber <= self.funnyModeProbabilityPercent

    def CameraCountDownOverlay(self):
        countDownPictures = self.countDownPicturesArray
        counter = 0
        isThisAFunnyRound = self.IsFunTime()
        for picture in countDownPictures:
            counter = counter + 1
            if self.isFunnyModeEnabled and isThisAFunnyRound and counter == 2:
                logging.info("Is fun time!");
                chosenFunnyPicture = random.choice(self.funnyPicturesArray)
                logging.info("Adding funny overlay: " + chosenFunnyPicture)
                self.funOverlay = self.GenerateOverlay(chosenFunnyPicture, 4, self.maximumImageAlphaValue)
            countDownOverlay = self.GenerateOverlay(picture, 4, self.maximumImageAlphaValue)
            time.sleep(self.countdownStepLength)
            self.RemoveOverlay(countDownOverlay)

    def CameraFrameOverlay(self, filename):
        self.frame_overlay = self.GenerateOverlay(filename, 3, self.maximumImageAlphaValue)

    def DoNothing(self):
        return
