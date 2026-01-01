import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import keyboard
import threading
import os
import sys

class ImageOverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Overlay Tool")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Стиль
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Цветовая схема
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#3498db',
            'secondary': '#34495e',
            'success': '#27ae60',
            'danger': '#e74c3c'
        }
        
        # Переменные
        self.image = None
        self.photo_image = None
        self.overlay_window = None
        self.is_pinned = False
        self.bind_key = "ctrl+shift+space"  # Бинд по умолчанию
        
        # Настройка горячей клавиши
        self.setup_hotkey()
        
        # Загрузка иконки
        self.setup_icon()
        
        # Создание интерфейса
        self.setup_ui()
        
        # Бинд закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_icon(self):
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
    
    def setup_hotkey(self):
        keyboard.unhook_all()  # Очистка старых биндов
        try:
            keyboard.add_hotkey(self.bind_key, self.toggle_overlay)
            print(f"Горячая клавиша установлена: {self.bind_key}")
        except:
            print("Ошибка установки горячей клавиши")
    
    def setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            title_frame,
            text="Image Overlay Tool",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Закрепляйте изображения поверх всех окон",
            font=('Segoe UI', 10),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg=self.colors['secondary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Левая панель (управление)
        control_frame = tk.Frame(main_frame, bg=self.colors['secondary'])
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Кнопки управления
        buttons = [
            ("📁 Загрузить изображение", self.load_image, self.colors['accent']),
            ("📐 Изменить размер", self.resize_image, self.colors['success']),
            ("📍 Показать/Скрыть поверх окон", self.toggle_overlay, self.colors['danger']),
            ("⚙️ Настройки", self.open_settings, self.colors['secondary']),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                control_frame,
                text=text,
                command=command,
                font=('Segoe UI', 10),
                bg=color,
                fg='white',
                activebackground=color,
                activeforeground='white',
                relief=tk.FLAT,
                padx=20,
                pady=10,
                width=25
            )
            btn.pack(pady=5, fill=tk.X)
        
        # Настройка горячей клавиши
        hotkey_frame = tk.Frame(control_frame, bg=self.colors['secondary'])
        hotkey_frame.pack(pady=20, fill=tk.X)
        
        tk.Label(
            hotkey_frame,
            text="Горячая клавиша:",
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['secondary']
        ).pack(anchor=tk.W)
        
        self.hotkey_entry = tk.Entry(
            hotkey_frame,
            font=('Segoe UI', 10),
            bg='white',
            fg='black'
        )
        self.hotkey_entry.insert(0, self.bind_key)
        self.hotkey_entry.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(
            hotkey_frame,
            text="Обновить горячую клавишу",
            command=self.update_hotkey,
            font=('Segoe UI', 9),
            bg=self.colors['accent'],
            fg='white'
        ).pack(pady=(5, 0), fill=tk.X)
        
        # Статус
        self.status_label = tk.Label(
            control_frame,
            text="Статус: Окно скрыто",
            font=('Segoe UI', 9),
            fg=self.colors['success'],
            bg=self.colors['secondary']
        )
        self.status_label.pack(pady=20)
        
        # Правая панель (предпросмотр)
        preview_frame = tk.Frame(main_frame, bg='black')
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            preview_frame,
            text="Предпросмотр изображения",
            font=('Segoe UI', 11, 'bold'),
            fg='white',
            bg='black'
        ).pack(pady=10)
        
        self.preview_label = tk.Label(
            preview_frame,
            text="Изображение не загружено",
            font=('Segoe UI', 10),
            fg='#888',
            bg='black'
        )
        self.preview_label.pack(expand=True)
        
        # Информационная панель
        info_frame = tk.Frame(self.root, bg=self.colors['bg'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(
            info_frame,
            text="📌 Используйте горячую клавишу для быстрого переключения режима поверх окон",
            font=('Segoe UI', 8),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.image = Image.open(file_path)
                self.display_preview()
                messagebox.showinfo("Успех", f"Изображение загружено: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")
    
    def display_preview(self):
        if self.image:
            # Изменяем размер для предпросмотра
            preview_size = (400, 400)
            img_copy = self.image.copy()
            img_copy.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            self.photo_image = ImageTk.PhotoImage(img_copy)
            self.preview_label.configure(
                image=self.photo_image,
                text="",
                bg='black'
            )
    
    def resize_image(self):
        if not self.image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        
        resize_window = tk.Toplevel(self.root)
        resize_window.title("Изменение размера")
        resize_window.geometry("300x200")
        resize_window.configure(bg=self.colors['bg'])
        
        tk.Label(
            resize_window,
            text="Новая ширина:",
            font=('Segoe UI', 10),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        ).pack(pady=(20, 5))
        
        width_entry = tk.Entry(resize_window, font=('Segoe UI', 10))
        width_entry.insert(0, str(self.image.width))
        width_entry.pack(pady=5)
        
        tk.Label(
            resize_window,
            text="Новая высота:",
            font=('Segoe UI', 10),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        ).pack(pady=5)
        
        height_entry = tk.Entry(resize_window, font=('Segoe UI', 10))
        height_entry.insert(0, str(self.image.height))
        height_entry.pack(pady=5)
        
        def apply_resize():
            try:
                new_width = int(width_entry.get())
                new_height = int(height_entry.get())
                
                if new_width <= 0 or new_height <= 0:
                    raise ValueError("Размер должен быть положительным числом")
                
                self.image = self.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.display_preview()
                resize_window.destroy()
                messagebox.showinfo("Успех", f"Размер изменен на {new_width}x{new_height}")
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неверный размер: {str(e)}")
        
        tk.Button(
            resize_window,
            text="Применить",
            command=apply_resize,
            font=('Segoe UI', 10),
            bg=self.colors['accent'],
            fg='white'
        ).pack(pady=20)
    
    def create_overlay(self):
        if not self.image:
            return
        
        if self.overlay_window:
            self.overlay_window.destroy()
        
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.overrideredirect(True)  # Убираем рамки
        self.overlay_window.attributes('-topmost', True)  # Поверх всех окон
        
        if self.is_pinned:
            self.overlay_window.attributes('-disabled', True)  # Отключаем взаимодействие
            self.overlay_window.attributes('-transparentcolor', 'black')  # Прозрачный фон для кликов
        
        # Преобразуем изображение для Tkinter
        photo = ImageTk.PhotoImage(self.image)
        
        label = tk.Label(self.overlay_window, image=photo, bg='black')
        label.image = photo  # Сохраняем ссылку
        label.pack()
        
        # Размещаем в правом верхнем углу
        screen_width = self.overlay_window.winfo_screenwidth()
        screen_height = self.overlay_window.winfo_screenheight()
        
        window_width = self.image.width
        window_height = self.image.height
        
        x = screen_width - window_width - 20
        y = 20
        
        self.overlay_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def toggle_overlay(self):
        if not self.image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение")
            return
        
        self.is_pinned = not self.is_pinned
        
        if self.is_pinned:
            self.create_overlay()
            self.status_label.config(
                text="Статус: Поверх всех окон ✓",
                fg=self.colors['success']
            )
            print("Изображение закреплено поверх окон")
        else:
            if self.overlay_window:
                self.overlay_window.destroy()
                self.overlay_window = None
            self.status_label.config(
                text="Статус: Окно скрыто",
                fg=self.colors['danger']
            )
            print("Изображение скрыто")
    
    def update_hotkey(self):
        new_bind = self.hotkey_entry.get().strip()
        
        if new_bind:
            try:
                keyboard.unhook_all()
                keyboard.add_hotkey(new_bind, self.toggle_overlay)
                self.bind_key = new_bind
                messagebox.showinfo("Успех", f"Горячая клавиша обновлена: {new_bind}")
                print(f"Новая горячая клавиша: {new_bind}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверная горячая клавиша: {str(e)}")
                self.hotkey_entry.delete(0, tk.END)
                self.hotkey_entry.insert(0, self.bind_key)
    
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.colors['bg'])
        
        tk.Label(
            settings_window,
            text="Настройки программы",
            font=('Segoe UI', 16, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        ).pack(pady=20)
        
        # Описание горячих клавиш
        info_text = """
        Поддерживаемые комбинации клавиш:
        
        • ctrl + shift + [любая буква/цифра]
        • alt + shift + [любая буква/цифра]
        • ctrl + alt + [любая буква/цифра]
        
        Примеры:
        ctrl+shift+a
        alt+shift+f5
        ctrl+alt+space
        """
        
        tk.Label(
            settings_window,
            text=info_text,
            font=('Segoe UI', 9),
            fg=self.colors['fg'],
            bg=self.colors['bg'],
            justify=tk.LEFT
        ).pack(pady=10, padx=20)
        
        tk.Button(
            settings_window,
            text="Закрыть",
            command=settings_window.destroy,
            font=('Segoe UI', 10),
            bg=self.colors['accent'],
            fg='white'
        ).pack(pady=20)
    
    def on_closing(self):
        keyboard.unhook_all()  # Очищаем бинды при закрытии
        if self.overlay_window:
            self.overlay_window.destroy()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ImageOverlayApp(root)
    
    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()