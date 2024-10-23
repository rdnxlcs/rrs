from django.contrib.auth.models import AbstractUser
from django.db import models
import datetime

class User(AbstractUser):
  max_bookings = models.IntegerField(default=20)  # Максимальное количество бронирований

class Room(models.Model):
  name = models.CharField(max_length=100)
  timebreak = models.DurationField()  # Длительность перерыва между бронированиями
  open_time = models.TimeField(default=datetime.time(0, 0))  # Время открытия комнаты
  close_time = models.TimeField(default=datetime.time(23, 59))  # Время закрытия комнаты
  image = models.CharField(max_length=1000, default='')
  comment = models.CharField(max_length=1000, default='')

  def formatted_timebreak(self):
    total_seconds = int(self.timebreak.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}"  # Формат "часы:минуты"

class Booking(models.Model):
  user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='bookings')  # Связь с пользователем
  room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='bookings')
  start_time = models.DateTimeField()
  end_time = models.DateTimeField()
  tag = models.CharField(max_length=32)
  comment = models.CharField(max_length=1000)

