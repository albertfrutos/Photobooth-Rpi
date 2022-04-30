import json
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from threading import *
from tkinter import Button

from PIL import Image
from grpclib import Status
from gpiozero import Button, LED
from picamera import PiCamera

from Uploader import Uploader
from StatusDisplay import StatusDisplay


class Photobooth():
    frame_overlay = None
    event_execution_ongoing = False

    run_event = threading.Event()
    run_event.set()
    uploadsQueue = queue.Queue(maxsize=0)

    logging.basicConfig(
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.DEBUG, format='%(asctime)s - [%(levelname)s] (%(threadName)-9s) %(message)s', )

    def __init__(self):
        self.overlay = None
        self.camera_width = None
        self.camera_height = None
        self.camera_enable_frame_overlay = None
        self.pin_button = None
        self.pin_button = None
        self.pin_flash = None
        self.pin_flash = None
        self.alpha_min = None
        self.alpha_max = None
        self.countdown_time_step = None
        self.upload_interval_check_connection_seconds = None
        self.upload_pictures_endPoint_full_resolution = None
        self.upload_pictures_endPoint_thumbnail = None
        self.upload_JSON_endPoint = None
        self.upload_JSON_apikey = None
        self.pictures_directory_full_resolution = None
        self.pictures_directory_thumbnail = None
        self.pictures_overlayed_directory = None
        self.pictures_base_filename = None
        self.pictures_save_overlayed = None
        self.pictures_upload_pictures = None
        self.resources_directory = None
        self.frame_picture = None
        self.countdown_pictures_array = None

        self.LoadConfiguration()
        
        self.camera = PiCamera()
        self.camera.resolution = (self.camera_width, self.camera_height)
        self.camera.framerate = 15
        self.FilesUploader = Uploader(self.upload_pictures_endPoint_full_resolution,
                                      self.upload_pictures_endPoint_thumbnail, self.upload_JSON_endPoint,
                                      self.upload_JSON_apikey)
        self.StatusDisplay = StatusDisplay(self.uploadsQueue,self.upload_interval_check_connection_seconds)
        
        os.putenv("DISPLAY", ":0.0")

        self.button = Button(self.pin_button, pull_up=True)
        self.flash = LED(self.pin_flash)

        self.FilesUploader.gDriveUploader.Authenticate()

    def Start(self):
        try:
            logging.info("Starting...")
            self.camera.start_preview()
            time.sleep(2)
            if self.camera_enable_frame_overlay:
                self.CameraFrameOverlay("frame.png")
            self.StartListeningButtonPush()
            logging.info("Start finished")

            threadStatusDisplay = Thread(name="StatusDisplayThread", target=self.StartStatusDisplay, args=(
                self.run_event,))
            threadStatusDisplay.start()
            
            threadUploader = Thread(name="UploaderThread", target=self.ProcessFilesToUploadQueue, args=(
                self.uploadsQueue, self.run_event,))
            threadUploader.start()            
        except:
            e = sys.exc_info()[0]
            logging.error(e)

    def LoadConfiguration(self):

        with open('config.json', 'r') as configFile:
            config = json.load(configFile)
            self.camera_width = config["camera"]["camera_width"]
            self.camera_height = config["camera"]["camera_height"]
            self.camera_enable_frame_overlay = config["camera"]["camera_enable_frame_overlay"]
            self.pin_button = config["pins"]["pin_button"]
            self.pin_flash = config["pins"]["pin_flash"]
            self.alpha_min = config["alpha_values"]["alpha_min"]
            self.alpha_max = config["alpha_values"]["alpha_max"]
            self.countdown_time_step = config["countdown"]["countdown_time_step"]
            self.upload_interval_check_connection_seconds = config[
                "upload"]["upload_interval_check_connection_seconds"]
            self.upload_pictures_endPoint_full_resolution = config[
                "upload"]["upload_pictures_endPoint_full_resolution"]
            self.upload_pictures_endPoint_thumbnail = config[
                "upload"]["upload_pictures_endPoint_thumbnail"]
            self.upload_JSON_endPoint = config["upload"]["upload_JSON_endPoint"]
            self.upload_JSON_apikey = config["upload"]["upload_JSON_apikey"]
            self.pictures_directory_full_resolution = config[
                "pictures"]["pictures_directory_full_resolution"]
            self.pictures_directory_thumbnail = config["pictures"]["pictures_directory_thumbnail"]
            self.pictures_overlayed_directory = config["pictures"]["pictures_overlayed_directory"]
            self.pictures_base_filename = config["pictures"]["pictures_base_filename"]
            self.pictures_save_overlayed = config["pictures"]["pictures_save_overlayed"]
            self.pictures_upload_pictures = config["pictures"]["pictures_upload_pictures"]
            self.resources_directory = config["resources"]["resources_directory"]
            self.frame_picture = config["resources"]["frame_picture_overlay"]
            self.countdown_pictures_array = config["resources"]["countdown_pictures_array"]

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
        filename = self.pictures_base_filename + "_" + \
                   datetime.now().strftime('%Y%m%d%H%M%S') + '.jpg'
        logging.info("filename is " + filename)
        return filename

    def TakePicture(self):
        try:
            pictureName = self.GetFilename()
            path_full = os.path.join(
                self.pictures_directory_full_resolution, pictureName)
            path_thumb = os.path.join(
                self.pictures_directory_thumbnail, pictureName)

            self.flash.on()
            self.camera.capture(path_full)
            self.flash.off()

            logging.info("Image picture captured")
            
            if self.pictures_save_overlayed:
                self.SaveWithOverlay(path_full, pictureName)
                
            self.GenerateThumbnail(path_full, path_thumb)
            if self.pictures_upload_pictures:
                self.EnqueueFilesForUpload(path_full, path_thumb)

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
                if not (self.uploadsQueue.empty()) :
                    filepaths = self.uploadsQueue.get()
                    logging.info("Processing paths for " +
                                 filepaths[0] + " and " + filepaths[1])
                    self.FilesUploader.UploadFile(filepaths[0], filepaths[1], True)
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
            frame = os.path.join(self.resources_directory, self.frame_picture)
            overlayedImage = os.path.join(
                self.pictures_directory_full_resolution, self.pictures_overlayed_directory, filename)
            logging.info(overlayedImage)
            imgFrame = Image.open(frame)
            background.paste(imgFrame, (0, 0), imgFrame)
            background.save(overlayedImage)
        except:
            e = sys.exc_info()[0]
            logging.error(e)

    def GenerateOverlay(self, filename, overlay_layer, alphaValue):
        try:
            overlayFile = os.path.join(self.resources_directory, filename)
            img = Image.open(overlayFile)
            pad = Image.new('RGBA', (
                ((img.size[0] + 31) // 32) * 32,
                ((img.size[1] + 15) // 16) * 16,
            ))
            pad.paste(img, (0, 0), img)
            self.overlay = self.camera.add_overlay(pad.tobytes(), size=img.size)
            self.overlay.layer = overlay_layer
            self.overlay.alpha = 0
            self.overlay.alpha = alphaValue
        except:
            e = sys.exc_info()[0]
            logging.error(e)

        return self.overlay

    def RemoveOverlay(self, overlay):
        self.camera.remove_overlay(overlay)

    def CameraCountDownOverlay(self):
        countDownPictures = self.countdown_pictures_array

        for picture in countDownPictures:
            overlay = self.GenerateOverlay(picture, 4, self.alpha_max)
            time.sleep(self.countdown_time_step)
            self.RemoveOverlay(overlay)

    def CameraFrameOverlay(self, filename):
        self.frame_overlay = self.GenerateOverlay(filename, 3, self.alpha_max)

    def DoNothing(self):
        return
