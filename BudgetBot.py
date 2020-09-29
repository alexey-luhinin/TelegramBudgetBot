import config
import requests
import re
import sqlite3
import datetime as dt
from numpy import array_split

def create_db():
    db = sqlite3.connect('budget.db')
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS balance (id_chat INTEGER, category TEXT, value FLOAT, commentary TEXT, date TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS category (id_chat INTEGER, category TEXT)")
    db.commit()
    db.close()


def insert_in_db(chat_id, category, digit, commentary=''):
    year = dt.datetime.now().year
    month = dt.datetime.now().month
    day = dt.datetime.now().day
    date = f'{year}-{month}-{day}'
    try:
        db = sqlite3.connect('budget.db')
        c = db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS balance (id_chat INTEGER, category TEXT, value FLOAT, commentary TEXT, date TEXT)")
        c.execute("INSERT INTO balance VALUES ({}, '{}', {}, '{}', '{}')".format(chat_id, category, digit, commentary, date))
        c.execute("SELECT * FROM balance")
        db.commit()
        send_message(chat_id, 'Добавил')
    except:
        send_message(chat_id, 'Что-то пошло не так...')
    db.close()

def check_in_db(last_update_id):
    db = sqlite3.connect('budget.db')
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS log(last_update_id INTEGER)")
    c.execute("SELECT * FROM log")
    ids = c.fetchall()
    if not ids:
        c.execute("INSERT INTO log VALUES ({})".format(last_update_id))
        db.commit()
        return False
    for ID in ids:
        if last_update_id in ID:
            return True
    c.execute("INSERT INTO log VALUES ({})".format(last_update_id))
    db.commit()
    db.close()
    return False


def get_updates():
    url = f'https://api.telegram.org/bot{config.TOKEN}/getUpdates'
    r = requests.get(url)
    data = r.json()
    chat_id = data['result'][-1]['message']['chat']['id']
    message = data['result'][-1]['message']['text']
    last_update_id = data['result'][-1]['update_id']
    if check_in_db(last_update_id):
        return None
    return chat_id, message


def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{config.TOKEN}/sendMessage?chat_id={chat_id}&text={text}'
    r = requests.get(url)

def send_message_with_categories(chat_id, text):
    create_db()
    create_defaul_categories(chat_id)
    category = set()
    db = sqlite3.connect('budget.db')
    c = db.cursor()
    c.execute("SELECT category FROM category")
    cta = ''
    for i in c.fetchall():
        category.add('"{}"'.format(i[0]))
    ar = array_split(list(category), len(category) // 3)
    for i in ar:
        cta += str(list(i)).replace('\'', '') + ', '
    reply_markup = '{"keyboard":[' + cta + '  ["Отмена"]],"one_time_keyboard":true,"resize_keyboard":true}'
    url = f'https://api.telegram.org/bot{config.TOKEN}/sendMessage?chat_id={chat_id}&text={text}&reply_markup={reply_markup}'
    r = requests.get(url)

def spending_per_month(chat_id):
    create_db()
    year = dt.datetime.now().year
    month = dt.datetime.now().month
    db = sqlite3.connect('budget.db')
    c = db.cursor()
    c.execute("SELECT value FROM balance WHERE date >= '{}-{}-1'".format(year, month))
    total = 0
    for i in c.fetchall():
        total += i[0]
    send_message(chat_id, f'Всего в этом месяце потрачено: {round(total, 2)} гривен')

def add_new_category(chat_id, category):
    create_db()
    db = sqlite3.connect('budget.db')
    c = db.cursor()
    c.execute("INSERT INTO category VALUES ({}, '{}')".format(chat_id, category))
    db.commit()
    c.execute("SELECT category FROM category")
    send_message(chat_id, 'Готово')
    db.close()


def create_defaul_categories(chat_id):
    categories = ['Аренда', 'Машина', 'АЗС', 'Кошка', 'Продукты', 'Интернет','Рынок','Кафе','Досуг','Путешествия', 'Аптека', 'Доход',]
    create_db()
    db = sqlite3.connect('budget.db')
    c = db.cursor()
    for category in categories:
        c.execute("SELECT category FROM category")
        cat_list = []
        for i in c.fetchall():
            if category == i[0]:
                cat_list.append(category)
        if category not in cat_list:
            c.execute("INSERT INTO category VALUES ({}, '{}')".format(chat_id, category))
    db.commit()
    db.close()



def parse_message(chat_id, message):
    if message == '/month':
        return spending_per_month(chat_id)
    if message == '/new_category':
        send_message(chat_id, 'Введите название категории: ')
        updates = get_updates()
        while(not updates):
            updates = get_updates()
        else:
            chat_id, category = updates
        if category:
            return add_new_category(chat_id, category)
    pattern_find_digit = r'[-+]?\d*[.,]\d+|\d+'
    digit = re.search(pattern_find_digit, message)
    if digit:
        send_message_with_categories(chat_id, 'Выберите категорию: ')
        updates = get_updates()
        while(not updates):
            updates = get_updates()
        else:
            chat_id, category = updates
        if category and category!='Отмена':
            insert_in_db(chat_id, category, digit.group().replace(',','.'))
            

    # pattern_find_category = r'\d\s([а-яА-Я]+)\s*'
    # pattern_find_commentary = r'\"(.+)\"'
    # category = re.search(pattern_find_category, message) 
    # commentary = re.search(pattern_find_commentary, message)
    # if not commentary:
    #     commentary = ''
    # else:
    #     commentary = commentary.group(1)
    # if digit and category:
    # else:
    #     send_message(chat_id, 'Вы пишите какую-то ерунду!')

if __name__ == '__main__':
    while(True):
        message_from_user = get_updates()
        if message_from_user:
           chat_id, message = message_from_user 
           parse_message(chat_id, message)
