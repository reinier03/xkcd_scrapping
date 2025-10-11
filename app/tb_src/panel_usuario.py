import telebot
import sys
import os
import traceback
from .main_classes import *


def help_usuario(m, scrapper: scrapping):
    scrapper, scrapper.bot.send_message(m.chat.id,                      
"""
Hola {} ! :D

¿Te parece tedioso estar re publicando por TODOS tus grupos en Facebook?
No te preocupes, yo me encargo por ti ;)

<u><b>Lista de Comandos</b></u>:
<b>/help</b> - Para ver la ayuda que muestro ahora mismo

<b>/lista_planes</b> - Para ver TODOS los planes disponibles

<b>/info</b> - Para obtener más información de comenzar a publicar

<b>/publicaciones</b> - Administra tus publicaciones, crea nuevas , elimina o edita las que ya tienes

<b>/publicar</b> - ¡Comienza a publicar! :D

<b>/cancelar</b> - Para CANCELAR la operación y no publicar (esto solo funciona si estás publicando)

<b>/panel</b> - Para administrar tu información y tus PUBLICACIONES

<b>/sobre_mi</b> - Información sobre el bot y su creador

{}""".format(m.from_user.first_name,"<blockquote>Te quedan " + scrapper.entrada.get_caducidad(m.from_user.id, scrapper) + " para que expire el plan que contrataste</blockquote>" if not m.from_user.id in [scrapper.admin, scrapper.creador] else ""))


def definir_repiticion(c, scrapper: scrapping):

    msg = scrapper.bot.send_message(c.message.chat.id, "A continuación, establece un tiempo de espera luego de finalizada la publicación masiva para reiniciar el proceso en bucle\nIngresa el tiempo de repetición en HORAS\n\nSi solo deseas que no se repita y se publique solamente una vez en todos tus grupos pulsa en '<b>No Repetir</b>'\n\n{}".format("Actualmente tu tiempo de repetición es de: " + str(scrapper.entrada.obtener_usuario(c.from_user.id).plan.repetir) + " horas" if isinstance(scrapper.entrada.obtener_usuario(c.from_user.id).plan.repetir, int) and scrapper.entrada.obtener_usuario(c.from_user.id).plan.repetir != True else "Aún no has establecido un tiempo de repetición"), reply_markup=ReplyKeyboardMarkup(True, True).add("No Repetir"))


    scrapper.bot.register_next_step_handler(msg, set_repeticion, scrapper)


def set_repeticion(m, scrapper: scrapping):

    if m.text == "No Repetir":
        scrapper.entrada.obtener_usuario(m.from_user.id).plan.tiempo_repeticion = False
        scrapper.bot.send_message(m.chat.id, "Muy bien, las publicaciones se enviarán una única vez por todos los grupos")

    if re.search(r"\d", m.text):
        if re.search(r"\d[.,]\d", m.text):
            if "," in m.text:
                m.text.replace(",", ".")

            scrapper.entrada.obtener_usuario(m.from_user.id).plan.tiempo_repeticion = int(float(re.search(r"\d+[.]\d+", m.text).group()) * 60 * 60)

        else:
            
            scrapper.entrada.obtener_usuario(m.from_user.id).plan.tiempo_repeticion = int(m.text) * 60 * 60


        
        scrapper.bot.send_message(m.chat.id, "Muy bien, {} hora(s) y {} minuto(s) será el tiempo de espera para reiniciar la publicación masiva en la cuenta".format(int(scrapper.entrada.obtener_usuario(m.from_user.id).plan.tiempo_repeticion / 60 / 60), int(scrapper.entrada.obtener_usuario(m.from_user.id).plan.tiempo_repeticion / 60 % 60)), reply_markup=telebot.types.ReplyKeyboardRemove())

        scrapper.administrar_BD(user=m.from_user.id)



    else:
        msg = scrapper.bot.send_message(m_texto("ERROR No has introducido un tiempo específico\n\nA continuación, establece un tiempo de espera luego de finalizada la publicación masiva para volver a repetir el proceso en bucle\nIngresa el tiempo de repetición en HORAS\n\nSi solo deseas que no se repita y se publique solamente una vez en todos tus grupos pulsa en '<b>No Repetir</b>'"), reply_markup=ReplyKeyboardMarkup(True, True).add("No Repetir"))

        scrapper.bot.register_next_step_handler(msg, set_repeticion, scrapper)
    
    return


def opciones_publicaciones(user, scrapper: scrapping):
    bot = scrapper.bot

    scrapper.cargar_datos_usuario(user)

    if len(scrapper.entrada.obtener_usuario(user).publicaciones) == 0:
        scrapper.bot.send_message(user, "Lo siento pero ni siquiera tienes ninguna publicación creada :(\n\n👇 Agrega alguna 👇", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Agregar Publicación", callback_data="p/add")]]))

    else:
        if scrapper.cola["uso"] == user:
            bot.send_message(user, """
Hola {} :D
                             
Este es el panel para administrar las publicaciones que hago en facebook... Actualmente tienes {} publicacion(es)

<blockquote><b>Nota IMPORTANTE</b>:
Actualmente estoy PUBLICANDO, no puedes ni agregar ni ELIMINAR publicaciones hasta que no termine o hasta que canceles la operación (para cancelar envíame /cancelar)"</blockquote>

Entonces? Qué harás?
""".format(bot.get_chat(user).first_name, len(scrapper.entrada.obtener_usuario(user).publicaciones)).strip() if scrapper.entrada.usuarios else 0, reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Ver Publicaciones Creadas", callback_data="p/wl")],
                    [InlineKeyboardButton("❌ Limpiar", callback_data = "clear")]
                ]
            ))

        else:

            bot.send_message(user, """
Hola {} :D
                            
Este es el panel para administrar las publicaciones que hago en facebook... Actualmente tienes {} publicacion(es)

<blockquote>Nota:
Si quieres <b>Eliminar</b> alguna publicación primero debes de darle en "<b>Ver Publicaciones Creadas</b>" y entonces seleccionar alguna, luego te saldrá la opción de eliminar dicha publicación</blockquote>

Entonces? Qué harás?
""".format(bot.get_chat(user).first_name, len(scrapper.entrada.obtener_usuario(user).publicaciones)).strip() if scrapper.entrada.usuarios else 0, reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Agregar Publicación", callback_data="p/add")], 
                    [InlineKeyboardButton("Ver Publicaciones Creadas", callback_data="p/wl")],
                    [InlineKeyboardButton("❌ Limpiar", callback_data = "clear")]
                ]
            ))


    return

def limpiar_publicaciones_panel(c, bot: telebot.TeleBot):
    bot.delete_message(c.message.chat.id, c.message.message_id)
    return


def crear_publicacion_SetTitulo(m, scrapper, bot):
    if m.text == "Cancelar Operacion":
        bot.send_message(m.chat.id, "Muy bien, Operación de creación de Publicación cancelada")
        return

    msg = bot.send_message(m.chat.id, m_texto("Muy Bien, ahora introduce el texto de la publicación\n\nEste texto SI se verá en Facebook, es el texto que estará adjunto a la propia Publicación", True))


    bot.register_next_step_handler(msg, crear_publicacion_SetText, scrapper, bot, {"titulo": " ".join(m.text.strip().split()[:1]).replace(" ", "_")})

def crear_publicacion_SetText(m, scrapper, bot, diccionario_publicacion):
    if m.text == "Cancelar Operacion":
        bot.send_message(m.chat.id, "Muy bien, Operación de creación de Publicación cancelada")
        return
    
    diccionario_publicacion["texto"] = m.text.strip()

    msg = bot.send_message(m.chat.id, m_texto("A continuación, envíame UNA FOTO para la Publicación (por ahora, solo soportamos 1, a futuro incluiré más)\n\nSi no quieres que la Publicación solamente tenga el texto que enviaste oprime en el botón de '<b>Omitir Foto</b>'", True), reply_markup=ReplyKeyboardMarkup(True, True).add("Omitir Foto", "Cancelar Operacion", row_width=1))

    bot.register_next_step_handler(msg, crear_publicacion_SetTFoto, scrapper, bot, diccionario_publicacion)


def crear_publicacion_SetTFoto(m: telebot.types.Message, scrapper: scrapping, bot: telebot.TeleBot, diccionario_publicacion):

    if m.text == "Cancelar Operacion":
        bot.send_message(m.chat.id, "Muy bien, Operación de creación de Publicación cancelada")
        return

    
    diccionario_publicacion["fotos"] = []

    if m.text == "Omitir Foto":
        diccionario_publicacion["fotos"] = False


    if m.photo:

        with open(os.path.join(user_folder(m.from_user.id), diccionario_publicacion["titulo"] + "_" + str(m.from_user.id) + "_0.jpg"), "wb") as file:

            file.write(bot.download_file(bot.get_file(m.photo[-1].file_id).file_path))
            diccionario_publicacion["fotos"].append(file.name)


            
    scrapper.entrada.obtener_usuario(m.from_user.id).publicaciones.append(Publicacion(diccionario_publicacion["titulo"], diccionario_publicacion["texto"], m.from_user.id, diccionario_publicacion["fotos"]))

    bot.send_message(m.chat.id, "Muy bien!, TU Publicación es la siguiente:", reply_markup=telebot.types.ReplyKeyboardRemove())
    scrapper.entrada.obtener_usuario(m.from_user.id).publicaciones[-1].enviar(scrapper, m.chat.id)

    bot.send_message(m.chat.id, "Enviame /publicar para comenzar a llevar esta Publicación por todos tus grupos de Facebook 🙂")

    scrapper.administrar_BD(user=m.from_user.id)

    return

    