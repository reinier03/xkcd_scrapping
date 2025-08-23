import telebot
from telebot.types import *
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src.usefull_functions import *


def set_delay(m, scrapper ,bot: telebot.TeleBot):
    if m.text == "Cancelar Operación":
        bot.send_message(m.chat.id, m_texto("Operación Cancelada Exitosamente"), reply_markup=telebot.types.ReplyKeyboardRemove())
        return

    if not m.text.isdigit():


        msg = bot.send_message(m.chat.id, m_texto("No has introducido un tiempo adecuado (en segundos númericos sin decimales)\nA continuación establece el tiempo de espera entre la publicación en cada grupo (En segundos)\n\nEl tiempo actual de espera es de {} segundos".format(scrapper.delay)), 
        reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))
        
        bot.register_next_step_handler(msg, set_delay, scrapper, bot)
        return

    scrapper.delay = int(m.text)

    bot.send_message(m.chat.id, m_texto("Muy bien, el tiempo de espera es de {} segundos".format(scrapper.delay)), reply_markp=telebot.types.ReplyKeyboardRemove())

    return





def set_pass(m, bot, scrapper):
    if m.text == "Cancelar Operación":
        bot.send_message(m.from_user.id, m_texto("Operación cancelada exitosamente"), reply_markup=telebot.types.ReplyKeyboardRemove())
        

    else:
        bot.send_message(m.from_user.id, m_texto("Muy bien, la contraseña ahora es: <code>{}</code>".format(m.text.strip().lower())), reply_markup=ReplyKeyboardRemove())
        scrapper.password = m.text.strip().lower()


    return
