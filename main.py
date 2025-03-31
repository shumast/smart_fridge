import sqlite3 as sl
import telebot
from datetime import datetime, timezone
from telebot import types
import csv

last_call_closest = []
dict = {}
prod = []
cnt = 0
with open('products.csv', encoding='UTF8') as f:
    reader = csv.reader(f)
    for row in reader:
        dict.update({row[0]: cnt})
        if len(row[0].split(' ')) == 2:
            x, y = row[0].split(' ')
            dict.update({y + ' ' + x: cnt})
        prod.append(row[0])
        cnt += 1

bot = telebot.TeleBot('7438301360:AAE6fjH2wYcjNEYYz1Th9ICz7e8vQX6H6rE')

con = sl.connect('fridge.db')

with con:
    data = con.execute("select count(*) from sqlite_master where type='table' and name='fridge'")
    for row in data:
        if row[0] == 0:
            with con:
                con.execute("""
                    CREATE TABLE fridge (
                        datetime VARCHAR(40) PRIMARY KEY,
                        date VARCHAR(40),
                        name VARCHAR(40),
                        product INTEGER(20),
                        amount INTEGER(20)
                    );
                """)

@bot.message_handler(commands=['start'])
def start(message):
    con = sl.connect('fridge.db')
    cursor = con.cursor()
    with (con):
        cursor.execute('DELETE FROM fridge WHERE name = ?', (str(message.from_user.username),))
        con.commit()
    bot.send_message(message.chat.id, 'Привет, {0.first_name}! Я твой холодильник'.format(message.chat))
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Добавить')
    button2 = types.KeyboardButton('Убрать')
    button3 = types.KeyboardButton('Рецепт')
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, "Что изволите?", reply_markup=markup)

@bot.message_handler(commands=['show'])
def start(message):
    con = sl.connect('fridge.db')
    s = ''
    with con:
        data = con.execute('SELECT * FROM fridge WHERE name = ?', [str(message.from_user.username)])
        for row in data:
            s = s + '*' + str(prod[int(row[3])]) + '*' + ' - ' + str(row[4]) + '\n'
    if s == '':
        s = 'Холодильник пустой, надо бы в магазин сходить'
    bot.send_message(message.chat.id, s, parse_mode='Markdown')

@bot.message_handler(commands=['ask'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Добавить')
    button2 = types.KeyboardButton('Убрать')
    button3 = types.KeyboardButton('Рецепт')
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, "Что изволите?", reply_markup=markup)

def dist(a, b):
    n = len(a)
    m = len(b)
    dp = []
    for i in range(n + 1):
        dp.append([])
        for j in range(m + 1):
            dp[i].append(0)
    for i in range(n + 1):
        dp[i][0] = i
    for i in range(m + 1):
        dp[0][i] = i
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] != b[j - 1]:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1
            else:
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1])
            if i >= 2 and j >= 2 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
    return dp[n][m]

def get_closest(s):
    global last_call_closest
    mx = 10
    best = []
    best_res = []
    for i in range(len(prod)):
        c = dist(prod[i], s)
        for j in prod[i].split(' '):
            c = min(c, dist(j, s))
        if len(best) < mx:
            best.append(i)
            best_res.append(c)
            for j in range(len(best) - 1, 0, -1):
                if best_res[j - 1] > best_res[j]:
                    best_res[j - 1], best_res[j] = best_res[j], best_res[j - 1]
                    best[j - 1], best[j] = best[j], best[j - 1]
        elif best_res[mx - 1] > c:
            best_res[mx - 1] = c
            best[mx - 1] = i
            for j in range(mx - 1, 0, -1):
                if best_res[j - 1] > best_res[j]:
                    best_res[j - 1], best_res[j] = best_res[j], best_res[j - 1]
                    best[j - 1], best[j] = best[j], best[j - 1]
    last_call_closest = best
    return best

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global last_call_closest
    if call.data == "yes1":
        bot.send_message(call.message.chat.id,
                         'Теперь попробуйте снова')
        bot.register_next_step_handler(call.message, add)
    if call.data == "yes2":
        bot.send_message(call.message.chat.id,
                         'Теперь попробуйте снова')
        bot.register_next_step_handler(call.message, delete)
    elif call.data == "no1":
        ans = prod[last_call_closest[0]]
        for i in range(1, 10):
            ans += '\n'
            ans += prod[last_call_closest[i]]
        bot.send_message(call.message.chat.id,
                         'Возможно одно из этих:\n' + ans)
        bot.register_next_step_handler(call.message, add)
    elif call.data == "no2":
        ans = prod[last_call_closest[0]]
        for i in range(1, 10):
            ans += '\n'
            ans += prod[last_call_closest[i]]
        bot.send_message(call.message.chat.id,
                         'Возможно одно из этих:\n' + ans)
        bot.register_next_step_handler(call.message, delete)

def add(message):
    con = sl.connect('fridge.db')
    cursor = con.cursor()
    sql = 'SELECT amount FROM fridge WHERE name = ? AND product = ? and date = ?'
    sql1 = 'INSERT INTO fridge (datetime, date, name, product, amount) values(?, ?, ?, ?, ?)'
    sql2 = 'UPDATE fridge SET amount = amount + ? WHERE name = ? AND product = ? AND date = ?'
    now = datetime.now(timezone.utc)
    z = message.text.split(' ')
    product = z[0]
    for i in range(1, len(z) - 1):
        product += ' '
        product += z[i]
    amount = z[len(z) - 1]
    product = product.lower()
    if dict.get(product) == None:
        best = get_closest(product)
        markup = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Одно из этих', callback_data='yes1')
        key_no = types.InlineKeyboardButton(text='Покажи больше', callback_data='no1')
        markup.add(key_yes, key_no)
        ans = prod[best[0]]
        for i in range(1, 3):
            ans += '\n'
            ans += prod[best[i]]
        bot.send_message(message.chat.id,
                         'Попробуйте снова, возможно имелось в виду:\n' + ans,
                         reply_markup=markup)
    else:
        product = dict.get(product)
        with con:
            prods = cursor.execute(sql, (str(message.chat.username), int(product), str(now.date())))
            con.commit()
            cntt = 0
            for row in prods:
                cntt += 1
            if cntt == 0:
                data = (str(now),
                     str(now.date()),
                     str(message.chat.username),
                     int(product),
                     int(amount))
                with con:
                    cursor.execute(sql1, data)
                    con.commit()
            else:
                data = (int(amount),
                        str(message.chat.username),
                        int(product),
                        str(now.date()))
                with con:
                    cursor.execute(sql2, data)

def delete(message):
    con = sl.connect('fridge.db')
    cursor = con.cursor()
    z = message.text.split(' ')
    product = z[0]
    for i in range(1, len(z) - 1):
        product += ' '
        product += z[i]
    amount = int(z[len(z) - 1])
    product = product.lower()
    if dict.get(product) == None:
        best = get_closest(product)
        markup = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Одно из этих', callback_data='yes2')
        key_no = types.InlineKeyboardButton(text='Покажи больше', callback_data='no2')
        markup.add(key_yes, key_no)
        ans = prod[best[0]]
        for i in range(1, 3):
            ans += '\n'
            ans += prod[best[i]]
        bot.send_message(message.chat.id,
                         'Попробуйте снова, возможно имелось в виду:\n' + ans,
                         reply_markup=markup)
    else:
        product = dict.get(product)
        dates = []
        with con:
            prods = cursor.execute('SELECT date FROM fridge WHERE name = ? AND product = ?', [str(message.from_user.username), str(product)])
            con.commit()
            for row in prods:
                dates.append(datetime.strptime(row[0], '%Y-%m-%d').date())
        cursor = con.cursor()
        sql1 = 'UPDATE fridge SET amount = amount - ? WHERE name = ? AND product = ? AND date = ?'
        sql2 = 'DELETE FROM fridge WHERE name = ? AND product = ? AND date = ?'
        ind = 0
        while amount > 0 and ind < len(dates):
            with con:
                prods = cursor.execute('SELECT amount FROM fridge WHERE name = ? AND product = ?',
                                    [str(message.from_user.username), str(product)])
                for row in prods:
                    if int(row[0]) > amount:
                        cursor.execute(sql1, (int(amount), str(message.chat.username), int(product), str(dates[ind])))
                        con.commit()
                        amount = 0
                        break
                    else:
                        amount -= int(row[0])
                        cursor.execute(sql2, (str(message.chat.username), int(product), str(dates[ind])))
                        con.commit()
            ind += 1

@bot.message_handler(content_types=['text'])
def func(message):
    if message.text == 'Добавить':
        bot.send_message(message.chat.id,
                         'Введите продукты по образцу:\nназвание и количество(через пробел)')
        bot.register_next_step_handler(message, add)
    elif message.text == 'Убрать':
        bot.send_message(message.chat.id,
                         'Введите продукты по образцу:\nназвание и количество, которое было использовано(через пробел)')
        bot.register_next_step_handler(message, delete)
    else:
        bot.send_message(message.chat.id,
                         'Я не понимаю\n')


bot.polling(none_stop=True, interval=0)
#if __name__ == '__main__':
#    while True:
#        try:
#            bot.polling(none_stop=True, interval=0)
#        except Exception as e:
#            print('❌❌❌❌❌ Сработало исключение! ❌❌❌❌❌')