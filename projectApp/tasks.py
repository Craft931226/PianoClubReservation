import json
from django.http import HttpResponse
import requests
import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from .google_sheets import read_data, update_data


def reset_reservation_weekly(request):
    logging.basicConfig(level=logging.INFO)

    RESERVATION_LIMIT_RANGE = os.getenv("RESERVATION_LIMIT_RANGE")
    STATUS_RANGE = os.getenv("STATUS_RANGE")
    try:
        
        # 讀取當前試算表中的數據
        status_data = read_data(STATUS_RANGE)
        reserve_limit =0
        for row in status_data:
            if len(row) > 0:
                if row[0] == 'WeeklyReservationLimit':
                    reserve_limit = int(row[1])
                    logging.info(f"reserve_limit: {reserve_limit}")
        data = read_data(RESERVATION_LIMIT_RANGE)
        if not data:
            print("無法讀取預約上限數據")
            return

        # 構建新的數據，將 B 欄設置為 0，C~P 欄設置為 "-"
        reset_values = []
        for row in data:
            if len(row) > 0:
                reset_row = [row[0], 0] + ["-"] * reserve_limit + [""] * 10  # C~P 欄總共 14 欄
                reset_values.append(reset_row)

        update_data(RESERVATION_LIMIT_RANGE, reset_values)
        logging.info("✅ 預約次數與預約紀錄已重置")


    except Exception as e:
        logging.error(f"❌ 重置預約次數時發生錯誤: {e}")
        return HttpResponse("Error resetting reservation", status=500)
    return HttpResponse("Reservation reset successfully", status=200)

def update_FB(request):
    logging.basicConfig(level=logging.INFO)

    try:
        # 設定 Google Sheets 相關資訊
        FBLLT_RANGE = os.getenv("FBLLT_RANGE")

        # 讀取當前試算表中的數據
        data = read_data(FBLLT_RANGE)
        # print(data)
        if not data:
            return HttpResponse("❌ 無法讀取 Facebook token", status=500)

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
            return HttpResponse("❌ 無法獲取新的 Facebook token", status=500)

        # 更新試算表中的數據
        update_data(FBLLT_RANGE, [[new_token]])
        logging.info("✅ Facebook token 已更新")
        return HttpResponse("Facebook token updated successfully", status=200)

    except Exception as e:
        logging.error(f"❌ 更新 Facebook token 時發生錯誤: {e}")
        return HttpResponse("Error updating Facebook token", status=500)