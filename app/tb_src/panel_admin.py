import telebot 
import sys
import os
import traceback
from tb_src.usefull_functions import *
import telebot.types

from tb_src.main_classes import *


def help_admin(m, bot: telebot.TeleBot):
    if isinstance(m, telebot.types.CallbackQuery):
        m = m.message


    bot.send_message(m.chat.id, """
---- <b>Ayuda para Administradores</b> ----:
Primero que todo, este bot fué creado por @mistakedelalaif, si tienes dudas de mi funcionamiento, preguntale a él

<b><u>Nota Aclaratoria</u></b>:
Para saber el ID de un usuario, simplemente reenvia uno de sus mensajes a mi chat y te daré toda la información de él

<b><u>Comandos</u></b>:
/admin - Para acceder a esta ayuda directamente
                    
/panel - Accede al panel de control de administración, este panel tiene casi que las mismas funciones que estos comandos, solo que este es más interactivo y claro
                    
/entrada <b>[id_usuario]</b> - Le da permiso a un usuario para acceder al bot LUEGO de que este haya pagado
                    
/ban <b>[id_usuario]</b> - Banea a un usuario de TODOS los bots. Luego del baneo el usuario no podrá interactuar con el bot
Si no se especifica el [id_usuario] mostrará los usuarios baneados en TODOS los bots
                    
/unban <b>[id_usuario]</b> - Para permitirle nuevamente la entrada del bot a un usuario
                    
/usuario_actual - Muestra el usuario actual que me está usando para publicar
                    
/cancelar <b>[id_usuario]</b> - Cancela el proceso de publicación en Facebook de un usuario específico EN ESTE BOT, debes de ingresar el ID de un usuario que ya esté usando el bot, para saber este ID de usuario envíame /usuario_actual
                    
/cancelar_plan <b>[id_usuario]</b> - Elimina el plan dado a un usuario y si esta publicando para automáticamente de publicar
                    
/mensaje - Le envia un mensaje a cada usuario que pagó por el servicio en todos los bots que TÚ administras, ya sea de alguna noticia o un cambio importante que quieres que todos sepan
                    
/captura - Te envia una captura del navegador con el que se accede a facebook mostrando su estado actual
""")
    
    return


def call_ver(c, scrapper: scrapping):


    scrapper.bot.send_message(c.from_user.id, "Qué deseas saber?", reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Ver Usuarios", callback_data="c/a/w/user")],
            [InlineKeyboardButton("Ver Variables principales", callback_data="c/a/w/main_vars")],
            [InlineKeyboardButton("Ver TODAS las Variables", callback_data= "c/a/w/vars")],
            [InlineKeyboardButton("❌ Limpiar", callback_data = "clear")]
        ]
    ))

    scrapper.bot.register_callback_query_handler(watch, lambda c: c.data.startswith("c/a/w"))

def watch(c, scrapper: scrapping):
    bot = scrapper.bot
    admin = scrapper.admin


    if c.data == "c/a/w/user":
            

        if scrapper.entrada.pasar == False:
            if scrapper.cola["uso"]:
                bot.send_message(c.from_user.id, m_texto("<b>Actualmente NADIE puede usarme...</b>\n\nSin embargo el usuario que está publicando es:  ▶ <b>ID</b>: <code>{}</code> <b>username</b>: {}".format(scrapper.cola["uso"], "@" + scrapper.bot.get_chat(scrapper.cola["uso"]).username if scrapper.bot.get_chat(scrapper.cola["uso"]) else "No tiene")))

            else:
                bot.send_message(c.from_user.id, m_texto("<b>Actualmente NADIE puede usarme...</b>"))

        elif scrapper.entrada.pasar:
            usuarios = "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n"

            for usuario in scrapper.entrada.obtener_usuarios():
                if len(usuarios + "{}<b>ID</b>: <code>{}</code>, <b>username</b>: {}, <b>plan<b>: {}\n\n".format("▶ " if i == scrapper.cola["uso"] else "", usuario.telegram_id, "@" + str(bot.get_chat(usuario.telegram_id).username) if bot.get_chat(usuario.telegram_id).username else "None", usuario.plan.__class__.__name__ )) > 4000:

                    bot.send_message(c.from_user.id, usuarios)
                    usuarios = ""

                usuarios += "{}<b>ID</b>: <code>{}</code>, <b>username</b>: {}, <b>plan<b>: {}\n\n".format("▶ " if i == scrapper.cola["uso"] else "", usuario.telegram_id, "@" + str(bot.get_chat(usuario.telegram_id).username) if bot.get_chat(usuario.telegram_id).username else "None", usuario.plan.__class__.__name__ )

            if usuarios != "<u>Lista de usuarios que tienen permiso de usarme</u>:\n\n":
                bot.send_message(c.from_user.id, usuarios)

            else:
                bot.send_message(c.from_user.id, "No hay usuarios para mostrar\n\nAl parecer ninguno ha podido acceder")


        return

    elif c.data == "c/a/w/main_vars":
        variables = []

        for k,v in {"clase scrapper": scrapper, "admin": admin, "scrapper.MONGO_URL" : scrapper.MONGO_URL, "clase BD": scrapper.collection, "url_host" : os.environ.get("webhook_url")}.items():

            try:
                
                variables.append("{}  :  {}\n".format(str(k) , str(v)))

                for i in list(set(re.findall(r"<[/]*\D>", variables[-1]))):
                    variables[-1] = variables[-1].replace(i, "")

            except:
                pass

        for i in range(int(len("\n".join(variables)) / 4000) + 1):
            bot.send_message(c.from_user.id, "\n".join(variables)[i*4000 : (i+1) * 4000], parse_mode=False)

    elif c.data == "c/a/w/vars":
        
        #el limite de envio de mensajes en telegram es de 4000 caracteres
        variables = []
        
        for k,v in globals().items():

            try:
                
                variables.append("{}  :  {}\n".format(str(k) , str(v)))

                for i in list(set(re.findall(r"<[/]*\D>", variables[-1]))):
                    variables[-1] = variables[-1].replace(i, "")

            except:
                pass
        
        for i in range((int(len("\n".join(variables)) / 4000) + 1)):
            bot.send_message(c.from_user.id, "\n".join(variables)[i*4000 : (i+1) * 4000], parse_mode=False)

    return


def entrada(c, scrapper: scrapping):
    bot = scrapper.bot
    admin = scrapper.admin


    msg = bot.send_message(c.from_user.id, 
"""Qué quieres hacer?
<u>Explicación</u>:
""")
    
    if scrapper.entrada.pasar == False:
        bot.edit_message_text(msg.text + 
"""
                           
'Prohibir Entrada' - Prohibirá la entrada de TODOS, Prohibirá la entrada de TODOS, incluido de los que tienen planes  

=><b>Actualmente estoy recibiendo la entrada de los usuarios</b>""",
        msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
            InlineKeyboardButton("Prohibir Entrada", callback_data="c/a/pass/r"), 
            InlineKeyboardButton("Cancelar Operacion", callback_data="c/a/pass/cancel"),
            row_width=1))


    elif scrapper.entrada.pasar == True:
        bot.edit_message_text(msg.text + """
                              
'Permitir Entrada' - Permitirá la entrada de TODOS los usuarios sin contraseña requerida
                              
=><b>Actualmente estoy bloqueando a TODOS los usuarios</b>""",
        msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
            InlineKeyboardButton("Permitir Entrada", callback_data="c/a/pass/pass"),
            InlineKeyboardButton("Cancelar Operacion", callback_data="c/a/pass/cancel"), row_width=1))
        
    else:
        bot.edit_message_text(msg.text + 
"""

'<b>Prohibir Entrada</b>' - Prohibirá la entrada de TODOS, incluido de los que tienen planes  

'<b>Permitir Entrada</b>' - Permitirá la entrada de los usuarios          
""", msg.chat.id, msg.message_id, reply_markup=msg.reply_markup.add(
    InlineKeyboardButton("Prohibir Entrada", callback_data="c/a/pass/r"),
    InlineKeyboardButton("Permitir Entrada", callback_data="c/a/pass/pass"), 
    InlineKeyboardButton("Cancelar Operacion", callback_data="c/a/pass/cancel"), row_width=1))
        


def modificar_entrada(c, scrapper):

    bot = scrapper.bot
    admin = scrapper.admin


    if c.data == "c/a/pass/cancel":
        bot.send_message(c.from_user.id, 
            "Operación Cancelada exitosamente")
            

    elif c.data == "c/a/pass/pass":
        scrapper.entrada.pasar = False

        scrapper.entrada.prohibir_pasar(scrapper, bot, False)

        bot.send_message(c.from_user.id, 
            m_texto("La entrada libre ahora está disponible para TODOS los usuarios"))

    elif c.data == "c/a/pass/r":
        scrapper.entrada.pasar = True

        scrapper.entrada.prohibir_pasar(scrapper, bot)
            
        
        scrapper.cola["cola_usuarios"].clear()
        
        bot.send_message(c.from_user.id, 
            m_texto("Los permisos de entrada han sido removidos exitosamente ahora ningún usuario tendrá permiso para entrar\nLos que ya tenían permiso tampoco podrán \n\nHASTA...que no cambies nuevamente la contraseña o permitas la entrada para todos"))
        

    return

def cambiar_delay(c, scrapper: scrapping):
    bot = scrapper.bot
    admin = scrapper.admin

    msg = bot.send_message(c.message.chat.id, 
        m_texto("A continuación establece el tiempo de espera entre la publicación en cada grupo (En segundos)\n\n"
        "El tiempo actual de espera es de {} segundos".format(scrapper.delay), True), 
        reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))
        
    bot.register_next_step_handler(msg, set_delay, scrapper , bot)
    return



def set_delay(m, scrapper: scrapping ,bot: telebot.TeleBot):
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

    scrapper.administrar_BD()

    return




def agregar_usuario_set_time(scrapper : scrapping , usuario_cliente, chat_admin , bot):
    
    if usuario_cliente == scrapper.creador:
        bot.send_message(chat_admin, "No puedes asignarle un plan a mi creador\n\nOperación Cancelada")
        return

    TEXTO = """
<u><b>Explicación</b></u>:
El tiempo que deberás introducir está compuesto de 3 valores que indican el intervalo de tiempo que deberá de pasar para que el servicio al usuario expire.
El conteo del tiempo comienza a partir de tu siguiente mensaje (osea, cuando lo establezcas, si tiene el formato correcto)

<b>Formato de tiempo</b>:
<code>[días]d[horas]h[minutos]m</code>

<blockquote><u><b>Ejemplo</b></u>:
<code>7d4h2m</code> - Aquí el tiempo de expiración se establece a dentro de 7 días, 4 horas y 2 minutos para su vencimiento</blockquote>

<b>Nota</b>:
También está la posibilidad de ingresar 1 o 2 valores de los 3, solo se tomará el tiempo de los ingresados

<blockquote><u><b>Ejemplo</b></u>:
<code>7d</code> - Aquí el tiempo de expiración se establece a dentro de 7 días exactamente</blockquote>

En el siguiente mensaje especifique este tiempo siguiendo el formato indicado    
"""
    msg = bot.send_message(chat_admin, m_texto("A continuación, establece el <b>tiempo de expiración del servicio para el usuario</b> (osea, luego de ese tiempo tendrá que volver a contratar el servicio ya que habrá caducado por lo que pagó)\n\n{}".format(TEXTO).strip(), True), reply_markup=ReplyKeyboardMarkup(True).add("Dejar en 7 Días", "Cancelar Operación", row_width=1))

    bot.register_next_step_handler(msg, agregar_usuario, bot, scrapper, usuario_cliente, TEXTO)

def agregar_usuario(m, bot: telebot.TeleBot, scrapper: scrapping, usuario_cliente, TEXTO):
    if "Dejar en 7 Días" == m.text:
        tiempo = time.time() + 7 * 24 * 60 * 60

    elif "Cancelar Operación" == m.text:
        bot.send_message(m.chat.id, m_texto("Operación Cancelada Exitosamente"), reply_markup=telebot.types.ReplyKeyboardRemove())
        return
        
    else:
        tiempo = 0

        if not re.search(r"\d+h", m.text) or not re.search(r"\d+d", m.text) or not re.search(r"\d+m", m.text):
            msg = bot.send_message(m.chat.id, m_texto("ERROR No has ingresado el formato adecuado!!\n\n{}".format
            (TEXTO)))
            
            bot.register_next_step_handler(msg, agregar_usuario, bot, TEXTO)

        if re.search(r"\d+h", m.text):
            tiempo += int(re.search(r"\d+h", m.text).group()) * 60 * 60

        if re.search(r"\d+d", m.text):
            tiempo += int(re.search(r"\d+d", m.text).group()) * 24 * 60 * 60

        if re.search(r"\d+m", m.text):
            tiempo += int(re.search(r"\d+h", m.text).group()) * 60 


        tiempo += time.time()

    bot.send_message(m.chat.id, m_texto("Último paso!\nA continuación, elige el plan contratado por el cliente para poder asignárselo\n\n👇 Planes disponibles 👇",True))
    
    msg = bot.send_message(m.chat.id, "{}".format(Planes_para_comprar().show()), reply_markup=telebot.types.ReplyKeyboardMarkup(True, True).add(*[KeyboardButton(i.__class__.__name__) for i in Planes_para_comprar().lista_planes], row_width=2).row("Cancelar Operación"))

    bot.register_next_step_handler(msg, agregar_usuario_set_plan, bot, scrapper, usuario_cliente, tiempo)

def agregar_usuario_set_plan(m, bot, scrapper: scrapping, usuario_cliente, tiempo):
    
    if m.text == "Basico":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Basico(tiempo, bot.user.id)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Basico(tiempo, bot.user.id)))

    elif m.text == "Medio":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Medio(tiempo, bot.user.id)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Medio(tiempo, bot.user.id)))

    elif m.text == "Pro":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Pro(tiempo, bot.user.id)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Pro(tiempo, bot.user.id)))

    elif m.text == "Ilimitado":
        if scrapper.entrada.obtener_usuario(usuario_cliente):
            scrapper.entrada.obtener_usuario(usuario_cliente).plan = Ilimitado(tiempo, bot.user.id)

        else:
            scrapper.entrada.usuarios.append(Usuario(usuario_cliente, Ilimitado(tiempo, bot.user.id)))

    else:
        msg = bot.send_message(m.chat.id, "¡No has elegido ninguno de los botones!\n\n¡Por favor, presiona uno de los siguientes!\n\n{}".format(Planes_para_comprar().show()), reply_markup=telebot.types.ReplyKeyboardMarkup(True, True).add(*Planes_para_comprar().lista_planes, row_width=2).row("Cancelar Operación"))

        bot.register_next_step_handler(msg, agregar_usuario_set_plan, bot, scrapper, usuario_cliente, tiempo)

        return
    
    bot.send_message(m.chat.id, m_texto("Muy bien, el Usuario {} podrá usarme <b>a partir de ahora</b> hasta dentro de {}").format("@" + str(bot.get_chat(usuario_cliente).username) if bot.get_chat(usuario_cliente) else "<code>" + str(usuario_cliente) + "</code>", scrapper.entrada.get_caducidad(usuario_cliente, scrapper)), reply_markup=telebot.types.ReplyKeyboardRemove())

    try:
        bot.send_message(usuario_cliente, """
<b>Hola {}!</b> :D/

Has obtenido acceso a mis servicios, ya puedes comenzar a publicar ;)

<b><u>Plan Obtenido</u></b>:
<blockquote>{}</blockquote>

<b><u>Expiración del Plan</u></b>:
<blockquote>{}</blockquote>
""".format(bot.get_chat(usuario_cliente).first_name, scrapper.entrada.obtener_usuario(usuario_cliente).plan.show(), scrapper.entrada.get_caducidad(usuario_cliente, scrapper)))

    except:
        pass



    scrapper.guardar_datos(m.from_user.id, False)
    
    if scrapper.collection.find_one({"tipo": "datos"})["creador_dict"].get("notificar_planes") and m.from_user.id != scrapper.creador:
        bot.send_message(scrapper.creador, "El administrador: {} ha autorizado al usuario: {} con el siguiente plan: \n\n{}".format(m.from_user.id if not bot.get_chat(m.from_user.id).username else "@" + bot.get_chat(m.from_user.id).username, usuario_cliente if not bot.get_chat(usuario_cliente).username else "@" + bot.get_chat(usuario_cliente).username , scrapper.entrada.obtener_usuario(usuario_cliente).plan.__str__))

    return



def comandos_admin(m: telebot.types.Message, scrapper: scrapping):
    bot = scrapper.bot
    if re.search("/entrada", m.text):

        if re.search(r"\d", m.text):

            if bot.get_chat(int(re.search(r"\d+", m.text).group())):

                agregar_usuario_set_time(scrapper, int(re.search(r"\d+", m.text).group()), m.chat.id ,bot)

            else:
                bot.send_message(m.chat.id, m_texto("ERROR El ID de usuario que has ingresado no es correcto\n\nSi no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él"))
        else:
            bot.send_message(m.chat.id, m_texto("""
ERROR ¡Debes de ingresar el ID de usuario!
El comando debe darse así:

/entrada <b>[ID_NUMÉRICO]</b>

Si no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él

Operación Cancelada :(
"""))   
                
    elif re.search(r"/unban", m.text):
        if re.search(r"\d+", m.text):
            if bot.get_chat(re.search(r"\d+", m.text).group()):
                if int(re.search(r"\d+", m.text).group()) in scrapper.collection.find_one({"tipo": "datos"})["usuarios_baneados"]:

                    lista_cluster = scrapper.collection.find_one({"tipo": "datos"})["usuarios_baneados"]

                    lista_cluster.remove(int(re.search(r"\d+", m.text).group()))

                    scrapper.collection.update_one({"tipo": "datos"}, {"$set": {"usuarios_baneados": lista_cluster}})

                    scrapper.entrada.actualizar_baneados(scrapper)

                    bot.send_message(m.chat.id, "El usuario ha sido quitado de la lista de baneados correctamente :D")

                    scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)
                
                else:
                    bot.send_message(m.chat.id, "El usuario que me indicaste no está baneado, envíame /ban para ver la lista de usuarios baneados")
            
            else:
                bot.send_message(m.chat.id, m_texto("ERROR El ID de usuario que me indicaste ni siquiera existe!\n\nOperación Cancelada"))

        else:
            bot.send_message(m.chat.id, m_texto("ERROR Debes de indicar el ID de un usuario para poder permitirle volver a usarme\nSi no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él\n\nOperación Cancelada"))

    elif re.search(r"/ban", m.text):
        if re.search(r"\d", m.text):

            if int(re.search(r"\d+", m.text).group()) == scrapper.creador:
                bot.send_message(m.chat.id, "No puedo banear a mi propio creador listillo\n\nOperación cancelada")
                return

            if bot.get_chat(int(re.search(r"\d+", m.text).group())):
                if scrapper.cola["uso"] == int(re.search(r"\d+", m.text).group()):
                    scrapper.temp_dict[int(m.text.split()[1])]["cancelar_forzoso"] = True
                    liberar_cola(scrapper, int(re.search(r"\d+", m.text).group()), bot)

                scrapper.usuarios_baneados = int(re.search(r"\d+", m.text).group())

                bot.send_message(m.chat.id, "Muy bien, el usuario {} no podrá usarme".format(
                    "@" + bot.get_chat(int(re.search(r"\d+", m.text).group())).username if bot.get_chat(int(re.search(r"\d+", m.text).group())) else int(re.search(r"\d+", m.text).group())
                    ))

                scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)

            else:
                bot.send_message(m.chat.id, m_texto("ERROR El ID del usuario ingresado no es correcto, por favor ingresa uno correctamente\n\nSi no sabes cual es el ID de un usuario puedes simplemente reenviarme algún mensaje de ese usuario aquí y te daré toda la información sobre él"))
        
        else:

            if scrapper.usuarios_baneados:
                texto = "<b><u>Usuarios baneados</u></b>:\n\n\n"

                for e, i in enumerate(scrapper.usuarios_baneados):

                    if len(texto + "{} =>  <b>ID de usuario</b>: <code>{}</code>, username: {}\n\n".format(e, i , "@" + bot.get_chat(i).username if bot.get_chat(i).username else "No disponible")) >= 4000:
                        
                        bot.send_message(m.chat.id, texto)
                        texto = ""


                    texto += "{} =>  <b>ID de usuario</b>: <code>{}</code>, username: {}\n\n".format(e, i , "@" + bot.get_chat(i).username if bot.get_chat(i).username else "No disponible")

                bot.send_message(m.chat.id, texto)

            else:
                bot.send_message(m.chat.id, "No hay usuarios baneados, por ahora")

    elif re.search("/usuario_actual", m.text):
        if scrapper.cola["uso"]:
            mostrar_info_usuario(m.chat.id , scrapper.cola["uso"], bot)

        else:
            bot.send_message(m.chat.id, "Actualmente nadie está publicando en este bot")


    

    elif re.search("/cancelar_plan", m.text):
        if bot.get_chat(int(re.search(r"\d+", m.text).group())):
            scrapper.entrada.obtener_usuario(int(re.search(r"\d+", m.text).group())).plan = Sin_Plan()
            
            for publicacion in scrapper.entrada.obtener_usuario(int(re.search(r"\d+", m.text).group())).publicaciones:
                scrapper.entrada.obtener_usuario(int(re.search(r"\d+", m.text).group())).eliminar_publicacion(publicacion)

            scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)

            try:
                bot.send_message(int(re.search(r"\d+", m.text).group()), "Su servicio de publicaciones ha sido suspendido por el administrador\n\n👇 Si quiere reclamar, vaya a su privado 👇", reply_markup=scrapper.admin_markup)

            except:
                pass

            scrapper.guardar_datos(int(re.search(r"\d+", m.text).group()), False)

        else:
            bot.send_message(m.chat.id, "Debes de introducir tambien un id de usuario")

    elif re.search("/mensaje", m.text):
        
        if m.from_user.id == scrapper.creador and re.search("admins", m.text.split()[1]):

            for administrador in list(set([dill.loads(datos["cookies"])["scrapper"].admin for datos in scrapper.collection.find({"tipo": "telegram_bot"}).to_list()])):
                bot.send_message(administrador, m.text.split()[2:], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contactar con mi creador 👨‍💻", "https://t.me/{}".format(scrapper.bot.get_chat(scrapper.creador).username))]]))

        elif len(m.text.split()) > 1:
            
            for i in list(filter(lambda i: dill.loads(i["cookies"])["scrapper"].admin == m.from_user.id or dill.loads(i["cookies"])["scrapper"].creador == m.from_user.id, scrapper.collection.find({"tipo": "telegram_bot"}).to_list())):
                scrapper_copia = dill.loads(i["cookies"])["scrapper"]

                for usuario in scrapper_copia.entrada.obtener_usuarios():
                    if usuario != m.chat.id and i != scrapper.creador:
                        if scrapper.creador == m.from_user.id:
                            scrapper_copia.bot.send_message(usuario, "👨‍💻 <b>Mensaje del Creador</b>:\n\n{}".format(m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "")), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Preguntar 👨‍💻", "https://t.me/{}?text=Háblame+más+acerca+de+'{}'".format(bot.get_chat(scrapper.creador).username, m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "").replace(" ", "+")))]]))
                        else:
                            scrapper_copia.bot.send_message(usuario, "👮‍♂️ <b>Mensaje del Administrador</b>:\n\n{}".format(m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "")), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Preguntar 👮‍♂️", "https://t.me/{}?text=Háblame+más+acerca+de+'{}'".format(bot.get_chat(m.from_user.id).username, m.text.replace(re.search(r"/mensaje\s*", m.text).group(), "").replace(" ", "+")))]]))


        else:
            bot.send_message(m.chat.id, m_texto("ERROR Debiste de ingresar un texto luego del comando\n\nEl formato correcto es:\n/mensaje <b>hola a todos los usuarios</b>\n\nTambién puede ser así:\n/mensaje admins Hola a todos los administradores"))

    elif re.search("/captura", m.text):
        bot.send_document(m.chat.id, telebot.types.InputFile(make_screenshoot(scrapper.driver, m.chat.id)))




def comandos_creador(user, scrapper: scrapping, comando = False):

    if not user == scrapper.creador:
        return False

    if not comando:
        scrapper.bot.send_message(user, """
<u><b>Ayuda con los comandos avanzados</b></u>:
                                  
<code>/c s</code> - Captura de pantalla
<code>/c b</code> - breakpoint
<code>/c bots</code> - Muestra todos los bots y sus respectivos administradores
<code>/c del_db</code> [BOT_ID] - borra la base de datos y todos los datos de los bots (a excepcion de quien lo administra), en caso de que se le especifique un [BOT_ID] pues hace este proceso solamente en ese bot concretamente. Esto es útil para cuando hay actualizaciones en el codigo que requieren nuevos valores
<code>/c set_admin</code> [bot_id] [new_admin_id] - Establece un nuevo admin en un bot específico
""")
        return False


    elif re.search("del_db", comando.lower()):
        if re.search(r"\d+", comando.lower()):
            if scrapper.bot.get_chat(int(re.search(r"\d+", comando.lower()).group())):
                if scrapper.bot.get_chat(int(re.search(r"\d+", comando.lower()).group())).username.endswith("bot"):
                    msg = scrapper.bot.send_message(user, "Estás SEGURO que deseas eliminar todos los datos del bot: {} ({})?\n\nPodrán seguir usándolo pero luego del reinicio en el host el bot solamente conservará información importante cómo quien es el administrador, variables de entorno, etc".format(scrapper.bot.get_chat(int(re.search(r"\d+", comando.lower()).group())).first_name , "@" + scrapper.bot.get_chat(int(re.search(r"\d+", comando.lower()).group())).username), reply_markup=ReplyKeyboardMarkup(True, True).add("❌ Cancela!", "✅ Si, borrar todo de {}".format(scrapper.bot.get_chat(int(re.search(r"\d+", comando.lower()).group())).first_name), row_width=1))

                    scrapper.bot.register_next_step_handler(msg, borrar_db, scrapper, int(re.search(r"\d+", comando).group()))

                else:
                    comando.replace(re.search(r"\d+", comando).group(), "")
            else:
                comando.replace(re.search(r"\d+", comando).group(), "")
        
        if not re.search(r"\d+", comando):
            msg = scrapper.bot.send_message(user, "Estás SEGURO que deseas eliminar todos los datos de TODOS los bots?\n\nPodrán seguir usándolos pero luego del reinicio en el host los bot solamente conservarán información importante cómo quien es el administrador, variables de entorno, etc", reply_markup=ReplyKeyboardMarkup(True, True).add("❌ Cancela!", "✅ Si, borrar TODO", row_width=1))

            scrapper.bot.register_next_step_handler(msg, borrar_db, scrapper)

            return


    elif comando == "b":
        try:
            breakpoint()
            print("Estoy en el breakpoint")
        except:
            print("ocurrio un error con el breakpoint pero lo controlé, al parecer estás usando el host\n\nEste comando aquí es inserbible")

        return True
    
    elif re.search("set_admin", comando) and re.findall(r"\d+", comando) == 2:
        #/c set_admin <bot_id> <new_admin_id>
        if scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[0])) and scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[1])):

            if scrapper.collection.find_element({"tipo": "telegram_bot", "telegram_id": scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[0])).id}):
                scrapper_copia = dill.loads(scrapper.collection.find_one({"tipo": "telegram_bot", "telegram_id": scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[0])).id})["cookies"])["scrapper"]

                scrapper_copia.admin = int(re.findall(r"\d+", comando)[1])
                scrapper_copia.env.update({"admin": int(re.findall(r"\d+", comando)[1])})
                scrapper_copia.administrar_BD()

                scrapper.bot.send_message(user, "Muy bien, ahora el nuevo admin de: @{} es: {}".format(scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[0])).username, "@" + scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[1])).username if scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[1])).username else scrapper.bot.get_chat(int(re.findall(r"\d+", comando)[1])).firs_name))

            else:
                scrapper.bot.send_message(user, "El ID del bot que ingresaste ni siquiera te pertenece!")

        else:
            scrapper.bot.send_message(user, "No has ingresado un ID correcto! ")

    elif comando == "bots":
        #muestra todos los bots en la base de datos
        texto = "<b>Lista de bots desplegados</b>:\n\n"
        for e, i in enumerate(scrapper.collection.find({"tipo": "telegram_bot"}).to_list()):

            if len(texto + "{} =>  <b>bot ID</b>: <code>{}</code>, <b>admin</b>: <code>{}</code>, <b>url</b>: {}\n\n".format(e, i["telegram_id"], dill.loads(i["cookies"])["scrapper"].admin, dill.loads(i["cookies"])["scrapper"].env.get("webhook_url"))) >= 4000:

                scrapper.bot.send_message(user, texto)
                texto = ""
            

            texto += "{} =>  <b>bot ID</b>: <code>{}</code>, <b>admin</b>: <code>{}</code>, <b>url</b>: {}\n\n".format(e, i["telegram_id"], dill.loads(i["cookies"])["scrapper"].admin, dill.loads(i["cookies"])["scrapper"].env.get("webhook_url"))

        scrapper.bot.send_message(user, texto)

        return True

        
    

    elif re.search("notificar_planes", comando.lower()):
        if scrapper.collection.find_one({"tipo": "datos"}).get("notificar_planes"):
            scrapper.creador_dict = {"notificar_planes": False}
            
        else:
            scrapper.creador_dict = {"notificar_planes": True}
        
    return False
            

def borrar_db(m, scrapper: scrapping, bot_id=False):
    if m.text == "❌ Cancela!":
        scrapper.bot.send_message(m.chat.id, "Operación Cancelada", reply_markup=ReplyKeyboardRemove())
        return
    
    if m.text.startswith("✅ Si"):  
        if bot_id:
            #quiere eliminar la BD de un bot específico

            bots_iterar = scrapper.collection.find({"tipo": "telegram_bot", "telegram_id": bot_id}).to_list()

            for e, datos_db in enumerate(bots_iterar):
                scrapper_copia = dill.loads(datos_db["cookies"])["scrapper"]
                scrapper_copia.administrar_BD()

            bots_iterar = scrapper.collection.find({"tipo": "telegram_bot", "telegram_id": bot_id}).to_list()

            scrapper.creador_dict = {"del_db": scrapper.collection.find_one({"tipo": "usuarios"})["creador_dict"]["del_db"] + [bot_id]}

        else:
            #Quiere eliminar las BD de TODOS los bots

            bots_iterar = scrapper.collection.find({"tipo": "telegram_bot"}).to_list()

            for e, datos_db in enumerate(bots_iterar):
                scrapper_copia = dill.loads(datos_db["cookies"])["scrapper"]
                scrapper_copia.administrar_BD()

            bots_iterar = scrapper.collection.find({"tipo": "telegram_bot"}).to_list()

            scrapper.creador_dict = {"del_db": [datos["telegram_id"] for datos in scrapper.collection.find({"tipo": "telegram_bot"}).to_list()]}


        for e, datos_db in enumerate(bots_iterar):
            
            scrapper_copia = dill.loads(datos_db["cookies"])["scrapper"]

            scrapper_copia.bot.send_message(scrapper_copia.admin, """
<b>‼ADVERTENCIA‼</b>
Mi creador @{} ha hecho cambios en mi código fuente, borraré todos los datos de los clientes y algunos otros a excepción de los que te permiten administrarme.

Por ahora mantendré los datos hasta el próximo reinicio (el cual será pronto), luego del reinicio los usuarios perderán los planes y deberán volver a ingresar todo nuevamente (la información de publicaciones y sus cuentas en Facebook)

Sentimos las molestias, <b>este bot aún está en desarrollo</b>... Es normal que estos cambios pasen

A continación te enviaré los datos de tus clientes para que puedas reembolsarlos o renovarles el servicio 👇""".format(scrapper_copia.bot.get_chat(scrapper_copia.creador).username).strip())
            

            texto = "<b>Información de los usuarios</b>:\n\n"

            if scrapper_copia.entrada.usuarios:
                for e, usuario in enumerate(scrapper_copia.entrada.usuarios):

                    if isinstance(usuario.plan, Administrador):
                        continue
                    
                    if not scrapper_copia.entrada.get_caducidad(usuario.telegram_id, scrapper_copia, True):
                        if len(texto + "{} =>  ID: <code>{}</code> , username: {}, plan: {}, tiempo de expiración: {}".format(e, "@" + scrapper_copia.bot.get_chat(usuario.telegram_id).username if scrapper_copia.bot.get_chat(usuario.telegram_id).username else str("No tiene"), usuario.plan.__class__.__name__, str(scrapper_copia.entrada.get_caducidad(usuario.telegram_id, scrapper_copia)) if scrapper_copia.entrada.get_caducidad(usuario.telegram_id, scrapper_copia) else "No tiene expiración")) >= 4000:
                            scrapper_copia.bot.send_message(scrapper_copia.admin, texto)
                            texto = ""

                        
                        texto += "{} =>  ID: <code>{}</code> , username: {}, plan: {}, tiempo de expiración: {}".format(e, "@" + scrapper_copia.bot.get_chat(usuario.telegram_id).username if scrapper_copia.bot.get_chat(usuario.telegram_id).username else str("No tiene"), usuario.plan.__class__.__name__, str(scrapper_copia.entrada.get_caducidad(usuario.telegram_id, scrapper_copia)) if scrapper_copia.entrada.get_caducidad(usuario.telegram_id, scrapper_copia) else "No tiene expiración")


                if texto != "<b>Información de los usuarios</b>:\n\n":
                    scrapper_copia.bot.send_message(scrapper_copia.admin, texto)


                # if scrapper_copia.cola["uso"]:
                #     scrapper_copia.temp_dict[scrapper_copia.cola["uso"]]["cancelar_forzoso"] = True
                #     liberar_cola(scrapper_copia, scrapper_copia.cola["uso"], scrapper_copia.bot, False)

            if not scrapper_copia.entrada.usuarios or texto == "<b>Información de los usuarios</b>:\n\n":
                scrapper_copia.bot.send_message(scrapper_copia.admin, m_texto("Pues no, no tienes clientes a los que notificarles los cambios"))

            

            res = {}
            for k,v in scrapper_copia.__getstate__().copy().items():
                if k in ["env", "admin", "MONGO_URL", "bot", "webhook_url", "creador"]:
                    res.update({k: v})

            scrapper_copia.__dict__ = res.copy()

            dict_guardar = {"scrapper": scrapper_copia}

            with open(os.path.join(gettempdir(), "copia_bot_cookies.pkl"), "wb") as file:

                dill.dump(dict_guardar, file)

            with open(os.path.join(gettempdir(), "copia_bot_cookies.pkl"), "rb") as file:

                if scrapper.collection.find_one({"tipo": "telegram_bot", "telegram_id": scrapper_copia.bot.user.id}):
                    
                    scrapper.collection.update_one({"tipo": "telegram_bot", "telegram_id": scrapper_copia.bot.user.id}, {"$set": {"cookies" : file.read()}})

                else:
                    scrapper.collection.insert_one({"_id": int(time.time()) + 1, "tipo": "telegram_bot", "telegram_id": scrapper.bot.user.id, "cookies" : file.read()})

            os.remove(os.path.join(gettempdir(), "copia_bot_cookies.pkl"))
            
                
                

        scrapper.bot.send_message(m.chat.id, m_texto("Operación realizada exitosamente :D No se volverá a guardar el estado de los bots en el cluster hasta que no se reinicie en el host"))

        return True





def comprobacion_env(usuario_accionador, scrapper: scrapping):

    if not os.environ.get("admin") or not os.environ.get("MONGO_URL") and (scrapper.env.get("admin") and scrapper.env.get("MONGO_URL")):
        for k, v in scrapper.env.items():
            os.environ[k] = v

        scrapper.admin = os.environ.get("admin")
        scrapper.MONGO_URL = os.environ.get("MONGO_URL")

            

    elif (not scrapper.admin or not scrapper.admin) and (not scrapper.env.get("admin") and not scrapper.env.get("MONGO_URL")):
        try:
            TEXTO = (
"""Enviame el archivo.env a continuación con las siguientes variables de entorno y sus respectivos valores:

admin=[ID del administrador del bot]
MONGO_URL=[Enlace del cluster de MongoDB (Atlas)]
webhook_url=(OPCIONAL) [Si esta variable es definida se usará el metodo webhook, sino pues se usara el método polling]""".strip())


            msg = scrapper.bot.send_message(scrapper.creador, m_texto(TEXTO, True))

            scrapper.bot.register_next_step_handler(msg, set_env_vars, scrapper.bot, TEXTO, scrapper, usuario_accionador)

        except Exception as err:

            scrapper.bot.send_message(usuario_accionador, "👇Contacta con mi creador @{} para que te dé acceso a mi👇".format(scrapper.bot.get_chat(scrapper.creador).username), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contactar 👨‍💻", "https://t.me/{}".format(scrapper.bot.get_chat(scrapper.creador).username))]]))
            quit()

    return

def set_env_vars(m: telebot.types.Message, bot, TEXTO, scrapper: scrapping, usuario_accionador ,**kwargs):


    if m.document:
        if not m.document.file_name.endswith(".env"):
            msg = bot.send_message(m.chat.id, m_texto("No has enviado el archivo variables de entorno!\nEnvía el adecuado!\n\n{}", True).format(TEXTO))
                
            scrapper.bot.register_next_step_handler(msg, set_env_vars, bot, TEXTO, scrapper, usuario_accionador)
            return

        with open("variables_entorno.env", "wb") as file:
            try:
                file.write(bot.download_file(bot.get_file(m.document.file_id).file_path))

            except:
                msg = bot.send_message(m.chat.id, m_texto("No has enviado el archivo variables de entorno!\nEnvía el adecuado!\n\n{}", True).format(TEXTO))
                
                scrapper.bot.register_next_step_handler(msg, set_env_vars, bot, TEXTO, scrapper, usuario_accionador)
                return

        with open("variables_entorno.env", "r") as file:
            texto = file.read()

        os.remove("variables_entorno.env")
        
        if "admin=" in texto and "MONGO_URL=" in texto:
            scrapper.env[bot.user.id] = {}
            for i in texto.splitlines():
                os.environ[re.search(r".*=", i).group().replace("=", "")] = re.search(r"=.*", i).group().replace("=", "")
                scrapper.env[re.search(r".*=", i).group().replace("=", "")] = re.search(r"=.*", i).group().replace("=", "")
                
            scrapper.MONGO_URL = os.environ["MONGO_URL"]
            scrapper.admin = int(os.environ["admin"])
            scrapper.admin_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Contacta con el Administrador 👮‍♂️", "https://t.me/{}".format(scrapper.bot.get_chat(scrapper.admin).username))
            ]])

            

            
        else:
            msg = bot.send_message(m.chat.id, m_texto("No has enviado el formato correcto del archivo!\nPor favor envie a continuacion un archivo .env que siga el formato adecuado\n\n{}", True).format(TEXTO))

                
            scrapper.bot.register_next_step_handler(msg, set_env_vars, bot, TEXTO, scrapper, usuario_accionador)

            return 


    else:

        msg = bot.send_message(m.chat.id, m_texto("No has enviado el archivo variables de entorno!\nEnvía el adecuado!\n\n{}", True).format(TEXTO)
)

        scrapper.bot.register_next_step_handler(msg, set_env_vars, bot, TEXTO, scrapper, usuario_accionador)

        return


    scrapper.administrar_BD()


    if not int(os.environ.get("admin")) in scrapper.entrada.obtener_usuarios():
        scrapper.entrada.usuarios.append(tb_src.main_classes.Usuario(int(os.environ["admin"]), tb_src.main_classes.Administrador(False)))



    bot.set_my_commands([
        BotCommand("/help", "Información sobre el bot"),
        BotCommand("/lista_planes", "Para ver TODOS los planes disponibles"),
        BotCommand("/publicaciones", "administra tus publicaciones"),
        BotCommand("/publicar", "Comienza a publicar"),
        BotCommand("/cancelar", "Cancela el proceso actual"),
        BotCommand("/panel", "Panel de ajustes")], 
        BotCommandScopeChat(int(os.environ["admin"])))
    
    bot.send_message(m.chat.id, "Todo está listo aquí :D")
    bot.send_message(usuario_accionador, "Ya pueden usarme :D")
    scrapper.entrada.pasar = True
    
    return 