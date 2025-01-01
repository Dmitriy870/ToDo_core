from django.conf import settings
from django.core.mail import send_mail


def send_notification():
    try:
        user_email = "rbinans@gmail.com"  # Адрес получателя
        subject = "Дедлайн задачи"  # Тема письма
        message = "Дедлайн задачи наступит через час."  # Текст письма

        # Отправка письма
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Адрес отправителя
            [user_email],  # Список получателей
            fail_silently=False,  # Выбросить исключение при ошибке
        )

        print(f"Уведомление отправлено на {user_email}.")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")
