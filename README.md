<a href="https://wucaiapp.com/"><img src="https://www.wucainote.com/_next/image?url=%2Flogo.png&w=64&q=75" height="50" align="right"></a>

# 五彩 Python API
python API for wucai ( https://www.wucainote.com , https://marker.dotalk.cn )


[![PyPI](https://img.shields.io/pypi/v/wucai)](https://pypi.org/project/wucai/)

## 安装 Install

```
pip install wucai
```

## 使用 Usage

`token` 请在网页 F12 - Network 中获取

```python
from wucai import WuCai

token = "eyJxxxxxx"  # your Bearer token here

tags = "待读"

wucai = WuCai(token)

# 根据 tag 搜索卡片
cards_response = wucai.indexCardList(tags=tags)
for card in cards_response:
    print(card)
    break

# 根据 tag 搜索笔记
notes_response = wucai.searchTagNote(tags=tags)
if notes_response['code'] == 1:
    for note in notes_response['data']['list']:
        print(note)
        break
```