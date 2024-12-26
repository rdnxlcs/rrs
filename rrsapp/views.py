from django.shortcuts import render, redirect, get_object_or_404

from .forms import UserSignUpForm, UserSignInForm, BookingForm, DeleteBookingForm, ChangeBookingForm, CreateRoomForm
from .models import Room, Booking
from .mvp import *

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

import json
import os
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
  enter = ''
  if request.method == 'POST':
    form = UserSignInForm(request.POST)
    if form.is_valid():
      username = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')
      user = authenticate(request, username=username, password=password)
      if user is not None:
        login(request, user)
        return redirect('/personal')
      else:
        enter = "Неверное имя пользователя или пароль"
        print(enter)
    else:
      enter = "Некорректные данные"
      print(enter)
  else:
    form = UserSignInForm()

  context = {
    'form': form,
    'jsonerrors': json.dumps(form.errors),
    'errors': form.errors.as_data(),
    'enter': enter
  }

  return render(request, 'signin.html', context)

@login_required
def personal(request):
  user = request.user

  bookings = Booking.objects.filter(user=user)

  form = DeleteBookingForm()

  change_form = ChangeBookingForm()

  if request.method == 'POST':
    form = DeleteBookingForm(request.POST)
    change_form = ChangeBookingForm(request.POST)
    print(change_form.errors.as_data())

    if 'delete' in request.POST:
      print('delete')
      if form.is_valid():
        delete_all = form.cleaned_data['delete_all']
        if delete_all:
          current_booking = Booking.objects.get(pk=form.cleaned_data['pk'])
          bookings = Booking.objects.filter(tag=form.cleaned_data['tag'])
          for booking in bookings:
            if booking.start_time >= current_booking.start_time: 
              print(booking, 'delete_all')
              booking.delete()
        else:
          booking = Booking.objects.get(pk=form.cleaned_data['pk'])
          print(booking, delete_all)
          booking.delete()
        return redirect('/personal')
    
    if 'change' in request.POST:
      print('change')
      if change_form.is_valid():
        change_all = change_form.cleaned_data['change_all']

        booking = Booking.objects.get(pk=change_form.cleaned_data['pk'])
        booking.start_time = change_form.cleaned_data['start_time']
        booking.end_time = change_form.cleaned_data['end_time']
        booking.comment = change_form.cleaned_data['comment']
        booking.save()
        return redirect('/personal')
      


  events = []
  for booking in bookings:
    events.append({
      'title': booking.room.name,  # Название события
      'start': booking.start_time.strftime("%Y-%m-%dT%H:%M:%S"),  # Начало события
      'end': booking.end_time.strftime("%Y-%m-%dT%H:%M:%S"),  # Конец события
      'comment': booking.comment,  # Дополнительная информация
      'pk': booking.pk,
      'tag': booking.tag,
    })

  context = {
    'user': user,
    'bookings': bookings,
    'events': json.dumps(events),
    'form': form,
    'change_form': change_form,
  }
  return render(request, 'personal.html', context)

@login_required
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

      if any([booking.availability for booking in created_bookings]):
        return redirect('/personal') # Перенаправляем на страницу успеха
  else:
    form = BookingForm()

  context = {
    'form': form,
    'jsonerrors': json.dumps(form.errors),
    'errors': form.errors.as_data(), # Логическая валидация
    'jsonbookings': json.dumps({  
      'start_time': list(set([booking.message for booking in created_bookings if booking.field == 'start_time'])),
      'repeats': list(set([booking.message for booking in created_bookings if booking.field == 'repeats'])),
      'interval': list(set([booking.message for booking in created_bookings if booking.field == 'interval'])),
    }), # Фактическая валидация
    'bookings': {  
      'start_time': list(set([booking.message for booking in created_bookings if booking.field == 'start_time'])),
      'repeats': list(set([booking.message for booking in created_bookings if booking.field == 'repeats'])),
      'interval': list(set([booking.message for booking in created_bookings if booking.field == 'interval'])),
    }, # Фактическая валидация
    'room': room,
    'days': [i for i in range(1, 32)],
    'week_days': ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'],
  }
  return render(request, 'booking.html', context)

def newroom(request):
  form = CreateRoomForm()

  if request.method == 'POST':
    form = CreateRoomForm(request.POST, request.FILES)
    if form.is_valid():
      image_file = request.FILES['image']
      dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

      os.makedirs(dir, exist_ok=True)

      file_path = os.path.join(dir, image_file.name)

      with open(file_path, 'wb') as f:
        for chunk in image_file.chunks():
            f.write(chunk)

      name = form.cleaned_data['name']
      timebreak = form.cleaned_data['timebreak']
      open_time = form.cleaned_data['open_time']
      close_time = form.cleaned_data['close_time']
      image = 'static/uploads/' + str(form.cleaned_data['image'])
      comment = form.cleaned_data['comment']

      room = Room(name=name, timebreak=timebreak, open_time=open_time, close_time=close_time, image=image, comment=comment)

      room.pk = None
      room.save()
 
      return redirect('/rooms') #admpersonal
  else:
    form = CreateRoomForm()
  print(form.errors.as_data())
  context = {
    'form': form,
    'jsonerrors': json.dumps(form.errors),
    'errors': form.errors.as_data(), # Логическая валидация
  }

  return render(request, 'newroom.html', context)

def pptx(request):
  return render(request, 'pptx.html')
