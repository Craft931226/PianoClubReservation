import json
import requests
import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google_sheets import read_data, update_data


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
        return "Error resetting reservation", 500
    return "Reservation reset successfully", 200

