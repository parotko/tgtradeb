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
    "Sakura": "UQAweYdzulm9kpeNXJOrCD7JHq7sWSYQOG-r9YP5F-8NmYS3",
    "AIcramer": "UQBaIrIsmAxq7bnLxD5vaAZYZp2djYDhItNbFhK9cEB2Qvub",
    "HypeAI": "UQCRb-hZ5vFdNmC8TAYLRlHDSLegTVm_AVekwmfSHeM9efo0",
    "aiTON": "UQDPsYCeoUWpYLg14y7vfk-bHBVWygtJ9ZXUcBsLiYlYsR1j"
}


address_pattern = re.compile(r'^[U][A-Za-z0-9_-]{47}$')
pattern = re.compile(r"^(\d+),\s*(\d+),\s*([A-Za-z0-9_]*),\s*(\d+)$")

languages = {
    "ru": {
        "start": "Этот бот может торговать токенами в сети ТОН без вашего участия.\n\nИспользуется технология AI Agents. Вы можете проверить баланс своего кошелька командой /balance. Для трейдинга используйте команду /trade.",
        "trade_prompt": "Выберите одного из трейдеров:",
        "back": "Назад",
        "start_trade": "Начать торги",
        "balance": "Введите адрес кошелька после команды. Например: \n`/balance UQBaIrI2kdXR7afLx22kfA2RZos2jYDhItNbFhK9csk22kfW`",
        "trade_instructions": "Для старта агента нада указать *суму на которую будут вестись торги*(минимум 8ton + 2ton комисия для оплаты услуг), *время роботы агента*(минимум 8дней, макс -30), *стоп слово*(можно ввести после окончания 8 дней) которое прикратит роботу агента, *сума при которой агент прекращает роботу -15% от суми депозита*. \n \n \n*Для старта агента нада скинуть указаную суму (+2TON для оплаты бота )на адрес агента и указать в коментарии стоп слово(обезательно, иначе можно потерять агента). Бот подтвердить успешность транзакции и вы получете персоналную команду для отслеживания роботы агента. Рекомендуеть использовать* _Tonkeeper_ \n \n \nТеперь введите по шаблону 'сума для торгов, без учета комисии(просто число),время в днях(просто число),стоп слово(на английском), число процентов при котором будет остановка(мин 15, макс 100)' пример как должно выглядеть  \n*10, 9, Cheir, 15*",
        "trade_details": ("Сумма для торгов которую нада скинуть: {total_amount}  TON(с учетом комиссии)\n"
                "Время работы агента: {days} days\n"
                "Стоп слово: {stop_word}\n"
                "Процент для остановки: {stop_percentage}%\n\n"
                "Для старта агента нужно сбросить указанную сумму на адрес агента и указать в комментарии стоп слово "
                "(обязательно, иначе можно потерять деньги).\n"
                "Адрес агента: `{agent_address}`\n"
                "После транзакции подождите 3-5 мин и напишите боту 'ready' "),
        "transaction": ("Транзакция успешно подтверждена!"
                        "Сумма на торгах: {total_amount} TON\n"
                        "Вы можете написать боту ваше стоп слово: `{tx_comment}` после окончанию 8 суток\n"
                        "Вы можете отправить /stats, чтобы увидеть статистику"),
        "error1": "Не удалось найти соответствующую транзакцию.\n Убедитесь что вы отправили верное стоп слово и/или верную суму"
    },

    "en": {
        "start": "This bot can trade tokens on the TON network without your involvement.\n\nIt uses AI Agents technology. You can check your wallet balance using /balance. Use /trade to start trading.",
        "trade_prompt": "Choose one of the traders:",
        "back": "Back",
        "start_trade": "Start trading",
        "balance": "Enter your wallet address after the command. For example: \n`/balance UQBaIrI2kdXR7afLx22kfA2RZos2jYDhItNbFhK9csk22kfW`",
        "trade_instructions": "To start an agent, you need to indicate *the amount for which trading will be conducted* (minimum 8ton + 2ton commission for payment of services), *agent's working time* (minimum 8 days, max -30), *stop word* (can be entered after 8 days) which will terminate the agent's work, *the amount at which the agent terminates the work - 15% of the deposit amount*. \n \n \n*To start an agent, you need to drop the specified amount (+2TON to pay for the bot) to agent address and specify a stop word in the comment (required, otherwise you can lose the agent). The bot will confirm the success of the transaction and you will receive a personal command to track the agent's robot. It is recommended to use * _Tonkeeper_ \n \n \nNow enter the template 'amount for trading, excluding commission (just a number), time in days (just a number), stop word (in English), the number of percent at which there will be a stop (min 15, max 100)' an example of how it should look \n*10, 9, Cheir, 15*",
        "trade_details": (
                    "Trading amount to send: {total_amount} TON (including commission)\n"
                    "Agent runtime: {days} days\n"
                    "Stop word: {stop_word}\n"
                    "Stop percentage: {stop_percentage}%\n\n"
                    "To start the agent, send the specified amount to the agent's address and include the stop word in the comment "
                    "(mandatory, otherwise funds may be lost).\n"
                    "Agent address: `{agent_address}`\n"
                    "After the transaction, wait 3-5 minutes and send 'ready' to the bot."
                ),
        "transaction": ("Transaction successfully confirmed!"
                        "Amount at auction: {total_amount} TON\n"
                        "You can write your stop word to the bot: `{tx_comment}` after the end of 8 days\n"
                        "You can send /stats to see statistics"),
        "error1": "Unable to find matching transaction.\nPlease make sure you have sent the correct stop word and/or the correct amount."
    },
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("English", callback_data='lang_en'),
            InlineKeyboardButton("Русский язык", callback_data='lang_uk')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select your language:", reply_markup=reply_markup)
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'lang_en':
        context.user_data['language'] = 'en'
    elif query.data == 'lang_uk':
        context.user_data['language'] = 'ru'

    lang = context.user_data.get('language', 'en')
    text = languages[lang]['start']

    await query.edit_message_text(text)
async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('language', 'en')
    keyboard = [
        [
            InlineKeyboardButton("Sakura", callback_data='Sakura'),
            InlineKeyboardButton("AIcramer", callback_data='AIcramer')
        ],
        [
            InlineKeyboardButton("HypeAI", callback_data='HypeAI'),
            InlineKeyboardButton("aiTON", callback_data='aiTON')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(languages[lang]['trade_prompt'], reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  

    selected_option = query.data
    context.user_data['selected_agent'] = selected_option  

    # Текст на основі вибору
    if selected_option == 'Sakura':
        text = "Market Cap: $5,96M \nHolder Count: 411 \nLiquidit: $91,39K \nVollume: $8,52K"
    elif selected_option == 'AIcramer':
        text = "Market Cap: $3,52M \nHolder Count: 389 \nLiquidit: $50,23K \nVollume: $19,02K"
    elif selected_option == 'HypeAI':
        text = "Market Cap: $895,4K \nHolder Count: 459 \nLiquidit: $19,45K \nVollume: $20,9K"
    elif selected_option == 'aiTON':
        text = "Market Cap: $401,49K \nHolder Count: 239 \nLiquidit: $31,9K \nVollume: $4,52K"

    
    back_button = InlineKeyboardButton("back to list", callback_data='back_to_list')
    trade_button = InlineKeyboardButton("start trade", callback_data='start_trade')

    
    keyboard = [[trade_button],[back_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)


    
    await query.edit_message_text(text=text, reply_markup=reply_markup)




async def start_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = context.user_data.get('language', 'en')
    await query.answer()
    await query.edit_message_text(languages[lang]['trade_instructions'], parse_mode='Markdown')






async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = context.user_data.get('language', 'en')
    await query.answer()  

    
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
    await query.edit_message_text(languages[lang]['trade_prompt'], reply_markup=reply_markup)


async def get_wallet_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = ' '.join(context.args)
    if not wallet_address:
        lang = context.user_data.get('language', 'en')
        await update.message.reply_text(languages[lang]['balance'], parse_mode='Markdown')
        return

   
    if not address_pattern.match(wallet_address):
        await update.message.reply_text('Invalid TON address format. Make sure the address is correct..')
        return

    
    url = f'https://toncenter.com/api/v2/getAddressInformation?address={wallet_address}'
    try:
        response = requests.get(url)
        print(f"Request sent to {url}. Status code: {response.status_code}") 
        response.raise_for_status() 
        data = response.json()
        print("API Response:", data) 

        
        raw_balance = data.get('result', {}).get('balance', None)
        if raw_balance is None:
            await update.message.reply_text('Unable to retrieve balance. Please check if the address is correct.')
        else:
            
            balance_in_ton = int(raw_balance) / 10 ** 9
            await update.message.reply_text(f'Your wallet balance: {balance_in_ton} TON')

    except requests.exceptions.RequestException as e:
        print(f"Error while making request: {e}")
        await update.message.reply_text('An error occurred while requesting the server. Please try again later.')
    except Exception as e:
        print(f"Unexpected error: {e}")
        await update.message.reply_text('An unknown error has occurred. Please try again later..')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    lang = context.user_data.get('language', 'en')
    
    match_trade = re.match(pattern, user_message)

    if match_trade:
        
        amount = match_trade.group(1)  
        days = match_trade.group(2)  
        stop_word = match_trade.group(3)  
        stop_percentage = match_trade.group(4) 
        print(amount)
        
        if int(amount)>=0 and int(days) >= 8 and 15 <= int(stop_percentage) <= 100:
            context.user_data["amount"] = amount
            context.user_data["stop_word"] = stop_word
            if amount is None:
                await update.message.reply_text("An error occurred: the bid amount is not set.")
                return

            selected_agent = context.user_data.get('selected_agent')
            agent_address = agent_addresses.get(selected_agent, "Unknown address")
            context.user_data["agent_address"] = agent_address

            await update.message.reply_text(
                languages[lang]['trade_details'].format(
                    total_amount=int(amount) + 2,
                    days=days,
                    stop_word=stop_word,
                    stop_percentage=stop_percentage,
                    agent_address=agent_address
                ),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "Incorrect values.")

    elif user_message.lower() == "ready":
        amount = context.user_data.get("amount")
        if amount is None:
            await update.message.reply_text("Amount for trading not set. Please start the trading process again.")
            return
        
        agent_address = context.user_data.get("agent_address")
        expected_amount = int(amount) + 1.99
        expected_stop_word = context.user_data.get("stop_word")
        print(expected_amount)
        toncenter_api_url = "https://toncenter.com/api/v2/"
        toncenter_api_key = os.getenv("toncenter_api_key")

        try:

            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"https://toncenter.com/api/v2/getTransactions",
                        params={"address": agent_address, "limit": 10, "archival": "true"},
                        headers={"Authorization": f"Bearer {toncenter_api_key}"}

                ) as response:
                   
                    if response.status != 200:
                        raise Exception(f"The server responded with an error: {response.status}")

                 
                    try:
                        data = await response.json()  

                    except ValueError:
                        raise Exception(f"Invalid format of response from server: {await response.text()}")

                  
                    transactions = data.get("result", [])

                    for tx in transactions:
                        in_msg = tx.get("in_msg", {})
                        tx_comment = in_msg.get("message", "")
                        tx_value = in_msg.get("value", 0)
                        tx_amount = int(tx_value) / 10 ** 9 if tx_value != 0 else 0.0


                        if tx_comment == expected_stop_word and tx_amount == float(expected_amount):
                            await update.message.reply_text(languages[lang]['transaction'].format(
                                                            total_amount=int(tx_amount) + 2,
                                                            tx_comment = tx_comment
                                                            ),
                                                            parse_mode = 'Markdown'
                                                            )
                            
                            return

                    await update.message.reply_text(languages[lang]['error1'],
                                                            parse_mode = 'Markdown')
                    
                    return

        except Exception as e:
            await update.message.reply_text(f"Error verifying transaction: {e}")

    """else:
        # Інша обробка повідомлень
        await update.message.reply_text("Send 'ready' to check the transaction.")
"""


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('language', 'en')

   
    amount = context.user_data.get('amount')
    stop_word = context.user_data.get('stop_word')
    days = 7
    print(amount)
    print(stop_word)


    profit = float(amount) * 0.0565

  
    await update.message.reply_text(
        f"Balance: {amount} TON\n"
        f"Profit: +{profit} TON\n"
        f"Days: {days} days\n"
        f"Stop word: {stop_word}\n",
        parse_mode='Markdown'
    )
def main():

    
    application = Application.builder().token(TOKEN).build()

   
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", get_wallet_balance))
    application.add_handler(CommandHandler("trade", trade))
    application.add_handler(CommandHandler("stats", stats))

    application.add_handler(CallbackQueryHandler(button, pattern='^(Sakura|AIcramer|HypeAI|aiTON)$'))
    application.add_handler(CallbackQueryHandler(back_to_list, pattern='^back_to_list$'))
    application.add_handler(CallbackQueryHandler(start_trade, pattern='^start_trade'))
    application.add_handler(CallbackQueryHandler(set_language, pattern='^lang_.*$'))


    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


    
    application.run_polling()


if __name__ == '__main__':
    main()
