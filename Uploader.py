import sys

from httplib2 import FailedToDecompressContent
from PHPUploader import PHPUploader
from GDriveUploader import GDriveUploader
import os
import logging


class Uploader:

    def __init__(self, uploadConfig):
        self.UploadAgents = []
        
        uploadModes = uploadConfig["upload_mode"].split(",");
        for mode in uploadModes:
            if mode == "GDrive": #GDrive Upload
                logging.info("Configuring Uploader class for GDrive UploadAgents")
                agent = GDriveUploader(uploadConfig["upload_GDrive"]["upload_pictures_endPoint_full_resolution"],
                                                uploadConfig["upload_GDrive"]["upload_pictures_endPoint_thumbnail"],
                                                uploadConfig["upload_GDrive"]["upload_JSON_endPoint"],
                                                uploadConfig["upload_GDrive"]["upload_JSON_apikey"])
                agent.Authenticate()
                self.UploadAgents.append(agent);
            elif mode == "PHP": #PHP endpoint upload
                logging.info("Configuring Uploader class for PHP UploadAgents")
                agent = PHPUploader(uploadConfig["upload_PHP"]["upload_PHP_endPoint"])
                self.UploadAgents.append(agent);
            else:
                print("uploadMode" + mode + "unknown. Will not be initialized.")
            

    def UploadFile(self, filePath, filePathThumb):
        try:
            for uploader in self.UploadAgents:
                if isinstance(filePath, str) and isinstance(filePathThumb, str):
                    logging.info("Will upload a single image as the name corresponds to a file")
                    uploader.UploadFile(filePath, filePathThumb)
                elif isinstance(filePath, list) and isinstance(filePathThumb, list):
                    logging.info("Will upload a multiple images as the name corresponds to an array/list")
                    for file, fileThumb in zip(filePath, filePathThumb):
                        logging.info("Uploading full image {} and thumbnail {}".format(file, fileThumb))
                        uploader.UploadFile(file, fileThumb)
                else:
                    logging.info("No compatible upload format found. Will exit and no upload will be done.")
        except:
            e = sys.exc_info()[0]
            logging.error(e)
