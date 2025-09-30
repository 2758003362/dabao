import tkinter as tk
from tkinter import messagebox

# 创建主窗口
root = tk.Tk()
root.title("Hello World 表单")

# 创建按钮，点击后弹出消息
button = tk.Button(root, text="点击我", command=lambda: messagebox.showinfo("提示", "Hello World!"))
button.pack(pady=20)

# 运行主循环
root.mainloop()
