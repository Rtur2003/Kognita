# kognita/ui.py
import tkinter as tk
from tkinter import ttk, messagebox, Listbox, OptionMenu, StringVar, Frame, Label, Entry, Button, simpledialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

from . import analyzer, database, reporter

# Projenizin görsel tutarlılığı için temel renk ve font ayarları
STYLE_CONFIG = {
    "font_normal": ("Helvetica", 10),
    "font_bold": ("Helvetica", 12, "bold"),
    "font_title": ("Helvetica", 14, "bold"),
    "bg_color": "#F0F0F0",
    "button_color": "#E1E1E1",
    "accent_color": "#0078D7",
}

class BaseWindow(tk.Toplevel):
    """Tüm pencereler için temel stil ve davranışları içeren ana sınıf."""
    def __init__(self, master, title, geometry):
        super().__init__(master) # Kök pencereyi ata
        self.title(title)
        self.geometry(geometry)
        self.configure(bg=STYLE_CONFIG["bg_color"])
        
        # Pencereyi öne getir ve odakla
        self.lift()
        self.focus_force()

        self.center_window()

        # Pencere kapatıldığında yok edilmesini sağlar
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def center_window(self):
        """Pencereyi ekranın ortasında açar."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class ReportWindow(BaseWindow):
    """Gelişmiş raporlama penceresi."""
    def __init__(self, master):
        super().__init__(master, "Kognita - Aktivite Raporu", "800x650")
        self.resizable(False, False)
        
        # Üst Frame: Tarih aralığı seçimi için
        top_frame = Frame(self, bg=STYLE_CONFIG["bg_color"], pady=10)
        top_frame.pack(fill='x')

        Label(top_frame, text="Rapor Aralığı:", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG["bg_color"]).pack(side='left', padx=(10, 5))

        self.time_range_var = StringVar(self)
        self.time_range_var.set("Son 24 Saat")
        time_options = ["Son 24 Saat", "Son 7 Gün", "Son 30 Gün"]
        time_menu = ttk.OptionMenu(top_frame, self.time_range_var, self.time_range_var.get(), *time_options, command=self.refresh_report)
        time_menu.pack(side='left', padx=5)

        # Ana içerik için Notebook (Sekmeli yapı)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.tab_overview = ttk.Frame(self.notebook)
        self.tab_hourly = ttk.Frame(self.notebook)
        self.tab_weekly = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_overview, text='Genel Bakış')
        self.notebook.add(self.tab_hourly, text='Saatlik Aktivite')
        self.notebook.add(self.tab_weekly, text='Haftalık Karşılaştırma')
        
        self.refresh_report()

    def get_date_range(self):
        """Seçilen zaman aralığına göre başlangıç ve bitiş tarihlerini döndürür."""
        selection = self.time_range_var.get()
        today = datetime.datetime.now()
        if selection == "Son 24 Saat":
            start_date = today - datetime.timedelta(days=1)
        elif selection == "Son 7 Gün":
            start_date = today - datetime.timedelta(days=7)
        elif selection == "Son 30 Gün":
            start_date = today - datetime.timedelta(days=30)
        return start_date, today

    def clear_frame(self, frame):
        """Bir frame içindeki tüm widget'ları temizler."""
        for widget in frame.winfo_children():
            widget.destroy()

    def refresh_report(self, event=None):
        """Tüm sekmelerdeki verileri yeniler."""
        start_date, end_date = self.get_date_range()
        
        self.clear_frame(self.tab_overview)
        self.clear_frame(self.tab_hourly)
        self.clear_frame(self.tab_weekly)

        category_totals, total_duration = analyzer.get_analysis_data(start_date, end_date)

        if not category_totals or total_duration == 0:
            Label(self.tab_overview, text="\nBu tarih aralığı için yeterli veri bulunamadı.", font=STYLE_CONFIG["font_bold"], bg='white').pack(pady=20, expand=True)
            Label(self.tab_hourly, text="\nBu tarih aralığı için yeterli veri bulunamadı.", font=STYLE_CONFIG["font_bold"], bg='white').pack(pady=20, expand=True)
            Label(self.tab_weekly, text="\nBu tarih aralığı için yeterli veri bulunamadı.", font=STYLE_CONFIG["font_bold"], bg='white').pack(pady=20, expand=True)
        else:
            self.create_overview_tab(category_totals, total_duration)
            self.create_hourly_tab()
            self.create_weekly_tab()

    def create_overview_tab(self, category_totals, total_duration):
        """Genel Bakış sekmesini oluşturur."""
        days = (self.get_date_range()[1] - self.get_date_range()[0]).days
        days = 1 if days == 0 else days
        
        # Sol Taraf: Pasta Grafiği
        left_frame = Frame(self.tab_overview, bg='white')
        left_frame.pack(side='left', fill='both', expand=True, padx=5)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(category_totals.values(), labels=category_totals.keys(), autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=left_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # Sağ Taraf: Metin Raporu
        right_frame = Frame(self.tab_overview, bg='white', padx=10)
        right_frame.pack(side='right', fill='both', expand=True)
        
        summary_text = reporter.get_report_as_string(category_totals, total_duration, days)
        Label(right_frame, text=summary_text, font=("Courier New", 9), justify=tk.LEFT, bg='white').pack(pady=10, anchor='n')

    def create_hourly_tab(self):
        """Saatlik Aktivite sekmesini oluşturur."""
        hourly_data = analyzer.get_hourly_activity()
        if not hourly_data:
            Label(self.tab_hourly, text="Saatlik aktivite verisi bulunamadı.", font=STYLE_CONFIG["font_normal"]).pack()
            return

        fig = Figure(figsize=(7, 5), dpi=100)
        ax = fig.add_subplot(111)
        
        hours = range(24)
        activity = [hourly_data.get(h, 0) / 60 for h in hours] # Dakikaya çevir

        ax.bar(hours, activity, color=STYLE_CONFIG["accent_color"])
        ax.set_title("Son 7 Günün Saatlik Aktivite Ortalaması", fontdict={'fontsize': 12})
        ax.set_xlabel("Saat")
        ax.set_ylabel("Toplam Kullanım (Dakika)")
        ax.set_xticks(hours)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.tab_hourly)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def create_weekly_tab(self):
        """Haftalık Karşılaştırma sekmesini oluşturur."""
        comparison_data = analyzer.get_weekly_comparison()
        if not comparison_data:
            Label(self.tab_weekly, text="Haftalık karşılaştırma için yeterli veri bulunamadı.", font=STYLE_CONFIG["font_normal"]).pack()
            return
            
        categories = list(comparison_data.keys())
        this_week_vals = [d['this_week'] for d in comparison_data.values()]
        last_week_vals = [d['last_week'] for d in comparison_data.values()]

        fig = Figure(figsize=(7, 5), dpi=100)
        ax = fig.add_subplot(111)

        x = range(len(categories))
        ax.bar([i - 0.2 for i in x], this_week_vals, width=0.4, label='Bu Hafta', color='skyblue')
        ax.bar([i + 0.2 for i in x], last_week_vals, width=0.4, label='Geçen Hafta', color='lightcoral')
        
        ax.set_title("En Aktif Kategorilerin Haftalık Karşılaştırması", fontdict={'fontsize': 12})
        ax.set_ylabel("Toplam Kullanım (Dakika)")
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.tab_weekly)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

class GoalsWindow(BaseWindow):
    """Hedef yönetim penceresi."""
    def __init__(self, master):
        super().__init__(master, "Hedefleri Yönet", "450x450")
        self.resizable(False, False)

        Label(self, text="Mevcut Hedefler:", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG["bg_color"]).pack(pady=(10,0))
        list_frame = Frame(self, bg=STYLE_CONFIG["bg_color"]); list_frame.pack(pady=5, padx=10, fill="x")
        self.goals_listbox = Listbox(list_frame, height=8); self.goals_listbox.pack(side="left", fill="x", expand=True)

        add_frame = Frame(self, pady=10, bg=STYLE_CONFIG["bg_color"]); add_frame.pack(pady=10, padx=10)
        Label(add_frame, text="Yeni Hedef Ekle:", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG["bg_color"]).grid(row=0, columnspan=2, sticky="w")
        
        Label(add_frame, text="Kategori:", bg=STYLE_CONFIG["bg_color"]).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.category_var = StringVar(self)
        categories = database.get_all_categories()
        self.category_var.set(categories[0] if categories else "Other")
        OptionMenu(add_frame, self.category_var, *categories).grid(row=1, column=1, sticky="ew")

        Label(add_frame, text="Tip:", bg=STYLE_CONFIG["bg_color"]).grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.type_var = StringVar(self); self.type_var.set("Max")
        OptionMenu(add_frame, self.type_var, "Max", "Min").grid(row=2, column=1, sticky="ew")

        Label(add_frame, text="Süre (dakika):", bg=STYLE_CONFIG["bg_color"]).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.time_entry = Entry(add_frame, width=10); self.time_entry.grid(row=3, column=1, sticky="w")

        Button(add_frame, text="Hedef Ekle", command=self.add_new_goal, bg=STYLE_CONFIG["button_color"]).grid(row=4, columnspan=2, pady=10)
        
        button_frame = Frame(self, bg=STYLE_CONFIG["bg_color"]); button_frame.pack(pady=10)
        Button(button_frame, text="Seçili Hedefi Sil", command=self.delete_selected_goal, bg=STYLE_CONFIG["button_color"]).pack()
        
        self.refresh_goals_list()

    def refresh_goals_list(self):
        self.goals_listbox.delete(0, tk.END)
        for goal in database.get_goals():
            goal_id, category, goal_type, time_limit = goal
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
                database.delete_goal(goal_id)
                self.refresh_goals_list()
            except Exception as e: messagebox.showerror("Hata", f"Hedef silinemedi: {e}")

class SettingsWindow(BaseWindow):
    """Ayarlar penceresi."""
    def __init__(self, master, app_instance):
        super().__init__(master, "Ayarlar", "350x250")
        self.app = app_instance

        # Idle Threshold Setting
        Label(self, text="Boşta Kalma Eşiği (saniye):", font=STYLE_CONFIG["font_normal"], bg=STYLE_CONFIG["bg_color"]).pack(pady=(10,0))
        self.idle_entry = Entry(self, width=10)
        self.idle_entry.insert(0, self.app.config['settings']['idle_threshold_seconds'])
        self.idle_entry.pack(pady=5)

        Button(self, text="Ayarları Kaydet", command=self.save_settings_action, bg=STYLE_CONFIG["button_color"]).pack(pady=20)

        # Category Management Button
        Button(self, text="Uygulama Kategorilerini Yönet", command=self.open_app_manager, bg=STYLE_CONFIG["button_color"]).pack(pady=10)

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

    def open_app_manager(self):
        AppManagerWindow(master=self.master) # Kök pencereyi yeni pencereye aktar

class AppManagerWindow(BaseWindow):
    """Kategorize edilmemiş uygulamaları yönetme penceresi."""
    def __init__(self, master):
        super().__init__(master, "Uygulama Yöneticisi", "500x400")
        self.resizable(False, False)

        Label(self, text="Kategorize Edilmemiş Uygulamalar", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG["bg_color"]).pack(pady=10)
        
        self.app_listbox = Listbox(self, height=15)
        self.app_listbox.pack(padx=10, pady=5, fill='x')
        self.app_listbox.bind('<<ListboxSelect>>', self.on_app_select)

        self.refresh_app_list()

        # Action Frame
        action_frame = Frame(self, bg=STYLE_CONFIG["bg_color"], pady=10)
        action_frame.pack()
        
        self.selected_app_label = Label(action_frame, text="Bir uygulama seçin", bg=STYLE_CONFIG["bg_color"])
        self.selected_app_label.grid(row=0, column=0, padx=5)

        self.category_var = StringVar(self)
        categories = database.get_all_categories()
        if categories:
            self.category_var.set(categories[0])
            self.category_menu = OptionMenu(action_frame, self.category_var, *categories)
        else: # Hiç kategori yoksa (beklenmedik durum)
             self.category_var.set("Other")
             self.category_menu = OptionMenu(action_frame, self.category_var, "Other")
        
        self.category_menu.grid(row=0, column=1, padx=5)

        Button(action_frame, text="Kategori Ata", command=self.assign_category, bg=STYLE_CONFIG["button_color"]).grid(row=0, column=2, padx=5)

    def refresh_app_list(self):
        self.app_listbox.delete(0, tk.END)
        apps = database.get_uncategorized_apps()
        if not apps:
            self.app_listbox.insert(tk.END, "Tüm uygulamalar kategorize edilmiş.")
            self.app_listbox.config(state=tk.DISABLED)
        else:
            self.app_listbox.config(state=tk.NORMAL)
            for app in apps:
                self.app_listbox.insert(tk.END, app)

    def on_app_select(self, event):
        try:
            selection = self.app_listbox.get(self.app_listbox.curselection())
            self.selected_app_label.config(text=f"Seçili: {selection}")
        except tk.TclError:
            # Liste boşken seçim yapmaya çalışınca oluşan hatayı yoksay
            pass

    def assign_category(self):
        try:
            selected_app = self.app_listbox.get(tk.ACTIVE)
            selected_category = self.category_var.get()
            if not selected_app or self.app_listbox.cget('state') == tk.DISABLED:
                messagebox.showwarning("Seçim Yok", "Lütfen bir uygulama seçin.")
                return

            database.update_app_category(selected_app, selected_category)
            messagebox.showinfo("Başarılı", f"'{selected_app}' uygulaması '{selected_category}' kategorisine atandı.")
            self.refresh_app_list()
            self.selected_app_label.config(text="Bir uygulama seçin")

        except Exception as e:
            messagebox.showerror("Hata", f"Kategori atanamadı: {e}")
