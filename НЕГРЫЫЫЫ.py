import telebot
from telebot import types
from random import randint
import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)

DB = 'db4.db'

if not os.path.exists(DB):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY, coins INTEGER, name TEXT, user TEXT, kol INTEGER)")
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO data (id, coins) VALUES (?, ?)", (user_id, 0))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM data WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result is None:
        add_user(user_id)
        return False
    return True

def get_coins(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT coins FROM data WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result is None:
        add_user(user_id)
        return 0
    return result[0]

def set_coins(user_id, coins):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE data SET coins = coins + ? WHERE id = ?", (coins, user_id))
    conn.commit()
    conn.close()

def set_coins_1(user_id, coins):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE data SET coins = coins - ? WHERE id = ?", (coins, user_id))
    conn.commit()
    conn.close()

bot = telebot.TeleBot("токин")

@bot.message_handler(commands=["start"])
def start(msg):
    if msg.chat.type != "private":
        bot.send_message(msg.chat.id, f"Привет {msg.from_user.first_name}. Что бы зарегестрироватся, введите команду /start в личных сообщениях бота.")
    with sqlite3.connect("db4.db", check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data WHERE id = ?", (msg.from_user.id,))
        user = cursor.fetchone()

    if not user:
        bot.send_message(msg.chat.id, "Приветствую тебя в Laybot\nТут ты сможешь поиграть")
        ask_for_name(msg)
    else:
        bot.send_message(msg.chat.id, f"С возвращением, {user[2]}!")
        show_main_menu(msg)

def ask_for_name(msg):
    a = bot.send_message(msg.chat.id, "Придумай и напиши свое имя:")
    bot.register_next_step_handler(a, register_name)

import re

def register_name(msg):
    name = msg.text.strip()

    if len(name) < 2:
        a = bot.send_message(msg.chat.id, "Имя слишком короткое. Попробуй снова:")
        bot.register_next_step_handler(a, register_name)
        return

    if not re.match("^[A-Za-zА-Яа-я0-9 ]+$", name):
        a = bot.send_message(msg.chat.id, "Имя должно содержать только буквы и цифры. Попробуй снова:")
        bot.register_next_step_handler(a, register_name)
        return

    with sqlite3.connect("db4.db", check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data WHERE name = ?", (name,))
        existing_user = cursor.fetchone()

        if existing_user:
            bot.send_message(msg.chat.id, "Имя уже занято. Попробуйте другое:")
            a = bot.send_message(msg.chat.id, "Придумай и напиши новое имя:")
            bot.register_next_step_handler(a, register_name)
            return

        try:
            cursor.execute("INSERT INTO data (id, coins, name) VALUES (?, ?, ?)", (msg.from_user.id, 0, name))
            conn.commit()
        except sqlite3.IntegrityError:
            bot.send_message(msg.chat.id, "Ошибка: пользователь с таким ID уже существует.")
            return

    bot.send_message(msg.chat.id, f"Привет, {name}!")
    show_main_menu(msg)

@bot.message_handler(commands=["newname"])
def new_name(msg):
    if msg.chat.type != "private":
        bot.send_message(msg.chat.id, "Эту команду можно использовать только в личных сообщениях.")
        return
    
    with sqlite3.connect("db4.db", check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data WHERE id = ?", (msg.from_user.id,))
        user = cursor.fetchone()

    if not user:
        bot.send_message(msg.chat.id, "Сначала зарегистрируйтесь с помощью команды /start.")
        return

    if user[1] < 0: 
        bot.send_message(msg.chat.id, "Недостаточно монет для изменения имени. Вам нужно 10,000 монет.")
        return

    a = bot.send_message(msg.chat.id, "Введите новое имя:")
    bot.register_next_step_handler(a, lambda message: process_new_name(message, user[1]))

def process_new_name(msg, current_coins):
    new_name = msg.text.strip()
    if len(new_name) < 2:
        a = bot.send_message(msg.chat.id, "Имя слишком короткое. Попробуйте снова:")
        bot.register_next_step_handler(a, lambda message: process_new_name(message, current_coins))
        return

    with sqlite3.connect("db4.db", check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE data SET name = ?, coins = ? WHERE id = ?", (new_name, current_coins - 0, msg.from_user.id))
        conn.commit()

    bot.send_message(msg.chat.id, f"Ваше новое имя: {new_name}!")
    show_main_menu(msg)

def show_main_menu(msg):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Клик"), types.KeyboardButton("Топ игроков"))
    markup.add(types.KeyboardButton("Баланс"), types.
KeyboardButton("Казино"),types.
KeyboardButton("Биржа"),types.
KeyboardButton("Помощь"))
    bot.send_message(msg.chat.id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(commands=['me'])
def me_message(message):
    coins = get_coins(message.from_user.id)
    bot.send_message(message.chat.id, f"Ваш баланс: {coins}, id: {message.from_user.id}")

@bot.message_handler(commands=['give'])
def give_message(message):
    if message.from_user.id == 6492780518 or message.from_user.id == 7503416902 or message.from_user.id == 7121076671:
        pass
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды")
        return
    if len(message.text.split()) == 2:
        try:
            amount = int(message.text.split()[1])
            user_id = message.from_user.id
            bot.send_message(message.chat.id, f"Ваш ID {user_id}. Выдаем {amount} монет")
            set_coins(user_id, amount)
            bot.send_message(message.chat.id, f"Вы успешно получили {amount} монет(а)")
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат команды. Пример: /give 1000")
    else:
        bot.send_message(message.chat.id, "Неверный формат команды. Пример: /give 1000")

@bot.message_handler(commands=['send'])
def send_message(message):
    args = message.text.split()
    
    if len(args) == 3:
        try:
            amount = int(args[1])
            recipient_name = args[2] 
            
            with sqlite3.connect("db3.db", check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM data WHERE name = ?", (recipient_name,))
                recipient = cursor.fetchone()
                
            if recipient:
                to_id = recipient[0]
            else:
                bot.send_message(message.chat.id, "Пользователь не найден. Убедитесь, что имя введено правильно.")
                return
            
            if to_id == message.from_user.id:
                bot.send_message(message.chat.id, "Нельзя отправить монеты самому себе")
                return

            if get_user(to_id):
                if get_coins(message.from_user.id) >= amount:
                    set_coins_1(message.from_user.id, amount)
                    set_coins(to_id, amount)
                    bot.send_message(message.chat.id, f"Вы успешно отправили {amount} монет(а) пользователю {recipient_name}")
                    bot.send_message(to_id, f"Пользователь {message.from_user.id} отправил вам {amount} монет(а)")
                else:
                    bot.send_message(message.chat.id, "Недостаточно средств")
            else:
                bot.send_message(message.chat.id, "Пользователь не зарегистрирован")
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат команды. Пример: /send 100 ИмяИгрока")
    else:
        bot.send_message(message.chat.id, "Неверный формат команды. Пример: /send 100 ИмяИгрока")


from random import randint

def Game(user_id, bet, coin_amount, msg):
    Coin = randint(0, 36)  
    red = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]  
    black = [i for i in range(1, 37) if i not in red]  
    Chet = [i for i in range(1, 37) if i % 2 == 0]
    Nechet = [i for i in range(1, 37) if i % 2 != 0]
    winning_combinations = {
        "мал": range(1, 19),
        "бол": range(19, 37),
        "1-12": range(1,13),
        "13-24": range(13,25),
        "25-36": range(25,37),
        "ряд1": [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
        "ряд2": [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
        "ряд3": [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
        "кра": red,  
        "красный": red,
        "чер": black,  
        "чёр": black,
        "черный": black,
        "чёрный": black,
        "чет": Chet,
        "чёт": Chet,
        "чётный": Chet,
        "чётное": Chet,
        "четный": Chet,
        "четное": Chet,
        "нечет": Nechet,
        "нечёт": Nechet,
        "нечётный": Nechet,
        "нечётное": Nechet,
        "нечетный": Nechet,
        "нечетное": Nechet
    }
    
    if Coin == 0:
        state = "зелёный"
    elif Coin in red:
        state = "красный"
    else:
        state = "чёрный"
    
    print(f"Пользователь {user_id} ставит {bet} на {coin_amount} монет(а). Выпало {state} {Coin}")
    
    if isinstance(bet, int): 
        if Coin == bet:
            winnings = coin_amount * 36
            bot.send_message(msg.chat.id, f"Вы выиграли {winnings} монет! Выпало {state} {Coin}")
            set_coins(user_id, winnings)
        else:
            bot.send_message(msg.chat.id, f"Вы проиграли! Выпало {state} {Coin}")
            set_coins_1(user_id, coin_amount)
    else:        
        if bet in ["ряд1", "ряд2", "ряд3", "1-12", "13-24", "25-36"]:
            if Coin in winning_combinations[bet]:
                winnings = coin_amount * 2
                bot.send_message(msg.chat.id, f"Вы выиграли {winnings} монет! Выпало {state} {Coin}")
                set_coins(user_id, winnings)
            else:
                bot.send_message(msg.chat.id, f"Вы проиграли! Выпало {state} {Coin}")
                set_coins_1(user_id, coin_amount)
        elif Coin in winning_combinations[bet]:
            winnings = coin_amount 
            bot.send_message(msg.chat.id, f"Вы выиграли {winnings} монет! Выпало {state} {Coin}")
            set_coins(user_id, winnings)
        else:
            bot.send_message(msg.chat.id, f"Вы проиграли! Выпало {state} {Coin}")
            set_coins_1(user_id, coin_amount)

@bot.message_handler(commands=['ezzwin'])
def ezzwin_message(message):
    if message.from_user.id == 6492780518 or message.from_user.id == 7024934875 or message.from_user.id == 7503416902:
        if len(message.text.split()) == 2:
            try:
                amount = int(message.text.split()[1])
                user_id = message.from_user.id
                rr = randint(0, 36)
                bot.send_message(message.chat.id, f"Вы выиграли {amount} монет! Выпало {rr}")
                set_coins(user_id, amount)
            except ValueError:
                bot.send_message(message.chat.id, "Неверный формат команды. Пример: /ezzwin 1000")
    else:
        pass

@bot.message_handler(content_types=['text'])
def handle_text(msg):
    if msg.text == "Клик" or msg.text == "/klik":
        with sqlite3.connect("db4.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE data SET coins = coins + 10 WHERE id = ?", (msg.from_user.id,))
            conn.commit()
        bot.send_message(msg.chat.id, "+10 коинов")

    elif"рул" in msg.text or "Рул" in msg.text:
        if len(msg.text.split()) < 3:
            bot.send_message(msg.chat.id, "Неверный формат команды. Пример: /рул [мал|бол|чет|нечёт|кра|чер|ряд1|ряд2|ряд3|число] [ставка]")
            return
        
        user_id = msg.from_user.id
        bet_type = msg.text.split()[1]
        coin_amount = int(msg.text.split()[2])

        if coin_amount < 1:
            bot.send_message(msg.chat.id, "Ставка должна быть больше 0")
            return

        if bet_type.isdigit():
            bet = int(bet_type)
        elif bet_type in ["мал", "чет", "чёт", "кра", "нечет","чер","чëр","черное","чëрное","нечëт","бол", "ряд1", "ряд2", "ряд3", "1-12", "13-24", "25-36"]:
            bet = bet_type
        else:
            bot.send_message(msg.chat.id, "Неверный формат ставки")
            return

        if not get_user(user_id):
            bot.send_message(user_id, "Пользователь не зарегистрирован")
            return
        
        if get_coins(user_id) < coin_amount:
            bot.send_message(user_id, "Недостаточно средств")
            return

        Game(user_id, bet, coin_amount,msg)

    elif msg.text == "Баланс":
        with sqlite3.connect("db4.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT coins FROM data WHERE id = ?", (msg.from_user.id,))
            balans = cursor.fetchone()
        bot.send_message(msg.chat.id, f"Ваш баланс: {balans[0]} коинов" if balans else "Баланс не найден")

    elif msg.text == "Топ игроков" or msg.text == "/top":
        with sqlite3.connect("db4.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, coins, name FROM data ORDER BY coins DESC LIMIT 15")
            top_users = cursor.fetchall()

        top_message = "Топ игроков:\n"
        for i, (user_id, coins, name) in enumerate(top_users):
            user_info = bot.get_chat(user_id)
            username = f"{name} (@{user_info.username})" if user_info.username else "Неизвестно"
            top_message += f"{i + 1}. {username} - {coins} коинов\n"

        bot.send_message(msg.chat.id, top_message)

    
    elif msg.text == "/kazino" or msg.text == "Казино":
        bot.send_message(msg.chat.id, "Как играть:\n Рул (ставка (кра;чер;мал;бол;чëт;нечëт; отдельное число;ряд;ряд2;ряд3) (сумма ставки)")
       
    elif msg.text == "/bal" or msg.text == "б" or msg.text == "Б" or msg.text == "бал" or msg.text == "Бал":
        with sqlite3.connect("db4.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT coins FROM data WHERE id = ?", (msg.from_user.id,))
            balans = cursor.fetchone()
            bot.send_message(msg.chat.id, f"Ваш баланс: {balans[0]} коинов" if balans else "Баланс не найден")
     
    elif msg.text == "/info" or msg.text == "Помощь":
      bot.send_message(msg.chat.id, "команды для чата: \n/klik - заработок кликами \n/top - топ игроков \n/bal - ваш баланс \n/info - выводит команды бота\n/newname - смена имени\nИгра в рулетку:\nРул (ставка) (сумма ставки)\n /send - перевод коинов другому человеку,пример:\n/send 1000 (имя игрока в боте)")

bot.infinity_polling()