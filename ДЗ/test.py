import telebot
from telebot import types
from models import *
from decimal import Decimal

initialize_database()

# Добавим валюты
usd = create_currency("USD")
eur = create_currency("EUR", exchange_rate=0.85)
rub = create_currency("RUB", exchange_rate=65)  # Пример с рублями

# Создадим аккаунты
petr = Account.create(name='Пётр', balance=1000, trader=False, currency=usd)
olga = Account.create(name='Ольга', balance=1200, trader=False, currency=usd)
grig = Account.create(name='Григорий', balance=1500,
                      trader=False, currency=eur)

bot = telebot.TeleBot('6966266455:AAHoz_2aDK7o040xkvLjDAY4zJ4cOJj5V0I')


# Словарь для хранения данных о переводе
transfer_data = {}


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Регистрация")
    btn2 = types.KeyboardButton("Список пользователей")
    btn3 = types.KeyboardButton("Перевести деньги")
    btn4 = types.KeyboardButton("Смена валюты")
    btn5 = types.KeyboardButton("История транзакций")
    markup.add(btn1, btn2, btn3, btn4, btn5)

    bot.send_message(message.from_user.id,
                     "Выберите опцию:", reply_markup=markup)


def register_user(user_id, name):
    # Проверяем, существует ли пользователь
    existing_account = Account.select().where(Account.user_id == user_id)
    if existing_account.exists():
        return "Вы уже зарегистрированы."
    else:
        # Добавляем нового пользователя с начальным балансом 100 USD
        usd_currency = Currency.get(Currency.code == "USD")
        Account.create(user_id=user_id, name=name, balance=100.0,
                       trader=False, currency=usd_currency)
        return "Регистрация успешно завершена!"


@bot.message_handler(func=lambda message: message.text == "Регистрация")
def ask_for_name(message):
    msg = bot.send_message(message.from_user.id,
                           "Введите ваше имя для регистрации:")
    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message):
    try:
        user_id = message.from_user.id
        name = message.text
        response = register_user(user_id, name)
        bot.send_message(message.from_user.id, response)
    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка.')


@bot.message_handler(func=lambda message: message.text == "Список пользователей")
def handle_user_list(message):
    accounts = Account.select()
    response = "Список всех пользователей:\n\n"
    for account in accounts:
        response += f"ID: {account.user_id}, Имя: {account.name}, Баланс: {account.balance: .2f} {account.currency.code}\n"
    bot.send_message(message.from_user.id, response)


@bot.message_handler(func=lambda message: message.text == "Перевести деньги")
def ask_recipient_id(message):
    msg = bot.send_message(
        message.from_user.id, "Введите ID пользователя, которому хотите перевести деньги:")
    bot.register_next_step_handler(msg, process_transfer_step)


def process_transfer_step(message):
    try:
        recipient_id = int(message.text)
        transfer_data[message.from_user.id] = {'recipient_id': recipient_id}
        msg = bot.send_message(message.from_user.id, 'Введите сумму перевода:')
        bot.register_next_step_handler(msg, process_amount_step)
    except ValueError:
        bot.send_message(message.from_user.id,
                         'Пожалуйста, введите корректный ID.')


def process_amount_step(message):
    try:
        amount = Decimal(message.text)
        sender_id = message.from_user.id
        recipient_id = transfer_data[sender_id]['recipient_id']

        # Извлечение объектов аккаунта из базы данных
        sender = Account.get_or_none(Account.user_id == sender_id)
        recipient = Account.get_or_none(Account.user_id == recipient_id)

        if sender is None or recipient is None:
            bot.send_message(message.from_user.id,
                             'Отправитель или получатель не найден.')
            return

        # Вызов функции перевода с объектами аккаунта
        transfer_money(sender, recipient, amount)
        bot.send_message(message.from_user.id, 'Перевод выполнен успешно.')
    except ValueError:
        bot.send_message(message.from_user.id,
                         'Пожалуйста, введите корректную сумму.')
    except Exception as e:
        bot.send_message(message.from_user.id, f'Произошла ошибка: {e}')


@bot.message_handler(func=lambda message: message.text == "Смена валюты")
def change_currency_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    currencies = Currency.select()
    for currency in currencies:
        markup.add(types.KeyboardButton(currency.code))
    markup.add(types.KeyboardButton("Вернуться назад"))
    bot.send_message(message.from_user.id,
                     "Выберите валюту:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in [currency.code for currency in Currency.select()])
def handle_currency_change(message):
    new_currency_code = message.text
    user_id = message.from_user.id
    account = Account.get_or_none(Account.user_id == user_id)

    if account:
        old_balance, old_currency_code = account.balance, account.currency.code
        new_currency = Currency.get(Currency.code == new_currency_code)
        account.balance = convert_currency(
            old_balance, account.currency, new_currency)
        account.currency = new_currency
        account.save()

        response = f"Ваш баланс был переведен из {old_balance: .2f} {old_currency_code} в {account.balance: .2f} {new_currency_code}."
        bot.send_message(user_id, response)
    else:
        bot.send_message(user_id, "Ваш аккаунт не найден.")

    start(message)  # Возвращаемся в основное меню


@bot.message_handler(func=lambda message: message.text == "Вернуться назад")
def back_to_main_menu(message):
    start(message)


def convert_currency(amount, from_currency, to_currency):
    return amount * (to_currency.exchange_rate / from_currency.exchange_rate)


@bot.message_handler(func=lambda message: message.text == "История транзакций")
def show_transaction_history(message):
    user_id = message.from_user.id
    account = Account.get_or_none(Account.user_id == user_id)
    if account:
        transactions = (Transaction
                        .select()
                        .join(TransactionHistory)
                        .where((Transaction.sender == account) | (Transaction.receiver == account))
                        .order_by(Transaction.timestamp.desc()))
        response = "Ваша история транзакций:\n"
        for transaction in transactions:
            history = TransactionHistory.get(
                TransactionHistory.transaction == transaction)
            direction = "отправлено" if transaction.sender == account else "получено"
            response += f"{direction} {transaction.amount: .2f} {transaction.currency} to/from {transaction.receiver.name if direction == 'отправлено' else transaction.sender.name} на {transaction.timestamp}, Заметка: {history.message}\n\n"

        bot.send_message(user_id, response)
    else:
        bot.send_message(user_id, "Ваш аккаунт не найден.")


bot.polling(none_stop=True, interval=0)
