# kognita/ui.py

import tkinter as tk
from tkinter import ttk, messagebox, Listbox, StringVar, Frame, Label, Entry, Button, filedialog
import datetime
import os
import sys
from PIL import Image, ImageTk
import logging

# Yerel modülleri içe aktar
from . import analyzer, database, reporter
from .achievement_checker import ACHIEVEMENTS
from .utils import resource_path

# Matplotlib import'larını try-except bloğuna alarak opsiyonel hale getirelim
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# --- STİL YAPILANDIRMASI ---
STYLE_CONFIG = {
    "font_normal": ("Segoe UI", 10),
    "font_bold": ("Segoe UI", 11, "bold"),
    "font_title": ("Segoe UI Light", 22),
    "font_header": ("Segoe UI Semibold", 12),
    "header_bg": "#2c3e50",
    "header_fg": "#ecf0f1",
    "bg_color": "#FDFEFE",
    "footer_bg": "#F4F6F7",
    "accent_color": "#3498db",
    "danger_color": "#e74c3c",
    "success_color": "#2ecc71",
    "text_color": "#34495e",
    "border_color": "#bdc3c7",
}

class BaseWindow(tk.Toplevel):
    """Tüm pencereler için temel şablonu (header, main, footer) oluşturan sınıf."""
    def __init__(self, master, title, geometry):
        super().__init__(master)
        self.overrideredirect(True)
        self.geometry(geometry)
        self.configure(bg=STYLE_CONFIG["bg_color"])
        
        self.border_frame = Frame(self, bg=STYLE_CONFIG["border_color"], relief='solid', bd=1)
        self.border_frame.pack(fill='both', expand=True, padx=1, pady=1)

        self._drag_start_x = 0
        self._drag_start_y = 0
        
        self.border_frame.grid_rowconfigure(1, weight=1)
        self.border_frame.grid_columnconfigure(0, weight=1)

        self.header_frame = Frame(self.border_frame, bg=STYLE_CONFIG["header_bg"], height=50)
        self.main_frame = Frame(self.border_frame, bg=STYLE_CONFIG["bg_color"], padx=20, pady=20)
        self.footer_frame = Frame(self.border_frame, bg=STYLE_CONFIG["footer_bg"], height=55)
        
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.main_frame.grid(row=1, column=0, sticky="nsew")
        self.footer_frame.grid(row=2, column=0, sticky="ew")
        
        self.footer_frame.pack_propagate(False)

        self.header_frame.bind("<ButtonPress-1>", self.start_drag)
        self.header_frame.bind("<B1-Motion>", self.do_drag)

        self.populate_header(title)

        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
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
        close_button = Button(self.header_frame, text="✕", command=self.destroy, bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"], relief='flat', font=("Segoe UI Symbol", 12), activebackground=STYLE_CONFIG['danger_color'], activeforeground='white')
        close_button.pack(side='right', padx=10, pady=5, fill='y')

        try:
            logo_image = Image.open(resource_path("logo.png")).resize((28, 28), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = Label(self.header_frame, image=self.logo_photo, bg=STYLE_CONFIG["header_bg"])
            logo_label.pack(side='left', padx=(15,10), pady=10)
            logo_label.bind("<ButtonPress-1>", self.start_drag)
            logo_label.bind("<B1-Motion>", self.do_drag)
        except Exception:
            pass

        title_label = Label(self.header_frame, text=title, font=STYLE_CONFIG["font_header"], bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"])
        title_label.pack(side='left', pady=10)
        title_label.bind("<ButtonPress-1>", self.start_drag)
        title_label.bind("<B1-Motion>", self.do_drag)
        
    def center_window(self):
        self.update_idletasks()
        try:
            width = int(self.geometry().split('x')[0])
            height = int(self.geometry().split('x')[1].split('+')[0])
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            self.geometry(f'{width}x{height}+{x}+{y-30}')
        except (ValueError, IndexError):
            pass


class WelcomeWindow(BaseWindow):
    """Uygulama ilk kez çalıştığında gösterilen çok adımlı karşılama sihirbazı."""
    def __init__(self, master, on_close_callback):
        super().__init__(master, "Kognita'ya Hoş Geldiniz", "600x520")
        self.on_close_callback = on_close_callback
        self.current_step = 0
        self.steps = [self.create_step1, self.create_step2, self.create_step3]
        
        self.populate_footer()
        self.show_step()

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_step(self):
        self.clear_main_frame()
        self.steps[self.current_step]()
        self.update_footer_buttons()

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.show_step()

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.show_step()
    
    def finish(self):
        self.on_close_callback()
        self.destroy()

    def populate_footer(self):
        self.prev_button = Button(self.footer_frame, text="< Geri", command=self.prev_step, relief='flat', font=STYLE_CONFIG['font_normal'])
        self.prev_button.pack(side='left', padx=20, pady=10)
        
        self.next_button = Button(self.footer_frame, text="İleri >", command=self.next_step, relief='flat', font=STYLE_CONFIG['font_bold'], bg=STYLE_CONFIG['accent_color'], fg='white')
        self.next_button.pack(side='right', padx=20, pady=10, ipadx=10)

    def update_footer_buttons(self):
        self.prev_button.config(state='normal' if self.current_step > 0 else 'disabled')
        if self.current_step == len(self.steps) - 1:
            self.next_button.config(text="Anladım, Başla!", command=self.finish, bg=STYLE_CONFIG['success_color'])
        else:
            self.next_button.config(text="İleri >", command=self.next_step, bg=STYLE_CONFIG['accent_color'])

    def create_step1(self):
        """Adım 1: Karşılama ve ana görsel."""
        # --- YENİ: Daha profesyonel metinler ---
        Label(self.main_frame, text="Dijital Dünyanızı Anlamlandırın", font=STYLE_CONFIG['font_title'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(5, 10))
        Label(self.main_frame, text="Zamanınızın nereye gittiğini keşfedin ve kontrolü elinize alın.", font=STYLE_CONFIG['font_normal'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(0, 20))

        try:
            image_container = Frame(self.main_frame, bg=STYLE_CONFIG['bg_color'])
            image_container.pack(pady=10, expand=True)

            max_width = 400
            max_height = 300

            original_image = Image.open(resource_path("welcome_illustration.png"))
            original_width, original_height = original_image.size

            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.welcome_photo = ImageTk.PhotoImage(resized_image)
            Label(image_container, image=self.welcome_photo, bg=STYLE_CONFIG['bg_color']).pack()
            
        except Exception as e:
            Label(self.main_frame, text="Kognita, bilgisayar kullanımınızı anlamanıza\nve hedefler belirlemenize yardımcı olur.",
                  font=STYLE_CONFIG['font_normal'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=20)
            logging.warning(f"Hoşgeldin ekranı görseli yüklenemedi: {e}")

    def create_step2(self):
        """Adım 2: Nasıl Çalışır."""
        Label(self.main_frame, text="Temel Özellikler", font=STYLE_CONFIG['font_title'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(10, 25))
        
        # --- YENİ: Daha fayda odaklı metinler ---
        info_texts = [
            ("Akıllı ve Otomatik Takip", "Siz çalışırken Kognita arka planda hangi uygulamayı ne kadar kullandığınızı sessizce ve güvenli bir şekilde kaydeder."),
            ("Anlaşılır Raporlar", "Verilerinizi 'İş', 'Oyun', 'Tasarım' gibi kategorilerde toplar ve kolayca yorumlanabilen grafiklerle size sunar."),
            ("Kişisel Hedefler & Bildirimler", "Belirli kategoriler için günlük kullanım limitleri belirleyin, hedeflerinize ulaştığınızda veya limitinizi aştığınızda bildirim alın.")
        ]
        
        for title, desc in info_texts:
            line_frame = Frame(self.main_frame, bg=STYLE_CONFIG['bg_color'])
            line_frame.pack(fill='x', pady=10, padx=30, anchor='w')
            Label(line_frame, text=f"✓  {title}:", font=STYLE_CONFIG['font_bold'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['accent_color']).pack(anchor='w')
            Label(line_frame, text=desc, font=STYLE_CONFIG['font_normal'], wraplength=450, justify='left', bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(anchor='w', pady=(5,0))

    def create_step3(self):
        """Adım 3: Gizlilik Güvencesi."""
        Label(self.main_frame, text="Gizliliğiniz Önceliğimizdir", font=STYLE_CONFIG['font_title'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(10, 25))

        try:
            img = Image.open(resource_path("privacy_icon.png")).resize((80, 80), Image.Resampling.LANCZOS)
            self.privacy_photo = ImageTk.PhotoImage(img)
            Label(self.main_frame, image=self.privacy_photo, bg=STYLE_CONFIG['bg_color']).pack(pady=10)
        except Exception:
             pass

        # --- YENİ: Daha güven veren metin ---
        privacy_text = (
            "Kognita, gizliliğinize saygı duyar. Tüm verileriniz, uygulamanın kurulu olduğu "
            "bilgisayar dışına **asla çıkarılmaz** ve herhangi bir sunucuya gönderilmez. "
            "Yaptığınız her şey **sadece sizin bilgisayarınızda** kalır.\n\n"
            "Uygulama, tuş vuruşlarınızı, ekran görüntülerinizi veya kişisel dosyalarınızı "
            "**asla kaydetmez** ve takip etmez."
        )
        
        # --- DEĞİŞTİ: "-bordercolor" hatasını düzelten yapı ---
        # Önce kenarlık görevi görecek bir Frame oluşturuyoruz.
        border_frame = Frame(self.main_frame, bg=STYLE_CONFIG['border_color'], bd=1)
        border_frame.pack(pady=15, padx=20, fill='x')
        
        # Asıl Label'ı bu Frame'in içine yerleştiriyoruz.
        # Label'ın kenar boşlukları (padx, pady), dışındaki Frame'in rengini (kenarlık rengi) gösterir.
        Label(border_frame, 
              text=privacy_text, 
              font=STYLE_CONFIG['font_normal'], 
              justify='left', 
              bg='#F4F6F7', 
              fg=STYLE_CONFIG['text_color'],
              wraplength=480,
              padx=15, 
              pady=15
        ).pack(fill='x')


class ReportWindow(BaseWindow):
    def __init__(self, master):
        super().__init__(master, "Aktivite Raporu", "850x700")
        self.achievement_icons = {} 

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
        self.tab_achievements = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_overview, text='📊 Genel Bakış')
        self.notebook.add(self.tab_hourly, text='🕒 Saatlik Aktivite')
        self.notebook.add(self.tab_weekly, text='📅 Haftalık Karşılaştırma')
        self.notebook.add(self.tab_achievements, text='🏆 Başarımlar')
        
        Button(self.footer_frame, text="Kapat", command=self.destroy, bg=STYLE_CONFIG['danger_color'], fg='white', font=STYLE_CONFIG['font_bold'], width=10, relief='flat').pack(side='right', padx=15, pady=10)
        
        self.refresh_report()
        self.create_achievements_tab()

    def setup_custom_header(self):
        for widget in self.header_frame.winfo_children():
            if isinstance(widget, Frame):
                widget.destroy()
        
        dropdown_frame = Frame(self.header_frame, bg=STYLE_CONFIG["header_bg"])
        dropdown_frame.pack(side='right', padx=20)
        
        Label(dropdown_frame, text="Rapor Aralığı:", font=STYLE_CONFIG['font_normal'], bg=STYLE_CONFIG["header_bg"], fg=STYLE_CONFIG["header_fg"]).pack(side='left', padx=(0, 5))
        self.time_range_var = StringVar(self)
        time_options = ["Son 24 Saat", "Son 7 Gün", "Son 30 Gün"]
        self.time_range_var.set(time_options[1])
        s = ttk.Style()
        s.configure('Header.TMenubutton', font=STYLE_CONFIG['font_normal'])
        time_menu = ttk.OptionMenu(dropdown_frame, self.time_range_var, time_options[1], *time_options, command=self.refresh_report, style='Header.TMenubutton')
        time_menu.pack(side='left')

        dropdown_frame.bind("<ButtonPress-1>", self.start_drag)
        dropdown_frame.bind("<B1-Motion>", self.do_drag)
        for child in dropdown_frame.winfo_children():
            child.bind("<ButtonPress-1>", self.start_drag)
            child.bind("<B1-Motion>", self.do_drag)

    def get_date_range(self):
        selection = self.time_range_var.get()
        today = datetime.datetime.now()
        if "24 Saat" in selection:
            days = 1
        elif "7 Gün" in selection:
            days = 7
        else:
            days = 30
        return today - datetime.timedelta(days=days), today

    def clear_frame(self, frame):
        for widget in frame.winfo_children(): widget.destroy()

    def refresh_report(self, event=None):
        start_date, end_date = self.get_date_range()
        for tab in [self.tab_overview, self.tab_hourly, self.tab_weekly]: self.clear_frame(tab)
        
        category_totals, total_duration = analyzer.get_analysis_data(start_date, end_date)
        if not category_totals or total_duration == 0:
            for tab in [self.tab_overview, self.tab_hourly, self.tab_weekly]:
                Label(tab, text="\nBu tarih aralığı için yeterli veri bulunamadı.", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=20, expand=True)
        else:
            self.create_overview_tab(category_totals, total_duration)
            self.create_hourly_tab()
            self.create_weekly_tab()

    def create_overview_tab(self, category_totals, total_duration):
        left_frame = Frame(self.tab_overview, bg=STYLE_CONFIG['bg_color']); left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        right_frame = Frame(self.tab_overview, bg=STYLE_CONFIG['bg_color']); right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        fig = Figure(figsize=(5, 4), dpi=100); fig.patch.set_facecolor(STYLE_CONFIG['bg_color'])
        ax = fig.add_subplot(111); ax.set_facecolor(STYLE_CONFIG['bg_color'])
        wedges, texts, autotexts = ax.pie(category_totals.values(), autopct='%1.1f%%', shadow=False, startangle=140, pctdistance=0.85, wedgeprops=dict(width=0.4, edgecolor='w'))
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        ax.axis('equal')
        fig.tight_layout()
        FigureCanvasTkAgg(fig, master=left_frame).get_tk_widget().pack(fill='both', expand=True)

        report_frame = Frame(right_frame, bg=STYLE_CONFIG['bg_color']); report_frame.pack(fill='both', expand=True)
        persona_text, table_data = reporter.get_report_data(category_totals, total_duration)

        Label(report_frame, text=persona_text, font=STYLE_CONFIG['font_bold'], justify='left', bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(0,15), anchor='w')

        style = ttk.Style()
        style.configure("Treeview", font=STYLE_CONFIG['font_normal'], rowheight=28, background=STYLE_CONFIG['bg_color'], fieldbackground=STYLE_CONFIG['bg_color'], foreground=STYLE_CONFIG['text_color'])
        style.configure("Treeview.Heading", font=STYLE_CONFIG['font_bold'])
        style.map('Treeview', background=[('selected', STYLE_CONFIG['accent_color'])])
        
        tree = ttk.Treeview(report_frame, columns=('Category', 'Time', 'Percentage'), show='headings')
        tree.heading('Category', text='Kategori')
        tree.heading('Time', text='Harcanan Süre')
        tree.heading('Percentage', text='Yüzde (%)')
        tree.column('Percentage', anchor='center')
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
    
    def create_achievements_tab(self):
        self.clear_frame(self.tab_achievements)
        
        canvas = tk.Canvas(self.tab_achievements, bg=STYLE_CONFIG['bg_color'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_achievements, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        unlocked_achievements = {row[0]: row for row in database.get_all_unlocked_achievements()}
        
        for ach_id, details in ACHIEVEMENTS.items():
            name, desc, icon_file, _, _ = details
            
            is_unlocked = name in unlocked_achievements
            
            card = Frame(scrollable_frame, bg=STYLE_CONFIG['bg_color'], relief='solid', bd=1, borderwidth=1, highlightbackground=STYLE_CONFIG['border_color'])
            card.pack(fill='x', padx=20, pady=8, ipady=10)
            
            icon_label = Label(card, bg=STYLE_CONFIG['bg_color'])
            icon_label.pack(side='left', padx=(15, 20), pady=10)
            
            text_frame = Frame(card, bg=STYLE_CONFIG['bg_color'])
            text_frame.pack(side='left', fill='x', expand=True)

            try:
                img = Image.open(resource_path(icon_file)).resize((64, 64), Image.Resampling.LANCZOS)
                if not is_unlocked:
                    img = img.convert('LA').convert('RGBA')
                
                self.achievement_icons[ach_id] = ImageTk.PhotoImage(img)
                icon_label.config(image=self.achievement_icons[ach_id])
            except Exception as e:
                icon_label.config(text="🏆", font=("Segoe UI Symbol", 24))
                logging.warning(f"Başarım ikonu yüklenemedi '{icon_file}': {e}")
            
            name_label = Label(text_frame, text=name, font=STYLE_CONFIG['font_bold'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color'])
            name_label.pack(anchor='w')
            
            desc_label = Label(text_frame, text=desc, font=STYLE_CONFIG['font_normal'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color'], wraplength=550, justify='left')
            desc_label.pack(anchor='w')
            
            if is_unlocked:
                unlocked_date = datetime.datetime.fromtimestamp(unlocked_achievements[name][3]).strftime('%d.%m.%Y')
                date_label = Label(text_frame, text=f"Kazanıldı: {unlocked_date}", font=("Segoe UI", 8), bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['success_color'])
                date_label.pack(anchor='w', pady=(5,0))
            else:
                name_label.config(fg='grey')
                desc_label.config(fg='grey')

class GoalsWindow(BaseWindow):
    def __init__(self, master):
        super().__init__(master, "Hedefleri Yönet", "450x480")
        self.resizable(False, False)

        Label(self.main_frame, text="Mevcut Hedefler:", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(0,5), anchor='w')
        self.goals_listbox = Listbox(self.main_frame, height=8, font=STYLE_CONFIG['font_normal'], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color'], selectbackground=STYLE_CONFIG['accent_color']); self.goals_listbox.pack(fill="x", expand=True)
        Button(self.main_frame, text="Seçili Hedefi Sil", command=self.delete_selected_goal, bg=STYLE_CONFIG["danger_color"], fg='white', relief='flat').pack(pady=5, anchor='e')
        
        ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=15)

        Label(self.main_frame, text="Yeni Hedef Ekle:", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(10,5), anchor='w')
        add_frame = Frame(self.main_frame, bg=STYLE_CONFIG["bg_color"]); add_frame.pack(fill='x')
        
        Label(add_frame, text="Kategori:", bg=STYLE_CONFIG["bg_color"], fg=STYLE_CONFIG['text_color']).grid(row=0, column=0, sticky="w", pady=2)
        self.category_var = StringVar(self)
        categories = database.get_all_categories()
        if "Other" in categories:
            categories.remove("Other")
            categories.append("Other")
        
        self.category_var.set(categories[0] if categories else "Other")
        ttk.OptionMenu(add_frame, self.category_var, categories[0] if categories else "Diğer", *categories).grid(row=0, column=1, sticky="ew", padx=5)

        Label(add_frame, text="Tip:", bg=STYLE_CONFIG["bg_color"], fg=STYLE_CONFIG['text_color']).grid(row=1, column=0, sticky="w", pady=2)
        self.type_var = StringVar(self); self.type_var.set("Max")
        ttk.OptionMenu(add_frame, self.type_var, "Max", "Max", "Min").grid(row=1, column=1, sticky="ew", padx=5)
        
        Label(add_frame, text="Süre (dakika):", bg=STYLE_CONFIG["bg_color"], fg=STYLE_CONFIG['text_color']).grid(row=2, column=0, sticky="w", pady=2)
        self.time_entry = Entry(add_frame, width=10); self.time_entry.grid(row=2, column=1, sticky="w", padx=5)
        add_frame.grid_columnconfigure(1, weight=1)

        Button(self.footer_frame, text="Kapat", command=self.destroy, width=10, relief='flat').pack(side='right', padx=15, pady=10)
        Button(self.footer_frame, text="Hedef Ekle", command=self.add_new_goal, bg=STYLE_CONFIG["success_color"], fg='white', relief='flat').pack(side='right')

        self.refresh_goals_list()

    def refresh_goals_list(self):
        self.goals_listbox.delete(0, tk.END)
        for goal_id, category, goal_type, time_limit in database.get_goals():
            type_tr = "En Fazla" if goal_type == "max" else "En Az"
            self.goals_listbox.insert(tk.END, f"[{goal_id}] {category}: {type_tr} {time_limit} dakika/gün")

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
                if messagebox.askyesno("Onay", f"'{selected.split('] ')[1]}' hedefini silmek istediğinizden emin misiniz?"):
                    database.delete_goal(goal_id)
                    self.refresh_goals_list()
            except Exception as e: messagebox.showerror("Hata", f"Hedef silinemedi: {e}")

class SettingsWindow(BaseWindow):
    def __init__(self, master, app_instance):
        super().__init__(master, "Ayarlar", "400x350")
        self.app = app_instance

        main_padding_frame = Frame(self.main_frame, bg=STYLE_CONFIG['bg_color'])
        main_padding_frame.pack(expand=True, fill='both')

        Label(main_padding_frame, text="Boşta Kalma Eşiği", font=STYLE_CONFIG["font_bold"], bg=STYLE_CONFIG['bg_color'], fg=STYLE_CONFIG['text_color']).pack(pady=(10,2), anchor='w')
        Label(main_padding_frame, text="Bu süreden sonraki aktiviteleriniz kaydedilmez.", font=STYLE_CONFIG["font_normal"], bg=STYLE_CONFIG['bg_color']).pack(pady=(0,5), anchor='w')
        
        current_idle_seconds = self.app.config_manager.get('settings', {}).get('idle_threshold_seconds', 180)
        self.idle_entry = Entry(main_padding_frame, width=15, font=STYLE_CONFIG['font_normal'])
        self.idle_entry.insert(0, current_idle_seconds)
        self.idle_entry.pack(pady=5, anchor='w', ipady=2)

        ttk.Separator(main_padding_frame, orient='horizontal').pack(fill='x', pady=15)
        
        Button(main_padding_frame, text="Uygulama Kategorilerini Yönet", command=lambda: AppManagerWindow(self), relief='flat', bg='#f0f0f0', highlightthickness=1, highlightbackground=STYLE_CONFIG['accent_color']).pack(pady=10, fill='x', ipady=5)
        
        Button(main_padding_frame, text="Verileri Dışa Aktar (CSV)", command=self.export_data_action, relief='flat', bg='#f0f0f0', highlightthickness=1, highlightbackground=STYLE_CONFIG['accent_color']).pack(pady=10, fill='x', ipady=5)

        Button(self.footer_frame, text="Kapat", command=self.destroy, width=10, relief='flat').pack(side='right', padx=15, pady=10)
        Button(self.footer_frame, text="Kaydet", command=self.save_settings_action, bg=STYLE_CONFIG["accent_color"], fg='white', relief='flat').pack(side='right')

    def export_data_action(self):
        """Verileri CSV olarak dışa aktarmak için dosya diyalogunu açar."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyaları", "*.csv"), ("Tüm Dosyalar", "*.*")],
            title="Kognita Veri Raporunu Kaydet",
            initialfile=f"kognita_raporu_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
        )
        if not file_path:
            return

        success, error_message = database.export_all_data_to_csv(file_path)

        if success:
            messagebox.showinfo("Başarılı", f"Tüm veriler başarıyla '{os.path.basename(file_path)}' dosyasına aktarıldı.")
        else:
            messagebox.showerror("Hata", f"Veriler dışa aktarılamadı:\n{error_message}")


    def save_settings_action(self):
        try:
            new_idle_time = int(self.idle_entry.get())
            if new_idle_time < 30:
                messagebox.showwarning("Geçersiz Değer", "Boşta kalma eşiği en az 30 saniye olmalıdır.")
                return

            self.app.config_manager.set('settings.idle_threshold_seconds', new_idle_time)
            self.app.tracker_instance.update_settings(self.app.config_manager.get('settings'))
            
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi. Değişiklikler anında geçerli olacaktır.")
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
        if "Other" in categories:
            categories.remove("Other")
        
        custom_categories = ["Yeni Kategori Oluştur..."] + categories

        if custom_categories:
            self.category_var.set(custom_categories[0])
            self.category_menu = ttk.OptionMenu(action_frame, self.category_var, custom_categories[0], *custom_categories, command=self.handle_new_category)
            self.category_menu.grid(row=0, column=1, padx=5, sticky='ew')
        action_frame.grid_columnconfigure(1, weight=1)

        Button(self.footer_frame, text="Kapat", command=self.destroy, width=10, relief='flat').pack(side='right', padx=15, pady=10)
        Button(self.footer_frame, text="Kategori Ata", command=self.assign_category, bg=STYLE_CONFIG["accent_color"], fg='white', relief='flat').pack(side='right')

        self.refresh_app_list()
    
    def refresh_app_list(self):
        self.app_listbox.delete(0, tk.END)
        apps = database.get_uncategorized_apps()
        if not apps:
            self.app_listbox.insert(tk.END, "Tüm uygulamalar kategorize edilmiş. Harika!")
            self.app_listbox.config(state=tk.DISABLED)
        else:
            self.app_listbox.config(state=tk.NORMAL)
            for app in apps: self.app_listbox.insert(tk.END, app)

    def on_app_select(self, event):
        try: self.selected_app_label.config(text=f"Seçili: {self.app_listbox.get(self.app_listbox.curselection())}")
        except tk.TclError: pass

    def handle_new_category(self, selection):
        if selection == "Yeni Kategori Oluştur...":
            from tkinter.simpledialog import askstring
            new_cat = askstring("Yeni Kategori", "Yeni kategori adını girin:", parent=self)
            if new_cat:
                categories = database.get_all_categories()
                if "Other" in categories: categories.remove("Other")
                if new_cat not in categories:
                    categories.append(new_cat)
                    categories.sort()

                custom_categories = ["Yeni Kategori Oluştur..."] + categories
                
                self.category_menu.destroy()
                self.category_var.set(new_cat)
                self.category_menu = ttk.OptionMenu(self.category_menu.master, self.category_var, new_cat, *custom_categories, command=self.handle_new_category)
                self.category_menu.grid(row=0, column=1, padx=5, sticky='ew')

    def assign_category(self):
        try:
            selected_app = self.app_listbox.get(tk.ACTIVE)
            selected_category = self.category_var.get()

            if not selected_app or self.app_listbox.cget('state') == tk.DISABLED: 
                return messagebox.showwarning("Seçim Yok", "Lütfen bir uygulama seçin.")
            
            if selected_category == "Yeni Kategori Oluştur...":
                return messagebox.showwarning("Kategori Seçimi", "Lütfen geçerli bir kategori seçin veya oluşturun.")

            database.update_app_category(selected_app, selected_category)
            messagebox.showinfo("Başarılı", f"'{selected_app}' uygulaması '{selected_category}' kategorisine atandı.")
            self.refresh_app_list()
            self.selected_app_label.config(text="Uygulama seçin:")
        except Exception as e: messagebox.showerror("Hata", f"Kategori atanamadı: {e}")