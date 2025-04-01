import json
import requests
import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from flask import jsonify



def read_data(range_name, service, spreadsheet_id):
    """從 Google 試算表中讀取數據"""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])
    except Exception as e:
        logging.error(f"❌ 讀取試算表時發生錯誤: {e}")
        return []

def update_data(range_name, values, service, spreadsheet_id):
    """更新 Google 試算表中的數據"""
    try:
        sheet = service.spreadsheets()
        body = {'values': values}
        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        logging.info(f"✅ {result.get('updatedCells')} 個儲存格已更新")
    except Exception as e:
        logging.error(f"❌ 更新試算表時發生錯誤: {e}")

def update_FB(request):
    logging.basicConfig(level=logging.INFO)

    try:
        # 設定 Google Sheets 相關資訊
        GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
        FBLLT_RANGE = os.getenv("FBLLT_RANGE")
        credentials_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        # 讀取當前試算表中的數據
        data = read_data(FBLLT_RANGE, service, GOOGLE_SHEET_ID)
        # print(data)
        if not data:
            return jsonify({"error": "❌ 無法讀取數據"}), 500

        # 向 Facebook API 取得新的 long-lived token
        fb_app_id = os.getenv("FB_APP_ID")
        fb_app_secret = os.getenv("FB_APP_SECRET")
        fb_old_token = data[0]

        url = "https://graph.facebook.com/v19.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": fb_app_id,
            "client_secret": fb_app_secret,
            "fb_exchange_token": fb_old_token,
        }
        response = requests.get(url, params=params)
        new_token = response.json().get("access_token")

        if not new_token:
            return jsonify({"error": "❌ 未能取得新的 Facebook token"}), 500

        # 更新試算表中的數據
        update_data(FBLLT_RANGE, [[new_token]], service, GOOGLE_SHEET_ID)
        logging.info("✅ Facebook token 已更新")
        return jsonify({"message": "✅ Facebook token 已成功更新"}), 200

    except Exception as e:
        logging.error(f"❌ 更新 Facebook token 時發生錯誤: {e}")
        return jsonify({"error": f"❌ 更新 Facebook token 時發生錯誤: {e}"}), 500
