import sys
import os



res = input("Pon algo: ")
dict = {"hol": 123456}

if res == ".":
    os.system("cls")
    os.execv(sys.executable, [sys.executable, '"' + str(__file__) + '"'])


breakpoint()

