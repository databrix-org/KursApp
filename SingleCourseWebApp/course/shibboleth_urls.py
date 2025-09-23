from django.urls import path
from .shibboleth_views import (
    ShibbolethLoginView,
    ShibbolethLogoutView,
    ShibbolethDebugView,
    ShibbolethRequestDebugView,
)

app_name = 'shibboleth'

urlpatterns = [
    path('login/', ShibbolethLoginView.as_view(), name='login'),
    path('logout/', ShibbolethLogoutView.as_view(), name='logout'),
    path('debug/', ShibbolethDebugView.as_view(), name='debug'),
    path('request-debug/', ShibbolethRequestDebugView.as_view(), name='request_debug'),
]