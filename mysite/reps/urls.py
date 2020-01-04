from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<str:name>/', views.view, name='view'),
    path('<str:name>/data/count/<str:data>/', views.count_data, name='data')
]
