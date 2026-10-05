#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎓 أداة تحليل بيانات الجامعة المتكاملة
مصممة خصيصاً للعمل مع university.db
"""

# ========== استيراد المكتبات ==========
import sqlite3
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# مكتبات خارجية
import pandas as pd
import numpy as np
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter

# ========== تهيئة الأدوات ==========
console = Console()

# مجلدات العمل
BASE_DIR = Path(__file__).parent
BACKUP_DIR = BASE_DIR / "backups"
EXPORT_DIR = BASE_DIR / "exports"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"

# إنشاء المجلدات
for dir_path in [BACKUP_DIR, EXPORT_DIR, REPORT_DIR, LOG_DIR]:
    dir_path.mkdir(exist_ok=True)

# ملف التاريخ
history_file = LOG_DIR / ".analyzer_history"

# ========== الإكمال التلقائي ==========
commands_completer = WordCompleter([
    'show tables', 'show tables detailed', 'describe', 'preview',
    'stats', 'analyze', 'analyze all', 'query', 'export csv',
    'export json', 'export excel', 'export html', 'search student',
    'search course', 'report students', 'report performance',
    'report summary', 'backup', 'history', 'clear', 'help', 'exit'
], ignore_case=True)

# ========== الكلاس الرئيسي ==========
class UniversityAnalyzer:
    """🎓 محلل بيانات الجامعة الشامل"""
    
    def __init__(self, db_path: str = "university.db"):
        """تهيئة الأداة"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.history = []
        self.connect()
        
    def connect(self):
        """الاتصال بقاعدة البيانات"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            
            # تفعيل المفاتيح الخارجية
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            console.print(f"[green]✓ تم الاتصال بقاعدة البيانات: {self.db_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ خطأ في الاتصال: {e}[/red]")
            sys.exit(1)
    
    # ========== وظائف العرض ==========
    def show_tables(self, detailed: bool = False):
        """عرض كل الجداول"""
        try:
            self.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = self.cursor.fetchall()
            
            if not tables:
                console.print("[yellow]⚠️ لا توجد جداول[/yellow]")
                return []
            
            table = Table(
                title="📊 جداول قاعدة البيانات",
                show_lines=True,
                box=box.ROUNDED,
                title_style="bold cyan"
            )
            
            table.add_column("اسم الجدول", style="cyan")
            table.add_column("الأعمدة", justify="center", style="green")
            table.add_column("الصفوف", justify="right", style="yellow")
            
            total_rows = 0
            for t in tables:
                table_name = t[0]
                
                self.cursor.execute(f"PRAGMA table_info('{table_name}')")
                col_count = len(self.cursor.fetchall())
                
                self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = self.cursor.fetchone()[0]
                total_rows += row_count
                
                table.add_row(table_name, str(col_count), f"{row_count:,}")
            
            table.add_row("[bold]المجموع[/bold]", "", f"[bold]{total_rows:,}[/bold]", style="bold")
            console.print(table)
            return [t[0] for t in tables]
            
        except Exception as e:
            console.print(f"[red]❌ خطأ: {e}[/red]")
            return []
    
    def describe_table(self, table_name: str):
        """وصف جدول"""
        try:
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = self.cursor.fetchall()
            
            if not columns:
                console.print(f"[red]❌ الجدول '{table_name}' غير موجود[/red]")
                return
            
            table = Table(
                title=f"📋 هيكل جدول: {table_name}",
                show_lines=True,
                box=box.ROUNDED
            )
            table.add_column("العمود", style="cyan")
            table.add_column("النوع", style="green")
            table.add_column("NOT NULL", justify="center")
            table.add_column("المفتاح", justify="center", style="yellow")
            table.add_column("الافتراضي")
            
            for col in columns:
                cid, name, type_, not_null, default_val, is_pk = col
                null_status = "✓" if not_null else ""
                key_status = "🔑 PRIMARY" if is_pk else ""
                table.add_row(name, type_, null_status, key_status, str(default_val or ""))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]❌ خطأ: {e}[/red]")
    
    def preview_data(self, table_name: str, limit: int = 10):
        """معاينة البيانات"""
        try:
            self.cursor.execute(f"SELECT * FROM '{table_name}' LIMIT {limit}")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            if rows:
                data = [[str(row[i])[:50] if row[i] is not None else "NULL" 
                        for i in range(len(columns))] for row in rows]
                
                console.print(f"\n[bold]👁️ معاينة {table_name} (أول {limit} صف):[/bold]")
                print(tabulate(data, headers=columns, tablefmt='grid', maxcolwidths=30))
                
                self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                total = self.cursor.fetchone()[0]
                console.print(f"[dim]إجمالي الصفوف: {total:,}[/dim]")
            else:
                console.print("[yellow]⚠️ لا توجد بيانات[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ خطأ: {e}[/red]")
    
    # ========== وظائف التحليل ==========
    def quick_stats(self, table_name: str, column: str):
        """إحصائيات سريعة"""
        try:
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns_info = self.cursor.fetchall()
            col_exists = any(col[1] == column for col in columns_info)
            
            if not col_exists:
                console.print(f"[red]❌ العمود '{column}' غير موجود[/red]")
                return
            
            stats_table = Table(
                title=f"📈 إحصائيات {column} من {table_name}",
                show_lines=True,
                box=box.ROUNDED
            )
            stats_table.add_column("الإحصائية", style="cyan")
            stats_table.add_column("القيمة", style="green", justify="right")
            
            # إحصائيات أساسية
            stats_queries = [
                ("العدد الإجمالي", f"SELECT COUNT(*) FROM '{table_name}'"),
                ("القيم المختلفة", f"SELECT COUNT(DISTINCT {column}) FROM '{table_name}'"),
                ("القيم الفارغة", f"SELECT COUNT(*) FROM '{table_name}' WHERE {column} IS NULL"),
                ("نسبة الفارغة %", f"""
                    SELECT ROUND(100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM '{table_name}'), 0), 2) 
                    FROM '{table_name}' WHERE {column} IS NULL
                """)
            ]
            
            # محاولة إضافة إحصائيات رقمية
            try:
                numeric_stats = [
                    ("أصغر قيمة", f"SELECT MIN({column}) FROM '{table_name}'"),
                    ("أكبر قيمة", f"SELECT MAX({column}) FROM '{table_name}'"),
                    ("المتوسط", f"SELECT ROUND(AVG({column}), 2) FROM '{table_name}'"),
                    ("المجموع", f"SELECT ROUND(SUM({column}), 2) FROM '{table_name}'")
                ]
                stats_queries.extend(numeric_stats)
            except:
                pass
            
            for stat_name, query in stats_queries:
                try:
                    self.cursor.execute(query)
                    result = self.cursor.fetchone()[0]
                    if result is None:
                        result = "N/A"
                    elif isinstance(result, float):
                        result = f"{result:,.2f}"
                    elif isinstance(result, int):
                        result = f"{result:,}"
                    stats_table.add_row(stat_name, str(result))
                except:
                    pass
            
            console.print(stats_table)
            
            # أعلى 5 قيم
            try:
                self.cursor.execute(f"""
                    SELECT {column}, COUNT(*) as count 
                    FROM '{table_name}' 
                    WHERE {column} IS NOT NULL
                    GROUP BY {column} 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_values = self.cursor.fetchall()
                
                if top_values:
                    console.print("\n[bold]🏆 أعلى 5 قيم:[/bold]")
                    top_table = Table(show_lines=True)
                    top_table.add_column("القيمة", style="cyan")
                    top_table.add_column("التكرار", style="green", justify="right")
                    
                    for value, count in top_values:
                        top_table.add_row(str(value), f"{count:,}")
                    
                    console.print(top_table)
            except:
                pass
            
        except Exception as e:
            console.print(f"[red]❌ خطأ: {e}[/red]")
    
    def analyze_table(self, table_name: str):
        """تحليل شامل لجدول"""
        try:
            console.print(Panel.fit(
                f"[bold cyan]🔍 التحليل الشامل لجدول {table_name}[/bold cyan]",
                border_style="cyan"
            ))
            
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            total_rows = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = self.cursor.fetchall()
            
            console.print(f"\n📊 [bold]المعلومات الأساسية:[/bold]")
            console.print(f"  • عدد الصفوف: {total_rows:,}")
            console.print(f"  • عدد الأعمدة: {len(columns)}")
            
            console.print(f"\n📋 [bold]تحليل الأعمدة:[/bold]")
            
            for col in columns:
                col_name = col[1]
                col_type = col[2].upper()
                
                console.print(f"\n[bold cyan]  📌 {col_name} ({col_type})[/bold cyan]")
                
                self.cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM '{table_name}'")
                distinct_count = self.cursor.fetchone()[0]
                
                self.cursor.execute(f"""
                    SELECT COUNT(*) FROM '{table_name}' 
                    WHERE {col_name} IS NULL OR {col_name} = ''
                """)
                null_count = self.cursor.fetchone()[0]
                
                null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
                
                console.print(f"    ├─ القيم المختلفة: {distinct_count:,}")
                console.print(f"    └─ القيم الفارغة: {null_count:,} ({null_percentage:.1f}%)")
            
        except Exception as e:
            console.print(f"[red]❌ خطأ: {e}[/red]")
    
    def analyze_database(self):
        """تحليل شامل لقاعدة البيانات"""
        try:
            console.print(Panel.fit(
                "[bold cyan]🎓 التحليل الشامل لقاعدة البيانات[/bold cyan]",
                border_style="cyan"
            ))
            
            tables = self.show_tables()
            
            console.print(f"\n📈 [bold]ملخص الجداول:[/bold]")
            
            summary_table = Table(show_lines=True, box=box.ROUNDED)
            summary_table.add_column("الجدول", style="cyan")
            summary_table.add_column("الصفوف", style="green", justify="right")
            summary_table.add_column("الأعمدة", style="yellow", justify="center")
            
            total_rows = 0
            total_columns = 0
            
            for table_name in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                rows = self.cursor.fetchone()[0]
                
                self.cursor.execute(f"PRAGMA table_info('{table_name}')")
                cols = len(self.cursor.fetchall())
                
                total_rows += rows
                total_columns += cols
                
                summary_table.add_row(table_name, f"{rows:,}", str(cols))
            
            summary_table.add_row(
                "[bold]المجموع[/bold]",
                f"[bold]{total_rows:,}[/bold]",
                f"[bold]{total_columns}[/bold]",
                style="bold"
            )
            
            console.print(summary_table)
            
            # حجم قاعدة البيانات
            db_size = os.path.getsize(self.db_path) / (1024 * 1024)
            console.print(f"\n💾 حجم قاعدة البيانات: {db_size:.2f} MB")
            
        except Exception as e:
            console.print(f"[red]❌ خطأ: {e}[/red]")
    
    # ========== وظائف التصدير ==========
    def export_data(self, query: str, format_type: str = "csv"):
        """تصدير البيانات"""
        try:
            df = pd.read_sql_query(query, self.conn)
            
            if df.empty:
                console.print("[yellow]⚠️ لا توجد بيانات للتصدير[/yellow]")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == "csv":
                filename = EXPORT_DIR / f"export_{timestamp}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
            elif format_type == "json":
                filename = EXPORT_DIR / f"export_{timestamp}.json"
                df.to_json(filename, orient='records', force_ascii=False, indent=2)
            elif format_type == "excel":
                filename = EXPORT_DIR / f"export_{timestamp}.xlsx"
                df.to_excel(filename, index=False)
            elif format_type == "html":
                filename = EXPORT_DIR / f"export_{timestamp}.html"
                df.to_html(filename, index=False)
            
            console.print(f"[green]✓ تم التصدير إلى: {filename}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ خطأ في التصدير: {e}[/red]")
    
    # ========== النسخ الاحتياطي ==========
    def backup_database(self):
        """إنشاء نسخة احتياطية"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BACKUP_DIR / f"university_backup_{timestamp}.db"
            
            backup_conn = sqlite3.connect(backup_path)
            self.conn.backup(backup_conn)
            backup_conn.close()
            
            console.print(f"[green]✓ تم إنشاء النسخة الاحتياطية: {backup_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ خطأ في النسخ الاحتياطي: {e}[/red]")
    
    # ========== المساعدة ==========
    def show_help(self):
        """عرض المساعدة"""
        help_text = """
[bold cyan]🎓 أداة تحليل بيانات الجامعة[/bold cyan]

[bold green]📊 الأوامر الأساسية:[/bold green]
  • show tables - عرض الجداول
  • describe <جدول> - وصف جدول
  • preview <جدول> [عدد] - معاينة البيانات

[bold yellow]📈 أوامر التحليل:[/bold yellow]
  • stats <جدول> <عمود> - إحصائيات عمود
  • analyze <جدول> - تحليل جدول
  • analyze all - تحليل قاعدة البيانات

[bold cyan]💾 أوامر التصدير:[/bold cyan]
  • export csv <SQL> - تصدير CSV
  • export json <جدول> - تصدير JSON
  • export excel <SQL> - تصدير Excel
  • export html <SQL> - تصدير HTML

[bold magenta]⚙️ أوامر النظام:[/bold magenta]
  • query <SQL> - تنفيذ استعلام
  • backup - نسخة احتياطية
  • history - سجل الأوامر
  • clear - مسح الشاشة
  • help - المساعدة
  • exit - خروج

[bold]💡 أمثلة:[/bold]
  • preview students 20
  • stats students age
  • analyze enrollments
  • export csv SELECT * FROM students
  • query SELECT * FROM courses WHERE credits > 3
        """
        console.print(Panel(help_text, border_style="cyan", box=box.ROUNDED))
    
    # ========== الإغلاق ==========
    def close(self):
        """إغلاق الاتصال"""
        try:
            if self.conn:
                self.conn.close()
        except:
            pass

# ========== الدالة الرئيسية ==========
def main():
    """الدالة الرئيسية"""
    
    # شاشة البداية
    console.print(Panel.fit(
        "[bold cyan]🎓 أداة تحليل بيانات الجامعة[/bold cyan]\n"
        "[dim]الإصدار النهائي - متوافقة مع Parrot OS[/dim]",
        border_style="cyan",
        box=box.DOUBLE
    ))
    
    # البحث عن قاعدة البيانات
    db_path = "university.db"
    
    if not os.path.exists(db_path):
        # البحث في المجلدات المجاورة
        possible_paths = [
            "university.db",
            "database/university.db",
            "db/university.db",
            "data/university.db",
            "../university.db",
            "$HOME/university.db"
        ]
        
        for path in possible_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                db_path = expanded_path
                break
        else:
            db_path = prompt(
                "📁 أدخل مسار قاعدة البيانات: ",
                history=FileHistory(str(history_file)),
                auto_suggest=AutoSuggestFromHistory()
            ).strip()
            
            if not os.path.exists(db_path):
                console.print("[red]❌ الملف غير موجود![/red]")
                return
    
    # إنشاء المحلل
    analyzer = UniversityAnalyzer(db_path)
    
    # عرض المساعدة
    analyzer.show_help()
    
    # الحلقة الرئيسية
    while True:
        try:
            command = prompt(
                "\n🔍 > ",
                history=FileHistory(str(history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                completer=commands_completer
            ).strip()
            
            if not command:
                continue
            
            # تسجيل الأمر
            analyzer.history.append({
                'command': command,
                'timestamp': datetime.now().isoformat()
            })
            
            # تحليل الأمر
            parts = command.split()
            cmd = parts[0].lower()
            
            # ========== الأوامر ==========
            if cmd == 'show':
                if len(parts) > 1 and parts[1] == 'tables':
                    analyzer.show_tables()
                else:
                    analyzer.show_tables()
            
            elif cmd == 'describe':
                if len(parts) > 1:
                    analyzer.describe_table(parts[1])
                else:
                    console.print("[red]❌ استخدام: describe <جدول>[/red]")
            
            elif cmd == 'preview':
                if len(parts) > 1:
                    limit = int(parts[2]) if len(parts) > 2 else 10
                    analyzer.preview_data(parts[1], limit)
                else:
                    console.print("[red]❌ استخدام: preview <جدول> [عدد][/red]")
            
            elif cmd == 'stats':
                if len(parts) >= 3:
                    analyzer.quick_stats(parts[1], parts[2])
                else:
                    console.print("[red]❌ استخدام: stats <جدول> <عمود>[/red]")
            
            elif cmd == 'analyze':
                if len(parts) > 1:
                    if parts[1] == 'all':
                        analyzer.analyze_database()
                    else:
                        analyzer.analyze_table(parts[1])
                else:
                    analyzer.analyze_database()
            
            elif cmd == 'query':
                if len(command) > 6:
                    query = command[6:]
                    try:
                        analyzer.cursor.execute(query)
                        if query.strip().upper().startswith('SELECT'):
                            results = analyzer.cursor.fetchall()
                            if results:
                                columns = [desc[0] for desc in analyzer.cursor.description]
                                data = [[row[i] for i in range(len(columns))] for row in results]
                                console.print(f"\n[bold]نتائج الاستعلام:[/bold]")
                                print(tabulate(data, headers=columns, tablefmt='grid', maxcolwidths=30))
                                console.print(f"[dim]عدد النتائج: {len(results):,}[/dim]")
                            else:
                                console.print("[yellow]⚠️ لا توجد نتائج[/yellow]")
                        else:
                            analyzer.conn.commit()
                            console.print(f"[green]✓ تم التنفيذ ({analyzer.cursor.rowcount} صف متأثر)[/green]")
                    except Exception as e:
                        console.print(f"[red]❌ خطأ: {e}[/red]")
            
            elif cmd == 'export':
                if len(parts) >= 3:
                    format_type = parts[1]
                    if format_type in ['csv', 'json', 'excel', 'html']:
                        if format_type == 'json':
                            table_name = parts[2]
                            query = f"SELECT * FROM {table_name}"
                        else:
                            query = ' '.join(parts[2:])
                        analyzer.export_data(query, format_type)
                    else:
                        console.print("[red]❌ صيغة غير مدعومة[/red]")
                else:
                    console.print("[red]❌ استخدام: export <صيغة> <استعلام>[/red]")
            
            elif cmd == 'backup':
                analyzer.backup_database()
            
            elif cmd == 'history':
                if analyzer.history:
                    console.print("\n[bold]📜 سجل الأوامر:[/bold]")
                    for i, entry in enumerate(analyzer.history[-20:], 1):
                        console.print(f"  {i:2d}. {entry['command']}")
                else:
                    console.print("[yellow]⚠️ لا يوجد سجل[/yellow]")
            
            elif cmd == 'clear':
                os.system('clear')
                analyzer.show_help()
            
            elif cmd == 'help':
                analyzer.show_help()
            
            elif cmd in ['exit', 'quit']:
                break
            
            else:
                console.print("[red]❌ أمر غير معروف! اكتب help[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 مع السلامة![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ خطأ: {e}[/red]")
    
    analyzer.close()
    console.print("[green]👋 شكراً لاستخدامك الأداة![/green]")

if __name__ == "__main__":
    main()
