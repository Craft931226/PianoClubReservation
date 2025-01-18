from django.core.management.base import BaseCommand
import pandas as pd
from projectApp.models import User

class Command(BaseCommand):
    help = '匯入 PianoClubMembers.xlsx 的資料到資料庫'

    def handle(self, *args, **kwargs):
        # 解決路徑問題
        file_path = r"C:\Users\User\Downloads\PianoClubMembers_NameID.xlsx"  # 選擇原始字串
        try:
            # 讀取 Excel 文件
            data = pd.read_excel(file_path)

            for _, row in data.iterrows():
                # 將每行資料插入資料庫
                User.objects.create(name=row['姓名'], student_id=row['學號'], weeklyTimeLimitHours=row['每週時數限制'])

            self.stdout.write(self.style.SUCCESS("資料匯入完成！"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"找不到文件：{file_path}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"發生錯誤：{str(e)}"))
