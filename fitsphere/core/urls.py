from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('workout-planner/', views.workout_planner, name='workout_planner'),
    path('diet-planner/', views.diet_planner, name='diet_planner'),
    path('fitness-tracker/', views.fitness_tracker, name='fitness_tracker'),
    path('bmi-tracker/', views.bmi_tracker, name='bmi_tracker'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/message/', views.chatbot_message, name='chatbot_message'),
    path('chatbot/clear/', views.chatbot_clear, name='chatbot_clear'),
    path('logout/', views.logout_view, name='logout'),
    path("terms/", views.terms_view, name="terms"),
    path("privacy/", views.privacy_view, name="privacy"),
]