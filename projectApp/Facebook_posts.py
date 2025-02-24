import requests
import json
import os
from .google_sheets import read_data

# Facebook API 設定
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")  # 你的 API Token
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")  # 粉絲專頁 ID
FIELDS = "message,full_picture,permalink_url"
SYSTEM_STATE_SHEET = '系統狀態'

def get_facebook_posts():
    data = read_data(SYSTEM_STATE_SHEET)
    if not data:
        print("無法讀取系統狀態數據")
        return
    for row in data:
        if len(row) > 0:
            if row[0] == 'NumbersOfPosts':
                LIMIT = int(row[1])
                # print(LIMIT)
                break
    url = f"https://graph.facebook.com/v22.0/{PAGE_ID}/posts"
    params = {
        'fields': FIELDS,
        'access_token': ACCESS_TOKEN,
        'limit': LIMIT
    }
    response = requests.get(url, params = params)
    # print(response)

    if response.status_code == 200:
        data = response.json()
        postlist = []  # 存儲多篇貼文
        if 'data' in data and len(data['data']) > 0:
            for post in data['data']:
                post_data = {
                    "message": post.get("message", "（無文字內容）"),
                    "image": post.get("full_picture", None),
                    "link": post.get("permalink_url", None)
                }
                postlist.append(post_data)

        return postlist
    else:
        print(f"❌ API 請求失敗: {response.status_code}")
        return []

# # 測試取得貼文
facebook_posts = get_facebook_posts()
print(json.dumps(facebook_posts, indent=2, ensure_ascii=False))
