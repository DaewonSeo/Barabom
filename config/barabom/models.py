from django.db import models
from django.contrib.auth.models import User


class Keyword(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.CharField(max_length=100)

    def __str__(self):
        return self.word


class PublishingCompany(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=255)
    publishing_company = models.ManyToManyField(PublishingCompany)
    date = models.DateField()
    description = models.TextField()
    link = models.CharField(max_length=255)
    is_naver = models.BooleanField(default=False)
    keywords = models.ManyToManyField(Keyword)

    def __str__(self):
        return f'{self.title} - {self.publishing_company} '


class Telegram(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    chat_id = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.user}의 텔레그램 봇 정보'


