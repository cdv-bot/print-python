#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Print Server - Entry Point
Tương thích với Windows 7
"""

import sys
import os
import threading
import time
from http_printer_server import run_server

def main():
    """
    Entry point chính của ứng dụng
    """
    print("🖨️  Python Print Server")
    print("📋 Tương thích Windows 7")
    print("🚀 Đang khởi động server...")
    
    try:
        print("✅ Server đang khởi động...")
        print("🌐 HTTP Server: http://localhost:8081")
        print("📡 API Endpoints:")
        print("   - GET /printers - Lấy danh sách máy in")
        print("   - POST /print-content - Gửi lệnh in")
        print("   - GET /print-test - Test in")
        print("")
        print("⚠️  Nhấn Ctrl+C để dừng server")
        print("="*50)
        
        # Chạy server
        run_server(8081)
        
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng server...")
        print("✅ Server đã dừng thành công!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Lỗi khởi động server: {e}")
        input("Nhấn Enter để thoát...")
        sys.exit(1)

if __name__ == "__main__":
    # Đảm bảo encoding UTF-8 cho Windows 7
    if sys.platform.startswith('win'):
        import locale
        try:
            locale.setlocale(locale.LC_ALL, 'Vietnamese_Vietnam.1258')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except:
                pass
    
    main()