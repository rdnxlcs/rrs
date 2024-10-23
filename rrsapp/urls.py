from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'rrsapp'

urlpatterns = [
  path('', views.home, name='home'),
  path('rooms', views.rooms, name='rooms'),
  path('about', views.about, name='about'),
  path('personal', views.personal, name='personal'),
  path('booking/<int:room_id>/', views.booking, name='booking'),
  path('signin', views.signin, name='signin'),
  path('signup', views.signup, name='signup'),
  path('logout', LogoutView.as_view(), name='logout')
]