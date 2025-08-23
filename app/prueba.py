from threading import Thread
lo = "Juan"



def hilo():
    global lo

    def cambiar():
        lo = "Pedro"

    cambiar()


Thread(target=hilo, name="hilo_secundario").start()

breakpoint()

