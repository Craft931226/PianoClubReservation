import json
import requests
import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 讀取數據
def read_data(range_name, service, SPREADSHEET_ID):
    """從 Google 試算表中讀取數據"""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Error reading data: {e}")
        return []

def update_data(range_name, values, service, SPREADSHEET_ID):
    """更新 Google 試算表中的數據"""

    try:
        sheet = service.spreadsheets()
        body = {'values': values}
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"{result.get('updatedCells')} cells updated.")
    except Exception as e:
        print(f"Error updating data: {e}")

def reset_reservation_weekly(request):
    logging.basicConfig(level=logging.INFO)

    # 設定 Google Sheets 相關資訊
    GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
    RESERVATION_LIMIT_RANGE = os.getenv("RESERVATION_LIMIT_RANGE")
    STATUS_RANGE = os.getenv("STATUS_RANGE")
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    

    try:
        
        # 讀取當前試算表中的數據
        status_data = read_data(STATUS_RANGE, service, GOOGLE_SHEET_ID)
        reserve_limit =0
        for row in status_data:
            if len(row) > 0:
                if row[0] == 'WeeklyReservationLimit':
                    reserve_limit = int(row[1])
                    logging.info(f"reserve_limit: {reserve_limit}")
        data = read_data(RESERVATION_LIMIT_RANGE, service, GOOGLE_SHEET_ID)
        if not data:
            print("無法讀取預約上限數據")
            return

        # 構建新的數據，將 B 欄設置為 0，C~P 欄設置為 "-"
        reset_values = []
        for row in data:
            if len(row) > 0:
                reset_row = [row[0], 0] + ["-"] * reserve_limit + [""] * 10  # C~P 欄總共 14 欄
                reset_values.append(reset_row)

        update_data(RESERVATION_LIMIT_RANGE, reset_values, service, GOOGLE_SHEET_ID)
        logging.info("✅ 預約次數與預約紀錄已重置")


    except Exception as e:
        logging.error(f"❌ 重置預約次數時發生錯誤: {e}")
        return "Error resetting reservation", 500
    return "Reservation reset successfully", 200

