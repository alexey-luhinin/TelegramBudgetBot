import config
import requests
import re
import sqlite3

def insert_in_db(chat_id, category, digit, commentary=''):
    db = sqlite3.connect('budget.db')
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS balance (id_chat INTEGER, category TEXT, value FLOAT, commentary TEXT)")
    c.execute("INSERT INTO balance VALUES ({}, '{}',{},'{}')".format(chat_id, category, digit, commentary))
    c.execute("SELECT * FROM balance")
    print(c.fetchall())
    db.commit()
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
    return chat_id, last_update_id, message


def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{config.TOKEN}/sendMessage?chat_id={chat_id}&text={text}'
    r = requests.get(url)

def parse_message(chat_id, message):
    pattern_find_digit = r'[-+]?\d*[.,]\d+|\d+'
    pattern_find_category = r'\d\s([а-яА-Я]+)\s*'
    pattern_find_commentary = r'\"(.+)\"'
    digit = re.search(pattern_find_digit, message)
    category = re.search(pattern_find_category, message) 
    commentary = re.search(pattern_find_commentary, message)
    if not commentary:
        commentary = ''
    else:
        commentary = commentary.group(1)
    if digit and category:
        insert_in_db(chat_id, category.group(1), digit.group(), commentary)
    else:
        send_message(chat_id, 'Вы пишите какую-то ерунду!')

if __name__ == '__main__':
    while(True):
        message_from_user = get_updates()
        if message_from_user:
           chat_id, last_update_id, message = message_from_user 
           parse_message(chat_id, message)
