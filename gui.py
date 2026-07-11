import tkinter as tk
from employee import send_document

root = tk.Tk()
tk.Label(root, text="File Path").pack(); path = tk.Entry(root); path.pack()
tk.Label(root, text="Name").pack(); name = tk.Entry(root); name.pack()
tk.Label(root, text="Email").pack(); email = tk.Entry(root); email.pack()
tk.Label(root, text="Recipient").pack(); recipient = tk.Entry(root); recipient.pack()
tk.Label(root, text="PIN").pack(); pin = tk.Entry(root, show="*"); pin.pack()

def submit():
    send_document(path.get(), 1, name.get(), email.get(), recipient.get(), pin.get())

tk.Button(root, text="Send", command=submit).pack()
root.mainloop()