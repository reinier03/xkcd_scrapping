import telebot
import sys
import os
import traceback
from .main_classes import *



def definir_repiticion(c, scrapper: scrapping):

    msg = scrapper.bot.send_message(c.message.chat.id, "A continuación, establece un tiempo de espera luego de finalizada la publicación masiva para volver a repetir el proceso en bucle\nIngresa el tiempo de repetición en HORAS\n\nSi solo deseas que no se repita y se publique solamente una vez en todos tus grupos pulsa en '<b>No Repetir</b>'", reply_markup=ReplyKeyboardMarkup(True, True).add("No Repetir"))


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


        
        scrapper.bot.send_message(m.chat.id, "Muy bien, cada {} hora(s) y {} minuto(s) estaré difundiendo la publicación por todos los grupos de esta cuenta\n\nCuando quieras cancelar la difusión por los grupos envíame /cancelar\n\n<b>Comenzaré la publicación en breve...</b>".format(int(scrapper.entrada.obtener_usuario(m.from_user.id).plan.tiempo_repeticion / 60 / 60), int(scrapper.entrada.obtener_usuario(m.from_user.id).plan.tiempo_repeticion / 60 % 60)), reply_markup=telebot.types.ReplyKeyboardRemove())



    else:
        msg = scrapper.bot.send_message(m_texto("ERROR No has introducido un tiempo específico\n\nA continuación, establece un tiempo de espera luego de finalizada la publicación masiva para volver a repetir el proceso en bucle\nIngresa el tiempo de repetición en HORAS\n\nSi solo deseas que no se repita y se publique solamente una vez en todos tus grupos pulsa en '<b>No Repetir</b>'"), reply_markup=ReplyKeyboardMarkup(True, True).add("No Repetir"))

        scrapper.bot.register_next_step_handler(msg, set_repeticion, scrapper)
    
    return


def opciones_publicaciones(user, scrapper):
    bot = scrapper.bot

    if len(scrapper.entrada.obtener_usuario(user).publicaciones) == 0:
        scrapper.bot.send_message(user, "Lo siento pero ni siquiera tienes ninguna publicación creada :(\n\n👇 Agrega alguna 👇", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Agregar Publicación", callback_data="p/add")]]))

    else:
        bot.send_message(user, """
Hola @{} :D
Este es el panel para administrar las publicaciones que hago en facebook... Actualmente tienes {} publicaciones

Nota:
Si quieres <b>Eliminar</b> alguna publicación primero debes de darle en "<b>Ver Publicaciones Creadas</b>" y entonces seleccionar alguna, luego te saldrá la opción de eliminar dicha publicación

Entonces? Qué harás?
""".format(bot.get_chat(user).username, len(scrapper.entrada.obtener_usuario(user).publicaciones)).strip() if scrapper.entrada.usuarios else 0, reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Agregar Publicación", callback_data="p/add")], 
                [InlineKeyboardButton("Ver Publicaciones Creadas", callback_data="p/wl")],
            ]
        ))

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

    