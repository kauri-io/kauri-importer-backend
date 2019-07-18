#TODO-> Change ipfs line 17

import requests
import os
import shutil
import configparser

from requests_toolbelt import MultipartEncoder
from urllib.parse import urlparse
import logging

class IpfsHandler:
    def __init__(self, source_url, token):
        # config variables
        self.config = configparser.RawConfigParser()
        self.config.read('config.ini')
        self.kauri_ipfs = 'https://api.dev.kauri.io:443/ipfs/'
        self.JWT_token = token
        # file variables
        self.ipfs_url = None
        self.source_url = source_url
        self.img_bytes = self.get_bytes(self.source_url)
        if self.ipfs_url is None:
            self.json_resp = self.make_a_mp_request(self.img_bytes)
            self.build_url()

    def get_bytes(self, source_url):
        res = requests.get(self.source_url, stream=True)
        f = os.path.basename(urlparse(source_url).path)
        # check filesize, if >= 10MB, skip multipart post request and use CDN URL
        if res.ok and (int(res.headers['content-length']) >= 10000000):
            print(
                '[ATTN] Content length > 10MB: ' + \
                res.headers['content-length'] + '. ' + \
                'Using CDN URL instead.'
            )
            self.ipfs_url = self.source_url
        else:
            print(
                '[OK] Content length <= 10MB: ' + \
                res.headers['content-length'] + '. ' + \
                'POSTing image to Kauri Gateway'
            )
            return (f, res.content)

    def make_a_mp_request(self, img_bytes):
        mp = MultipartEncoder(
                fields = {
                    'file': (self.img_bytes[0], self.img_bytes[1])
                }
        )
        try:
            response = requests.post(
                    self.kauri_ipfs, # kauri ipfs gateway
                    data=mp,
                    headers={
                        'Content-Type': mp.content_type,
                        'X-Auth-Token': 'Bearer ' + self.JWT_token
                        }
            )
            if response.ok:
                return response.json()
            else:
                print('[!] Failed post request. Reason: ' + response.status_code)
        except:
            print('[!] Post request to api gateway failed')
            return None

    def build_url(self):
        new_url = self.kauri_ipfs + self.json_resp['hash']
        self.ipfs_url = new_url
        return None
