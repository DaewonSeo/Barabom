from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from config import SCOPE, JSON_FILE, SPREAD_SHEET_FILE, CHAT_ID, TOKEN
import requests
import gspread
import telegram


USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)\
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132\
    Safari/537.36'

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


def send_telegram_message(message):
    bot = telegram.Bot(token=TOKEN)
    bot.sendMessage(chat_id=CHAT_ID, text=message)


def connect_file():
    """구글 스프레드 시트에 접속 연결"""   
    credentials = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, SCOPE)
    gc = gspread.authorize(credentials)
    doc = gc.open_by_url(SPREAD_SHEET_FILE)
    worksheet = doc.worksheet('시트1')
    return worksheet


def next_available_row(worksheet):
    """제일 최근 기사를 가져오기 위해 제일 하단 row로 접근"""
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list))


def write_file(worksheet, articles):
    """가져온 기사 리스트를 스택을 통해 순서 변경 후 스프레드 시트에 저장"""
    for _ in range(len(articles)):
        article = articles.pop()
        worksheet.append_row([
            article['제목'],
            article['날짜'],
            article['발행사'],
            article['링크'],
            article['요약'],
            ])


def get_article(keyword, latest_news):
    """네이버 기사 가져오기"""
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
    
    # html 요청
    base_url = 'https://search.naver.com/search.naver?'
    req = requests.get(base_url, params=params, headers={'User-Agent': USER_AGENT})
    
    # 파싱을 위한 뷰티풀 수프 객체 선언
    soup = BeautifulSoup(req.text, 'html.parser')
    news_list = soup.select('div.group_news div.news_area')
    
    results = []

    # 페이지당 기사 순회
    for news in news_list:
        publishing_company = news.select('a.info')
        date = change_date_format(news.select('span.info')[-1].text)
        is_naver = publishing_company[1]['href'] \
            if len(publishing_company) > 1 else '없음'
        title = news.select_one('a.news_tit')['title']
        url = news.select_one('a.news_tit')['href']
        description = news.select_one('a.api_txt_lines.dsc_txt_wrap').text
        article = {
            '제목': title,
            '날짜': date,
            '발행사': publishing_company[0].text,
            '링크': url,
            '요약': description
        }

        if url == latest_news:
            send_telegram_message('최신 기사가 이미 저장되어 있기 때문에 종료합니다.')
            break

        else:
            results.append(article)
            message = f"""[{article['날짜']}]\n
            {article['발행사']}의 기사 1건이 보도되었습니다.\n
            기사제목 : {article['제목']}\n,
            {article['링크']}
            """
            send_telegram_message(message)

    return results    
    

def run():
    keyword = '제11전투비행단'
    load_file = connect_file()
    last_row = next_available_row(load_file)
    latest_news = load_file.row_values(last_row)[3] # google sheet 시트 내 기사 링크 주소
    articles = get_article(keyword, latest_news)
    write_file(load_file, articles)


if __name__ == "__main__":
    run()