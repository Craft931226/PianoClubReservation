from django.http import HttpResponse
from django.shortcuts import render, redirect
from .google_sheets import read_data

# 試算表的範圍，包含用戶數據
GOOGLE_SHEET_RANGE = '表單回應 1!A2:B'  # 假設試算表有 Name 和 Student ID 列

def second_page(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')

        try:
            # 從 Google Sheets 獲取數據
            users = read_data(GOOGLE_SHEET_RANGE)
            if not users:
                error_message = "無法讀取用戶數據，請稍後再試。"
            else:
                # 驗證用戶是否存在
                user_found = False
                for user in users:
                    if len(user) >= 2 and user[0] == name and user[1] == student_id:
                        user_found = True
                        # 登錄成功，將用戶名作為 URL 參數
                        return redirect(f'/home/?username={name}')
                
                if not user_found:
                    error_message = "帳號或密碼錯誤，請重新輸入。"
        except Exception as e:
            error_message = f"系統錯誤：{e}"

    return render(request, 'Login.html', {'error_message': error_message})


def home_view(request):
    # 從 URL 獲取用戶名
    username = request.GET.get('username')
    if not username:
        return redirect('login')  # 如果沒有用戶名，重定向到登錄頁面

    return render(request, "homePage.html", {'username': username})

