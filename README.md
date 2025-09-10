# WebSocket Print Client for Windows

Ứng dụng Python để kết nối với WebSocket server và in tài liệu từ web sang máy in Windows.

## Tính năng

- Kết nối WebSocket tới server `wss://print-socket.onrender.com`
- Hỗ trợ in nhiều loại nội dung:
  - Văn bản thuần túy (text)
  - HTML
  - PDF (từ base64 hoặc file)
  - Hình ảnh (từ base64 hoặc file)
- Tự động kết nối lại khi mất kết nối
- Logging chi tiết
- Quản lý máy in Windows

## Yêu cầu hệ thống

- Windows 10/11
- Python 3.8+
- Máy in đã được cài đặt và cấu hình

## Cài đặt

1. Clone hoặc tải về project
2. Mở Command Prompt hoặc PowerShell tại thư mục project
3. Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

## Sử dụng

### Chạy ứng dụng

```bash
python main.py
```

### Cấu trúc tin nhắn WebSocket

Ứng dụng hỗ trợ các loại tin nhắn sau:

#### 1. Công việc in (print_job)

```json
{
  "type": "print_job",
  "job_id": "unique_job_id",
  "content": "nội dung cần in",
  "options": {
    "content_type": "text|html|pdf|image",
    "printer": "tên máy in (tùy chọn)",
    "copies": 1
  }
}
```

#### 2. Yêu cầu trạng thái (status_request)

```json
{
  "type": "status_request"
}
```

#### 3. Ping

```json
{
  "type": "ping"
}
```

### Các loại nội dung hỗ trợ

#### Văn bản thuần túy
```json
{
  "type": "print_job",
  "job_id": "text_001",
  "content": "Đây là nội dung văn bản cần in",
  "options": {
    "content_type": "text"
  }
}
```

#### HTML
```json
{
  "type": "print_job",
  "job_id": "html_001",
  "content": "<html><body><h1>Tiêu đề</h1><p>Nội dung HTML</p></body></html>",
  "options": {
    "content_type": "html"
  }
}
```

#### PDF (Base64)
```json
{
  "type": "print_job",
  "job_id": "pdf_001",
  "content": "data:application/pdf;base64,JVBERi0xLjQK...",
  "options": {
    "content_type": "pdf"
  }
}
```

#### Hình ảnh (Base64)
```json
{
  "type": "print_job",
  "job_id": "image_001",
  "content": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "options": {
    "content_type": "image"
  }
}
```

## Cấu hình

### Thay đổi WebSocket URL

Sửa file `main.py`, dòng:
```python
uri = "wss://print-socket.onrender.com"
```

### Cấu hình logging

Sửa file `main.py`, phần cấu hình logging:
```python
logging.basicConfig(
    level=logging.INFO,  # Thay đổi level: DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('print_client.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

## Troubleshooting

### Lỗi kết nối WebSocket
- Kiểm tra kết nối internet
- Đảm bảo URL WebSocket server đúng
- Kiểm tra firewall/antivirus

### Lỗi không tìm thấy máy in
- Đảm bảo máy in đã được cài đặt và kết nối
- Chạy `Control Panel > Devices and Printers` để kiểm tra
- Thử in test page từ Windows

### Lỗi quyền truy cập
- Chạy Command Prompt/PowerShell với quyền Administrator
- Đảm bảo user có quyền sử dụng máy in

### Lỗi encoding
- Đảm bảo file được lưu với encoding UTF-8
- Kiểm tra cấu hình locale của Windows

## File log

Ứng dụng tạo file log `print_client.log` trong thư mục chạy để theo dõi hoạt động và debug.

## Cấu trúc project

```
print-python/
├── main.py              # File chính chứa WebSocket client
├── print_handler.py     # Module xử lý in ấn
├── requirements.txt     # Dependencies
├── README.md           # Hướng dẫn sử dụng
└── print_client.log    # File log (tự động tạo)
```

## Phát triển thêm

### Thêm loại nội dung mới

1. Thêm handler trong `print_handler.py`
2. Cập nhật method `print_content()` để xử lý loại mới
3. Test với tin nhắn WebSocket tương ứng

### Tùy chỉnh xử lý tin nhắn

Sửa method `handle_message()` trong `main.py` để thêm các loại tin nhắn mới.

## Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra file log `print_client.log`
2. Đảm bảo đã cài đặt đúng dependencies
3. Kiểm tra cấu hình máy in Windows

## License

MIT License