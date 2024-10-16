from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_duration(duration):
    """Форматирует длительность в строку 'X час(ов) Y минут(ы)' с правильным склонением."""
    if isinstance(duration, timedelta):
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        # Функция для склонения слов "час" и "минута"
        def pluralize_unit(value, unit_forms):
            if 11 <= value % 100 <= 19:
                return unit_forms[2]
            elif value % 10 == 1:
                return unit_forms[0]
            elif 2 <= value % 10 <= 4:
                return unit_forms[1]
            else:
                return unit_forms[2]

        hour_str = f"{hours} {pluralize_unit(hours, ['час', 'часа', 'часов'])}" if hours > 0 else ""
        minute_str = f"{minutes} {pluralize_unit(minutes, ['минута', 'минуты', 'минут'])}" if minutes > 0 else ""

        # Склеиваем часы и минуты, если обе величины не равны нулю
        return " ".join(filter(None, [hour_str, minute_str]))

    return ""