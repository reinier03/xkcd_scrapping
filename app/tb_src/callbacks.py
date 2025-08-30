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





def set_pass(m, bot: telebot.TeleBot, scrapper):
    if m.text == "Cancelar Operación":
        bot.send_message(m.from_user.id, m_texto("Operación cancelada exitosamente"), reply_markup=telebot.types.ReplyKeyboardRemove())
        

    else:
        msg = bot.send_message(m.from_user.id, m_texto(
"""Muy bien, la contraseña ahora es: <code>{}</code>

A continuación, establece el tiempo de caducidad en el que volveré a estar cerrado al público

<u>Explicación<u>:
Está compuesto de 2 valores que son contados a partir de la fecha en la que se establece (osea luego de este mensaje al introducir la duración).

<b>Formato de tiempo</b>:
<code>(horas)h(días)d</code>

<b>Ejemplo</b>:
<code>4h3d</code>


En el ejemplo, la caducidad de la contraseña se establece a dentro de 3 días y 4 horas para su vencimiento a partir del momento en el que se establece dicha duración


Si quiere que la contraseña no tenga tiempo de caducidad entonces presione en 'Cancelar Operacion'
""".format(m.text.strip().lower())), reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operacion"))
        
        scrapper.entrada.contrasena = m.text.strip().lower()

        bot.register_next_step_handler(msg, set_pass_timeout, bot, scrapper)

    return


def set_pass_timeout(m, bot, scrapper):
    m.text = m.text.lower().strip()

    if m.text == "cancelar operacion":
        scrapper.entrada.caducidad = False

        bot.send_message(m.chat.id, "Muy bien, la contraseña durará indefinidamente hasta que cambie estos valores nuevamente", reply_markup = ReplyKeyboardRemove())
        return

    if re.search(r"\d+", m.text):
        if len(re.findall(r"\d+\D", m.text)) == 2 and re.search(r"\d+[h]", m.text) and re.search(r"\d+[d]", m.text):

            fecha = {"hora": int(re.search(r"\d+[h]", m.text).group().replace("h", "")), "dia" : int(re.search(r"\d+[d]", m.text).group().replace("d", ""))}

            scrapper.entrada.caducidad = time.time() + (fecha["hora"] * 60 * 60) + (fecha["dia"] * 24 * 60 * 60)

            bot.send_message(m.chat.id, "Muy bien, faltan {} horas y {} minutos para que la contraseña caduque y bloquee el acceso a los usuarios".format((time.time() - scrapper.entrada.caducidad)/60/60 , (time.time() - scrapper.entrada.caducidad) /60 % 60))

        else:

            msg = bot.send_message(m.chat.id, 
"""No has ingresado un formato adecuado!

<u>Explicación<u>:
Está compuesto de 2 valores que son contados a partir de la fecha en la que se establece (osea luego de este mensaje al introducir la duración).

<b>Formato de tiempo</b>:
<code>(horas)h(días)d</code>

<b>Ejemplo</b>:
<code>4h3d</code>


En el ejemplo, la caducidad de la contraseña se establece a dentro de 3 días y 4 horas para su vencimiento a partir del momento en el que se establece dicha duración


Si quiere que la contraseña no tenga tiempo de caducidad entonces presione en 'Cancelar Operacion'""".format(m.text.strip().lower()),reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operacion"))

            bot.register_next_step_handler(msg, set_pass_timeout, bot)
    
    return