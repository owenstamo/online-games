import time
import _thread

a = 1

def func():
    global a
    while True:
        a += 1
        time.sleep(0.1/60)

_thread.start_new_thread(func, ())
while True:
    if a % 100 == 0:
        print(a)

    time.sleep(0.1 / 60)
input()