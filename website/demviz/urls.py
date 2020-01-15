from django.urls import path

from . import views

urlpatterns = [
    path('', views.CoreIndex.as_view(), name='index'),
    path('search/<str:cls>', views.QueryResult.as_view(), name='qres')
]
