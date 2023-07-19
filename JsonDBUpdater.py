import json
import requests
import logging


class JsonDBUpdater:
    def __init__(self, jsonUpdateEndpoint, apikey):
        self.url = jsonUpdateEndpoint
        self.apikey = apikey

    def UpdateJSONDB(self, filename, file_url, file_url_thumb):
        entry = {
            "filename": filename,
            "url": file_url,
            "url_thumb": file_url_thumb
        }

        data = self.GetCurrentJSON()
        data["pictures"].append(entry)
        self.UpdateJSON(data)

    def UpdateJSON(self, data):
        headers = {
            'Content-Type': 'application/json',
            'X-Master-Key': self.apikey,
            'X-BIN-META': 'false'
        }

        req = requests.put(self.url, json=data, headers=headers)
        logging.info("JSON updated")

    def GetCurrentJSON(self):
        headers = {
            'X-Master-Key': self.apikey,
            'X-BIN-META': 'false'
        }
        req = requests.get(self.url + '/latest', json=None, headers=headers)
        return req.json()
