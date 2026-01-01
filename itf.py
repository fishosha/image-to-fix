import sys
import os
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import keyboard
import threading
import json

class ModernToggleSwitch:
    def __init__(self, parent, text="", command=None, width=60, height=30):
        self.parent = parent
        self.text = text
        self.command = command
        self.state = False
        
        self.frame = tk.Frame(parent, bg='#2b2b2b')
        
        self.canvas = tk.Canvas(self.frame, width=width, height=height, 
                               bg='#2b2b2b', highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))
        
        self.label = tk.Label(self.frame, text=text, font=('Segoe UI', 10),
                             fg='white', bg='#2b2b2b')
        self.label.pack(side=tk.LEFT)
        
        self.draw_switch()
        self.canvas.bind('<Button-1>', self.toggle)
        self.canvas.bind('<Enter>', self.on_enter)
        self.canvas.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        self.canvas.config(cursor='hand2')
        
    def on_leave(self, e):
        self.canvas.config(cursor='')
        
    def draw_switch(self):
        self.canvas.delete("all")
        
        bg_color = '#27ae60' if self.state else '#7f8c8d'
        outline_color = '#2ecc71' if self.state else '#95a5a6'
        
        self.canvas.create_rectangle(5, 5, 55, 25, fill=bg_color, 
                                    outline=outline_color, width=2)
        
        circle_x = 45 if self.state else 15
        self.canvas.create_oval(circle_x-10, 3, circle_x+10, 27, 
                               fill='white', outline='#bdc3c7', width=2)
        
        state_text = "ON" if self.state else "OFF"
        text_color = 'white' if self.state else '#2c3e50'
        self.canvas.create_text(30, 15, text=state_text, fill=text_color,
                               font=('Segoe UI', 9, 'bold'))
    
    def toggle(self, event=None):
        self.state = not self.state
        self.draw_switch()
        if self.command:
            try:
                self.command()
            except Exception as e:
                print(f"Error in toggle command: {e}")
    
    def get(self):
        return self.state
    
    def set(self, value):
        self.state = value
        self.draw_switch()

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Создаем Canvas и Scrollbar
        self.canvas = tk.Canvas(self, bg='#34495e', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Создаем фрейм для содержимого
        self.scrollable_frame = tk.Frame(self.canvas, bg='#34495e')
        
        # Настраиваем Canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Размещаем элементы
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Бинд для колесика мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Бинд для обновления прокрутки
        self.scrollable_frame.bind("<Configure>", self._update_scrollregion)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _update_scrollregion(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class ImageOverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to Fix Pro")
        self.root.geometry("1200x700")
        
        # Центрируем окно
        self.center_window()
        
        # Настройка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Инициализация переменных
        self.setup_variables()
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Загрузка настроек
        self.load_settings()
        
        # Настройка горячих клавиш
        self.setup_hotkey()
        
        # Статус
        self.update_status("Готов к работе")
        
    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = 1200
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_variables(self):
        """Инициализация переменных"""
        self.image = None
        self.photo_image = None
        self.overlay_window = None
        self.is_pinned = False
        self.bind_key = "ctrl+shift+space"
        self.position = "top-right"
        self.original_size = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.scale_factor = 1.0
        
        # Переменные для ползунков
        self.width_var = tk.IntVar(value=800)
        self.height_var = tk.IntVar(value=600)
        
        # Цветовая схема
        self.colors = {
            'primary': '#3498db',
            'primary_dark': '#2980b9',
            'secondary': '#2ecc71',
            'secondary_dark': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'dark_bg': '#2c3e50',
            'darker_bg': '#1a252f',
            'card_bg': '#34495e',
            'text': '#ecf0f1',
            'text_secondary': '#bdc3c7'
        }
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Устанавливаем цвет фона
        self.root.configure(bg=self.colors['dark_bg'])
        
        # Создаем меню
        self.create_menu()
        
        # Header
        self.create_header()
        
        # Основной контейнер
        self.create_main_container()
        
        # Статус бар
        self.create_status_bar()
    
    def create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть", command=self.load_image)
        file_menu.add_command(label="Сохранить", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing)
        
        # Меню Помощь
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def create_header(self):
        """Создание заголовка"""
        header_frame = tk.Frame(self.root, bg=self.colors['darker_bg'], height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Заголовок с иконкой
        title_frame = tk.Frame(header_frame, bg=self.colors['darker_bg'])
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(title_frame, text="🖼️", font=('Segoe UI', 24),
                bg=self.colors['darker_bg'], fg=self.colors['primary']).pack(side=tk.LEFT)
        
        tk.Label(title_frame, text="Image to Fix Pro", 
                font=('Segoe UI', 20, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['darker_bg']).pack(side=tk.LEFT, padx=10)
        
        # Индикатор состояния
        self.status_indicator = tk.Label(header_frame, text="●", 
                                        font=('Segoe UI', 14),
                                        fg='#2ecc71',
                                        bg=self.colors['darker_bg'])
        self.status_indicator.pack(side=tk.RIGHT, padx=20, pady=15)
        
        self.status_text = tk.Label(header_frame, text="Готов",
                                  font=('Segoe UI', 10),
                                  fg=self.colors['text_secondary'],
                                  bg=self.colors['darker_bg'])
        self.status_text.pack(side=tk.RIGHT, pady=15)
    
    def create_main_container(self):
        """Создание основного контейнера"""
        main_frame = tk.Frame(self.root, bg=self.colors['dark_bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель с прокруткой
        left_container = tk.Frame(main_frame, bg=self.colors['dark_bg'], width=400)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_container.pack_propagate(False)
        
        # Заголовок левой панели
        left_header = tk.Frame(left_container, bg=self.colors['primary'], height=40)
        left_header.pack(fill=tk.X)
        left_header.pack_propagate(False)
        
        tk.Label(left_header, text="Панель настроек", 
                font=('Segoe UI', 12, 'bold'),
                fg='white',
                bg=self.colors['primary']).pack(pady=10)
        
        # Создаем прокручиваемый фрейм для настроек
        self.scrollable_frame = ScrollableFrame(left_container)
        self.scrollable_frame.pack(fill=tk.BOTH, expand=True)
        
        # Контейнер для всех настроек
        settings_container = self.scrollable_frame.scrollable_frame
        
        # Добавляем все настройки
        self.create_control_buttons(settings_container)
        self.create_size_controls(settings_container)
        self.create_position_controls(settings_container)
        self.create_hotkey_controls(settings_container)
        self.create_additional_controls(settings_container)
        
        # Правая панель (предпросмотр)
        self.create_preview_panel(main_frame)
    
    def create_control_buttons(self, parent):
        """Создание кнопок управления"""
        button_frame = tk.LabelFrame(parent, text="Управление изображением",
                                   font=('Segoe UI', 11, 'bold'),
                                   fg=self.colors['text'],
                                   bg=self.colors['card_bg'],
                                   padx=15, pady=15)
        button_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        buttons = [
            ("📁 Загрузить изображение", self.load_image, self.colors['primary']),
            ("💾 Сохранить изображение", self.save_image, self.colors['secondary']),
            ("🗑️ Очистить", self.clear_image, self.colors['danger'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                          font=('Segoe UI', 10),
                          bg=color, fg='white',
                          activebackground=color,
                          relief=tk.FLAT,
                          padx=15, pady=10,
                          cursor='hand2',
                          anchor='w')
            btn.pack(fill=tk.X, pady=5)
    
    def create_size_controls(self, parent):
        """Создание элементов управления размером"""
        size_frame = tk.LabelFrame(parent, text="Настройки размера",
                                 font=('Segoe UI', 11, 'bold'),
                                 fg=self.colors['text'],
                                 bg=self.colors['card_bg'],
                                 padx=15, pady=15)
        size_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Ширина
        tk.Label(size_frame, text="Ширина (px):",
                font=('Segoe UI', 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']).pack(anchor=tk.W, pady=(0, 5))
        
        width_frame = tk.Frame(size_frame, bg=self.colors['card_bg'])
        width_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.width_scale = tk.Scale(width_frame, from_=10, to=2000,
                                  variable=self.width_var,
                                  orient=tk.HORIZONTAL,
                                  length=250,
                                  bg=self.colors['card_bg'],
                                  fg=self.colors['text'],
                                  highlightthickness=0,
                                  troughcolor=self.colors['primary'],
                                  sliderrelief=tk.FLAT,
                                  command=self.on_width_scale_change)
        self.width_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.width_entry = tk.Entry(width_frame, width=8,
                                  font=('Segoe UI', 10),
                                  bg='#2c3e50', fg='white',
                                  justify=tk.CENTER)
        self.width_entry.insert(0, "800")
        self.width_entry.pack(side=tk.RIGHT, padx=(10, 0))
        self.width_entry.bind('<KeyRelease>', self.on_width_entry_change)
        
        # Высота
        tk.Label(size_frame, text="Высота (px):",
                font=('Segoe UI', 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']).pack(anchor=tk.W, pady=(0, 5))
        
        height_frame = tk.Frame(size_frame, bg=self.colors['card_bg'])
        height_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.height_scale = tk.Scale(height_frame, from_=10, to=2000,
                                   variable=self.height_var,
                                   orient=tk.HORIZONTAL,
                                   length=250,
                                   bg=self.colors['card_bg'],
                                   fg=self.colors['text'],
                                   highlightthickness=0,
                                   troughcolor=self.colors['primary'],
                                   sliderrelief=tk.FLAT,
                                   command=self.on_height_scale_change)
        self.height_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.height_entry = tk.Entry(height_frame, width=8,
                                   font=('Segoe UI', 10),
                                   bg='#2c3e50', fg='white',
                                   justify=tk.CENTER)
        self.height_entry.insert(0, "600")
        self.height_entry.pack(side=tk.RIGHT, padx=(10, 0))
        self.height_entry.bind('<KeyRelease>', self.on_height_entry_change)
        
        # Кнопки управления размером
        size_buttons_frame = tk.Frame(size_frame, bg=self.colors['card_bg'])
        size_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(size_buttons_frame, text="Применить размер",
                 command=self.apply_size,
                 font=('Segoe UI', 10),
                 bg=self.colors['warning'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=20, pady=8,
                 cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(size_buttons_frame, text="Сбросить",
                 command=self.reset_size,
                 font=('Segoe UI', 10),
                 bg=self.colors['text_secondary'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=20, pady=8,
                 cursor='hand2').pack(side=tk.LEFT)
    
    def on_width_scale_change(self, value):
        """Обработчик изменения ползунка ширины"""
        try:
            width = int(float(value))
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(width))
        except:
            pass
    
    def on_height_scale_change(self, value):
        """Обработчик изменения ползунка высоты"""
        try:
            height = int(float(value))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(height))
        except:
            pass
    
    def on_width_entry_change(self, event):
        """Обработчик изменения поля ввода ширины"""
        try:
            value = self.width_entry.get()
            if value.strip():
                width = int(value)
                if 10 <= width <= 2000:
                    self.width_scale.set(width)
        except ValueError:
            pass
    
    def on_height_entry_change(self, event):
        """Обработчик изменения поля ввода высоты"""
        try:
            value = self.height_entry.get()
            if value.strip():
                height = int(value)
                if 10 <= height <= 2000:
                    self.height_scale.set(height)
        except ValueError:
            pass
    
    def create_position_controls(self, parent):
        """Создание элементов управления положением"""
        pos_frame = tk.LabelFrame(parent, text="Положение на экране",
                                font=('Segoe UI', 11, 'bold'),
                                fg=self.colors['text'],
                                bg=self.colors['card_bg'],
                                padx=15, pady=15)
        pos_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Сетка позиций
        positions_grid = tk.Frame(pos_frame, bg=self.colors['card_bg'])
        positions_grid.pack()
        
        positions = [
            ("↖", "top-left"), ("⬆", "top-center"), ("↗", "top-right"),
            ("⬅", "middle-left"), ("⏺", "center"), ("➡", "middle-right"),
            ("↙", "bottom-left"), ("⬇", "bottom-center"), ("↘", "bottom-right")
        ]
        
        self.position_var = tk.StringVar(value="top-right")
        
        for i, (symbol, value) in enumerate(positions):
            row, col = divmod(i, 3)
            btn = tk.Radiobutton(positions_grid, text=symbol,
                               variable=self.position_var,
                               value=value,
                               font=('Segoe UI', 14),
                               bg=self.colors['card_bg'],
                               fg=self.colors['text'],
                               selectcolor=self.colors['primary'],
                               indicatoron=0,
                               width=3, height=1,
                               command=self.update_position)
            btn.grid(row=row, column=col, padx=5, pady=5, ipadx=5, ipady=5)
    
    def create_hotkey_controls(self, parent):
        """Создание элементов управления горячими клавишами"""
        hotkey_frame = tk.LabelFrame(parent, text="Горячие клавиши",
                                   font=('Segoe UI', 11, 'bold'),
                                   fg=self.colors['text'],
                                   bg=self.colors['card_bg'],
                                   padx=15, pady=15)
        hotkey_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Текущая горячая клавиша
        hotkey_info = tk.Frame(hotkey_frame, bg=self.colors['card_bg'])
        hotkey_info.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(hotkey_info, text="Текущая клавиша:",
                font=('Segoe UI', 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']).pack(side=tk.LEFT)
        
        self.hotkey_label = tk.Label(hotkey_info, text=self.bind_key,
                                   font=('Segoe UI', 10, 'bold'),
                                   fg=self.colors['primary'],
                                   bg=self.colors['card_bg'])
        self.hotkey_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Настройка горячей клавиши
        tk.Label(hotkey_frame, text="Новая комбинация:",
                font=('Segoe UI', 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']).pack(anchor=tk.W, pady=(5, 0))
        
        hotkey_input_frame = tk.Frame(hotkey_frame, bg=self.colors['card_bg'])
        hotkey_input_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.hotkey_entry = tk.Entry(hotkey_input_frame,
                                   font=('Segoe UI', 10),
                                   bg='#2c3e50', fg='white')
        self.hotkey_entry.insert(0, self.bind_key)
        self.hotkey_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(hotkey_input_frame, text="Обновить",
                 command=self.update_hotkey,
                 font=('Segoe UI', 10),
                 bg=self.colors['primary'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=15,
                 cursor='hand2').pack(side=tk.RIGHT, padx=(5, 0))
        
        # Основная кнопка переключения
        self.toggle_btn = tk.Button(hotkey_frame, text="📌 ВКЛЮЧИТЬ ПОВЕРХ ОКОН",
                                  command=self.toggle_overlay,
                                  font=('Segoe UI', 11, 'bold'),
                                  bg=self.colors['secondary'],
                                  fg='white',
                                  relief=tk.FLAT,
                                  padx=20, pady=12,
                                  cursor='hand2')
        self.toggle_btn.pack(fill=tk.X, pady=(10, 0))
    
    def create_additional_controls(self, parent):
        """Создание дополнительных элементов управления"""
        add_frame = tk.LabelFrame(parent, text="Дополнительные настройки",
                                font=('Segoe UI', 11, 'bold'),
                                fg=self.colors['text'],
                                bg=self.colors['card_bg'],
                                padx=15, pady=15)
        add_frame.pack(fill=tk.X, pady=(0, 5), padx=5)
        
        # Прозрачность
        opacity_frame = tk.Frame(add_frame, bg=self.colors['card_bg'])
        opacity_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(opacity_frame, text="Прозрачность:",
                font=('Segoe UI', 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['card_bg']).pack(side=tk.LEFT)
        
        self.opacity_scale = tk.Scale(opacity_frame, from_=10, to=100,
                                    orient=tk.HORIZONTAL,
                                    length=200,
                                    bg=self.colors['card_bg'],
                                    fg=self.colors['text'],
                                    highlightthickness=0,
                                    troughcolor=self.colors['primary'])
        self.opacity_scale.set(100)
        self.opacity_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # Всегда поверх
        self.always_on_top_var = tk.BooleanVar(value=True)
        on_top_check = tk.Checkbutton(add_frame, 
                                     text="Всегда поверх других окон",
                                     variable=self.always_on_top_var,
                                     font=('Segoe UI', 10),
                                     fg=self.colors['text_secondary'],
                                     bg=self.colors['card_bg'],
                                     selectcolor=self.colors['primary'],
                                     activebackground=self.colors['card_bg'],
                                     activeforeground=self.colors['text'])
        on_top_check.pack(anchor=tk.W, pady=(5, 0))
        
        # Показывать рамку
        self.show_border_var = tk.BooleanVar(value=True)
        border_check = tk.Checkbutton(add_frame, 
                                     text="Показывать рамку вокруг изображения",
                                     variable=self.show_border_var,
                                     font=('Segoe UI', 10),
                                     fg=self.colors['text_secondary'],
                                     bg=self.colors['card_bg'],
                                     selectcolor=self.colors['primary'],
                                     activebackground=self.colors['card_bg'],
                                     activeforeground=self.colors['text'])
        border_check.pack(anchor=tk.W, pady=(5, 0))
    
    def create_preview_panel(self, parent):
        """Создание правой панели с предпросмотром"""
        right_panel = tk.Frame(parent, bg=self.colors['darker_bg'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок предпросмотра с информацией
        preview_header = tk.Frame(right_panel, bg=self.colors['darker_bg'], height=40)
        preview_header.pack(fill=tk.X)
        preview_header.pack_propagate(False)
        
        tk.Label(preview_header, text="Предпросмотр изображения",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['darker_bg']).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Информация об изображении
        self.image_info = tk.Label(preview_header,
                                 text="Нет изображения",
                                 font=('Segoe UI', 10),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['darker_bg'])
        self.image_info.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Контейнер для предпросмотра
        preview_container = tk.Frame(right_panel, bg='black', relief=tk.SUNKEN, bd=2)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Canvas для предпросмотра
        self.preview_canvas = tk.Canvas(preview_container, bg='black',
                                      highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Текст по центру (отображается когда нет изображения)
        self.preview_canvas.create_text(400, 200,
                                       text="Перетащите изображение сюда\nили нажмите 'Загрузить изображение'",
                                       fill='#7f8c8d',
                                       font=('Segoe UI', 12),
                                       justify=tk.CENTER,
                                       tags="placeholder")
        
        # Информация о размере на Canvas
        self.preview_canvas.create_text(400, 300,
                                       text="",
                                       fill='#95a5a6',
                                       font=('Segoe UI', 10),
                                       justify=tk.CENTER,
                                       tags="size_info")
        
        # Настройка drag&drop
        self.setup_drag_drop()
        
        # Масштабирование колесиком мыши
        self.preview_canvas.bind("<MouseWheel>", self.on_preview_zoom)
    
    def setup_drag_drop(self):
        """Настройка drag&drop для Canvas"""
        # В Windows для drag&drop нужно использовать протокол DND
        def on_drop(event):
            # Простая реализация drag&drop
            file_path = event.data
            if file_path:
                self.load_image_file(file_path)
        
        # Упрощенная версия drag&drop
        self.preview_canvas.bind('<Button-1>', lambda e: self.load_image())
    
    def on_preview_zoom(self, event):
        """Масштабирование превью колесиком мыши"""
        if not self.image:
            return
        
        # Определяем направление прокрутки
        if event.delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor *= 0.9
        
        # Ограничиваем масштаб
        self.scale_factor = max(0.1, min(5.0, self.scale_factor))
        
        # Обновляем превью
        self.display_preview()
    
    def create_status_bar(self):
        """Создание статус бара"""
        self.status_bar = tk.Label(self.root, text="Готов к работе",
                                 bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                 font=('Segoe UI', 9),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['darker_bg'])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message):
        """Обновление статуса"""
        self.status_bar.config(text=message)
        self.status_text.config(text=message[:20])
        self.root.update_idletasks()
    
    # Основные функции программы
    
    def load_image(self):
        """Загрузка изображения"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            self.load_image_file(file_path)
    
    def load_image_file(self, file_path):
        """Загрузка изображения из файла"""
        try:
            # Открываем изображение
            self.image = Image.open(file_path)
            self.original_size = self.image.size
            
            # Обновляем UI
            self.display_preview()
            
            # Устанавливаем размеры
            self.width_scale.set(self.image.width)
            self.height_scale.set(self.image.height)
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(self.image.width))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(self.image.height))
            
            # Обновляем информацию
            filename = os.path.basename(file_path)
            info_text = f"{filename} | {self.image.width}×{self.image.height}"
            self.image_info.config(text=info_text)
            
            self.update_status(f"Загружено: {filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{str(e)}")
    
    def display_preview(self):
        """Отображение превью"""
        if not self.image:
            return
        
        # Очищаем Canvas
        self.preview_canvas.delete("all")
        
        # Получаем размер Canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas еще не отрисован, ждем
            self.root.after(100, self.display_preview)
            return
        
        try:
            # Рассчитываем размер для превью с учетом масштаба
            preview_width = int(self.image.width * self.scale_factor)
            preview_height = int(self.image.height * self.scale_factor)
            
            # Изменяем размер изображения
            img_copy = self.image.copy()
            if preview_width != self.image.width or preview_height != self.image.height:
                img_copy = img_copy.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
            
            # Конвертируем для Tkinter
            self.photo_image = ImageTk.PhotoImage(img_copy)
            
            # Центрируем
            x = (canvas_width - preview_width) // 2
            y = (canvas_height - preview_height) // 2
            
            # Отображаем
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.photo_image)
            
            # Рамка если включено
            if self.show_border_var.get():
                self.preview_canvas.create_rectangle(x-1, y-1, 
                                                   x + preview_width + 1, 
                                                   y + preview_height + 1,
                                                   outline=self.colors['primary'], 
                                                   width=2)
            
            # Отображаем информацию о масштабе
            if abs(self.scale_factor - 1.0) > 0.01:
                scale_text = f"Масштаб: {self.scale_factor:.1f}x"
                self.preview_canvas.create_text(canvas_width - 60, 20,
                                               text=scale_text,
                                               fill='white',
                                               font=('Segoe UI', 9),
                                               anchor=tk.NE)
            
            # Отображаем информацию о размере
            size_text = f"Размер: {self.image.width} × {self.image.height}"
            self.preview_canvas.create_text(canvas_width // 2, canvas_height - 20,
                                           text=size_text,
                                           fill='#95a5a6',
                                           font=('Segoe UI', 10))
                
        except Exception as e:
            print(f"Ошибка отображения превью: {e}")
    
    def save_image(self):
        """Сохранение изображения"""
        if not self.image:
            messagebox.showwarning("Внимание", "Нет изображения для сохранения")
            return
        
        # Получаем текущий размер
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
        except:
            width, height = self.image.size
        
        # Изменяем размер если нужно
        if width != self.image.width or height != self.image.height:
            img_to_save = self.image.resize((width, height), Image.Resampling.LANCZOS)
        else:
            img_to_save = self.image
        
        # Сохраняем
        try:
            file_path = filedialog.asksaveasfilename(
                title="Сохранить изображение",
                defaultextension=".png",
                filetypes=[
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg;*.jpeg"),
                    ("Все файлы", "*.*")
                ]
            )
            
            if file_path:
                img_to_save.save(file_path)
                self.update_status(f"Сохранено: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{str(e)}")
    
    def clear_image(self):
        """Очистка изображения"""
        if self.image:
            if messagebox.askyesno("Подтверждение", "Удалить текущее изображение?"):
                self.image = None
                self.photo_image = None
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(400, 200,
                                               text="Перетащите изображение сюда\nили нажмите 'Загрузить изображение'",
                                               fill='#7f8c8d',
                                               font=('Segoe UI', 12),
                                               justify=tk.CENTER,
                                               tags="placeholder")
                self.image_info.config(text="Нет изображения")
                self.scale_factor = 1.0
                self.update_status("Изображение удалено")
    
    def apply_size(self):
        """Применение размера"""
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            
            if width <= 0 or height <= 0:
                raise ValueError("Размер должен быть положительным числом")
            
            # Обновляем слайдеры
            self.width_scale.set(width)
            self.height_scale.set(height)
            
            # Обновляем превью
            if self.image:
                self.display_preview()
            
            self.update_status(f"Размер установлен: {width}×{height}")
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный размер:\n{str(e)}")
    
    def reset_size(self):
        """Сброс размера к оригинальному"""
        if self.image and self.original_size:
            self.width_scale.set(self.original_size[0])
            self.height_scale.set(self.original_size[1])
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, str(self.original_size[0]))
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, str(self.original_size[1]))
            self.scale_factor = 1.0
            self.display_preview()
            self.update_status("Размер сброшен к оригинальному")
    
    def update_position(self):
        """Обновление позиции"""
        if self.overlay_window:
            self.move_overlay_to_position()
    
    def toggle_overlay(self):
        """Переключение режима поверх окон"""
        if not self.image:
            messagebox.showwarning("Внимание", "Сначала загрузите изображение")
            return
        
        self.is_pinned = not self.is_pinned
        
        if self.is_pinned:
            self.create_overlay()
            self.toggle_btn.config(text="📌 ОТКЛЮЧИТЬ ПОВЕРХ ОКОН", 
                                 bg=self.colors['danger'])
            self.status_indicator.config(fg='#e74c3c')
            self.update_status("Режим поверх окон ВКЛЮЧЕН")
        else:
            self.destroy_overlay()
            self.toggle_btn.config(text="📌 ВКЛЮЧИТЬ ПОВЕРХ ОКОН", 
                                 bg=self.colors['secondary'])
            self.status_indicator.config(fg='#2ecc71')
            self.update_status("Режим поверх окон ВЫКЛЮЧЕН")
    
    def create_overlay(self):
        """Создание окна поверх других окон"""
        if self.overlay_window:
            self.overlay_window.destroy()
        
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
        except:
            width, height = self.image.size
        
        # Создаем окно
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.overrideredirect(True)
        
        if self.always_on_top_var.get():
            self.overlay_window.attributes('-topmost', True)
        
        self.overlay_window.configure(bg='black')
        
        # Устанавливаем прозрачность
        opacity = self.opacity_scale.get() / 100.0
        self.overlay_window.attributes('-alpha', opacity)
        
        # Изменяем размер изображения
        resized_image = self.image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Конвертируем для Tkinter
        photo = ImageTk.PhotoImage(resized_image)
        
        # Создаем Label с изображением
        label = tk.Label(self.overlay_window, image=photo, bg='black')
        label.image = photo
        label.pack()
        
        # Устанавливаем позицию
        self.move_overlay_to_position()
        
        # Добавляем возможность перетаскивания
        label.bind('<Button-1>', self.start_move)
        label.bind('<B1-Motion>', self.on_move)
        label.bind('<ButtonRelease-1>', self.stop_move)
        
        # Добавляем возможность закрытия по ПКМ
        label.bind('<Button-3>', lambda e: self.toggle_overlay())
    
    def start_move(self, event):
        """Начало перемещения окна"""
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
    
    def on_move(self, event):
        """Перемещение окна"""
        x = self.overlay_window.winfo_x() + (event.x - self.drag_data['x'])
        y = self.overlay_window.winfo_y() + (event.y - self.drag_data['y'])
        self.overlay_window.geometry(f"+{x}+{y}")
    
    def stop_move(self, event):
        """Окончание перемещения окна"""
        self.drag_data['x'] = 0
        self.drag_data['y'] = 0
    
    def move_overlay_to_position(self):
        """Перемещение окна в выбранную позицию"""
        if not self.overlay_window:
            return
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
        except:
            width, height = 800, 600
        
        position = self.position_var.get()
        
        if position == "top-left":
            x, y = 10, 30
        elif position == "top-center":
            x = (screen_width - width) // 2
            y = 30
        elif position == "top-right":
            x = screen_width - width - 10
            y = 30
        elif position == "middle-left":
            x = 10
            y = (screen_height - height) // 2
        elif position == "center":
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        elif position == "middle-right":
            x = screen_width - width - 10
            y = (screen_height - height) // 2
        elif position == "bottom-left":
            x = 10
            y = screen_height - height - 50
        elif position == "bottom-center":
            x = (screen_width - width) // 2
            y = screen_height - height - 50
        elif position == "bottom-right":
            x = screen_width - width - 10
            y = screen_height - height - 50
        else:
            x, y = 100, 100
        
        self.overlay_window.geometry(f"{width}x{height}+{x}+{y}")
    
    def destroy_overlay(self):
        """Уничтожение окна поверх окон"""
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
    
    def update_hotkey(self):
        """Обновление горячей клавиши"""
        new_bind = self.hotkey_entry.get().strip()
        
        if new_bind:
            try:
                # Удаляем старый бинд
                try:
                    keyboard.remove_hotkey(self.bind_key)
                except:
                    pass
                
                # Добавляем новый
                keyboard.add_hotkey(new_bind, self.toggle_overlay)
                self.bind_key = new_bind
                self.hotkey_label.config(text=new_bind)
                
                # Сохраняем настройки
                self.save_settings()
                
                self.update_status(f"Горячая клавиша обновлена: {new_bind}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверная горячая клавиша:\n{str(e)}")
                self.hotkey_entry.delete(0, tk.END)
                self.hotkey_entry.insert(0, self.bind_key)
    
    def setup_hotkey(self):
        """Настройка горячей клавиши"""
        try:
            keyboard.add_hotkey(self.bind_key, self.toggle_overlay)
        except Exception as e:
            print(f"Ошибка настройки горячей клавиши: {e}")
    
    # Настройки
    
    def load_settings(self):
        """Загрузка настроек"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.bind_key = settings.get('bind_key', 'ctrl+shift+space')
                    self.position = settings.get('position', 'top-right')
                    self.hotkey_entry.delete(0, tk.END)
                    self.hotkey_entry.insert(0, self.bind_key)
                    self.hotkey_label.config(text=self.bind_key)
                    self.position_var.set(self.position)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    
    def save_settings(self):
        """Сохранение настроек"""
        try:
            settings = {
                'bind_key': self.bind_key,
                'position': self.position_var.get(),
                'last_saved': datetime.now().isoformat()
            }
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    def show_about(self):
        """Показать информацию о программе"""
        messagebox.showinfo("О программе",
                          "Image to Fix Pro v2.0\n\n" +
                          "Программа для работы с изображениями поверх окон.\n\n" +
                          "Функции:\n" +
                          "• Загрузка и сохранение изображений\n" +
                          "• Изменение размера изображений\n" +
                          "• Закрепление поверх всех окон\n" +
                          "• Настраиваемые горячие клавиши\n" +
                          "• Выбор положения на экране\n\n" +
                          "© 2024 Все права защищены")
    
    def on_closing(self):
        """Обработка закрытия программы"""
        try:
            keyboard.unhook_all()
        except:
            pass
        
        self.destroy_overlay()
        self.save_settings()
        
        self.root.quit()
        self.root.destroy()

def main():
    """Основная функция"""
    try:
        root = tk.Tk()
        app = ImageOverlayApp(root)
        
        # Обновляем превью после отрисовки окна
        def update_preview():
            app.display_preview()
            root.after(100, update_preview)
        
        root.after(100, update_preview)
        root.mainloop()
        
    except Exception as e:
        print("❌ Критическая ошибка в программе:")
        print(traceback.format_exc())
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()