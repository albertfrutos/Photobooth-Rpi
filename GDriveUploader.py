import logging
import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from JsonDBUpdater import JsonDBUpdater


class GDriveUploader:
    def __init__(self, parentFolderIDOriginal, parentFolderIDThumb, jsonUpdateEndpoint, jsonUpdateApikey):

        # If modifying these scopes, delete the file token.json.
        
        self.scopes = ['https://www.googleapis.com/auth/drive.metadata',
                       'https://www.googleapis.com/auth/drive.file',
                       'https://www.googleapis.com/auth/drive',
                       'https://www.googleapis.com/auth/drive.appdata'
                       ]

        self.service = None

        self.parentFolderOriginal = parentFolderIDOriginal
        self.parentFolderThumb = parentFolderIDThumb

        self.jsonDBUpdater = JsonDBUpdater(jsonUpdateEndpoint, jsonUpdateApikey)

    def Authenticate(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('drive', 'v3', credentials=creds)

    def UploadFileToGDrive(self, localPath, mimetype, parentFolder, filenameInDestination):
        self.Authenticate()
        file_metadata = {'name': filenameInDestination, 'parents': [parentFolder]}
        media = MediaFileUpload(localPath, mimetype=mimetype)
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        fileID = file.get('id')
        self.service.permissions().create(body={"role": "reader", "type": "anyone"}, fileId=file.get('id')).execute()
        logging.info('File ID: ' + fileID)
        self.service = None
        return fileID

    def AssembleDownloadLink(self, fileId):
        downloadLink = "https://drive.google.com/uc?id=" + fileId + "&export=download"
        return downloadLink

    def UploadFile(self,filePath, filePathThumb):
        try:
            filename = os.path.basename(filePath)

            uploadedFileID = self.UploadFileToGDrive(filePath, 'image/jpeg', self.parentFolderOriginal, filename)
            uploadedFileIDThumb = self.UploadFileToGDrive(filePathThumb, 'image/jpeg', self.parentFolderThumb, filename)

            downloadLink = self.AssembleDownloadLink(uploadedFileID)
            downloadLinkThumb = self.AssembleDownloadLink(uploadedFileIDThumb)


            self.jsonDBUpdater.UpdateJSONDB(filename, downloadLink, downloadLinkThumb)

        except:
            e = sys.exc_info()[0]
            logging.error(e)

