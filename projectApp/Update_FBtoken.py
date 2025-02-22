import requests
import json
import os

# 設定 Facebook 應用程式資訊
APP_ID = os.getenv("FB_APP_ID")
APP_SECRET = os.getenv("FB_APP_SECRET")
LONG_LIVED_USER_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

# 設定 Render API 相關資訊
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")

# Facebook Graph API 端點
fb_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
fb_params = {
    'grant_type': 'fb_exchange_token',
    'client_id': APP_ID,
    'client_secret': APP_SECRET,
    'fb_exchange_token': LONG_LIVED_USER_ACCESS_TOKEN
}

# 取得新的存取權杖
fb_response = requests.get(fb_url, params=fb_params)
if fb_response.status_code == 200:
    new_access_token = fb_response.json().get('access_token')

    # Render API 端點
    render_url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars"

    # 取得目前的環境變數
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {RENDER_API_KEY}"
    }
    env_vars = requests.get(render_url, headers=headers).json()

    # 找到並更新 FB_ACCESS_TOKEN 變數
    for var in env_vars:
        if var["key"] == "FACEBOOK_ACCESS_TOKEN":
            env_var_id = var["id"]
            update_url = f"{render_url}/{env_var_id}"
            update_data = {"value": new_access_token}

            update_response = requests.patch(update_url, json=update_data, headers=headers)
            if update_response.status_code == 200:
                print("新的存取權杖已成功更新到 Render 環境變數。")
            else:
                print("更新 Render 環境變數時發生錯誤:", update_response.json())
            break
else:
    print("取得新的存取權杖時發生錯誤:", fb_response.json())
