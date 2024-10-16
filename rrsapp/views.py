from django.shortcuts import render, redirect, get_object_or_404

from .forms import UserSignUpForm, UserSignInForm, BookingForm
from .models import Room
from .mvp import *

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

import json
'''
new_room = Room(name="Порно студия", timebreak=datetime.timedelta(minutes=30), open_time=datetime.time(0, 0), close_time=datetime.time(6, 00))
new_room.save()
'''
def home(request):
  return render(request, 'home.html')

def signup(request):
  if request.method == 'POST':
    form = UserSignUpForm(request.POST)
    print('Данные получены', request.POST)
    if form.is_valid():
      print(form)
      form.save()
      return redirect('/signin')
    else:
      print('Не удалось зарегистрироваться')
  else:
    form = UserSignUpForm()

  context = {
    'form': form,
    'jsonerrors': json.dumps(form.errors),
    'errors': form.errors.as_data()
  }

  return render(request, 'signup.html', context)

def signin(request):
  if request.method == 'POST':
    form = UserSignInForm(request.POST)
    if form.is_valid():
      username = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')
      user = authenticate(request, username=username, password=password)
      if user is not None:
        login(request, user)
        messages.success(request, f"Добро пожаловать, {username}!")
        return redirect('/personal')
      else:
        messages.error(request, "Неверное имя пользователя или пароль")
    else:
      messages.error(request, "Некорректные данные")
  else:
    form = UserSignInForm()

  return render(request, 'signin.html', {'form': form})
    
def personal(request):
  user = request.user
  return render(request, 'personal.html', {'user': user})

def booking(request, room_id):
  room = Room.objects.get(id=room_id) # брать из строки
  booking = RoomAvailability(False, '')
   
  if request.method == 'POST':
    form = BookingForm(request.POST)
    if form.is_valid():
      print(form.cleaned_data['recurrence_type'])
      bookings = Booking.objects
      booking = create_booking(request.user, room, form, bookings)
      if booking.availability:
        return redirect('/personal') # Перенаправляем на страницу успеха
  else:
    form = BookingForm()

  context = {
    'form': form,
    'jsonerrors': json.dumps(form.errors),
    'errors': form.errors.as_data(), # Логическая валидация
    'booking': booking, # Фактическая валидация
    'room': room,
    'days': [i for i in range(1, 32)],
    'week_days': ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'],
  }
  return render(request, 'booking.html', context)

