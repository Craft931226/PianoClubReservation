import requests
import json
import os

# Facebook API 設定
# 這個別忘了上傳GitHub要刪掉
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")  # 你的 API Token
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")  # 粉絲專頁 ID
FIELDS = "message,full_picture,permalink_url"
LIMIT = 1

def get_facebook_posts():
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/posts"
    params = {
        'fields': FIELDS,
        'access_token': ACCESS_TOKEN,
        'limit': LIMIT
    }
    response = requests.get(url, params = params)

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            post = data['data'][0]
            return {
                "message": post.get("message", "（無文字內容）"),
                "image": post.get("full_picture", None),
                "link": post.get("permalink_url", None),
            }
    else:
        print(f"❌ API 請求失敗: {response.status_code}")
        return []

# # 測試取得貼文
# facebook_posts = get_facebook_posts()
# print(json.dumps(facebook_posts, indent=2, ensure_ascii=False))
