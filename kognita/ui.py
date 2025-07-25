# kognita/ui.py

import tkinter as tk
from tkinter import ttk, messagebox, Listbox, StringVar, Frame, Label, Entry, Button
import datetime
import os
import sys
from PIL import Image, ImageTk

# Yerel modülleri içe aktar
from . import analyzer, database, reporter

# Matplotlib import'larını try-except bloğuna alarak opsiyonel hale getirelim
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# --- Stil ve Tasarım Yapılandırması ---
STYLE_CONFIG = {
    "font_normal": ("Segoe UI", 10),
    "font_bold": ("Segoe UI Semibold", 11),
    "font_title": ("Segoe UI Light", 18),
    "header_bg": "#2c3e50",  # Koyu Mavi-Gri
    "header_fg": "#ecf0f1",  # Açık Gri
    "bg_color": "#ffffff",   # Beyaz
    "footer_bg": "#f8f9fa",  # Çok Açık Gri
    "accent_color": "#3498db", # Parlak Mavi
    "danger_color": "#e74c3c", # Kırmızı
    "success_color": "#2ecc71", # Yeşil
}

def resource_path(relative_path):
    """ PyInstaller ile paketlendiğinde varlık dosyalarına doğru yolu bulur. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, 'assets', relative_path)


class BaseWindow(tk.Toplevel):
    """Tüm pencereler için temel şablonu (header, main, footer) oluşturan sınıf."""
    def __init__(self, master, title, geometry):
        super().__init__(master)
        self.overrideredirect(True) # Pencerenin başlık çubuğunu kaldır
        self.geometry(geometry)
        self.configure(bg=STYLE_CONFIG["bg_color"])
        
        # Sürükleme için değişkenler
        self._drag_start_x = 0
        self._drag_start_y = 0

        # --- Ana Yerleşim Alanları ---
        self.header_frame = Frame(self, bg=STYLE_CONFIG["header_bg"], height=50) # Yüksekliği biraz azalttık
        self.main_frame = Frame(self, bg=STYLE_CONFIG["bg_color"], padx=15, pady=15)
        self.footer_frame = Frame(self, bg=STYLE_CONFIG["footer_bg"], height=55)
        
        self.header_frame.pack(fill='x', side='top')
        self.main_frame.pack(fill='both', expand=True)
        self.footer_frame.pack(fill='x', side='bottom')
        self.footer_frame.pack_propagate(False)

        # Sürükleme olaylarını başlık çubuğuna bağla
        self.header_frame.bind("<ButtonPress-1>", self.start_drag)
        self.header_frame.bind("<B1-Motion>", self.do_drag)

        self.populate_header(title)

        self.lift()
        self.attributes('-topmost', True)
        self.focus_force()
        self.attributes('-topmost', False)
        self.center_window()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_start_x
        y = self.winfo_y() + event.y - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def populate_header(self, title):
        """Varsayılan başlık bölümünü logo, başlık ve özel kapatma düğmesi ile doldurur."""
        # Kapatma düğmesi
        close_button = Button(self.header_frame, text="✕", command=self.destroy, bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"], relief='flat', font=("Segoe UI Symbol", 12), activebackground=STYLE_CONFIG['danger_color'], activeforeground='white')
        close_button.pack(side='right', padx=10, pady=5, fill='y')

        try:
            logo_image = Image.open(resource_path("logo.png")).resize((30, 30), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = Label(self.header_frame, image=self.logo_photo, bg=STYLE_CONFIG["header_bg"])
            logo_label.pack(side='left', padx=(15,10), pady=10)
            logo_label.bind("<ButtonPress-1>", self.start_drag) # Logoya tıklayarak da sürükle
            logo_label.bind("<B1-Motion>", self.do_drag)
        except Exception:
            pass

        title_label = Label(self.header_frame, text=title, font=STYLE_CONFIG["font_title"], bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"])
        title_label.pack(side='left', pady=10)
        title_label.bind("<ButtonPress-1>", self.start_drag) # Başlığa tıklayarak da sürükle
        title_label.bind("<B1-Motion>", self.do_drag)
        
    def center_window(self):
        self.update_idletasks()
        width = int(self.geometry().split('x')[0])
        height = int(self.geometry().split('x')[1].split('+')[0])
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class ReportWindow(BaseWindow):
    def __init__(self, master):
        super().__init__(master, "Aktivite Raporu", "850x700")
        
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Eksik Kütüphane", "Raporları görüntülemek için 'matplotlib' kütüphanesi gereklidir.")
            self.destroy()
            return

        self.setup_custom_header()
        
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(expand=True, fill='both')
        
        self.tab_overview = ttk.Frame(self.notebook)
        self.tab_hourly = ttk.Frame(self.notebook)
        self.tab_weekly = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_overview, text=' Genel Bakış ')
        self.notebook.add(self.tab_hourly, text=' Saatlik Aktivite ')
        self.notebook.add(self.tab_weekly, text=' Haftalık Karşılaştırma ')
        
        Button(self.footer_frame, text="Kapat", command=self.destroy, bg=STYLE_CONFIG['danger_color'], fg='white', font=STYLE_CONFIG['font_bold'], width=10, relief='flat').pack(side='right', padx=15, pady=10)
        
        self.refresh_report()

    def setup_custom_header(self):
        for widget in self.header_frame.winfo_children(): widget.destroy()
        self.populate_header("Aktivite Raporu")
        
        dropdown_frame = Frame(self.header_frame, bg=STYLE_CONFIG["header_bg"])
        dropdown_frame.pack(side='right', padx=20)
        
        Label(dropdown_frame, text="Rapor Aralığı:", font=STYLE_CONFIG['font_normal'], bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"]).pack(side='left', padx=(0, 5))
        self.time_range_var = StringVar(self)
        time_options = ["Son 24 Saat", "Son 7 Gün", "Son 30 Gün"]
        self.time_range_var.set(time_options[1])
        time_menu = ttk.OptionMenu(dropdown_frame, self.time_range_var, time_options[1], *time_options, command=self.refresh_report)
        time_menu.pack(side='left')

        # Dropdown menüye de sürükleme bağlayalım
        dropdown_frame.bind("<ButtonPress-1>", self.start_drag)
        dropdown_frame.bind("<B1-Motion>", self.do_drag)
        for child in dropdown_frame.winfo_children():
            child.bind("<ButtonPress-1>", self.start_drag)
            child.bind("<B1-Motion>", self.do_drag)

    def get_date_range(self):
        selection = self.time_range_var.get()
        today = datetime.datetime.now()
        days = 1 if "24 Saat" in selection else 7 if "7 Gün" in selection else 30
        return today - datetime.timedelta(days=days), today

    def clear_frame(self, frame):
        for widget in frame.winfo_children(): widget.destroy()

    def refresh_report(self, event=None):
        start_date, end_date = self.get_date_range()
        for tab in [self.tab_overview, self.tab_hourly, self.tab_weekly]: self.clear_frame(tab)
        
        category_totals, total_duration = analyzer.get_analysis_data(start_date, end_date)
        if not category_totals or total_duration == 0:
            for tab in [self.tab_overview, self.tab_hourly, self.tab_weekly]:
                Label(tab, text="\nBu tarih aralığı için yeterli veri bulunamadı.", font=STYLE_CONFIG["font_bold"]).pack(pady=20, expand=True)
        else:
            self.create_overview_tab(category_totals, total_duration)
            self.create_hourly_tab()
            self.create_weekly_tab()

    def create_overview_tab(self, category_totals, total_duration):
        left_frame = Frame(self.tab_overview, bg=STYLE_CONFIG['bg_color']); left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        right_frame = Frame(self.tab_overview, bg=STYLE_CONFIG['bg_color']); right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        fig = Figure(figsize=(5, 4), dpi=100); fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111); ax.set_facecolor(STYLE_CONFIG['bg_color'])
        wedges, texts, autotexts = ax.pie(category_totals.values(), autopct='%1.1f%%', shadow=False, startangle=90, pctdistance=0.85)
        ax.axis('equal')
        ax.legend(wedges, category_totals.keys(), title="Kategoriler", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=left_frame).get_tk_widget().pack(fill='both', expand=True)

        report_frame = Frame(right_frame, bg=STYLE_CONFIG['bg_color']); report_frame.pack(fill='both', expand=True)
        persona_text, table_data = reporter.get_report_data(category_totals, total_duration)

        Label(report_frame, text=persona_text, font=STYLE_CONFIG['font_bold'], justify='left', bg=STYLE_CONFIG['bg_color']).pack(pady=(0,10), anchor='w')

        style = ttk.Style()
        style.configure("Treeview", font=STYLE_CONFIG['font_normal'], rowheight=25)
        style.configure("Treeview.Heading", font=STYLE_CONFIG['font_bold'])
        tree = ttk.Treeview(report_frame, columns=('Category', 'Time', 'Percentage'), show='headings')
        tree.heading('Category', text='Kategori')
        tree.heading('Time', text='Harcanan Süre')
        tree.heading('Percentage', text='Yüzde (%)')
        for item in table_data: tree.insert('', 'end', values=item)
        tree.pack(fill='both', expand=True)

    def create_hourly_tab(self):
        hourly_data = analyzer.get_hourly_activity()
        if not hourly_data: return
        fig = Figure(figsize=(7, 5), dpi=100); fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111); ax.set_facecolor(STYLE_CONFIG['bg_color'])
        hours, activity = range(24), [hourly_data.get(h, 0) / 60 for h in range(24)]
        ax.bar(hours, activity, color=STYLE_CONFIG["accent_color"])
        ax.set(title="Son 7 Günün Saatlik Aktivite Ortalaması", xlabel="Saat", ylabel="Toplam Kullanım (Dakika)", xticks=hours)
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=self.tab_hourly).get_tk_widget().pack(fill='both', expand=True)

    def create_weekly_tab(self):
        comparison_data = analyzer.get_weekly_comparison()
        if not comparison_data: return
        categories = list(comparison_data.keys())
        this_week = [d['this_week'] for d in comparison_data.values()]
        last_week = [d['last_week'] for d in comparison_data.values()]
        fig = Figure(figsize=(7, 5), dpi=100); fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111); ax.set_facecolor(STYLE_CONFIG['bg_color'])
        x = range(len(categories))
        ax.bar([i - 0.2 for i in x], this_week, width=0.4, label='Bu Hafta', color='skyblue')
        ax.bar([i + 0.2 for i in x], last_week, width=0.4, label='Geçen Hafta', color='lightcoral')
        ax.set(title="En Aktif Kategorilerin Haftalık Karşılaştırması", ylabel="Toplam Kullanım (Dakika)", xticks=x, xticklabels=categories)
        ax.legend()
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=self.tab_weekly).get_tk_widget().pack(fill='both', expand=True)

class GoalsWindow(BaseWindow):
    def __init__(self, master):
        super().__init__(master, "Hedefleri Yönet", "450x480")
        self.resizable(False, False)

        Label(self.main_frame, text="Mevcut Hedefler:", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG['bg_color']).pack(pady=(0,5), anchor='w')
        self.goals_listbox = Listbox(self.main_frame, height=8, font=STYLE_CONFIG['font_normal']); self.goals_listbox.pack(fill="x", expand=True)
        Button(self.main_frame, text="Seçili Hedefi Sil", command=self.delete_selected_goal, bg=STYLE_CONFIG["danger_color"], fg='white', relief='flat').pack(pady=5, anchor='e')
        
        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=15)

        Label(self.main_frame, text="Yeni Hedef Ekle:", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG['bg_color']).pack(pady=(10,5), anchor='w')
        add_frame = Frame(self.main_frame, bg=STYLE_CONFIG["bg_color"]); add_frame.pack(fill='x')
        
        Label(add_frame, text="Kategori:", bg=STYLE_CONFIG["bg_color"]).grid(row=0, column=0, sticky="w", pady=2)
        self.category_var = StringVar(self)
        categories = database.get_all_categories()
        self.category_var.set(categories[0] if categories else "Other")
        ttk.OptionMenu(add_frame, self.category_var, categories[0] if categories else "Diğer", *categories).grid(row=0, column=1, sticky="ew", padx=5)

        Label(add_frame, text="Tip:", bg=STYLE_CONFIG["bg_color"]).grid(row=1, column=0, sticky="w", pady=2)
        self.type_var = StringVar(self); self.type_var.set("Max")
        ttk.OptionMenu(add_frame, self.type_var, "Max", "Max", "Min").grid(row=1, column=1, sticky="ew", padx=5)
        
        Label(add_frame, text="Süre (dakika):", bg=STYLE_CONFIG["bg_color"]).grid(row=2, column=0, sticky="w", pady=2)
        self.time_entry = Entry(add_frame, width=10); self.time_entry.grid(row=2, column=1, sticky="w", padx=5)
        add_frame.grid_columnconfigure(1, weight=1)

        Button(self.footer_frame, text="Kapat", command=self.destroy, width=10, relief='flat').pack(side='right', padx=15, pady=10)
        Button(self.footer_frame, text="Hedef Ekle", command=self.add_new_goal, bg=STYLE_CONFIG["success_color"], fg='white', relief='flat').pack(side='right')

        self.refresh_goals_list()

    def refresh_goals_list(self):
        self.goals_listbox.delete(0, tk.END)
        for goal_id, category, goal_type, time_limit in database.get_goals():
            self.goals_listbox.insert(tk.END, f"[{goal_id}] {category}: {goal_type.capitalize()} {time_limit} dakika/gün")

    def add_new_goal(self):
        try:
            database.add_goal(self.category_var.get(), self.type_var.get().lower(), int(self.time_entry.get()))
            self.refresh_goals_list(); self.time_entry.delete(0, tk.END)
        except ValueError: messagebox.showerror("Geçersiz Girdi", "Lütfen süre için geçerli bir sayı girin.")
        except Exception as e: messagebox.showerror("Hata", f"Hedef eklenemedi: {e}")

    def delete_selected_goal(self):
        selected = self.goals_listbox.get(tk.ACTIVE)
        if not selected: messagebox.showwarning("Seçim Yok", "Lütfen silmek için bir hedef seçin.")
        else:
            try:
                goal_id = int(selected.split(']')[0][1:])
                if messagebox.askyesno("Onay", f"'{selected}' hedefini silmek istediğinizden emin misiniz?"):
                    database.delete_goal(goal_id)
                    self.refresh_goals_list()
            except Exception as e: messagebox.showerror("Hata", f"Hedef silinemedi: {e}")

class SettingsWindow(BaseWindow):
    def __init__(self, master, app_instance):
        super().__init__(master, "Ayarlar", "380x280")
        self.app = app_instance

        Label(self.main_frame, text="Boşta Kalma Eşiği (saniye):", font=STYLE_CONFIG["font_normal"], bg=STYLE_CONFIG['bg_color']).pack(pady=(10,2), anchor='w')
        self.idle_entry = Entry(self.main_frame, width=15, font=STYLE_CONFIG['font_normal'])
        self.idle_entry.insert(0, self.app.config['settings']['idle_threshold_seconds'])
        self.idle_entry.pack(pady=5, anchor='w')

        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=15)
        
        Button(self.main_frame, text="Uygulama Kategorilerini Yönet", command=lambda: AppManagerWindow(self), relief='flat', bg='#f0f0f0', highlightthickness=1, highlightbackground=STYLE_CONFIG['accent_color']).pack(pady=10, fill='x', ipady=5)
        
        Button(self.footer_frame, text="Kapat", command=self.destroy, width=10, relief='flat').pack(side='right', padx=15, pady=10)
        Button(self.footer_frame, text="Kaydet", command=self.save_settings_action, bg=STYLE_CONFIG["accent_color"], fg='white', relief='flat').pack(side='right')

    def save_settings_action(self):
        try:
            new_idle_time = int(self.idle_entry.get())
            self.app.config['settings']['idle_threshold_seconds'] = new_idle_time
            self.app.save_config()
            self.app.tracker_instance.update_settings(self.app.config)
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi.")
            self.destroy()
        except ValueError:
            messagebox.showerror("Hata", "Lütfen saniye için geçerli bir sayı girin.")

class AppManagerWindow(BaseWindow):
    def __init__(self, master):
        super().__init__(master, "Uygulama Yöneticisi", "500x450")
        
        Label(self.main_frame, text="Kategorize Edilmemiş Uygulamalar", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG['bg_color']).pack(pady=10, anchor='w')
        self.app_listbox = Listbox(self.main_frame, height=15); self.app_listbox.pack(padx=10, pady=5, fill='x', expand=True)
        self.app_listbox.bind('<<ListboxSelect>>', self.on_app_select)

        action_frame = Frame(self.main_frame, bg=STYLE_CONFIG["bg_color"], pady=10)
        action_frame.pack(fill='x')
        self.selected_app_label = Label(action_frame, text="Uygulama seçin:", bg=STYLE_CONFIG["bg_color"]); self.selected_app_label.grid(row=0, column=0, padx=5, sticky='w')
        self.category_var = StringVar(self)
        categories = database.get_all_categories()
        if categories:
            self.category_var.set(categories[0])
            self.category_menu = ttk.OptionMenu(action_frame, self.category_var, categories[0], *categories)
            self.category_menu.grid(row=0, column=1, padx=5, sticky='ew')
        action_frame.grid_columnconfigure(1, weight=1)

        Button(self.footer_frame, text="Kapat", command=self.destroy, width=10, relief='flat').pack(side='right', padx=15, pady=10)
        Button(self.footer_frame, text="Kategori Ata", command=self.assign_category, bg=STYLE_CONFIG["accent_color"], fg='white', relief='flat').pack(side='right')

        self.refresh_app_list()
    
    def refresh_app_list(self):
        self.app_listbox.delete(0, tk.END)
        apps = database.get_uncategorized_apps()
        if not apps:
            self.app_listbox.insert(tk.END, "Tüm uygulamalar kategorize edilmiş.")
            self.app_listbox.config(state=tk.DISABLED)
        else:
            self.app_listbox.config(state=tk.NORMAL)
            for app in apps: self.app_listbox.insert(tk.END, app)

    def on_app_select(self, event):
        try: self.selected_app_label.config(text=f"Seçili: {self.app_listbox.get(self.app_listbox.curselection())}")
        except tk.TclError: pass

    def assign_category(self):
        try:
            selected_app = self.app_listbox.get(tk.ACTIVE)
            if not selected_app or self.app_listbox.cget('state') == tk.DISABLED: return messagebox.showwarning("Seçim Yok", "Lütfen bir uygulama seçin.")
            database.update_app_category(selected_app, self.category_var.get())
            messagebox.showinfo("Başarılı", f"'{selected_app}' uygulaması '{self.category_var.get()}' kategorisine atandı.")
            self.refresh_app_list()
            self.selected_app_label.config(text="Uygulama seçin:")
        except Exception as e: messagebox.showerror("Hata", f"Kategori atanamadı: {e}")
