from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # 空路徑對應登入頁面
    path('login/', views.login_view, name='login'),  # 可選，提供 /login/ 進入
    path('home/', views.home_view, name='home'),
    path('change_password/', views.change_password_view, name='change_password'),  # 新增更改密碼頁面
    path('Profile/', views.Profile_view, name='Profile'),  # 新增個人資料頁面
    path('logout/', views.logout_view, name='logout'),  # 新增登出頁面
    path('get-calendar-events/', views.get_calendar_events_view, name='get_calendar_events'),  # 新增獲取日曆事件的視圖
    path('create-calendar-event/', views.create_calendar_event_view, name='create_calendar_event'), # 新增創建日曆事件的視圖
    path('cancel-calendar-event-by-time/', views.cancel_calendar_event_by_time, name='cancel_calendar_event_by_time'), # 新增取消日曆事件的視圖
    path('get-latest-post/', views.get_latest_post_view, name='get_latest_post'),  # 新增獲取最新貼文的視圖
    path('get-show-reserve-name/', views.get_show_reserve_name, name='get_show_reserve_name'),  # 新增獲取預約者名單的視圖
    path('get-room-type/', views.get_room_type, name='get_room_type'),  # 新增獲取預約時間的視圖
    path('get-system-name/', views.get_system_name, name='get_system_name'),  # 新增獲取預約上限的視圖
    path('get-time-range/', views.get_time_range, name='get_time_range'),  # 新增獲取時間範圍的視圖
    path('get-rules/', views.get_rules, name='get_rules'),  # 新增獲取規則的視圖
    path('cron/run_reset_reservation_weekly/', views.reset_reservation_view, name='run_reset_reservation_weekly'),  # 新增重置預約次數的視圖
    path('cron/run_refresh_fb_token/', views.refresh_fb_token, name='refresh_fb_token'),  # 新增刷新 Facebook 令牌的視圖
]