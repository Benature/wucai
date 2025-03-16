from __future__ import annotations
import hashlib
import time
import json
from subprocess import Popen, PIPE
import random
from typing import Dict, List
from typing_extensions import Literal
import datetime

__version__ = "0.1.2"


def timestamp(t):
    if isinstance(t, datetime.date):
        return int(
            datetime.datetime.strptime(t.isoformat(), "%Y-%m-%d").timestamp())
    elif isinstance(t, datetime.datetime):
        return int(t.timestamp())
    else:
        raise ValueError(f"Invalid timestamp {type(t)}")


class WuCai():

    def __init__(self,
                 token: str,
                 app_id: str = None,
                 version: str = None,
                 random_sleep: bool | int = True) -> None:
        """
        Args:
            token (str): Bearer token
        """
        self.version = version or "25.2.3"
        self.app_id = str(app_id) if app_id is not None else "20"
        self.ep = "web"
        self.authorization = "Bearer " + token
        self.preAPI = "https://marker.dotalk.cn/apix/wucai"
        self.random_sleep_time = int(random_sleep) if isinstance(
            random_sleep, bool) else random_sleep

    def search_tag_note(self,
                        tags: str = None,
                        note_idx: str = None,
                        nav: Literal['today', 'inbox', 'later', 'archive',
                                     'star', 'daily', 'all', 'trash',
                                     'untag'] = None,
                        order: Literal['time-desc', 'time-asc', 'utime-desc',
                                       'stars-desc'] = 'time-desc',
                        page: int = 1,
                        page_size: int = 11,
                        page_max: int = None) -> List[Dict]:
        """根据 tags/noteIdx 搜索笔记
        
        Args:
            tags (str, optional): tag. Defaults to None.
            noteIdx (str, optional): noteIdx. Defaults to None.
            nav (Literal['today', 'inbox', 'later', 'archive', 'star', 'daily', 'all', 'trash', 'untag'], optional): 
                导航栏. Defaults to None.
                
                - today: 24小时
                - inbox: Inbox
                - later: 稍读
                - archive: 归档
                - star: 星标
                - daily: Daily
                - all: 所有
                - trash: 回收站
                
            sortBy (Literal['time-desc', 'time-asc', 'utime-desc','stars-desc'], optional): 
                排序方式. Defaults to 'time-desc'.
            page (int, optional): page. Defaults to 1.
            pageSize (int, optional): pageSize. Defaults to 11.
            
        Returns:
            Dict: 笔记列表
        """
        if page_max is None:
            if page > page_size:
                return []
        else:
            if page > page_max:
                return []

        assert (
            (tags is not None) ^ (note_idx is not None) ^
            (nav is not None)), "tags or noteIdx or nav should be provided one"
        payload = {
            "page": page,
            "pagesize": page_size,
            "sort": order,
            "pageId": 0,
            "tmhl": 0,
            "fid": 0,
            "useSearch": 0,
        }

        if tags is not None:
            payload['tags'] = tags
        if note_idx is not None:
            payload['noteidx'] = note_idx
        if nav is not None:
            payload['in'] = nav

        response = self.curl("user/searchtagnote", payload)
        this_page = response['data']['list']
        if this_page is None:
            return []
        self.random_sleep()
        next_page = self.search_tag_note(tags=tags,
                                         note_idx=note_idx,
                                         nav=nav,
                                         order=order,
                                         page=page + 1,
                                         page_size=page_size,
                                         page_max=page_max)
        return this_page + next_page

    def index_card_list(self,
                        tags: str = None,
                        nav: Literal['today', 'all'] = 'all',
                        order: Literal['time-desc', 'time-asc',
                                       'utime-desc'] = 'time-desc',
                        page: int = 1,
                        page_size: int = 26,
                        page_max: int = None) -> List:
        """获取卡片列表
        
        Args:
            tags (str, optional): tag. Defaults to None. 可按 tag 进行搜索卡片。
            page (int, optional): 从第几页开始获取列表. Defaults to 1，默认从第一页开始。
            page_size (int, optional): 每页大小. Defaults to 26.
            page_max (int, optional): 最大页数. Defaults to None.
            
        Returns:
            List: 卡片列表
        """
        if page_max is not None and page > page_max:
            return []

        payload = {
            'in': nav,
            'page': page,
            'pagesize': page_size,
            'sort': order,
            'pageId': 0,
            'myid': 0,
            'tmhl': 0,
        }
        if tags is not None:
            payload['tags'] = tags

        response = self.curl("user/indexcardlist", payload)
        if response['code'] != 1:
            return []
        if response['data']['items'] is None:
            return []
        self.random_sleep()
        next_page = self.index_card_list(tags=tags,
                                         nav=nav,
                                         order=order,
                                         page=page + 1,
                                         page_size=page_size,
                                         page_max=page_max)
        return response['data']['items'] + next_page

    def detail(self, note_id: int) -> Dict:
        """根据 noteId 获取笔记详情
        
        Args:
            noteId (int): noteId
            
        Returns:
            Dict: 笔记详情
        """
        payload = {"noteId": int(note_id)}
        return self.curl("note/detail", payload)

    def update_tags(self, note_id: int, tags: str | List[str]):
        """更新标签"""
        if isinstance(tags, str):
            tags = tags.split(",")

        for i in range(len(tags)):
            tags[i] = tags[i].strip()
            if not tags[i].startswith("#"):
                tags[i] = "#" + tags[i]

        tags_string = ",".join(tags)

        payload = {
            "noteId": note_id,
            "tags": tags_string,
        }
        return self.curl("note/updatetags", payload)

    def add_tags(self, note_id: int, new_tags: str | List[str]):
        """添加标签"""
        # get current tags
        current_tags_set = set(
            self.detail(note_id)['data']['items'][0]['tags'] or [])

        if isinstance(new_tags, str):
            new_tags = new_tags.split(",")
        new_tags_set = set(map(lambda x: "#" + x.strip().lstrip("#"),
                               new_tags))

        tags = list(current_tags_set.union(new_tags_set))
        return self.update_tags(note_id, tags)

    def remove_tags(self, note_id: int, tags: str | List[str]):
        """删除标签"""
        # get current tags
        current_tags_set = set(
            self.detail(note_id)['data']['items'][0]['tags'] or [])
        if isinstance(tags, str):
            tags = tags.split(",")
        tags_set = set(map(lambda x: "#" + x.strip().rstrip("#"), tags))

        tags = list(current_tags_set.difference(tags_set))
        return self.update_tags(note_id, tags)

    def move_to_folder(self, note_ids: List[int] | int, folder_id: int,
                       full_path: str):
        """移动至文件夹"""
        if not isinstance(note_ids, list):
            note_ids = [note_ids]
        payload = {
            "noteIds": note_ids,
            "folderId": folder_id,
            "fullPath": full_path
        }
        return self.curl("note/movetofolder", payload)

    def create_folder(self, full_path: str):
        """创建文件夹"""
        return self.curl("folder/create", {"fullPath": full_path})

    def curl(self, func: str, payload: Dict):
        """query data via curl, as requests failed to handle the data correctly for unknown reasons
        
        Args:
            func (str): function name
            data (Dict): data to be sent
        
        Returns:
            Dict: response data
        """
        payload["reqtime"] = int(time.time())
        params = self._get_params(payload)
        params_string = "&".join([f"{k}={v}" for k, v in params.items()])
        cmd = f"""curl --location '{self.preAPI}/{func}?{params_string}' \
                  --header 'Authorization: {self.authorization}' \
                  --header 'Content-Type: application/json' \
                  --data '{json.dumps(payload).replace(" ", "")}'
                  """
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
        response_text = p.stdout.read()
        payload = json.loads(response_text)
        return payload

    def _calc_signx(self, payload: Dict):
        """calculate signx"""
        Fa = lambda e: hashlib.md5((e).encode("utf-8")).hexdigest()
        l = '166p7jjd83L8m5Mk'
        c = json.dumps(payload).replace(" ", "")
        signx = Fa(l + Fa(c + l))
        return signx

    def _get_params(self, payload: Dict):
        signx = self._calc_signx(payload)
        params = {
            "appid": self.app_id,
            "ep": self.ep,
            "version": self.version,
            "signx": signx,
            "reqtime": str(payload['reqtime']),
        }
        return params

    def random_sleep(self):
        time.sleep(random.random() * self.random_sleep_time)

    @staticmethod
    def timestamp(*args, **kwargs):
        return timestamp(*args, **kwargs)
