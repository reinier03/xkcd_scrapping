import telebot
from telebot.types import *
from telebot.handler_backends import ContinueHandling
import os
import sys

import telebot.types
from tb_src.main_classes import *
from tb_src import panel_usuario, panel_admin


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tb_src.usefull_functions import *


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


def set_pass_timeout(m, bot, scrapper: scrapping):
    m.text = m.text.lower().strip()

    if m.text == "cancelar operacion":
        scrapper.entrada.obtener_usuario(m.from_user.id).plan.caducidad = False

        bot.send_message(m.chat.id, "Muy bien, la contraseña durará indefinidamente hasta que cambie estos valores nuevamente", reply_markup = ReplyKeyboardRemove())
        return

    if re.search(r"\d+", m.text):
        if len(re.findall(r"\d+\D", m.text)) == 3 and (re.search(r"\d+[h]", m.text) and re.search(r"\d+[d]", m.text) and re.search(r"\d+[m]", m.text)):

            fecha = {"hora": int(re.search(r"\d+[h]", m.text).group().replace("h", "")), "dia" : int(re.search(r"\d+[d]", m.text).group().replace("d", "")) , "min" : int(re.search(r"\d+[m]", m.text).group().replace("m", ""))}

            scrapper.entrada.obtener_usuario(m.from_user.id).plan.caducidad = time.time() + (fecha["hora"] * 60 * 60) + (fecha["dia"] * 24 * 60 * 60) + (fecha["min"] * 60)
            bot.send_message(m.chat.id, "Muy bien, faltan {} horas y {} minutos para que la contraseña caduque y bloquee el acceso a los usuarios".format(int((scrapper.entrada.obtener_usuario(m.from_user.id).plan.caducidad - time.time())/60/60) , int((scrapper.entrada.obtener_usuario(m.from_user.id).plan.caducidad - time.time()) /60 % 60)))

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



def recibir_cookies(c, bot):

    bot.delete_message(c.message.chat.id, c.message.message_id)


    # if scrapper.collection.find({"telegram_id": c.from_user.id}):
    #     with open(os.path.join(user_folder(c.from_user.id), "cookies.pkl"), "wb") as file:
    #         file.write(scrapper.collection.find_one({'_id': c.from_user.id})["cookies"])


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

    if scrapper.if_borrar_db():
        return False

    if not m.document.file_name.endswith(".pkl"):
        bot.send_message(m.chat.id, "Operación Cancelada")
        return
    
    with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "wb") as file:
        file.write(bot.download_file(bot.get_file(m.document.file_id).file_path))
        
    if scrapper.collection.find({"telegram_id": m.from_user.id}):
        
        with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "rb") as file:
            scrapper.collection.update_one({"telegram_id": m.from_user.id}, {"$set" : {"cookies" : dill.load(file)["cookies"]}})

    
    bot.send_message(m.chat.id, "Cookies capturadas :)")
    
    return True


def elegir_cuenta_publicar(c: telebot.types.CallbackQuery, scrapper: scrapping ,cantidad_cuentas_mostrar = 6):

    if c.data.startswith("p/c/e/p"):
        scrapper.temp_dict[c.from_user.id]["perfil_seleccionado"] = scrapper.entrada.obtener_usuario(c.from_user.id).obtener_perfiles()[int(re.search(r"\d+", c.data).group())]
        
        mensaje_elegir_publicacion(c.from_user.id, scrapper)

    elif c.data.startswith("p/c/e/b"):
        scrapper.bot.send_message(c.message.chat.id, "<u><b>Opciones disponibles</b></u>:\nDale a '<b>Elegir Perfil</b>' para elegir entre algunos de los que has introducido aquí para comenzar a publicar\n\nDale a '<b>Acceder con un perfil nuevo</b>' para acceder con una cuenta que no has puesto aquí anteriormente\n\nDale a '<b>Cancelar</b>' para cancelar la operación de publicación", reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔳 Elegir perfil", callback_data="p/c/e/w/0")], 
                [InlineKeyboardButton("🆕 Acceder con un perfil nuevo", callback_data="p/c/n")],
                [InlineKeyboardButton("❌ Cancelar Operación", callback_data="cancel")]
            ]))
        
    elif c.data.startswith("p/c/e/w"):

        markup=InlineKeyboardMarkup(row_width=1)

        for e, perfil in enumerate(scrapper.entrada.obtener_usuario(c.from_user.id).obtener_perfiles()):
            markup.add(InlineKeyboardButton(perfil, callback_data="p/c/e/p/{}".format(e)))
        
        markup.row_width = 1
        markup.row(
            InlineKeyboardButton("◀", callback_data="p/c/e/w{}".format(0 if int(re.search(r"\d+", c.data).group()) - cantidad_cuentas_mostrar < 0 else int(re.search(r"\d+", c.data).group()) - cantidad_cuentas_mostrar)),
            
            InlineKeyboardButton("▶", callback_data= "p/c/e/w{}".format(int(re.search(r"\d+", c.data).group()) + cantidad_cuentas_mostrar)),
            )

        markup.row(InlineKeyboardButton("🔙 Volver Atrás", callback_data="p/c/e/b"))
            

        scrapper.bot.send_message(c.from_user.id, "👇 Elige una de las siguientes cuentas con las que te has logueado para comenzar a publicar 👇", reply_markup=markup)

    return

    

def mensaje_elegir_publicacion(user, scrapper: scrapping):

    if len(scrapper.entrada.obtener_usuario(user).publicaciones) > 1:

        if isinstance(scrapper.entrada.obtener_usuario(user).plan.publicaciones, bool):
            if scrapper.entrada.obtener_usuario(user).plan.publicaciones == True:
                markup = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("⬛ Publicar TODAS", callback_data="publicar/all")], 
                    [InlineKeyboardButton("🔲 Seleccionar qué publicar", callback_data="publicar/seleccionar")],
                    [InlineKeyboardButton("❌ Cancelar Operación", callback_data="cancel")]
                ]
            )
                
        else:
            if len(scrapper.entrada.obtener_usuario(user).publicaciones) > scrapper.entrada.obtener_usuario(user).plan.publicaciones and not user != scrapper.creador and user != scrapper.admin:

                markup = InlineKeyboardMarkup(
                    [ 
                        [InlineKeyboardButton("🔲 Seleccionar qué publicar", callback_data="publicar/seleccionar")],
                        [InlineKeyboardButton("❌ Cancelar Operación", callback_data="cancel")]
                    ]
                )

            else:

                markup = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("⬛ Publicar TODAS", callback_data="publicar/all")], 
                        [InlineKeyboardButton("🔲 Seleccionar qué publicar", callback_data="publicar/seleccionar")],
                        [InlineKeyboardButton("❌ Cancelar Operación", callback_data="cancel")]
                    ]
                )

        scrapper.bot.send_message(user, "Muy bien, ahora dime, quieres que publique TODAS tus Publicaciones a la vez en cada grupo o prefieres seleccionar la que publicaré en todos tus grupos?\n\n(Tienes {} publicacion/es)".format(len(scrapper.entrada.obtener_usuario(user).publicaciones)), reply_markup = markup)

        # scrapper.bot.register_callback_query_handler(cual_publicar, lambda c: c.data in ["publicar/all", "publicar/seleccionar"])

    else:
        if scrapper.temp_dict[user].get("perfil_seleccionado"):
            scrapper.bot.send_message(user, m_texto("Al parecer tienes solamente la publicación:\n<blockquote>{}</blockquote>\n\nVoy a proceder a publicar solamente esa publicación por los grupos en facebook de <b>{}</b>").format(scrapper.entrada.obtener_usuario(user).publicaciones[0].titulo, scrapper.temp_dict[user]["perfil_seleccionado"]))

        else:
            scrapper.bot.send_message(user, m_texto("Al parecer tienes solamente la publicación:\n<blockquote>{}</blockquote>\n\nVoy a proceder a publicar solamente esa publicación por los grupos en facebook").format(scrapper.entrada.obtener_usuario(user).publicaciones[0].titulo))
        
        scrapper.temp_dict[user]["obj_publicacion"] = [scrapper.entrada.obtener_usuario(user).publicaciones[0]]

        threading.Thread(name="Hilo usuario: {}".format(user), target=scrapper.start_publish, args=(user,)).start()

    return



def manage_publicaciones(c: telebot.types.CallbackQuery, scrapper: scrapping, bot: telebot.TeleBot):
    
    if c.data.startswith("p/add"):
        msg = bot.send_message(c.from_user.id, m_texto("""
El primer paso para crear la Publicación es ponerle un título con el que será representado aquí en el bot

<b><u>Nota</u></b>:
El <b>máximo</b> de palabras para el título son 2, si pones más, el resto será omitido

<blockquote><b><u>Ejemplos de <i>Títulos de Publicación</i></u></b>:
                                                       
<b>Ejemplo 1</b> => <i>Venta Camisas</i>
<b>Ejemplo 2</b> => <i>Promocion Comida</i>
<b>Ejemplo 3</b> => <i>Celulares</i>
(etcétera, ponle algo descriptivo en 2 palabras o menos)</blockquote>


Esto solo será útil para referenciarlo más facilmente aquí, este título NO se mostrará en <b>Facebook</b> ni en ninguna otra parte
""".strip(), True), reply_markup=ReplyKeyboardMarkup(True).add("Cancelar Operacion"))

        bot.register_next_step_handler(msg, panel_usuario.crear_publicacion_SetTitulo, scrapper, bot)


    elif c.data.startswith("p/w"):
        cantidad_publicaciones_mostrar = 6

        if c.data.startswith("p/wl"):
            if re.search(r"\d+", c.data):
                if int(re.search(r"\d+", c.data).group()) <= 0:
                    try:
                        bot.answer_callback_query(c.id, "¡Ya estás en la primera publicación de la lista!")
                    except:
                        pass

                elif int(re.search(r"\d+", c.data).group()) >= len(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones):
                    try:
                        bot.answer_callback_query(c.id, "¡Ya estás en la última publicación de la lista!")
                    except:
                        pass

                else:
                    ver_lista_publicaciones(c, scrapper, bot, indice=int(re.search(r"\d+", c.data).group()))

            elif c.data == "p/wl/b":
                panel_usuario.opciones_publicaciones(c.from_user.id, scrapper)

            else:
                ver_lista_publicaciones(c, scrapper, bot, cantidad_publicaciones_mostrar = cantidad_publicaciones_mostrar)
        
        elif re.search(r"p/w/\d+", c.data):
            ver_publicacion(c, scrapper, bot, indice=int(re.search(r"\d+", c.data).group()), cantidad_publicaciones_mostrar = cantidad_publicaciones_mostrar)

    

        

    elif c.data.startswith("p/del"):

        if "conf" in c.data:

            if c.message.caption:
                bot.edit_message_caption(m_texto("Estás SEGURO/SEGURA que quieres borrar la Publicación <blockquote>{}</blockquote> ? ".format(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())].titulo)), c.message.chat.id, c.message.message_id , reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🚫 NO BORRAR!", callback_data=c.data.replace("conf", "no"))],
                        [InlineKeyboardButton("✅ Sí! Bórralo!", callback_data=c.data.replace("conf", "si"))]
                    ]   
                ))

            elif c.message.text:
                bot.edit_message_text(m_texto("Estás SEGURO/SEGURA que quieres borrar la Publicación <blockquote>{}</blockquote> ? ".format(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())].titulo)), c.message.chat.id, c.message.message_id , reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🚫 NO BORRAR!", callback_data=c.data.replace("conf", "no"))],
                        [InlineKeyboardButton("✅ Sí! Bórralo!", callback_data=c.data.replace("conf", "si"))]
                    ]   
                ))

        elif "no" in c.data:
            bot.edit_message_text(m_texto("Proceso de borrado de la publicación: <blockquote>{}</blockquote>\n\n<b>🚫 Cancelado correctamente</b>\n¡Ten más cuidado para la próxima!".format(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())].titulo)), c.message.chat.id, c.message.message_id)

        elif "si" in c.data:
            bot.delete_message(c.message.chat.id, c.message.message_id)
            bot.send_message(c.from_user.id, m_texto("La Publicación: <blockquote>{}</blockquote>\n\n<b>✅ Ha sido ELIMINADA correctamente</b>").format(scrapper.entrada.obtener_usuario(c.from_user.id).publicaciones[int(re.search(r"\d+", c.data).group())].titulo))

            scrapper.entrada.obtener_usuario(c.from_user.id).eliminar_publicacion(int(re.search(r"\d+", c.data).group()))

            scrapper.guardar_datos(c.from_user.id, False)

    return

