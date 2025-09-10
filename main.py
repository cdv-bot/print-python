#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Print Client - Entry Point
Kết nối với Node.js WebSocket Server
"""

import sys
import os
import asyncio
from websocket_print_client import WebSocketPrintClient

async def main():
    """
    Entry point chính của ứng dụng
    """
    print("🖨️  WebSocket Print Client")
    print("🔌 Kết nối với Node.js WebSocket Server")
    print("🚀 Đang khởi động client...")
    
    try:
        print("✅ Client đang khởi động...")
        print("🌐 WebSocket Server: ws://localhost:3001")
        print("📡 Chức năng:")
        print("   - Lấy danh sách máy in")
        print("   - In test page")
        print("   - In nội dung tùy chỉnh")
        print("")
        print("⚠️  Nhấn Ctrl+C để dừng client")
        print("="*50)
        
        # Chạy WebSocket client
        client = WebSocketPrintClient()
        await client.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng client...")
        print("✅ Client đã dừng thành công!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Lỗi khởi động client: {e}")
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

    asyncio.run(main())