from django.shortcuts import render, redirect, get_object_or_404

from .forms import UserSignUpForm, UserSignInForm, BookingForm
from .models import Room, Booking
from .mvp import *

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

import json
import openai
'''
new_room = Room(name="Гей качалка", timebreak=datetime.timedelta(minutes=0), open_time=datetime.time(0, 0), close_time=datetime.time(23, 59))
new_room.save()
'''
def home(request):
  return render(request, 'home.html', {'rooms': Room.objects.all()})

def rooms(request):
  return render(request, 'rooms.html', {'rooms': Room.objects.all()})

def about(request):
  return render(request, 'about.html')

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

  bookings = Booking.objects.filter(user=user)

  events = []
  for booking in bookings:
      events.append({
          'title': booking.room.name,  # Название события
          'start': booking.start_time.strftime("%Y-%m-%dT%H:%M:%S"),  # Начало события
          'end': booking.end_time.strftime("%Y-%m-%dT%H:%M:%S"),  # Конец события
          'description': booking.comment,  # Дополнительная информация
      })

  context = {
    'user': user,
    'bookings': bookings,
    'events': json.dumps(events),
  }
  return render(request, 'personal.html', context)

def booking(request, room_id):
  room = Room.objects.get(id=room_id) # брать из строки
  created_bookings = [RoomAvailability(False, '', '')]

  if request.method == 'POST':
    form = BookingForm(request.POST)
    if form.is_valid():
      user = request.user
      room = Room.objects.get(id=room_id)

      start_time = form.cleaned_data['start_time']
      end_time = form.cleaned_data['end_time']
      comment = form.cleaned_data['comment']

      recurrence_type = form.cleaned_data['recurrence_type']
      interval = form.cleaned_data['interval'] if form.cleaned_data['interval'] != None else 0
      repeats = form.cleaned_data['repeats'] if form.cleaned_data['repeats'] != None else 0
      selected_days = json.loads(form.cleaned_data['selected_days']) if form.cleaned_data['selected_days'] else []

      tag = f'{request.user.id:04} - {room.id:04} - {start_time:%Y%m%d%H%M} - {end_time:%Y%m%d%H%M}'

      booking = Booking(user=user, room=room, start_time=start_time, end_time=end_time, comment=comment, tag=tag)
      bookings = Booking.objects

      created_bookings = create_booking(user, room, booking, recurrence_type, interval, repeats, selected_days, bookings)

      print(created_bookings, repeats)

      if any([booking.availability for booking in created_bookings]):
        return redirect('/personal') # Перенаправляем на страницу успеха
  else:
    form = BookingForm()

  context = {
    'form': form,
    'jsonerrors': json.dumps(form.errors),
    'errors': form.errors.as_data(), # Логическая валидация
    'jsonbookings': json.dumps({  
      'strat_time': [booking.message for booking in created_bookings if booking.field == 'strat_time'],
      'repeats': [booking.message for booking in created_bookings if booking.field == 'repeats'],
      'interval': [booking.message for booking in created_bookings if booking.field == 'interval'],
    }), # Фактическая валидация
    'bookings': {  
      'strat_time': [booking.message for booking in created_bookings if booking.field == 'strat_time'],
      'repeats': [booking.message for booking in created_bookings if booking.field == 'repeats'],
      'interval': [booking.message for booking in created_bookings if booking.field == 'interval'],
    }, # Фактическая валидация
    'room': room,
    'days': [i for i in range(1, 32)],
    'week_days': ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'],
  }
  return render(request, 'booking.html', context)

