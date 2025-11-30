 
# kognita/ui.py - Geliştirilmiş ve Optimize Edilmiş UI

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

# Matplotlib kontrolü
MATPLOTLIB_AVAILABLE = True
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Backend ayarla
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib kütüphanesi bulunamadı. Grafik özellikleri devre dışı.")

# Modern UI Konfigürasyonu
STYLE_CONFIG = {
    # Fontlar
    "font_family": "Segoe UI",
    "font_normal": ("Segoe UI", 10),
    "font_bold": ("Segoe UI", 10, "bold"),
    "font_title": ("Segoe UI Light", 18),
    "font_h2": ("Segoe UI Semibold", 14),
    "font_h3": ("Segoe UI", 12, "bold"),
    "font_small": ("Segoe UI", 9),

    # Modern Renk Paleti
    "bg_color": "#F8F9FA",              # Ana arka plan (açık gri-beyaz)
    "bg_secondary": "#FFFFFF",          # İkincil arka plan (beyaz)
    "bg_card": "#FFFFFF",               # Kart arka planları
    
    "text_primary": "#212529",          # Ana metin (koyu gri)
    "text_secondary": "#6C757D",        # İkincil metin (orta gri)
    "text_muted": "#ADB5BD",            # Soluk metin
    
    "accent_color": "#0066CC",          # Ana vurgu rengi (mavi)
    "accent_hover": "#0052A3",          # Hover durumu
    "accent_light": "#E7F1FF",          # Açık vurgu
    
    "success_color": "#28A745",         # Başarı rengi (yeşil)
    "warning_color": "#FFC107",         # Uyarı rengi (sarı)
    "danger_color": "#DC3545",          # Hata rengi (kırmızı)
    "info_color": "#17A2B8",            # Bilgi rengi (mavi-yeşil)
    
    "border_color": "#DEE2E6",          # Kenarlık rengi
    "shadow_color": "#00000010",        # Gölge rengi
    
    # Header özel renkler
    "header_bg": "#FFFFFF",
    "header_fg": "#212529",
    "header_border": "#DEE2E6",
    
    # Footer renkler
    "footer_bg": "#F8F9FA",
    "footer_border": "#DEE2E6",
    
    # Buton varsayılanları
    "button_default_bg": "#6C757D",
    "button_default_fg": "#FFFFFF",
}

def resource_path(relative_path):
    """PyInstaller ile paketlendiğinde varlık dosyalarına doğru yolu bulur."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, 'assets', relative_path)

def apply_global_styles():
    """Modern ve tutarlı ttk stillerini uygular."""
    style = ttk.Style()
    style.theme_use('clam')
    
    # Temel widget stilleri
    style.configure('TLabel', 
                   font=STYLE_CONFIG["font_normal"], 
                   background=STYLE_CONFIG["bg_color"],
                   foreground=STYLE_CONFIG["text_primary"])
    
    style.configure('TButton', 
                   font=STYLE_CONFIG["font_normal"],
                   background=STYLE_CONFIG["button_default_bg"],
                   foreground=STYLE_CONFIG["button_default_fg"],
                   borderwidth=0,
                   focuscolor='none',
                   padding=(12, 8))
    style.map('TButton', 
             background=[('active', STYLE_CONFIG["accent_hover"]),
                        ('pressed', STYLE_CONFIG["accent_color"])])
    
    # Özel buton stilleri
    style.configure('Accent.TButton',
                   background=STYLE_CONFIG["accent_color"],
                   foreground='white',
                   font=STYLE_CONFIG["font_bold"])
    style.map('Accent.TButton',
             background=[('active', STYLE_CONFIG["accent_hover"]),
                        ('pressed', STYLE_CONFIG["accent_color"])])
    
    style.configure('Success.TButton',
                   background=STYLE_CONFIG["success_color"],
                   foreground='white')
    style.map('Success.TButton',
             background=[('active', '#218838')])
    
    style.configure('Danger.TButton',
                   background=STYLE_CONFIG["danger_color"],
                   foreground='white')
    style.map('Danger.TButton',
             background=[('active', '#C82333')])
    
    # Frame stilleri
    style.configure('TFrame', 
                   background=STYLE_CONFIG["bg_color"],
                   relief='flat')
    
    style.configure('Card.TFrame',
                   background=STYLE_CONFIG["bg_card"],
                   relief='solid',
                   borderwidth=1)
    
    # Entry ve Combobox
    style.configure('TEntry',
                   fieldbackground=STYLE_CONFIG["bg_secondary"],
                   borderwidth=1,
                   relief='solid',
                   padding=8)
    
    style.configure('TCombobox',
                   fieldbackground=STYLE_CONFIG["bg_secondary"],
                   borderwidth=1,
                   relief='solid',
                   padding=8)
    
    # Treeview
    style.configure('Treeview',
                   background=STYLE_CONFIG["bg_secondary"],
                   fieldbackground=STYLE_CONFIG["bg_secondary"],
                   foreground=STYLE_CONFIG["text_primary"],
                   rowheight=28,
                   borderwidth=1,
                   relief='solid')
    style.configure('Treeview.Heading',
                   background=STYLE_CONFIG["bg_color"],
                   foreground=STYLE_CONFIG["text_primary"],
                   font=STYLE_CONFIG["font_bold"],
                   relief='flat',
                   borderwidth=1)
    style.map('Treeview',
             background=[('selected', STYLE_CONFIG["accent_color"])],
             foreground=[('selected', 'white')])
    
    # Notebook
    style.configure('TNotebook',
                   background=STYLE_CONFIG["bg_color"],
                   borderwidth=0)
    style.configure('TNotebook.Tab',
                   background=STYLE_CONFIG["bg_color"],
                   foreground=STYLE_CONFIG["text_secondary"],
                   padding=[12, 8],
                   font=STYLE_CONFIG["font_normal"])
    style.map('TNotebook.Tab',
             background=[('selected', STYLE_CONFIG["accent_color"]),
                        ('active', STYLE_CONFIG["accent_light"])],
             foreground=[('selected', 'white'),
                        ('active', STYLE_CONFIG["accent_color"])])
    
    # LabelFrame
    style.configure('TLabelframe',
                   background=STYLE_CONFIG["bg_color"],
                   borderwidth=1,
                   relief='solid',
                   bordercolor=STYLE_CONFIG["border_color"])
    style.configure('TLabelframe.Label',
                   background=STYLE_CONFIG["bg_color"],
                   foreground=STYLE_CONFIG["text_primary"],
                   font=STYLE_CONFIG["font_bold"])

class BaseWindow(tk.Toplevel):
    """Modern ve tutarlı pencere tasarımı için temel sınıf."""
    
    def __init__(self, master, title, geometry, resizable=False):
        super().__init__(master)
        self.title(title)
        self.geometry(geometry)
        self.resizable(resizable, resizable)
        self.configure(bg=STYLE_CONFIG["bg_color"])
        
        # Modern görünüm için başlık çubuğunu kaldır
        self.overrideredirect(True)
        
        # Pencereyi ortala
        self.update_idletasks()
        self.center_window()
        
        # Sürükleme değişkenleri
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # Modern pencere yapısı
        self._create_window_structure(title)
        
        # Gölge efekti (Windows 10+ için)
        try:
            self.attributes('-topmost', False)
            self.lift()
        except:
            pass

    def _create_window_structure(self, title):
        """Modern pencere yapısını oluşturur."""
        # Ana container
        self.main_container = ttk.Frame(self, style='TFrame')
        self.main_container.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Header (başlık çubuğu)
        self.header_frame = ttk.Frame(self.main_container, style='TFrame', height=50)
        self.header_frame.pack(fill='x', side='top')
        self.header_frame.pack_propagate(False)
        self.header_frame.configure(style='Header.TFrame')
        
        # Header stillendirme
        style = ttk.Style()
        style.configure('Header.TFrame',
                       background=STYLE_CONFIG["header_bg"],
                       relief='flat')
        
        # İçerik alanı
        self.content_frame = ttk.Frame(self.main_container, style='TFrame')
        self.content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Footer
        self.footer_frame = ttk.Frame(self.main_container, style='TFrame', height=60)
        self.footer_frame.pack(fill='x', side='bottom')
        self.footer_frame.pack_propagate(False)
        
        # Header içeriği
        self._populate_header(title)
        
        # Sürükleme olayları
        self.header_frame.bind("<ButtonPress-1>", self.start_drag)
        self.header_frame.bind("<B1-Motion>", self.do_drag)

    def _populate_header(self, title):
        """Modern header tasarımı."""
        # Sol taraf - Logo ve başlık
        left_frame = ttk.Frame(self.header_frame, style='Header.TFrame')
        left_frame.pack(side='left', fill='y', expand=True)
        
        # Logo (32x32 PNG gerekli - assets/logo.png)
        try:
            logo_image = Image.open(resource_path("logo.png")).resize((28, 28), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = Label(left_frame, image=self.logo_photo, 
                              bg=STYLE_CONFIG["header_bg"], bd=0)
            logo_label.pack(side='left', padx=(15, 8), pady=11)
            
            # Logo sürükleme
            logo_label.bind("<ButtonPress-1>", self.start_drag)
            logo_label.bind("<B1-Motion>", self.do_drag)
        except Exception as e:
            logging.warning(f"Logo yüklenemedi: {e}")
        
        # Başlık
        title_label = Label(left_frame, text=title, 
                           font=STYLE_CONFIG["font_title"],
                           bg=STYLE_CONFIG["header_bg"], 
                           fg=STYLE_CONFIG["header_fg"],
                           bd=0)
        title_label.pack(side='left', pady=11)
        title_label.bind("<ButtonPress-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.do_drag)
        
        # Sağ taraf - Kontroller
        right_frame = ttk.Frame(self.header_frame, style='Header.TFrame')
        right_frame.pack(side='right', fill='y')
        
        # Minimize butonu (opsiyonel)
        self.minimize_btn = self._create_header_button(right_frame, "─", self.minimize_window)
        self.minimize_btn.pack(side='right', padx=2, pady=8)
        
        # Kapat butonu
        self.close_btn = self._create_header_button(right_frame, "✕", self.destroy, danger=True)
        self.close_btn.pack(side='right', padx=(2, 12), pady=8)

    def _create_header_button(self, parent, text, command, danger=False):
        """Header için özel buton."""
        if danger:
            bg_color = STYLE_CONFIG["header_bg"]
            hover_color = STYLE_CONFIG["danger_color"]
            fg_color = STYLE_CONFIG["text_secondary"]
        else:
            bg_color = STYLE_CONFIG["header_bg"]
            hover_color = STYLE_CONFIG["accent_light"]
            fg_color = STYLE_CONFIG["text_secondary"]
            
        btn = Button(parent, text=text, command=command,
                    bg=bg_color, fg=fg_color,
                    font=("Segoe UI", 9), bd=0, relief='flat',
                    width=3, height=1,
                    activebackground=hover_color,
                    activeforeground='white' if danger else STYLE_CONFIG["accent_color"])
        
        # Hover efektleri
        def on_enter(e):
            btn.configure(bg=hover_color, 
                         fg='white' if danger else STYLE_CONFIG["accent_color"])
        
        def on_leave(e):
            btn.configure(bg=bg_color, fg=fg_color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def minimize_window(self):
        """Pencereyi simge durumuna küçült."""
        self.iconify()

    def start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_start_x
        y = self.winfo_y() + event.y - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def center_window(self):
        """Pencereyi ekranın ortasına yerleştirir."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f'{width}x{height}+{x}+{y}')

    def add_action_buttons(self, buttons_config):
        """Footer'a eylem butonları ekler."""
        for btn_config in buttons_config:
            btn = ttk.Button(self.footer_frame, 
                           text=btn_config.get('text', 'Button'),
                           command=btn_config.get('command', lambda: None),
                           style=btn_config.get('style', 'TButton'))
            btn.pack(side='right', padx=8, pady=15)

class WelcomeWindow(BaseWindow):
    """Hoş geldin penceresi - modern tasarım."""
    
    def __init__(self, master, on_close_callback):
        super().__init__(master, "Kognita'ya Hoş Geldiniz", "520x400")
        self.master = master
        self.on_close_callback = on_close_callback
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self._create_welcome_content()
        self.lift()
        self.attributes('-topmost', True)
        self.focus_force()

    def _create_welcome_content(self):
        """Hoş geldin içeriği."""
        # Ana içerik alanı
        content = ttk.Frame(self.content_frame, style='Card.TFrame')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Üst alan - Logo ve başlık
        top_frame = ttk.Frame(content, style='TFrame')
        top_frame.pack(fill='x', pady=(30, 20))
        
        # Büyük logo (64x64 PNG gerekli - assets/welcome_logo.png)
        try:
            welcome_logo = Image.open(resource_path("welcome_logo.png")).resize((64, 64), Image.Resampling.LANCZOS)
            self.welcome_logo_photo = ImageTk.PhotoImage(welcome_logo)
            logo_label = Label(top_frame, image=self.welcome_logo_photo, 
                              bg=STYLE_CONFIG["bg_card"], bd=0)
            logo_label.pack(pady=(0, 15))
        except Exception as e:
            logging.warning(f"Welcome logo yüklenemedi: {e}")
        
        # Ana başlık
        title_label = Label(content, text="Kognita'ya Hoş Geldiniz!",
                           font=("Segoe UI Light", 24, "bold"),
                           bg=STYLE_CONFIG["bg_card"],
                           fg=STYLE_CONFIG["accent_color"])
        title_label.pack(pady=(0, 10))
        
        # Alt başlık
        subtitle_label = Label(content, 
                              text="Dijital Yaşamınızı Optimize Edin",
                              font=STYLE_CONFIG["font_h2"],
                              bg=STYLE_CONFIG["bg_card"],
                              fg=STYLE_CONFIG["text_secondary"])
        subtitle_label.pack(pady=(0, 20))
        
        # Açıklama metni
        desc_text = """Kognita, bilgisayar kullanım alışkanlıklarınızı akıllıca analiz eder ve size kişiselleştirilmiş öneriler sunar.

• Detaylı kullanım raporları
• Akıllı hedef belirleme sistemi  
• Odaklanma modu ve bildirimler
• Kategori bazlı analiz ve takip"""
        
        desc_label = Label(content, text=desc_text,
                          font=STYLE_CONFIG["font_normal"],
                          bg=STYLE_CONFIG["bg_card"],
                          fg=STYLE_CONFIG["text_primary"],
                          justify='left')
        desc_label.pack(pady=(0, 30), padx=30)
        
        # Başlat butonu
        start_btn = ttk.Button(content, text="Kognita'yı Başlat",
                              command=self._on_closing,
                              style='Accent.TButton')
        start_btn.pack(pady=20)

    def _on_closing(self):
        self.grab_release()
        self.on_close_callback()
        self.destroy()

class ReportWindow(BaseWindow):
    """Geliştirilmiş rapor penceresi."""
    
    def __init__(self, master=None):
        super().__init__(master, "Kognita - Analiz ve Raporlar", "1000x750", resizable=True)
        self.current_report_range = "today"
        
        self._create_report_interface()
        self._load_report_data()
        
        # Footer butonları
        self.add_action_buttons([
            {'text': 'Kapat', 'command': self.destroy, 'style': 'TButton'}
        ])

    def _create_report_interface(self):
        """Modern rapor arayüzü."""
        # Üst kontrol paneli
        control_panel = ttk.Frame(self.content_frame, style='Card.TFrame')
        control_panel.pack(fill='x', pady=(0, 15))
        
        # İç padding
        control_inner = ttk.Frame(control_panel, style='TFrame')
        control_inner.pack(fill='x', padx=20, pady=15)
        
        # Sol taraf - Rapor aralığı
        left_controls = ttk.Frame(control_inner, style='TFrame')
        left_controls.pack(side='left', fill='x', expand=True)
        
        ttk.Label(left_controls, text="Rapor Aralığı:",
                 font=STYLE_CONFIG["font_bold"]).pack(side='left', padx=(0, 8))
        
        self.range_var = StringVar(self)
        range_options = [
            ("Bugün", "today"),
            ("Son 7 Gün", "last_7_days"), 
            ("Bu Hafta", "this_week"),
            ("Bu Ay", "this_month"),
            ("Tüm Zamanlar", "all_time")
        ]
        
        self.range_combobox = ttk.Combobox(left_controls, textvariable=self.range_var,
                                          values=[opt[0] for opt in range_options],
                                          state="readonly", width=15)
        self.range_combobox.set("Bugün")
        self.range_combobox.pack(side='left', padx=(0, 15))
        self.range_combobox.bind("<<ComboboxSelected>>", self._on_range_change)
        
        self.range_mapping = dict(range_options)
        self.reverse_range_mapping = {v: k for k, v in range_options}
        
        # Sağ taraf - Dışa aktarma butonları
        right_controls = ttk.Frame(control_inner, style='TFrame')
        right_controls.pack(side='right')
        
        ttk.Button(right_controls, text="CSV Dışa Aktar",
                  command=self._export_data).pack(side='right', padx=5)
        
        if MATPLOTLIB_AVAILABLE:
            ttk.Button(right_controls, text="PDF Rapor",
                      command=self._export_pdf_report,
                      style='Accent.TButton').pack(side='right', padx=5)
        
        # Özet bilgi paneli
        self.summary_frame = ttk.LabelFrame(self.content_frame, text="Özet Bilgiler", 
                                           style='TLabelframe')
        self.summary_frame.pack(fill='x', pady=(0, 15))
        
        summary_inner = ttk.Frame(self.summary_frame, style='TFrame')
        summary_inner.pack(fill='x', padx=15, pady=10)
        
        self.persona_label = ttk.Label(summary_inner, text="Kullanıcı profili hesaplanıyor...",
                                      font=STYLE_CONFIG["font_bold"],
                                      foreground=STYLE_CONFIG["accent_color"])
        self.persona_label.pack(anchor='w', pady=(0, 5))
        
        self.total_duration_label = ttk.Label(summary_inner, text="Toplam süre hesaplanıyor...",
                                             font=STYLE_CONFIG["font_normal"])
        self.total_duration_label.pack(anchor='w')
        
        # Ana içerik alanı - Notebook
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(expand=True, fill='both')
        
        # Sekmeler
        self._create_category_tab()
        
        if MATPLOTLIB_AVAILABLE:
            self._create_charts_tab()
            self._create_analysis_tab()
            self._create_trends_tab()
            self._create_suggestions_tab()

    def _create_category_tab(self):
        """Kategori detayları sekmesi."""
        self.category_tab = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.category_tab, text="📊 Kategori Detayları")
        
        # Treeview container
        tree_frame = ttk.Frame(self.category_tab, style='TFrame')
        tree_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Modern treeview
        self.category_tree = ttk.Treeview(tree_frame, 
                                         columns=("category", "duration", "percentage", "sessions"),
                                         show="headings", height=15)
        
        # Sütun başlıkları ve genişlikleri
        self.category_tree.heading("category", text="Kategori")
        self.category_tree.heading("duration", text="Toplam Süre")  
        self.category_tree.heading("percentage", text="Yüzde")
        self.category_tree.heading("sessions", text="Oturum Sayısı")
        
        self.category_tree.column("category", width=200, anchor="w")
        self.category_tree.column("duration", width=120, anchor="center")
        self.category_tree.column("percentage", width=80, anchor="center")
        self.category_tree.column("sessions", width=100, anchor="center")
        
        # Scrollbar
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", 
                                      command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.category_tree.pack(side='left', fill='both', expand=True)
        tree_scrollbar.pack(side='right', fill='y')

    def _create_charts_tab(self):
        """Grafikler sekmesi."""
        self.charts_tab = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.charts_tab, text="📈 Grafikler")
        
        # Grafik container'ı
        chart_container = ttk.Frame(self.charts_tab, style='TFrame')
        chart_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Grafik notebook
        self.chart_notebook = ttk.Notebook(chart_container)
        self.chart_notebook.pack(fill='both', expand=True)
        
        # Alt sekmeler
        self.pie_chart_frame = ttk.Frame(self.chart_notebook, style='TFrame')
        self.chart_notebook.add(self.pie_chart_frame, text="Pasta Grafik")
        
        self.bar_chart_frame = ttk.Frame(self.chart_notebook, style='TFrame')
        self.chart_notebook.add(self.bar_chart_frame, text="Sütun Grafik")
        
        self.hourly_chart_frame = ttk.Frame(self.chart_notebook, style='TFrame')
        self.chart_notebook.add(self.hourly_chart_frame, text="Saatlik Aktivite")
        
        # Grafik canvas'ları için placeholder'lar
        self.pie_chart_canvas = None
        self.bar_chart_canvas = None  
        self.hourly_chart_canvas = None

    def _create_analysis_tab(self):
        """Analiz sekmesi."""
        self.analysis_tab = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.analysis_tab, text="🔍 Detaylı Analiz")
        
        # İçerik alanı
        analysis_content = ttk.Frame(self.analysis_tab, style='TFrame')
        analysis_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Günlük ortalamalar
        avg_frame = ttk.LabelFrame(analysis_content, text="Son 7 Günlük Ortalamalar",
                                  style='TLabelframe')
        avg_frame.pack(fill='x', pady=(0, 15))
        
        self.avg_tree = ttk.Treeview(avg_frame, columns=("category", "avg_duration"),
                                    show="headings", height=6)
        self.avg_tree.heading("category", text="Kategori")
        self.avg_tree.heading("avg_duration", text="Günlük Ortalama")
        self.avg_tree.column("category", width=200)
        self.avg_tree.column("avg_duration", width=150)
        self.avg_tree.pack(fill='x', padx=10, pady=10)
        
        # En verimli gün
        productive_frame = ttk.LabelFrame(analysis_content, text="Verimlilik Analizi",
                                         style='TLabelframe')
        productive_frame.pack(fill='x')
        
        self.productive_label = ttk.Label(productive_frame, text="Analiz ediliyor...",
                                         font=STYLE_CONFIG["font_normal"])
        self.productive_label.pack(padx=15, pady=15)

    def _create_trends_tab(self):
        """Trendler sekmesi."""
        self.trends_tab = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.trends_tab, text="📉 Uygulama Trendleri")
        
        # Kontrol paneli
        trend_control = ttk.Frame(self.trends_tab, style='TFrame')
        trend_control.pack(fill='x', padx=15, pady=15)
        
        ttk.Label(trend_control, text="Uygulama Seçin:",
                 font=STYLE_CONFIG["font_bold"]).pack(side='left', padx=(0, 10))
        
        self.trend_app_var = StringVar()
        self.trend_app_combo = ttk.Combobox(trend_control, textvariable=self.trend_app_var,
                                           state="readonly", width=30)
        self.trend_app_combo.pack(side='left', padx=(0, 10))
        self.trend_app_combo.bind("<<ComboboxSelected>>", self._load_app_trend)
        
        # Grafik alanı
        self.trend_chart_frame = ttk.Frame(self.trends_tab, style='TFrame')
        self.trend_chart_frame.pack(fill='both', expand=True, padx=15)
        
        self.trend_chart_canvas = None

    def _create_suggestions_tab(self):
        """Öneriler sekmesi."""
        self.suggestions_tab = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(self.suggestions_tab, text="💡 Kişisel Öneriler")
        
        # İçerik alanı
        suggestions_content = ttk.Frame(self.suggestions_tab, style='TFrame')
        suggestions_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Başlık
        title_label = ttk.Label(suggestions_content, 
                               text="Size Özel Öneriler",
                               font=STYLE_CONFIG["font_h2"])
        title_label.pack(pady=(0, 15))
        
        # Öneriler text widget
        suggestions_frame = ttk.Frame(suggestions_content, style='Card.TFrame')
        suggestions_frame.pack(fill='both', expand=True)
        
        self.suggestions_text = tk.Text(suggestions_frame, wrap=tk.WORD, 
                                       font=STYLE_CONFIG["font_normal"],
                                       bg=STYLE_CONFIG["bg_card"],
                                       fg=STYLE_CONFIG["text_primary"],
                                       relief='flat', bd=0,
                                       padx=20, pady=20)
        self.suggestions_text.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Scrollbar
        suggestions_scroll = ttk.Scrollbar(suggestions_frame, orient="vertical",
                                          command=self.suggestions_text.yview)
        self.suggestions_text.configure(yscrollcommand=suggestions_scroll.set)
        suggestions_scroll.pack(side='right', fill='y')

    def _on_range_change(self, event=None):
        """Rapor aralığı değiştiğinde."""
        selected_display = self.range_combobox.get()
        self.current_report_range = self.range_mapping.get(selected_display, "today")
        self._load_report_data()

    def _get_date_range(self, selection):
        """Seçime göre tarih aralığını döndürür."""
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

        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_date, end_date

    def _load_report_data(self):
        """Rapor verilerini yükler."""
        try:
            start_date, end_date = self._get_date_range(self.current_report_range)
            category_totals, total_duration = analyzer.get_analysis_data(start_date, end_date)

            # Özet bilgileri güncelle
            persona_text, table_data = reporter.get_report_data(category_totals, total_duration)
            self.persona_label.config(text=persona_text)
            self.total_duration_label.config(text=f"Toplam Aktif Süre: {reporter.format_duration(total_duration)}")

            # Kategori tablosunu güncelle
            self._update_category_table(table_data, category_totals)

            # Grafikleri güncelle
            if MATPLOTLIB_AVAILABLE:
                self._update_charts(category_totals, total_duration)
                self._update_analysis_data()
                self._update_trends_data()
                self._update_suggestions(category_totals, total_duration)

        except Exception as e:
            logging.error(f"Rapor verileri yüklenirken hata: {e}")
            messagebox.showerror("Hata", f"Veriler yüklenirken bir hata oluştu: {e}", parent=self)

    def _update_category_table(self, table_data, category_totals):
        """Kategori tablosunu günceller."""
        # Mevcut verileri temizle
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)

        if table_data:
            for i, row in enumerate(table_data):
                # Oturum sayısını hesapla (basit yaklaşım)
                category_name = row[0]
                sessions = len(database.get_sessions_for_category(category_name)) if hasattr(database, 'get_sessions_for_category') else "-"
                
                # Satırı ekle
                self.category_tree.insert("", "end", values=(row[0], row[1], row[2], sessions))
                
                # Renklendirme (alternatif satırlar)
                if i % 2 == 0:
                    self.category_tree.set(self.category_tree.get_children()[-1], "category", row[0])
        else:
            self.category_tree.insert("", "end", values=("Veri Yok", "", "", ""))

    def _update_charts(self, category_totals, total_duration):
        """Grafikleri günceller."""
        self._draw_pie_chart(category_totals, total_duration)
        self._draw_bar_chart(category_totals, total_duration)
        self._draw_hourly_chart()

    def _draw_pie_chart(self, category_totals, total_duration):
        """Pasta grafiği çizer."""
        if self.pie_chart_canvas:
            self.pie_chart_canvas.get_tk_widget().destroy()
            self.pie_chart_canvas = None

        labels, sizes = reporter.get_chart_data(category_totals, total_duration)

        if not labels or not sizes:
            no_data_label = ttk.Label(self.pie_chart_frame, 
                                     text="Bu aralık için yeterli veri bulunmuyor.",
                                     font=STYLE_CONFIG["font_normal"])
            no_data_label.pack(expand=True)
            return

        # Modern grafik stili
        fig = Figure(figsize=(8, 6), dpi=100, facecolor=STYLE_CONFIG["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(STYLE_CONFIG["bg_card"])

        # Modern renkler
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                         colors=colors[:len(labels)], startangle=90,
                                         textprops={'fontsize': 10, 'color': STYLE_CONFIG["text_primary"]})

        # Başlık
        ax.set_title('Kategori Dağılımı', fontsize=14, fontweight='bold', 
                    color=STYLE_CONFIG["text_primary"], pad=20)

        # Yüzde metinlerini beyaz yap
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        fig.tight_layout()

        self.pie_chart_canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_frame)
        self.pie_chart_canvas.draw()
        self.pie_chart_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _draw_bar_chart(self, category_totals, total_duration):
        """Sütun grafiği çizer."""
        if self.bar_chart_canvas:
            self.bar_chart_canvas.get_tk_widget().destroy()
            self.bar_chart_canvas = None

        if not category_totals:
            no_data_label = ttk.Label(self.bar_chart_frame,
                                     text="Bu aralık için yeterli veri bulunmuyor.",
                                     font=STYLE_CONFIG["font_normal"])
            no_data_label.pack(expand=True)
            return

        # Verileri hazırla
        categories = list(category_totals.keys())[:8]  # İlk 8 kategori
        durations = [category_totals[cat] / 60 for cat in categories]  # Dakikaya çevir

        fig = Figure(figsize=(10, 6), dpi=100, facecolor=STYLE_CONFIG["bg_card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(STYLE_CONFIG["bg_card"])

        # Modern sütun grafiği
        bars = ax.bar(categories, durations, color=STYLE_CONFIG["accent_color"], alpha=0.8)

        # Stil düzenlemeleri
        ax.set_xlabel('Kategoriler', fontsize=12, color=STYLE_CONFIG["text_primary"])
        ax.set_ylabel('Süre (Dakika)', fontsize=12, color=STYLE_CONFIG["text_primary"])
        ax.set_title('Kategori Bazlı Kullanım Süreleri', fontsize=14, fontweight='bold',
                    color=STYLE_CONFIG["text_primary"], pad=20)

        # X ekseni etiketlerini döndür
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # Grid ekle
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)

        # Renkleri ayarla
        ax.tick_params(colors=STYLE_CONFIG["text_primary"])
        ax.spines['bottom'].set_color(STYLE_CONFIG["border_color"])
        ax.spines['left'].set_color(STYLE_CONFIG["border_color"])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        fig.tight_layout()

        self.bar_chart_canvas = FigureCanvasTkAgg(fig, master=self.bar_chart_frame)
        self.bar_chart_canvas.draw()
        self.bar_chart_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _draw_hourly_chart(self):
        """Saatlik aktivite grafiği çizer."""
        if self.hourly_chart_canvas:
            self.hourly_chart_canvas.get_tk_widget().destroy()
            self.hourly_chart_canvas = None

        try:
            hourly_data = analyzer.get_hourly_activity()
            
            if not hourly_data:
                no_data_label = ttk.Label(self.hourly_chart_frame,
                                         text="Saatlik aktivite için yeterli veri bulunmuyor.",
                                         font=STYLE_CONFIG["font_normal"])
                no_data_label.pack(expand=True)
                return

            hours = list(range(24))
            durations = [hourly_data.get(h, 0) / 60 for h in hours]  # Dakikaya çevir

            fig = Figure(figsize=(12, 6), dpi=100, facecolor=STYLE_CONFIG["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(STYLE_CONFIG["bg_card"])

            # Line chart
            ax.plot(hours, durations, color=STYLE_CONFIG["accent_color"], linewidth=2, marker='o', markersize=4)
            ax.fill_between(hours, durations, alpha=0.3, color=STYLE_CONFIG["accent_color"])

            ax.set_xlabel('Saat', fontsize=12, color=STYLE_CONFIG["text_primary"])
            ax.set_ylabel('Ortalama Süre (Dakika)', fontsize=12, color=STYLE_CONFIG["text_primary"])
            ax.set_title('Günlük Saatlik Aktivite Dağılımı', fontsize=14, fontweight='bold',
                        color=STYLE_CONFIG["text_primary"], pad=20)

            ax.set_xticks(range(0, 24, 2))
            ax.grid(True, alpha=0.3)
            ax.set_axisbelow(True)

            # Renkleri ayarla
            ax.tick_params(colors=STYLE_CONFIG["text_primary"])
            ax.spines['bottom'].set_color(STYLE_CONFIG["border_color"])
            ax.spines['left'].set_color(STYLE_CONFIG["border_color"])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            fig.tight_layout()

            self.hourly_chart_canvas = FigureCanvasTkAgg(fig, master=self.hourly_chart_frame)
            self.hourly_chart_canvas.draw()
            self.hourly_chart_canvas.get_tk_widget().pack(fill='both', expand=True)

        except Exception as e:
            logging.error(f"Saatlik grafik çizilirken hata: {e}")

    def _update_analysis_data(self):
        """Analiz sekmesi verilerini günceller."""
        try:
            # Günlük ortalamalar
            for item in self.avg_tree.get_children():
                self.avg_tree.delete(item)

            daily_avg_data = analyzer.get_daily_average_usage_by_category(num_days=7)
            if daily_avg_data:
                sorted_data = sorted(daily_avg_data.items(), key=lambda item: item[1], reverse=True)
                for category, duration in sorted_data[:10]:  # İlk 10 kategori
                    formatted_duration = reporter.format_duration(duration)
                    self.avg_tree.insert("", "end", values=(category, formatted_duration))
            else:
                self.avg_tree.insert("", "end", values=("Veri Yok", ""))

            # En verimli gün
            most_productive_day, max_time = analyzer.get_most_productive_day()
            if most_productive_day != "Yeterli Veri Yok":
                productive_text = f"En verimli gününüz: {most_productive_day}\nToplam verimli süre: {reporter.format_duration(max_time)}"
            else:
                productive_text = "En verimli gün analizi için yeterli veri bulunmuyor."
                
            self.productive_label.config(text=productive_text)

        except Exception as e:
            logging.error(f"Analiz verileri güncellenirken hata: {e}")

    def _update_trends_data(self):
        """Trendler sekmesi verilerini günceller."""
        try:
            # Uygulama listesini güncelle
            all_processes = sorted(database.get_all_processes())
            self.trend_app_combo['values'] = all_processes
            if all_processes and not self.trend_app_var.get():
                self.trend_app_combo.set(all_processes[0])
                self._load_app_trend()

        except Exception as e:
            logging.error(f"Trend verileri güncellenirken hata: {e}")

    def _load_app_trend(self, event=None):
        """Seçili uygulamanın trend grafiğini yükler."""
        if self.trend_chart_canvas:
            self.trend_chart_canvas.get_tk_widget().destroy()
            self.trend_chart_canvas = None

        selected_app = self.trend_app_var.get()
        if not selected_app:
            return

        try:
            # Son 30 günlük veriyi al
            trend_data = analyzer.get_app_usage_over_time(selected_app, num_days=30)
            
            if not trend_data:
                no_data_label = ttk.Label(self.trend_chart_frame,
                                         text=f"'{selected_app}' için trend verisi bulunmuyor.",
                                         font=STYLE_CONFIG["font_normal"])
                no_data_label.pack(expand=True)
                return

            # Tarihleri ve süreleri hazırla
            dates = []
            durations = []
            
            # Son 30 günü oluştur
            today = datetime.datetime.now()
            for i in range(29, -1, -1):
                date = today - datetime.timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                dates.append(date_str)
                durations.append(trend_data.get(date_str, 0) / 60)  # Dakikaya çevir

            fig = Figure(figsize=(12, 6), dpi=100, facecolor=STYLE_CONFIG["bg_card"])
            ax = fig.add_subplot(111)
            ax.set_facecolor(STYLE_CONFIG["bg_card"])

            # Trend çizgisi
            ax.plot(range(len(dates)), durations, color=STYLE_CONFIG["accent_color"], 
                   linewidth=2, marker='o', markersize=3)
            ax.fill_between(range(len(dates)), durations, alpha=0.3, color=STYLE_CONFIG["accent_color"])

            ax.set_xlabel('Tarih', fontsize=12, color=STYLE_CONFIG["text_primary"])
            ax.set_ylabel('Kullanım Süresi (Dakika)', fontsize=12, color=STYLE_CONFIG["text_primary"])
            ax.set_title(f"'{selected_app}' - 30 Günlük Kullanım Trendi", fontsize=14, fontweight='bold',
                        color=STYLE_CONFIG["text_primary"], pad=20)

            # X ekseni etiketleri (her 5 günde bir)
            ax.set_xticks(range(0, len(dates), 5))
            ax.set_xticklabels([dates[i].split('-')[1] + '/' + dates[i].split('-')[2] for i in range(0, len(dates), 5)])

            ax.grid(True, alpha=0.3)
            ax.set_axisbelow(True)

            # Renkleri ayarla
            ax.tick_params(colors=STYLE_CONFIG["text_primary"])
            ax.spines['bottom'].set_color(STYLE_CONFIG["border_color"])
            ax.spines['left'].set_color(STYLE_CONFIG["border_color"])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            fig.tight_layout()

            self.trend_chart_canvas = FigureCanvasTkAgg(fig, master=self.trend_chart_frame)
            self.trend_chart_canvas.draw()
            self.trend_chart_canvas.get_tk_widget().pack(fill='both', expand=True)

        except Exception as e:
            logging.error(f"Trend grafiği çizilirken hata: {e}")

    def _update_suggestions(self, category_totals, total_duration):
        """Öneriler sekmesini günceller."""
        try:
            self.suggestions_text.config(state=tk.NORMAL)
            self.suggestions_text.delete(1.0, tk.END)

            suggestions = analyzer.get_user_suggestions(category_totals, total_duration)
            
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    self.suggestions_text.insert(tk.END, f"{i}. {suggestion}\n\n")
            else:
                self.suggestions_text.insert(tk.END, "Henüz yeterli veri toplanmadığı için öneri oluşturulamıyor. Lütfen birkaç gün daha kullanım verisi biriktirin.")

            self.suggestions_text.config(state=tk.DISABLED)

        except Exception as e:
            logging.error(f"Öneriler güncellenirken hata: {e}")

    def _export_data(self):
        """Verileri CSV olarak dışa aktar."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV dosyaları", "*.csv"), ("Tüm dosyalar", "*.*")],
                title="Verileri CSV Olarak Kaydet"
            )
            
            if file_path:
                success, error = database.export_all_data_to_csv(file_path)
                if success:
                    messagebox.showinfo("Başarılı", f"Veriler '{file_path}' dosyasına kaydedildi.", parent=self)
                else:
                    messagebox.showerror("Hata", f"Dışa aktarma hatası: {error}", parent=self)
                    
        except Exception as e:
            logging.error(f"CSV dışa aktarma hatası: {e}")
            messagebox.showerror("Hata", f"Dışa aktarma sırasında hata oluştu: {e}", parent=self)

    def _export_pdf_report(self):
        """PDF rapor oluştur."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF dosyaları", "*.pdf"), ("Tüm dosyalar", "*.*")],
                title="PDF Rapor Kaydet"
            )
            
            if file_path:
                start_date, end_date = self._get_date_range(self.current_report_range)
                success, error = reporter.create_pdf_report(file_path, start_date, end_date)
                
                if success:
                    messagebox.showinfo("Başarılı", f"PDF raporu '{file_path}' dosyasına kaydedildi.", parent=self)
                else:
                    messagebox.showerror("Hata", f"PDF oluşturma hatası: {error}", parent=self)
                    
        except Exception as e:
            logging.error(f"PDF dışa aktarma hatası: {e}")
            messagebox.showerror("Hata", f"PDF oluşturma sırasında hata oluştu: {e}", parent=self)

class GoalsWindow(BaseWindow):
    """Hedef yönetimi penceresi."""
    
    def __init__(self, master=None):
        super().__init__(master, "Hedef Yönetimi", "750x600")
        self._create_goals_interface()
        self._load_goals()
        
        self.add_action_buttons([
            {'text': 'Kapat', 'command': self.destroy, 'style': 'TButton'}
        ])

    def _create_goals_interface(self):
        """Hedef yönetimi arayüzü."""
        # Yeni hedef ekleme paneli
        add_panel = ttk.LabelFrame(self.content_frame, text="Yeni Hedef Oluştur", 
                                  style='TLabelframe')
        add_panel.pack(fill='x', pady=(0, 20))
        
        add_content = ttk.Frame(add_panel, style='TFrame')
        add_content.pack(fill='x', padx=15, pady=15)
        
        # Grid düzeni
        add_content.grid_columnconfigure(1, weight=1)
        
        # Hedef tipi
        ttk.Label(add_content, text="Hedef Tipi:", 
                 font=STYLE_CONFIG["font_bold"]).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
        
        self.goal_type_var = StringVar(value="max_usage")
        goal_types = [
            ("Maksimum Kullanım", "max_usage"),
            ("Minimum Kullanım", "min_usage"), 
            ("Uygulama Engelleme", "block"),
            ("Zaman Aralığı Limiti", "time_window_max")
        ]
        
        self.goal_type_combo = ttk.Combobox(add_content, textvariable=self.goal_type_var,
                                           values=[gt[0] for gt in goal_types],
                                           state="readonly")
        self.goal_type_combo.grid(row=0, column=1, sticky='ew', pady=5)
        self.goal_type_combo.bind("<<ComboboxSelected>>", self._on_goal_type_change)
        
        self.goal_type_mapping = dict(goal_types)
        
        # Dinamik alanlar için frame
        self.dynamic_frame = ttk.Frame(add_content, style='TFrame')
        self.dynamic_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)
        
        # Ekle butonu
        ttk.Button(add_content, text="Hedef Ekle", command=self._add_goal,
                  style='Accent.TButton').grid(row=2, column=0, columnspan=2, pady=15)
        
        # İlk yükleme
        self._create_dynamic_fields()
        
        # Mevcut hedefler listesi
        goals_panel = ttk.LabelFrame(self.content_frame, text="Mevcut Hedefler",
                                    style='TLabelframe')
        goals_panel.pack(fill='both', expand=True)
        
        goals_content = ttk.Frame(goals_panel, style='TFrame')
        goals_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Hedefler tablosu
        self.goals_tree = ttk.Treeview(goals_content, 
                                      columns=("type", "target", "limit", "time_window", "status"),
                                      show="headings", height=10)
        
        self.goals_tree.heading("type", text="Tip")
        self.goals_tree.heading("target", text="Hedef")
        self.goals_tree.heading("limit", text="Limit")
        self.goals_tree.heading("time_window", text="Zaman Aralığı")
        self.goals_tree.heading("status", text="Durum")
        
        self.goals_tree.column("type", width=120)
        self.goals_tree.column("target", width=150)
        self.goals_tree.column("limit", width=100)
        self.goals_tree.column("time_window", width=120)
        self.goals_tree.column("status", width=80)
        
        # Scrollbar
        goals_scroll = ttk.Scrollbar(goals_content, orient="vertical",
                                    command=self.goals_tree.yview)
        self.goals_tree.configure(yscrollcommand=goals_scroll.set)
        
        self.goals_tree.pack(side='left', fill='both', expand=True)
        goals_scroll.pack(side='right', fill='y')
        
        # Sil butonu
        delete_frame = ttk.Frame(goals_content, style='TFrame')
        delete_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(delete_frame, text="Seçili Hedefi Sil", command=self._delete_goal,
                  style='Danger.TButton').pack(side='right')

    def _create_dynamic_fields(self):
        """Hedef tipine göre dinamik alanlar oluşturur."""
        # Mevcut widget'ları temizle
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
            
        goal_type = self.goal_type_var.get()
        selected_type = self.goal_type_mapping.get(goal_type, "max_usage")
        
        if selected_type in ['min_usage', 'max_usage']:
            # Kategori seçimi
            ttk.Label(self.dynamic_frame, text="Kategori:",
                     font=STYLE_CONFIG["font_bold"]).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
            
            self.category_var = StringVar()
            self.category_combo = ttk.Combobox(self.dynamic_frame, textvariable=self.category_var,
                                              state="readonly")
            self.category_combo.grid(row=0, column=1, sticky='ew', pady=5)
            
            # Kategorileri yükle
            categories = database.get_all_categories()
            self.category_combo['values'] = categories
            if categories:
                self.category_combo.set(categories[0])
            
            # Süre limiti
            ttk.Label(self.dynamic_frame, text="Süre Limiti (dakika):",
                     font=STYLE_CONFIG["font_bold"]).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=5)
            
            self.time_limit_var = StringVar()
            self.time_limit_entry = ttk.Entry(self.dynamic_frame, textvariable=self.time_limit_var)
            self.time_limit_entry.grid(row=1, column=1, sticky='ew', pady=5)
            
        elif selected_type == 'block':
            # Uygulama seçimi
            ttk.Label(self.dynamic_frame, text="Engellenecek Uygulama:",
                     font=STYLE_CONFIG["font_bold"]).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
            
            self.process_var = StringVar()
            self.process_combo = ttk.Combobox(self.dynamic_frame, textvariable=self.process_var)
            self.process_combo.grid(row=0, column=1, sticky='ew', pady=5)
            
            # Uygulamaları yükle
            processes = database.get_all_processes()
            self.process_combo['values'] = processes
            if processes:
                self.process_combo.set(processes[0])
                
        elif selected_type == 'time_window_max':
            # Kategori seçimi
            ttk.Label(self.dynamic_frame, text="Kategori:",
                     font=STYLE_CONFIG["font_bold"]).grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
            
            self.category_var = StringVar()
            self.category_combo = ttk.Combobox(self.dynamic_frame, textvariable=self.category_var,
                                              state="readonly")
            self.category_combo.grid(row=0, column=1, sticky='ew', pady=5)
            
            categories = database.get_all_categories()
            self.category_combo['values'] = categories
            if categories:
                self.category_combo.set(categories[0])
            
            # Zaman aralığı
            ttk.Label(self.dynamic_frame, text="Zaman Aralığı:",
                     font=STYLE_CONFIG["font_bold"]).grid(row=1, column=0, sticky='w', padx=(0, 10), pady=5)
            
            time_frame = ttk.Frame(self.dynamic_frame, style='TFrame')
            time_frame.grid(row=1, column=1, sticky='ew', pady=5)
            
            self.start_hour_var = StringVar(value="09")
            self.start_min_var = StringVar(value="00")
            self.end_hour_var = StringVar(value="17")
            self.end_min_var = StringVar(value="00")
            
            ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.start_hour_var,
                       width=3, format="%02.0f").pack(side='left', padx=2)
            ttk.Label(time_frame, text=":").pack(side='left')
            ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.start_min_var,
                       width=3, format="%02.0f").pack(side='left', padx=2)
            ttk.Label(time_frame, text=" - ").pack(side='left', padx=5)
            ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.end_hour_var,
                       width=3, format="%02.0f").pack(side='left', padx=2)
            ttk.Label(time_frame, text=":").pack(side='left')
            ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.end_min_var,
                       width=3, format="%02.0f").pack(side='left', padx=2)
            
            # Süre limiti
            ttk.Label(self.dynamic_frame, text="Maksimum Süre (dakika):",
                     font=STYLE_CONFIG["font_bold"]).grid(row=2, column=0, sticky='w', padx=(0, 10), pady=5)
            
            self.time_limit_var = StringVar()
            self.time_limit_entry = ttk.Entry(self.dynamic_frame, textvariable=self.time_limit_var)
            self.time_limit_entry.grid(row=2, column=1, sticky='ew', pady=5)

    def _on_goal_type_change(self, event=None):
        """Hedef tipi değiştiğinde dinamik alanları günceller."""
        self._create_dynamic_fields()

    def _add_goal(self):
        """Yeni hedef ekler."""
        try:
            goal_type_display = self.goal_type_var.get()
            goal_type = self.goal_type_mapping.get(goal_type_display, "max_usage")
            
            category = None
            process_name = None
            time_limit = None
            start_time = None
            end_time = None
            
            if goal_type in ['min_usage', 'max_usage']:
                category = self.category_var.get()
                time_limit_str = self.time_limit_var.get()
                
                if not category or not time_limit_str:
                    raise ValueError("Kategori ve süre limiti gereklidir.")
                    
                time_limit = int(time_limit_str)
                if time_limit <= 0:
                    raise ValueError("Süre limiti pozitif bir sayı olmalıdır.")
                    
            elif goal_type == 'block':
                process_name = self.process_var.get()
                if not process_name:
                    raise ValueError("Engellenecek uygulama seçilmelidir.")
                    
            elif goal_type == 'time_window_max':
                category = self.category_var.get()
                time_limit_str = self.time_limit_var.get()
                
                if not category or not time_limit_str:
                    raise ValueError("Kategori ve süre limiti gereklidir.")
                    
                time_limit = int(time_limit_str)
                if time_limit <= 0:
                    raise ValueError("Süre limiti pozitif bir sayı olmalıdır.")
                
                start_time = f"{int(self.start_hour_var.get()):02d}:{int(self.start_min_var.get()):02d}"
                end_time = f"{int(self.end_hour_var.get()):02d}:{int(self.end_min_var.get()):02d}"
                
                # Zaman kontrolü
                start_dt = datetime.datetime.strptime(start_time, '%H:%M').time()
                end_dt = datetime.datetime.strptime(end_time, '%H:%M').time()
                if start_dt >= end_dt:
                    raise ValueError("Başlangıç zamanı bitiş zamanından önce olmalıdır.")
            
            # Hedefi veritabanına ekle
            database.add_goal(category, process_name, goal_type, time_limit, start_time, end_time)
            
            messagebox.showinfo("Başarılı", "Hedef başarıyla eklendi.", parent=self)
            self._load_goals()
            self._clear_form()
            
        except ValueError as e:
            messagebox.showwarning("Geçersiz Giriş", str(e), parent=self)
        except Exception as e:
            logging.error(f"Hedef eklenirken hata: {e}")
            messagebox.showerror("Hata", f"Hedef eklenirken hata oluştu: {e}", parent=self)

    def _clear_form(self):
        """Formu temizler."""
        try:
            if hasattr(self, 'time_limit_var'):
                self.time_limit_var.set("")
        except:
            pass

    def _load_goals(self):
        """Mevcut hedefleri yükler."""
        try:
            # Mevcut öğeleri temizle
            for item in self.goals_tree.get_children():
                self.goals_tree.delete(item)
            
            goals = database.get_goals()
            for goal in goals:
                # Tip çevirisi
                type_display = {
                    'max_usage': 'Maks. Kullanım',
                    'min_usage': 'Min. Kullanım',
                    'block': 'Engelleme',
                    'time_window_max': 'Zaman Aralığı'
                }.get(goal['goal_type'], goal['goal_type'])
                
                # Hedef (kategori veya uygulama)
                target = goal['category'] or goal['process_name'] or "N/A"
                
                # Limit
                limit = f"{goal['time_limit_minutes']} dk" if goal['time_limit_minutes'] else "N/A"
                
                # Zaman aralığı
                time_window = "Tüm Gün"
                if goal['start_time_of_day'] and goal['end_time_of_day']:
                    time_window = f"{goal['start_time_of_day']}-{goal['end_time_of_day']}"
                
                # Durum (basit kontrol)
                status = "Aktif"  # Bu kısım geliştirilebilir
                
                self.goals_tree.insert("", "end", iid=goal['id'],
                                      values=(type_display, target, limit, time_window, status))
                                      
        except Exception as e:
            logging.error(f"Hedefler yüklenirken hata: {e}")

    def _delete_goal(self):
        """Seçili hedefi siler."""
        selected_item = self.goals_tree.selection()
        if not selected_item:
            messagebox.showwarning("Seçim Gerekli", "Lütfen silmek istediğiniz hedefi seçin.", parent=self)
            return
        
        goal_id = selected_item[0]
        
        if messagebox.askyesno("Hedef Sil", "Bu hedefi silmek istediğinizden emin misiniz?", parent=self):
            try:
                database.delete_goal(goal_id)
                messagebox.showinfo("Başarılı", "Hedef başarıyla silindi.", parent=self)
                self._load_goals()
            except Exception as e:
                logging.error(f"Hedef silinirken hata: {e}")
                messagebox.showerror("Hata", f"Hedef silinirken hata oluştu: {e}", parent=self)

class SettingsWindow(BaseWindow):
    """Ayarlar penceresi."""
    
    def __init__(self, master=None, app_instance=None):
        super().__init__(master, "Ayarlar", "600x650")
        self.app_instance = app_instance
        self.config_manager = app_instance.config_manager if app_instance else None
        
        self._create_settings_interface()
        self._load_settings()
        
        self.add_action_buttons([
            {'text': 'Kaydet', 'command': self._save_settings, 'style': 'Accent.TButton'},
            {'text': 'İptal', 'command': self.destroy, 'style': 'TButton'}
        ])

    def _create_settings_interface(self):
        """Ayarlar arayüzü."""
        # Ayarlar notebook
        settings_notebook = ttk.Notebook(self.content_frame)
        settings_notebook.pack(fill='both', expand=True)
        
        # Genel Ayarlar
        general_frame = ttk.Frame(settings_notebook, style='TFrame')
        settings_notebook.add(general_frame, text="⚙️ Genel")
        self._create_general_settings(general_frame)
        
        # Bildirim Ayarları
        notifications_frame = ttk.Frame(settings_notebook, style='TFrame')
        settings_notebook.add(notifications_frame, text="🔔 Bildirimler")
        self._create_notification_settings(notifications_frame)
        
        # Gelişmiş Ayarlar
        advanced_frame = ttk.Frame(settings_notebook, style='TFrame')
        settings_notebook.add(advanced_frame, text="🔧 Gelişmiş")
        self._create_advanced_settings(advanced_frame)

    def _create_general_settings(self, parent):
        """Genel ayarlar sekmesi."""
        content = ttk.Frame(parent, style='TFrame')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(content, text="Genel Ayarlar",
                               font=STYLE_CONFIG["font_h2"])
        title_label.pack(anchor='w', pady=(0, 20))
        
        # Ayarlar grid
        settings_grid = ttk.Frame(content, style='TFrame')
        settings_grid.pack(fill='x')
        settings_grid.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # Boşta kalma eşiği
        ttk.Label(settings_grid, text="Boşta Kalma Eşiği (saniye):",
                 font=STYLE_CONFIG["font_bold"]).grid(row=row, column=0, sticky='w', padx=(0, 15), pady=8)
        
        self.idle_threshold_var = tk.IntVar()
        self.idle_threshold_spin = ttk.Spinbox(settings_grid, from_=30, to=600, increment=30,
                                              textvariable=self.idle_threshold_var, width=10)
        self.idle_threshold_spin.grid(row=row, column=1, sticky='w', pady=8)
        row += 1
        
        # Uygulama dili
        ttk.Label(settings_grid, text="Uygulama Dili:",
                 font=STYLE_CONFIG["font_bold"]).grid(row=row, column=0, sticky='w', padx=(0, 15), pady=8)
        
        self.language_var = StringVar()
        self.language_combo = ttk.Combobox(settings_grid, textvariable=self.language_var,
                                          values=["Türkçe", "English"], state="readonly", width=15)
        self.language_combo.grid(row=row, column=1, sticky='w', pady=8)
        row += 1
        
        # Başlangıçta çalıştır
        self.startup_var = tk.BooleanVar()
        startup_check = ttk.Checkbutton(settings_grid, text="Windows başlangıcında çalıştır",
                                       variable=self.startup_var)
        startup_check.grid(row=row, column=0, columnspan=2, sticky='w', pady=8)
        row += 1
        
        # Veri saklama süresi
        ttk.Label(settings_grid, text="Veri Saklama Süresi (gün):",
                 font=STYLE_CONFIG["font_bold"]).grid(row=row, column=0, sticky='w', padx=(0, 15), pady=8)
        
        self.retention_var = tk.IntVar()
        self.retention_spin = ttk.Spinbox(settings_grid, from_=0, to=9999, increment=30,
                                         textvariable=self.retention_var, width=10)
        self.retention_spin.grid(row=row, column=1, sticky='w', pady=8)
        
        # Açıklama
        ttk.Label(settings_grid, text="(0 = Sonsuz saklama)",
                 font=STYLE_CONFIG["font_small"],
                 foreground=STYLE_CONFIG["text_secondary"]).grid(row=row+1, column=1, sticky='w', pady=2)

    def _create_notification_settings(self, parent):
        """Bildirim ayarları sekmesi."""
        content = ttk.Frame(parent, style='TFrame')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(content, text="Bildirim Ayarları",
                               font=STYLE_CONFIG["font_h2"])
        title_label.pack(anchor='w', pady=(0, 20))
        
        # Bildirim türleri
        notifications_frame = ttk.LabelFrame(content, text="Bildirim Türleri",
                                            style='TLabelframe')
        notifications_frame.pack(fill='x', pady=(0, 15))
        
        notif_content = ttk.Frame(notifications_frame, style='TFrame')
        notif_content.pack(fill='x', padx=15, pady=15)
        
        self.goal_notifications_var = tk.BooleanVar()
        ttk.Checkbutton(notif_content, text="Hedef bildirimlerini göster",
                       variable=self.goal_notifications_var).pack(anchor='w', pady=3)
        
        self.focus_notifications_var = tk.BooleanVar()
        ttk.Checkbutton(notif_content, text="Odaklanma modu bildirimlerini göster",
                       variable=self.focus_notifications_var).pack(anchor='w', pady=3)
        
        self.achievement_notifications_var = tk.BooleanVar()
        ttk.Checkbutton(notif_content, text="Başarım bildirimlerini göster",
                       variable=self.achievement_notifications_var).pack(anchor='w', pady=3)
        
        # Bildirim sıklığı
        freq_frame = ttk.LabelFrame(content, text="Bildirim Sıklığı",
                                   style='TLabelframe')
        freq_frame.pack(fill='x')
        
        freq_content = ttk.Frame(freq_frame, style='TFrame')
        freq_content.pack(fill='x', padx=15, pady=15)
        freq_content.grid_columnconfigure(1, weight=1)
        
        ttk.Label(freq_content, text="Odaklanma bildirimi sıklığı (saniye):",
                 font=STYLE_CONFIG["font_bold"]).grid(row=0, column=0, sticky='w', padx=(0, 15), pady=5)
        
        self.focus_freq_var = tk.IntVar()
        ttk.Spinbox(freq_content, from_=60, to=1800, increment=60,
                   textvariable=self.focus_freq_var, width=10).grid(row=0, column=1, sticky='w', pady=5)

    def _create_advanced_settings(self, parent):
        """Gelişmiş ayarlar sekmesi."""
        content = ttk.Frame(parent, style='TFrame')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Başlık
        title_label = ttk.Label(content, text="Gelişmiş Ayarlar",
                               font=STYLE_CONFIG["font_h2"])
        title_label.pack(anchor='w', pady=(0, 20))
        
        # Hata raporlama
        error_frame = ttk.LabelFrame(content, text="Hata Raporlama",
                                    style='TLabelframe')
        error_frame.pack(fill='x', pady=(0, 15))
        
        error_content = ttk.Frame(error_frame, style='TFrame')
        error_content.pack(fill='x', padx=15, pady=15)
        
        self.sentry_var = tk.BooleanVar()
        ttk.Checkbutton(error_content, text="Anonim hata raporlamasını etkinleştir (Sentry)",
                       variable=self.sentry_var).pack(anchor='w', pady=3)
        
        # Açıklama
        desc_text = ("Bu seçenek etkinleştirildiğinde, uygulama hataları anonim olarak "
                    "geliştiricilere gönderilir. Kişisel verileriniz paylaşılmaz.")
        ttk.Label(error_content, text=desc_text, font=STYLE_CONFIG["font_small"],
                 foreground=STYLE_CONFIG["text_secondary"],
                 wraplength=400).pack(anchor='w', pady=(5, 0))
        
        # Güncellemeler
        update_frame = ttk.LabelFrame(content, text="Güncellemeler",
                                     style='TLabelframe')
        update_frame.pack(fill='x')
        
        update_content = ttk.Frame(update_frame, style='TFrame')
        update_content.pack(fill='x', padx=15, pady=15)
        
        ttk.Button(update_content, text="Güncellemeleri Kontrol Et",
                  command=self._check_updates).pack(anchor='w')

    def _load_settings(self):
        """Mevcut ayarları yükler."""
        if not self.config_manager:
            return
        
        try:
            # Genel ayarlar
            self.idle_threshold_var.set(self.config_manager.get('settings.idle_threshold_seconds', 180))
            
            language = self.config_manager.get('settings.language', 'tr')
            language_display = "Türkçe" if language == 'tr' else "English"
            self.language_var.set(language_display)
            
            self.startup_var.set(self.config_manager.get('settings.run_on_startup', False))
            self.retention_var.set(self.config_manager.get('settings.data_retention_days', 365))
            
            # Bildirim ayarları
            notif_settings = self.config_manager.get('settings.notification_settings', {})
            self.goal_notifications_var.set(notif_settings.get('enable_goal_notifications', True))
            self.focus_notifications_var.set(notif_settings.get('enable_focus_notifications', True))
            self.achievement_notifications_var.set(notif_settings.get('show_achievement_notifications', True))
            self.focus_freq_var.set(notif_settings.get('focus_notification_frequency_seconds', 300))
            
            # Gelişmiş ayarlar
            self.sentry_var.set(self.config_manager.get('settings.enable_sentry_reporting', True))
            
        except Exception as e:
            logging.error(f"Ayarlar yüklenirken hata: {e}")

    def _save_settings(self):
        """Ayarları kaydeder."""
        if not self.config_manager:
            messagebox.showerror("Hata", "Yapılandırma yöneticisi bulunamadı.", parent=self)
            return
        
        try:
            # Genel ayarlar
            idle_threshold = self.idle_threshold_var.get()
            if idle_threshold <= 0:
                raise ValueError("Boşta kalma eşiği pozitif bir sayı olmalıdır.")
            self.config_manager.set('settings.idle_threshold_seconds', idle_threshold)
            
            language_display = self.language_var.get()
            language_code = 'tr' if language_display == 'Türkçe' else 'en'
            self.config_manager.set('settings.language', language_code)
            
            self.config_manager.set('settings.run_on_startup', self.startup_var.get())
            
            retention_days = self.retention_var.get()
            if retention_days < 0:
                raise ValueError("Veri saklama süresi negatif olamaz.")
            self.config_manager.set('settings.data_retention_days', retention_days)
            
            # Bildirim ayarları
            notif_settings = {
                'enable_goal_notifications': self.goal_notifications_var.get(),
                'enable_focus_notifications': self.focus_notifications_var.get(),
                'show_achievement_notifications': self.achievement_notifications_var.get(),
                'focus_notification_frequency_seconds': self.focus_freq_var.get()
            }
            
            if notif_settings['focus_notification_frequency_seconds'] <= 0:
                raise ValueError("Bildirim sıklığı pozitif bir sayı olmalıdır.")
                
            self.config_manager.set('settings.notification_settings', notif_settings)
            
            # Gelişmiş ayarlar
            self.config_manager.set('settings.enable_sentry_reporting', self.sentry_var.get())
            
            # App instance güncelle
            if self.app_instance:
                self.app_instance._set_run_on_startup(self.startup_var.get())
                if hasattr(self.app_instance, 'tracker_instance'):
                    self.app_instance.tracker_instance.update_settings(self.config_manager.get('settings'))
            
            messagebox.showinfo("Başarılı", "Ayarlar başarıyla kaydedildi.", parent=self)
            self.destroy()
            
        except ValueError as e:
            messagebox.showwarning("Geçersiz Giriş", str(e), parent=self)
        except Exception as e:
            logging.error(f"Ayarlar kaydedilirken hata: {e}")
            messagebox.showerror("Hata", f"Ayarlar kaydedilirken hata oluştu: {e}", parent=self)

    def _check_updates(self):
        """Güncellemeleri kontrol eder."""
        messagebox.showinfo("Güncelleme Kontrolü", 
                           "Güncellemeler kontrol ediliyor...\n\n"
                           "Bu özellik gelecek sürümlerde aktif hale gelecektir.", 
                           parent=self)

class FocusSetupWindow(BaseWindow):
    """Odaklanma oturumu kurulum penceresi."""
    
    def __init__(self, master, on_start_callback):
        super().__init__(master, "Odaklanma Oturumu Ayarla", "450x550")
        self.on_start_callback = on_start_callback
        
        self._create_focus_interface()
        
        self.add_action_buttons([
            {'text': 'Başlat', 'command': self._start_session, 'style': 'Accent.TButton'},
            {'text': 'İptal', 'command': self.destroy, 'style': 'TButton'}
        ])

    def _create_focus_interface(self):
        """Odaklanma arayüzü."""
        # Başlık
        title_label = ttk.Label(self.content_frame, 
                               text="Odaklanma Oturumu",
                               font=STYLE_CONFIG["font_h2"])
        title_label.pack(pady=(0, 20))
        
        # Oturum süresi
        duration_frame = ttk.LabelFrame(self.content_frame, text="Oturum Süresi",
                                       style='TLabelframe')
        duration_frame.pack(fill='x', pady=(0, 20))
        
        duration_content = ttk.Frame(duration_frame, style='TFrame')
        duration_content.pack(fill='x', padx=15, pady=15)
        
        self.duration_var = tk.IntVar(value=60)
        
        # Hazır süre seçenekleri
        duration_options = [
            ("25 dakika (Pomodoro)", 25),
            ("45 dakika", 45),
            ("60 dakika", 60),
            ("90 dakika", 90),
            ("120 dakika", 120)
        ]
        
        for text, value in duration_options:
            rb = ttk.Radiobutton(duration_content, text=text, 
                                variable=self.duration_var, value=value)
            rb.pack(anchor='w', pady=3)
        
        # Özel süre
        custom_frame = ttk.Frame(duration_content, style='TFrame')
        custom_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Radiobutton(custom_frame, text="Özel süre:", 
                       variable=self.duration_var, value=0).pack(side='left')
        
        self.custom_duration_var = tk.IntVar(value=30)
        custom_spin = ttk.Spinbox(custom_frame, from_=10, to=240, increment=5,
                                 textvariable=self.custom_duration_var, width=8)
        custom_spin.pack(side='left', padx=(10, 5))
        ttk.Label(custom_frame, text="dakika").pack(side='left')
        
        # İzin verilen kategoriler
        categories_frame = ttk.LabelFrame(self.content_frame, text="İzin Verilen Kategoriler",
                                         style='TLabelframe')
        categories_frame.pack(fill='both', expand=True)
        
        categories_content = ttk.Frame(categories_frame, style='TFrame')
        categories_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Scrollable frame
        canvas = tk.Canvas(categories_content, bg=STYLE_CONFIG["bg_card"], 
                          highlightthickness=0, height=200)
        scrollbar = ttk.Scrollbar(categories_content, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Kategorileri yükle
        categories = database.get_all_categories()
        if "Other" not in categories:
            categories.append("Other")
        
        self.category_vars = {}
        for i, category in enumerate(sorted(categories)):
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(scrollable_frame, text=category, variable=var)
            cb.grid(row=i, column=0, sticky='w', padx=5, pady=2)
            self.category_vars[category] = var
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Hızlı seçim butonları
        quick_frame = ttk.Frame(categories_content, style='TFrame')
        quick_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(quick_frame, text="Tümünü Seç", 
                  command=self._select_all_categories).pack(side='left', padx=5)
        ttk.Button(quick_frame, text="Hiçbirini Seçme", 
                  command=self._deselect_all_categories).pack(side='left', padx=5)
        ttk.Button(quick_frame, text="Sadece Verimlilik", 
                  command=self._select_productivity_categories).pack(side='left', padx=5)

    def _select_all_categories(self):
        """Tüm kategorileri seçer."""
        for var in self.category_vars.values():
            var.set(True)

    def _deselect_all_categories(self):
        """Tüm kategori seçimlerini kaldırır."""
        for var in self.category_vars.values():
            var.set(False)

    def _select_productivity_categories(self):
        """Sadece verimlilik kategorilerini seçer."""
        productivity_categories = ['Work', 'Development', 'Design', 'Education', 'Writing']
        
        for category, var in self.category_vars.items():
            if any(prod_cat.lower() in category.lower() for prod_cat in productivity_categories):
                var.set(True)
            else:
                var.set(False)

    def _start_session(self):
        """Odaklanma oturumunu başlatır."""
        try:
            # Süreyi belirle
            if self.duration_var.get() == 0:
                duration = self.custom_duration_var.get()
            else:
                duration = self.duration_var.get()
            
            if duration <= 0:
                raise ValueError("Oturum süresi pozitif bir sayı olmalıdır.")
            
            # İzin verilen kategorileri topla
            allowed_categories = [cat for cat, var in self.category_vars.items() if var.get()]
            
            if not allowed_categories:
                raise ValueError("En az bir kategori seçilmelidir.")
            
            # Callback'i çağır
            self.on_start_callback(duration, allowed_categories)
            self.destroy()
            
        except ValueError as e:
            messagebox.showwarning("Geçersiz Ayar", str(e), parent=self)
        except Exception as e:
            logging.error(f"Odaklanma oturumu başlatılırken hata: {e}")
            messagebox.showerror("Hata", f"Oturum başlatılırken hata oluştu: {e}", parent=self)

class CategoryManagementWindow(BaseWindow):
    """Kategori yönetimi penceresi."""
    
    def __init__(self, master=None):
        super().__init__(master, "Kategori Yönetimi", "900x650")
        
        self._create_category_interface()
        self._load_data()
        
        self.add_action_buttons([
            {'text': 'Kapat', 'command': self.destroy, 'style': 'TButton'}
        ])

    def _create_category_interface(self):
        """Kategori yönetimi arayüzü."""
        # Ana panel düzeni
        main_panel = ttk.Frame(self.content_frame, style='TFrame')
        main_panel.pack(fill='both', expand=True)
        
        # Sol panel - Kategorize edilmemiş uygulamalar
        left_panel = ttk.LabelFrame(main_panel, text="Kategorize Edilmemiş Uygulamalar",
                                   style='TLabelframe')
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        left_content = ttk.Frame(left_panel, style='TFrame')
        left_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Arama kutusu
        search_frame = ttk.Frame(left_content, style='TFrame')
        search_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(search_frame, text="Ara:", font=STYLE_CONFIG["font_bold"]).pack(side='left', padx=(0, 5))
        self.search_var = StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True)
        search_entry.bind('<KeyRelease>', self._filter_uncategorized)
        
        # Uncategorized listbox
        self.uncategorized_listbox = Listbox(left_content, selectmode=tk.SINGLE,
                                            font=STYLE_CONFIG["font_normal"])
        self.uncategorized_listbox.pack(fill='both', expand=True)
        self.uncategorized_listbox.bind("<<ListboxSelect>>", self._on_uncategorized_select)
        
        # Orta panel - Kontroller
        middle_panel = ttk.Frame(main_panel, style='TFrame', width=200)
        middle_panel.pack(side='left', fill='y', padx=10)
        middle_panel.pack_propagate(False)
        
        # Kategori seçimi
        category_frame = ttk.LabelFrame(middle_panel, text="Kategori İşlemleri",
                                       style='TLabelframe')
        category_frame.pack(fill='x', pady=(0, 15))
        
        cat_content = ttk.Frame(category_frame, style='TFrame')
        cat_content.pack(fill='x', padx=15, pady=15)
        
        ttk.Label(cat_content, text="Kategori Seç:",
                 font=STYLE_CONFIG["font_bold"]).pack(anchor='w', pady=(0, 5))
        
        self.category_var = StringVar()
        self.category_combo = ttk.Combobox(cat_content, textvariable=self.category_var,
                                          state="readonly")
        self.category_combo.pack(fill='x', pady=(0, 10))
        
        # Butonlar
        ttk.Button(cat_content, text="Kategori Ata", command=self._assign_category,
                  style='Accent.TButton').pack(fill='x', pady=2)
        
        ttk.Button(cat_content, text="Yeni Kategori", command=self._add_new_category).pack(fill='x', pady=2)
        
        ttk.Button(cat_content, text="Kategori Sil", command=self._delete_category,
                  style='Danger.TButton').pack(fill='x', pady=2)
        
        # İstatistikler
        stats_frame = ttk.LabelFrame(middle_panel, text="İstatistikler",
                                    style='TLabelframe')
        stats_frame.pack(fill='x')
        
        stats_content = ttk.Frame(stats_frame, style='TFrame')
        stats_content.pack(fill='x', padx=15, pady=15)
        
        self.stats_label = ttk.Label(stats_content, text="İstatistikler yükleniyor...",
                                    font=STYLE_CONFIG["font_small"])
        self.stats_label.pack(anchor='w')
        
        # Sağ panel - Kategorize edilmiş uygulamalar
        right_panel = ttk.LabelFrame(main_panel, text="Kategorize Edilmiş Uygulamalar",
                                    style='TLabelframe')
        right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        right_content = ttk.Frame(right_panel, style='TFrame')
        right_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Kategorize edilmiş uygulamalar tablosu
        self.categorized_tree = ttk.Treeview(right_content, 
                                           columns=("app", "category", "usage"),
                                           show="headings", height=20)
        
        self.categorized_tree.heading("app", text="Uygulama")
        self.categorized_tree.heading("category", text="Kategori")
        self.categorized_tree.heading("usage", text="Son Kullanım")
        
        self.categorized_tree.column("app", width=200)
        self.categorized_tree.column("category", width=120)
        self.categorized_tree.column("usage", width=100)
        
        # Scrollbar
        cat_scrollbar = ttk.Scrollbar(right_content, orient="vertical",
                                     command=self.categorized_tree.yview)
        self.categorized_tree.configure(yscrollcommand=cat_scrollbar.set)
        
        self.categorized_tree.pack(side='left', fill='both', expand=True)
        cat_scrollbar.pack(side='right', fill='y')
        
        self.categorized_tree.bind("<<TreeviewSelect>>", self._on_categorized_select)

    def _load_data(self):
        """Kategori verilerini yükler."""
        try:
            # Kategorize edilmemiş uygulamaları yükle
            self.uncategorized_apps = database.get_uncategorized_apps()
            self._update_uncategorized_list()
            
            # Kategorileri yükle
            categories = database.get_all_categories()
            if 'Other' not in categories:
                categories.append('Other')
            self.category_combo['values'] = sorted(categories)
            
            if categories:
                self.category_combo.set(categories[0])
            
            # Kategorize edilmiş uygulamaları yükle
            self._load_categorized_apps()
            
            # İstatistikleri güncelle
            self._update_stats()
            
        except Exception as e:
            logging.error(f"Kategori verileri yüklenirken hata: {e}")

    def _update_uncategorized_list(self):
        """Kategorize edilmemiş liste günceller."""
        self.uncategorized_listbox.delete(0, tk.END)
        
        search_term = self.search_var.get().lower()
        filtered_apps = [app for app in self.uncategorized_apps 
                        if search_term in app.lower()]
        
        for app in sorted(filtered_apps):
            self.uncategorized_listbox.insert(tk.END, app)

    def _filter_uncategorized(self, event=None):
        """Arama kutusuna göre filtreler."""
        self._update_uncategorized_list()

    def _load_categorized_apps(self):
        """Kategorize edilmiş uygulamaları yükler."""
        try:
            self.categorized_tree.delete(*self.categorized_tree.get_children())
            
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ac.process_name, ac.category, 
                           MAX(ul.start_time) as last_usage
                    FROM app_categories ac
                    LEFT JOIN usage_logs ul ON ac.process_name = ul.process_name
                    GROUP BY ac.process_name, ac.category
                    ORDER BY ac.category, ac.process_name
                """)
                
                categorized_apps = cursor.fetchall()
            
            for app, category, last_usage in categorized_apps:
                if last_usage:
                    usage_date = datetime.datetime.fromtimestamp(last_usage).strftime('%Y-%m-%d')
                else:
                    usage_date = "Hiç kullanılmamış"
                
                self.categorized_tree.insert("", "end", values=(app, category, usage_date))
                
        except Exception as e:
            logging.error(f"Kategorize edilmiş uygulamalar yüklenirken hata: {e}")

    def _update_stats(self):
        """İstatistikleri günceller."""
        try:
            uncategorized_count = len(self.uncategorized_apps)
            
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM app_categories")
                categorized_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT category) FROM app_categories")
                category_count = cursor.fetchone()[0]
            
            stats_text = (f"Kategorize edilmemiş: {uncategorized_count}\n"
                         f"Kategorize edilmiş: {categorized_count}\n"
                         f"Toplam kategori: {category_count}")
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            logging.error(f"İstatistikler güncellenirken hata: {e}")

    def _on_uncategorized_select(self, event):
        """Kategorize edilmemiş uygulama seçildiğinde."""
        selection = self.uncategorized_listbox.curselection()
        if selection:
            app_name = self.uncategorized_listbox.get(selection[0])
            # Mevcut kategoriyi bul ve seç
            current_category = database.get_category_for_process(app_name)
            if current_category and current_category in self.category_combo['values']:
                self.category_combo.set(current_category)

    def _on_categorized_select(self, event):
        """Kategorize edilmiş uygulama seçildiğinde."""
        selection = self.categorized_tree.selection()
        if selection:
            item_values = self.categorized_tree.item(selection[0], 'values')
            if item_values:
                category = item_values[1]
                self.category_combo.set(category)

    def _assign_category(self):
        """Seçili uygulamaya kategori atar."""
        try:
            selected_category = self.category_var.get()
            if not selected_category:
                messagebox.showwarning("Uyarı", "Lütfen bir kategori seçin.", parent=self)
                return
            
            # Hangi uygulamanın seçildiğini bul
            app_to_assign = None
            
            # Önce uncategorized listeden kontrol et
            uncategorized_selection = self.uncategorized_listbox.curselection()
            if uncategorized_selection:
                app_to_assign = self.uncategorized_listbox.get(uncategorized_selection[0])
            else:
                # Categorized tree'den kontrol et
                categorized_selection = self.categorized_tree.selection()
                if categorized_selection:
                    item_values = self.categorized_tree.item(categorized_selection[0], 'values')
                    app_to_assign = item_values[0]
            
            if not app_to_assign:
                messagebox.showwarning("Uyarı", "Lütfen bir uygulama seçin.", parent=self)
                return
            
            # Kategoriyi ata
            database.update_app_category(app_to_assign, selected_category)
            
            messagebox.showinfo("Başarılı", 
                               f"'{app_to_assign}' uygulaması '{selected_category}' kategorisine atandı.",
                               parent=self)
            
            # Verileri yenile
            self._load_data()
            
        except Exception as e:
            logging.error(f"Kategori atanırken hata: {e}")
            messagebox.showerror("Hata", f"Kategori atanırken hata oluştu: {e}", parent=self)

    def _add_new_category(self):
        """Yeni kategori ekler."""
        try:
            new_category = simpledialog.askstring(
                "Yeni Kategori", 
                "Yeni kategori adını girin:",
                parent=self
            )
            
            if new_category and new_category.strip():
                new_category = new_category.strip()
                
                # Mevcut kategorileri kontrol et
                current_categories = list(self.category_combo['values'])
                if new_category in current_categories:
                    messagebox.showwarning("Uyarı", "Bu kategori zaten mevcut.", parent=self)
                    return
                
                # Kategoriyi ekle
                current_categories.append(new_category)
                self.category_combo['values'] = sorted(current_categories)
                self.category_combo.set(new_category)
                
                messagebox.showinfo("Başarılı", 
                                   f"'{new_category}' kategorisi eklendi.",
                                   parent=self)
            
        except Exception as e:
            logging.error(f"Yeni kategori eklenirken hata: {e}")
            messagebox.showerror("Hata", f"Kategori eklenirken hata oluştu: {e}", parent=self)

    def _delete_category(self):
        """Seçili kategoriyi siler."""
        try:
            selected_category = self.category_var.get()
            if not selected_category:
                messagebox.showwarning("Uyarı", "Lütfen silinecek kategoriyi seçin.", parent=self)
                return
            
            if selected_category == 'Other':
                messagebox.showerror("Hata", "'Other' kategorisi silinemez.", parent=self)
                return
            
            # Onay al
            if not messagebox.askyesno("Kategori Sil", 
                                      f"'{selected_category}' kategorisini silmek istediğinizden emin misiniz?\n\n"
                                      "Bu kategorideki tüm uygulamalar 'Other' kategorisine taşınacaktır.",
                                      parent=self):
                return
            
            # Kategoriyi sil ve uygulamaları Other'a taşı
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE app_categories SET category = 'Other' WHERE category = ?", 
                             (selected_category,))
                conn.commit()
            
            # Combobox'ı güncelle
            current_categories = list(self.category_combo['values'])
            if selected_category in current_categories:
                current_categories.remove(selected_category)
                self.category_combo['values'] = sorted(current_categories)
                if current_categories:
                    self.category_combo.set(current_categories[0])
            
            messagebox.showinfo("Başarılı", 
                               f"'{selected_category}' kategorisi silindi ve uygulamalar 'Other' kategorisine taşındı.",
                               parent=self)
            
            # Verileri yenile
            self._load_data()
            
        except Exception as e:
            logging.error(f"Kategori silinirken hata: {e}")
            messagebox.showerror("Hata", f"Kategori silinirken hata oluştu: {e}", parent=self)

class NotificationHistoryWindow(BaseWindow):
    """Bildirim geçmişi penceresi."""
    
    def __init__(self, master=None, app_instance=None):
        super().__init__(master, "Bildirim Geçmişi", "800x600")
        self.app_instance = app_instance
        
        self._create_notification_interface()
        self._load_notifications()
        
        self.add_action_buttons([
            {'text': 'Kapat', 'command': self._on_closing, 'style': 'TButton'}
        ])
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_notification_interface(self):
        """Bildirim arayüzü."""
        # Üst kontrol paneli
        control_panel = ttk.Frame(self.content_frame, style='TFrame')
        control_panel.pack(fill='x', pady=(0, 15))
        
        # Sol taraf - Filtreler
        filter_frame = ttk.Frame(control_panel, style='TFrame')
        filter_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(filter_frame, text="Filtrele:",
                 font=STYLE_CONFIG["font_bold"]).pack(side='left', padx=(0, 10))
        
        self.filter_var = StringVar(value="Tümü")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                   values=["Tümü", "Okunmamış", "Hedef", "Odaklanma", "Başarım"],
                                   state="readonly", width=12)
        filter_combo.pack(side='left', padx=(0, 15))
        filter_combo.bind("<<ComboboxSelected>>", self._filter_notifications)
        
        # Sağ taraf - Eylemler
        action_frame = ttk.Frame(control_panel, style='TFrame')
        action_frame.pack(side='right')
        
        ttk.Button(action_frame, text="Tümünü Okundu İşaretle",
                  command=self._mark_all_read).pack(side='right', padx=5)
        ttk.Button(action_frame, text="Okunmuşları Sil",
                  command=self._delete_read_notifications,
                  style='Danger.TButton').pack(side='right', padx=5)
        
        # Bildirimler tablosu
        self.notifications_tree = ttk.Treeview(self.content_frame,
                                             columns=("time", "title", "message", "type", "status"),
                                             show="headings", height=18)
        
        self.notifications_tree.heading("time", text="Zaman")
        self.notifications_tree.heading("title", text="Başlık")
        self.notifications_tree.heading("message", text="Mesaj")
        self.notifications_tree.heading("type", text="Tip")
        self.notifications_tree.heading("status", text="Durum")
        
        self.notifications_tree.column("time", width=120)
        self.notifications_tree.column("title", width=150)
        self.notifications_tree.column("message", width=300)
        self.notifications_tree.column("type", width=80)
        self.notifications_tree.column("status", width=80)
        
        # Scrollbar
        notif_scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical",
                                       command=self.notifications_tree.yview)
        self.notifications_tree.configure(yscrollcommand=notif_scrollbar.set)
        
        self.notifications_tree.pack(side='left', fill='both', expand=True)
        notif_scrollbar.pack(side='right', fill='y')
        
        # Çift tıklama olayı
        self.notifications_tree.bind("<Double-1>", self._on_notification_double_click)

    def _load_notifications(self):
        """Bildirimleri yükler."""
        try:
            self.notifications_tree.delete(*self.notifications_tree.get_children())
            
            notifications = database.get_all_notifications()
            
            for notif in notifications:
                timestamp = datetime.datetime.fromtimestamp(notif['timestamp'])
                time_str = timestamp.strftime('%m/%d %H:%M')
                
                status = "Okundu" if notif['is_read'] else "Okunmamış"
                
                # Satır renklendirmesi için tag
                tag = "read" if notif['is_read'] else "unread"
                
                item = self.notifications_tree.insert("", "end", 
                                                     iid=notif['id'],
                                                     values=(time_str, notif['title'], 
                                                           notif['message'][:50] + "..." if len(notif['message']) > 50 else notif['message'], 
                                                           notif['type'], status),
                                                     tags=(tag,))
            
            # Tag renklendirmesi
            self.notifications_tree.tag_configure("unread", 
                                                 font=STYLE_CONFIG["font_bold"],
                                                 background=STYLE_CONFIG["accent_light"])
            self.notifications_tree.tag_configure("read", 
                                                 foreground=STYLE_CONFIG["text_secondary"])
            
        except Exception as e:
            logging.error(f"Bildirimler yüklenirken hata: {e}")

    def _filter_notifications(self, event=None):
        """Bildirimleri filtreler."""
        # Bu fonksiyon gelecekte implement edilebilir
        pass

    def _on_notification_double_click(self, event):
        """Bildirime çift tıklandığında."""
        try:
            item_id = self.notifications_tree.focus()
            if not item_id:
                return
            
            item_values = self.notifications_tree.item(item_id, 'values')
            notification_id = item_id
            
            # Bildirim detaylarını göster
            title = item_values[1]
            message_preview = item_values[2]
            time_str = item_values[0]
            
            # Tam mesajı al
            notifications = database.get_all_notifications()
            full_message = ""
            for notif in notifications:
                if str(notif['id']) == str(notification_id):
                    full_message = notif['message']
                    break
            
            # Detail dialog
            messagebox.showinfo(f"Bildirim: {title}", 
                               f"Zaman: {time_str}\n\n{full_message}",
                               parent=self)
            
            # Okundu olarak işaretle
            database.mark_notification_as_read(notification_id)
            self._load_notifications()
            
            # Tray icon güncelle
            if self.app_instance:
                self.app_instance.update_tray_icon()
                
        except Exception as e:
            logging.error(f"Bildirim detayı gösterilirken hata: {e}")

    def _mark_all_read(self):
        """Tüm bildirimleri okundu işaretle."""
        if messagebox.askyesno("Onay", "Tüm bildirimler okundu olarak işaretlensin mi?", parent=self):
            try:
                with database.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
                    conn.commit()
                
                self._load_notifications()
                
                if self.app_instance:
                    self.app_instance.update_tray_icon()
                
                messagebox.showinfo("Başarılı", "Tüm bildirimler okundu olarak işaretlendi.", parent=self)
                
            except Exception as e:
                logging.error(f"Bildirimler okundu işaretlenirken hata: {e}")
                messagebox.showerror("Hata", f"İşlem sırasında hata oluştu: {e}", parent=self)

    def _delete_read_notifications(self):
        """Okunmuş bildirimleri siler."""
        if messagebox.askyesno("Onay", 
                              "Tüm okunmuş bildirimler silinsin mi?\n\nBu işlem geri alınamaz.", 
                              parent=self):
            try:
                with database.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM notifications WHERE is_read = 1")
                    deleted_count = cursor.rowcount
                    conn.commit()
                
                self._load_notifications()
                
                if self.app_instance:
                    self.app_instance.update_tray_icon()
                
                messagebox.showinfo("Başarılı", 
                                   f"{deleted_count} okunmuş bildirim silindi.", 
                                   parent=self)
                
            except Exception as e:
                logging.error(f"Okunmuş bildirimler silinirken hata: {e}")
                messagebox.showerror("Hata", f"Silme işlemi sırasında hata oluştu: {e}", parent=self)

    def _on_closing(self):
        """Pencere kapatılırken."""
        if self.app_instance:
            self.app_instance.update_tray_icon()
        self.destroy()

class AchievementWindow(BaseWindow):
    """Başarımlar penceresi."""
    
    def __init__(self, master=None):
        super().__init__(master, "Başarımlar", "700x500")
        
        self._create_achievement_interface()
        self._load_achievements()
        
        self.add_action_buttons([
            {'text': 'Kapat', 'command': self.destroy, 'style': 'TButton'}
        ])

    def _create_achievement_interface(self):
        """Başarım arayüzü."""
        # Başlık
        title_frame = ttk.Frame(self.content_frame, style='TFrame')
        title_frame.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="🏆 Kazanılmış Başarımlar",
                               font=STYLE_CONFIG["font_h2"])
        title_label.pack(side='left')
        
        # İstatistik
        self.stats_label = ttk.Label(title_frame, text="",
                                    font=STYLE_CONFIG["font_normal"],
                                    foreground=STYLE_CONFIG["text_secondary"])
        self.stats_label.pack(side='right')
        
        # Başarımlar tablosu
        self.achievements_tree = ttk.Treeview(self.content_frame,
                                            columns=("name", "description", "date", "category"),
                                            show="headings", height=15)
        
        self.achievements_tree.heading("name", text="Başarım")
        self.achievements_tree.heading("description", text="Açıklama")
        self.achievements_tree.heading("date", text="Kazanılma Tarihi")
        self.achievements_tree.heading("category", text="Kategori")
        
        self.achievements_tree.column("name", width=150)
        self.achievements_tree.column("description", width=300)
        self.achievements_tree.column("date", width=120)
        self.achievements_tree.column("category", width=100)
        
        # Scrollbar
        ach_scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical",
                                     command=self.achievements_tree.yview)
        self.achievements_tree.configure(yscrollcommand=ach_scrollbar.set)
        
        self.achievements_tree.pack(side='left', fill='both', expand=True)
        ach_scrollbar.pack(side='right', fill='y')

    def _load_achievements(self):
        """Başarımları yükler."""
        try:
            self.achievements_tree.delete(*self.achievements_tree.get_children())
            
            achievements = database.get_all_unlocked_achievements()
            
            for ach in achievements:
                date_str = datetime.datetime.fromtimestamp(ach[3]).strftime('%Y-%m-%d %H:%M')
                
                # Kategori belirleme (basit yaklaşım)
                category = "Genel"
                if "gün" in ach[0].lower():
                    category = "Süreklilik"
                elif "saat" in ach[0].lower() or "dakika" in ach[0].lower():
                    category = "Zaman"
                elif "uygulama" in ach[0].lower():
                    category = "Kullanım"
                
                self.achievements_tree.insert("", "end", values=(ach[0], ach[1], date_str, category))
            
            # İstatistik güncelle
            total_achievements = len(achievements)
            self.stats_label.config(text=f"Toplam {total_achievements} başarım kazanıldı")
            
        except Exception as e:
            logging.error(f"Başarımlar yüklenirken hata: {e}")

class MainDashboardWindow(BaseWindow):
    """Ana kontrol paneli."""
    
    def __init__(self, master=None, app_instance=None):
        super().__init__(master, "Kognita - Ana Panel", "900x700", resizable=True)
        self.app_instance = app_instance
        
        self._create_dashboard_interface()
        self._load_dashboard_data()
        
        self.add_action_buttons([
            {'text': 'Kapat', 'command': self.destroy, 'style': 'TButton'}
        ])
        
        # Otomatik yenileme (5 dakikada bir)
        self.after(300000, self._auto_refresh)

    def _create_dashboard_interface(self):
        """Ana panel arayüzü."""
        # Üst özet paneli
        summary_panel = ttk.Frame(self.content_frame, style='Card.TFrame')
        summary_panel.pack(fill='x', pady=(0, 20))
        
        summary_content = ttk.Frame(summary_panel, style='TFrame')
        summary_content.pack(fill='x', padx=20, pady=20)
        
        # Özet başlığı
        summary_title = ttk.Label(summary_content, text="📊 Günlük Özet",
                                 font=STYLE_CONFIG["font_h2"])
        summary_title.pack(anchor='w', pady=(0, 10))
        
        # Özet metrikleri
        metrics_frame = ttk.Frame(summary_content, style='TFrame')
        metrics_frame.pack(fill='x')
        
        # Grid düzeni için 4 sütun
        for i in range(4):
            metrics_frame.grid_columnconfigure(i, weight=1)
        
        # Metrik kartları
        self.total_time_label = self._create_metric_card(metrics_frame, "Toplam Süre", "Hesaplanıyor...", 0, 0)
        self.active_apps_label = self._create_metric_card(metrics_frame, "Aktif Uygulama", "Hesaplanıyor...", 0, 1)
        self.top_category_label = self._create_metric_card(metrics_frame, "En Çok Kullanılan", "Hesaplanıyor...", 0, 2)
        self.productivity_score_label = self._create_metric_card(metrics_frame, "Verimlilik Skoru", "Hesaplanıyor...", 0, 3)
        
        # Ana içerik alanı
        content_panel = ttk.Frame(self.content_frame, style='TFrame')
        content_panel.pack(fill='both', expand=True)
        
        # Sol panel - Hızlı eylemler
        left_panel = ttk.LabelFrame(content_panel, text="🚀 Hızlı Eylemler",
                                   style='TLabelframe')
        left_panel.pack(side='left', fill='y', padx=(0, 10), ipadx=10)
        
        left_content = ttk.Frame(left_panel, style='TFrame')
        left_content.pack(fill='both', padx=15, pady=15)
        
        # Hızlı eylem butonları
        action_buttons = [
            ("📈 Detaylı Rapor", lambda: ReportWindow(master=self), 'Accent.TButton'),
            ("🎯 Hedef Yönetimi", lambda: GoalsWindow(master=self), 'TButton'),
            ("📁 Kategori Yönetimi", lambda: CategoryManagementWindow(master=self), 'TButton'),
            ("🔔 Bildirimler", lambda: NotificationHistoryWindow(master=self, app_instance=self.app_instance), 'TButton'),
            ("🏆 Başarımlar", lambda: AchievementWindow(master=self), 'TButton'),
            ("⚙️ Ayarlar", lambda: SettingsWindow(master=self, app_instance=self.app_instance), 'TButton'),
            ("🎯 Odaklanma Başlat", self._start_focus_session, 'Success.TButton')
        ]
        
        for text, command, style in action_buttons:
            btn = ttk.Button(left_content, text=text, command=command, style=style)
            btn.pack(fill='x', pady=3)
        
        # Sağ panel - Son aktiviteler ve durum
        right_panel = ttk.Frame(content_panel, style='TFrame')
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Son aktiviteler
        recent_frame = ttk.LabelFrame(right_panel, text="📝 Son Aktiviteler",
                                     style='TLabelframe')
        recent_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        recent_content = ttk.Frame(recent_frame, style='TFrame')
        recent_content.pack(fill='both', expand=True, padx=15, pady=15)
        
        self.recent_tree = ttk.Treeview(recent_content,
                                       columns=("time", "app", "category", "duration"),
                                       show="headings", height=12)
        
        self.recent_tree.heading("time", text="Zaman")
        self.recent_tree.heading("app", text="Uygulama")
        self.recent_tree.heading("category", text="Kategori")
        self.recent_tree.heading("duration", text="Süre")
        
        self.recent_tree.column("time", width=80)
        self.recent_tree.column("app", width=150)
        self.recent_tree.column("category", width=100)
        self.recent_tree.column("duration", width=80)
        
        recent_scrollbar = ttk.Scrollbar(recent_content, orient="vertical",
                                        command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scrollbar.set)
        
        self.recent_tree.pack(side='left', fill='both', expand=True)
        recent_scrollbar.pack(side='right', fill='y')
        
        # Sistem durumu
        status_frame = ttk.LabelFrame(right_panel, text="🔍 Sistem Durumu",
                                     style='TLabelframe')
        status_frame.pack(fill='x')
        
        status_content = ttk.Frame(status_frame, style='TFrame')
        status_content.pack(fill='x', padx=15, pady=15)
        
        self.status_label = ttk.Label(status_content, text="Durum bilgileri yükleniyor...",
                                     font=STYLE_CONFIG["font_small"])
        self.status_label.pack(anchor='w')

    def _create_metric_card(self, parent, title, value, row, col):
        """Metrik kartı oluşturur."""
        card_frame = ttk.Frame(parent, style='Card.TFrame')
        card_frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        
        # Padding
        card_content = ttk.Frame(card_frame, style='TFrame')
        card_content.pack(fill='both', padx=15, pady=15)
        
        # Başlık
        title_label = ttk.Label(card_content, text=title,
                               font=STYLE_CONFIG["font_small"],
                               foreground=STYLE_CONFIG["text_secondary"])
        title_label.pack(anchor='w')
        
        # Değer
        value_label = ttk.Label(card_content, text=value,
                               font=STYLE_CONFIG["font_h3"])
        value_label.pack(anchor='w', pady=(5, 0))
        
        return value_label

    def _load_dashboard_data(self):
        """Dashboard verilerini yükler."""
        try:
            # Bugünün verilerini al
            today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + datetime.timedelta(days=1)
            
            category_totals, total_duration = analyzer.get_analysis_data(today, tomorrow)
            
            # Metrikleri güncelle
            self.total_time_label.config(text=reporter.format_duration(total_duration))
            
            # Aktif uygulama sayısı
            active_apps = len(category_totals) if category_totals else 0
            self.active_apps_label.config(text=f"{active_apps} uygulama")
            
            # En çok kullanılan kategori
            if category_totals:
                top_category = max(category_totals.items(), key=lambda x: x[1])
                self.top_category_label.config(text=top_category[0])
            else:
                self.top_category_label.config(text="Veri yok")
            
            # Verimlilik skoru (basit hesaplama)
            productivity_score = self._calculate_productivity_score(category_totals, total_duration)
            self.productivity_score_label.config(text=f"{productivity_score}/100")
            
            # Son aktiviteleri yükle
            self._load_recent_activities()
            
            # Sistem durumunu güncelle
            self._update_system_status()
            
        except Exception as e:
            logging.error(f"Dashboard verileri yüklenirken hata: {e}")

    def _calculate_productivity_score(self, category_totals, total_duration):
        """Basit verimlilik skoru hesaplar."""
        if not category_totals or total_duration == 0:
            return 0
        
        # Verimli kategoriler (örnekler)
        productive_categories = ['Work', 'Development', 'Design', 'Education', 'Writing']
        
        productive_time = 0
        for category, duration in category_totals.items():
            if any(prod_cat.lower() in category.lower() for prod_cat in productive_categories):
                productive_time += duration
        
        # Yüzdelik hesaplama
        score = int((productive_time / total_duration) * 100) if total_duration > 0 else 0
        return min(100, score)  # Maksimum 100

    def _load_recent_activities(self):
        """Son aktiviteleri yükler."""
        try:
            self.recent_tree.delete(*self.recent_tree.get_children())
            
            recent_logs = database.get_recent_usage_logs(limit=20)
            
            for log in recent_logs:
                start_time = datetime.datetime.fromtimestamp(log['start_time'])
                time_str = start_time.strftime('%H:%M')
                
                app_name = log['process_name']
                if len(app_name) > 20:
                    app_name = app_name[:17] + "..."
                
                category = database.get_category_for_process(log['process_name'])
                duration = reporter.format_duration(log['duration_seconds'])
                
                self.recent_tree.insert("", "end", values=(time_str, app_name, category, duration))
                
        except Exception as e:
            logging.error(f"Son aktiviteler yüklenirken hata: {e}")
            # Hata durumunda placeholder göster
            self.recent_tree.insert("", "end", values=("--", "Veri yüklenemedi", "--", "--"))

    def _update_system_status(self):
        """Sistem durumunu günceller."""
        try:
            # Basit sistem durumu bilgileri
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Toplam kayıt sayısı
                cursor.execute("SELECT COUNT(*) FROM usage_logs")
                total_logs = cursor.fetchone()[0]
                
                # Son 24 saatteki aktivite
                yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
                cursor.execute("SELECT COUNT(*) FROM usage_logs WHERE start_time > ?", 
                              (yesterday.timestamp(),))
                recent_activity = cursor.fetchone()[0]
                
                # Toplam uygulama sayısı
                cursor.execute("SELECT COUNT(DISTINCT process_name) FROM usage_logs")
                total_apps = cursor.fetchone()[0]
            
            status_text = (f"• Toplam {total_logs:,} kullanım kaydı\n"
                          f"• Son 24 saatte {recent_activity} aktivite\n"
                          f"• {total_apps} farklı uygulama takip ediliyor")
            
            self.status_label.config(text=status_text)
            
        except Exception as e:
            logging.error(f"Sistem durumu güncellenirken hata: {e}")
            self.status_label.config(text="Sistem durumu alınamadı")

    def _start_focus_session(self):
        """Odaklanma oturumu başlatır."""
        if self.app_instance and hasattr(self.app_instance, 'start_focus_session_flow'):
            self.app_instance.start_focus_session_flow()
        else:
            messagebox.showinfo("Bilgi", "Odaklanma oturumu özelliği kullanılamıyor.", parent=self)

    def _auto_refresh(self):
        """Otomatik veri yenileme."""
        try:
            self._load_dashboard_data()
            # 5 dakika sonra tekrar çalıştır
            self.after(300000, self._auto_refresh)
        except:
            # Hata olursa 10 dakika sonra tekrar dene
            self.after(600000, self._auto_refresh)

# Yardımcı fonksiyonlar ve sınıflar

def show_error_dialog(parent, title, message):
    """Gelişmiş hata dialogu gösterir."""
    error_window = BaseWindow(parent, f"Hata - {title}", "400x300")
    
    content = ttk.Frame(error_window.content_frame, style='TFrame')
    content.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Hata ikonu (Unicode)
    icon_label = ttk.Label(content, text="⚠️", font=("Segoe UI", 32))
    icon_label.pack(pady=(0, 15))
    
    # Başlık
    title_label = ttk.Label(content, text=title, font=STYLE_CONFIG["font_h2"])
    title_label.pack(pady=(0, 10))
    
    # Mesaj
    message_text = tk.Text(content, wrap=tk.WORD, height=6, 
                          font=STYLE_CONFIG["font_normal"],
                          bg=STYLE_CONFIG["bg_card"],
                          fg=STYLE_CONFIG["text_primary"],
                          relief='flat', bd=0)
    message_text.pack(fill='both', expand=True, pady=(0, 15))
    message_text.insert('1.0', message)
    message_text.config(state='disabled')
    
    # Kapat butonu
    error_window.add_action_buttons([
        {'text': 'Kapat', 'command': error_window.destroy, 'style': 'Accent.TButton'}
    ])

def show_success_dialog(parent, title, message):
    """Başarı dialogu gösterir."""
    success_window = BaseWindow(parent, f"Başarılı - {title}", "350x250")
    
    content = ttk.Frame(success_window.content_frame, style='TFrame')
    content.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Başarı ikonu
    icon_label = ttk.Label(content, text="✅", font=("Segoe UI", 32))
    icon_label.pack(pady=(0, 15))
    
    # Başlık
    title_label = ttk.Label(content, text=title, font=STYLE_CONFIG["font_h2"])
    title_label.pack(pady=(0, 10))
    
    # Mesaj
    message_label = ttk.Label(content, text=message, 
                             font=STYLE_CONFIG["font_normal"],
                             wraplength=300, justify='center')
    message_label.pack(pady=(0, 15))
    
    # Kapat butonu
    success_window.add_action_buttons([
        {'text': 'Tamam', 'command': success_window.destroy, 'style': 'Success.TButton'}
    ])

# Ana uygulama başlatma fonksiyonu
def initialize_ui():
    """UI sistemini başlatır."""
    try:
        apply_global_styles()
        logging.info("UI başarıyla başlatıldı")
        return True
    except Exception as e:
        logging.error(f"UI başlatılırken hata: {e}")
        return False

# Modül yüklendiğinde çalışacak
if __name__ == "__main__":
    # Test için basit bir demo
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle
    
    apply_global_styles()
    
    # Test penceresi
    test_window = MainDashboardWindow(master=root)
    test_window.mainloop()
