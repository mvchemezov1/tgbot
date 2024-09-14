import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Замените TOKEN на Ваш токен бота
TOKEN = '7165285804:AAHqilK4Dg85YnAE95_81rLgFdNvyAPihms'

# Создание бота
bot = telebot.TeleBot(TOKEN)

# Словарь врачей и их расписание
doctors_slots = {}
doctors = {
    'Dr. Smith': ['10:00 - 12:00', '14:00 - 16:00'],
    'Dr. Johnson': ['09:00 - 11:00', '15:00 - 17:00'],
    'Dr. Williams': ['11:00 - 13:00', '17:00 - 19:00']
}

# Словарь пациентов
patients = {}


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text="Добро пожаловать в бот для записи к врачам!")
    show_menu(message)


# Обработчик команды /menu
@bot.message_handler(commands=['menu'])
def show_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    btn1 = telebot.types.KeyboardButton('Список врачей')
    btn2 = telebot.types.KeyboardButton('Записаться к врачу')
    btn3 = telebot.types.KeyboardButton('Список пациентов')
    btn4 = telebot.types.KeyboardButton('Добавить врача')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(chat_id=message.chat.id, text="Выберите действие:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('show_slots_'))
def show_slots(call):
    doctor = call.data.replace('show_slots_', '')
    slots = doctors[doctor]
    text = f"Доступные слоты для {doctor}:\n\n"
    for slot in slots:
        text += f"- {slot}\n"
    bot.send_message(chat_id=call.message.chat.id, text=text)


# Обработчик выбора "Список врачей"
@bot.message_handler(func=lambda message: message.text == 'Список врачей')
def show_doctors(message):
    markup = InlineKeyboardMarkup()
    for doctor, slots in doctors.items():
        btn = InlineKeyboardButton(f"{doctor} ({', '.join(slots)})", callback_data=f"show_slots_{doctor}")
        markup.add(btn)
    bot.send_message(chat_id=message.chat.id, text="Список врачей и их расписание:", reply_markup=markup)


# Обработчик выбора "Записаться к врачу"
@bot.message_handler(func=lambda message: message.text == 'Записаться к врачу')
def book_appointment(message):
    markup = InlineKeyboardMarkup()
    for doctor, slots in doctors.items():
        btn = InlineKeyboardButton(f"{doctor} ({', '.join(slots)})", callback_data=f"book_{doctor}")
        markup.add(btn)
    bot.send_message(chat_id=message.chat.id, text="Выберите врача:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('book_'))
def book_appointment_handler(call):
    doctor = call.data.replace('book_', '')
    bot.send_message(chat_id=call.message.chat.id, text=f"Вы выбрали {doctor}. Введите Ваше имя:")
    bot.register_next_step_handler(call.message, handle_patient_name, doctor)


def handle_doctor_selection(message):
    selected_doctor = message.text
    if selected_doctor in doctors:
        bot.send_message(chat_id=message.chat.id, text=f"Вы выбрали {selected_doctor}. Введите Ваше имя:")
        bot.register_next_step_handler(message, handle_patient_name, selected_doctor)
    else:
        bot.send_message(chat_id=message.chat.id, text="Извините, такого врача нет. Попробуйте еще раз.")
        book_appointment(message)


def handle_patient_name(message, selected_doctor):
    patient_name = message.text
    if patient_name in patients:
        bot.send_message(chat_id=message.chat.id, text="Извините, Вы уже записаны к врачу.")
        show_menu(message)
    else:
        available_slots = [slot for slot in doctors[selected_doctor] if
                           slot not in [appointment[1] for appointment in patients.values()]]
        if available_slots:
            markup = InlineKeyboardMarkup()
            for slot in available_slots:
                btn = InlineKeyboardButton(f"{slot}", callback_data=f"confirm_{selected_doctor}_{slot}_{patient_name}")
                markup.add(btn)
            bot.send_message(chat_id=message.chat.id, text=f"Доступные слоты для {selected_doctor}:\n\n",
                             reply_markup=markup)
        else:
            bot.send_message(chat_id=message.chat.id, text=f"Извините, у {selected_doctor} нет свободных слотов.")
        show_menu(message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def confirm_appointment(call):
    data = call.data.split('_')
    doctor = data[1]
    slot = data[2]
    patient_name = data[3]
    patients[patient_name] = (doctor, slot)
    bot.send_message(chat_id=call.message.chat.id, text=f"Вы успешно записаны к {doctor} на {slot}.")
    show_menu(call.message)


# Обработчик выбора "Список пациентов"
@bot.message_handler(func=lambda message: message.text == 'Список пациентов')
def show_patients(message):
    text = "Список пациентов:\n\n"
    for patient, (doctor, time) in patients.items():
        text += f"{patient} - {doctor} ({time})\n"
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(func=lambda message: message.text == 'Добавить врача')
def add_doctor(message):
    bot.send_message(chat_id=message.chat.id, text="Введите имя нового врача:")
    bot.register_next_step_handler(message, handle_new_doctor_name)


def handle_new_doctor_name(message):
    new_doctor_name = message.text
    if new_doctor_name in doctors:
        bot.send_message(chat_id=message.chat.id, text="Извините, такой врач уже существует.")
        show_menu(message)
    else:
        bot.send_message(chat_id=message.chat.id,
                         text=f"Введите доступные слоты для {new_doctor_name} (разделенные запятыми):")
        bot.register_next_step_handler(message, handle_new_doctor_slots, new_doctor_name)


def handle_new_doctor_slots(message, new_doctor_name):
    slots = message.text.split(',')
    doctors[new_doctor_name] = [slot.strip() for slot in slots]
    doctors_slots[new_doctor_name] = slots
    bot.send_message(chat_id=message.chat.id, text=f"Врач {new_doctor_name} успешно добавлен.")
    show_menu(message)


# Запуск бота
bot.polling()
