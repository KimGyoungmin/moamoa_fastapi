from django.urls import path
from . import views

urlpatterns = [
    # 월말 결산
    path('monthly/<int:child_id>/', views.MonthlySummaryView.as_view(), name='monthly-summary'),
    # 아이들만 사용할수 있는 챗봇
    path('chat/', views.ChatbotProcessView.as_view()),
    # 아이 채팅 기록
    path('chat/messages/<int:child_pk>/', views.ChatMessageHistory.as_view()),
    # 기입장 특정 삭제
    path('chat/<int:pk>/delete/', views.ChatbotProcessDelete.as_view()),
    # 월별 용돈 기입장 리스트
    path('<int:child_pk>/<int:year>/<int:month>/', views.MonthlyDiaryView.as_view()),
    # 키즈 프로필 콤보박스 사용 가능한 월을 가져오는 URL
    path('<int:child_pk>/available-months/', views.AvailableMonthsView.as_view(), name='available-months'),
]
