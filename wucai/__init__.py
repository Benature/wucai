from __future__ import annotations
import hashlib
import time
import json
from subprocess import Popen, PIPE
import random
from typing import Dict, List

__version__ = "0.0.1"


class WuCai():

    def __init__(self,
                 token: str,
                 appId: str = None,
                 version: str = None) -> None:
        self.version = version or "24.10.10"
        self.appID = str(appId) is appId is not None or "20"
        self.ep = "web"
        self.authorization = "Bearer " + token
        self.url_prefix = "https://marker.dotalk.cn/apix/wucai"

    def _get_reqTime(self):
        """get current timestamp"""
        return int(time.time())

    def _calc_signx(self, data_json: Dict):
        """calculate signx"""
        Fa = lambda e: hashlib.md5((e).encode("utf-8")).hexdigest()
        l = '166p7jjd83L8m5Mk'
        c = json.dumps(data_json).replace(" ", "")
        signx = Fa(l + Fa(c + l))
        return signx

    def get_params(self, data_json: Dict):
        signx = self._calc_signx(data_json)
        params = {
            "appid": self.appID,
            "ep": self.ep,
            "version": self.version,
            "signx": signx,
            "reqtime": str(data_json['reqtime']),
        }
        return params

    def searchTagNote(self,
                      tags: str = None,
                      noteIdx: str = None,
                      page: int = 1,
                      pageSize: int = 11):
        assert (tags is not None) ^ (
            noteIdx is not None), "tags or noteIdx should be provided one"
        data_json = {
            "page": page,
            "pagesize": pageSize,
            "sort": "time-desc",
            "pageId": 0,
            "tmhl": 0,
            "fid": 0,
            "useSearch": 0,
            "reqtime": self._get_reqTime()
        }

        if tags is not None:
            data_json['tags'] = tags
        if noteIdx is not None:
            data_json['noteidx'] = noteIdx

        response = self.cUrl("user/searchtagnote", data_json)
        return response

    def detail(self, noteId: int):
        data_json = {"noteId": int(noteId), "reqtime": self._get_reqTime()}
        return self.cUrl("note/detail", data_json)

    def indexCardList(self,
                      tags: str = None,
                      page: int = 1,
                      pageSize: int = 26,
                      page_max: int = None):
        if page_max is None:
            if page > pageSize:
                return []
        else:
            if page > page_max:
                return []

        data_json = {
            'page': page,
            'pagesize': pageSize,
            'sort': 'time-desc',
            'pageId': 0,
            'myid': 0,
            'tmhl': 0,
            'reqtime': self._get_reqTime()
        }
        if tags is not None:
            data_json['tags'] = tags

        response = self.cUrl("user/indexcardlist", data_json)
        if response['code'] != 1:
            return []
        if response['data']['items'] is None:
            return []
        time.sleep(random.random())
        next_page = self.indexCardList(tags=tags, page=page + 1)
        return response['data']['items'] + next_page

    def cUrl(self, func: str, data: Dict):
        params = self.get_params(data)
        """query data via curl, as requests failed to handle the data correctly for unknown reasons"""
        params_string = "&".join([f"{k}={v}" for k, v in params.items()])
        cmd = f"""curl --location '{self.url_prefix}/{func}?{params_string}' \
                  --header 'Authorization: {self.authorization}' \
                  --header 'Content-Type: application/json' \
                  --data '{json.dumps(data).replace(" ", "")}'
                  """
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
        response_text = p.stdout.read()
        data = json.loads(response_text)
        return data
