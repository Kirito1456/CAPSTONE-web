from django.urls import path
from hmis import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create, name='create'),
    path('reset/', views.reset , name='reset'),
    path('forgotpass/', views.forgotpass, name='forgotpass'),
]