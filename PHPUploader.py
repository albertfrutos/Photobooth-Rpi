import logging
import os.path
import sys

import requests;


class PHPUploader:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def UploadFile(self, filePath, filePathThumb):
        try:
            url = self.endpoint
            filelist = dict()
            filelist['myfile[0]'] = open(filePath, 'rb')
            filelist['myfile[1]'] = open(filePathThumb, 'rb')
            r = requests.post(url, files=filelist)
            if r.status_code != 200:
                print('sendErr: ' + r.url)
            else:
                print(r.text)
        except:
            e = sys.exc_info()[0]
            logging.error(e)


