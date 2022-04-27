import sys

from httplib2 import FailedToDecompressContent
from GDriveUploader import GDriveUploader
from JsonDBUpdater import JsonDBUpdater
import os
import logging


class Uploader:

    def __init__(self, parentFolderIDOriginal, parentFolderIDThumb, jsonUpdateEndpoint, jsonUpdateApikey):
        self.JSONUpdateEndpoint = jsonUpdateEndpoint
        self.parentFolderOriginal = parentFolderIDOriginal
        self.parentFolderThumb = parentFolderIDThumb
        self.gDriveUploader = GDriveUploader(parentFolderIDOriginal, parentFolderIDThumb)
        self.jsonDBUpdater = JsonDBUpdater(jsonUpdateEndpoint, jsonUpdateApikey)

    def UploadFile(self, filePath, filePathThumb, updateJSON = True):
        try:
            if isinstance(filePath, str) and isinstance(filePathThumb, str):
                logging.info("Will upload a single image as the name corresponds to a file")
                self.UploadFileSingleMode(filePath, filePathThumb, updateJSON)
            elif isinstance(filePath, list) and isinstance(filePathThumb, list):
                logging.info("Will upload a multiple images as the name corresponds to an array/list")
                for file, fileThumb in zip(filePath,filePathThumb):
                    logging.info("Uploading full image {} and thumbnail {}".format(file,fileThumb))
                    self.UploadFileSingleMode(file, fileThumb, updateJSON)
            else:
                logging.info("No compatible upload format found. Will exit and no upload will be done.")
        except:
            e = sys.exc_info()[0]
            logging.error(e)
        
    def UploadFileSingleMode(self,filePath, filePathThumb, updateJSON):
        try:
            filename = os.path.basename(filePath)

            uploadedFileID = self.gDriveUploader.UploadFile(filePath, 'image/jpeg', self.parentFolderOriginal, filename)
            uploadedFileIDThumb = self.gDriveUploader.UploadFile(filePathThumb, 'image/jpeg', self.parentFolderThumb, filename)

            downloadLink = self.gDriveUploader.AssembleDownloadLink(uploadedFileID)
            downloadLinkThumb = self.gDriveUploader.AssembleDownloadLink(uploadedFileIDThumb)

            if updateJSON:
               self.jsonDBUpdater.UpdateJSONDB(filename, downloadLink, downloadLinkThumb)

        except:
            e = sys.exc_info()[0]
            logging.error(e)



