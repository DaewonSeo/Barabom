from django.contrib import admin
from .models import Keyword, PublishingCompany, Article, Telegram

admin.site.register([Keyword, PublishingCompany, Article, Telegram])
