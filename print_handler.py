import win32print
import win32api
import win32con
import tempfile
import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class PrintHandler:
    def __init__(self):
        self.default_printer = None
        self._initialize_default_printer()
        
    def _initialize_default_printer(self):
        """Khởi tạo máy in mặc định"""
        try:
            self.default_printer = win32print.GetDefaultPrinter()
            logger.info(f"Máy in mặc định: {self.default_printer}")
        except Exception as e:
            logger.warning(f"Không thể lấy máy in mặc định: {e}")
            
    def get_available_printers(self) -> List[Dict[str, Any]]:
        """Lấy danh sách máy in có sẵn"""
        printers = []
        try:
            printer_enum = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            
            for printer in printer_enum:
                printer_info = {
                    'name': printer[2],
                    'server': printer[1] if printer[1] else 'Local',
                    'status': 'Available'
                }
                
                # Kiểm tra trạng thái máy in
                try:
                    handle = win32print.OpenPrinter(printer[2])
                    printer_status = win32print.GetPrinter(handle, 2)
                    win32print.ClosePrinter(handle)
                    
                    if printer_status['Status'] == 0:
                        printer_info['status'] = 'Ready'
                    else:
                        printer_info['status'] = 'Busy/Error'
                        
                except Exception:
                    printer_info['status'] = 'Unknown'
                    
                printers.append(printer_info)
                
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách máy in: {e}")
            
        return printers
    
    async def print_content(self, content: str, options: Dict[str, Any] = None) -> bool:
        """In nội dung"""
        if options is None:
            options = {}
            
        try:
            # Xác định loại nội dung và phương thức in
            content_type = options.get('content_type', 'text')
            printer_name = options.get('printer', self.default_printer)
            
            if content_type == 'text':
                return await self._print_text(content, printer_name, options)
            elif content_type == 'html':
                return await self._print_html(content, printer_name, options)
            elif content_type == 'pdf':
                return await self._print_pdf(content, printer_name, options)
            elif content_type == 'image':
                return await self._print_image(content, printer_name, options)
            else:
                logger.error(f"Loại nội dung không được hỗ trợ: {content_type}")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi khi in: {e}")
            return False
    
    async def _print_text(self, text: str, printer_name: str, options: Dict[str, Any]) -> bool:
        """In văn bản thuần túy"""
        try:
            # Tạo file tạm thời trong thư mục dự án
            project_dir = os.path.dirname(os.path.abspath(__file__))
            temp_file_path = os.path.join(project_dir, f"temp_print.txt")
            with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                temp_file.write(text)
            
            # In file
            success = await self._print_file(temp_file_path, printer_name, options)
            
            # Xóa file tạm
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
                
            return success
            
        except Exception as e:
            logger.error(f"Lỗi khi in văn bản: {e}")
            return False
    
    async def _print_html(self, html_content: str, printer_name: str, options: Dict[str, Any]) -> bool:
        """In nội dung HTML"""
        try:
            # Tạo file HTML tạm thời trong thư mục dự án
            project_dir = os.path.dirname(os.path.abspath(__file__))
            temp_file_path = os.path.join(project_dir, f"temp_print.html")
            with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                temp_file.write(html_content)
            
            # Sử dụng trình duyệt mặc định để in HTML
            success = await self._print_html_file(temp_file_path, printer_name, options)
            
            # Xóa file tạm
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
                
            return success
            
        except Exception as e:
            logger.error(f"Lỗi khi in HTML: {e}")
            return False
    
    async def _print_pdf(self, pdf_data: str, printer_name: str, options: Dict[str, Any]) -> bool:
        """In file PDF (từ base64 hoặc đường dẫn)"""
        try:
            import base64
            
            # Kiểm tra xem có phải base64 không
            if pdf_data.startswith('data:application/pdf;base64,'):
                # Decode base64
                pdf_base64 = pdf_data.split(',')[1]
                pdf_bytes = base64.b64decode(pdf_base64)
                
                # Tạo file PDF trong thư mục hiện tại với tên có timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"printed_pdf_{timestamp}.pdf"
                temp_file_path = os.path.join(os.getcwd(), pdf_filename)
                
                with open(temp_file_path, 'wb') as pdf_file:
                    pdf_file.write(pdf_bytes)
                    
                logger.info(f"Đã lưu file PDF: {temp_file_path}")
            else:
                # Giả sử là đường dẫn file
                temp_file_path = pdf_data
            
            # In PDF
            success = await self._print_file(temp_file_path, printer_name, options)
            
            # Không xóa file PDF để có thể mở sau khi in
            if success and pdf_data.startswith('data:application/pdf;base64,'):
                logger.info(f"File PDF đã được in và lưu tại: {temp_file_path}")
                    
            return success
            
        except Exception as e:
            logger.error(f"Lỗi khi in PDF: {e}")
            return False
    
    async def _print_image(self, image_data: str, printer_name: str, options: Dict[str, Any]) -> bool:
        """In hình ảnh"""
        try:
            import base64
            
            # Xử lý dữ liệu hình ảnh base64
            if image_data.startswith('data:image/'):
                # Decode base64
                header, image_base64 = image_data.split(',', 1)
                image_bytes = base64.b64decode(image_base64)
                
                # Xác định định dạng file
                if 'jpeg' in header or 'jpg' in header:
                    suffix = '.jpg'
                elif 'png' in header:
                    suffix = '.png'
                elif 'gif' in header:
                    suffix = '.gif'
                else:
                    suffix = '.png'  # mặc định
                
                # Tạo file hình ảnh tạm thời
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                    temp_file.write(image_bytes)
                    temp_file_path = temp_file.name
            else:
                # Giả sử là đường dẫn file
                temp_file_path = image_data
            
            # In hình ảnh
            success = await self._print_file(temp_file_path, printer_name, options)
            
            # Xóa file tạm nếu đã tạo
            if image_data.startswith('data:image/'):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                    
            return success
            
        except Exception as e:
            logger.error(f"Lỗi khi in hình ảnh: {e}")
            return False
    
    async def _print_file(self, file_path: str, printer_name: str, options: Dict[str, Any]) -> bool:
        """In file sử dụng Windows API"""
        try:
            # Chạy trong thread pool để tránh blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None, 
                self._sync_print_file, 
                file_path, 
                printer_name, 
                options
            )
            return success
            
        except Exception as e:
            logger.error(f"Lỗi khi in file {file_path}: {e}")
            return False
    
    def _sync_print_file(self, file_path: str, printer_name: str, options: Dict[str, Any]) -> bool:
        """In file đồng bộ sử dụng win32print API"""
        try:
            # Sử dụng win32print để in trực tiếp
            if not printer_name:
                printer_name = self.default_printer
            
            # Mở máy in
            printer_handle = win32print.OpenPrinter(printer_name)
            
            try:
                # Đọc nội dung file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Tạo job in
                job_info = ("Python Print Job", None, "RAW")
                job_id = win32print.StartDocPrinter(printer_handle, 1, job_info)
                
                try:
                    # Bắt đầu trang
                    win32print.StartPagePrinter(printer_handle)
                    
                    # Gửi dữ liệu
                    win32print.WritePrinter(printer_handle, content.encode('utf-8'))
                    
                    # Kết thúc trang
                    win32print.EndPagePrinter(printer_handle)
                    
                    logger.info(f"Đã gửi file {file_path} tới máy in {printer_name}")
                    return True
                    
                finally:
                    # Kết thúc job
                    win32print.EndDocPrinter(printer_handle)
                    
            finally:
                # Đóng máy in
                win32print.ClosePrinter(printer_handle)
                
        except Exception as e:
            logger.error(f"Lỗi khi in file {file_path}: {e}")
            return False
    
    async def _print_html_file(self, html_file_path: str, printer_name: str, options: Dict[str, Any]) -> bool:
        """In file HTML sử dụng trình duyệt"""
        try:
            # Sử dụng Internet Explorer để in HTML (có sẵn trên Windows)
            import subprocess
            
            # Tạo script VBS để in HTML
            vbs_script = f'''
Set ie = CreateObject("InternetExplorer.Application")
ie.Visible = False
ie.Navigate "file:///{html_file_path.replace(chr(92), "/")}"
Do While ie.Busy Or ie.ReadyState <> 4
    WScript.Sleep 100
Loop
ie.ExecWB 6, 2
ie.Quit
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False) as vbs_file:
                vbs_file.write(vbs_script)
                vbs_file_path = vbs_file.name
            
            # Chạy script VBS
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ['cscript', '//NoLogo', vbs_file_path],
                    capture_output=True,
                    text=True
                )
            )
            
            # Xóa file VBS tạm
            try:
                os.unlink(vbs_file_path)
            except Exception:
                pass
            
            if result.returncode == 0:
                logger.info(f"Đã in file HTML {html_file_path}")
                return True
            else:
                logger.error(f"Lỗi khi in HTML: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi khi in HTML: {e}")
            return False
    
    def get_printer_status(self, printer_name: str = None) -> Dict[str, Any]:
        """Lấy trạng thái máy in"""
        if printer_name is None:
            printer_name = self.default_printer
            
        try:
            handle = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(handle, 2)
            win32print.ClosePrinter(handle)
            
            status = {
                'name': printer_name,
                'status': 'Ready' if printer_info['Status'] == 0 else 'Busy/Error',
                'jobs_count': printer_info['cJobs'],
                'location': printer_info.get('pLocation', ''),
                'comment': printer_info.get('pComment', '')
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy trạng thái máy in {printer_name}: {e}")
            return {
                'name': printer_name,
                'status': 'Error',
                'error': str(e)
            }
    
    async def print_test_page(self, printer_name: str = None) -> Dict[str, Any]:
        """In trang thử nghiệm"""
        if printer_name is None:
            printer_name = self.default_printer
        
        test_content = f"""=== PRINT TEST PAGE ===

Printer: {printer_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Test ID: {datetime.now().timestamp()}

This is a test page printed from Python WebSocket Print Client.

If you can see this page, the printer is working correctly.

=== END TEST PAGE ==="""
        
        try:
            success = await self.print_content(test_content, {'printer': printer_name, 'content_type': 'text'})
            return {
                "success": success,
                "message": f"Test page sent to {printer_name}" if success else "Failed to send test page",
                "printer": printer_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Lỗi khi in trang thử: {e}")
            return {
                "success": False,
                "error": str(e),
                "printer": printer_name,
                "timestamp": datetime.now().isoformat()
            }