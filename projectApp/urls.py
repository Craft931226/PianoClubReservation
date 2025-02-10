from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # 空路徑對應登入頁面
    path('login/', views.login_view, name='login'),  # 可選，提供 /login/ 進入
    path('home/', views.home_view, name='home'),
    path('change_password/', views.change_password_view, name='change_password'),  # 新增更改密碼頁面
    path('Profile/', views.Profile_view, name='Profile'),  # 新增個人資料頁面
    path('get-calendar-events/', views.get_calendar_events_view, name='get_calendar_events'),  # 新增獲取日曆事件的視圖
    path('create-calendar-event/', views.create_calendar_event_view, name='create_calendar_event'), # 新增創建日曆事件的視圖
    path('cancel-calendar-event-by-time/', views.cancel_calendar_event_by_time, name='cancel_calendar_event_by_time'), # 新增取消日曆事件的視圖
]