from __future__ import annotations
import hashlib
import time
import json
from subprocess import Popen, PIPE
import random
from typing import Dict, List
from typing_extensions import Literal

__version__ = "0.1.0"


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
                        noteIdx: str = None,
                        nav: Literal['today', 'inbox', 'later', 'archive',
                                     'star', 'daily', 'all', 'trash',
                                     'untag'] = None,
                        sortBy: Literal['time-desc', 'time-asc', 'utime-desc',
                                        'stars-desc'] = 'time-desc',
                        page: int = 1,
                        pageSize: int = 11,
                        maxPage: int = None) -> List[Dict]:
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
        if maxPage is None:
            if page > pageSize:
                return []
        else:
            if page > maxPage:
                return []

        assert (
            (tags is not None) ^ (noteIdx is not None) ^
            (nav is not None)), "tags or noteIdx or nav should be provided one"
        payload = {
            "page": page,
            "pagesize": pageSize,
            "sort": sortBy,
            "pageId": 0,
            "tmhl": 0,
            "fid": 0,
            "useSearch": 0,
        }

        if tags is not None:
            payload['tags'] = tags
        if noteIdx is not None:
            payload['noteidx'] = noteIdx
        if nav is not None:
            payload['in'] = nav

        response = self.curl("user/searchtagnote", payload)
        this_page = response['data']['list']
        if this_page is None:
            return []
        self.random_sleep()
        next_page = self.search_tag_note(tags=tags,
                                         noteIdx=noteIdx,
                                         nav=nav,
                                         sortBy=sortBy,
                                         page=page + 1,
                                         pageSize=pageSize,
                                         maxPage=maxPage)
        return this_page + next_page

    def index_card_list(self,
                        tags: str = None,
                        page: int = 1,
                        pageSize: int = 26,
                        maxPage: int = None) -> List:
        """获取卡片列表
        
        Args:
            tags (str, optional): tag. Defaults to None. 可按 tag 进行搜索卡片。
            page (int, optional): 从第几页开始获取列表. Defaults to 1，默认从第一页开始。
            pageSize (int, optional): 每页大小. Defaults to 26.
            page_max (int, optional): 最大页数. Defaults to None.
            
        Returns:
            List: 卡片列表
        """
        if maxPage is None:
            if page > pageSize:
                return []
        else:
            if page > maxPage:
                return []

        payload = {
            'page': page,
            'pagesize': pageSize,
            'sort': 'time-desc',
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
        next_page = self.index_card_list(tags=tags, page=page + 1)
        return response['data']['items'] + next_page

    def detail(self, noteId: int) -> Dict:
        """根据 noteId 获取笔记详情
        
        Args:
            noteId (int): noteId
            
        Returns:
            Dict: 笔记详情
        """
        payload = {"noteId": int(noteId)}
        return self.curl("note/detail", payload)

    def update_tags(self, noteId: int, tags: str | List[str]):
        """更新标签"""
        if isinstance(tags, str):
            tags = tags.split(",")

        for i in range(len(tags)):
            tags[i] = tags[i].strip()
            if not tags[i].startswith("#"):
                tags[i] = "#" + tags[i]

        tags_string = ",".join(tags)

        payload = {
            "noteId": noteId,
            "tags": tags_string,
        }
        return self.curl("note/updatetags", payload)

    def add_tags(self, noteId: int, new_tags: str | List[str]):
        """添加标签"""
        # get current tags
        current_tags_set = set(
            self.detail(noteId)['data']['items'][0]['tags'] or [])

        if isinstance(new_tags, str):
            new_tags = new_tags.split(",")
        new_tags_set = set(map(lambda x: "#" + x.strip().lstrip("#"),
                               new_tags))

        tags = list(current_tags_set.union(new_tags_set))
        return self.update_tags(noteId, tags)

    def remove_tags(self, noteId: int, tags: str | List[str]):
        """删除标签"""
        # get current tags
        current_tags_set = set(
            self.detail(noteId)['data']['items'][0]['tags'] or [])
        if isinstance(tags, str):
            tags = tags.split(",")
        tags_set = set(map(lambda x: "#" + x.strip().rstrip("#"), tags))

        tags = list(current_tags_set.difference(tags_set))
        return self.update_tags(noteId, tags)

    def move_to_folder(self, noteIds: List[int] | int, folderId: int,
                       fullPath: str):
        """移动至文件夹"""
        if not isinstance(noteIds, list):
            noteIds = [noteIds]
        payload = {
            "noteIds": noteIds,
            "folderId": folderId,
            "fullPath": fullPath
        }
        return self.curl("note/movetofolder", payload)

    def create_folder(self, fullPath: str):
        """创建文件夹"""
        return self.curl("folder/create", {"fullPath": fullPath})

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
