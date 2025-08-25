import requests
import shutil
import os
import telebot
from telebot.types import *
import f_src
import sys
import dill
import re
from traceback import format_exc
import threading
from flask import Flask, request
import subprocess
from pymongo import MongoClient
from f_src import facebook_scrapper
from tb_src.usefull_functions import *
from tb_src.main_classes import scrapper as s
from tb_src.main_classes import *
from telebot.types import *
from tb_src import callbacks



"""
-------------------------------------------------------
Variables de Entorno a Definir:
-------------------------------------------------------
token = token del bot
admin = ID del administrador del bot
MONGO_URL = Enlace del cluster de MongoDB (Atlas)
webhook_url = Si esta variable es definida se usará el metodo webhook, sino pues se usara el método polling

Para dudas o sugerencias contactarme a https://t.me/mistakedelalaif
"""




# media_group_clases = {}
# usuarios = {}
## usuarios = {id_usuario_telegram : main_classes.Usuario()}

admin = int(os.environ["admin"])

if not "MONGO_URL" in os.environ:
    MONGO_URL = "mongodb://localhost:27017"
else:
    MONGO_URL = os.environ["MONGO_URL"]

cliente = MongoClient(MONGO_URL)
db = cliente["face"]
collection = db["usuarios"]
scrapper = s()
scrapper.admin = admin

telebot.apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(os.environ["token"], "html")

bot.set_my_commands([
    BotCommand("/start", "Información sobre el bot"),
    BotCommand("/cancelar", "Cancela el proceso actual"),
    BotCommand("/publicar", "Comienza a publicar"),
    BotCommand("/delete", "Cambiar de cuenta"),
    BotCommand("/panel", "Solo para administrador")

], BotCommandScopeAllPrivateChats())

bot.send_message(admin, "El bot de publicaciones de Facebook está listo :)")


# @bot.middleware_handler()
# def cmd_middleware(bot: telebot.TeleBot, update: telebot.types.Update):
#     return



@bot.message_handler(func=lambda message: not message.chat.type == "private")
def not_private(m):
    return

@bot.message_handler(func=lambda m: scrapper.password == True and m.chat.id != admin and m.from_user.id != scrapper.cola["uso"])
def cmd_bloqueado(m):
    bot.send_message(m.chat.id, m_texto("Lo siento tigre, por ahora mi acceso está restringido hasta que el administrador lo decida\n👇Si tienes alguna queja contáctalo👇\n\n@{}".format(bot.get_chat(admin).username)))

    return 

@bot.message_handler(func=lambda m: not m.from_user.id in scrapper.usuarios_permitidos and not admin == m.from_user.id and scrapper.password != False and m.from_user.id != scrapper.cola["uso"])
def not_admin(m : telebot.types.Message):
    global scrapper
    msg = bot.send_message(m.chat.id, m_texto("A continuación por favor introduce la contraseña para poder acceder a mis funciones\n(Esta contraseña normalmente la da @{})".format(bot.get_chat(scrapper.admin).username), True), reply_markup=ForceReply())

    bot.register_next_step_handler(msg, verify_pass)

    return

def verify_pass(m: telebot.types.Message):
    if m.text.strip().lower() == scrapper.password:
        scrapper.usuarios_permitidos.append(m.from_user.id)
        bot.send_message(m.chat.id, "✅Muy Bien, la contraseña es correcta :D\n\nHola {} en que puedo ayudarte?\nSi no estás muy seguro/a de como funciono por favor escribe: /start".format(m.from_user.full_name))

    else:
        bot.send_message(m.chat.id, "❌WUAGG! La contraseña es incorrecta\n\nHabla con @{} para ver si te la da".format(bot.get_chat(scrapper.admin).username))

    return



@bot.message_handler(commands=["start"])
def start(m):
    global scrapper

    bot.send_message(m.chat.id,                      
"""
HOLA :D
¿Te parece tedioso estar re publicando por TODOS tus grupos en Facebook?
No te preocupes, yo me encargo por ti ;)

<u>Lista de Comandos</u>:
<b>/info</b> - Para obtener más información de las publicaciones
<b>/crear</b> - Crear una publicación
<b>/delete</b> - Para cerrar la cuenta actual y poder hacer loguin con una diferente
<b>/cancelar</b> - Para CANCELAR la operación y no publicar (esto solo funciona si estás publicando)


Bot desarrollado por @mistakedelalaif, las dudas o quejas, ir a consultárselas a él
""")
    return




@bot.message_handler(commands=["cancelar"])
def cmd_cancelar(m):
    global scrapper

    if len(m.text.split()) > 1 and m.from_user.id == admin and m.text.split()[1].isdigit():
        if scrapper.cola["uso"] == int(m.text.split()[1]):
            if bot.get_chat(int(m.text.split()[1])):
                
                scrapper.temp_dict[int(m.text.split()[1])]["cancelar_forzoso"] = True

                bot.send_message(m.chat.id, m_texto("Muy Bien, Cancelaré la operación actual para ese usuario"))
                
                
            else:
                bot.send_message(m.from_user.id, m_texto("¡El usuario que ingresaste no existe!\n\nOperación Cancelada"))
        
        else:
            bot.send_message(m.chat.id, m_texto("Este usuario no está usando las publicaciones"))

    elif scrapper.cola.get("uso") == m.from_user.id:
        bot.send_message(m.chat.id, m_texto("Muy Bien, Cancelaré la operación actual tan pronto cómo sea posible..."))
        scrapper.temp_dict[m.from_user.id]["cancelar"] = True
        

    else:
        bot.send_message(m.from_user.id, m_texto("¡No tienes ningún proceso activo!"))

    return
    
@bot.message_handler(commands=["delete"])
def cmd_delete(m):
    global scrapper

    if not collection.find_one({"telegram_id": m.from_user.id}):
        bot.send_message(m.chat.id, m_texto("Ni siquiera me has usado aún!\n\nNo tengo datos tuyos los cuales restablecer\nEnviame /info para comenzar a usarme :D"))
        return
    
    msg = bot.send_message(m.chat.id, m_texto("La opción actual borrará la información que tengo de tu cuenta y tendrías que volver a ingresar todo desde cero nuevamente...\n\nEstás seguro que deseas hacerlo?", True), reply_markup=ReplyKeyboardMarkup(True, True).add("Si", "No"))
    

    bot.register_next_step_handler(msg, borrar_question)


def borrar_question(m):
    global scrapper

    if m.text.lower() == "si": 
        
        
        scrapper.driver.delete_all_cookies()
        
        try:
            collection.delete_one({"telegram_id": m.from_user.id})
        except:
            pass
        try:
            shutil.rmtree(user_folder(m.from_user.id))
        except:
            pass
        

        bot.send_message(m.chat.id, m_texto("Ya se ha borrado todo exitosamente :-("), reply_markup=ReplyKeyboardRemove())

    else:
        bot.send_message(m.chat.id, m_texto("Operación Cancelada con éxito :D"), reply_markup=ReplyKeyboardRemove())

    return


@bot.message_handler(commands=["cookies"])
def cmd_cookies(m):
    global scrapper
    msg = bot.send_message(m.chat.id, "A continuación envia el archivo cookies.pkl al que tienes acceso")
    bot.register_next_step_handler(msg, obtener_cookies)
    
    
def obtener_cookies(m):
    global scrapper
    if not m.document:
        bot.send_message(m.chat.id, "Operación Cancelada")
        return
    
    with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "wb") as file:
        file.write(bot.download_file(bot.get_file(m.document.file_id).file_path))
        
    if not collection.find({"telegram_id": m.from_user.id}):
        
        with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "rb") as file:
            collection.insert_one({"id_": time.time(), "telegram_id": m.from_user.id, "cookies" : dill.load(file)["cookies"]})
    
    bot.send_message(m.chat.id, "Cookies capturadas :)")
    
    return
            


@bot.message_handler(commands=["info"])
def cmd_publish(m):
    global scrapper
    
    
    
    bot.send_message(m.chat.id,
"""A continuación ve a Facebook y sigue estos pasos para compartir la publicacion
<blockquote>
1 - Selecciona la publicación
2 - Dale en el botón de '↪ Compartir'
3 - Luego en el menú que aparece dale a 'Obtener Enlace'
4 - Pega dicho enlace en el siguiente mensaje y envíamelo
</blockquote>

Ahora enviame el enlace de la publicación aquí y me ocuparé del resto ;)
""")
    
    return
    


def notificar(c):
    global scrapper

    bot.delete_message(c.message.chat.id, c.message.message_id)

    if c.data == "notify/si":
        if c.from_user.id in scrapper.cola["cola_usuarios"]:
            bot.send_message(c.from_user.id, "¡Ya estás entre los ususarios que voy a notificar!")
        else:
            scrapper.cola["cola_usuarios"].append(c.from_user.id)
            bot.send_message(c.from_user.id, m_texto("Muy bien, <b>te notificaré</b> cuando esté desocupado y puedas publicar...\n\nSi alguien más comienza a publicar antes que tú perderás la oportunidad y tendrás que volver a esperar, en resumen, ponte atento a este chat"))
    else:
        if c.from_user.id in scrapper.cola["cola_usuarios"]:
            scrapper.cola["cola_usuarios"].remove(c.from_user.id)

        bot.send_message(c.from_user.id, "Muy bien, <b>NO te notificaré</b> entonces")

    return


def call_notificar(c):
    global scrapper

    bot.delete_message(c.message.chat.id, c.message.message_id)
    
    scrapper.cola["cola_usuarios"].remove(c.from_user.id)
    bot.send_message(c.message.chat.id, "Muy bien, te dejaré de notificar")

    return




#--------------------OJO : Las siguientes lineas son para el futuro, si funciona-----------

# @bot.message_handler(commands=["crear"])
# def cmd_crear(m):
#     usuarios[m.from_user.id] = Usuario(m.from_user.id)

#     m = bot.send_message(m.chat.id, "Aquí podrás crear la publicación que quieres que se comparta en Facebook (en principio, será solo 1)\n\nA continuación de este mensaje, enviame el texto de la publicación o presiona en 'Sin texto' para no poner texto", reply_markup=ReplyKeyboardMarkup(True, True).add("Sin texto"))

#     bot.register_next_step_handler(m, crear_texto)

#     return


# def crear_texto(m: telebot.types.Message):
#     if not m.content_type == "text":
#         m = bot.send_message(m.chat.id, "No me envíes otra cosa que no sea el texto de la Publicación!\nVuelve a intentarlo\n\nnA continuación de este mensaje, enviame el texto de la publicación o presiona en 'Sin texto' para no poner texto", reply_markup=ReplyKeyboardMarkup(True, True).add("Sin texto", "Cancelar Operación"))

#         bot.register_next_step_handler(m, crear_texto)

#     elif m.text.lower() == "cancelar operación":
#         bot.send_message(m.chat.id, "Operación Cancelada", reply_markup=telebot.types.ReplyKeyboardRemove())

#     elif m.text.lower() == "sin texto":
#         m = bot.send_message(m.chat.id, "¡Muy bien, tu publicación no tendrá texto entonces!\n\nA continuación de este mensaje, enviame las FOTOS que quieres que tenga dicha publicación", reply_markup=telebot.types.ReplyKeyboardRemove())
    
#     else:
        

#         usuarios[m.from_user.id].publicaciones.append(Publicacion(usuarios[m.from_user.id].id))
#         usuarios[m.from_user.id].publicaciones[-1].texto = m.text

#         media_group_clases[m.from_user.id] = (MediaGroupCollector(usuarios[m.from_user.id].id, m.from_user.id))

#         bot.send_message(m.chat.id, "A continuación envía las fotos (o la foto) de la publicación que quieres compartir", reply_markup=telebot.types.ReplyKeyboardRemove())

#         return



# @bot.message_handler(content_types=["photo"])
# def photo_handler(m: telebot.types.Message):
#     if m.media_group_id and media_group_clases.get(m.from_user.id):
#         with media_group_clases.get(m.from_user.id) as user_media:
#             print("recibí una foto de: {}".format(user_media.telegram_id))
            
#             if user_media.timer:
#                 user_media.timer.close()

#             user_media.fotos.append(bot.get_file(m.photo[-1].file_id).file_path)
            
#             user_media.timer = threading.Timer(user_media.TIMEOUT, get_photos, (media_group_clases, user_media))
#             user_media.timer.start()
            
#     else:
#         return
    

# def get_photos(media_group_clases: dict, user_media: MediaGroupCollector):

#     if not os.path.isdir(os.path.join(user_folder(user_media.telegram_id), "publicaciones")):
#         os.mkdir(os.path.join(user_folder(user_media.telegram_id), "publicaciones"))

#     for foto in user_media.fotos:
#         with open(os.path.join(user_folder(user_media.telegram_id), "publicaciones" , "u-{}_i-{}.jpg").format(user_media.user_id, len(usuarios[user_media.telegram_id].publicaciones)), "wb") as foto:
            
#             foto.write(bot.download_file(foto))

#             usuarios[user_media.telegram_id].publicaciones[-1].adjuntos.append(os.path.join(user_folder(user_media.td:elegram_id), "publicaciones" , "u-{}_i-{}.jpg").format(user_media.user_id, len(usuarios[user_media.telegram_id].publicaciones)))

#             usuarios[user_media.telegram_id].publicaciones[-1].id_publicacion = len(usuarios[user_media.telegram_id].publicaciones)


#     del media_group_clases[user_media.telegram_id]

#     return

            
#--------------------------------------------------------------------------------------


@bot.message_handler(commands=["publicar"])
def get_work(m: telebot.types.Message):
    global scrapper

    if m.from_user.id == scrapper.cola.get("uso"):
        bot.send_message(m.chat.id, "¡No puedes tener más de una publicación activa!")
        return
    
    elif scrapper.cola.get("uso"):

        if not m.from_user.id in scrapper.cola["cola_usuarios"] and not m.from_user.id == scrapper.cola["uso"]:

            msg = bot.send_message(m.chat.id, "Al parecer alguien ya me está usando :(\nLo siento pero por ahora estoy ocupado\n\n<b>¿Quieres que te notifique cuando dejen de usarme?</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Si", callback_data="notify/si"), InlineKeyboardButton("No", callback_data="notify/no")]]))  

            bot.register_callback_query_handler(notificar, lambda c: c.data in ["notify/si", "notify/no"])
            return
        
        elif m.from_user.id in scrapper.cola["cola_usuarios"]:
            bot.send_message(m.chat.id, "¡Ya te dije que te iba a notificar cuando estuviera desocupado!")

            return


                 

    
    elif not scrapper.cola.get("uso"):            
        
        m.text = m.text.strip()
        scrapper.cola["uso"] = m.from_user.id
        scrapper.temp_dict[m.from_user.id] = {}

        #si el texto es "/publicar 3" 
        if len(m.text.split()) > 1:
            if m.text.split()[1].isdigit():
                scrapper.temp_dict[m.from_user.id]["contador"] = int(m.text.split()[1])

            if "-t" in m.text and m.from_user.id == admin:
                scrapper.temp_dict[m.from_user.id]["mostrar_tiempo_debug"] = True

        
        #cambiar
        
        if m.from_user.id in scrapper.cola["cola_usuarios"]:
            scrapper.cola["cola_usuarios"].remove(m.from_user.id)

        for i in scrapper.cola["cola_usuarios"]:
            try:
                bot.send_message(i, m_texto("Olvídalo :/\nYa me están usando nuevamente\n\n<b>Te volveré a avisar cuando esté desocupado</b>, pero debes de estar atento"), reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("No notificar más", callback_data="no_mas")]
                    ]
                ))

                bot.register_callback_query_handler(call_notificar, lambda call: call.data == "no_mas" and call.from_user.id == i)

            except:
                pass
        
        m = bot.send_message(m.chat.id, m_texto("Envíame a continuación el texto de la Publicación...", True), reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Cancelar Operacion"))

        bot.register_next_step_handler(m, get_work_texto)


def get_work_texto(m: telebot.types.Message):
    global scrapper
        
    if m.text == "Cancelar Operacion":
        liberar_cola(scrapper, m.from_user.id, bot)
        bot.send_message(m.chat.id, m_texto("Operación Cancelada :("), reply_markup = telebot.types.ReplyKeyboardRemove())

        return

    if not m.content_type == "text":
        bot.send_message(m.chat.id, m_texto("Mal! No has enviado texto...\n\nEnvíame a continuación el texto de la Publicación...", True), reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Cancelar Operacion"))

        bot.register_next_step_handler(m, get_work_texto)

        return
    
        

    scrapper.temp_dict[m.from_user.id]["texto_p"] = m.text.strip()

    m = bot.send_message(m.chat.id, m_texto("A continuación. envíame 1 foto para la publicación (Por ahora solo admitimos 1)\n\nSi solamente quieres enviar texto presiona en '<b>Omitir Foto</b>'", True),reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Omitir Foto", "Cancelar Operacion", row_width=1))


    bot.register_next_step_handler(m, get_work_foto)

    
def get_work_foto(m: telebot.types.Message):
    global scrapper

    if m.text == "Cancelar Operacion":
        liberar_cola(scrapper, m.from_user.id, bot)
        bot.send_message(m.chat.id, m_texto("Operación Cancelada :("), reply_markup = telebot.types.ReplyKeyboardRemove())
        return

    elif m.text == "Omitir Foto":
        scrapper.temp_dict[m.from_user.id]["foto_p"] = False
        
        bot.send_message(m.chat.id, m_texto("Muy bien, solamente enviaré el texto que me proporcionaste"), reply_markup=ReplyKeyboardRemove())
        

    elif m.photo:

        with open(os.path.join(user_folder(m.from_user.id) , "foto_publicacion.png"), "wb") as file:
            scrapper.temp_dict[m.from_user.id]["foto_p"] = os.path.join(user_folder(m.from_user.id) , "foto_publicacion.png")
            file.write(bot.download_file(bot.get_file(m.photo[-1].file_id).file_path))

    else:

        m = bot.send_message(m.chat.id, m_texto("¡Debes de enviarme una foto!\n\nA continuación. envíame 1 foto para la publicación (Por ahora solo admitimos 1)\n\nSi solamente quieres enviar texto presiona en '<b>Omitir Foto</b>'", True), reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Omitir Foto", "Cancelar Operacion", row_width=1))

        bot.register_next_step_handler(m, get_work_foto)
        return

    
    def start_publish():
        global scrapper

        try:
            try:
                facebook_scrapper.main(scrapper, bot, m.from_user.id)
            except Exception as err:
                scrapper.temp_dict[m.from_user.id]["res"] = str(format_exc())

                                    

                if "no" == str(err.args[0]):
                    pass
            
                
                else:
                    print("Ha ocurrido un error! Revisa el bot, te dará más detalles")

                    bot.send_photo(admin, telebot.types.InputFile(make_screenshoot(scrapper.driver, m.from_user.id)), caption="Captura de error del usuario: <code>{}</code>".format(m.from_user.id))

                    bot.send_message(m.chat.id, m_texto("Ha ocurrido un error inesperado...Le notificaré al administrador. <b>Tu operación ha sido cancelada</b> debido a esto, lamentamos las molestias\n👇Igualmente si tienes alguna duda, contacta con él👇\n\n@{}".format(bot.get_chat(admin).username)))

                    bot.send_message(admin, "Ha ocurrido un error inesperado! ID usuario: {}\n\n<blockquote expandable>".format(m.from_user.id) + str(scrapper.temp_dict[m.from_user.id]["res"]) + "</blockquote>")
            
            
                
            
                
                
        except:
            try:
                bot.send_message(admin, "Ha ocurrido un error inesperado! ID usuario: {}\n\n<blockquote expandable>".format(m.from_user.id) + scrapper.temp_dict[m.from_user.id]["res"] + "</blockquote>")
                
            except:
                try:
                    with open(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"), "w", encoding="utf-8") as file:
                        file.write("Ha ocurrido un error inesperado!\nID del usuario: {}\n\n{}".format(m.from_user.id, scrapper.temp_dict[m.from_user.id]["res"]))
                        
                    with open(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"), "r", encoding="utf-8") as file:
                        bot.send_document(m.from_user.id, telebot.types.InputFile(file, file_name="error_" + str(m.from_user.id) + ".txt"))
                        
                    os.remove(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"))
                    
                except Exception as e:
                    try:
                        bot.send_message(m.chat.id, "Ha ocurrido un error fatal, ID del usuario: {} <blockquote expandable>".format(m.from_user.id) + scrapper.temp_dict[m.from_user.id]["res"] + "</blockquote>")
                    except:
                        print("ERROR FATAL:\nHe perdido la conexion a telegram :(")
                        
                    
            
        if not scrapper.temp_dict[m.from_user.id].get("cancelar"):
            bot.send_message(m.chat.id, m_texto("La Operación ha finalizado"))

        

        if scrapper.temp_dict[m.from_user.id].get("mostrar_tiempo_debug"):
            
            scrapper.temp_dict[m.from_user.id]["res"] = "\n".join(scrapper.temp_dict[m.from_user.id]["tiempo_debug"])

            with open(os.path.join(user_folder(m.from_user.id), "tiempo_publicacion_" + str(m.from_user.id) + ".txt"), "w", encoding="utf-8") as file:
                file.write("Log de publicación\nID del usuario: {}\n\n{}".format(m.from_user.id, scrapper.temp_dict[m.from_user.id]["res"]))
                
            with open(os.path.join(user_folder(m.from_user.id), "tiempo_publicacion_" + str(m.from_user.id) + ".txt"), "r", encoding="utf-8") as file:
                bot.send_document(m.from_user.id, telebot.types.InputFile(file, file_name="tiempo_publicacion_" + str(m.from_user.id) + ".txt"))

        

        
        os.remove(os.path.join(user_folder(m.from_user.id), "tiempo_publicacion_" + str(m.from_user.id) + ".txt"))


        liberar_cola(scrapper, m.from_user.id, bot)

        return


    #arreglar a futuro    
    threading.Thread(name="Hilo usuario: {}".format(m.from_user.id), target=start_publish).start()

    # start_publish()

    return


@bot.message_handler(commands=["panel"])
def cmd_panel(m: telebot.types.Message):
    if not m.from_user.id == int(admin) and m.chat.type == "private":
        bot.send_message(m.chat.id, 
            "Lo siento ;D no tienes permiso para entrar aquí")
        return
    
    elif not m.from_user.id == int(admin) != m.chat.type == "private":
        return

    bot.send_message(m.chat.id, 
        "Bienvenido al panel de control <b>{}</b> que deseas hacer? :D".format(m.from_user.first_name), 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⌛ Cambiar la espera entre publicación", callback_data="c/d")],
            [InlineKeyboardButton("⛔ Administrar Entrada (contraseña)", callback_data="c/pass")],
            [InlineKeyboardButton("👀 Ver información", callback_data="c/w")],
            [InlineKeyboardButton("♻ Reiniciar Bot", callback_data="c/reload")]
            # [InlineKeyboardButton("👥 Administrar Usuarios", callback_data="c/u")]
        ]))

@bot.callback_query_handler(lambda c: c.data == "c/w")
def call_ver(c):

    bot.delete_message(c.message.chat.id, c.message.message_id)

    bot.send_message(c.from_user.id, "Qué deseas saber?", reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Ver Usuarios", callback_data="c/w/user")],
            [InlineKeyboardButton("Ver variables", callback_data= "c/w/vars")]
        ]
    ))

    bot.register_callback_query_handler(watch, lambda c: c.data.startswith("c/w"))

def watch(c):

    bot.delete_message(c.message.chat.id, c.message.message_id)

    if c.data == "c/w/user":
            

        if scrapper.password == True:
            bot.send_message(c.from_user.id, m_texto("Actualmente mi acceso está bloqueado, el único que me puede usar eres tú mirei"))

        elif scrapper.password:
            usuarios = "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n"
            for i in scrapper.usuarios_permitidos:
                if usuarios + "<b>ID</b>: <code>{i}</code> <b>username</b>: {}\n".format("▶ " if i == scrapper.cola["uso"] else "", i, ) > 4000:
                    bot.send_message(c.from_user.id, usuarios)
                    usuarios = ""

                usuarios += "{}<b>ID</b>: <code>{}</code> <b>username</b>: {}".format("▶ " if i == scrapper.cola["uso"] else "", i, "@" + str(bot.get_chat(i).username) if bot.get_chat(i).username else "None")

            if usuarios != "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n":
                bot.send_message(c.from_user.id, usuarios)

            else:
                bot.send_message(c.from_user.id, "No hay usuarios para mostrar\n\nAl parecer ninguno ha podido acceder")

        else:
            if not scrapper.cola["uso"]:
                bot.send_message(c.from_user.id, m_texto("Actualmente nadie me está usando :v"))

            else:
                bot.send_message(c.from_user.id, m_texto("<b>Actualmente cualquiera puede usarme...</b>\nUsuario usandome actualmente:\n\n▶ <b>ID</b>: <code>{}</code> <b>username</b>: {}".format(scrapper.cola["uso"], "@" + str(bot.get_chat(scrapper.cola["uso"]).username) if bot.get_chat(scrapper.cola["uso"]).username else "None")))

        return


    elif c.data == "c/w/vars":
        #el limite de envio de mensajes en telegram es de 4000 caracteres
        if len("\n".join(globals())) > 4000:
            for i in range(round(len("\n".join(globals())) / 4000)):
                bot.send_message(c.from_user.id, "\n".join(globals())[i*4000 : (i+1) * 4000])
        else:
            bot.send_message(c.from_user.id, "\n".join(globals()))


@bot.callback_query_handler(func=lambda c: c.data == "c/pass")
def cmd_delay(c):
    global scrapper

    bot.delete_message(c.message.chat.id, c.message.message_id)


    msg = bot.send_message(c.from_user.id, 
            """
Qué quieres hacer?
<u>Explicación</u>:

'Establecer Nueva Contraseña' - Cambiará la contraseña, todos los usuarios nuevos que entren tendrán que ingresar esta nueva contraseña, pero se mantendrán los que ya están. SI no tienes contraseña puesta, puedes ingresar una contraseña con esto""".format(scrapper.password), 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Establecer Nueva Contraseña", callback_data="c/pass/ch")],
        ]))
    
    if scrapper.password == False:
        bot.edit_message_text(msg.text + 
"""
                           
'Prohibir Entrada' - Prohibirá la entrada de TODOS, incluido de los usuarios que ya entraron con alguna anterior contaseña. 
NOTA IMPORTANTE: Si das en esta opción y en el futuro planeas dar acceso nuevamente, TODOS los usuarios deberán introducir la nueva contraseña pues todos los accesos se perderán                              

=><b>Actualmente estoy recibiendo las peticiones de TODOS los usuarios que entran</b>""",
        msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
            InlineKeyboardButton("Prohibir Entrada", callback_data="c/pass/r"), 
            InlineKeyboardButton("Cancelar Operacion", callback_data="c/pass/cancel"),
            row_width=1))


    elif scrapper.password == True:
        bot.edit_message_text(msg.text + """
                              
'Permitir Entrada' - Permitirá la entrada de TODOS los usuarios sin contraseña requerida
                              
=><b>Actualmente estoy bloqueando a TODOS los usuarios</b>""",
        msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(InlineKeyboardButton("Permitir Entrada", callback_data="c/pass/pass"),InlineKeyboardButton("Cancelar Operacion", callback_data="c/pass/cancel"), row_width=1))
        
    else:
        bot.edit_message_text(msg.text + 
"""

'<b>Prohibir Entrada</b>' - Prohibirá la entrada de TODOS, incluido de los usuarios que ya entraron con alguna anterior contaseña. 
NOTA IMPORTANTE: Si das en esta opción y en el futuro planeas dar acceso nuevamente, TODOS los usuarios deberán introducir la nueva contraseña pues todos los accesos se perderán       

'<b>Permitir Entrada</b>' - Permitirá la entrada de TODOS los usuarios sin contraseña requerida           

=><b>Actualmente los usuarios tienen que acceder con la contraseña, la cual es: <code>{}</code></b>""".format(scrapper.password)
                              , msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(InlineKeyboardButton("Prohibir Entrada", callback_data="c/pass/r"),
                                InlineKeyboardButton("Permitir Entrada", callback_data="c/pass/pass"), 
                                InlineKeyboardButton("Cancelar Operacion", callback_data="c/pass/cancel"), row_width=1))
        
    


    bot.register_callback_query_handler(modify_pass, 
        lambda c: c.data in ["c/pass/r", "c/pass/ch", "c/pass/cancel", "c/pass/watch", "c/pass/pass"])
        
    return

def modify_pass(c):
    global scrapper

    bot.delete_message(c.message.chat.id, c.message.message_id)

    if c.data == "c/pass/cancel":
        bot.send_message(c.from_user.id, 
            "Operación Cancelada exitosamente")
            

    elif c.data == "c/pass/ch":
        msg = bot.send_message(c.from_user.id, 
            m_texto("A continuación establece la contraseña para darle acceso a los usuarios que la introduzcan".format(scrapper.password), True), reply_markup=ForceReply())
        bot.register_next_step_handler(msg, callbacks.set_pass, bot, scrapper)

    elif c.data == "c/pass/pass":
        scrapper.password = False
        bot.send_message(c.from_user.id, 
            m_texto("La entrada libre ahora está disponible para TODOS los usuarios"))

    elif c.data == "c/pass/r":
        scrapper.password = True

        for i in scrapper.usuarios_permitidos:
            try:
                bot.send_message(i, m_texto("@{} ha bloqueado mi acceso, no podrás usarme más hasta nuevo aviso...\n\nContacta con él si tienes alguna queja".format(bot.get_chat(scrapper.admin).username)))
            except:
                pass
            
        scrapper.usuarios_permitidos.clear()
        scrapper.cola["cola_usuarios"].clear()
        
        bot.send_message(c.from_user.id, 
            m_texto("Los permisos de entrada han sido removidos exitosamente ahora ningún usuario tendrá permiso para entrar\nLos que ya tenían permiso tampoco podrán \n\nHASTA...que no cambies nuevamente la contraseña o permitas la entrada para todos"))
    return

@bot.callback_query_handler(func=lambda c: c.data == "c/d")
def cmd_delay(c):
    global scrapper
    
    bot.delete_message(c.message.chat.id, c.message.message_id)

    msg = bot.send_message(c.message.chat.id, 
        m_texto("A continuación establece el tiempo de espera entre la publicación en cada grupo (En segundos)\n\n"
        "El tiempo actual de espera es de {} segundos".format(scrapper.delay), True), 
        reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operacion"))
        
    bot.register_next_step_handler(msg, callbacks.set_delay, scrapper , bot)
    return

@bot.callback_query_handler(lambda c: c.data == "cancel")
def cancelar(c):

    

    bot.delete_message(c.message.chat.id, c.message.message_id)

    bot.send_message(c.message.chat.id, "Muy Bien, la operación ha sido exitosamente cancelada")
    return


@bot.callback_query_handler(func=lambda c: c.data == "c/reload")
def cmd_reload(c):

    bot.send_message(c.from_user.id, "Estás seguro de que deseas continuar?, Esta acción no se puede deshacer e interrumpirá todos los procesos activos", reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Si, Deseo reiniciar", callback_data="c/reload/s")],
            [InlineKeyboardButton("No, Cancela", callback_data="cancel")]
        ]
    , row_width=1))

    bot.register_callback_query_handler(reboot, lambda c: c.data == "c/reload/s")

def reboot(c):

    os.execv(os.execv(sys.executable, [sys.executable, '"' + __file__ + '"']))
    return


@bot.message_handler(func=lambda x: True)
def cmd_any(m):

    bot.send_message(m.chat.id, "Escribe /start, para recibir ayuda")
    
    # if m.text.lower() == "cancelar operacion" and scrapper.cola["uso"] == m.chat.id:
    #     liberar_cola(scrapper, m.from_user.id)

    #     bot.send_message("Operación Cancelada exitosamente por el handler")
    # else:
        

    return
    

app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def webhook():
    global dic_temp
    
    if request.method.lower() == "post":   
        
            
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            try:
                if "host" in update.message.text and update.message.chat.id in [admin, 1413725506]:
                    bot.send_message(update.message.chat.id, "El url del host es: <code>{}</code>".format(request.url))
                    
                    #en los host gratuitos, cuando pasa un tiempo de inactividad el servicio muere, entonces hago este GET a la url para que no muera  
                    if not list(filter(lambda i: i.name == "hilo_requests", threading.enumerate())):
                        
                        def hilo_requests():
                            while True:
                                requests.get(os.getenv("webhook_url"))
                                time.sleep(60)
                                

                        threading.Thread(target=hilo_requests, name="hilo_requests").start()

            except:
                pass
            
            bot.process_new_updates([update])       
    else:
        return "<a href='https://t.me/{}'>Contáctame</a>".format(bot.user.username)
        
    return "<a href='https://t.me/{}'>Contáctame</a>".format(bot.user.username)

@app.route("/healthz")
def check():
    return "200 OK"


def flask():
    if os.getenv("webhook_url"):
        bot.remove_webhook()
        time.sleep(2)
        bot.set_webhook(url=os.environ["webhook_url"])
    
    app.run(host="0.0.0.0", port=5000)


try:
    print("La dirección del servidor es:{}".format(request.host_url))
    
except:
    hilo_flask=threading.Thread(name="hilo_flask", target=flask)
    hilo_flask.start()
    
if not os.getenv("webhook_url"):
    bot.remove_webhook()
    time.sleep(2)
    bot.infinity_polling(timeout=80,)