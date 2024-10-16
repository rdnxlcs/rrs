class RoomAvailability:
    def __init__(self, availability, message):
        self.availability = availability
        self.message = message

import datetime
from .models import Booking
from django.db import transaction
import calendar
import json
import pprint

def is_room_available(user, room, start_time, end_time, bookings): # Готово
    if not is_within_working_hours(room, start_time, end_time):
        return RoomAvailability(False, f"Комната {room.name} доступна с {room.open_time.strftime('%H:%M')} до {room.close_time.strftime('%H:%M')}")
    if not can_user_book_more(user, bookings):
        return RoomAvailability(False, f"Пользователь {user.name} достиг лимита на бронирования")
    for booking in bookings.filter(room=room):
        if (start_time < booking.end_time and end_time > booking.start_time):
            return RoomAvailability(False, f"Помещение '{room.name}' занято на {start_time.strftime('%-d %B %Y %H:%M')}")
        elif (start_time < booking.end_time + room.timebreak and end_time > booking.start_time - room.timebreak):
            return RoomAvailability(False, f"Между бронированиями команты '{room.name}' необходим перерыв")
    return RoomAvailability(True, f"Бронирование комнаты '{room.name}' создано на {start_time.strftime('%-d %B %Y %H:%M')}")

def create_booking(user, room, form, bookings):
    if form.cleaned_data['recurrence_type'] == 'no':
        create_single_booking(user, room, form, bookings)
        form.cleaned_data['start_time'] += datetime.timedelta(days=1)
        form.cleaned_data['end_time'] += datetime.timedelta(days=1)
        create_single_booking(user, room, form, bookings)
    elif form.cleaned_data['recurrence_type'] == 'bydays':
        create_daily_recurrence_bookings(user, room, form, bookings)
    elif form.cleaned_data['recurrence_type'] == 'byweeks':
        create_weekly_recurrence_bookings(user, room, form, bookings)
    elif form.cleaned_data['recurrence_type'] == 'bymonths':
        create_monthly_recurrence_bookings(user, room, form, bookings)
        


def create_single_booking(user, room, form, bookings): # Готово
    start_time = form.cleaned_data['start_time']
    end_time = form.cleaned_data['end_time']
    room_availabilityis = is_room_available(user, room, start_time, end_time, bookings)
    if room_availabilityis.availability:
        booking = form.save(commit=False) # Создаём объект бронирования, но не сохраняем его
        booking.start_time = start_time
        booking.end_time = end_time
        print(booking.start_time, booking.end_time)
        booking.user = user # Присваиваем пользователя из текущей сессии
        booking.room = room # Привязываем бронирование к выбранной комнате

        booking.save()
    print(room_availabilityis.availability, room_availabilityis.message)
    return room_availabilityis

def can_user_book_more(user, bookings): # Готово
    return len(bookings.filter(user=user)) < user.max_bookings


def create_daily_recurrence_bookings(user, room, form, bookings):
    """
    Функция для создания повторяющихся бронирований по дням.
    
    :param room: Room object (комната, которую бронируем)
    :param start_time: datetime, начало первого бронирования
    :param end_time: datetime, конец первого бронирования
    :param interval: int, количество дней между сериями повторений
    :param repeat_count: int, сколько раз бронирование повторяется подряд
    :param comment: str, комментарий к бронированию
    """
    # Список для всех бронирований
    start_time = form.cleaned_data['start_time']
    end_time = form.cleaned_data['end_time']
    repeats = form.cleaned_data['repeats']
    interval = form.cleaned_data['interval']

    # Обернем в транзакцию, чтобы все бронирования были сохранены или отменены в случае ошибки

        # Основной цикл для создания бронирований
    current_start_time = start_time
    current_end_time = end_time

    for repeat in range(repeats):
        # Создаем каждое бронирование
        form.cleaned_data['start_time'] = current_start_time
        form.cleaned_data['end_time'] = current_end_time

        create_single_booking(user, room, form, bookings)

        # Обновляем время для следующего цикла (добавляем интервал)
        current_start_time += datetime.timedelta(days=interval)
        current_end_time += datetime.timedelta(days=interval)

    return bookings

def create_weekly_recurrence_bookings(user, room, form, bookings):
    """
    Функция для создания повторяющихся бронирований по неделям.
    
    :param room: Room object (комната, которую бронируем)
    :param form: Форма с данными бронирования
    :param user: Пользователь, который делает бронирование
    :param bookings: Список, куда добавляются созданные бронирования
    :return: список созданных бронирований
    """
    # Получаем данные из формы
    start_time = form.cleaned_data['start_time']
    end_time = form.cleaned_data['end_time']
    repeats = form.cleaned_data['repeats']  # Количество повторений
    interval = form.cleaned_data['interval']  # Интервал между повторениями (в неделях)
    weekdays = json.loads(form.cleaned_data['selected_days'])  # Массив с днями недели, например, [0, 2, 4] (понедельник, среда, пятница)
    weekdays = [day - 1 for day in weekdays]
    
    # Обернем в транзакцию для атомарности
    with transaction.atomic():
        # Основной цикл для создания серий бронирований
        for repeat in range(repeats):
            # Вычисляем смещение по неделям для текущей серии
            week_offset = repeat * interval
            
            # Итерируемся по дням недели, когда должно быть событие
            for day in weekdays:
                # Вычисляем дату для каждого дня недели в этой серии
                current_start_time = start_time + datetime.timedelta(weeks=week_offset) + datetime.timedelta(days=(day - start_time.weekday()) % 7)
                current_end_time = end_time + datetime.timedelta(weeks=week_offset) + datetime.timedelta(days=(day - start_time.weekday()) % 7)

                # Убедимся, что текущее время находится в будущем (если нет, пропускаем)
                if current_start_time >= datetime.datetime.now():
                    form.cleaned_data['start_time'] = current_start_time
                    form.cleaned_data['end_time'] = current_end_time
                    # Создаем бронирование на вычисленное время
                    create_single_booking(user, room, form, bookings)

    return bookings

def create_monthly_recurrence_bookings(user, room, form, bookings):
    """
    Функция для создания повторяющихся бронирований по месяцам с выбором дней.
    
    :param room: Room object (комната, которую бронируем)
    :param form: Форма с данными бронирования
    :param user: Пользователь, который делает бронирование
    :param bookings: Список, куда добавляются созданные бронирования
    :return: список созданных бронирований
    """
    # Получаем данные из формы
    start_time = form.cleaned_data['start_time']
    end_time = form.cleaned_data['end_time']
    repeats = form.cleaned_data['repeats']  # Количество повторений
    interval = form.cleaned_data['interval']  # Интервал между повторениями (в месяцах)
    days_of_month = json.loads(form.cleaned_data['selected_days'])  # Массив с выбранными днями месяца, например, [1, 15, 31]
    
    # Обернем в транзакцию для атомарности
    with transaction.atomic():
        # Основной цикл для создания серий бронирований
        for repeat in range(repeats):
            # Вычисляем смещение по месяцам для текущей серии
            month_offset = repeat * interval

            # Итерируемся по дням месяца, когда должно быть событие
            for day in days_of_month:
                # Вычисляем текущий месяц и год
                current_month = (start_time.month - 1 + month_offset) % 12 + 1
                current_year = start_time.year + (start_time.month - 1 + month_offset) // 12

                # Проверяем, сколько дней в текущем месяце
                _, days_in_month = calendar.monthrange(current_year, current_month)
                
                # Если выбранный день больше количества дней в месяце, пропускаем этот день
                if day > days_in_month:
                    continue

                # Вычисляем дату для каждого дня месяца в этой серии
                try:
                    current_start_time = start_time.replace(year=current_year, month=current_month, day=day)
                    current_end_time = end_time.replace(year=current_year, month=current_month, day=day)
                except ValueError:
                    # Если дата недопустима (например, 31 февраля), пропускаем этот день
                    continue

                # Убедимся, что текущее время находится в будущем (если нет, пропускаем)
                if current_start_time >= datetime.datetime.now():
                    form.cleaned_data['start_time'] = current_start_time
                    form.cleaned_data['end_time'] = current_end_time
                    # Создаем бронирование на вычисленное время
                    create_single_booking(user, room, form, bookings)

    return bookings

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