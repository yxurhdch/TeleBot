# bot.py
import telebot
import random
from telebot import types
from sql import add_user, get_user_id, get_user_words, add_word, delete_word, word_exists
from config_reader import config

bot = telebot.TeleBot(token=config.bot_token.get_secret_value())

MAIN_MENU = ["Добавить слово", "Удалить слово"]


def create_quiz_keyboard(options, include_menu=True):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for i in range(0, len(options), 2):
        if i + 1 < len(options):
            markup.row(options[i], options[i + 1])
        else:
            markup.row(options[i])

    if include_menu and MAIN_MENU:
        markup.row(*MAIN_MENU)

    return markup


@bot.message_handler(commands=['start'])
def handle_start(message):
    telegram_id = message.from_user.id
    user_id = add_user(telegram_id)  # Теперь add_user не создаёт дубликаты
    if user_id is None:
        bot.send_message(message.chat.id, "Произошла ошибка при регистрации. Попробуйте ещё раз.")
        return
    bot.send_message(
        message.chat.id,
        "Привет! Это бот для изучения английских слов. Давай начнем!"
    )
    start_quiz(message, user_id)


def start_quiz(message, user_id):
    words = get_user_words(user_id)
    if not words:
        bot.send_message(
            message.chat.id,
            "У вас пока нет слов в словаре. Давайте добавим первое слово!"
        )
        return ask_new_word(message, user_id)

    word = random.choice(words)
    correct_answer = word['ru_word']
    options = [correct_answer] + [
        w['ru_word'] for w in random.sample(
            [w for w in words if w['ru_word'] != correct_answer],
            min(3, len(words) - 1)
        )
    ]
    random.shuffle(options)

    markup = create_quiz_keyboard(options)
    bot.send_message(
        message.chat.id,
        f"Переведи слово: {word['en_word']}",
        reply_markup=markup
    )
    bot.register_next_step_handler(
        message,
        handle_quiz_answer,
        user_id,
        correct_answer
    )


def handle_quiz_answer(message, user_id, correct_answer):
    if message.text in MAIN_MENU:
        return handle_menu_choice(message, user_id)

    if message.text == correct_answer:
        answer = "Правильно! Отличная работа!"
    else:
        f"Неправильно. Правильный ответ: {correct_answer}"
    bot.send_message(message.chat.id, answer)
    start_quiz(message, user_id)


def handle_menu_choice(message, user_id):
    if message.text == "Добавить слово":
        ask_new_word(message, user_id)
    elif message.text == "Удалить слово":
        ask_delete_word(message, user_id)


def ask_new_word(message, user_id):
    bot.send_message(message.chat.id, "Введи слово на английском:")
    bot.register_next_step_handler(message, handle_english_word, user_id)


def handle_english_word(message, user_id):
    en_word = message.text.strip()
    bot.send_message(message.chat.id, "Введи перевод на русском:")
    bot.register_next_step_handler(message, handle_russian_word, user_id, en_word)


def handle_russian_word(message, user_id, en_word):
    ru_word = message.text.strip()
    if word_exists(user_id, en_word):
        bot.send_message(
            message.chat.id,
            f"Слово '{en_word}' уже есть в вашем словаре!"
        )
    elif add_word(user_id, en_word, ru_word):
        bot.send_message(
            message.chat.id,
            f"Слово '{en_word}' - '{ru_word}' добавлено!"
        )
    else:
        bot.send_message(
            message.chat.id,
            "Не удалось добавить слово. Попробуй еще раз!"
        )
    start_quiz(message, user_id)


def ask_delete_word(message, user_id):
    words = get_user_words(user_id)
    if not words:
        bot.send_message(
            message.chat.id,
            "Ваш словарь пуст!",
            reply_markup=create_quiz_keyboard([], False)
        )
        return start_quiz(message, user_id)

    markup = create_quiz_keyboard([w['en_word'] for w in words], False)
    bot.send_message(
        message.chat.id,
        "Выбери слово для удаления:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, handle_delete_word, user_id)


def handle_delete_word(message, user_id):
    en_word = message.text
    if delete_word(user_id, en_word):
        bot.send_message(
            message.chat.id,
            f"Слово '{en_word}' удалено!"
        )
    else:
        bot.send_message(
            message.chat.id,
            "Не удалось удалить слово!"
        )
    start_quiz(message, user_id)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    telegram_id = message.from_user.id
    user_id = get_user_id(telegram_id)
    if user_id:
        handle_menu_choice(message, user_id)


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)