from datetime import date
from http import client
import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 配置 Google Sheets API 憑證
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# 從環境變數中加載憑證
# credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
# credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')  # 修改為實際試算表的 ID
# service = build('sheets', 'v4', credentials=credentials)
_service = None 
# # 配置 Google Sheets API 憑證(本地端)
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# SERVICE_ACCOUNT_FILE = r"C:\Users\yanch\Downloads\skilled-script-448314-j0-99fdb0f4b352.json"
# credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# service = build('sheets', 'v4', credentials=credentials)


# update_user_name 函數將用戶名更新到試算表中
# Define the sheet names and ranges
FORM_RESPONSES_SHEET = '社員資料'
RESERVATION_LIMIT_SHEET = '預約上限'
SYSTEM_STATE_SHEET = '系統狀態'
FORM_RESPONSES_RANGE = f'{FORM_RESPONSES_SHEET}!A1:B'  # 假設第一列為名稱，第二列為學號
RESERVATION_LIMIT_RANGE = f'{RESERVATION_LIMIT_SHEET}!A1:P'  

def _get_service():
    global _service
    if _service is None:
        creds_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        _service = build("sheets", "v4", credentials=creds)
    return _service
# 讀取數據
def read_data(range_name):
    """從 Google 試算表中讀取數據"""
    try:
        sheet = _get_service().spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Error reading data: {e}")
        return []

def update_data(range_name, values):
    """更新 Google 試算表中的數據"""
    try:
        sheet = _get_service().spreadsheets()
        body = {'values': values}
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        # print(f"{result.get('updatedCells')} cells updated.")
    except Exception as e:
        print(f"Error updating data: {e}")

def get_user_email(user_name):
    """
    根據使用者名稱從試算表中獲取信箱地址。
    :param user_name: 使用者名稱
    :return: 信箱地址 (如果找到)
    """
    try:
        # 讀取社員資料表的所有數據
        sheet_data = read_data(f'{FORM_RESPONSES_SHEET}!A1:D')  # 假設信箱在第四列
        for row in sheet_data:
            if len(row) >= 4 and row[0] == user_name:  # 確保行數據足夠長並匹配使用者名稱
                return row[3]  # 返回第四列（信箱）
        return None  # 如果未找到對應使用者
    except Exception as e:
        print(f"Error retrieving email for user {user_name}: {e}")
        return None

# def reset_reservation_limits():
#     """
#     將預約上限試算表中的 B 欄（預約次數）全部重置為 0。
#     將 C 欄至 P 欄（預約紀錄）重置為 "-"。
#     僅當本週未執行過重置操作時執行。
#     """
#     try:
#         # 檢查是否已經執行過重置
#         status_range = '系統狀態!A1:B1'
#         status_data = read_data(status_range)
#         last_reset_date = status_data[0][1] if len(status_data) > 0 and len(status_data[0]) > 1 else None

#         today = date.today()
#         if last_reset_date == today.isoformat():
#             print("今天已經執行過重置操作，跳過重置")
#             return

#         # 讀取當前試算表中的數據
#         data = read_data(RESERVATION_LIMIT_RANGE)
#         if not data:
#             print("無法讀取預約上限數據")
#             return

#         # 構建新的數據，將 B 欄設置為 0，C~P 欄設置為 "-"
#         reset_values = []
#         for row in data:
#             if len(row) > 0:
#                 reset_row = [row[0], 0] + ["-"] * 14  # C~P 欄總共 14 欄
#                 reset_values.append(reset_row)

#         update_data(RESERVATION_LIMIT_RANGE, reset_values)
#         print("✅ 預約次數與預約紀錄已重置")

#         # 更新重置日期
#         update_data(status_range, [["last_reset_date", today.isoformat()]])
#         print("✅ 重置標記已更新")

#     except Exception as e:
#         print(f"❌ 重置預約次數時發生錯誤: {e}")


def create_reservation_log(user_name, event_details):
    """
    在 '預約上限' 試算表中的該使用者的第三欄開始寫入預約事件
    若第三欄已有預約，則填入下一個可用欄位（最多到第16欄）

    :param user_name: 使用者名稱
    :param event_details: 預約事件詳情 (例如 "2025-01-30 10:00 - 大琴房")
    """
    try:
        reservation_data = read_data(RESERVATION_LIMIT_RANGE)

        for index, row in enumerate(reservation_data):
            # print(f"row: {row}")
            if len(row) >= 2 and row[0] == user_name:
                # 找到使用者所在行
                user_row_index = index + 1  # Google Sheets 的行索引是從 1 開始的

                # 計算下一個可寫入的欄位（C 到 P，因為第三欄是 C，16 欄是 P）
                max_columns = 16  # A, B 是使用者名稱與次數，C~P 是預約紀錄
                start_column = 3   # 第三欄 (C)
                next_available_col = None

                # 找到第一個空白欄位
                for col in range(start_column, max_columns + 1):
                    # print(f"row: {row}, col: {col}, len(row): {len(row)}")
                    if row[col - 1] == "-":
                        next_available_col = col
                        break

                # 若已達到第16欄，則不再新增
                if next_available_col is None:
                    print(f"⚠️ 使用者 {user_name} 預約已達 14 次上限，無法再新增事件。")
                    return False

                # 轉換為 Google Sheets 的欄位字母（C ~ P）
                column_letter = chr(65 + next_available_col - 1)
                range_to_update = f'預約上限!{column_letter}{user_row_index}'

                # 更新該欄位為新的預約事件
                update_data(range_to_update, [[event_details]])
                print(f"✅ 已將事件 '{event_details}' 記錄到 {range_to_update}")
                return True

        print(f"⚠️ 未找到使用者 {user_name}，無法記錄預約事件。")
        return False

    except Exception as e:
        print(f"❌ 更新預約紀錄時發生錯誤: {e}")
        return False

def cancel_reservation_log(user_name, event_name):
    """
    取消使用者的預約事件
    :param user_name: 使用者名稱
    :param event_name: 要取消的預約事件名稱
    """
    try:
        reservation_data = read_data(RESERVATION_LIMIT_RANGE)

        for index, row in enumerate(reservation_data):
            if len(row) >= 2 and row[0] == user_name:
                # 找到使用者所在行
                user_row_index = index + 1  # Google Sheets 的行索引是從 1 開始的

                # 找到要取消的預約事件
                for col in range(3, 16 + 1):
                    if row[col - 1] == event_name:
                        # 轉換為 Google Sheets 的欄位字母（C ~ P）
                        column_letter = chr(65 + col - 1)
                        range_to_update = f'預約上限!{column_letter}{user_row_index}'

                        # 更新該欄位為 "-"
                        update_data(range_to_update, [["-"]])
                        print(f"✅ 已取消事件 '{event_name}'")
                        return True

                print(f"⚠️ 未找到事件 '{event_name}'，無法取消。")
                return False

        print(f"⚠️ 未找到使用者 {user_name}，無法取消預約事件。")
        return False

    except Exception as e:
        print(f"❌ 取消預約紀錄時發生錯誤: {e}")
        return False

def GetRoomEmail():
    try:
        data = read_data(SYSTEM_STATE_SHEET)
        if not data:
            print("無法讀取系統狀態數據")
            return
        NumbersOfrooms = 0
        for row in data:
            if len(row) > 0:
                if row[0] == 'NumbersOfrooms':
                    NumbersOfrooms = int(row[1])
                    break

        RoomName = []
        gmail = []
        for row in data:
            if len(row) > 0:
                if row[0] == 'RoomGmail':
                    for i in range(1,NumbersOfrooms+1):
                        gmail.append(row[i])
                if row[0] == 'RoomName':
                    for i in range(1,NumbersOfrooms+1):
                        RoomName.append(row[i])
        RoomGmail = dict(zip(RoomName, gmail))
        return RoomGmail
    except Exception as e:
        print(f"Error retrieving email: {e}")
        return None

