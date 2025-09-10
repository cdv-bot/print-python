from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from print_handler import PrintHandler
from urllib.parse import urlparse, parse_qs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrinterHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.print_handler = PrintHandler()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Xử lý GET request"""
        parsed_path = urlparse(self.path)
        
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if parsed_path.path == '/printers':
            try:
                printers = self.print_handler.get_available_printers()
                response = {
                    "status": "success",
                    "printers": printers,
                    "count": len(printers)
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                logger.info(f"Sent {len(printers)} printers via HTTP")
            except Exception as e:
                error_response = {
                    "status": "error",
                    "message": str(e)
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                logger.error(f"Error getting printers: {e}")
        elif parsed_path.path == '/print-test':
            import asyncio
            asyncio.run(self.handle_print_test(parsed_path.query))
        else:
            error_response = {
                "status": "error",
                "message": "Endpoint not found"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_POST(self):
        """Xử lý POST request"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/print-content':
            import asyncio
            asyncio.run(self.handle_print_content())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                "status": "error",
                "message": "Endpoint not found"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Xử lý OPTIONS request cho CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    async def handle_print_test(self, query_string):
        """Xử lý print test request"""
        try:
            # Parse query parameters
            params = parse_qs(query_string)
            printer_name = params.get('printer', [''])[0]
            
            if not printer_name:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {
                    "status": "error",
                    "message": "Missing printer parameter"
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return
                
            # Thực hiện in test với await
            result = await self.print_handler.print_test_page(printer_name)
            success = result.get('success', False)
            
            # Gửi phản hồi
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'success' if success else 'error',
                'message': result.get('message', 'Print test completed'),
                'printer': printer_name
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            logger.info(f"Print test {'successful' if success else 'failed'} for printer: {printer_name}")
            
        except Exception as e:
            logger.error(f"Error in print test: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                "status": "error",
                "message": "Internal Server Error"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    async def handle_print_content(self):
        """Xử lý print content request"""
        try:
            # Đọc POST data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            printer_name = data.get('printer')
            content = data.get('content')
            content_type = data.get('content_type', 'text')
            
            if not printer_name:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {
                    "status": "error",
                    "message": "Missing printer parameter"
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return
            
            if not content:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {
                    "status": "error",
                    "message": "Missing content parameter"
                }
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return
                
            # Thực hiện in nội dung với await
            options = {'printer': printer_name, 'content_type': content_type}
            success = await self.print_handler.print_content(content, options)
            
            # Gửi phản hồi
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'status': 'success' if success else 'error',
                'message': f'Content sent to {printer_name}' if success else 'Failed to print content',
                'printer': printer_name
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            logger.info(f"Print content {'successful' if success else 'failed'} for printer: {printer_name}")
            
        except Exception as e:
            logger.error(f"Error in print content: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                "status": "error",
                "message": "Internal Server Error"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override để sử dụng logger của chúng ta"""
        logger.info(f"{self.address_string()} - {format % args}")

def run_server(port=8081):
    """Chạy HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, PrinterHTTPHandler)
    logger.info(f"HTTP Printer Server running on port {port}")
    logger.info(f"Access printers at: http://localhost:{port}/printers")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()