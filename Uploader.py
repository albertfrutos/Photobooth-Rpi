import sys

from httplib2 import FailedToDecompressContent
from PHPUploader import PHPUploader
from GDriveUploader import GDriveUploader
import os
import logging


class Uploader:

    def __init__(self, uploadConfig):
        self.uploadAgent = None
        if uploadConfig["upload_mode"] == "GDrive": #GDrive Upload
            self.UploadAgent = GDriveUploader(uploadConfig["upload_pictures_endPoint_full_resolution"],
                                              uploadConfig["upload_pictures_endPoint_thumbnail"],
                                              uploadConfig["upload_JSON_endPoint"],
                                              uploadConfig["upload_JSON_apikey"])
            self.UploadAgent.Authenticate()
        else: #PHP endpoint upload
            self.UploadAgent = PHPUploader(uploadConfig["upload_PHP_endPoint"])

    def UploadFile(self, filePath, filePathThumb):
        try:
            if isinstance(filePath, str) and isinstance(filePathThumb, str):
                logging.info("Will upload a single image as the name corresponds to a file")
                self.UploadAgent.UploadFile(filePath, filePathThumb)
            elif isinstance(filePath, list) and isinstance(filePathThumb, list):
                logging.info("Will upload a multiple images as the name corresponds to an array/list")
                for file, fileThumb in zip(filePath, filePathThumb):
                    logging.info("Uploading full image {} and thumbnail {}".format(file, fileThumb))
                    self.UploadAgent.UploadFile(file, fileThumb)
            else:
                logging.info("No compatible upload format found. Will exit and no upload will be done.")
        except:
            e = sys.exc_info()[0]
            logging.error(e)
