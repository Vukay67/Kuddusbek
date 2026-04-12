from django.urls import path
from core import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/rates/', views.rates_view),
    path('api/admin/check/', views.admin_check_view),
    path('api/admin/rates/', views.admin_rates_view),
    path('api/admin/save/', views.admin_save_view),
    path('api/comments/', views.api_comments),
    path('api/comments/add/', views.api_comment_add),
    path('api/comments/delete/', views.api_comment_delete),
    path('api/comments/pin/', views.api_comment_pin),
]