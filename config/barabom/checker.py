from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from models import Keyword, PublishingCompany, Article, Telegram
import requests
import telegram
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'pisicalnote.settings')
django.setup()


def change_date_format(date):
    """
    날짜 포맷을 년.월.일. 형식으로 변경하는 함수
    네이버 뉴스의 경우
    0분전, 0시간 전, 0일전 등 7일 내 뉴스는
    년.월.일이 아닌 다른 포맷으로 표시되므로 날짜를 통일해주는 함수가 필요함
    """
    current_time = datetime.now()
    date = date.replace(" ", "")
    if date.endswith('분전'):
        minutes = int(date[:-2])
        date = current_time - timedelta(minutes=minutes)

    elif date.endswith('시간전'):
        hours = int(date[:-3])
        date = current_time - timedelta(hours=hours)

    elif date.endswith('일전'):
        days = int(date[:-2])
        date = current_time - timedelta(days=days)

    else:
        date = datetime.strptime(date, '%Y.%m.%d.')
    return date.strftime("%Y-%m-%d")


def send_telegram_message(request, message):
    user = Telegram.objects.get(user__id=request.user.id)
    bot = telegram.Bot(token=user.token)
    bot.sendMessage(chat_id=user.chat_id, text=message)


def get_article(keyword, useragent):
    query = f'\"{keyword}\"'
    params = {
        'where': 'news',
        'query': query,
        'sm': 'tab_opt',
        'sort': 1,
        'photo': 0,
        'field': 0,
        'pd': 0,
        'ds': '',
        'de': '',
        'docid': '',
        'related': 0,
        'mynews': 0,
        'nso': 'so:dd,p:all,a:all',
        'office_type': 0,
        'office_section_code': 0,
        'news_office_checked': '',
        'is_sug_officeid': 0,
    }

    base_url = 'https://search.naver.com/search.naver?'
    req = requests.get(base_url, params=params, headers={'User-Agent': useragent})
    soup = BeautifulSoup(req.text, 'html.parser')
    news_list = soup.select('div.group_news div.news_area')
    results = []
    recent_news = Article.objects.get(word=keyword).order_by('date').first()
    for news in news_list:
        publishing_company = news.select('a.info')
        date = change_date_format(news.select_one('span.info').text)
        is_naver = publishing_company[1]['href'] \
            if len(publishing_company) > 1 else '없음'
        title = news.select_one('a.news_tit')['title']
        url = news.select_one('a.news_tit')['href']
        description = news.select_one('a.api_txt_lines.dsc_txt_wrap').text
        if url == recent_news.link:
            message = '최신 기사가 이미 저장되어 있기 때문에 종료합니다.'
            send_telegram_message(message)
            break
        try:
            pb = PublishingCompany.objects.get(name=publishing_company[0].text)
        except PublishingCompany.DoesNotExist:
            pb = PublishingCompany(name=publishing_company[0].text)
            pb.save()
        article = Article(title=title,
                          publishing_company=pb,
                          date=date,
                          description=description,
                          link=url,
                          is_naver=is_naver,
                          keyword=keyword
                          )
        article.save()

def main(request):
    keyword = Keyword.objects.filter(user__id=request.user.id).first()
    useragent = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132\
     Safari/537.36'
    get_article(keyword, useragent)


main()