#!/bin/bash
# ============================================
# 🎓 أداة تحليل بيانات الجامعة - الحل النهائي
# متوافقة مع Parrot OS - بدون أي مكتبات خارجية
# ============================================

clear
echo "=========================================="
echo "🎓 أداة تحليل بيانات الجامعة النهائية"
echo "Parrot OS Edition - بدون مكتبات خارجية"
echo "=========================================="
echo ""

# إنشاء مجلد المشروع
PROJECT_DIR="$HOME/university_analyzer"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "📁 مجلد المشروع: $PROJECT_DIR"
echo ""

# ============================================
# إنشاء ملف الأداة الكامل
# ============================================
cat > analyzer.py << 'PYEOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎓 أداة تحليل بيانات الجامعة الكاملة
تعمل بدون أي مكتبات خارجية - Python مدمج فقط
"""

import sqlite3
import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path

class UniversityAnalyzer:
    """محلل بيانات الجامعة"""
    
    def __init__(self, db_path="university.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.history = []
        
    def show_tables(self):
        """عرض كل الجداول"""
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = self.cursor.fetchall()
        
        if not tables:
            print("⚠️ لا توجد جداول في قاعدة البيانات")
            return []
        
        print("\n" + "="*60)
        print("📊 الجداول المتاحة في قاعدة البيانات")
        print("="*60)
        print(f"{'#':<3} {'اسم الجدول':<25} {'الصفوف':<10} {'الأعمدة':<10}")
        print("-"*60)
        
        total_rows = 0
        table_names = []
        
        for i, t in enumerate(tables, 1):
            table_name = t[0]
            table_names.append(table_name)
            
            # عدد الصفوف
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            row_count = self.cursor.fetchone()[0]
            total_rows += row_count
            
            # عدد الأعمدة
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            col_count = len(self.cursor.fetchall())
            
            print(f"{i:<3} {table_name:<25} {row_count:<10,} {col_count:<10}")
        
        print("-"*60)
        print(f"{'':<3} {'المجموع':<25} {total_rows:<10,}")
        print("="*60)
        return table_names
    
    def describe_table(self, table_name):
        """وصف هيكل جدول"""
        self.cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = self.cursor.fetchall()
        
        if not columns:
            print(f"❌ الجدول '{table_name}' غير موجود")
            return
        
        print("\n" + "="*80)
        print(f"📋 هيكل جدول: {table_name}")
        print("="*80)
        print(f"{'العمود':<20} {'النوع':<15} {'NOT NULL':<12} {'مفتاح':<15} {'الافتراضي':<15}")
        print("-"*80)
        
        for col in columns:
            cid, name, type_, not_null, default_val, is_pk = col
            null_str = "نعم" if not_null else "لا"
            key_str = "🔑 PRIMARY KEY" if is_pk else ""
            def_str = str(default_val) if default_val else ""
            print(f"{name:<20} {type_:<15} {null_str:<12} {key_str:<15} {def_str:<15}")
        
        print("="*80)
        
        # عرض المفاتيح الخارجية
        self.cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
        fks = self.cursor.fetchall()
        
        if fks:
            print("\n🔗 المفاتيح الخارجية:")
            print("-"*60)
            for fk in fks:
                print(f"  • {fk[3]} → {fk[2]}({fk[4]})")
            print("-"*60)
    
    def preview_data(self, table_name, limit=10):
        """معاينة البيانات"""
        try:
            self.cursor.execute(f"SELECT * FROM '{table_name}' LIMIT {limit}")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            if not rows:
                print("⚠️ لا توجد بيانات في الجدول")
                return
            
            print(f"\n👁️ معاينة {table_name} (أول {limit} صف):")
            print("="*100)
            
            # طباعة العناوين
            header = " | ".join([col[:15].ljust(15) for col in columns])
            print(header)
            print("-"*100)
            
            # طباعة البيانات
            for row in rows:
                values = []
                for i in range(len(columns)):
                    val = str(row[i])[:15] if row[i] is not None else "NULL"
                    values.append(val.ljust(15))
                print(" | ".join(values))
            
            print("="*100)
            
            # إجمالي الصفوف
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            total = self.cursor.fetchone()[0]
            print(f"📊 إجمالي الصفوف: {total:,}")
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
    
    def quick_stats(self, table_name, column):
        """إحصائيات سريعة لعمود"""
        try:
            # التحقق من وجود العمود
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns_info = self.cursor.fetchall()
            col_exists = any(col[1] == column for col in columns_info)
            
            if not col_exists:
                print(f"❌ العمود '{column}' غير موجود في {table_name}")
                return
            
            print(f"\n📈 إحصائيات {column} من {table_name}:")
            print("="*60)
            print(f"{'الإحصائية':<25} {'القيمة':<20}")
            print("-"*60)
            
            # العدد الإجمالي
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            total = self.cursor.fetchone()[0]
            print(f"{'العدد الإجمالي':<25} {total:<20,}")
            
            # القيم المختلفة
            self.cursor.execute(f"SELECT COUNT(DISTINCT {column}) FROM '{table_name}'")
            distinct = self.cursor.fetchone()[0]
            print(f"{'القيم المختلفة':<25} {distinct:<20,}")
            
            # القيم الفارغة
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}' WHERE {column} IS NULL")
            null_count = self.cursor.fetchone()[0]
            print(f"{'القيم الفارغة':<25} {null_count:<20,}")
            
            # نسبة الفارغة
            null_percentage = (null_count / total * 100) if total > 0 else 0
            print(f"{'نسبة الفارغة %':<25} {null_percentage:<20.1f}%")
            
            # إحصائيات رقمية
            try:
                self.cursor.execute(f"SELECT MIN({column}), MAX({column}), AVG({column}), SUM({column}) FROM '{table_name}'")
                min_val, max_val, avg_val, sum_val = self.cursor.fetchone()
                
                if min_val is not None:
                    print(f"{'أصغر قيمة':<25} {min_val:<20}")
                    print(f"{'أكبر قيمة':<25} {max_val:<20}")
                    print(f"{'المتوسط':<25} {avg_val:<20.2f}")
                    print(f"{'المجموع':<25} {sum_val:<20,.2f}")
            except:
                pass  # العمود ليس رقماً
            
            print("="*60)
            
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
                    print(f"\n🏆 أعلى 5 قيم في {column}:")
                    print("-"*40)
                    print(f"{'القيمة':<20} {'التكرار':<10}")
                    print("-"*40)
                    for value, count in top_values:
                        print(f"{str(value):<20} {count:<10,}")
                    print("-"*40)
            except:
                pass
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
    
    def analyze_table(self, table_name):
        """تحليل شامل لجدول"""
        try:
            print("\n" + "="*60)
            print(f"🔍 التحليل الشامل لجدول: {table_name}")
            print("="*60)
            
            # عدد الصفوف
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            total_rows = self.cursor.fetchone()[0]
            
            # معلومات الأعمدة
            self.cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = self.cursor.fetchall()
            
            print(f"\n📊 المعلومات الأساسية:")
            print(f"  • عدد الصفوف: {total_rows:,}")
            print(f"  • عدد الأعمدة: {len(columns)}")
            
            print(f"\n📋 تحليل الأعمدة:")
            print("-"*60)
            
            for col in columns:
                col_name = col[1]
                col_type = col[2].upper()
                
                print(f"\n📌 {col_name} ({col_type})")
                
                # القيم المختلفة
                self.cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM '{table_name}'")
                distinct_count = self.cursor.fetchone()[0]
                print(f"  ├─ القيم المختلفة: {distinct_count:,}")
                
                # القيم الفارغة
                self.cursor.execute(f"""
                    SELECT COUNT(*) FROM '{table_name}' 
                    WHERE {col_name} IS NULL OR {col_name} = ''
                """)
                null_count = self.cursor.fetchone()[0]
                
                null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
                print(f"  └─ القيم الفارغة: {null_count:,} ({null_percentage:.1f}%)")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
    
    def execute_query(self, query):
        """تنفيذ استعلام SQL"""
        try:
            self.cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = self.cursor.fetchall()
                
                if results:
                    columns = [desc[0] for desc in self.cursor.description]
                    
                    print(f"\n✓ نتائج الاستعلام ({len(results):,} صف):")
                    print("="*100)
                    
                    # العناوين
                    header = " | ".join([col[:15].ljust(15) for col in columns])
                    print(header)
                    print("-"*100)
                    
                    # البيانات (أول 50 صف)
                    for row in results[:50]:
                        values = []
                        for i in range(len(columns)):
                            val = str(row[i])[:15] if row[i] is not None else "NULL"
                            values.append(val.ljust(15))
                        print(" | ".join(values))
                    
                    if len(results) > 50:
                        print(f"... و {len(results) - 50} صف إضافي")
                    
                    print("="*100)
                else:
                    print("⚠️ لا توجد نتائج")
            else:
                self.conn.commit()
                print(f"✓ تم التنفيذ ({self.cursor.rowcount} صف متأثر)")
                
        except Exception as e:
            print(f"❌ خطأ في الاستعلام: {e}")
    
    def export_csv(self, query, filename):
        """تصدير إلى CSV"""
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            # إنشاء مجلد exports
            os.makedirs("exports", exist_ok=True)
            filepath = os.path.join("exports", filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in results:
                    writer.writerow([str(val) if val is not None else "" for val in row])
            
            print(f"✓ تم التصدير إلى: {filepath}")
            print(f"  • عدد الصفوف: {len(results):,}")
            
        except Exception as e:
            print(f"❌ خطأ في التصدير: {e}")
    
    def export_json(self, table_name, filename=None):
        """تصدير إلى JSON"""
        try:
            self.cursor.execute(f"SELECT * FROM '{table_name}'")
            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            
            data = []
            for row in results:
                data.append({columns[i]: row[i] for i in range(len(columns))})
            
            os.makedirs("exports", exist_ok=True)
            if not filename:
                filename = f"{table_name}.json"
            filepath = os.path.join("exports", filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ تم التصدير إلى: {filepath}")
            print(f"  • عدد السجلات: {len(data):,}")
            
        except Exception as e:
            print(f"❌ خطأ في التصدير: {e}")
    
    def backup(self):
        """نسخ احتياطي"""
        try:
            os.makedirs("backups", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join("backups", f"university_backup_{timestamp}.db")
            
            backup_conn = sqlite3.connect(backup_path)
            self.conn.backup(backup_conn)
            backup_conn.close()
            
            # معلومات النسخة
            info = {
                'original_db': self.db_path,
                'backup_date': datetime.now().isoformat(),
                'backup_size': os.path.getsize(backup_path),
            }
            
            info_path = os.path.join("backups", f"backup_info_{timestamp}.json")
            with open(info_path, 'w') as f:
                json.dump(info, f, indent=2)
            
            print(f"✓ تم إنشاء النسخة الاحتياطية:")
            print(f"  • الملف: {backup_path}")
            print(f"  • الحجم: {os.path.getsize(backup_path):,} بايت")
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
    
    def close(self):
        """إغلاق الاتصال"""
        try:
            self.conn.close()
        except:
            pass

def show_help():
    """عرض المساعدة"""
    help_text = """
╔══════════════════════════════════════════════════════════╗
║        🎓 أداة تحليل بيانات الجامعة - الأوامر            ║
╚══════════════════════════════════════════════════════════╝

📊 أوامر العرض:
  show tables              - عرض كل الجداول
  describe <جدول>          - وصف هيكل جدول
  preview <جدول> [عدد]     - معاينة البيانات

📈 أوامر التحليل:
  stats <جدول> <عمود>      - إحصائيات عمود
  analyze <جدول>           - تحليل شامل لجدول

🔍 أوامر الاستعلام:
  query <SQL>              - تنفيذ استعلام مخصص

💾 أوامر التصدير:
  export csv <SQL> <اسم>   - تصدير CSV
  export json <جدول>       - تصدير JSON
  backup                   - نسخة احتياطية

⚙️ أوامر النظام:
  history                  - سجل الأوامر
  clear                    - مسح الشاشة
  help                     - عرض المساعدة
  exit                     - خروج

💡 أمثلة:
  show tables
  preview students 20
  stats students age
  analyze courses
  query SELECT * FROM students WHERE age > 20
  export csv SELECT * FROM students students.csv
  export json students
  backup
"""
    print(help_text)

def main():
    """الدالة الرئيسية"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     🎓 أداة تحليل بيانات الجامعة النهائية              ║")
    print("║     Parrot OS Edition - بدون مكتبات خارجية             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # البحث عن قاعدة البيانات
    db_path = "university.db"
    
    if not os.path.exists(db_path):
        # البحث في أماكن أخرى
        possible_paths = [
            "university.db",
            "database/university.db",
            "db/university.db",
            "data/university.db",
            "../university.db",
        ]
        
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                found = True
                break
        
        if not found:
            db_path = input("📁 أدخل مسار قاعدة البيانات: ").strip()
            
            if not os.path.exists(db_path):
                print("❌ الملف غير موجود!")
                return
    
    # إنشاء المحلل
    print(f"\n✓ تم الاتصال بقاعدة البيانات: {db_path}")
    analyzer = UniversityAnalyzer(db_path)
    
    show_help()
    
    history = []
    
    # الحلقة الرئيسية
    while True:
        try:
            command = input("\n🔍 > ").strip()
            
            if not command:
                continue
            
            history.append(command)
            parts = command.split()
            cmd = parts[0].lower()
            
            # عرض الجداول
            if cmd == 'show':
                analyzer.show_tables()
            
            # وصف جدول
            elif cmd == 'describe':
                if len(parts) > 1:
                    analyzer.describe_table(parts[1])
                else:
                    print("❌ استخدام: describe <جدول>")
            
            # معاينة
            elif cmd == 'preview':
                if len(parts) > 1:
                    limit = int(parts[2]) if len(parts) > 2 else 10
                    analyzer.preview_data(parts[1], limit)
                else:
                    print("❌ استخدام: preview <جدول> [عدد]")
            
            # إحصائيات
            elif cmd == 'stats':
                if len(parts) >= 3:
                    analyzer.quick_stats(parts[1], parts[2])
                else:
                    print("❌ استخدام: stats <جدول> <عمود>")
            
            # تحليل
            elif cmd == 'analyze':
                if len(parts) > 1:
                    analyzer.analyze_table(parts[1])
                else:
                    print("❌ استخدام: analyze <جدول>")
            
            # استعلام
            elif cmd == 'query':
                if len(command) > 6:
                    analyzer.execute_query(command[6:])
                else:
                    print("❌ استخدام: query <SQL>")
            
            # تصدير CSV
            elif cmd == 'export':
                if len(parts) >= 3:
                    export_type = parts[1]
                    
                    if export_type == 'csv':
                        # export csv <SQL> <filename>
                        remainder = command[11:].rsplit(' ', 1)
                        if len(remainder) == 2:
                            analyzer.export_csv(remainder[0], remainder[1])
                        else:
                            print("❌ استخدام: export csv <SQL> <اسم الملف>")
                    
                    elif export_type == 'json':
                        # export json <table> [filename]
                        table_name = parts[2]
                        filename = parts[3] if len(parts) > 3 else None
                        analyzer.export_json(table_name, filename)
                    
                    else:
                        print("❌ نوع تصدير غير معروف")
                else:
                    print("❌ استخدام: export <نوع> <بيانات>")
            
            # نسخ احتياطي
            elif cmd == 'backup':
                analyzer.backup()
            
            # سجل
            elif cmd == 'history':
                print("\n📜 سجل الأوامر:")
                print("-"*50)
                for i, cmd in enumerate(history[-20:], 1):
                    print(f"  {i:2d}. {cmd}")
                print("-"*50)
            
            # مسح
            elif cmd == 'clear':
                os.system('clear')
                show_help()
            
            # مساعدة
            elif cmd == 'help':
                show_help()
            
            # خروج
            elif cmd in ['exit', 'quit']:
                break
            
            # أمر غير معروف
            else:
                print("❌ أمر غير معروف! اكتب help للمساعدة")
                
        except KeyboardInterrupt:
            print("\n\n👋 مع السلامة!")
            break
        except Exception as e:
            print(f"❌ خطأ: {e}")
    
    analyzer.close()
    print("\n👋 شكراً لاستخدامك أداة تحليل بيانات الجامعة!")

if __name__ == "__main__":
    main()
PYEOF

echo "✓ تم إنشاء ملف analyzer.py"
echo ""

# ============================================
# إنشاء ملف التشغيل
# ============================================
cat > run.sh << 'SHEOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 analyzer.py
SHEOF

chmod +x run.sh
chmod +x analyzer.py

echo "✓ تم إنشاء ملف التشغيل run.sh"
echo ""

# ============================================
# إنشاء ملف التعليمات
# ============================================
cat > README.md << 'MDEOF'
# 🎓 أداة تحليل بيانات الجامعة

## 🚀 التشغيل
```bash
./run.sh
