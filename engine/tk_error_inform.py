import tkinter as tk
import os
from tkinter import ttk
import requests
import webbrowser
import urllib.parse


def open_email_client(to_email, subject="", body=""):
    base_url = "https://mail.google.com/mail/?view=cm&fs=1"
    params = {"to": to_email}

    if subject:
        params["su"] = urllib.parse.quote(subject)
    if body:
        params["body"] = urllib.parse.quote(body)

    url = base_url + "&" + "&".join(f"{key}={value}" for key, value in params.items())
    webbrowser.open(url)

def has_internet(timeout=3):
    try:
        requests.get("https://www.google.com", timeout=timeout)
        return True
    except requests.RequestException:
        return False

class ErrorWindow(tk.Toplevel):
    def __init__(self, master, title, text, telemetry):
        super().__init__(master)

        self.master = master
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.title(title)
        self.resizable(True, True)

        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))

        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        header = ttk.Label(
            container,
            text="Упс! Произошла непредвиденная ошибка.",
            font=("Segoe UI", 14, "bold")
        )
        header.pack(anchor="w")

        sub_sub_text = None
        if has_internet() and telemetry:
            sub_text = "Логи были отправлены и наша команда уже работает над исправлением этого бага!"
        else:
            sub_text = "У вас отсутствует подключение к интернету или отключена телеметрия! К сожалению, мы не можем отправить ваши логи :("
            sub_sub_text = "Пожалуйста, скопируйте логи игры и свяжитесь с разработчиками, чтобы мы могли исправить эту ошибку."

        sub = ttk.Label(
            container,
            text=sub_text,
            font=("Segoe UI", 10)
        )
        sub.pack(anchor="w", pady=(2, 8))

        if sub_sub_text:
            sub_sub = ttk.Label(
                container,
                text=sub_sub_text,
                font=("Segoe UI", 10),
                foreground="red"
            )
            sub_sub.pack(anchor="w", pady=(2, 8))

        # --- traceback + scrollbar ---
        frame = ttk.Frame(container)
        frame.pack(fill="both", expand=True)

        yscroll = ttk.Scrollbar(frame)
        yscroll.pack(side="right", fill="y")

        xscroll = ttk.Scrollbar(frame, orient="horizontal")
        xscroll.pack(side="bottom", fill="x")

        self.text = tk.Text(
            frame,
            height=12,
            width=70,
            wrap="none",
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set,
            font=("Consolas", 10)
        )
        self.text.pack(side="left", fill="both", expand=True)

        yscroll.config(command=self.text.yview)
        xscroll.config(command=self.text.xview)

        self.text.insert("1.0", text)
        self.text.config(state="disabled")

        # --- buttons ---
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="Копировать логи",
            command=self.copy_text
        ).pack(side="left")

        # Кликабельные ссылки для связи
        contacts_frame = ttk.Frame(btn_frame)
        contacts_frame.pack(side="left", padx=(20, 0))


        error_log_email_text = f"""
        ===============================
        Пожалуйста, вставьте сюда логи игры, скопировав их на кнопку "Копировать логи":
        """

        # Email ссылка
        email_link = tk.Label(
            contacts_frame,
            text="📧 romat3422@gmail.com",
            font=("Segoe UI", 9),
            fg="blue",
            cursor="hand2"
        )
        email_link.pack(side="left", padx=(0, 10))
        email_link.bind("<Button-1>", lambda e: open_email_client("romat3422@gmail.com", f"Error log", error_log_email_text))

        # Telegram ссылка
        telegram_link = tk.Label(
            contacts_frame,
            text="💬 t.me/br0mand",
            font=("Segoe UI", 9),
            fg="blue",
            cursor="hand2"
        )
        telegram_link.pack(side="left")
        telegram_link.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/br0mand"))

        ttk.Button(
            btn_frame,
            text="Закрыть",
            command=self.close
        ).pack(side="right")

        self.update_idletasks()
        self._center()


    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", "end"))

    def close(self):
        self.destroy()
        self.master.quit()

def get_save_path():
    if os.name == 'nt':  # Windows
        # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        save_dir = os.path.join(app_data, 'OneDay')
    else:
        # Linux/Mac
        save_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'OneDay')

    os.makedirs(save_dir, exist_ok=True)

    file = os.path.join(save_dir, "latest_full.log")

    return file

def get_full_logs():
    file = get_save_path()
    with open(file, "r", encoding="UTF-8") as logs:
        logs = logs.read()
    return logs

def show_error(exc_type, telemetry = True):

    root = tk.Tk()
    root.withdraw()

    ErrorWindow(root, f"Ошибка: {exc_type.__name__}", get_full_logs(), telemetry)

    root.mainloop()