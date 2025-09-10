#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Print Client
Kết nối trực tiếp với Node.js WebSocket server để xử lý in ấn
"""

import asyncio
import websockets
import json
import logging
import sys
import os
from datetime import datetime
from print_handler import PrintHandler

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('websocket_client.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebSocketPrintClient:
    def __init__(self, server_url="ws://localhost:3001"):
        self.server_url = server_url
        self.print_handler = PrintHandler()
        self.websocket = None
        self.running = False
        
    async def connect(self):
        """Kết nối tới WebSocket server"""
        try:
            logger.info(f"Đang kết nối tới {self.server_url}...")
            self.websocket = await websockets.connect(self.server_url)
            self.running = True
            logger.info("✅ Kết nối WebSocket thành công!")
            return True
        except Exception as e:
            logger.error(f"❌ Lỗi kết nối WebSocket: {e}")
            return False
    
    async def disconnect(self):
        """Ngắt kết nối WebSocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Đã ngắt kết nối WebSocket")
    
    async def send_message(self, message):
        """Gửi tin nhắn qua WebSocket"""
        try:
            if self.websocket:
                await self.websocket.send(json.dumps(message))
                logger.debug(f"📤 Gửi: {message}")
        except Exception as e:
            logger.error(f"❌ Lỗi gửi tin nhắn: {e}")
    
    async def handle_message(self, message_data):
        """Xử lý tin nhắn từ server"""
        try:
            message_type = message_data.get('type')
            
            if message_type == 'getPrinters':
                await self.handle_get_printers()
            elif message_type == 'printTest':
                await self.handle_print_test(message_data)
            elif message_type == 'print':
                await self.handle_print(message_data)
            else:
                logger.warning(f"⚠️ Loại tin nhắn không xác định: {message_type}")
                
        except Exception as e:
            logger.error(f"❌ Lỗi xử lý tin nhắn: {e}")
    
    async def handle_get_printers(self):
        """Xử lý yêu cầu lấy danh sách máy in"""
        try:
            printers = self.print_handler.get_available_printers()
            default_printer = self.print_handler.default_printer
            
            # Đánh dấu máy in mặc định
            for printer in printers:
                printer['isDefault'] = (printer['name'] == default_printer)
            
            response = {
                'type': 'getPrinters',
                'success': True,
                'data': {
                    'printers': printers,
                    'count': len(printers),
                    'defaultPrinter': default_printer
                }
            }
            
            await self.send_message(response)
            logger.info(f"📋 Gửi danh sách {len(printers)} máy in")
            
        except Exception as e:
            logger.error(f"❌ Lỗi lấy danh sách máy in: {e}")
            await self.send_message({
                'type': 'getPrinters',
                'success': False,
                'error': str(e)
            })
    
    async def handle_print_test(self, message_data):
        """Xử lý yêu cầu in test"""
        try:
            printer_name = message_data.get('printer')
            result = await self.print_handler.print_test_page(printer_name)
            
            response = {
                'type': 'printTest',
                'success': result.get('success', False),
                'data': result
            }
            
            if result.get('success'):
                logger.info(f"🖨️ In test thành công trên {printer_name or 'máy in mặc định'}")
            else:
                logger.error(f"❌ In test thất bại: {result.get('message')}")
            
            await self.send_message(response)
            
        except Exception as e:
            logger.error(f"❌ Lỗi in test: {e}")
            await self.send_message({
                'type': 'printTest',
                'success': False,
                'error': str(e)
            })
    
    async def handle_print(self, message_data):
        """Xử lý yêu cầu in nội dung"""
        try:
            content = message_data.get('content', '')
            printer_name = message_data.get('printer')
            options = message_data.get('options', {})
            
            # Mặc định in dạng text
            if 'content_type' not in options:
                options['content_type'] = 'text'
            
            success = await self.print_handler.print_content(content, {
                **options,
                'printer': printer_name
            })
            
            response = {
                'type': 'print',
                'success': success,
                'data': {
                    'printer': printer_name or self.print_handler.default_printer,
                    'content_length': len(content),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if success:
                logger.info(f"🖨️ In thành công {len(content)} ký tự trên {printer_name or 'máy in mặc định'}")
            else:
                logger.error("❌ In thất bại")
                response['error'] = 'Print failed'
            
            await self.send_message(response)
            
        except Exception as e:
            logger.error(f"❌ Lỗi in: {e}")
            await self.send_message({
                'type': 'print',
                'success': False,
                'error': str(e)
            })
    
    async def listen(self):
        """Lắng nghe tin nhắn từ server"""
        try:
            while self.running and self.websocket:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=1.0
                    )
                    
                    logger.debug(f"📥 Nhận: {message}")
                    message_data = json.loads(message)
                    await self.handle_message(message_data)
                    
                except asyncio.TimeoutError:
                    # Timeout bình thường, tiếp tục lắng nghe
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("🔌 Kết nối WebSocket bị đóng")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Lỗi parse JSON: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Lỗi lắng nghe: {e}")
        finally:
            self.running = False
    
    async def run(self):
        """Chạy client"""
        logger.info("🚀 Khởi động WebSocket Print Client...")
        
        while True:
            try:
                if await self.connect():
                    await self.listen()
                else:
                    logger.error("❌ Không thể kết nối, thử lại sau 5 giây...")
                    await asyncio.sleep(5)
                    continue
                    
            except KeyboardInterrupt:
                logger.info("🛑 Nhận tín hiệu dừng...")
                break
            except Exception as e:
                logger.error(f"❌ Lỗi không mong muốn: {e}")
                await asyncio.sleep(5)
            finally:
                await self.disconnect()
                
        logger.info("✅ WebSocket Print Client đã dừng")

async def main():
    """Hàm main"""
    print("🖨️ WebSocket Print Client")
    print("🔌 Kết nối tới Node.js WebSocket Server")
    print("⚠️ Nhấn Ctrl+C để dừng")
    print("="*50)
    
    client = WebSocketPrintClient()
    await client.run()

if __name__ == "__main__":
    # Đảm bảo encoding UTF-8 cho Windows
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