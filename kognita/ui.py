# kognita/ui.py (TAMAMI - Adım 11 Hata Düzeltmeleri Uygulandı)

import logging
import tkinter as tk
from tkinter import ttk, messagebox, Listbox, StringVar, Frame, Label, Entry, Button, simpledialog, OptionMenu, filedialog 
import datetime
import os
import sys
from PIL import Image, ImageTk
import matplotlib.pyplot as plt 
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 


# Yerel modülleri içe aktar
from . import analyzer, database, reporter 

# Matplotlib import'larını try-except bloğuna alarak opsiyonel hale getirelim
try:
    # Bu importlar sadece MATPLOTLIB_AVAILABLE True ise kullanılacak
    # from matplotlib.figure import Figure
    # from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib kütüphanesi bulunamadı. Grafik özellikleri devre dışı bırakılacak.")


# --- Stil ve Tasarım Yapılandırması ---
STYLE_CONFIG = {
    "font_normal": ("Segoe UI", 10),
    "font_bold": ("Segoe UI Semibold", 11),
    "font_title": ("Segoe UI Light", 18),
    "header_bg": "#2c3e50",  # Koyu Mavi-Gri
    "header_fg": "#ecf0f1",  # Açık Gri
    "bg_color": "#ffffff",    # Beyaz
    "footer_bg": "#f8f9fa",  # Çok Açık Gri
    "accent_color": "#3498db", # Parlak Mavi
    "danger_color": "#e74c3c", # Kırmızı
    "success_color": "#2ecc71", # Yeşil
    "button_default_bg": "#e0e0e0", # Varsayılan buton rengi
    "button_default_fg": "black",
}

def resource_path(relative_path):
    """ PyInstaller ile paketlendiğinde varlık dosyalarına doğru yolu bulur. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, 'assets', relative_path)

def apply_global_styles():
    """Uygulama genelinde ttk stillerini ayarlar."""
    style = ttk.Style()
    style.theme_use('clam') 

    style.configure('.', font=STYLE_CONFIG["font_normal"]) 
    
    style.configure('TButton', font=STYLE_CONFIG["font_bold"], background=STYLE_CONFIG["button_default_bg"], foreground=STYLE_CONFIG["button_default_fg"])
    style.map('TButton', background=[('active', '#cceeff'), ('!disabled', STYLE_CONFIG["button_default_bg"])])

    style.configure('TLabel', font=STYLE_CONFIG["font_normal"], background=STYLE_CONFIG["bg_color"])
    style.configure('TCheckbutton', font=STYLE_CONFIG["font_normal"], background=STYLE_CONFIG["bg_color"])
    style.configure('TRadiobutton', font=STYLE_CONFIG["font_normal"], background=STYLE_CONFIG["bg_color"])
    style.configure('TEntry', font=STYLE_CONFIG["font_normal"])
    style.configure('TCombobox', font=STYLE_CONFIG["font_normal"])
    style.configure('TSpinbox', font=STYLE_CONFIG["font_normal"])
    # Tüm Frame'ler için ttk.Frame stili uygulandı.
    style.configure('TFrame', background=STYLE_CONFIG["bg_color"]) 
    style.configure('TLabelframe', background=STYLE_CONFIG["bg_color"])
    style.configure('TLabelframe.Label', font=STYLE_CONFIG["font_bold"], background=STYLE_CONFIG["bg_color"])

    style.configure('Treeview', font=STYLE_CONFIG["font_normal"], rowheight=25, background=STYLE_CONFIG["bg_color"], fieldbackground=STYLE_CONFIG["bg_color"], foreground='black')
    style.map('Treeview', background=[('selected', STYLE_CONFIG['accent_color'])], foreground=[('selected', 'white')])
    style.configure('Treeview.Heading', font=STYLE_CONFIG["font_bold"], background=STYLE_CONFIG["header_bg"], foreground=STYLE_CONFIG["header_fg"])
    
    style.configure('TNotebook', background=STYLE_CONFIG["bg_color"])
    style.configure('TNotebook.Tab', font=STYLE_CONFIG["font_bold"], background=STYLE_CONFIG["footer_bg"], foreground='black')
    style.map('TNotebook.Tab', background=[('selected', STYLE_CONFIG["accent_color"])], foreground=[('selected', 'white')])

    style.configure('Accent.TButton', background=STYLE_CONFIG["accent_color"], foreground='white')
    style.map('Accent.TButton', background=[('active', STYLE_CONFIG["accent_color"])])
    style.configure('Danger.TButton', background=STYLE_CONFIG["danger_color"], foreground='white')
    style.map('Danger.TButton', background=[('active', STYLE_CONFIG["danger_color"])])
    style.configure('Success.TButton', background=STYLE_CONFIG["success_color"], foreground='white')
    style.map('Success.TButton', background=[('active', STYLE_CONFIG["success_color"])])
    
    style.configure('TButton', padding=6)
    style.configure('TEntry', padding=5)
    style.configure('TCombobox', padding=5)
    style.configure('TSpinbox', padding=5)


class BaseWindow(tk.Toplevel):
    """Tüm pencereler için temel şablonu (header, main, footer) oluşturan sınıf."""
    def __init__(self, master, title, geometry):
        super().__init__(master)
        self.title(title)
        self.geometry(geometry)
        self.configure(bg=STYLE_CONFIG["bg_color"])
        self.overrideredirect(True) # Pencerenin başlık çubuğunu kaldır

        # Pencereyi ortala (geometry set edildikten sonra)
        self.update_idletasks() # Geometry uygulandıktan sonra boyutları alabilmek için
        self.center_window()

        # Sürükleme için değişkenler
        self._drag_start_x = 0
        self._drag_start_y = 0

        # --- Ana Yerleşim Alanları ---
        # Tüm Frame'ler için ttk.Frame kullanıyoruz ve padding'i style üzerinden yönetiyoruz.
        self.header_frame = ttk.Frame(self, style='TFrame', height=40) 
        self.main_frame = ttk.Frame(self, style='TFrame', padding=(15,15)) 
        self.footer_frame = ttk.Frame(self, style='TFrame', height=45) 
        
        # Header frame'i koyu renk yap
        self.header_frame.configure(style='Header.TFrame')
        
        self.header_frame.pack(fill='x', side='top')
        self.main_frame.pack(fill='both', expand=True)
        self.footer_frame.pack(fill='x', side='bottom')
        self.footer_frame.pack_propagate(False) # Footer'ın boyutunu korumak için

        # Header için özel stil
        style = ttk.Style()
        style.configure('Header.TFrame', background=STYLE_CONFIG["header_bg"])

        # Sürükleme olaylarını başlık çubuğuna bağla
        self.header_frame.bind("<ButtonPress-1>", self.start_drag)
        self.header_frame.bind("<B1-Motion>", self.do_drag)

        self.populate_header(title)
        
        # Başlık çubuğundaki standart kapatma butonu
        self.header_close_button = Button(self.header_frame, text="✕", command=self.destroy,
                                   bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"],
                                   relief='flat', font=("Segoe UI Symbol", 10), 
                                   activebackground=STYLE_CONFIG['danger_color'], activeforeground='white',
                                   bd=0, highlightthickness=0)
        self.header_close_button.pack(side='right', padx=10, pady=5)


    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_start_x
        y = self.winfo_y() + event.y - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def populate_header(self, title):
        """Varsayılan başlık bölümünü logo, başlık ve özel kapatma düğmesi ile doldurur."""
        # Logo
        try:
            logo_image = Image.open(resource_path("logo.png")).resize((25, 25), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = Label(self.header_frame, image=self.logo_photo, bg=STYLE_CONFIG["header_bg"])
            logo_label.pack(side='left', padx=(10,5), pady=5)
            logo_label.bind("<ButtonPress-1>", self.start_drag)
            logo_label.bind("<B1-Motion>", self.do_drag)
        except Exception as e:
            logging.warning(f"Logo yüklenemedi: {e}") 
            pass 

        title_label = Label(self.header_frame, text=title, font=STYLE_CONFIG["font_title"], bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"])
        title_label.pack(side='left', pady=5)
        title_label.bind("<ButtonPress-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.do_drag)
        
    def center_window(self):
        """Pencereyi ekranın ortasında açar."""
        width = self.winfo_width()
        height = self.winfo_height()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    # Alt sınıflar eğer footer'a ek bir kapatma butonu isterse bu metodu çağırabilirler.
    def add_footer_close_button(self):
        ttk.Button(self.footer_frame, text="Kapat", command=self.destroy,
                   style='Danger.TButton').pack(side='right', padx=15, pady=10)

    # _create_widgets metodu alt sınıflar tarafından doldurulacak.
    def _create_widgets(self):
        pass


class WelcomeWindow(BaseWindow): 
    def __init__(self, master, on_close_callback):
        super().__init__(master, "Kognita'ya Hoş Geldiniz!", "500x350")
        self.master = master
        self.on_close_callback = on_close_callback
        self.resizable(False, False)
        self.grab_set() # Ana pencereyi bloke et (modal)
        self.protocol("WM_DELETE_WINDOW", self._on_closing) # Kapatma butonuna basıldığında


        self._create_widgets()
        self.lift()
        self.attributes('-topmost', True) # Her zaman en üstte kal
        self.focus_force()


    def _create_widgets(self):
        # Header ve Footer BaseWindow'da oluşturuldu. İçerik main_frame içine yerleştirilecek.
        ttk.Label(self.main_frame, text="Kognita'ya Hoş Geldiniz!", font=STYLE_CONFIG["font_title"]).pack(pady=10)
        ttk.Label(self.main_frame, text="Dijital Ayak İzinizi Keşfetmek ve Verimliliğinizi Artırmak İçin Hazır Olun!", 
                  wraplength=400, justify=tk.CENTER, font=STYLE_CONFIG["font_normal"]).pack(pady=5)
        ttk.Label(self.main_frame, text="Uygulama arka planda çalışarak bilgisayar kullanım alışkanlıklarınızı takip edecek ve size özel raporlar sunacaktır.", 
                  wraplength=400, justify=tk.CENTER, font=STYLE_CONFIG["font_normal"]).pack(pady=5)
        ttk.Label(self.main_frame, text="Başlamak için 'Devam Et' butonuna tıklayın.", 
                  wraplength=400, justify=tk.CENTER, font=STYLE_CONFIG["font_normal"]).pack(pady=10)
        
        # 'Devam Et' butonu footer'da olacak
        ttk.Button(self.footer_frame, text="Devam Et", command=self._on_closing, 
                   style='Accent.TButton').pack(pady=10)


    def _on_closing(self):
        self.grab_release() # Modalı kaldır
        self.on_close_callback()
        self.destroy()

class ReportWindow(BaseWindow): 
    def __init__(self, master=None):
        super().__init__(master, "Kognita - Rapor ve Analiz", "900x700")
        self.resizable(False, False)
        self.current_report_range = "today" 

        self._create_widgets()
        self._load_report_data()
        # Footer'a özel bir kapatma butonu eklemek istersek:
        self.add_footer_close_button() 

    def _create_widgets(self):
        # Header ve Footer BaseWindow'da oluşturuldu. İçerik main_frame içine yerleştirilecek.
        top_controls_frame = ttk.Frame(self.main_frame) 
        top_controls_frame.pack(pady=10, fill=tk.X)

        ttk.Label(top_controls_frame, text="Rapor Aralığı:", font=STYLE_CONFIG["font_bold"]).pack(side=tk.LEFT, padx=5)
        
        self.range_var = StringVar(self)
        self.range_var.set(self.current_report_range) 
        
        range_options_display = ["Bugün", "Son 7 Gün", "Bu Hafta", "Bu Ay", "Tüm Zamanlar"]
        range_options_values = ["today", "last_7_days", "this_week", "this_month", "all_time"]
        
        initial_display_value = range_options_display[range_options_values.index(self.current_report_range)]
        
        self.range_combobox = ttk.Combobox(top_controls_frame, textvariable=self.range_var, 
                                            values=range_options_display, state="readonly", font=STYLE_CONFIG["font_normal"])
        self.range_combobox.set(initial_display_value)
        self.range_combobox.pack(side=tk.LEFT, padx=5)
        self.range_combobox.bind("<<ComboboxSelected>>", self._on_range_change_wrapper)
        
        self.range_var_map = dict(zip(range_options_display, range_options_values))
        self.range_value_map = dict(zip(range_options_values, range_options_display))


        ttk.Button(top_controls_frame, text="Verileri Dışa Aktar (CSV)", command=self._export_data).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_controls_frame, text="Raporu Dışa Aktar (PDF)", command=self._export_pdf_report).pack(side=tk.RIGHT, padx=5) 

        self.report_content_frame = ttk.Frame(self.main_frame) 
        self.report_content_frame.pack(expand=True, fill=tk.BOTH, pady=10)

        # persona_label ve total_duration_label burada oluşturulmalıydı. Düzeltildi.
        self.persona_label = ttk.Label(self.report_content_frame, text="", font=STYLE_CONFIG["font_bold"])
        self.persona_label.pack(pady=5)

        self.total_duration_label = ttk.Label(self.report_content_frame, text="", font=STYLE_CONFIG["font_normal"])
        self.total_duration_label.pack(pady=2)

        self.notebook = ttk.Notebook(self.report_content_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH, pady=10)

        self.category_tab = ttk.Frame(self.notebook) 
        self.notebook.add(self.category_tab, text="Kategori Detayları")
        self._create_category_table(self.category_tab)

        if MATPLOTLIB_AVAILABLE:
            self.pie_chart_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.pie_chart_tab, text="Kategori Dağılımı (Pasta)")
            self.pie_chart_canvas = None 

            self.weekly_comp_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.weekly_comp_tab, text="Haftalık Karşılaştırma")
            self.weekly_chart_canvas = None

            self.hourly_activity_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.hourly_activity_tab, text="Saatlik Aktivite")
            self.hourly_chart_canvas = None
            
            self.other_analysis_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.other_analysis_tab, text="Diğer Analizler")
            self._create_other_analysis_widgets(self.other_analysis_tab)

            self.app_trend_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.app_trend_tab, text="Uygulama Trendleri")
            self._create_app_trend_widgets(self.app_trend_tab)

            self.suggestions_tab = ttk.Frame(self.notebook)
            self.notebook.add(self.suggestions_tab, text="Öneriler")
            self._create_suggestions_widgets(self.suggestions_tab)

        else:
            messagebox.showwarning("Grafik Uyarısı", "Matplotlib kütüphanesi yüklenemedi. Grafik ve bazı analiz tabları gösterilmeyecektir.", parent=self)


    def _create_category_table(self, parent_frame):
        self.tree = ttk.Treeview(parent_frame, columns=("category", "duration", "percentage"), show="headings")
        self.tree.heading("category", text="Kategori")
        self.tree.heading("duration", text="Harcanan Süre")
        self.tree.heading("percentage", text="Yüzde")

        self.tree.column("category", width=200, anchor="w")
        self.tree.column("duration", width=150, anchor="center")
        self.tree.column("percentage", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_range_change_wrapper(self, event):
        selected_display_value = self.range_combobox.get()
        self.current_report_range = self.range_var_map.get(selected_display_value, "today")
        self._load_report_data()

    def _get_date_range(self, selection):
        today = datetime.datetime.now() 
        start_date = None
        end_date = today

        if selection == "today":
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        elif selection == "last_7_days":
            start_date = today - datetime.timedelta(days=7)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif selection == "this_week":
            start_date = today - datetime.timedelta(days=today.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif selection == "this_month":
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif selection == "all_time":
            start_date = datetime.datetime(2020, 1, 1) 
            end_date = today 

        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        return start_date, end_date
    
    def _load_report_data(self):
        start_date, end_date = self._get_date_range(self.current_report_range)
        category_totals, total_duration = analyzer.get_analysis_data(start_date, end_date)

        persona_text, table_data = reporter.get_report_data(category_totals, total_duration)
        self.persona_label.config(text=persona_text)
        self.total_duration_label.config(text=f"Toplam Aktif Süre: {reporter.format_duration(total_duration)}")

        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if table_data:
            for row in table_data:
                self.tree.insert("", "end", values=row)
        else:
            self.tree.insert("", "end", values=("Veri Yok", "", ""))
        
        if MATPLOTLIB_AVAILABLE:
            self._draw_pie_chart(category_totals, total_duration)
            self._draw_weekly_comparison_chart()
            self._draw_hourly_activity_chart()
            self._load_other_analysis_data()
            self._load_app_trend_data()
            self._load_suggestions_data(category_totals, total_duration) 

    def _draw_pie_chart(self, category_totals, total_duration):
        if self.pie_chart_canvas:
            self.pie_chart_canvas.get_tk_widget().destroy()
            self.pie_chart_canvas = None

        labels, sizes = reporter.get_chart_data(category_totals, total_duration)

        if not labels:
            ttk.Label(self.pie_chart_tab, text="Bu aralıkta pasta grafik için yeterli veri yok.", font=STYLE_CONFIG["font_normal"]).pack(pady=20)
            return

        fig = Figure(figsize=(6, 6), dpi=100)
        fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(STYLE_CONFIG['bg_color'])
        
        wedges, texts, autotexts = ax.pie(sizes, autopct='%1.1f%%', shadow=False, startangle=90, pctdistance=0.85, colors=plt.cm.Paired.colors)
        ax.axis('equal') 
        ax.set_title("Kategoriye Göre Süre Dağılımı", fontname='Segoe UI', fontsize=12, fontweight='bold', color='black')
        ax.legend(wedges, labels, title="Kategoriler", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False, fontsize=9, title_fontsize=10)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)

        fig.tight_layout() 

        self.pie_chart_canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_tab)
        self.pie_chart_canvas.draw()
        self.pie_chart_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        plt.close(fig) 

    def _draw_weekly_comparison_chart(self):
        if self.weekly_chart_canvas:
            self.weekly_chart_canvas.get_tk_widget().destroy()
            self.weekly_chart_canvas = None
        
        comparison_data = analyzer.get_weekly_comparison()
        
        if not comparison_data:
            ttk.Label(self.weekly_comp_tab, text="Haftalık karşılaştırma için yeterli veri yok (Bu hafta veya geçen hafta kullanım).", font=STYLE_CONFIG["font_normal"]).pack(pady=20)
            return

        categories = list(comparison_data.keys())
        this_week_times = [comparison_data[cat]['this_week'] for cat in categories]
        last_week_times = [comparison_data[cat]['last_week'] for cat in categories]

        fig = Figure(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(STYLE_CONFIG['bg_color'])
        
        x = range(len(categories))
        width = 0.35

        ax.bar([i - width/2 for i in x], this_week_times, width, label='Bu Hafta', color=STYLE_CONFIG["accent_color"])
        ax.bar([i + width/2 for i in x], last_week_times, width, label='Geçen Hafta', color=STYLE_CONFIG["danger_color"])

        ax.set_ylabel('Süre (Dakika)', fontname='Segoe UI', color='black')
        ax.set_title('En Çok Kullanılan Kategorilerin Haftalık Karşılaştırması', fontname='Segoe UI', fontsize=12, fontweight='bold', color='black')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha="right", fontname='Segoe UI', color='black')
        ax.tick_params(axis='y', colors='black') 
        ax.legend(prop={'family': 'Segoe UI', 'size': 9}, frameon=False)
        fig.tight_layout() 

        self.weekly_chart_canvas = FigureCanvasTkAgg(fig, master=self.weekly_comp_tab)
        self.weekly_chart_canvas.draw()
        self.weekly_chart_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        plt.close(fig)

    def _draw_hourly_activity_chart(self):
        if self.hourly_chart_canvas:
            self.hourly_chart_canvas.get_tk_widget().destroy()
            self.hourly_chart_canvas = None

        hourly_data = analyzer.get_hourly_activity()
        
        if not hourly_data:
            ttk.Label(self.hourly_activity_tab, text="Saatlik aktivite grafiği için yeterli veri yok.", font=STYLE_CONFIG["font_normal"]).pack(pady=20)
            return

        hours = sorted(hourly_data.keys())
        durations = [hourly_data[h] / 60 for h in hours] 

        fig = Figure(figsize=(9, 5), dpi=100)
        fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(STYLE_CONFIG['bg_color'])

        ax.bar(hours, durations, color=STYLE_CONFIG["accent_color"])
        ax.set_xlabel('Saat Aralığı (0-23)', fontname='Segoe UI', color='black')
        ax.set_ylabel('Ortalama Süre (Dakika)', fontname='Segoe UI', color='black')
        ax.set_title('Son 7 Günlük Ortalama Saatlik Aktivite', fontname='Segoe UI', fontsize=12, fontweight='bold', color='black')
        ax.set_xticks(range(24))
        ax.tick_params(axis='x', colors='black')
        ax.tick_params(axis='y', colors='black')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        fig.tight_layout()

        self.hourly_chart_canvas = FigureCanvasTkAgg(fig, master=self.hourly_activity_tab)
        self.hourly_chart_canvas.draw()
        self.hourly_chart_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        plt.close(fig)

    def _create_other_analysis_widgets(self, parent_frame):
        daily_avg_frame = ttk.LabelFrame(parent_frame, text="Son 7 Günlük Kategori Ortalama Kullanım", padding=10)
        daily_avg_frame.pack(fill=tk.X, padx=10, pady=10)

        self.daily_avg_tree = ttk.Treeview(daily_avg_frame, columns=("category", "average_duration"), show="headings")
        self.daily_avg_tree.heading("category", text="Kategori")
        self.daily_avg_tree.heading("average_duration", text="Günlük Ortalama Süre")
        self.daily_avg_tree.column("category", width=200, anchor="w")
        self.daily_avg_tree.column("average_duration", width=200, anchor="center")
        self.daily_avg_tree.pack(fill=tk.BOTH, expand=True)

        productive_day_frame = ttk.LabelFrame(parent_frame, text="En Verimli Gün (Son 30 Gün)", padding=10)
        productive_day_frame.pack(fill=tk.X, padx=10, pady=10)

        self.productive_day_label = ttk.Label(productive_day_frame, text="", font=STYLE_CONFIG["font_normal"])
        self.productive_day_label.pack(pady=5)


    def _load_other_analysis_data(self):
        for item in self.daily_avg_tree.get_children():
            self.daily_avg_tree.delete(item)
        
        daily_avg_data = analyzer.get_daily_average_usage_by_category(num_days=7)
        if daily_avg_data:
            sorted_data = sorted(daily_avg_data.items(), key=lambda item: item[1], reverse=True)
            for category, duration in sorted_data:
                self.daily_avg_tree.insert("", "end", values=(category, reporter.format_duration(duration)))
        else:
            self.daily_avg_tree.insert("", "end", values=("Veri Yok", ""))

        most_productive_day, max_time = analyzer.get_most_productive_day()
        if most_productive_day != "Yeterli Veri Yok":
            self.productive_day_label.config(text=f"En verimli gününüz: {most_productive_day} (Toplam verimli süre: {reporter.format_duration(max_time)})")
        else:
            self.productive_day_label.config(text="En verimli gün verisi için yeterli aktif kullanım yok.")
    
    def _create_app_trend_widgets(self, parent_frame):
        top_frame = ttk.Frame(parent_frame, padding=10)
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Uygulama Seç:", font=STYLE_CONFIG["font_bold"]).pack(side=tk.LEFT, padx=5)
        self.app_trend_process_var = StringVar()
        
        self.app_trend_process_combobox = ttk.Combobox(top_frame, textvariable=self.app_trend_process_var, state="readonly", font=STYLE_CONFIG["font_normal"])
        self.app_trend_process_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.app_trend_process_combobox['values'] = sorted(database.get_all_processes())
        if self.app_trend_process_combobox['values']:
            self.app_trend_process_combobox.set(self.app_trend_process_combobox['values'][0])
        self.app_trend_process_combobox.bind("<<ComboboxSelected>>", self._load_app_trend_data)

        self.app_trend_chart_canvas = None

    def _load_app_trend_data(self, event=None):
        if self.app_trend_chart_canvas:
            self.app_trend_chart_canvas.get_tk_widget().destroy()
            self.app_trend_chart_canvas = None

        selected_process = self.app_trend_process_var.get()
        if not selected_process:
            ttk.Label(self.app_trend_tab, text="Lütfen trendini görmek istediğiniz bir uygulama seçin.", font=STYLE_CONFIG["font_normal"]).pack(pady=20)
            return

        app_usage_data = analyzer.get_app_usage_over_time(selected_process, num_days=30)
        
        if not app_usage_data:
            ttk.Label(self.app_trend_tab, text=f"'{selected_process}' için son 30 güne ait kullanım verisi bulunamadı.", font=STYLE_CONFIG["font_normal"]).pack(pady=20)
            return

        all_dates = []
        current_date = (datetime.datetime.now() - datetime.timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        while current_date <= datetime.datetime.now():
            all_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += datetime.timedelta(days=1)

        durations_minutes = [app_usage_data.get(d, 0) / 60 for d in all_dates] 

        fig = Figure(figsize=(10, 5), dpi=100)
        fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111)
        ax.set_facecolor(STYLE_CONFIG['bg_color'])

        ax.plot(all_dates, durations_minutes, marker='o', linestyle='-', color=STYLE_CONFIG["accent_color"])
        ax.set_xlabel('Tarih', fontname='Segoe UI', color='black')
        ax.set_ylabel('Süre (Dakika)', fontname='Segoe UI', color='black')
        ax.set_title(f"'{selected_process}' Uygulaması Günlük Kullanım Trendi (Son 30 Gün)", fontname='Segoe UI', fontsize=12, fontweight='bold', color='black')
        ax.tick_params(axis='x', rotation=45, colors='black')
        ax.tick_params(axis='y', colors='black')
        if len(all_dates) > 10:
            ax.set_xticks(all_dates[::len(all_dates)//5]) 
        ax.grid(True, linestyle='--', alpha=0.6)
        fig.tight_layout()

        self.app_trend_chart_canvas = FigureCanvasTkAgg(fig, master=self.app_trend_tab)
        self.app_trend_chart_canvas.draw()
        self.app_trend_chart_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        plt.close(fig)

    def _create_suggestions_widgets(self, parent_frame):
        self.suggestions_label_frame = ttk.LabelFrame(parent_frame, text="Kişiselleştirilmiş Öneriler", padding=10)
        self.suggestions_label_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.suggestions_text = tk.Text(self.suggestions_label_frame, wrap=tk.WORD, height=10, font=STYLE_CONFIG["font_normal"], bg=STYLE_CONFIG["bg_color"], fg='black', relief=tk.FLAT)
        self.suggestions_text.pack(fill=tk.BOTH, expand=True)
        self.suggestions_text.config(state=tk.DISABLED) 

    def _load_suggestions_data(self, category_totals, total_duration):
        self.suggestions_text.config(state=tk.NORMAL)
        self.suggestions_text.delete(1.0, tk.END) 
        
        suggestions = analyzer.get_user_suggestions(category_totals, total_duration)
        for i, suggestion in enumerate(suggestions):
            self.suggestions_text.insert(tk.END, f"• {suggestion}\n\n")
        
        self.suggestions_text.config(state=tk.DISABLED) 


    def _export_data(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Verileri Dışa Aktar (CSV)"
        )
        if file_path:
            success, error = database.export_all_data_to_csv(file_path)
            if success:
                messagebox.showinfo("Başarılı", f"Veriler '{file_path}' konumuna başarıyla dışa aktarıldı.", parent=self)
            else:
                messagebox.showerror("Hata", f"Veri dışa aktarılırken bir hata oluştu: {error}", parent=self)

    def _export_pdf_report(self):
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Hata", "PDF dışa aktarma için 'ReportLab' kütüphanesi gereklidir.", parent=self)
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Raporu Dışa Aktar (PDF)"
        )
        if file_path:
            start_date, end_date = self._get_date_range(self.current_report_range)
            success, error = reporter.create_pdf_report(file_path, start_date, end_date) 
            if success:
                messagebox.showinfo("Başarılı", f"PDF raporu '{file_path}' konumuna başarıyla oluşturuldu.", parent=self)
            else:
                messagebox.showerror("Hata", f"PDF raporu oluşturulurken bir hata oluştu: {error}", parent=self)


class GoalsWindow(BaseWindow): 
    def __init__(self, master=None):
        super().__init__(master, "Kognita - Hedefleri Yönet", "700x550") 
        self.resizable(False, False)

        self._create_widgets()
        self._load_goals()
        self.add_footer_close_button()


    def _create_widgets(self):
        add_frame = ttk.LabelFrame(self.main_frame, text="Yeni Hedef Ekle/Güncelle", padding=10)
        add_frame.pack(pady=10, padx=5, fill=tk.X) 

        add_frame.grid_columnconfigure(1, weight=1) 

        ttk.Label(add_frame, text="Hedef Tipi:", font=STYLE_CONFIG["font_normal"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.goal_type_var = StringVar()
        self.goal_type_combobox = ttk.Combobox(add_frame, textvariable=self.goal_type_var, 
                                                values=["min_usage", "max_usage", "block", "time_window_max"], 
                                                state="readonly", font=STYLE_CONFIG["font_normal"])
        self.goal_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.goal_type_combobox.set("max_usage") 
        self.goal_type_combobox.bind("<<ComboboxSelected>>", self._on_goal_type_change)

        self.dynamic_fields_frame = ttk.Frame(add_frame) 
        self.dynamic_fields_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.dynamic_fields_frame.grid_columnconfigure(1, weight=1)

        self._create_dynamic_goal_fields() 

        ttk.Button(add_frame, text="Hedef Ekle/Güncelle", command=self._add_or_update_goal, 
                   style='Accent.TButton').grid(row=10, column=0, columnspan=2, pady=10) 

        list_frame = ttk.LabelFrame(self.main_frame, text="Mevcut Hedefler", padding=10)
        list_frame.pack(pady=10, padx=5, fill=tk.BOTH, expand=True) 

        self.goals_tree = ttk.Treeview(list_frame, columns=("id", "type", "target", "limit", "time_window"), show="headings")
        self.goals_tree.heading("type", text="Tip")
        self.goals_tree.heading("target", text="Hedef (Kategori/Uyg.)")
        self.goals_tree.heading("limit", text="Süre Limiti (Dk)")
        self.goals_tree.heading("time_window", text="Zaman Aralığı")
        
        self.goals_tree.column("id", width=0, stretch=tk.NO) 
        self.goals_tree.column("type", width=100, anchor="w")
        self.goals_tree.column("target", width=180, anchor="w")
        self.goals_tree.column("limit", width=120, anchor="center")
        self.goals_tree.column("time_window", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.goals_tree.yview)
        self.goals_tree.configure(yscrollcommand=scrollbar.set)
        
        self.goals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(self.footer_frame, text="Seçili Hedefi Sil", command=self._delete_goal, 
                   style='Danger.TButton').pack(pady=10, padx=15, side=tk.RIGHT) 
        
    def _create_dynamic_goal_fields(self):
        for widget in self.dynamic_fields_frame.winfo_children():
            widget.destroy()

        goal_type = self.goal_type_var.get()

        if goal_type in ['min_usage', 'max_usage']:
            ttk.Label(self.dynamic_fields_frame, text="Kategori:", font=STYLE_CONFIG["font_normal"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.category_for_goal_var = StringVar()
            self.category_for_goal_combobox = ttk.Combobox(self.dynamic_fields_frame, textvariable=self.category_for_goal_var, state="readonly", font=STYLE_CONFIG["font_normal"])
            self.category_for_goal_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            self.category_for_goal_combobox['values'] = database.get_all_categories()
            if self.category_for_goal_combobox['values']:
                self.category_for_goal_combobox.set(self.category_for_goal_combobox['values'][0])

            ttk.Label(self.dynamic_fields_frame, text="Süre (Dakika):", font=STYLE_CONFIG["font_normal"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            self.time_limit_entry = ttk.Entry(self.dynamic_fields_frame, font=STYLE_CONFIG["font_normal"])
            self.time_limit_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        elif goal_type == 'block':
            ttk.Label(self.dynamic_fields_frame, text="Uygulama Adı:", font=STYLE_CONFIG["font_normal"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.process_name_for_goal_var = StringVar()
            self.process_name_for_goal_combobox = ttk.Combobox(self.dynamic_fields_frame, textvariable=self.process_name_for_goal_var, font=STYLE_CONFIG["font_normal"])
            self.process_name_for_goal_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            self.process_name_for_goal_combobox['values'] = database.get_all_processes() 
            if self.process_name_for_goal_combobox['values']:
                self.process_name_for_goal_combobox.set(self.process_name_for_goal_combobox['values'][0])

            ttk.Label(self.dynamic_fields_frame, text="Engellenecek (Sürekli Takip Edilir)", font=STYLE_CONFIG["font_normal"]).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
            
        elif goal_type == 'time_window_max':
            ttk.Label(self.dynamic_fields_frame, text="Kategori:", font=STYLE_CONFIG["font_normal"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            self.category_for_goal_var = StringVar()
            self.category_for_goal_combobox = ttk.Combobox(self.dynamic_fields_frame, textvariable=self.category_for_goal_var, state="readonly", font=STYLE_CONFIG["font_normal"])
            self.category_for_goal_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            self.category_for_goal_combobox['values'] = database.get_all_categories()
            if self.category_for_goal_combobox['values']:
                self.category_for_goal_combobox.set(self.category_for_goal_combobox['values'][0])

            ttk.Label(self.dynamic_fields_frame, text="Zaman Aralığı (HH:MM - HH:MM):", font=STYLE_CONFIG["font_normal"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
            time_frame = ttk.Frame(self.dynamic_fields_frame) 
            time_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

            self.start_time_hour_var = StringVar(value="09")
            self.start_time_min_var = StringVar(value="00")
            self.end_time_hour_var = StringVar(value="17")
            self.end_time_min_var = StringVar(value="00")

            ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.start_time_hour_var, width=3, format="%02.0f", font=STYLE_CONFIG["font_normal"]).pack(side=tk.LEFT)
            ttk.Label(time_frame, text=":", font=STYLE_CONFIG["font_normal"]).pack(side=tk.LEFT)
            ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.start_time_min_var, width=3, format="%02.0f", font=STYLE_CONFIG["font_normal"]).pack(side=tk.LEFT)
            ttk.Label(time_frame, text=" - ", font=STYLE_CONFIG["font_normal"]).pack(side=tk.LEFT)
            ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.end_time_hour_var, width=3, format="%02.0f", font=STYLE_CONFIG["font_normal"]).pack(side=tk.LEFT)
            ttk.Label(time_frame, text=":", font=STYLE_CONFIG["font_normal"]).pack(side=tk.LEFT)
            ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.end_time_min_var, width=3, format="%02.0f", font=STYLE_CONFIG["font_normal"]).pack(side=tk.LEFT)

            ttk.Label(self.dynamic_fields_frame, text="Maks. Süre (Dakika):", font=STYLE_CONFIG["font_normal"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
            self.time_limit_entry = ttk.Entry(self.dynamic_fields_frame, font=STYLE_CONFIG["font_normal"])
            self.time_limit_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    def _on_goal_type_change(self, *args):
        self._create_dynamic_goal_fields()

    def _load_goals(self):
        for item in self.goals_tree.get_children():
            self.goals_tree.delete(item)
        
        goals = database.get_goals()
        for goal in goals:
            target_str = goal['category'] if goal['category'] else goal['process_name'] if goal['process_name'] else "N/A"
            limit_str = f"{goal['time_limit_minutes']} dk" if goal['time_limit_minutes'] is not None else "N/A"
            time_window_str = f"{goal['start_time_of_day']}-{goal['end_time_of_day']}" if goal['start_time_of_day'] else "Tüm Gün"
            
            self.goals_tree.insert("", "end", iid=goal['id'], values=(
                goal['goal_type'].replace('_', ' ').title(), 
                target_str, 
                limit_str, 
                time_window_str
            ))

    def _add_or_update_goal(self):
        goal_type = self.goal_type_var.get()
        category = None
        process_name = None
        time_limit = None
        start_time_of_day = None
        end_time_of_day = None

        try:
            if goal_type in ['min_usage', 'max_usage']:
                category = self.category_for_goal_var.get()
                time_limit_str = self.time_limit_entry.get()
                if not category or not time_limit_str: raise ValueError("Kategori veya süre boş olamaz.")
                time_limit = int(time_limit_str)
                if time_limit <= 0: raise ValueError("Süre pozitif bir sayı olmalıdır.")
            
            elif goal_type == 'block':
                process_name = self.process_name_for_goal_var.get()
                if not process_name: raise ValueError("Uygulama adı boş olamaz.")
            
            elif goal_type == 'time_window_max':
                category = self.category_for_goal_var.get()
                start_h = self.start_time_hour_var.get()
                start_m = self.start_time_min_var.get()
                end_h = self.end_time_hour_var.get()
                end_m = self.end_time_min_var.get()
                time_limit_str = self.time_limit_entry.get()

                if not category or not start_h or not start_m or not end_h or not end_m or not time_limit_str:
                    raise ValueError("Tüm alanları doldurun.")
                
                start_time_of_day = f"{int(start_h):02d}:{int(start_m):02d}"
                end_time_of_day = f"{int(end_h):02d}:{int(end_m):02d}"
                time_limit = int(time_limit_str)
                if time_limit <= 0: raise ValueError("Maksimum süre pozitif bir sayı olmalıdır.")
                
                start_dt = datetime.datetime.strptime(start_time_of_day, '%H:%M').time()
                end_dt = datetime.datetime.strptime(end_time_of_day, '%H:%M').time()
                if start_dt >= end_dt:
                    messagebox.showwarning("Zaman Hatası", "Başlangıç saati bitiş saatinden önce olmalıdır.", parent=self)
                    return

        except ValueError as e:
            messagebox.showwarning("Geçersiz Giriş", f"Lütfen geçerli değerler girin: {e}", parent=self)
            return
        except Exception as e:
            logging.error(f"Hedef eklerken/güncellerken hata: {e}", exc_info=True)
            messagebox.showerror("Hata", f"Beklenmedik bir hata oluştu: {e}", parent=self)
            return

        database.add_goal(category, process_name, goal_type, time_limit, start_time_of_day, end_time_of_day)
        messagebox.showinfo("Başarılı", "Hedef başarıyla eklendi/güncellendi.", parent=self)
        self._load_goals() 
        self._create_dynamic_goal_fields() 

    def _delete_goal(self):
        selected_item = self.goals_tree.selection()
        if not selected_item:
            messagebox.showwarning("Seçim Yok", "Lütfen silmek istediğiniz hedefi seçin.", parent=self)
            return
        
        goal_id = self.goals_tree.item(selected_item, 'iid') 
        
        if messagebox.askyesno("Hedef Sil", "Bu hedefi silmek istediğinizden emin misiniz?", parent=self):
            database.delete_goal(goal_id)
            messagebox.showinfo("Başarılı", "Hedef başarıyla silindi.", parent=self)
            self._load_goals() 

class SettingsWindow(BaseWindow): 
    def __init__(self, master=None, app_instance=None):
        super().__init__(master, "Kognita - Ayarlar", "500x580") 
        self.resizable(False, False)
        self.app_instance = app_instance 
        self.config_manager = app_instance.config_manager if app_instance else None

        self._create_widgets()
        self._load_settings()
        self.add_footer_close_button()


    def _create_widgets(self):
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        content_frame.grid_columnconfigure(1, weight=1) 

        # Genel Ayarlar
        general_settings_frame = ttk.LabelFrame(content_frame, text="Genel Ayarlar", padding=10)
        general_settings_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        general_settings_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(general_settings_frame, text="Boşta Kalma Eşiği (saniye):", font=STYLE_CONFIG["font_normal"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.idle_threshold_var = tk.IntVar()
        self.idle_threshold_entry = ttk.Entry(general_settings_frame, textvariable=self.idle_threshold_var, font=STYLE_CONFIG["font_normal"])
        self.idle_threshold_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(general_settings_frame, text="Uygulama Dili:", font=STYLE_CONFIG["font_normal"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.language_var = StringVar()
        self.language_combobox = ttk.Combobox(general_settings_frame, textvariable=self.language_var, values=["tr", "en"], state="readonly", font=STYLE_CONFIG["font_normal"])
        self.language_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.language_combobox.bind("<<ComboboxSelected>>", self._on_language_change)

        self.run_on_startup_var = tk.BooleanVar()
        ttk.Checkbutton(general_settings_frame, text="Windows Başlangıcında Çalıştır", variable=self.run_on_startup_var, 
                        command=self._on_run_on_startup_change, font=STYLE_CONFIG["font_normal"]).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        ttk.Label(general_settings_frame, text="Veri Saklama Süresi (gün):", font=STYLE_CONFIG["font_normal"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.data_retention_var = tk.IntVar()
        self.data_retention_spinbox = ttk.Spinbox(general_settings_frame, from_=0, to=9999, increment=1, textvariable=self.data_retention_var, font=STYLE_CONFIG["font_normal"], width=10)
        self.data_retention_spinbox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(general_settings_frame, text="(0 = Sonsuz, negatif değer olamaz)", font=STYLE_CONFIG["font_normal"]).grid(row=4, column=0, columnspan=2, padx=5, sticky="w")


        # Bildirim Ayarları
        notification_frame = ttk.LabelFrame(content_frame, text="Bildirim Ayarları", padding=10) 
        notification_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=15, sticky="ew") 
        notification_frame.grid_columnconfigure(1, weight=1) 

        self.enable_goal_notifications_var = tk.BooleanVar()
        ttk.Checkbutton(notification_frame, text="Hedef Bildirimlerini Etkinleştir", variable=self.enable_goal_notifications_var, font=STYLE_CONFIG["font_normal"]).grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        self.enable_focus_notifications_var = tk.BooleanVar()
        ttk.Checkbutton(notification_frame, text="Odaklanma Modu Bildirimlerini Etkinleştir", variable=self.enable_focus_notifications_var, font=STYLE_CONFIG["font_normal"]).grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        ttk.Label(notification_frame, text="Odaklanma Bildirim Sıklığı (sn):", font=STYLE_CONFIG["font_normal"]).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.focus_freq_var = tk.IntVar()
        self.focus_freq_entry = ttk.Entry(notification_frame, textvariable=self.focus_freq_var, font=STYLE_CONFIG["font_normal"])
        self.focus_freq_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        self.show_achievement_notifications_var = tk.BooleanVar()
        ttk.Checkbutton(notification_frame, text="Başarım Bildirimlerini Göster", variable=self.show_achievement_notifications_var, font=STYLE_CONFIG["font_normal"]).grid(row=3, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        # Gelişmiş Ayarlar (Sentry vb.)
        advanced_settings_frame = ttk.LabelFrame(content_frame, text="Gelişmiş Ayarlar", padding=10)
        advanced_settings_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=15, sticky="ew") 
        advanced_settings_frame.grid_columnconfigure(1, weight=1)

        self.enable_sentry_reporting_var = tk.BooleanVar()
        ttk.Checkbutton(advanced_settings_frame, text="Anonim Hata Raporlamasını Etkinleştir (Sentry)", variable=self.enable_sentry_reporting_var, font=STYLE_CONFIG["font_normal"]).grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        ttk.Button(self.footer_frame, text="Ayarları Kaydet", command=self._save_settings, 
                   style='Accent.TButton').pack(side='right', padx=15, pady=10)
        
        ttk.Button(self.footer_frame, text="Güncellemeleri Kontrol Et", command=self._check_for_updates).pack(side='right', padx=(0, 5), pady=10)


    def _load_settings(self):
        if not self.config_manager:
            return
            
        self.idle_threshold_var.set(self.config_manager.get('settings.idle_threshold_seconds', 180))
        self.language_var.set(self.config_manager.get('settings.language', 'tr'))
        self.run_on_startup_var.set(self.config_manager.get('settings.run_on_startup', False))
        self.enable_sentry_reporting_var.set(self.config_manager.get('settings.enable_sentry_reporting', True))
        self.data_retention_var.set(self.config_manager.get('settings.data_retention_days', 365))
        
        notif_settings = self.config_manager.get('settings.notification_settings', {})
        self.enable_goal_notifications_var.set(notif_settings.get('enable_goal_notifications', True))
        self.enable_focus_notifications_var.set(notif_settings.get('enable_focus_notifications', True))
        self.focus_freq_var.set(notif_settings.get('focus_notification_frequency_seconds', 300))
        self.show_achievement_notifications_var.set(notif_settings.get('show_achievement_notifications', True))


    def _save_settings(self):
        if not self.config_manager:
            messagebox.showerror("Hata", "Yapılandırma yöneticisi bulunamadı.", parent=self)
            return
            
        try:
            new_idle_threshold = self.idle_threshold_var.get()
            if new_idle_threshold <= 0:
                messagebox.showwarning("Geçersiz Değer", "Boşta kalma eşiği pozitif bir sayı olmalıdır.", parent=self)
                return
            self.config_manager.set('settings.idle_threshold_seconds', new_idle_threshold)
            
            new_notif_settings = {
                "enable_goal_notifications": self.enable_goal_notifications_var.get(),
                "enable_focus_notifications": self.enable_focus_notifications_var.get(),
                "focus_notification_frequency_seconds": self.focus_freq_var.get(),
                "show_achievement_notifications": self.show_achievement_notifications_var.get()
            }
            if new_notif_settings["focus_notification_frequency_seconds"] <= 0:
                 messagebox.showwarning("Geçersiz Değer", "Odaklanma bildirim sıklığı pozitif bir sayı olmalıdır.", parent=self)
                 return

            self.config_manager.set('settings.notification_settings', new_notif_settings)
            
            self.config_manager.set('settings.run_on_startup', self.run_on_startup_var.get())
            self.config_manager.set('settings.enable_sentry_reporting', self.enable_sentry_reporting_var.get())
            
            new_data_retention_days = self.data_retention_var.get()
            if new_data_retention_days < 0: 
                 messagebox.showwarning("Geçersiz Değer", "Veri saklama süresi negatif olamaz.", parent=self)
                 return
            self.config_manager.set('settings.data_retention_days', new_data_retention_days)


            if self.app_instance:
                self.app_instance._set_run_on_startup(self.run_on_startup_var.get())
                self.app_instance.tracker_instance.update_settings(self.config_manager.get('settings'))
            
            messagebox.showinfo("Başarılı", "Ayarlar başarıyla kaydedildi.", parent=self)
        except ValueError:
            messagebox.showwarning("Geçersiz Giriş", "Ayarlar için geçerli sayısal değerler girin.", parent=self)
        except Exception as e:
            logging.error(f"Ayarlar kaydedilirken hata: {e}", exc_info=True)
            messagebox.showerror("Hata", f"Ayarlar kaydedilirken bir hata oluştu: {e}", parent=self)

    def _on_language_change(self, event):
        new_language = self.language_var.get()
        if self.config_manager:
            self.config_manager.set('settings.language', new_language)
        messagebox.showinfo("Bilgi", f"Uygulama dili '{new_language}' olarak ayarlandı. Değişiklikler bir sonraki başlatmada tam olarak uygulanabilir.", parent=self)

    def _on_run_on_startup_change(self):
        pass 

    def _check_for_updates(self):
        messagebox.showinfo("Güncelleme Kontrolü", "Güncellemeler kontrol ediliyor... (Bu özellik şu an için bir placeholder'dır).", parent=self)


class FocusSetupWindow(BaseWindow): 
    def __init__(self, master, on_start_callback):
        super().__init__(master, "Kognita - Odaklanma Oturumu Ayarla", "400x480") 
        self.resizable(False, False)
        self.on_start_callback = on_start_callback

        self._create_widgets()
        self.add_footer_close_button()


    def _create_widgets(self):
        content_frame = ttk.Frame(self.main_frame) 
        content_frame.pack(fill=tk.BOTH, expand=True)

        content_frame.grid_columnconfigure(0, weight=1) 

        ttk.Label(content_frame, text="Oturum Süresi (Dakika):", font=STYLE_CONFIG["font_bold"]).pack(pady=(10, 5))
        self.duration_var = tk.IntVar(value=60)
        self.duration_spinbox = ttk.Spinbox(content_frame, from_=10, to=240, increment=10, textvariable=self.duration_var, width=10, font=STYLE_CONFIG["font_normal"])
        self.duration_spinbox.pack(pady=5)

        ttk.Label(content_frame, text="İzin Verilen Kategoriler:", font=STYLE_CONFIG["font_bold"]).pack(pady=(15, 5))
        
        self.categories_frame = ttk.LabelFrame(content_frame, text="Seçilebilir Kategoriler", padding=10)
        self.categories_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)

        canvas = tk.Canvas(self.categories_frame, borderwidth=0, background=STYLE_CONFIG["bg_color"])
        vscroll = ttk.Scrollbar(self.categories_frame, orient="vertical", command=canvas.yview)
        canvas_frame = ttk.Frame(canvas) 

        canvas.create_window((0, 0), window=canvas_frame, anchor="nw")
        canvas.configure(yscrollcommand=vscroll.set)

        canvas_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        all_categories = database.get_all_categories()
        if "Other" not in all_categories:
            all_categories.append("Other")
        
        self.category_vars = {}
        row_num = 0
        for category in sorted(all_categories):
            var = tk.BooleanVar(value=True) 
            cb = ttk.Checkbutton(canvas_frame, text=category, variable=var, font=STYLE_CONFIG["font_normal"])
            cb.grid(row=row_num, column=0, sticky="w", padx=5, pady=2)
            self.category_vars[category] = var
            row_num += 1

        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")


        ttk.Button(self.footer_frame, text="Odaklanmayı Başlat", command=self._start_session, 
                   style='Accent.TButton').pack(pady=10, padx=15, side=tk.RIGHT)

    def _start_session(self):
        duration = self.duration_var.get()
        allowed_categories = [cat for cat, var in self.category_vars.items() if var.get()]

        if duration <= 0:
            messagebox.showwarning("Geçersiz Süre", "Lütfen pozitif bir oturum süresi girin.", parent=self)
            return
        
        if not allowed_categories:
            messagebox.showwarning("Kategori Seçimi", "Lütfen en az bir izin verilen kategori seçin.", parent=self)
            return

        self.on_start_callback(duration, allowed_categories)
        self.destroy()

class CategoryManagementWindow(BaseWindow): 
    def __init__(self, master=None):
        super().__init__(master, "Kognita - Kategorileri Yönet", "750x550") 
        self.resizable(False, False)

        self._create_widgets()
        self._load_data()
        self.add_footer_close_button()


    def _create_widgets(self):
        content_frame = ttk.Frame(self.main_frame) 
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(content_frame, text="Kategorize Edilmemiş Uygulamalar", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.uncategorized_listbox = Listbox(left_frame, selectmode=tk.SINGLE, font=STYLE_CONFIG["font_normal"])
        self.uncategorized_listbox.pack(fill=tk.BOTH, expand=True)
        self.uncategorized_listbox.bind("<<ListboxSelect>>", self._on_uncategorized_select)

        middle_frame = ttk.Frame(content_frame) 
        middle_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(middle_frame, text="Kategori Seç:", font=STYLE_CONFIG["font_bold"]).pack(pady=(0,5))
        self.category_combobox = ttk.Combobox(middle_frame, state="readonly", font=STYLE_CONFIG["font_normal"])
        self.category_combobox.pack(pady=5)
        
        ttk.Button(middle_frame, text="Kategori Ata", command=self._assign_category, 
                   style='Accent.TButton').pack(pady=(15,10))
        ttk.Button(middle_frame, text="Yeni Kategori Ekle", command=self._add_new_category).pack(pady=10)
        ttk.Button(middle_frame, text="Seçili Kategoriyi Sil", command=self._delete_selected_category, 
                   style='Danger.TButton').pack(pady=10)


        right_frame = ttk.LabelFrame(content_frame, text="Kategorize Edilmiş Uygulamalar", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.categorized_tree = ttk.Treeview(right_frame, columns=("process_name", "category"), show="headings")
        self.categorized_tree.heading("process_name", text="Uygulama Adı")
        self.categorized_tree.heading("category", text="Kategori")
        self.categorized_tree.column("process_name", width=150)
        self.categorized_tree.column("category", width=120)
        self.categorized_tree.pack(fill=tk.BOTH, expand=True)
        self.categorized_tree.bind("<<TreeviewSelect>>", self._on_categorized_select)
        
        tree_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.categorized_tree.yview)
        self.categorized_tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


    def _load_data(self):
        self.uncategorized_listbox.delete(0, tk.END)
        uncategorized_apps = database.get_uncategorized_apps()
        for app in uncategorized_apps:
            self.uncategorized_listbox.insert(tk.END, app)
        
        all_categories = database.get_all_categories()
        if 'Other' not in all_categories: 
            all_categories.append('Other')
        self.category_combobox['values'] = sorted(all_categories) 
        if all_categories:
            self.category_combobox.set(all_categories[0]) 

        self.categorized_tree.delete(*self.categorized_tree.get_children())
        
        with database.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT process_name, category FROM app_categories ORDER BY category, process_name")
            categorized_apps = cursor.fetchall()

        for app, category in categorized_apps:
            self.categorized_tree.insert("", "end", values=(app, category))


    def _on_uncategorized_select(self, event):
        selected_index = self.uncategorized_listbox.curselection()
        if selected_index:
            process_name = self.uncategorized_listbox.get(selected_index)
            current_category = database.get_category_for_process(process_name)
            if current_category != 'Other' or process_name in self.uncategorized_listbox.get(0, tk.END): 
                 self.category_combobox.set(current_category)

    def _on_categorized_select(self, event):
        selected_item = self.categorized_tree.selection()
        if selected_item:
            item_values = self.categorized_tree.item(selected_item, 'values')
            process_name = item_values[0]
            category = item_values[1]
            self.category_combobox.set(category) 

    def _assign_category(self):
        selected_uncategorized_index = self.uncategorized_listbox.curselection()
        selected_categorized_item = self.categorized_tree.selection()
        selected_category = self.category_combobox.get()

        if not selected_category:
            messagebox.showwarning("Uyarı", "Lütfen atanacak bir kategori seçin veya yeni bir kategori oluşturun.", parent=self)
            return

        process_name_to_assign = None
        if selected_uncategorized_index:
            process_name_to_assign = self.uncategorized_listbox.get(selected_uncategorized_index)
        elif selected_categorized_item:
            item_values = self.categorized_tree.item(selected_categorized_item, 'values')
            process_name_to_assign = item_values[0]
        
        if process_name_to_assign:
            database.update_app_category(process_name_to_assign, selected_category)
            messagebox.showinfo("Başarılı", f"'{process_name_to_assign}' uygulamasına '{selected_category}' kategorisi atandı.", parent=self)
            self._load_data() 
        else:
            messagebox.showwarning("Uyarı", "Lütfen kategorize edilecek bir uygulama seçin.", parent=self)

    def _add_new_category(self):
        new_category = simpledialog.askstring("Yeni Kategori", "Lütfen yeni kategori adını girin:", parent=self) 
        if new_category and new_category.strip():
            new_category_clean = new_category.strip()
            current_categories = list(self.category_combobox['values'])
            if new_category_clean not in current_categories:
                current_categories.append(new_category_clean)
                self.category_combobox['values'] = sorted(current_categories)
                self.category_combobox.set(new_category_clean)
                messagebox.showinfo("Bilgi", f"'{new_category_clean}' yeni kategori olarak eklendi. Şimdi bir uygulamaya atayabilirsiniz.", parent=self)
            else:
                messagebox.showwarning("Uyarı", "Bu kategori zaten mevcut.", parent=self)
        else:
            messagebox.showwarning("Uyarı", "Kategori adı boş olamaz.", parent=self)

    def _delete_selected_category(self):
        selected_category = self.category_combobox.get()
        if not selected_category:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz bir kategori seçin.", parent=self)
            return

        if selected_category == 'Other':
            messagebox.showerror("Hata", "'Other' varsayılan bir kategoridir ve silinemez.", parent=self)
            return

        response = messagebox.askyesno("Kategori Sil", 
                                       f"'{selected_category}' kategorisini silmek istediğinizden emin misiniz?\n"
                                       "Bu kategoriye atanmış tüm uygulamalar 'Other' kategorisine taşınacaktır. "
                                       "Bu işlem geri alınamaz.", parent=self)
        if response:
            try:
                apps_in_category = []
                with database.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT process_name FROM app_categories WHERE category = ?", (selected_category,))
                    apps_in_category = [row[0] for row in cursor.fetchall()]
                
                for app_name in apps_in_category:
                    database.update_app_category(app_name, 'Other') 

                current_categories = list(self.category_combobox['values'])
                if selected_category in current_categories:
                    current_categories.remove(selected_category)
                    self.category_combobox['values'] = sorted(current_categories)
                    if current_categories:
                        if self.category_combobox.get() == selected_category:
                            self.category_combobox.set(current_categories[0] if current_categories else '')
                    else:
                        self.category_combobox.set('')

                messagebox.showinfo("Başarılı", f"'{selected_category}' kategorisi silindi ve ilgili uygulamalar 'Other' kategorisine taşındı.", parent=self)
                self._load_data() 

            except Exception as e:
                logging.error(f"Kategori silinirken hata: {e}", exc_info=True)
                messagebox.showerror("Hata", f"Kategori silinirken bir hata oluştu: {e}", parent=self)

class NotificationHistoryWindow(BaseWindow): 
    def __init__(self, master=None, app_instance=None):
        super().__init__(master, "Kognita - Bildirim Geçmişi", "750x550") 
        self.resizable(False, False)
        self.app_instance = app_instance

        self._create_widgets()
        self._load_notifications()
        self.add_footer_close_button()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_widgets(self):
        content_frame = ttk.Frame(self.main_frame) 
        content_frame.pack(fill=tk.BOTH, expand=True)

        top_controls_frame = ttk.Frame(content_frame, padding="5") 
        top_controls_frame.pack(fill=tk.X)

        ttk.Button(top_controls_frame, text="Tümünü Okundu İşaretle", command=self._mark_all_as_read).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_controls_frame, text="Okunmuşları Sil", command=self._delete_read_notifications, 
                   style='Danger.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_controls_frame, text="Seçiliyi Sil", command=self._delete_selected_notification).pack(side=tk.RIGHT, padx=5)
        

        self.notification_tree = ttk.Treeview(content_frame, columns=("timestamp", "title", "message", "type"), show="headings")
        self.notification_tree.heading("timestamp", text="Zaman")
        self.notification_tree.heading("title", text="Başlık")
        self.notification_tree.heading("message", text="Mesaj")
        self.notification_tree.heading("type", text="Tip")

        self.notification_tree.column("timestamp", width=150, anchor="w")
        self.notification_tree.column("title", width=150, anchor="w")
        self.notification_tree.column("message", width=300, anchor="w")
        self.notification_tree.column("type", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.notification_tree.yview)
        self.notification_tree.configure(yscrollcommand=scrollbar.set)

        self.notification_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.notification_tree.bind("<Double-1>", self._on_double_click) 

    def _load_notifications(self):
        for item in self.notification_tree.get_children():
            self.notification_tree.delete(item)
        
        notifications = database.get_all_notifications()
        for notif in notifications:
            timestamp_str = datetime.datetime.fromtimestamp(notif['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            tag = "read" if notif['is_read'] else "unread"
            
            self.notification_tree.insert("", "end", iid=notif['id'], values=(timestamp_str, notif['title'], notif['message'], notif['type']), tags=(tag,))
        
        self.notification_tree.tag_configure("unread", font=(STYLE_CONFIG["font_normal"][0], 9, 'bold'), background='#E0F2F7', foreground='black') 
        self.notification_tree.tag_configure("read", font=STYLE_CONFIG["font_normal"], foreground='gray', background=STYLE_CONFIG["bg_color"]) 

    def _on_double_click(self, event):
        item_id = self.notification_tree.focus()
        if item_id:
            item_data = self.notification_tree.item(item_id, 'values')
            notification_id = item_id 

            title = item_data[1]
            message = item_data[2]
            timestamp_str = item_data[0]

            messagebox.showinfo(f"Bildirim Detayı: {title}", f"Zaman: {timestamp_str}\n\n{message}", parent=self) 
            
            database.mark_notification_as_read(notification_id)
            self._load_notifications()
            if self.app_instance:
                self.app_instance.update_tray_icon() 

    def _mark_all_as_read(self):
        response = messagebox.askyesno("Tümünü Okundu İşaretle", "Tüm bildirimleri okundu olarak işaretlemek istediğinizden emin misiniz?", parent=self) 
        if response:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
                conn.commit()
            self._load_notifications()
            if self.app_instance:
                self.app_instance.update_tray_icon() 
            messagebox.showinfo("Başarılı", "Tüm bildirimler okundu olarak işaretlendi.", parent=self) 

    def _delete_selected_notification(self):
        selected_item = self.notification_tree.focus()
        if not selected_item:
            messagebox.showwarning("Seçim Yok", "Lütfen silmek istediğiniz bir bildirim seçin.", parent=self)
            return
        
        notification_id = selected_item
        if messagebox.askyesno("Bildirim Sil", "Bu bildirimi silmek istediğinizden emin misiniz?", parent=self): 
            database.delete_notification(notification_id)
            self._load_notifications()
            if self.app_instance:
                self.app_instance.update_tray_icon()
            messagebox.showinfo("Başarılı", "Bildirim başarıyla silindi.", parent=self)
            
    def _delete_read_notifications(self):
        response = messagebox.askyesno("Okunmuş Bildirimleri Sil", "Tüm okunmuş bildirimleri silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.", parent=self) 
        if response:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notifications WHERE is_read = 1")
                conn.commit()
            self._load_notifications()
            if self.app_instance:
                self.app_instance.update_tray_icon()
            messagebox.showinfo("Başarılı", "Tüm okunmuş bildirimler silindi.", parent=self) 

    def _on_closing(self):
        if self.app_instance:
            self.app_instance.update_tray_icon() 
        self.destroy()

class AchievementWindow(BaseWindow): 
    def __init__(self, master=None):
        super().__init__(master, "Kognita - Başarımlar", "650x450")
        self.resizable(False, False)
        self._create_widgets()
        self._load_achievements()
        self.add_footer_close_button()


    def _create_widgets(self):
        content_frame = ttk.Frame(self.main_frame) 
        content_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content_frame, text="Kazanılmış Başarımlarınız", font=STYLE_CONFIG["font_title"]).pack(pady=10)

        self.achievement_tree = ttk.Treeview(content_frame, columns=("name", "description", "unlocked_at"), show="headings")
        self.achievement_tree.heading("name", text="Başarım Adı")
        self.achievement_tree.heading("description", text="Açıklama")
        self.achievement_tree.heading("unlocked_at", text="Kazanılma Tarihi")

        self.achievement_tree.column("name", width=150, anchor="w")
        self.achievement_tree.column("description", width=300, anchor="w")
        self.achievement_tree.column("unlocked_at", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.achievement_tree.yview)
        self.achievement_tree.configure(yscrollcommand=scrollbar.set)

        self.achievement_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_achievements(self):
        for item in self.achievement_tree.get_children():
            self.achievement_tree.delete(item)
        
        achievements = database.get_all_unlocked_achievements()
        for ach in achievements:
            unlocked_at_str = datetime.datetime.fromtimestamp(ach[3]).strftime('%Y-%m-%d %H:%M:%S')
            self.achievement_tree.insert("", "end", values=(ach[0], ach[1], unlocked_at_str))


class MainDashboardWindow(BaseWindow):
    """Ana kontrol paneli penceresi."""
    def __init__(self, master=None, app_instance=None):
        super().__init__(master, "Kognita - Ana Panel", "800x600")
        self.resizable(False, False)
        self.app_instance = app_instance

        self._create_widgets()
        self._load_dashboard_data()
        self.add_footer_close_button()

    def _create_widgets(self):
        # Ana içerik alanı
        main_content = ttk.Frame(self.main_frame)
        main_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Üst bilgi paneli
        info_frame = ttk.LabelFrame(main_content, text="Günlük Özet", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.daily_summary_label = ttk.Label(info_frame, text="Bugün toplam aktif süre: Hesaplanıyor...", 
                                             font=STYLE_CONFIG["font_bold"])
        self.daily_summary_label.pack(pady=5)

        # Hızlı eylemler
        actions_frame = ttk.LabelFrame(main_content, text="Hızlı Eylemler", padding=10)
        actions_frame.pack(fill=tk.X, pady=(0, 10))

        actions_grid = ttk.Frame(actions_frame)
        actions_grid.pack(fill=tk.X)

        ttk.Button(actions_grid, text="Raporu Göster", 
                  command=lambda: ReportWindow(master=self)).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(actions_grid, text="Hedefleri Yönet", 
                  command=lambda: GoalsWindow(master=self)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(actions_grid, text="Kategorileri Yönet", 
                  command=lambda: CategoryManagementWindow(master=self)).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ttk.Button(actions_grid, text="Odaklanma Başlat", 
                  command=self._start_focus_session,
                  style='Accent.TButton').grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(actions_grid, text="Bildirimler", 
                  command=lambda: NotificationHistoryWindow(master=self, app_instance=self.app_instance)).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(actions_grid, text="Ayarlar", 
                  command=lambda: SettingsWindow(master=self, app_instance=self.app_instance)).grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # Grid kolonlarını eşit genişlikte yap
        for i in range(3):
            actions_grid.grid_columnconfigure(i, weight=1)

        # Son aktiviteler
        recent_frame = ttk.LabelFrame(main_content, text="Son Aktiviteler", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True)

        self.recent_tree = ttk.Treeview(recent_frame, columns=("time", "app", "category", "duration"), show="headings")
        self.recent_tree.heading("time", text="Zaman")
        self.recent_tree.heading("app", text="Uygulama")
        self.recent_tree.heading("category", text="Kategori")
        self.recent_tree.heading("duration", text="Süre")

        self.recent_tree.column("time", width=120, anchor="w")
        self.recent_tree.column("app", width=200, anchor="w")
        self.recent_tree.column("category", width=100, anchor="w")
        self.recent_tree.column("duration", width=80, anchor="center")

        recent_scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scrollbar.set)

        self.recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _start_focus_session(self):
        if self.app_instance:
            self.app_instance.start_focus_session_flow()
        else:
            messagebox.showinfo("Bilgi", "Odaklanma oturumu başlatılamadı.", parent=self)

    def _load_dashboard_data(self):
        # Günlük özet yükle
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + datetime.timedelta(days=1)
        
        try:
            category_totals, total_duration = analyzer.get_analysis_data(today, tomorrow)
            formatted_duration = reporter.format_duration(total_duration)
            self.daily_summary_label.config(text=f"Bugün toplam aktif süre: {formatted_duration}")
        except:
            self.daily_summary_label.config(text="Bugün toplam aktif süre: Veri yok")

        # Son aktiviteleri yükle
        self._load_recent_activities()

    def _load_recent_activities(self):
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        try:
            recent_logs = database.get_recent_usage_logs(limit=20)
            for log in recent_logs:
                start_time = datetime.datetime.fromtimestamp(log['start_time'])
                time_str = start_time.strftime('%H:%M')
                app_name = log['process_name']
                category = database.get_category_for_process(app_name)
                duration = reporter.format_duration(log['duration_seconds'])
                
                self.recent_tree.insert("", "end", values=(time_str, app_name, category, duration))
        except Exception as e:
            logging.error(f"Son aktiviteler yüklenirken hata: {e}")
            self.recent_tree.insert("", "end", values=("--", "Veri yüklenemedi", "--", "--"))