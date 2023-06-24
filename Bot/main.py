import time
import flask
import telebot
import requests
from telebot import types
from key import TOKEN, PAYMENTS_TOKEN
from flask import Flask, request, Response
from datetime import datetime


base_url = 'http://localhost:8080/'
available_time = [['10:00', '11:00'], ['11:00', '12:00'], ['15:00', '16:00'], ['16:00', '17:00']]
chosen_time = []
place_number = 0

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'OK'
    else:
        flask.abort(403)
    if request.method == 'POST':
        return Response('OK', status=200)
    else:
        return ' '


def main_menu() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Знайти паркомісце', callback_data='find_place'),
               types.InlineKeyboardButton('Мої замовлення', callback_data='orders'))
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Я чат бот проекту Park.inc')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Надіслати контакти', request_contact=True))
    bot.send_message(message.chat.id, 'Щоб продовжити, надішліть, будь ласка, свої контакти.'
                                      ' Вони нам потрібні, щоб зареєструвати вас у нашій системі', reply_markup=markup)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id,
                     'За допомогою цього бота ви можете знаходити за допомогою карти паркомісця та винаймати їх')


@bot.message_handler(content_types=['contact'])
def get_contact(message):
    bot.send_message(message.chat.id, 'Дякую! Контакти отримано', reply_markup=types.ReplyKeyboardRemove())
    requests.post(url=base_url + 'api/user')
    bot.send_message(message.chat.id, 'Напишіть свою адресу електроннної пошти (email)')
    bot.register_next_step_handler(message, message.contact.phone_number)


def get_email(message, phone_number):
    bot.send_message(message.chat.id, 'Дякую! Email отримано', reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(message.chat.id, 'Тепер напишіть пароль від вашого акаунту. '
                                      'Повідомлення, яке ви напишете, буде видалено одразу після його отримання')
    bot.register_next_step_handler(message, phone_number, message.text)


def get_password(message, phone_number, email):
    print(requests.post(url=base_url + 'api/user',
                        data={'first_name': message.from_user.first_name,
                              'middle_name': '',
                              'last_name': message.from_user.last_name,
                              'created_at': datetime.timestamp(datetime.now()),
                              'userByUserId': {'phone_number': phone_number,
                                               'email': email,
                                               'password': message.text}
                              }).text)
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    bot.send_message(message.chat.id, 'Дякую! Дані отримано!')
    bot.send_message(message.chat.id, 'Виберіть потрібну вам опцію', reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: True)
def inline_buttons(call):
    global place_number
    if call.data == 'find_place':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Виберіть потрібну вам опцію', reply_markup=None)
        bot.send_message(call.message.chat.id, 'Вам потрібно буде обрати паркомісце на карті',
                         reply_markup=types.ReplyKeyboardRemove())
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='Відкрити карту', web_app=types.WebAppInfo(
            'https://umap.openstreetmap.fr/uk-ua/map/map_758045#17')))
        bot.send_message(call.message.chat.id, 'Ось карта:',
                         reply_markup=markup)
        time.sleep(6)
        msg = bot.send_message(call.message.chat.id, 'Вже знайшли потрібне місце? Напишіть його номер')
        bot.register_next_step_handler(msg, choose_place)

    if call.data == 'orders':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Виберіть потрібну вам опцію', reply_markup=None)
        markup2 = types.InlineKeyboardMarkup()
        markup2.add(types.InlineKeyboardButton('Повернутися назад', callback_data='return'))
        if place_number == 0:
            bot.send_message(call.message.chat.id, 'У вас немає замовлень', reply_markup=markup2)
        else:
            bot.send_message(call.message.chat.id, 'Ось список ваших замовлень:')
            markup3 = types.InlineKeyboardMarkup(row_width=1)
            markup3.add(types.InlineKeyboardButton('Відкрити ворота', callback_data='open_gates'),
                        types.InlineKeyboardButton('Повернутися назад', callback_data='return'))
            bot.send_message(call.message.chat.id, f'Паркомісце {place_number}', reply_markup=markup3)

    if call.data == 'open_gates':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f'Паркомісце {place_number}')
        markup6 = types.InlineKeyboardMarkup()
        markup6.add(types.InlineKeyboardButton('Повернутися назад', callback_data='return'))
        bot.send_message(call.message.chat.id, 'Ворота відчинилися!', reply_markup=markup6)
        time.sleep(3)

    if call.data == 'return':
        bot.send_message(call.message.chat.id, 'Виберіть потрібну вам опцію', reply_markup=main_menu())
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Повернутися назад', reply_markup=None)


@bot.message_handler(content_types=['text'])
def choose_place_by_yourself(message):
    if message.text == 'Вибрати місце самостійно':
        bot.send_message(message.chat.id, 'Вам потрібно буде обрати паркомісце на карті',
                         reply_markup=types.ReplyKeyboardRemove())
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='Відкрити карту', web_app=types.WebAppInfo(
            'https://umap.openstreetmap.fr/uk-ua/map/map_758045#17')))
        bot.send_message(message.chat.id, 'Ось карта:',
                         reply_markup=markup)
        time.sleep(6)
        msg = bot.send_message(message.chat.id, 'Вже знайшли потрібне місце? Напишіть його номер')
        bot.register_next_step_handler(msg, choose_place)


def choose_place(message):
    global place_number, available_time
    place_number = int(message.text)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    for i in range(len(available_time)):
        markup.add(types.KeyboardButton(f'{available_time[i][0]}-{available_time[i][1]}'))
    msg = bot.send_message(message.chat.id, f'Виберіть час на який ви б хотіли винайняти паркомісце №{place_number}.',
                           reply_markup=markup)
    bot.register_next_step_handler(msg, choose_time)


def choose_time(message):
    time = str(message.text)
    if time != 'Перейти до оплати':
        global available_time, chosen_time
        markup = types.ReplyKeyboardMarkup(row_width=1)
        available_time_of_place = available_time
        available_time_of_place.remove([f'{time[0:5]}', f'{time[6:11]}'])
        chosen_time.append([f'{time[0:5]}', f'{time[6:11]}'])
        for i in range(len(available_time)):
            markup.add(types.KeyboardButton(f'{available_time_of_place[i][0]}-{available_time_of_place[i][1]}'))
        markup.add(types.KeyboardButton('Перейти до оплати'))
        msg = bot.send_message(message.chat.id, 'Виберіть всі потрібні вам години або перейдіть до оплати',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, choose_time)
    else:
        global place_number
        bot.send_message(message.chat.id, 'Ось список ваших замовлень:', reply_markup=types.ReplyKeyboardRemove())
        markup1 = types.InlineKeyboardMarkup(row_width=1)
        bot.send_message(message.chat.id, f'Паркомісце {place_number}', reply_markup=markup1)
        chosen_time_string = ''
        list_of_labels = []
        for i in chosen_time:
            list_of_labels.append(types.LabeledPrice(f'{i[0]}-{i[1]}', 1500))
            chosen_time_string = chosen_time_string + i[0] + '-' + i[1] + ';' + ' '
        bot.send_message(message.chat.id, f'{chosen_time_string}')
        bot.send_invoice(chat_id=message.chat.id, title='Оплата', description='Пройдіть оплату',
                         invoice_payload='payment',
                         provider_token=PAYMENTS_TOKEN, currency='UAH', start_parameter='test_bot',
                         prices=list_of_labels)


if __name__ == '__main__':
    app.run()
