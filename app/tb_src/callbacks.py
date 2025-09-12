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

    bot.send_message(m.chat.id, m_texto("Muy bien, el tiempo de espera es de {} segundos".format(scrapper.delay)), reply_markup=telebot.types.ReplyKeyboardRemove())

    return





def set_pass(m, bot: telebot.TeleBot, scrapper):
    if m.text == "Cancelar Operación":
        bot.send_message(m.from_user.id, m_texto("Operación cancelada exitosamente"), reply_markup=telebot.types.ReplyKeyboardRemove())
        

    else:
        msg = bot.send_message(m.from_user.id, m_texto(
"""Muy bien, la contraseña ahora es: <code>{}</code>

A continuación, establece el tiempo de caducidad en el que volveré a estar cerrado al público

<u>Explicación</u>:
Está compuesto de 2 valores que son contados a partir de la fecha en la que se establece (osea luego de este mensaje al introducir la duración).

<b>Formato de tiempo</b>:
<code>(días)d(horas)h(minutos)m</code>

<b>Ejemplo</b>:
<code>3d4h0m</code>

En el ejemplo, la caducidad de la contraseña se establece a dentro de 3 días, 4 horas y 0 minutos para su vencimiento a partir del momento en el que se establece dicha duración

Si quiere que la contraseña no tenga tiempo de caducidad entonces presione en 'Cancelar Operacion'
""".format(m.text.strip().lower()), True), reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operacion"))
        
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
        if len(re.findall(r"\d+\D", m.text)) == 3 and (re.search(r"\d+[h]", m.text) and re.search(r"\d+[d]", m.text) and re.search(r"\d+[m]", m.text)):

            fecha = {"hora": int(re.search(r"\d+[h]", m.text).group().replace("h", "")), "dia" : int(re.search(r"\d+[d]", m.text).group().replace("d", "")) , "min" : int(re.search(r"\d+[m]", m.text).group().replace("m", ""))}

            scrapper.entrada.caducidad = time.time() + (fecha["hora"] * 60 * 60) + (fecha["dia"] * 24 * 60 * 60) + (fecha["min"] * 60)
            bot.send_message(m.chat.id, "Muy bien, faltan {} horas y {} minutos para que la contraseña caduque y bloquee el acceso a los usuarios".format(int((scrapper.entrada.caducidad - time.time())/60/60) , int((scrapper.entrada.caducidad - time.time()) /60 % 60)))

        else:

            msg = bot.send_message(m.chat.id, 
m_texto("""No has ingresado un formato adecuado!

<u>Explicación</u>:
Está compuesto de 2 valores que son contados a partir de la fecha en la que se establece (osea luego de este mensaje al introducir la duración).

<b>Formato de tiempo</b>:
<code>(días)d(horas)h(minutos)m</code>

<b>Ejemplo</b>:
<code>3d4h0m</code>

En el ejemplo, la caducidad de la contraseña se establece a dentro de 3 días, 4 horas y 0 minutos para su vencimiento a partir del momento en el que se establece dicha duración

Si quiere que la contraseña no tenga tiempo de caducidad entonces presione en 'Cancelar Operacion'""".format(m.text.strip().lower()), True),reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operacion"))

            bot.register_next_step_handler(msg, set_pass_timeout, bot)
    
    return



def recibir_cookies(c, bot, scrapper):

    bot.delete_message(c.message.chat.id, c.message.message_id)


    if scrapper.collection.find({"telegram_id": c.from_user.id}):
        with open(os.path.join(user_folder(c.from_user.id), "cookies.pkl"), "wb") as file:
            file.write(scrapper.collection.find_one({'_id': c.from_user.id})["cookies"])


    if os.path.isfile(os.path.join(user_folder(c.from_user.id), "cookies.pkl")):
        bot.send_document(c.message.chat.id, InputFile(os.path.join(user_folder(c.from_user.id), "cookies.pkl")), caption="Cookies del usuario <code>{}</code>".format(c.from_user.id))

        bot.send_message(c.from_user.id, m_texto("Cookies guardadas exitosamente :D"))

    
    else:
        bot.send_message(c.from_user.id, m_texto("Habrá ocurrido algo?\nNo pude enviar el archivo de cookies.pkl"))
        
    return

        
    
def cargar_cookies(c, bot, scrapper):

    bot.delete_message(c.message.chat.id, c.message.message_id)

    msg = bot.send_message(c.message.chat.id, "A continuacion, envíame el archivo de cookies.pkl")
    
    bot.register_next_step_handler(msg, cargar_cookies_get, bot, scrapper)

    return

def cargar_cookies_get(m: telebot.types.Message, bot, scrapper):

    if not m.document.file_name.endswith(".pkl"):
        bot.send_message(m.chat.id, "Operación Cancelada")
        return
    
    with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "wb") as file:
        file.write(bot.download_file(bot.get_file(m.document.file_id).file_path))
        
    if scrapper.collection.find({"telegram_id": m.from_user.id}):
        
        with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "rb") as file:
            scrapper.collection.update_one({"telegram_id": m.from_user.id}, {"$set" : {"cookies" : dill.load(file)["cookies"]}})

    
    bot.send_message(m.chat.id, "Cookies capturadas :)")
    
    return