from peewee import *
from datetime import datetime
import os
import shutil

db = SqliteDatabase('data.db')


class BaseModel(Model):
    class Meta:
        database = db


class Currency(BaseModel):
    code = CharField(unique=True)
    exchange_rate = DecimalField(max_digits=15, decimal_places=6, default=1.0)
    is_base_currency = BooleanField(default=False)


class Account(BaseModel):
    user_id = PrimaryKeyField()
    name = CharField()
    balance = DecimalField(max_digits=15, decimal_places=2)
    trader = BooleanField()
    currency = ForeignKeyField(Currency, backref="accounts")


class Transaction(BaseModel):
    sender = ForeignKeyField(
        Account, backref="sent_transactions", column_name='sender_id')
    receiver = ForeignKeyField(
        Account, backref="received_transactions", column_name='receiver_id')
    amount = DecimalField(max_digits=15, decimal_places=2)
    currency = CharField()
    timestamp = DateTimeField(default=datetime.now)


class TransferState(BaseModel):
    user_id = IntegerField(unique=True)  # ID пользователя в Telegram
    step = CharField()  # Текущий шаг (например, 'awaiting_receiver_id', 'awaiting_amount')
    receiver_id = IntegerField(null=True)  # ID получателя перевода
    amount = DecimalField(max_digits=15, decimal_places=2,
                          null=True)  # Сумма перевода


class TransactionHistory(BaseModel):
    transaction = ForeignKeyField(
        Transaction, backref="history", column_name='transaction_id')
    message = CharField()  # Описание транзакции (например, "Перевод от Петра к Ольге")


def initialize_database():
    db.connect()

    # Путь к текущей базе данных
    current_db_path = db.database
    # Путь к копии базы данных
    backup_db_path = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"

    # Создание копии базы данных
    if os.path.exists(current_db_path):
        shutil.copyfile(current_db_path, backup_db_path)
        print(f"База данных скопирована: {backup_db_path}")

    # Удаление и создание новых таблиц
    db.drop_tables([Account, Transaction, Currency,
                   TransactionHistory], safe=True)
    db.create_tables([Account, Transaction, Currency,
                     TransactionHistory], safe=True)

    print("База данных инициализирована.")


def convert_currency(amount, from_currency, to_currency):
    try:
        from_currency_obj = Currency.get(Currency.code == from_currency)
        to_currency_obj = Currency.get(Currency.code == to_currency)
    except DoesNotExist:
        print(f"Валюта не найдена.")
        return amount

    if from_currency_obj.is_base_currency:
        converted_amount = amount * to_currency_obj.exchange_rate
    elif to_currency_obj.is_base_currency:
        converted_amount = amount / from_currency_obj.exchange_rate
    else:
        converted_amount = amount * \
            (1 / from_currency_obj.exchange_rate) * to_currency_obj.exchange_rate

    return converted_amount


def transfer_money(sender, receiver, amount):
    if sender.balance >= amount:
        converted_amount = convert_currency(
            amount, sender.currency.code, receiver.currency.code)
        sender.balance -= amount
        receiver.balance += converted_amount
        sender.save()
        receiver.save()
        transaction = Transaction.create(
            sender=sender, receiver=receiver, amount=amount,  currency=sender.currency.code)
        TransactionHistory.create(
            transaction=transaction, message=f"Перевод от {sender.name} к {receiver.name}")
        print(
            f"Перевод {amount: .2f} {sender.currency.code} от {sender.name} к {receiver.name} выполнен успешно. ({converted_amount: .2f} {receiver.currency.code})")
    else:
        print("Недостаточно средств для выполнения перевода.")


def display_all_accounts():
    accounts = Account.select()
    print("Список всех аккаунтов:")
    for account in accounts:
        print(
            f"ID: {account.user_id}, Имя: {account.name}, Баланс: {account.balance: .2f} {account.currency.code}, Trader: {account.trader}")


def change_account_currency(account, new_currency):
    try:
        new_currency_obj = Currency.get(Currency.code == new_currency)
    except DoesNotExist:
        print(f"Валюта с кодом {new_currency} не найдена.")
        return

    if account.currency == new_currency_obj:
        print(f"Счет уже хранится в валюте {new_currency_obj.code}.")
        return

    converted_balance = convert_currency(
        account.balance, account.currency.code, new_currency_obj.code)

    account.balance = converted_balance
    account.currency = new_currency_obj
    account.save()

    print(
        f"Валюта счета успешно изменена на {new_currency_obj.code}. Новый баланс: {account.balance: .2f} {new_currency_obj.code}")


def create_currency(code, exchange_rate=1.0, is_base_currency=False):
    return Currency.create(code=code, exchange_rate=exchange_rate, is_base_currency=is_base_currency)


def display_transaction_history(account):
    print(f"История транзакций для аккаунта {account.name}:")
    transactions = Transaction.select().where(
        (Transaction.sender == account) | (Transaction.receiver == account)
    )
    for transaction in transactions:
        sender_name = transaction.sender.name if transaction.sender else "N/A"
        receiver_name = transaction.receiver.name if transaction.receiver else "N/A"
        history_entry = TransactionHistory.get(
            TransactionHistory.transaction == transaction)
        print(
            f"ID: {transaction.id}, Отправитель: {sender_name}, Сумма: {transaction.amount}, Описание: {history_entry.message}"
        )
