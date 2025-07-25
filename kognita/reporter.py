# kognita/reporter.py

from . import analyzer
import argparse

def format_duration(seconds):
    """Formats seconds into a human-readable string (e.g., 1.2 hours, 45.3 min)."""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "0s"
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f} min"
    hours = minutes / 60
    return f"{hours:.2f} saat"

def get_report_as_string(category_totals, total_duration, days=1):
    """
    Generates a formatted text report from pre-calculated analysis data.
    """
    report_lines = []
    report_lines.append("=" * 55)
    report_lines.append(f"   Kognita - Dijital Ayak İzi Raporunuz")
    report_lines.append(f"             (Son {days} Gün)")
    report_lines.append("=" * 55)

    if not category_totals or total_duration == 0:
        report_lines.append("\nBu periyot için rapor oluşturulacak veri yok.")
    else:
        report_lines.append(f"\nToplam Aktif Süre: {format_duration(total_duration)}\n")
        report_lines.append(f"{'Kategori':<20} | {'Harcanan Süre':<18} | {'Yüzde':<10}")
        report_lines.append("-" * 55)
        
        sorted_categories = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
        
        for category, time_in_seconds in sorted_categories:
            percentage = (time_in_seconds / total_duration) * 100
            report_lines.append(f"{category:<20} | {format_duration(time_in_seconds):<18} | {percentage:.1f}%")
        
        persona = analyzer.define_user_persona(category_totals, total_duration)
        report_lines.append("\n" + "=" * 55)
        report_lines.append(f" ✨ Dijital Personanız: {persona}")
    
    report_lines.append("=" * 55)
    return "\n".join(report_lines)

if __name__ == '__main__':
    # Bu blok, modülün doğrudan çalıştırıldığında test amaçlı kullanılır.
    # Gerçek uygulamada bu kısım çalışmaz.
    import datetime
    
    print("Reporter modülü test ediliyor...")
    parser = argparse.ArgumentParser(description="Kognita için test aktivite raporu oluştur.")
    parser.add_argument(
        '-d', '--days', 
        type=int, 
        default=1, 
        help='Raporun kapsayacağı geçmiş gün sayısı (varsayılan: 1)'
    )
    args = parser.parse_args()
    
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=args.days)
    
    # Test için analiz verilerini çek
    test_category_totals, test_total_duration = analyzer.get_analysis_data(start_date, end_date)
    
    # Raporu oluştur ve yazdır
    report_string = get_report_as_string(test_category_totals, test_total_duration, days=args.days)
    print(report_string)

