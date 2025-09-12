import telebot
from telebot.types import ForceReply
from tb_src.usefull_functions import *


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def get_user(m , bot , user , info, temp_dict, **kwargs):

    temp_dict[user][info] = m.text
    
    temp_dict[user]["res"] = m.text

    temp_dict[user]["completed"] = True
    
            
    return


def choose_perfil(m,bot,user, info,  temp_dict):
    if not m.text in temp_dict[user]["perfiles"]:
        temp_dict[user]["msg"] = bot.send_message(user, m_texto("La información ingresada es incorrecta! Intentalo de nuevo!\n\nCual de los perfiles de esta cuenta quieres usar?"), reply_markup = temp_dict[user]["teclado"])
        
        return bot.register_next_step_handler(temp_dict[user]["msg"], choose_perfil, bot , user , info, temp_dict)
    
    temp_dict[user]["res"] = temp_dict[user]["perfiles"].index(m.text)
    temp_dict[user]["completed"] = True
    return 


def get_codigo(m,bot,user, info, temp_dict):
    if not m.text[0:2].isdigit():
        temp_dict[user]["msg"] = bot.send_message(m.chat.id, m_texto("El código introducido es incorrecto\nInténtalo de nuevo\n\nIntroduce uno de los códigos de respaldo de Facebook a continuación\n\n(Estos códigos son de 8 dígitos numéricos y puedes obtenerlos en el centro de cuentas en los ajustes de tu cuenta de Facebook)"), reply_markup=ForceReply())
        
        bot.register_next_step_handler(temp_dict[user]["msg"], get_codigo, bot,user, info, temp_dict)
    
    else:
        
        temp_dict[user]["res"] = m
        temp_dict[user]["completed"] = True    
    
    return
    
    
def perfil_pregunta(m,bot,user, info, temp_dict):
            
    if not m.text.lower() in ["si", "no"]:
        temp_dict[user]["msg"] = bot.send_message(m.chat.id, "Has introducido una respuesta incorrecta...por favor pulse uno de los botones a continuación\n\nEl perfil actual es: " + "<b>" + temp_dict[user]["res"][1] + "</b>" + "\n\n¿Quieres cambiar de perfil?", reply_markup=temp_dict[user]["teclado"])
        
        bot.register_next_step_handler(temp_dict[user]["msg"], perfil_pregunta,bot,user, info, temp_dict)
    else:
        temp_dict[user]["res"] = m
        temp_dict[user]["completed"] = True
    
    return


def captcha_getter(m, bot:telebot.TeleBot ,user, info, temp_dict, file):

    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True
    return
    
def perfil_seleccion(m, bot:telebot.TeleBot ,user, info, temp_dict, teclado):
    if not m.text in temp_dict[user]["lista_perfiles"]:
        temp_dict[user]["msg"] = bot.send_message(m.chat.id, "¡Selecciona uno de los perfiles! ¡No ingreses nada por tu cuenta!\n\nVuelve a intentarlo", reply_markup = teclado)
        
        bot.register_next_step_handler(temp_dict[user]["msg"], perfil_seleccion, temp_dict[user]["teclado"])
        
    else:
        temp_dict[user]["res"] = m.text
        temp_dict[user]["completed"] = True
        
    return


def correo_o_numero(m, bot:telebot.TeleBot ,user, info, temp_dict):
    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True

    return m.text

def correo_o_numero_verificacion(m, bot:telebot.TeleBot ,user, info, temp_dict):

    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True

    return m.text


def email_verification(m, bot:telebot.TeleBot ,user, info, temp_dict):

    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True

    return m.text

def whats_verificacion(m, bot:telebot.TeleBot, user, info, temp_dict):
    if "Cancelar Operación" == m.text:
        bot.send_message(user, "Muy bien, operación cancelada", reply_markup=telebot.types.ReplyKeyboardRemove())
        temp_dict[user]["cancelar"] = True
        temp_dict[user]["completed"] = True
        temp_dict[user]["if_cancelar"]()
        return

    # elif not m.text.isdigit():
    #     msg = bot.send_message(user, m_texto("ATENCIÓN!! ❌El código que enviaste es incorrecto❌\n\nFacebook ha enviado un código de confirmación al WhatsApp del número perteneciente a esta cuenta\n(el número en cuestión es: <b>{}</b>)\n\nVe al WhatsApp de este número, copia el código y pégalo aquí...".format(re.search(r"[*].*", temp_dict[user]["e"]).group()), True), reply_markup=ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))
        
    #     bot.register_next_step_handler(msg, whats_verificacion, user, info, temp_dict)
    #     return


    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True
    return



def repetir_bucle(m, bot: telebot.TeleBot, user, info, temp_dict):
    
    if m.text == "No Repetir":
        m = bot.send_message(user, "Muy bien, por ahora publicaré solamente 1 vez en todos tus grupos, la repetición está desactivada\n\n<b>Comenzaré la publicación en breve...</b>", reply_markup=telebot.types.ReplyKeyboardRemove())

        bot.pin_chat_message(user, m.message_id, True)
        bot.unpin_all_chat_messages(user)
        
        temp_dict[user]["res"] = False
        temp_dict[user]["completed"] = True

    elif re.search(r"\d", m.text):
        if re.search(r"\d[.,]\d", m.text):
            temp_dict[user]["res"] = int(float(re.search(r"\d+[.,]\d+", m.text).group()) * 60 * 60)
            temp_dict[user]["completed"] = True

        else:
            
            temp_dict[user]["res"] = int(m.text) * 60 * 60
            temp_dict[user]["completed"] = True

        
        m = bot.send_message(user, "Muy bien, cada {} hora(s) y {} minuto(s) estaré difundiendo la publicación por todos los grupos de esta cuenta\n\nCuando quieras cancelar la difusión por los grupos envíame /cancelar\n\n<b>Comenzaré la publicación en breve...</b>".format(int(temp_dict[user]["res"] / 60 / 60), int(temp_dict[user]["res"] / 60 % 60)), reply_markup=telebot.types.ReplyKeyboardRemove())

        bot.pin_chat_message(user, m.message_id, True)
        bot.unpin_all_chat_messages(user)

    else:

        temp_dict[user]["msg"] = bot.send_message(user, "Por favor, ingrese un NÚMERO de MINUTOS de espera antes de volver a repetir el envio de esta publicación por los grupos en la cuenta de <b>{}</b> o presione en '<b>No Repetir</b>'".format(temp_dict[user]["perfil_actual"]))

        bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.repetir_bucle, bot,user, info, temp_dict)


    return