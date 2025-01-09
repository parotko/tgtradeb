from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
import re
import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

agent_addresses = {
    "Sakura": "UQCIofRXbpcSD7vgZ8XWsFQpacaKOV-ORxYzxfKGP0lHwZjT",
    "AIcramer": "UQBaIrIsmAxq7bnLxD5vaAZYZp2djYDhItNbFhK9cEB2Qvub",
    "HypeAI": "UQCRb-hZ5vFdNmC8TAYLRlHDSLegTVm_AVekwmfSHeM9efo0",
    "aiTON": "UQDPsYCeoUWpYLg14y7vfk-bHBVWygtJ9ZXUcBsLiYlYsR1j"
}

# Регулярний вираз для перевірки правильності адреси TON
address_pattern = re.compile(r'^[U][A-Za-z0-9_-]{47}$')
pattern = re.compile(r"^(\d+),\s*(\d+),\s*([A-Za-z0-9_]+),\s*(\d+)$")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Этот бот может торговать токенами в сети ТОН без твоего участия. В боте используется технология Ai Agents, это агенты обученные в отдельной сфере трейдинга крипты. С вероятностью 71% бот умножит ваши активы. \n\n \nВы можете проверить баланс своего кошелька командой ( /balance + адрес в сети ton). \n\n \n Для трейдинга пропишыте команду /trade')


async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Створюємо список кнопок
    keyboard = [
        [
            InlineKeyboardButton("Sakura", callback_data='Sakura'),
            InlineKeyboardButton("AIcramer", callback_data='AIcramer'),
        ],
        [
            InlineKeyboardButton("HypeAI", callback_data='HypeAI'),
            InlineKeyboardButton("aiTON", callback_data='aiTON'),
        ]
    ]

    # Створюємо клавіатуру з кнопок
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Відправляємо повідомлення з клавіатурою
    await update.message.reply_text('Выберите одного из AI Agent traders:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Відповідаємо на натискання кнопки

    # Отримуємо callback_data, яке ми вказали для кожної кнопки
    selected_option = query.data
    context.user_data['selected_agent'] = selected_option  # Зберігаємо вибраного агента

    # Текст на основі вибору
    if selected_option == 'Sakura':
        text = "Market Cap: $5,96M \nHolder Count: 411 \nLiquidit: $91,39K \nVollume: $8,52K"
    elif selected_option == 'AIcramer':
        text = "Market Cap: $3,52M \nHolder Count: 389 \nLiquidit: $50,23K \nVollume: $19,02K"
    elif selected_option == 'HypeAI':
        text = "Market Cap: $895,4K \nHolder Count: 459 \nLiquidit: $19,45K \nVollume: $20,9K"
    elif selected_option == 'aiTON':
        text = "Market Cap: $401,49K \nHolder Count: 239 \nLiquidit: $31,9K \nVollume: $4,52K"

    # Кнопка для повернення до списку
    back_button = InlineKeyboardButton("Назад к списку", callback_data='back_to_list')
    trade_button = InlineKeyboardButton("trade", callback_data='start_trade')

    # Створюємо клавіатуру з кнопкою для повернення
    keyboard = [[trade_button],[back_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)


    # Редагуємо повідомлення, додаючи вибрану опцію та кнопку повернення
    await query.edit_message_text(text=text, reply_markup=reply_markup)




async def start_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Для старта агента нада указать *суму на которую будут вестись торги*(минимум 8ton + 2ton комисия для оплаты услуг), *время роботы агента*(минимум 8дней, макс -30), *стоп слово*(можно ввести после окончания 8 дней) которое прикратит роботу агента, *сума при которой агент прекращает роботу -15% от суми депозита*. \n \n \n*Для старта агента нада скинуть указаную суму (+2TON для оплаты бота )на адрес агента и указать в коментарии стоп слово(обезательно, иначе можно потерять агента). Бот подтвердить успешность транзакции и вы получете персоналную команду для отслеживания роботы агента. Рекомендуеть использовать* _Tonkeeper_ \n \n \nТеперь введите по шаблону 'сума для торгов, без учета комисии(просто число),время в днях(просто число),стоп слово(на английском), число процентов при котором будет остановка(мин 15, макс 100)' пример как должно выглядеть  \n*10, 9, Cheir, 15*", parse_mode='Markdown')





# Обробник для кнопки "Повернутися до списку"
async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Відповідаємо на натискання кнопки

    # Відправляємо знову основний список кнопок
    keyboard = [
        [
            InlineKeyboardButton("Sakura", callback_data='Sakura'),
            InlineKeyboardButton("AIcramer", callback_data='AIcramer'),
        ],
        [
            InlineKeyboardButton("HypeAI", callback_data='HypeAI'),
            InlineKeyboardButton("aiTON", callback_data='aiTON'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Выберите одного из AI Agent traders:', reply_markup=reply_markup)


async def get_wallet_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = ' '.join(context.args)

    if not wallet_address:
        await update.message.reply_text(f'Введите адрес кошелька после команды.Приклад: '
                                        f"`/balance UQBaIrI2kdXR7afLx22kfA2RZos2jYDhItNbFhK9csk22kfW`",
                                        parse_mode='Markdown')
        return

    # Перевірка, чи адреса відповідає правильному формату TON
    if not address_pattern.match(wallet_address):
        await update.message.reply_text('Неверный формат адреса TON. Убедитесь, что адрес правильный.')
        return

    # Запит до TON API для отримання балансу
    url = f'https://toncenter.com/api/v2/getAddressInformation?address={wallet_address}'
    try:
        response = requests.get(url)
        print(f"Request sent to {url}. Status code: {response.status_code}")  # Лог для перевірки запиту
        response.raise_for_status()  # Якщо статус не 200, викликається помилка
        data = response.json()
        print("API Response:", data)  # Логування відповіді API

        # Перевірка, чи є баланс у відповіді
        raw_balance = data.get('result', {}).get('balance', None)
        if raw_balance is None:
            await update.message.reply_text('Невозможно получить баланс. Проверьте правильность адреса.')
        else:
            # Переведення в основні одиниці TON
            balance_in_ton = int(raw_balance) / 10 ** 9
            await update.message.reply_text(f'Баланс вашего кошелька: {balance_in_ton} TON')

    except requests.exceptions.RequestException as e:
        print(f"Error while making request: {e}")
        await update.message.reply_text('Произошла ошибка при запросе к серверу. Попытайтесь еще раз позже.')
    except Exception as e:
        print(f"Unexpected error: {e}")
        await update.message.reply_text('Произошла неизвестная ошибка. Попытайтесь еще раз позже.')


# Обробка всіх текстових повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    # Перевіряємо, чи текст відповідає шаблону для трейдінгу
    match_trade = re.match(pattern, user_message)

    if match_trade:
        # Отримуємо значення з шаблону
        amount = match_trade.group(1)  # сума
        days = match_trade.group(2)  # час
        stop_word = match_trade.group(3)  # стоп слово
        stop_percentage = match_trade.group(4)  # відсоток

        # Перевірка значень (сума >= 10, час >= 8, відсоток <= 100)
        if int(amount)>=8 and int(days) >= 8 and 15 <= int(stop_percentage) <= 100:
            context.user_data["amount"] = amount
            context.user_data["stop_word"] = stop_word

            selected_agent = context.user_data.get('selected_agent')
            agent_address = agent_addresses.get(selected_agent, "Неизвестный адрес")
            context.user_data["agent_address"] = agent_address

            await update.message.reply_text(
                f"Сумма для торгов которую нада скинуть: {int(amount) + 2}  TON(с учетом комиссии)\n"
                f"Время работы агента: {days} days\n"
                f"Стоп слово: {stop_word}\n"
                f"Процент для остановки: {stop_percentage}%\n\n"
                f"Для старта агента нужно сбросить указанную сумму на адрес агента и указать в комментарии стоп слово "
                f"(обязательно, иначе можно потерять деньги).\n"
                f"Адрес агента: `{agent_address}`\n"
                f"После транзакции подождите 3-5 мин и напишите боту 'готово' ",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "Неверные значения.")

    elif user_message.lower() == "готово":
        # Отримуємо дані для перевірки транзакції
        agent_address = context.user_data.get("agent_address")
        expected_amount = int(context.user_data.get("amount")) + 2
        expected_stop_word = context.user_data.get("stop_word")

        toncenter_api_url = "https://toncenter.com/api/v2/"
        toncenter_api_key = os.getenv("toncenter_api_key") # Вставте свій API-ключ

        try:

            # Для асинхронних запитів потрібно використовувати aiohttp замість requests
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"https://toncenter.com/api/v2/getTransactions",
                        params={"address": agent_address, "limit": 10},
                        headers={"Authorization": f"Bearer {toncenter_api_key}"}

                ) as response:
                    # Перевірка статусу відповіді
                    if response.status != 200:
                        raise Exception(f"Сервер ответил с ошибкой: {response.status}")

                    # Перевірка формату відповіді
                    try:
                        data = await response.json()  # асинхронне отримання JSON

                    except ValueError:
                        raise Exception(f"Неверный формат ответа от сервера: {await response.text()}")

                    # Обробка транзакцій
                    transactions = data.get("result", [])

                    for tx in transactions:
                        in_msg = tx.get("in_msg", {})
                        tx_comment = in_msg.get("message", "")
                        tx_value = in_msg.get("value", 0)
                        tx_amount = int(tx_value) / 10 ** 9 if tx_value != 0 else 0.0

                        if tx_comment == expected_stop_word and tx_amount == float(expected_amount):
                            await update.message.reply_text(f"Транзакция успешно подтверждена!"
                                                            f"Сумма на торгах: {int(tx_amount) - 2} TON\n"                                                           
                                                            f"Вы можете написать боту ваше стоп слово: `{tx_comment}` после окончанию 8 суток\n",
                                                            parse_mode = 'Markdown'
                                                            )
                            # Транзакція знайдена
                            return

                    await update.message.reply_text(f"Не удалось найти соответствующую транзакцию."
                                                    f"Убедитесь что вы отправили верное стоп слово и/или верную суму")
                    # Якщо транзакції не знайдено
                    return

        except Exception as e:
            await update.message.reply_text(f"Ошибка при проверке транзакции: {e}")

    else:
        # Інша обробка повідомлень
        await update.message.reply_text("Напишите 'готово', чтобы проверить транзакцию.")


def main():

    # Створення додатку
    application = Application.builder().token(TOKEN).build()

    # Обробники команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", get_wallet_balance))
    application.add_handler(CommandHandler("trade", trade))

    application.add_handler(CallbackQueryHandler(button, pattern='^(Sakura|AIcramer|HypeAI|aiTON)$'))
    application.add_handler(CallbackQueryHandler(back_to_list, pattern='^back_to_list$'))
    application.add_handler(CallbackQueryHandler(start_trade, pattern='^start_trade'))

    # Обробка всіх текстових повідомлень
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()