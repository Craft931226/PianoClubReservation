import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from email.mime.text import MIMEText
import base64
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# 憑證範圍
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    # 從環境變量讀取憑證
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_secret:
        raise Exception("環境變量 GOOGLE_CLIENT_SECRET 未設置")

    creds_data = json.loads(client_secret)

    # 在 Render 中，無法使用本地服務器授權，因此需要使用已授權的憑證
    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    # 創建 Gmail API 服務
    service = build("gmail", "v1", credentials=creds)
    return service

# def get_gmail_service():
#     """
#     初始化 Gmail API 服務。
#     如果 token.pickle 存在，則加載憑證；否則進行用戶驗證並保存憑證。
#     :return: Gmail API 服務對象
#     """
#     creds = None
#     # 檢查本地是否有保存的 token
#     if os.path.exists("token.pickle"):
#         with open("token.pickle", "rb") as token:
#             creds = pickle.load(token)

#     # 如果沒有可用的憑證，或憑證已失效，重新進行驗證
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 r"C:\Users\User\Downloads\client_secret_921569073879-o790mqkieupt27bg4902a6mji6hbcgi8.apps.googleusercontent.com.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)

#         # 保存憑證到本地
#         with open("token.pickle", "wb") as token:
#             pickle.dump(creds, token)

#     # 初始化 Gmail API 服務
#     service = build("gmail", "v1", credentials=creds)
#     return service

def send_email(name, time, room_type, recipient_email):
    """
    發送郵件通知
    :param name: 預約者姓名
    :param time: 預約時間 (格式: YYYY-MM-DD HH:MM)
    :param room_type: 預約房間類型
    :param recipient_email: 收件人電子郵件地址
    :return: 發送結果
    """
    try:
        # 構建郵件內容
        subject = "您的琴房預約通知 | Your Piano Room Reservation Confirmation"
        body = f"""
        親愛的 {name} 您好，

        您已成功預約琴房：
        - 預約時間：{time}
        - 琴房類型：{room_type}

        請準時使用琴房，並遵守相關規定。
        感謝您的使用！

        中央鋼琴社 敬上

        Dear {name},

        You have successfully reserved a piano room:
        - Reservation Time: {time}
        - Room Type: {room_type}

        Please make sure to use the piano room on time and follow the relevant rules.
        Thank you for using our service!

        Best regards,
        NCU Piano Club
        """
        message = MIMEText(body)
        message["to"] = recipient_email
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw}

        # 發送郵件
        try:
            service = get_gmail_service()
            print("Gmail API 初始化成功！")
        except Exception as e:
            print("Gmail API 初始化失敗：", e)
        messages = service.users().messages()
        message = messages.send(userId="me", body=body).execute()
        print("郵件已成功發送，ID：", message["id"])
        return message
    except HttpError as error:
        print("郵件發送失敗: %s" % error)
        return None

# 測試發送郵件
send_email(
    name="周訓練",
    time="2025-01-26 10:00",
    room_type="大琴房",
    recipient_email="yanchaun0970@gmail.com"
)
