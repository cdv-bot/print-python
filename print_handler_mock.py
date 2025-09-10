#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock Print Handler for macOS Testing
Mô phỏng print_handler.py cho việc test trên macOS
"""

import tempfile
import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class PrintHandler:
    def __init__(self):
        self.default_printer = "Default_Printer_macOS"
        logger.info(f"Mock Print Handler initialized with default printer: {self.default_printer}")
        
    def get_available_printers(self) -> List[Dict[str, Any]]:
        """Mock: Trả về danh sách máy in giả lập"""
        mock_printers = [
            {
                'name': 'HP LaserJet Pro',
                'server': 'Local',
                'status': 'Ready'
            },
            {
                'name': 'Canon PIXMA',
                'server': 'Local', 
                'status': 'Ready'
            },
            {
                'name': 'Default_Printer_macOS',
                'server': 'Local',
                'status': 'Ready'
            }
        ]
        
        logger.info(f"Mock: Returning {len(mock_printers)} printers")
        return mock_printers
    
    async def print_content(self, content: str, options: Dict[str, Any] = None) -> bool:
        """Mock: Giả lập in nội dung"""
        if options is None:
            options = {}
            
        try:
            content_type = options.get('content_type', 'text')
            printer_name = options.get('printer', self.default_printer)
            
            logger.info(f"Mock Print: {len(content)} chars to {printer_name} as {content_type}")
            
            # Giả lập thời gian in
            await asyncio.sleep(0.5)
            
            # Giả lập thành công 90% thời gian
            import random
            success = random.random() > 0.1
            
            if success:
                logger.info(f"Mock: Print successful to {printer_name}")
            else:
                logger.error(f"Mock: Print failed to {printer_name}")
                
            return success
                
        except Exception as e:
            logger.error(f"Mock: Print error: {e}")
            return False
    
    async def print_test_page(self, printer_name: str = None) -> Dict[str, Any]:
        """Mock: Giả lập in test page"""
        if printer_name is None:
            printer_name = self.default_printer
            
        try:
            logger.info(f"Mock: Printing test page to {printer_name}")
            
            # Giả lập thời gian in
            await asyncio.sleep(1.0)
            
            # Giả lập thành công 95% thời gian
            import random
            success = random.random() > 0.05
            
            if success:
                return {
                    'success': True,
                    'message': f'Test page printed successfully to {printer_name}',
                    'printer': printer_name,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to print test page to {printer_name}',
                    'printer': printer_name,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Mock: Test print error: {e}")
            return {
                'success': False,
                'message': f'Error printing test page: {str(e)}',
                'printer': printer_name,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_printer_status(self, printer_name: str = None) -> Dict[str, Any]:
        """Mock: Trả về trạng thái máy in"""
        if printer_name is None:
            printer_name = self.default_printer
            
        return {
            'name': printer_name,
            'status': 'Ready',
            'jobs_in_queue': 0,
            'is_online': True,
            'is_default': printer_name == self.default_printer
        }