import sys
import os



res = input("Pon algo: ")

if res == ".":
    os.system("cls")
    os.execv(sys.executable, [sys.executable, '"' + str(__file__) + '"'])


breakpoint()

