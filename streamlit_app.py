"""Streamlit Cloud 入口文件 — 自动加载 src/dashboard.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# 直接执行 src/dashboard.py
exec(open(os.path.join(os.path.dirname(__file__), "src", "dashboard.py"), encoding="utf-8").read())
