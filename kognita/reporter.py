# kognita/reporter.py

import datetime
import logging
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from . import analyzer

def format_duration(seconds):
    """Saniyeyi okunabilir bir saat/dakika formatına çevirir."""
    if not seconds: return "0s"
    seconds = int(seconds) # Küsüratı yuvarla
    if seconds < 60: return f"{seconds}s"
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

    persona = analyzer.define_user_persona(category_totals, total_duration)
    persona_text = f"✨ Dijital Personanız: {persona}"

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

def get_report_as_string(category_totals, total_duration): # start_date, end_date parametreleri kaldırıldı, get_report_data'dan gelecek
    """
    Konsol veya metin tabanlı çıktılar için raporu formatlı bir string olarak üretir.
    Bu fonksiyon artık test ve loglama amaçlıdır.
    """
    # category_totals ve total_duration zaten dışarıdan geliyor
    
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

def get_chart_data(category_totals, total_duration):
    """Grafikler için etiket ve değer listelerini döndürür."""
    if not category_totals or total_duration == 0:
        return [], []

    labels = []
    sizes = []
    
    sorted_categories = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
    
    top_n = 5
    other_time = 0
    
    for i, (category, time_in_seconds) in enumerate(sorted_categories):
        if i < top_n:
            labels.append(category)
            sizes.append(time_in_seconds)
        else:
            other_time += time_in_seconds
            
    if other_time > 0:
        labels.append("Diğer")
        sizes.append(other_time)
            
    return labels, sizes

def create_pdf_report(file_path, start_date, end_date):
    """Belirtilen tarih aralığı için kullanım verilerini PDF olarak dışa aktarır."""
    try:
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Başlık
        report_title = f"Kognita Dijital Ayak İzi Raporu\n{start_date.strftime('%Y-%m-%d %H:%M')} - {end_date.strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(report_title, styles['h1']))
        story.append(Spacer(1, 0.2 * inch))

        category_totals, total_duration = analyzer.get_analysis_data(start_date, end_date)
        
        if not category_totals or total_duration == 0:
            story.append(Paragraph("Bu periyotta analiz edilecek veri bulunamadı.", styles['Normal']))
            doc.build(story)
            return True, None

        # Toplam Süre ve Persona
        story.append(Paragraph(f"Toplam Aktif Süre: {format_duration(total_duration)}", styles['h2']))
        persona_text, _ = get_report_data(category_totals, total_duration)
        story.append(Paragraph(persona_text, styles['h3']))
        story.append(Spacer(1, 0.2 * inch))

        # Kategori Detayları Tablosu
        story.append(Paragraph("Kategori Kullanım Detayları:", styles['h2']))
        table_data = [["Kategori", "Harcanan Süre", "Yüzde"]]
        
        sorted_categories = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
        for category, time_in_seconds in sorted_categories:
            percentage = (time_in_seconds / total_duration) * 100 if total_duration > 0 else 0
            table_data.append([
                category,
                format_duration(time_in_seconds),
                f"{percentage:.1f}%"
            ])
        
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1*inch]) # Sütun genişliklerini ayarla
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4CAF50')), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'), 
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8F8F8')), # Alternatif renk
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5 * inch))

        # Diğer Analizler
        story.append(Paragraph("Diğer Analizler:", styles['h2']))

        # Günlük Ortalama Kullanım
        daily_avg_data = analyzer.get_daily_average_usage_by_category(num_days=7)
        story.append(Paragraph("Son 7 Günlük Kategori Ortalama Kullanım:", styles['h3']))
        if daily_avg_data:
            daily_avg_table_data = [["Kategori", "Günlük Ortalama Süre"]]
            sorted_data = sorted(daily_avg_data.items(), key=lambda item: item[1], reverse=True)
            for category, duration in sorted_data:
                daily_avg_table_data.append([category, format_duration(duration)])
            
            daily_avg_table = Table(daily_avg_table_data, colWidths=[2.5*inch, 2*inch])
            daily_avg_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            story.append(daily_avg_table)
        else:
            story.append(Paragraph("Günlük ortalama kullanım verisi bulunamadı.", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # En Verimli Gün
        most_productive_day, max_time = analyzer.get_most_productive_day()
        story.append(Paragraph("En Verimli Gün (Son 30 Gün):", styles['h3']))
        if most_productive_day != "Yeterli Veri Yok":
            story.append(Paragraph(f"En verimli gününüz: {most_productive_day} (Toplam verimli süre: {format_duration(max_time)})", styles['Normal']))
        else:
            story.append(Paragraph("En verimli gün verisi için yeterli aktif kullanım yok.", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

        # Kullanım Önerileri
        suggestions = analyzer.get_user_suggestions(category_totals, total_duration)
        story.append(Paragraph("Kişiselleştirilmiş Öneriler:", styles['h2']))
        for suggestion in suggestions:
            story.append(Paragraph(f"• {suggestion}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        logging.info(f"PDF raporu '{file_path}' adresine başarıyla oluşturuldu.")
        return True, None
    except Exception as e:
        logging.error(f"PDF raporu oluşturulurken hata: {e}", exc_info=True)
        return False, str(e)