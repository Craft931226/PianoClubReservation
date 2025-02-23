import requests
import os
import logging

def refresh_token_handler(request):
    logging.basicConfig(level=logging.INFO)
    
    # 設定 Facebook 應用程式資訊
    APP_ID = os.getenv("FB_APP_ID")
    APP_SECRET = os.getenv("FB_APP_SECRET")

    # 設定 Render API 相關資訊
    RENDER_API_KEY = os.getenv("RENDER_API_KEY")
    RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")

    try:
        # 從 Render 獲取當前的 FACEBOOK_ACCESS_TOKEN
        url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars/FACEBOOK_ACCESS_TOKEN"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {RENDER_API_KEY}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        LONG_LIVED_USER_ACCESS_TOKEN = response.json().get('value')
        logging.info(f"取得的長期存取權杖: {LONG_LIVED_USER_ACCESS_TOKEN}")
    except Exception as e:
        logging.error(f"從 Render 獲取資料時發生錯誤: {e}")
        return "Error getting Render data", 500

    try:
        # Facebook Graph API 端點
        fb_url = 'https://graph.facebook.com/v22.0/oauth/access_token'
        fb_params = {
            'grant_type': 'fb_exchange_token',
            'client_id': APP_ID,
            'client_secret': APP_SECRET,
            'fb_exchange_token': LONG_LIVED_USER_ACCESS_TOKEN
        }

        # 取得新的存取權杖
        fb_response = requests.get(fb_url, params=fb_params)
        fb_response.raise_for_status()
        new_access_token = fb_response.json().get('access_token')
        logging.info(f"取得新的存取權杖: {new_access_token}")

        # 更新 Render 的環境變數
        render_url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/env-vars/FACEBOOK_ACCESS_TOKEN"
        headers.update({"Content-Type": "application/json"})
        payload = {"value": new_access_token}
        update_response = requests.put(render_url, json=payload, headers=headers)
        update_response.raise_for_status()
        logging.info("新的存取權杖已成功更新到 Render 環境變數。")
        
    except Exception as e:
        logging.error(f"刷新存取權杖時發生錯誤: {e}")
        return "Error refreshing token", 500
    try:
        deploy_url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys"
        payload = {
        "clearCache": "do_not_clear"
        }   
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {RENDER_API_KEY}"
        }
        response = requests.post(deploy_url, json=payload, headers=headers)
        return "Token refreshed successfully", 200
    except Exception as e:
        logging.error(f"部署時發生錯誤: {e}")
        return "Error deploying", 500