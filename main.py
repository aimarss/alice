from flask import Flask, request
import logging
import json
import requests


class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.article = None

    def is_logged(self):

        if self.name is not None:
            return True
        else:
            return False

    def get_name(self):
        return self.name

    def set_article(self, article):
        self.article = article

    def get_article(self):
        return self.article


user = None

app = Flask(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')

logging.basicConfig(level=logging.DEBUG)


def log():
    logging.debug('Debug')
    logging.info('Info')
    logging.warning('Warning')
    logging.error('Error')
    logging.critical('Critical or Fatal')


sessionStorage = {}

info = ['О разработчике', 'Посоветуй статью', 'Поиск по ключевым словам', 'Показать обложку', 'Переведи', 'Выход']


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)

#функция снизу, которая когда ее отдельно запускаешь, работает, а тут нет)


def image(url):
    r = requests.get(url)
    f = {"file": r.content}
    return requests.post("https://dialogs.yandex.net/api/v1/skills/4be97f7a-f911-41be-90a4-36c4269647e4/images",
                         files=f, headers={"Authorization": "OAuth AQAAAAAg1GXEAAT7oydYIgkv-0-EkrYRD-ok6CE",
                         "Content - Type": "multipart / form - data"}).json()['image']['id']


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Request: %r', response)
    return json.dumps(response)


def handle_dialog(res, req):
    global user

    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = \
            'Привет! Как тебя зовут?'
        sessionStorage[user_id] = {
            'first_name': None,
            'prev_answer': ""
        }
        return
    if user is None:
        user = User(user_id, get_first_name(req))
        if user.get_name() is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста'
        else:
            user = User(user_id, get_first_name(req))
            res['response']['text'] = 'Приятно познакомиться, ' + user.get_name().title() \
                                      + '. Я - Алиса.Вот что я могу делать:'
            res['response']['buttons'] = [
                {
                    'title': inf,
                    'hide': True
                } for inf in info
            ]
    else:
        js = requests.get(
            "https://api.nytimes.com/svc/news/v3/content/all/all.json?api-key=pifEkKSGyCdh0UXJ39FGXGDeHGje9BMG").json()
        if 'Посоветуй статью' == req['request']['original_utterance']:
            res['response']['text'] = "Нажми на кнопку!\nЧтобы прочитать новость."
            url = js['results'][0]['url']
            user.set_article(0)
            res['response']['buttons'] = [
                {
                    'title': "Открыть ссылку",
                    'url': url
                }
                ]
        elif 'Поиск по ключевым словам' == req['request']['original_utterance']:
            res['response']['text'] = "Введи ключевые слова через пробел \n(как на русском так и на английском)"
            sessionStorage[user_id]['prev_answer'] = 'Ключевое слово'

        elif sessionStorage[user_id]['prev_answer'] == 'Ключевое слово':
            sessionStorage[user_id]['prev_answer'] = ""
            keywords = req['request']['original_utterance'].split(' ')
            langjs = requests.get(
                'https://translate.yandex.net/api/v1.5/tr.json/detect?key=\
                trnsl.1.1.20190423T163009Z.0c7f2c45aadff75c.766ce917d56e6d2d6314d1a3ca3f137ad71b6a8d&text=' +
                keywords[0] + '&hint=en,ru').json()
            lang = langjs['lang']
            js = requests.get(
                "https://api.nytimes.com/svc/news/v3/content/all/all.json?api-key=\
                pifEkKSGyCdh0UXJ39FGXGDeHGje9BMG").json()
            if lang == 'en':
                #тут есть возможность поддержки нескольких языков(я вам говорил на уроке что не работает, теперь есть)
                for i in range(len(js['results'])):
                    for keyword in keywords:
                        if keyword in js['results'][i]['title']:
                            res['response']['text'] = "Нажми на кнопку!\nЧтобы прочитать новость."
                            url = js['results'][i]['url']
                            user.set_article(i)
                            res['response']['buttons'] = [
                                {
                                    'title': "Открыть ссылку",
                                    'url': url
                                }
                            ]
                        elif i == len(js['results']) and keyword == keywords[-1]:
                            res['response']['text'] = 'упс, ничего не нашлось('
                            res['response']['buttons'] = [
                                {
                                    'title': inf,
                                    'hide': True
                                } for inf in info
                            ]
            elif lang == 'ru':
                for i in range(len(keywords)):
                    langjs = requests.get(
                        'https://translate.yandex.net/api/v1.5/tr.json/translate?key=\
                        trnsl.1.1.20190423T163009Z.0c7f2c45aadff75c.766ce917d56e6d2d6314d1a3ca3f137ad71b6a8d&text=' +
                        keywords[i] + '&lang=en').json()
                    keywords[i] = langjs['text'][0]
                for i in range(len(js['results'])):
                    for keyword in keywords:
                        if keyword in js['results'][i]['title']:
                            res['response']['text'] = "Нажми на кнопку!\nЧтобы прочитать новость."
                            url = js['results'][i]['url']
                            user.set_article(i)
                            res['response']['buttons'] = [
                                {
                                    'title': "Открыть ссылку",
                                    'url': url
                                }
                            ]
        elif 'Открыть ссылку' == req['request']['original_utterance']:
            res['response']['text'] = 'Вот еще функции'
            res['response']['buttons'] = [
                {
                    'title': inf,
                    'hide': True
                } for inf in info
            ]

        elif 'Показать обложку' == req['request']['original_utterance']:
            res['response']['card'] = {}
            res['response']['card']['type'] = 'BigImage'
            res['response']['card']['title'] = 'Durable, Adaptable Cork'
            res['response']['card']['image_id'] = "1540737/3b5afd7bca4d9644ee5e"
            res['response']['text'] = 'Вот еще функции'
            res['response']['buttons'] = [
                {
                    'title': inf,
                    'hide': True
                } for inf in info
            ]
        elif 'Переведи' == req['request']['original_utterance']:
            title = js['results'][user.get_article()]['title']
            langjs = requests.get(
                'https://translate.yandex.net/api/v1.5/tr.json/translate?key='
                'trnsl.1.1.20190423T163009Z.0c7f2c45aadff75c.766ce917d56e6d2d6314d1a3ca3f137ad71b6a8d&text=' + title +
                '&lang=ru').json()
            res['response']['text'] = langjs['text'][0]
            res['response']['buttons'] = [
                                {
                                    'title': inf,
                                    'hide': True
                                } for inf in info
                            ]

        elif 'О разработчике' == req['request']['original_utterance']:
            res['response']['text'] = 'Менояков Аймар, Яндекс Лицей 2019'
            res['response']['buttons'] = [
                {
                    'title': inf,
                    'hide': True
                } for inf in info
            ]
        elif 'Выход' == req['request']['original_utterance']:
            res['response']['text'] = 'Спасибо за использование!'
            res['response']['buttons'] = [
                {
                    'title': inf,
                    'hide': True
                } for inf in info
            ]


if __name__ == '__main__':
    app.run()
