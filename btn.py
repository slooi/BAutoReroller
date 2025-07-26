import tkinter as tk
import time
import random
import threading


done = False
def worker():
    counter=0
    while not done:
        time.sleep(1)
        counter+=1
        print(counter)

threading.Thread(target=worker).start()
input("press anything to cancel")
done=True




# w = tk.Tk()
 
# def wait():
#     time.sleep(3)

# b=tk.Button(w,text="fuk",command=lambda: threading.Thread(target=wait).start())
# b.pack()

# l=tk.Label(w)
# l.pack()
# def change():
#     l.config(text=f"{random.randint(0,1000)}")

# b2=tk.Button(w,text="random text",command=change)
# b2.pack()

# w.mainloop()