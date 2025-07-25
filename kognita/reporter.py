# kognita/reporter.py

from . import analyzer

def format_duration(seconds):
    """Saniyeyi okunabilir bir saat/dakika formatına çevirir."""
    if not seconds: return "0s"
    if seconds < 60: return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 60: return f"{minutes:.1f} min"
    hours = minutes / 60
    return f"{hours:.2f} saat"

def get_report_data(category_totals, total_duration):
    """
    UI bileşenleri için yapılandırılmış rapor verileri üretir.
    
    Returns:
        tuple: (persona_metni, tablo_verisi_listesi)
    """
    if not category_totals or total_duration == 0:
        return "Bu periyotta görüntülenecek veri yok.", []

    # 1. Persona metnini oluştur
    persona = analyzer.define_user_persona(category_totals, total_duration)
    persona_text = f"✨ Dijital Personanız: {persona}"

    # 2. Tablo verilerini oluştur (liste içinde demetler)
    table_data = []
    sorted_categories = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
    
    for category, time_in_seconds in sorted_categories:
        percentage = (time_in_seconds / total_duration) * 100 if total_duration > 0 else 0
        table_data.append((
            category,
            format_duration(time_in_seconds),
            f"{percentage:.1f}%"
        ))

    return persona_text, table_data

def get_report_as_string(start_date, end_date):
    """
    Konsol veya metin tabanlı çıktılar için raporu formatlı bir string olarak üretir.
    Bu fonksiyon artık test ve loglama amaçlıdır.
    """
    category_totals, total_duration = analyzer.get_analysis_data(start_date, end_date)
    
    report_lines = []
    report_lines.append("="*55)
    report_lines.append(f"      Kognita - Dijital Ayak İzi Raporu")
    report_lines.append("="*55)

    if not category_totals or total_duration == 0:
        report_lines.append("\nAnaliz edilecek yeterli veri bulunamadı.")
    else:
        persona_text, table_data = get_report_data(category_totals, total_duration)
        
        report_lines.append(f"\nToplam Aktif Süre: {format_duration(total_duration)}\n")
        report_lines.append(f"{'Kategori':<20} | {'Harcanan Süre':<18} | {'Yüzde':<10}")
        report_lines.append("-"*55)
        
        for row in table_data:
            report_lines.append(f"{row[0]:<20} | {row[1]:<18} | {row[2]}")
        
        report_lines.append("\n" + "="*55)
        report_lines.append(f" {persona_text}")
    
    report_lines.append("="*55)
    return "\n".join(report_lines)
