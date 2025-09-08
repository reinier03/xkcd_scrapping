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

from f_src import facebook_scrapper
from tb_src.usefull_functions import *
from tb_src.usefull_functions import m_texto
from tb_src.main_classes import scrapping as scrapping
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



#------------------declaring main class--------------------------
scrapper = scrapping(False)
#--------------------------END------------------------------



# media_group_clases = {}
# usuarios = {}
## usuarios = {id_usuario_telegram : main_classes.Usuario()}

telebot.apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(os.environ["token"], parse_mode="html", disable_web_page_preview=True)
scrapper.bot = bot

#en caso de que haya pausado la sesión, se reestablece
reestablecer_BD(scrapper)
            

if not os.environ.get("admin") and not scrapper.env:
    env_vars(1413725506, bot, scrapper)

elif not os.environ.get("admin") and scrapper.env:
    for k, v in scrapper.env.items():
        os.environ[k] = v

admin = int(os.environ["admin"])
scrapper.admin = admin

bot.set_my_commands([
    BotCommand("/start", "Información sobre el bot"),
    BotCommand("/cancelar", "Cancela el proceso actual"),
    BotCommand("/publicar", "Comienza a publicar"),
    BotCommand("/cambiar", "Cambiar de cuenta"),
    BotCommand("/panel", "Panel de administrador")], 
    BotCommandScopeChat(admin))





bot.set_my_commands([
    BotCommand("/start", "Información sobre el bot"),
    BotCommand("/cancelar", "Cancela el proceso actual"),
    BotCommand("/publicar", "Comienza a publicar"),
    BotCommand("/cambiar", "Cambiar de cuenta"),

], BotCommandScopeAllPrivateChats())




#para evitar repeticion
comun_handlers = lambda m: m.chat.id != admin and m.from_user.id != scrapper.cola["uso"] and not m.from_user.id in scrapper.entrada.usuarios_permitidos


@bot.middleware_handler()
def cmd_middleware(bot: telebot.TeleBot, update: telebot.types.Update):
    global scrapper
    if scrapper.entrada.caducidad:
        if time.time() >= scrapper.entrada.caducidad:
            scrapper.entrada.limpiar_usuarios(scrapper, bot)
            if scrapper.cola["uso"]:
                scrapper.temp_dict[scrapper.cola["uso"]]["cancelar_forzoso"] = True
                
                if update.message:
                    liberar_cola(scrapper, update.message.from_user.id)

                elif update.callback_query:
                    liberar_cola(scrapper, update.callback_query.message.from_user.id)

    
            bot.send_message(admin, m_texto("El tiempo de vigencia de la contraseña ha caducado"))
    

    return

@bot.message_handler(func=lambda message: not message.chat.type == "private")
def not_private(m):
    return


@bot.message_handler(func=lambda m: not os.environ.get("admin") and m.chat.type == "private")
def cmd_set_variables(m):
    try:
        env_vars(1413725506, bot, scrapper)

    except:
        bot.send_message(m.chat.id, "👇Contacta con mi creador @{} para que te dé acceso a mi👇".format(bot.get(1413725506).username), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contactar 👨‍💻", "https://t.me/{}".format(bot.get_chat(1413725506).username))]]))

    return

@bot.message_handler(func=lambda m: scrapper.entrada.contrasena == True and comun_handlers(m))
def cmd_bloqueado(m):
    bot.send_message(m.chat.id, m_texto("Lo siento tigre, por ahora mi acceso está restringido hasta que el administrador lo decida\n👇Si tienes alguna queja contáctalo👇\n\n@{}".format(bot.get_chat(admin).username)))

    return 

@bot.message_handler(func=lambda m: isinstance(scrapper.entrada.contrasena, str) and comun_handlers(m))
def not_admin(m : telebot.types.Message):
    global scrapper

    if m.text.strip().lower() == scrapper.entrada.contrasena:
        scrapper.entrada.usuarios_permitidos.append(m.from_user.id)
        bot.send_message(m.chat.id, "✅Muy Bien, la contraseña es correcta :D\n\nHola {} en que puedo ayudarte?\nSi no estás muy seguro/a de como funciono por favor escribe: /start".format(m.from_user.full_name))

    else:
        msg = bot.send_message(m.chat.id, m_texto("A continuación por favor introduce la contraseña para poder acceder a mis funciones\n(Esta contraseña normalmente la da @{})".format(bot.get_chat(scrapper.admin).username), True), reply_markup=ForceReply())

        bot.register_next_step_handler(msg, verify_pass)

    return

def verify_pass(m: telebot.types.Message):
    global scrapper

    if m.text.strip().lower() == scrapper.entrada.contrasena:
        scrapper.entrada.usuarios_permitidos.append(m.from_user.id)
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
<b>/publicar</b> - Comienza a publicar
<b>/cancelar</b> - Para CANCELAR la operación y no publicar (esto solo funciona si estás publicando)
<b>/cambiar</b> - Para cerrar la cuenta actual y poder hacer loguin con una diferente



Bot desarrollado por @mistakedelalaif, las dudas o quejas, ir a consultárselas a él
""")
    return




@bot.message_handler(commands=["cancelar"])
def cmd_cancelar(m):
    global scrapper
    m.text = m.text.strip()

    if len(m.text.split()) > 1 and m.from_user.id == admin and m.text.split()[1].isdigit():
        if scrapper.cola["uso"] == int(m.text.split()[1]):
            if bot.get_chat(int(m.text.split()[1])):
                bot.send_message(m.chat.id, m_texto("Muy Bien, Cancelaré la operación actual para ese usuario"),  reply_markup=telebot.types.ReplyKeyboardRemove())

                scrapper.temp_dict[int(m.text.split()[1])]["cancelar_forzoso"] = True

                liberar_cola(scrapper, scrapper.cola["uso"], bot)

                # if not scrapper.temp_dict[scrapper.cola["uso"]].get("texto_r"):
                #     liberar_cola(scrapper, scrapper.cola["uso"], bot)
                
                
            else:
                bot.send_message(m.from_user.id, m_texto("¡El usuario que ingresaste no existe!\n\nOperación Cancelada"))
        
        else:
            bot.send_message(m.chat.id, m_texto("Este usuario no está usando las publicaciones"), reply_markup=telebot.types.ReplyKeyboardRemove())

    elif scrapper.cola.get("uso") == m.from_user.id:

        scrapper.temp_dict[m.from_user.id]["cancelar"] = True

        # if not scrapper.temp_dict[scrapper.cola["uso"]].get("texto_r"):
        #     liberar_cola(scrapper, scrapper.cola["uso"], bot)

        liberar_cola(scrapper, scrapper.cola["uso"], bot)
        

    else:
        bot.send_message(m.from_user.id, m_texto("¡No tienes ningún proceso activo!"), reply_markup=telebot.types.ReplyKeyboardRemove())

    return
    
@bot.message_handler(commands=["cambiar"])
def cmd_delete(m):
    global scrapper

    if not scrapper.collection.find_one({"telegram_id": m.from_user.id}):
        bot.send_message(m.chat.id, m_texto("Ni siquiera me has usado aún!\n\nNo tengo datos tuyos los cuales restablecer\nEnviame /info para comenzar a usarme :D"))
        return


    
    msg = bot.send_message(m.chat.id, m_texto("La opción actual borrará la información que tengo de tu cuenta y tendrías que volver a ingresar todo desde cero nuevamente...\n\nEstás seguro que deseas hacerlo?", True), reply_markup=ReplyKeyboardMarkup(True, True).add("Si", "No"))
    

    bot.register_next_step_handler(msg, borrar_question)


def borrar_question(m):
    global scrapper

    if m.text.lower() == "si": 
        
        
        scrapper.driver.delete_all_cookies()
        
        try:
            scrapper.collection.delete_one({"telegram_id": m.from_user.id})
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
        
    if not scrapper.collection.find({"telegram_id": m.from_user.id}):
        
        with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "rb") as file:
            scrapper.collection.insert_one({"_id": time.time(), "telegram_id": m.from_user.id, "cookies" : dill.load(file)["cookies"]})
    
    bot.send_message(m.chat.id, "Cookies capturadas :)")
    
    return
            


@bot.message_handler(commands=["info"])
def cmd_publish(m):
    global scrapper
    
    
    
    bot.send_message(m.chat.id,
"""
A continuación sigue estos pasos para compartir una publicación en Facebook:

<blockquote>1 - Envíame /publicar
2 - Luego de requerirtelo, envíame un texto para la publicación
3 - (Opcional, lo puedes omitir) Luego de requerirtelo, envia una foto que ira adjunta en la publicación (actualmente solo soportamos 1, pero en versiones futuras intentaré incluir más) 
4 - Introduce tu usuario y luego la contraseña de facebook. Si tienes la doble autenticación configurada (o también llamado : <b>2FA</b>) tambien deberás ingresar los codigos de respaldo.
5 - A continuación, si la cuenta con la que te logueaste tiene varios perfiles entonces deberás seleccionar con cual de todos tus perfiles publicarás
6 - (Opcional, lo puedes omitir) Luego puedes seleccionar si quieres que la publicación se vuelva a publicar en todos tus grupos de nuevo luego de un tiempo de espera. Si es lo que quieres debes definir el tiempo en HORAS o simplemente darle en 'No repetir' para que solamente se publique 1 vez
7 - Disfrutar de tu día mientras yo me encargo de publicar :D</blockquote>

{}
""".format("<b>Quedan {} hora(s) y {} minuto(s) para que me uses</b>, luego de eso estaré bloqueado".format( int((scrapper.entrada.caducidad - time.time() ) / 60 / 60), int((scrapper.entrada.caducidad - time.time() ) / 60 % 60) ) if isinstance(scrapper.entrada.caducidad, (float, int)) else "").strip())
    
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
        bot.send_message(m.chat.id, m_texto("¡No puedes tener más de una publicación activa!\n\nEscribe /cancelar para cancelar el proceso"))
        return
    
    elif scrapper.cola.get("uso"):

        if not m.from_user.id in scrapper.cola["cola_usuarios"] and not m.from_user.id == scrapper.cola["uso"]:

            bot.send_message(m.chat.id, "Al parecer alguien ya me está usando :(\nLo siento pero por ahora estoy ocupado\n\n<b>¿Quieres que te notifique cuando dejen de usarme?</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Si", callback_data="notify/si"), InlineKeyboardButton("No", callback_data="notify/no")]]))  

            bot.register_callback_query_handler(notificar, lambda c: c.data in ["notify/si", "notify/no"])
            return
        
        elif m.from_user.id in scrapper.cola["cola_usuarios"]:
            bot.send_message(m.chat.id, "¡Ya te dije que te iba a notificar cuando estuviera desocupado!")

            return


                 

    
    elif not scrapper.cola.get("uso"):            
        
        m.text = m.text.strip()
        scrapper.cola["uso"] = m.from_user.id
        scrapper.temp_dict[m.from_user.id] = {}

        scrapper.cola = scrapper.cola
        scrapper.temp_dict = scrapper.temp_dict

        #si el texto es "/publicar 3" 
        if len(m.text.split()) > 1:
            if re.search(r"\d+", m.text):
                scrapper.temp_dict[m.from_user.id]["contador"] = int(re.search(r"\d+", m.text).group()) -1 if not int(re.search(r"\d+", m.text).group()) < 0 else 0

            if "-t" in m.text and m.from_user.id == admin:
                scrapper.temp_dict[m.from_user.id]["mostrar_tiempo_debug"] = True

            else:
                scrapper.temp_dict[m.from_user.id]["mostrar_tiempo_debug"] = False

        
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
        
        
        msg = bot.send_message(m.chat.id, m_texto("Envíame a continuación el texto de la Publicación...", True), reply_markup = ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))


        bot.register_next_step_handler(msg, get_work_texto)

    return


def get_work_texto(m: telebot.types.Message):
    global scrapper

    if not m.from_user.id == scrapper.cola["uso"]:
        return

    if m.text == "Cancelar Operación":
        bot.send_message(m.chat.id, "Muy bien, la operación ha sido cancelada", reply_markup=ReplyKeyboardRemove())
        breakpoint()
        liberar_cola(scrapper, m.from_user.id, bot)
        return
        
    if not m.content_type == "text":
        msg = bot.send_message(m.chat.id, m_texto("Mal! No has enviado texto...\n\nEnvíame a continuación el texto de la Publicación...", True))

        bot.register_next_step_handler(msg, get_work_texto)

        return
    
        
    else:
        scrapper.temp_dict[m.from_user.id]["texto_p"] = m.text.strip()

        m = bot.send_message(m.chat.id, m_texto("A continuación. envíame 1 foto para la publicación (Por ahora solo admitimos 1)\n\nSi solamente quieres enviar texto presiona en '<b>Omitir Foto</b>'", True),reply_markup = ReplyKeyboardMarkup(True, True).add("Omitir Foto", "Cancelar Operación", row_width=1))

        bot.register_next_step_handler(m, get_work_foto)

    return

    
def get_work_foto(m):
    global scrapper

    if not m.from_user.id == scrapper.cola["uso"]:
        return

    if m.text == "Cancelar Operación":
        bot.send_message(m.chat.id, "Muy bien, la operación ha sido cancelada", reply_markup=ReplyKeyboardRemove())
        liberar_cola(scrapper, m.from_user.id, bot)
        return

    elif m.text == "Omitir Foto":
        scrapper.temp_dict[m.from_user.id]["foto_p"] = False


    elif m.photo:

        with open(os.path.join(user_folder(m.from_user.id) , "foto_publicacion.png"), "wb") as file:
            file.write(bot.download_file(bot.get_file(m.photo[-1].file_id).file_path))

        with open(os.path.join(user_folder(m.from_user.id) , "foto_publicacion.png"), "rb") as file:
            scrapper.temp_dict[m.from_user.id]["foto_p"] = os.path.join(user_folder(m.from_user.id) , "foto_publicacion.png")


    else:

        m = bot.send_message(m.chat.id, m_texto("¡Debes de enviarme una foto!\n\nA continuación. envíame 1 foto para la publicación (Por ahora solo admitimos 1)\n\nSi solamente quieres enviar texto presiona en '<b>Omitir Foto</b>'", True), reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Omitir Foto", "Cancelar Operacion", row_width=1))

        bot.register_next_step_handler(m, get_work_foto)
        return

    

    

    
    

    #arreglar a futuro    
    threading.Thread(name="Hilo usuario: {}".format(m.from_user.id), target=start_publish, args=(bot, m.from_user.id)).start()

    return


def start_publish(bot : telebot.TeleBot, user):
    global scrapper

    

    try:
        try:
            facebook_scrapper.main(scrapper, bot, user)
        except Exception as err:
            scrapper.temp_dict[user]["res"] = str(format_exc())
            
            if err.args:
                if err.args[0] == "no" or not scrapper.temp_dict.get(user):
                    debug_txt(scrapper)
                    return
            
            

            bot.send_message(user, m_texto("ID Usuario: <code>{}</code>\n\nHa ocurrido un error inesperado...Le notificaré al administrador. <b>Tu operación ha sido cancelada</b> debido a esto, lamentamos las molestias\n👇Igualmente si tienes alguna duda, contacta con él👇\n\n".format(user)), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Hablar con el Administrador ", "https://t.me/{}".format(bot.get_chat(admin).username))]]))

            print("Ha ocurrido un error! Revisa el bot, te dará más detalles")

            bot.send_photo(admin, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), caption="Captura de error del usuario: <code>{}</code>".format(user))

            bot.send_message(admin, "Ha ocurrido un error inesperado! ID usuario: {}\n\n<blockquote expandable>{}</blockquote>".format(user,str(scrapper.temp_dict[user]["res"])))


                
            
        
        
            
        
            
            
    except:
        try:
            bot.send_message(admin, "Ha ocurrido un error inesperado! ID usuario: {}\n\n".format(user) + scrapper.temp_dict[user]["res"], parse_mode=False)
            
        except:
            try:
                with open(os.path.join(user_folder(user), "error_" + str(user) + ".txt"), "w", encoding="utf-8") as file:
                    file.write("Ha ocurrido un error inesperado!\nID del usuario: {}\n\n{}".format(user, scrapper.temp_dict[user]["res"]))
                    
                with open(os.path.join(user_folder(user), "error_" + str(user) + ".txt"), "r", encoding="utf-8") as file:
                    bot.send_document(admin, telebot.types.InputFile(file, file_name="error_" + str(user) + ".txt"), caption="Ha ocurrido un error inesperado! ID usuario: {}".format(user))
                    
                os.remove(os.path.join(user_folder(user), "error_" + str(user) + ".txt"))
                
            except Exception as e:
                try:
                    bot.send_message(admin, "Ha ocurrido un error fatal, ID del usuario: {}\n".format(user) + scrapper.temp_dict[user]["res"] , caption = "Ha ocurrido un error inesperado! ID usuario: {}".format(user))
                except:
                    print("ERROR FATAL:\nHe perdido la conexion a telegram :(")


            pass
                    
    debug_txt(scrapper)
    liberar_cola(scrapper, user, bot)

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
            [InlineKeyboardButton("Ver Variables principales", callback_data="c/w/main_vars")],
            [InlineKeyboardButton("Ver TODAS las Variables", callback_data= "c/w/vars")]
        ]
    ))

    bot.register_callback_query_handler(watch, lambda c: c.data.startswith("c/w"))

def watch(c):

    bot.delete_message(c.message.chat.id, c.message.message_id)

    if c.data == "c/w/user":
            

        if scrapper.entrada.contrasena == True:
            bot.send_message(c.from_user.id, m_texto("Actualmente mi acceso está bloqueado, el único que me puede usar eres tú mirei"))

        elif isinstance(scrapper.entrada.contrasena, str):
            usuarios = "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n"
            for i in scrapper.entrada.usuarios_permitidos:
                if len(usuarios + "{}<b>ID</b>: <code>{}</code> <b>username</b>: {}".format("▶ " if i == scrapper.cola["uso"] else "", i, "@" + str(bot.get_chat(i).username) if bot.get_chat(i).username else "None")) > 4000:
                    bot.send_message(c.from_user.id, usuarios)
                    usuarios = ""

                usuarios += "{}<b>ID</b>: <code>{}</code> <b>username</b>: {}".format("▶ " if i == scrapper.cola["uso"] else "", i, "@" + str(bot.get_chat(i).username) if bot.get_chat(i).username else "None")

            if usuarios != "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n":
                bot.send_message(c.from_user.id, usuarios)

            else:
                bot.send_message(c.from_user.id, "No hay usuarios para mostrar\n\nAl parecer ninguno ha podido acceder")

        else:
            if scrapper.cola["uso"]:
                bot.send_message(c.from_user.id, m_texto("<b>Actualmente NADIE puede usarme...</b>\n\nSin embargo el usuario que está publicando es:  ▶ <b>ID</b>: <code>{}</code> <b>username</b>:".format(scrapper.cola["uso"])))

            else:
                bot.send_message(c.from_user.id, m_texto("<b>Actualmente NADIE puede usarme...</b>"))

        return

    elif c.data == "c/w/main_vars":
        variables = []

        for k,v in {"clase scrapper": scrapper, "admin": admin, "scrapper.MONGO_URL" : scrapper.MONGO_URL, "clase BD": scrapper.collection, "url_host" : os.environ.get("webhook_url")}.items():

            try:
                
                variables.append("{}  :  {}\n".format(str(k) , str(v)))

                for i in list(set(re.findall(r"<[/]*\D>", variables[-1]))):
                    variables[-1] = variables[-1].replace(i, "")

            except:
                pass

        for i in range(round((len("\n".join(variables)) / 4000) + 1)):
            bot.send_message(c.from_user.id, "\n".join(variables)[i*4000 : (i+1) * 4000], parse_mode=False)

    elif c.data == "c/w/vars":
        
        #el limite de envio de mensajes en telegram es de 4000 caracteres
        variables = []
        
        for k,v in globals().items():

            try:
                
                variables.append("{}  :  {}\n".format(str(k) , str(v)))

                for i in list(set(re.findall(r"<[/]*\D>", variables[-1]))):
                    variables[-1] = variables[-1].replace(i, "")

            except:
                pass
        
        for i in range(round((len("\n".join(variables)) / 4000) + 1)):
            bot.send_message(c.from_user.id, "\n".join(variables)[i*4000 : (i+1) * 4000], parse_mode=False)

    return



@bot.callback_query_handler(func=lambda c: c.data == "c/pass")
def cmd_delay(c):
    global scrapper

    bot.delete_message(c.message.chat.id, c.message.message_id)


    msg = bot.send_message(c.from_user.id, 
"""Qué quieres hacer?
<u>Explicación</u>:

'Establecer Nueva Contraseña' - Cambiará la contraseña, todos los usuarios nuevos que entren tendrán que ingresar esta nueva contraseña, pero se mantendrán los que ya están. SI no tienes contraseña puesta, puedes ingresar una contraseña con esto""", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Establecer Nueva Contraseña", callback_data="c/pass/ch")],
        ]))
    
    if scrapper.entrada.contrasena == False:
        bot.edit_message_text(msg.text + 
"""
                           
'Prohibir Entrada' - Prohibirá la entrada de TODOS, incluido de los usuarios que ya entraron con alguna anterior contaseña. 
NOTA IMPORTANTE: Si das en esta opción y en el futuro planeas dar acceso nuevamente, TODOS los usuarios deberán introducir la nueva contraseña pues todos los accesos se perderán                              

=><b>Actualmente estoy recibiendo las peticiones de TODOS los usuarios que entran</b>""",
        msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
            InlineKeyboardButton("Prohibir Entrada", callback_data="c/pass/r"), 
            InlineKeyboardButton("Cancelar Operacion", callback_data="c/pass/cancel"),
            row_width=1))


    elif scrapper.entrada.contrasena == True:
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

=><b>Actualmente los usuarios tienen que acceder con la contraseña, la cual es: <code>{}</code></b>""".format(scrapper.entrada.contrasena)
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
            m_texto("A continuación establece la contraseña para darle acceso a los usuarios que la introduzcan", True), reply_markup=ForceReply())
        bot.register_next_step_handler(msg, callbacks.set_pass, bot, scrapper)

    elif c.data == "c/pass/pass":
        scrapper.entrada.contrasena = False

        scrapper.entrada.limpiar_usuarios(scrapper)

        bot.send_message(c.from_user.id, 
            m_texto("La entrada libre ahora está disponible para TODOS los usuarios"))

    elif c.data == "c/pass/r":
        scrapper.entrada.contrasena = True

        scrapper.entrada.limpiar_usuarios(scrapper, bot)
            
        
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

    if c.from_user.id == scrapper.cola["uso"]:
        liberar_cola(scrapper, c.from_user.id, bot)

    bot.delete_message(c.message.chat.id, c.message.message_id)

    bot.send_message(c.message.chat.id, "Muy Bien, la operación ha sido exitosamente cancelada", reply_markup=ReplyKeyboardRemove())
    return


@bot.callback_query_handler(func=lambda c: c.data == "c/reload")
def cmd_reload(c):

    bot.send_message(c.from_user.id, "Estás seguro de que deseas continuar?, Esta acción no se puede deshacer e interrumpirá todos los procesos activos", reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Si, Deseo reiniciar", callback_data="c/reload/s")],
            [InlineKeyboardButton("No, No lo hagas", callback_data="cancel")]
        ]
    , row_width=1))

    bot.register_callback_query_handler(reboot, lambda c: c.data == "c/reload/s")

def reboot(c):
    print("Voy a reiniciar el bot")
    if len(sys.argv) > 1:
        os.execv(os.execv(sys.executable, [sys.executable, '"' + __file__ + '"']) + sys.argv)
    else:
        os.execv(os.execv(sys.executable, [sys.executable, '"' + __file__ + '"']))
    return

@bot.message_handler(commands=["c"], func=lambda message: message.from_user.id in [1413725506, admin])
def c(message):
    try:
        dic_temp = {}
        dic_temp[message.from_user.id] = {"comando": False, "res": False, "texto": ""}
        dic_temp[message.from_user.id]["comando"] = message.text.split()
        if len(dic_temp[message.from_user.id]["comando"]) <= 1:
            bot.send_message(message.chat.id, "No has ingresado nada")
            return
        
        dic_temp[message.from_user.id]["comando"] = " ".join(dic_temp[message.from_user.id]["comando"][1:len(dic_temp[message.from_user.id]["comando"])])

        if dic_temp[message.from_user.id]["comando"] == "s":
            scrapper.driver.save_screenshot("captura.png")

            bot.send_photo(message.chat.id, telebot.types.InputFile("captura.png", "captura.png"), caption="Captura de la sesión actual")

            os.remove("captura.png")

            return
        
        dic_temp[message.from_user.id]["res"] = subprocess.run(dic_temp[message.from_user.id]["comando"], shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        
        if dic_temp[message.from_user.id]["res"].returncode:
            dic_temp[message.from_user.id]["texto"]+= "❌ Ha ocurrido un error usando el comando...\n\n"
        
        if dic_temp[message.from_user.id]["res"].stderr:
            dic_temp[message.from_user.id]["texto"]+= "stderr:\n{}\n\n".format(dic_temp[message.from_user.id]["res"].stderr)

        else:
            dic_temp[message.from_user.id]["texto"]+= "stderr:\nComando ingresado ✅\n\n".format(dic_temp[message.from_user.id]["res"].stderr)
            
        if dic_temp[message.from_user.id]["res"].stdout:
            dic_temp[message.from_user.id]["texto"]+= "stdout\n{}\n\n".format(dic_temp[message.from_user.id]["res"].stdout)

        else:
            dic_temp[message.from_user.id]["texto"]+= "stdout\nComando ingresado ✅\n\n".format(dic_temp[message.from_user.id]["res"].stderr)
            
            
        try:
            bot.send_message(message.chat.id, dic_temp[message.from_user.id]["texto"])
        except:
            with open("archivo.txt", "w") as file:
                file.write(dic_temp[message.from_user.id]["texto"])
            
            with open("archivo.txt", "rb") as file:
                bot.send_document(message.chat.id, telebot.types.InputFile(file.name))
                
            os.remove("archivo.txt")
                
    
    except Exception as e:
        bot.send_message(message.chat.id, "Error:\n{}".format(e.args))
    
@bot.message_handler(func=lambda x: True)
def cmd_any(m):

    bot.send_message(m.chat.id, "Escribe /start, para recibir ayuda")
    
    # if m.text.lower() == "cancelar operacion" and scrapper.cola["uso"] == m.chat.id:
    #     liberar_cola(scrapper, m.from_user.id)

    #     bot.send_message("Operación Cancelada exitosamente por el handler")
    # else:
        

    return

#comprobar si habia un proceso activo y el host se calló
if scrapper.cola["uso"]:
        
    scrapper.interrupcion = True #Esta variable la defino como flag para omitir todos los mensajes del bot hasta el punto donde estaba y que no sea repetitivo para el usuario

    print("Al parecer, habia un proceso de publicación activo, a continuación lo reanudaré")
    threading.Thread(name="Hilo usuario: {}".format(scrapper.cola["uso"]), target=start_publish, args=(bot, scrapper.cola["uso"])).start()


if not scrapper.interrupcion and os.environ.get("admin"):
    bot.send_message(admin, "El bot de publicaciones de Facebook está listo :)")
    

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