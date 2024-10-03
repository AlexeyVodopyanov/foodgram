from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]
    USERNAME_FIELD = 'email'

    username = models.CharField(
        unique=True, max_length=150,
        validators=[UnicodeUsernameValidator(), ],
        verbose_name='Ник',
        help_text='Назовите ник пользователя')
    first_name = models.CharField(
        max_length=150, verbose_name='Имя',
        help_text='Назовите имя пользователя')
    last_name = models.CharField(
        max_length=150, verbose_name='Фамилия',
        help_text='Назовите фамилию пользователя')
    email = models.EmailField(
        unique=True, verbose_name='E-mail',
        help_text='Укажите e-mail пользователя')
    password = models.CharField(
        max_length=128, verbose_name='Пароль',
        help_text='Введите пароль')
    avatar = models.ImageField(
        upload_to='avatars/', null=True, blank=True,
        verbose_name='Аватар', help_text='Выложите аватар')

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = verbose_name

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


class Subscriber(models.Model):
    """Модель автора и подписчик."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE, related_name='authors',
        verbose_name='Автор', help_text='Укажите автора рецепта')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE, related_name='subscriber',
        verbose_name='Подписчик', help_text='Укажите пользователя подписчика')

    class Meta:
        ordering = ('author',)
        verbose_name = 'Автор и подписчик'
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_author_user'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='author_and_user_different',
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.author}"
