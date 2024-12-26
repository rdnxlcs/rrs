class RoomAvailability:
    def __init__(self, availability, message, field):
        self.availability = availability
        self.message = message
        self.field = field

import datetime
from .models import Booking
from django.db import transaction
import calendar
import json
import pprint

def is_room_available(user, room, booking, bookings): # Готово
    print('is_room_available', booking.start_time)
    if not is_within_working_hours(room, booking.start_time, booking.end_time):
        return RoomAvailability(False, f"Комната {room.name} доступна с {room.open_time.strftime('%H:%M')} до {room.close_time.strftime('%H:%M')}", 'start_time')
    if not can_user_book_more(user, bookings):
        return RoomAvailability(False, f"Пользователь {user.name} достиг лимита на бронирования", 'start_time')
    for b in bookings.filter(room=room):
        if (booking.start_time < b.end_time and booking.end_time > b.start_time):
            return RoomAvailability(False, f"Помещение '{room.name}' занято на {booking.start_time.strftime('%-d %B %Y %H:%M')}", 'start_time')
        elif (booking.start_time < b.end_time + room.timebreak and booking.end_time > b.start_time - room.timebreak):
            return RoomAvailability(False, f"Между бронированиями команты '{room.name}' необходим перерыв")
    return RoomAvailability(True, f"Бронирование комнаты '{room.name}' создано на {booking.start_time.strftime('%-d %B %Y %H:%M')}", '')

def create_booking(user, room, booking, recurrence_type, interval, repeats, selected_days, bookings):
    if recurrence_type != 'no' and (repeats == 0 or interval == 0):
        created_bookings = []
        if repeats == 0:
            created_bookings.append(RoomAvailability(False, 'Количество повторений должно быть больше 0', 'repeats'))
        if interval == 0:
            created_bookings.append(RoomAvailability(False, 'Интервал должен быть больше 0', 'interval'))
        return created_bookings

    if recurrence_type == 'no':
        created_bookings = [create_single_booking(user, room, booking, bookings)]
    elif recurrence_type == 'bydays':
        created_bookings = create_daily_recurrence_bookings(user, room, booking, interval, repeats, bookings)
    elif recurrence_type == 'byweeks':
        created_bookings = create_weekly_recurrence_bookings(user, room, booking, interval, repeats, selected_days, bookings) 
    elif recurrence_type == 'bymonths':
        created_bookings = create_monthly_recurrence_bookings(user, room, booking, interval, repeats, selected_days, bookings)
    return created_bookings

def create_single_booking(user, room, booking, bookings): # Готово
    room_availabilityis = is_room_available(user, room, booking, bookings)
    if room_availabilityis.availability:
        booking.pk = None
        booking.save()
    print(room_availabilityis.availability, room_availabilityis.message)
    return room_availabilityis

def can_user_book_more(user, bookings): # Готово
    return len(bookings.filter(user=user)) < user.max_bookings

def create_daily_recurrence_bookings(user, room, booking, interval, repeats, bookings):

    created_bookings = []
    with transaction.atomic():
        for repeat in range(int(repeats)):

            created_booking = create_single_booking(user, room, booking, bookings)

            created_bookings.append(created_booking)

            booking.start_time += datetime.timedelta(days=interval)
            booking.end_time += datetime.timedelta(days=interval)

    return created_bookings

def create_weekly_recurrence_bookings(user, room, booking, interval, repeats, selected_days, bookings):
    weekdays = [day - 1 for day in selected_days] # Массив с днями недели, например, [0, 2, 4] (понедельник, среда, пятница)
    created_bookings = []
    start = booking.start_time
    end = booking.end_time

    with transaction.atomic():
        # Заполняем оставшуюся неделю
        for day in weekdays:
            day_offset = day - start.weekday()
            if day_offset >= 0:
                booking.start_time = start + datetime.timedelta(days=day_offset)
                booking.end_time = end + datetime.timedelta(days=day_offset)

                created_booking = create_single_booking(user, room, booking, bookings)
                created_bookings.append(created_booking)

        start += datetime.timedelta(weeks=interval-1)
        end += datetime.timedelta(weeks=interval-1)

        # Основной цикл для создания серий бронирований
        for repeat in range(int(repeats) - 1):
            # Вычисляем смещение по неделям для текущей серии
            week_offset = repeat * interval
            
            # Итерируемся по дням недели, когда должно быть событие
            for day in weekdays:

                day_offset = 7 - (start.weekday() - day)
                

                booking.start_time = start + datetime.timedelta(weeks=week_offset, days=day_offset)
                booking.end_time = end + datetime.timedelta(weeks=week_offset, days=day_offset)

                created_booking = create_single_booking(user, room, booking, bookings)
                created_bookings.append(created_booking)

    return created_bookings

def create_monthly_recurrence_bookings(user, room, booking, interval, repeats, selected_days, bookings):
    created_bookings = []
    start = booking.start_time
    end = booking.end_time

    with transaction.atomic():
        # Основной цикл для создания серий бронирований
        for repeat in range(int(repeats)):
            # Вычисляем смещение по месяцам для текущей серии
            month_offset = repeat * interval

            # Итерируемся по дням месяца, когда должно быть событие
            for day in selected_days:
                
                if booking.start_time >= start:
                    created_booking = create_single_booking(user, room, booking, bookings)
                    created_bookings.append(created_booking)

                # Вычисляем текущий месяц и год
                current_month = (start.month - 1 + month_offset) % 12 + 1
                current_year = start.year + (start.month - 1 + month_offset) // 12

                # Проверяем, сколько дней в текущем месяце
                _, days_in_month = calendar.monthrange(current_year, current_month)
                
                # Если выбранный день больше количества дней в месяце, пропускаем этот день
                if day > days_in_month:
                    continue

                # Вычисляем дату для каждого дня месяца в этой серии
                try:
                    booking.start_time = start.replace(year=current_year, month=current_month, day=day)
                    booking.end_time = end.replace(year=current_year, month=current_month, day=day)
                except ValueError:
                    # Если дата недопустима (например, 31 февраля), пропускаем этот день
                    continue

    return created_bookings

def is_within_working_hours(room, start_time, end_time):
    return room.open_time <= start_time.time() and room.close_time >= end_time.time()

def delete_booking(user, room, start_time, bookings):
    # Ищем бронирование для удаления
    booking_to_delete = None
    for booking in bookings:
        if booking.room == room and booking.start_time == start_time and booking in user.bookings:
            booking_to_delete = booking
            break

    # Если бронирование найдено, удаляем его
    if booking_to_delete:
        bookings.remove(booking_to_delete)
        user.bookings.remove(booking_to_delete)
        print(f"Бронирование комнаты {room.name} для пользователя {user.name} на {start_time} удалено.")
    else:
        print(f"Бронирование для комнаты {room.name} на {start_time} не найдено.")

def change_booking(booking, pk, tag):
    if change_form.is_valid():
        change_all = change_form.cleaned_data['change_all']
        if change_all:
          current_booking = Booking.objects.get(pk=change_form.cleaned_data['pk'])
          bookings = Booking.objects.filter(tag=change_form.cleaned_data['tag'])
          for booking in bookings:
            if booking.start_time >= current_booking.start_time: 
              booking.start_time = change_form.cleaned_data['start_time']
              booking.end_time = change_form.cleaned_data['end_time']
              booking.comment = change_form.cleaned_data['comment']
              booking.save()
              
        else:
          booking = Booking.objects.get(pk=change_form.cleaned_data['pk'])
          booking.start_time = change_form.cleaned_data['start_time']
          booking.end_time = change_form.cleaned_data['end_time']
          booking.comment = change_form.cleaned_data['comment']
          booking.save()