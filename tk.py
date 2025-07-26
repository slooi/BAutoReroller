import tkinter as tk

window = tk.Tk()

label = tk.Label(window)
label.pack()

photo = tk.PhotoImage(file="t.png")
label.config(image=photo)

window.mainloop()

