from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
import datetime

from .models import User, Booking, Room

import re


class UserSignUpForm(UserCreationForm):
  username = forms.CharField(
    required=True, 
    widget=forms.TextInput(attrs={
    'class': 'form-control rounded-3',
    'id': 'floatingInput',
    'placeholder': 'username'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
      'unique': "Пользователь с таким именем уже существует"
    }
  )
  password1 = forms.CharField(
    required=True, 
    widget=forms.PasswordInput(attrs={
    'class': 'form-control rounded-3',
    'id': 'floatingPassword1',
    'placeholder': 'password1'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
      'min_length': "Пароль должен содержать не менее 8 символов"
    }
  )
  password2 = forms.CharField(
    required=True, 
    widget=forms.PasswordInput(attrs={
    'class': 'form-control rounded-3',
    'id': 'floatingPassword2',
    'placeholder': 'password2'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
      'password_mismatch': "Пароли не совпадают"
    }
  )

  class Meta:
    model = User
    fields = ['username', 'password1', 'password2'] 

  def clean_username(self):
    username = self.cleaned_data.get('username')
    if User.objects.filter(username=username).exists():
      raise forms.ValidationError("Пользователь с таким именем уже существует")
    return username

  def clean_password1(self):
    password = self.cleaned_data.get('password1')

    if len(password) < 8:
      raise forms.ValidationError("Пароль должен содержать не менее 8 символов")
    if not re.search(r'\d', password):
      raise forms.ValidationError("Пароль должен содержать хотя бы одну цифру")
    if not re.search(r'[A-Z]', password):
      raise forms.ValidationError("Пароль должен содержать хотя бы одну заглавную букву")
    return password

  def clean_password2(self):
    password1 = self.cleaned_data.get('password1')
    password2 = self.cleaned_data.get('password2')

    if password1 and password2 and password1 != password2:
      raise forms.ValidationError("Пароли не совпадают")
    
    return password2
  
class UserSignInForm(forms.Form):
  username = forms.CharField(
    required=True, 
    widget=forms.TextInput(attrs={
      'class': 'form-control rounded-3', 
      'placeholder': 'username',
      'id': 'floatingInput'
    }),
  )
  password = forms.CharField(
    required=True, 
    widget=forms.PasswordInput(attrs={
      'class': 'form-control rounded-3', 
      'placeholder': 'password',
      'id': 'floatingPassword'
    }),
  )

  def clean(self):
    cleaned_data = super().clean()
    username = cleaned_data.get('username')
    password = cleaned_data.get('password')
    # Можно добавить свою логику валидации, например проверку длины пароля или другие проверки
    if username and password:
      if len(password) < 8:
        self.add_error('password', "Пароль должен быть не менее 8 символов")
  
    return cleaned_data
  
class BookingForm(forms.ModelForm):
  class Meta:
    model = Booking
    fields = ['start_time', 'end_time', 'recurrence_type', 'repeats', 'interval', 'comment', 'selected_days']  # Поля, которые будут на форме

  start_time = forms.DateTimeField(required=True, widget=forms.DateTimeInput(attrs={
    'type': 'datetime-local',
    'class': 'form-control',
    'id': 'start_time'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  end_time = forms.DateTimeField(required=True, widget=forms.DateTimeInput(attrs={
    'type': 'datetime-local',
    'class': 'form-control',
    'id': 'end_time'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  recurrence_type = forms.ChoiceField(
    choices=[
      ('no', 'Нет'),
      ('bydays', 'По дням'),
      ('byweeks', 'По неделям'),
      ('bymonths', 'По месяцам'),
    ],
    required=True,
    widget=forms.Select(attrs={
      'class': 'form-select recurrence_type',
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  repeats = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
    'type': 'number',
    'class': 'form-control repeats',
    'disabled': 'false',
    'value': '0'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  interval = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={
    'type': 'number',
    'class': 'form-control interval',
    'disabled': 'false',
    'value': '0'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  comment = forms.CharField(required=False, widget=forms.Textarea(attrs={
    'class': 'form-control',
    'id': 'comment',
    'placeholder': 'Укажите нюансы использования помещения, если таковые имеются'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  selected_days = forms.CharField(required=False, widget=forms.TextInput(attrs={
    'class': 'form-control selected-days',
    'hidden': 'true'
    })
  )

  def clean_start_time(self):
    start_time = self.cleaned_data['start_time']

    if start_time < timezone.now():
      raise forms.ValidationError('Нельзя бронировать на прошедшее время')
  
    return start_time
  
  def clean_end_time(self):
    end_time = self.cleaned_data.get('end_time')
    start_time = self.cleaned_data.get('start_time')  # Получаем начальное время

    if not start_time:
      raise forms.ValidationError("Необходимо корректно указать начальное время")
    
    if end_time and end_time <= start_time:
      raise forms.ValidationError("Конечное время должно быть больше начального")
    
    return end_time
  
class DeleteBookingForm(forms.Form):
  delete_all = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
    'type': 'checkbox',
    'class': 'form-check-input'
    }),
  )
  
  pk = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={
    'type': 'number',
    'class': 'form-control',
    'id': 'pk',
    'hidden': 'false',
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  tag = forms.CharField(required=True, widget=forms.TextInput(attrs={
    'type': 'text',
    'class': 'form-control',
    'id': 'tag',
    'hidden': 'false',
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

class ChangeBookingForm(forms.Form):
  start_time = forms.DateTimeField(required=True, widget=forms.DateTimeInput(attrs={
    'type': 'datetime-local',
    'class': 'form-control',
    'id': 'start_time'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  end_time = forms.DateTimeField(required=True, widget=forms.DateTimeInput(attrs={
    'type': 'datetime-local',
    'class': 'form-control',
    'id': 'end_time'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  change_all = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
    'type': 'checkbox',
    'class': 'form-check-input',
    }),
  )

  pk = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={
    'type': 'number',
    'class': 'form-control',
    'id': 'change_pk',
    'hidden': 'true'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  tag = forms.CharField(required=True, widget=forms.TextInput(attrs={
    'type': 'text',
    'class': 'form-control',
    'id': 'change_tag',
    'hidden': 'true'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

  comment = forms.CharField(required=False, widget=forms.Textarea(attrs={
    'class': 'form-control',
    'id': 'comment',
    'rows': '2',
    'placeholder': 'Укажите нюансы использования помещения, если таковые имеются'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    }
  )

class CreateRoomForm(forms.Form):
  class Meta:
    model = Room  # Укажите вашу модель
    fields = ['name', 'timebreak', 'open_time', 'close_time', 'image', 'comment']

  # Название помещения
  name = forms.CharField(
    required=True,
    widget=forms.TextInput(attrs={
      'class': 'form-control rounded-3',
      'id': 'name',
      'name': 'name',
      'placeholder': 'Введите название помещения'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    })

  timebreak = forms.TimeField(
    required=True,
    widget=forms.TimeInput(attrs={
      'type': 'time',
      'class': 'form-control',
      'id': 'timebreak',
      'name': 'timebreak'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    })

    # Время открытия помещения
  open_time = forms.TimeField(
    required=True,
    widget=forms.TimeInput(attrs={
      'type': 'time',
      'class': 'form-control',
      'id': 'open_time',
      'name': 'open_time'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    })

    # Время закрытия помещения (часы и минуты)
  close_time = forms.TimeField(
    required=True,
    widget=forms.TimeInput(attrs={
      'type': 'time',
      'class': 'form-control',
      'id': 'close_time',
      'name': 'close_time'
    }),
    error_messages={
      'required': "Это поле обязательно для заполнения",
    })

    # Файл изображения помещения
  image = forms.FileField(
    required=False,
    widget=forms.ClearableFileInput(attrs={
      'class': 'form-control',
      'name': 'image',
      'id': 'image',
    }))

    # Комментарий к помещению
  comment = forms.CharField(
    required=False,
    widget=forms.Textarea(attrs={
      'class': 'form-control rounded-3',
      'id': 'comment',
      'name': 'comment',
      'placeholder': 'Добавьте комментарий (необязательно)',
      'rows': 3,
    }))

  # Валидация поля timebreak
  def clean_timebreak(self):
    timebreak = self.cleaned_data.get('timebreak')  # Получаем значение как время
    if timebreak:
      # Преобразуем время в timedelta
      timebreak_delta = datetime.timedelta(hours=timebreak.hour, minutes=timebreak.minute)
      if timebreak_delta <= datetime.timedelta(minutes=0):
        raise forms.ValidationError("Перерыв между бронированиями должен быть положительным.")
      return timebreak_delta
    raise forms.ValidationError("Введите корректный перерыв.")