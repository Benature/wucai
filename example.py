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
        breakpoint
