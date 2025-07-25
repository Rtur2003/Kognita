# kognita/reporter.py

from . import analyzer
import argparse

def format_duration(seconds):
    """Formats seconds into a human-readable string (hours and minutes)."""
    if seconds < 60: return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 60: return f"{minutes:.1f} min"
    hours = minutes / 60
    return f"{hours:.2f} hours"

def get_report_as_string(days=1):
    """Generates the report and returns it as a formatted string."""
    category_totals, total_duration = analyzer.get_analysis_data(days=days)
    
    report_lines = []
    report_lines.append("="*55)
    report_lines.append(f"      Kognita - Your Digital Footprint Report")
    report_lines.append(f"                   (Last {days} Day(s))")
    report_lines.append("="*55)

    if not category_totals or total_duration == 0:
        report_lines.append("\nNot enough data to generate a report.")
        report_lines.append("\nHint: Let Kognita run for a while to collect data.")
    else:
        report_lines.append(f"\nTotal Active Time: {format_duration(total_duration)}\n")
        report_lines.append(f"{'Category':<20} | {'Time Spent':<18} | {'Percentage':<10}")
        report_lines.append("-"*55)
        
        sorted_categories = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)
        for category, time_in_seconds in sorted_categories:
            percentage = (time_in_seconds / total_duration) * 100
            report_lines.append(f"{category:<20} | {format_duration(time_in_seconds):<18} | {percentage:.1f}%")
        
        persona = analyzer.define_user_persona(category_totals, total_duration)
        report_lines.append("\n" + "="*55)
        report_lines.append(f" ✨ Your Digital Persona: {persona}")
    
    report_lines.append("="*55)
    return "\n".join(report_lines)

def generate_report(days=1):
    """Generates and prints a formatted usage report to the console for testing."""
    report_string = get_report_as_string(days=days)
    print(report_string)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a Kognita activity report.")
    parser.add_argument(
        '-d', '--days', 
        type=int, 
        default=1, 
        help='Number of past days to include in the report (default: 1)'
    )
    args = parser.parse_args()
    
    generate_report(days=args.days)