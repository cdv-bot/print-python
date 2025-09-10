const express = require('express');
const WebSocket = require('ws');
const axios = require('axios');
const cors = require('cors');
const http = require('http');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Python backend URL
const PYTHON_API_URL = 'http://localhost:8081';

// Store connected clients
const clients = new Map();

// WebSocket connection handling
wss.on('connection', (ws, req) => {
    const clientId = generateClientId();
    clients.set(clientId, {
        ws: ws,
        id: clientId,
        type: 'web-client',
        connectedAt: new Date()
    });
    
    console.log(`Client connected: ${clientId}`);
    
    // Send welcome message
    ws.send(JSON.stringify({
        type: 'welcome',
        clientId: clientId,
        message: 'Connected to Node.js Bridge Server'
    }));
    
    // Handle incoming messages
    ws.on('message', async (message) => {
        try {
            const data = JSON.parse(message);
            console.log(`Received from ${clientId}:`, data);
            
            switch (data.type) {
                case 'getPrinters':
                    await handleGetPrinters(ws, clientId);
                    break;
                case 'printTest':
                    await handlePrintTest(ws, clientId, data.printer);
                    break;
                case 'print':
                    await handleCustomPrint(ws, clientId, data);
                    break;
                default:
                    ws.send(JSON.stringify({
                        type: 'error',
                        message: 'Unknown message type'
                    }));
            }
        } catch (error) {
            console.error('Error processing message:', error);
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Invalid message format'
            }));
        }
    });
    
    // Handle client disconnect
    ws.on('close', () => {
        clients.delete(clientId);
        console.log(`Client disconnected: ${clientId}`);
    });
    
    ws.on('error', (error) => {
        console.error(`WebSocket error for ${clientId}:`, error);
        clients.delete(clientId);
    });
});

// Handle get printers request
async function handleGetPrinters(ws, clientId) {
    try {
        const response = await axios.get(`${PYTHON_API_URL}/printers`);
        
        // Extract printers array from Python backend response
        const printers = response.data.printers || [];
        
        ws.send(JSON.stringify({
            type: 'printers',
            data: printers
        }));
        console.log(`Sent ${printers.length} printers to ${clientId}`);
    } catch (error) {
        console.error('Error getting printers:', error.message);
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Failed to get printers from Python backend'
        }));
    }
}

// Handle print test request
async function handlePrintTest(ws, clientId, printerName) {
    try {
        if (!printerName) {
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Printer name is required'
            }));
            return;
        }
        
        const response = await axios.get(`${PYTHON_API_URL}/print-test`, {
            params: { printer: printerName }
        });
        
        ws.send(JSON.stringify({
            type: 'printResult',
            data: response.data
        }));
        
        console.log(`Print test result sent to ${clientId}:`, response.data);
    } catch (error) {
        console.error('Error in print test:', error.message);
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Failed to execute print test'
        }));
    }
}

// Handle custom print request
async function handleCustomPrint(ws, clientId, data) {
    try {
        if (!data.printer) {
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Printer name is required'
            }));
            return;
        }
        
        if (!data.content) {
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Print content is required'
            }));
            return;
        }
        
        // Gửi request tới Python backend để in nội dung tùy chỉnh
        const response = await axios.post(`${PYTHON_API_URL}/print-content`, {
            printer: data.printer,
            content: data.content,
            content_type: 'text'
        });
        
        ws.send(JSON.stringify({
            type: 'printResult',
            data: response.data
        }));
        
        console.log(`Custom print result sent to ${clientId}:`, response.data);
    } catch (error) {
        console.error('Error in custom print:', error.message);
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Failed to execute custom print'
        }));
    }
}

// REST API endpoints
app.get('/api/status', (req, res) => {
    res.json({
        status: 'running',
        clients: clients.size,
        uptime: process.uptime(),
        pythonBackend: PYTHON_API_URL
    });
});

app.get('/api/clients', (req, res) => {
    const clientList = Array.from(clients.values()).map(client => ({
        id: client.id,
        type: client.type,
        connectedAt: client.connectedAt
    }));
    res.json(clientList);
});

// Proxy endpoints to Python backend
app.get('/api/printers', async (req, res) => {
    try {
        const response = await axios.get(`${PYTHON_API_URL}/printers`);
        // Extract printers array from Python backend response
        const printers = response.data.printers || [];
        res.json({
            status: 'success',
            printers: printers,
            count: printers.length
        });
    } catch (error) {
        res.status(500).json({ 
            status: 'error',
            message: 'Failed to get printers from Python backend'
        });
    }
});

app.get('/api/print-test', async (req, res) => {
    try {
        const { printer } = req.query;
        if (!printer) {
            return res.status(400).json({ error: 'Printer parameter is required' });
        }
        
        const response = await axios.get(`${PYTHON_API_URL}/print-test`, {
            params: { printer }
        });
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to execute print test' });
    }
});

// Generate unique client ID
function generateClientId() {
    return 'client-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
}

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
    console.log(`🚀 Node.js Bridge Server running on port ${PORT}`);
    console.log(`📡 WebSocket server: ws://localhost:${PORT}`);
    console.log(`🌐 HTTP API: http://localhost:${PORT}/api`);
    console.log(`🔗 Python Backend: ${PYTHON_API_URL}`);
    console.log(`📄 Static files: http://localhost:${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('Shutting down gracefully...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});