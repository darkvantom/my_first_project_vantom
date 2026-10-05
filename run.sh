#!/bin/bash
# ملف التشغيل السريع
cd "$(dirname "$0")"
source env/bin/activate
python3 analyzer.py
deactivate
