import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import os
import json
import copy

# ==========================================
# СЛОЙ 1: ДАННЫЕ (Model Layer)
# ==========================================
class SpriteModel:
    """Хранит состояние проекта, кадры, историю и настройки."""
    def __init__(self):
        self.project_name = "Безымянный спрайт"
        self.width = 32
        self.height = 32
        self.bg_color = "#1e1e1e"
        self.fps = 12
        self.frames = []
        self.frame_durations = []
        self.current_frame_idx = 0

        """Отвечает за историю для Undo/Redo"""
        self.history = []
        self.future = []

        self.reset_project(32, 32, "#1e1e1e")

    def reset_project(self, width, height, bg_color):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.frames = [[[None for _ in range(height)] for _ in range(width)]]
        self.frame_durations = [100] # Длительность в мс
        self.current_frame_idx = 0
        self.history.clear()
        self.future.clear()

    def save_state(self):
        """Сохраняет текущее состояние кадров для Undo."""
        self.history.append(copy.deepcopy(self.frames))
        if len(self.history) > 50: # Ограничение памяти
            self.history.pop(0)
        self.future.clear()

    def undo(self):
        if self.history:
            self.future.append(copy.deepcopy(self.frames))
            self.frames = self.history.pop()
            return True
        return False

    def redo(self):
        if self.future:
            self.history.append(copy.deepcopy(self.frames))
            self.frames = self.future.pop()
            return True
        return False

    def add_frame(self):
        self.save_state()
        new_frame = [[None for _ in range(self.height)] for _ in range(self.width)]
        self.frames.append(new_frame)
        self.frame_durations.append(100)
        self.current_frame_idx = len(self.frames) - 1

    def duplicate_frame(self):
        self.save_state()
        current_data = copy.deepcopy(self.frames[self.current_frame_idx])
        self.frames.insert(self.current_frame_idx + 1, current_data)
        self.frame_durations.insert(self.current_frame_idx + 1, self.frame_durations[self.current_frame_idx])
        self.current_frame_idx += 1

    def delete_frame(self):
        if len(self.frames) > 1:
            self.save_state()
            self.frames.pop(self.current_frame_idx)
            self.frame_durations.pop(self.current_frame_idx)
            self.current_frame_idx = max(0, self.current_frame_idx - 1)
            return True
        return False

    def get_current_frame(self):
        return self.frames[self.current_frame_idx]

    def set_pixel(self, x, y, color, size=1):
        for dx in range(size):
            for dy in range(size):
                if 0 <= x+dx < self.width and 0 <= y+dy < self.height:
                    self.frames[self.current_frame_idx][x+dx][y+dy] = color

    def get_pixel(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.frames[self.current_frame_idx][x][y]
        return None

    def flood_fill(self, x, y, target, replacement):
        if target == replacement: return
        queue = [(x, y)]
        while queue:
            cx, cy = queue.pop(0)
            if not (0 <= cx < self.width and 0 <= cy < self.height): continue
            if self.get_pixel(cx, cy) != target: continue
            self.frames[self.current_frame_idx][cx][cy] = replacement
            queue.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])

# ==========================================
# СЛОЙ 2: ИНТЕРФЕЙС И ЛОГИКА (View/Controller)
# ==========================================
COLOR_BG = "#1e1e1e"
COLOR_PANEL = "#252526"
COLOR_ACCENT = "#c99e00"
COLOR_TEXT = "#e0e0e0"
FONT_MAIN = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 11, "bold")

BASE_PALETTE = [
    "#000000", "#1D2B53", "#7E2553", "#008751",
    "#AB5236", "#5F574F", "#C2C3C7", "#FFF1E8",
    "#FF004D", "#FFA300", "#FFEC27", "#00E436",
    "#29ADFF", "#83769C", "#FF77A8", "#FFCCAA"
]

"""Создаём диалог создания нового проекта"""
class NewProjectDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Новый проект")
        self.geometry("400x350")
        self.configure(bg=COLOR_PANEL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.bg_color = COLOR_BG

        tk.Label(self, text="НОВЫЙ ПРОЕКТ", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack(pady=15)

        """Данные строки отвечают за имя проекта"""
        tk.Label(self, text="Название проекта:", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w", padx=20)
        self.name_entry = tk.Entry(self, bg=COLOR_BG, fg="white", insertbackground="white", font=FONT_MAIN)
        self.name_entry.insert(0, "Безымянный спрайт")
        self.name_entry.pack(fill="x", padx=20, pady=(0, 10))

        frame_dims = tk.Frame(self, bg=COLOR_PANEL)
        frame_dims.pack(fill="x", padx=20)

        """Данные строки отвечают за ширину холста"""
        tk.Label(frame_dims, text="Ширина (px):", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).grid(row=0, column=0, sticky="w", pady=5)
        self.width_spin = tk.Spinbox(frame_dims, from_=1, to=1000, width=10, bg=COLOR_BG, fg="white", buttonbackground="#444", font=FONT_MAIN)
        self.width_spin.delete(0, "end")
        self.width_spin.insert(0, "32")
        self.width_spin.grid(row=0, column=1, pady=5)

        """Данные строки отвечают за ширину холста"""
        tk.Label(frame_dims, text="Высота (px):", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).grid(row=0, column=2, sticky="w", padx=10, pady=5)
        self.height_spin = tk.Spinbox(frame_dims, from_=1, to=1000, width=10, bg=COLOR_BG, fg="white", buttonbackground="#444", font=FONT_MAIN)
        self.height_spin.delete(0, "end")
        self.height_spin.insert(0, "32")
        self.height_spin.grid(row=0, column=3, pady=5)

        self.error_label = tk.Label(self, text="Размер должен быть от 8 до 512 пикселей!", bg=COLOR_PANEL, fg="#ff5555", font=FONT_MAIN)

        """Данные строки отвечают за фон холста"""
        tk.Label(self, text="Фон холста:", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w", padx=20, pady=(10, 0))
        self.bg_btn = tk.Button(self, text="Выбрать фон", bg=COLOR_BG, fg="white", command=self.choose_bg)
        self.bg_btn.pack(anchor="w", padx=20, pady=5)

        """Данная строка отвечает на ошибку в программе"""
        self.error_label = tk.Label(self, text="Размер должен быть от 8 до 512 пикселей!", bg=COLOR_PANEL, fg="#ff5555", font=FONT_MAIN)

        """Данные строки нужны для создания кнопок"""
        btn_frame = tk.Frame(self, bg=COLOR_PANEL)
        btn_frame.pack(side="bottom", fill="x", pady=15)

        tk.Button(btn_frame, text="Отмена", bg="#444", fg="white", font=FONT_MAIN, command=self.cancel).pack(side="left", padx=20, expand=True)
        self.create_btn = tk.Button(btn_frame, text="Создать", bg=COLOR_ACCENT, fg="black", font=FONT_MAIN, command=self.validate_and_accept)
        self.create_btn.pack(side="right", padx=20, expand=True)

        self.width_spin.bind("<KeyRelease>", self.validate)
        self.height_spin.bind("<KeyRelease>", self.validate)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.validate()

    def choose_bg(self):
        color = colorchooser.askcolor(title="Цвет фона", color=self.bg_color)[1]
        if color:
            self.bg_color = color
            self.bg_btn.config(bg=color, fg="black" if color != "#000000" else "white")

    def validate(self, event = None):
        try:
            w, h = int(self.width_spin.get()), int(self.height_spin.get())
            if w < 8 or w > 512 or h < 8 or h > 512:
                self.create_btn.config(state="disabled", bg="#333", fg="#666")
                self.error_label.pack(before=self.create_btn.master)
            else:
                self.create_btn.config(state="normal", bg=COLOR_ACCENT, fg="black")
                self.error_label.pack_forget()
        except ValueError:
            self.create_btn.config(state="disabled", bg="#333", fg="#666")

    def validate_and_accept(self):
        """Делает жёсткую фиксацию данных перед закрытием"""
        self.result = (self.name_entry.get(), int(self.width_spin.get()), int(self.height_spin.get()), self.bg_color)
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

"""Отвечает за диалог экспорта"""
class ExportDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Экспорт спрайта")
        self.geometry("400x400")
        self.configure(bg=COLOR_PANEL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None

        tk.Label(self, text="ЭКСПОРТ СПРАЙТА", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack(pady=15)

        frame = tk.Frame(self, bg=COLOR_PANEL)
        frame.pack(fill="x", padx=20)

        tk.Label(frame, text="Имя файла:", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
        self.name_input = tk.Entry(frame, bg=COLOR_BG, fg="white", insertbackground="white", font=FONT_MAIN)
        self.name_input.insert(0, "sprite")
        self.name_input.pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Формат:", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
        self.format_combo = ttk.Combobox(frame, values=["PNG", "Sprite Sheet"], state="readonly", font=FONT_MAIN)
        self.format_combo.current(0)
        self.format_combo.pack(fill="x", pady=(0, 10))

        tk.Label(frame, text="Масштаб:", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
        self.scale_combo = ttk.Combobox(frame, values=["1x", "2x", "4x", "8x"], state="readonly", font=FONT_MAIN)
        self.scale_combo.current(3)
        self.scale_combo.pack(fill="x", pady=(0, 10))

        btn_frame = tk.Frame(self, bg=COLOR_PANEL)
        btn_frame.pack(side="bottom", fill="x", pady=20)

        tk.Button(btn_frame, text="Отмена", bg="#444", fg="white", font=FONT_MAIN, command=self.cancel).pack(side="left", padx=20, expand=True)
        tk.Button(btn_frame, text="Экспортировать", bg=COLOR_ACCENT, fg="black", font=FONT_MAIN, command=self.accept).pack(side="right", padx=20, expand=True)

    def accept(self):
        scale_map = {"1x": 1, "2x": 2, "4x": 4, "8x": 8}
        self.result = (self.name_input.get(), self.format_combo.get(), scale_map[self.scale_combo.get()])
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

"""Отвечает за экран загрузки и успеха экспортирования"""
class LoadingDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Экспорт")
        self.geometry("300x150")
        self.configure(bg=COLOR_PANEL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.callback = callback
        tk.Label(self, text="⏳ ЭКСПОРТИРУЕМ СПРАЙТ\nПодготавливаем пиксели...", bg=COLOR_PANEL, fg=COLOR_ACCENT, font=FONT_MAIN).pack(pady=40)

        self.after(1500, self.finish) # """Делает имитацию 1.5 сек"""

    def finish(self):
        self.destroy()
        self.callback()

class SuccessDialog(tk.Toplevel):
    def __init__(self, parent, filename):
        super().__init__(parent)
        self.title("Успех")
        self.geometry("300x200")
        self.configure(bg=COLOR_PANEL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="✅", bg=COLOR_PANEL, fg="green", font=("Segoe UI", 40)).pack(pady=10)
        tk.Label(self, text="Спрайт готов!", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack()
        tk.Label(self, text=f"Файл {filename} успешно сохранен.", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(pady=5)

        tk.Button(self, text="Вернуться в редактор", bg=COLOR_ACCENT, fg="black", font=FONT_MAIN, command=self.destroy).pack(pady=15)

"""Отвечает за главное окно программы"""
class SpriteStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("8-bit Sprite Studio")
        self.geometry("1200x800")
        self.configure(bg=COLOR_BG)

        self.model = SpriteModel()

        # Состояния
        self.current_tool = "pencil"
        self.primary_color = BASE_PALETTE[0]
        self.brush_size = 1
        self.zoom = 1.0
        self.show_grid = True
        self.snap_to_grid = False
        self.is_playing = False
        self.play_job = None
        self.last_x, self.last_y = None, None

        self.init_menu()
        self.init_ui()

        self.after(100, self.show_new_project_dialog)

    def init_menu(self):
        menubar = tk.Menu(self, bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN)

        """Отвечает за панель Файл"""
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN)
        file_menu.add_command(label="Новый проект", command=self.show_new_project_dialog)
        file_menu.add_command(label="Экспорт...", command=self.show_export_dialog)
        menubar.add_cascade(label="Файл", menu=file_menu)

        """Отвечает за панель Правка"""
        edit_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN)
        edit_menu.add_command(label="Отменить (Ctrl+Z)", command=self.undo_action)
        edit_menu.add_command(label="Повторить (Ctrl+Y)", command=self.redo_action)
        menubar.add_cascade(label="Правка", menu=edit_menu)

        """Отвечает за панель Вид"""
        view_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN)
        view_menu.add_checkbutton(label="Показать сетку", command=self.toggle_grid)
        view_menu.add_checkbutton(label="Привязка к сетке", command=self.toggle_snap)
        view_menu.add_separator()
        for zoom in [1.0, 2.0, 4.0, 8.0]:
            view_menu.add_command(label=f"Масштаб {int(zoom*100)}%", command=lambda z=zoom: self.set_zoom(z))
        menubar.add_cascade(label="Вид", menu=view_menu)

        self.config(menu=menubar)
        self.bind("<Control-z>", lambda e: self.undo_action())
        self.bind("<Control-y>", lambda e: self.redo_action())

    def init_ui(self):
        """Отвечает за главный контейнер программы"""
        main_frame = tk.Frame(self, bg=COLOR_BG)
        main_frame.pack(fill="both", expand=True)

        """Отвечает за левую панель (Инструменты и Параметры)"""
        left_panel = tk.Frame(main_frame, bg=COLOR_PANEL, width=180)
        left_panel.pack(side="left", fill="y")
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="ИНСТРУМЕНТЫ", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack(pady=5)

        self.tool_btns = {}
        tools = [("✏ Карандаш (B)", "pencil"), ("✖️ Ластик (E)", "eraser"),
                 ("☕ Заливка (G)", "bucket"), ("⚱︎ Пипетка (I)", "eyedropper")]

        for name, tool_id in tools:
            btn = tk.Button(left_panel, text=name, bg="#2d2d2d", fg=COLOR_TEXT,
                            relief="flat", anchor="w", padx=10, font=FONT_MAIN,
                            command=lambda t=tool_id: self.select_tool(t))
            btn.pack(fill="x", padx=5, pady=2)
            self.tool_btns[tool_id] = btn

        tk.Label(left_panel, text="ПАРАМЕТРЫ", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack(pady=(15,5))

        param_frame = tk.Frame(left_panel, bg=COLOR_PANEL)
        param_frame.pack(fill="x", padx=10)

        tk.Label(param_frame, text="Размер кисти (px):", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack(anchor="w")
        self.size_spin = tk.Spinbox(param_frame, from_=1, to=10, width=5, bg=COLOR_BG, fg="white", command=self.update_brush_size)
        self.size_spin.pack(anchor="w", pady=(0, 10))

        """Отвечает за свойства кадра"""
        tk.Label(left_panel, text="СВОЙСТВА КАДРА", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack(pady=(15,5))
        self.duration_spin = tk.Spinbox(left_panel, from_=10, to=5000, width=10, bg=COLOR_BG, fg="white", command=self.update_frame_duration)
        self.duration_spin.pack(pady=5)
        tk.Label(left_panel, text="Длительность (мс)", bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_MAIN).pack()
        tk.Button(left_panel, text="Дублировать кадр", bg="#444", fg="white", command=self.duplicate_frame).pack(pady=10)

        """Отвечает за правую панель (Цвета и Предпросмотр)"""
        right_panel = tk.Frame(main_frame, bg=COLOR_PANEL, width=200)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        tk.Label(right_panel, text="ЦВЕТА", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack(pady=5)

        self.palette_frame = tk.Frame(right_panel, bg=COLOR_PANEL)
        self.palette_frame.pack()
        self.color_btns = []
        for i, color in enumerate(BASE_PALETTE):
            btn = tk.Button(self.palette_frame, bg=color, width=3, height=1, relief="flat",
                            command=lambda c=color: self.select_color(c))
            btn.grid(row=i//4, column=i%4, padx=2, pady=2)
            self.color_btns.append(btn)

        self.color_info = tk.Label(right_panel, text="#000000 (Idx: 0)", bg=COLOR_BG, fg="white", font=FONT_MAIN)
        self.color_info.pack(fill="x", padx=10, pady=5)
        tk.Button(right_panel, text="+ Свой цвет", bg="#444", fg="white", command=self.add_custom_color).pack(pady=5)

        """Отвечает за панель Предпросмотр"""
        tk.Label(right_panel, text="ПРЕДПРОСМОТР", bg=COLOR_PANEL, fg="white", font=FONT_TITLE).pack(pady=(20,5))
        self.preview_label = tk.Label(right_panel, bg=COLOR_BG, text="Нет данных", width=100, height=100)
        self.preview_label.pack(padx=10, pady=5)

        """Отвечает за центральную часть (Вкладки и Холст)"""
        center_panel = tk.Frame(main_frame, bg=COLOR_BG)
        center_panel.pack(side="left", fill="both", expand=True)

        self.notebook = ttk.Notebook(center_panel)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas_tab = tk.Frame(self.notebook, bg=COLOR_BG)
        self.notebook.add(self.canvas_tab, text="Безымянный спрайт")

        self.canvas = tk.Canvas(self.canvas_tab, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        self.canvas.bind("<Configure>", lambda e: self.draw_canvas())

        """Отвечает за нижнюю панель (Таймлайн)"""
        bottom_frame = tk.Frame(self, bg=COLOR_PANEL, height=120)
        bottom_frame.pack(side="bottom", fill="x")
        bottom_frame.pack_propagate(False)

        anim_frame = tk.Frame(bottom_frame, bg=COLOR_PANEL)
        anim_frame.pack(side="left", fill="y", padx=5, pady=5)

        """Отвечает за кнопки управления"""
        tk.Button(anim_frame, text="⏮", bg="#2d2d2d", fg="white", command=self.restart_anim).pack(side="left", padx=2)
        tk.Button(anim_frame, text="◀", bg="#2d2d2d", fg="white", command=self.prev_frame).pack(side="left", padx=2)
        self.play_btn = tk.Button(anim_frame, text="▶", bg="#2d2d2d", fg="white", command=self.toggle_play)
        self.play_btn.pack(side="left", padx=2)
        tk.Button(anim_frame, text="▶|", bg="#2d2d2d", fg="white", command=self.next_frame).pack(side="left", padx=2)

        tk.Button(anim_frame, text="+ Кадр", bg="#444", fg="white", command=self.add_frame).pack(side="left", padx=10)
        tk.Button(anim_frame, text="♻︎", bg="#2d2d2d", fg="white", command=self.delete_frame).pack(side="left", padx=2)

        """Делает прокручиваемый фрейм для миниатюр"""
        self.timeline_canvas = tk.Canvas(bottom_frame, bg=COLOR_BG, highlightthickness=0)
        self.timeline_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.timeline_frame = tk.Frame(self.timeline_canvas, bg=COLOR_BG)
        self.timeline_canvas.create_window((0, 0), window=self.timeline_frame, anchor="nw")

        """Отвечает за статус бар (Самый низ)"""
        self.status_bar = tk.Frame(self, bg="#111", height=25)
        self.status_bar.pack(side="bottom", fill="x")

        self.status_coords = tk.Label(self.status_bar, text="X: 0, Y: 0", bg="#111", fg=COLOR_TEXT, font=FONT_MAIN)
        self.status_coords.pack(side="left", padx=15)

        self.status_color = tk.Label(self.status_bar, text="Цвет: #000000", bg="#111", fg=COLOR_TEXT, font=FONT_MAIN)
        self.status_color.pack(side="left", padx=15)

        self.status_size = tk.Label(self.status_bar, text="Размер: 32x32", bg="#111", fg=COLOR_TEXT, font=FONT_MAIN)
        self.status_size.pack(side="right", padx=15)

        self.status_zoom = tk.Label(self.status_bar, text="Масштаб: 100%", bg="#111", fg=COLOR_TEXT, font=FONT_MAIN)
        self.status_zoom.pack(side="right", padx=15)

        self.bind("<Key-b>", lambda e: self.select_tool("pencil"))
        self.bind("<Key-e>", lambda e: self.select_tool("eraser"))
        self.bind("<Key-g>", lambda e: self.select_tool("bucket"))
        self.bind("<Key-i>", lambda e: self.select_tool("eyedropper"))

        self.select_tool("pencil")

    """Отвечает за логику отрисовки программы"""
    def draw_all(self):
        self.draw_canvas()
        self.update_preview()
        self.draw_timeline()

    def draw_canvas(self):
        self.canvas.delete("all")
        if not self.model.frames: return

        cell = 20 * self.zoom
        frame = self.model.get_current_frame()

        """Делает центрирование"""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        offset_x = max(0, (cw - self.model.width * cell) / 2)
        offset_y = max(0, (ch - self.model.height * cell) / 2)

        """Отвечает за фон"""
        self.canvas.create_rectangle(
            offset_x, offset_y,
            offset_x + self.model.width * cell, offset_y + self.model.height * cell,
            fill=self.model.bg_color, outline=""
        )

        for y in range(self.model.height):
            for x in range(self.model.width):
                x1, y1 = offset_x + x * cell, offset_y + y * cell
                x2, y2 = x1 + cell, y1 + cell

                """Делает шахматку только если фон прозрачный (упрощенно - просто рисуем пиксели)"""
                color = frame[x][y]
                if color:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        if self.show_grid and self.zoom > 0.5:
            for i in range(self.model.width + 1):
                x_pos = offset_x + i * cell
                self.canvas.create_line(x_pos, offset_y, x_pos, offset_y + self.model.height * cell, fill="#444444")
            for i in range(self.model.height + 1):
                y_pos = offset_y + i * cell
                self.canvas.create_line(offset_x, y_pos, offset_x + self.model.width * cell, y_pos, fill="#444444")

    def update_preview(self):
        if not self.model.frames: return
        frame = self.model.get_current_frame()
        img = tk.PhotoImage(width=self.model.width, height=self.model.height)

        """Заливает фон холста"""
        img.put(self.model.bg_color, to=(0, 0, self.model.width, self.model.height))

        for y in range(self.model.height):
            for x in range(self.model.width):
                c = frame[x][y]
                if c: img.put(c, (x, y))

        """Делает грубое масштабирование для превью"""
        self.preview_label.config(image=img, text="")
        self.preview_label.image = img

    def draw_timeline(self):
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()

        for i, frame in enumerate(self.model.frames):
            img = tk.PhotoImage(width=self.model.width, height=self.model.height)
            for y in range(self.model.height):
                for x in range(self.model.width):
                    c = frame[x][y]
                    if c: img.put(c, (x, y))

            border = COLOR_ACCENT if i == self.model.current_frame_idx else "#444"
            btn = tk.Button(self.timeline_frame, image=img, bg=COLOR_BG,
                            relief="solid", borderwidth=2 if i == self.model.current_frame_idx else 1,
                            command=lambda idx=i: self.select_frame(idx))
            """В Tkinter нельзя напрямую поменять цвет border у кнопки с картинкой, имитируем через highlightbackground"""
            btn.config(highlightbackground=border, highlightcolor=border)
            btn.image = img
            btn.pack(side="left", padx=5, pady=5)

        self.timeline_frame.update_idletasks()
        self.timeline_canvas.config(scrollregion=self.timeline_canvas.bbox("all"))

    """Отвечает за взаимодействия с холстом"""
    def get_pixel_at(self, event):
        cell = 20 * self.zoom
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        offset_x = max(0, (cw - self.model.width * cell) / 2)
        offset_y = max(0, (ch - self.model.height * cell) / 2)

        x = int((self.canvas.canvasx(event.x) - offset_x) / cell)
        y = int((self.canvas.canvasy(event.y) - offset_y) / cell)

        if self.snap_to_grid:
            x = (x // 2) * 2
            y = (y // 2) * 2

        return x, y

    def on_canvas_click(self, event):
        self.model.save_state()
        x, y = self.get_pixel_at(event)
        self.last_x, self.last_y = x, y
        self.apply_tool(x, y)

    def on_canvas_drag(self, event):
        x, y = self.get_pixel_at(event)
        if (x, y) != (self.last_x, self.last_y):
            self.apply_tool(x, y)
            self.last_x, self.last_y = x, y

    def on_canvas_release(self, event):
        self.last_x, self.last_y = None, None

    def apply_tool(self, x, y):
        if x is None or not (0 <= x < self.model.width and 0 <= y < self.model.height): return

        if self.current_tool == "pencil":
            self.model.set_pixel(x, y, self.primary_color, self.brush_size)
        elif self.current_tool == "eraser":
            self.model.set_pixel(x, y, None, self.brush_size)
        elif self.current_tool == "eyedropper":
            c = self.model.get_pixel(x, y)
            if c: self.select_color(c)
        elif self.current_tool == "bucket":
            self.model.flood_fill(x, y, self.model.get_pixel(x, y), self.primary_color)

        self.draw_all()

    def on_canvas_motion(self, event):
        x, y = self.get_pixel_at(event)
        if x is not None and 0 <= x < self.model.width and 0 <= y < self.model.height:
            self.status_coords.config(text=f"X: {x}, Y: {y}")

    def on_mouse_wheel(self, event):
        if event.num == 4 or getattr(event, 'delta', 0) > 0:
            self.zoom = min(self.zoom * 1.2, 8.0)
        elif event.num == 5 or getattr(event, 'delta', 0) < 0:
            self.zoom = max(self.zoom / 1.2, 0.5)
        self.status_zoom.config(text=f"Масштаб: {int(self.zoom*100)}%")
        self.draw_canvas()

    """Данные строки отвечают на действия пользователя"""
    def show_new_project_dialog(self):
        dialog = NewProjectDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            name, w, h, bg = dialog.result
            self.model.reset_project(w, h, bg)
            self.model.project_name = name
            self.notebook.tab(0, text=name)
            self.status_size.config(text=f"Размер: {w}x{h}")
            self.zoom = 1.0
            self.duration_spin.delete(0, "end")
            self.duration_spin.insert(0, "100")
            self.draw_all()

    def select_tool(self, t_id):
        self.current_tool = t_id
        for t, btn in self.tool_btns.items():
            btn.config(bg=COLOR_ACCENT if t == t_id else "#2d2d2d", fg="black" if t == t_id else "white")

        cursors = {"pencil": "crosshair", "bucket": "dot", "eraser": "circle", "eyedropper": "tcross"}
        try:
            self.canvas.config(cursor=cursors.get(t_id, "arrow"))
        except:
            self.canvas.config(cursor="arrow")

    def select_color(self, color):
        self.primary_color = color
        try:
            idx = BASE_PALETTE.index(color)
            self.color_info.config(text=f"{color.upper()} (Idx: {idx})")
        except ValueError:
            self.color_info.config(text=f"{color.upper()} (Custom)")
        self.status_color.config(text=f"Цвет: {color.upper()}")

    def update_brush_size(self):
        try: self.brush_size = int(self.size_spin.get())
        except: self.brush_size = 1

    def add_custom_color(self):
        color = colorchooser.askcolor(title="Выберите цвет")[1]
        if color:
            self.select_color(color)
            """Добавляем кнопку (упрощенно, просто в конец сетки)"""
            i = len(self.color_btns)
            btn = tk.Button(self.palette_frame, bg=color, width=3, height=1, relief="flat", command=lambda c=color: self.select_color(c))
            btn.grid(row=i//4, column=i%4, padx=2, pady=2)
            self.color_btns.append(btn)

    """Отвечает за историю программы"""
    def undo_action(self):
        if self.model.undo():
            self.draw_all()

    def redo_action(self):
        if self.model.redo():
            self.draw_all()

    """Отвечает за вид программы"""
    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.draw_canvas()

    def toggle_snap(self):
        self.snap_to_grid = not self.snap_to_grid

    def set_zoom(self, zoom_level):
        self.zoom = zoom_level
        self.status_zoom.config(text=f"Масштаб: {int(self.zoom*100)}%")
        self.draw_canvas()

    """Данные строки отвечают за панель таймлайна"""
    def add_frame(self):
        self.model.add_frame()
        self.update_duration_ui()
        self.draw_all()

    def duplicate_frame(self):
        self.model.duplicate_frame()
        self.update_duration_ui()
        self.draw_all()

    def delete_frame(self):
        if self.model.delete_frame():
            self.update_duration_ui()
            self.draw_all()
        else:
            messagebox.showwarning("Внимание", "Нельзя удалить единственный кадр!")

    def select_frame(self, idx):
        self.model.current_frame_idx = idx
        self.update_duration_ui()
        self.draw_all()

    def update_duration_ui(self):
        d = self.model.frame_durations[self.model.current_frame_idx]
        self.duration_spin.delete(0, "end")
        self.duration_spin.insert(0, str(d))

    def update_frame_duration(self):
        try:
            d = int(self.duration_spin.get())
            self.model.frame_durations[self.model.current_frame_idx] = d
        except: pass

    def toggle_play(self):
        if self.is_playing:
            self.is_playing = False
            self.play_btn.config(text="▶")
            if self.play_job: self.after_cancel(self.play_job)
        else:
            self.is_playing = True
            self.play_btn.config(text="⏸")
            self.play_animation()

    def play_animation(self):
        if not self.is_playing: return
        self.next_frame()
        delay = self.model.frame_durations[self.model.current_frame_idx]
        self.play_job = self.after(delay, self.play_animation)

    def next_frame(self):
        self.model.current_frame_idx = (self.model.current_frame_idx + 1) % len(self.model.frames)
        self.update_duration_ui()
        self.draw_canvas()
        self.update_preview()
        self.draw_timeline()

    def prev_frame(self):
        self.model.current_frame_idx = (self.model.current_frame_idx - 1) % len(self.model.frames)
        self.update_duration_ui()
        self.draw_canvas()
        self.update_preview()
        self.draw_timeline()

    def restart_anim(self):
        self.model.current_frame_idx = 0
        self.update_duration_ui()
        self.draw_canvas()
        self.update_preview()
        self.draw_timeline()

    """Данные строки отвечают за экспорт данных"""
    def show_export_dialog(self):
        dialog = ExportDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            name, fmt, scale = dialog.result
            LoadingDialog(self, lambda: self.export_process(name, fmt, scale))

    def export_process(self, name, fmt, scale):
        try:
            if fmt == "PNG":
                self.save_png(name, scale)
            elif fmt == "Sprite Sheet":
                self.save_sprite_sheet(name, scale)

            SuccessDialog(self, f"{name}.png")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def save_png(self, name, scale):
        frame = self.model.get_current_frame()
        img = tk.PhotoImage(width=self.model.width * scale, height=self.model.height * scale)

        img.put(self.model.bg_color, to=(0, 0, self.model.width * scale, self.model.height * scale))

        for y in range(self.model.height):
            for x in range(self.model.width):
                c = frame[x][y]
                if c:
                    for dy in range(scale):
                        for dx in range(scale):
                            img.put(c, (x * scale + dx, y * scale + dy))

        img.write(f"{name}.png", format="png")

    def save_sprite_sheet(self, name, scale):
        frame_count = len(self.model.frames)
        padding = 0
        img_w = frame_count * (self.model.width * scale + padding)
        img_h = self.model.height * scale

        img = tk.PhotoImage(width=img_w, height=img_h)

        for i, frame in enumerate(self.model.frames):
            offset_x = i * (self.model.width * scale + padding)
            for y in range(self.model.height):
                for x in range(self.model.width):
                    c = frame[x][y]
                    if c:
                        for dy in range(scale):
                            for dx in range(scale):
                                img.put(c, (offset_x + x * scale + dx, y * scale + dy))

        img.write(f"{name}.png", format="png")

if __name__ == "__main__":
    app = SpriteStudio()
    app.mainloop()