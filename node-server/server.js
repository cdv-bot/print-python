const express = require('express');
const WebSocket = require('ws');
const cors = require('cors');
const http = require('http');
const { exec, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Print utilities for macOS
class PrintHandler {
    static async getDefaultPrinter() {
        return new Promise((resolve) => {
            exec('lpstat -d', (error, stdout) => {
                if (error) {
                    resolve(null);
                    return;
                }
                const match = stdout.match(/system default destination: (.+)/);
                resolve(match ? match[1] : null);
            });
        });
    }

    static async getAvailablePrinters() {
        return new Promise((resolve) => {
            exec('lpstat -p', (error, stdout) => {
                if (error) {
                    resolve([]);
                    return;
                }
                const printers = [];
                const lines = stdout.split('\n');
                for (const line of lines) {
                    const match = line.match(/printer (.+) is/);
                    if (match) {
                        printers.push({
                            name: match[1],
                            status: line.includes('idle') ? 'idle' : 'busy'
                        });
                    }
                }
                resolve(printers);
            });
        });
    }

    static async printText(printerName, content) {
        return new Promise((resolve) => {
            const tempFile = path.join(os.tmpdir(), `print_${Date.now()}.txt`);
            fs.writeFileSync(tempFile, content);
            
            const cmd = printerName ? `lpr -P "${printerName}" "${tempFile}"` : `lpr "${tempFile}"`;
            exec(cmd, (error) => {
                fs.unlinkSync(tempFile);
                resolve({
                    success: !error,
                    message: error ? error.message : 'Print job sent successfully'
                });
            });
        });
    }

    static async printTestPage(printerName) {
        const testContent = `Test Page\n\nPrinter: ${printerName || 'Default'}\nTime: ${new Date().toLocaleString()}\nTest completed successfully.`;
        return await this.printText(printerName, testContent);
    }
}

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
        const printers = await PrintHandler.getAvailablePrinters();
        const defaultPrinter = await PrintHandler.getDefaultPrinter();
        
        // Mark default printer
        printers.forEach(printer => {
            printer.isDefault = printer.name === defaultPrinter;
        });
        
        ws.send(JSON.stringify({
            type: 'printers',
            data: printers
        }));
        console.log(`Sent ${printers.length} printers to ${clientId}`);
    } catch (error) {
        console.error('Error getting printers:', error.message);
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Failed to get printers from system'
        }));
    }
}

// Handle print test request
async function handlePrintTest(ws, clientId, printerName) {
    try {
        const result = await PrintHandler.printTestPage(printerName);
        
        ws.send(JSON.stringify({
            type: 'printResult',
            data: {
                success: result.success,
                message: result.message,
                printer: printerName || 'Default'
            }
        }));
        
        console.log(`Print test result sent to ${clientId}:`, result);
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
        if (!data.content) {
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Print content is required'
            }));
            return;
        }
        
        const result = await PrintHandler.printText(data.printer, data.content);
        
        ws.send(JSON.stringify({
            type: 'printResult',
            data: {
                success: result.success,
                message: result.message,
                printer: data.printer || 'Default'
            }
        }));
        
        console.log(`Custom print result sent to ${clientId}:`, result);
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
        platform: os.platform(),
        printSystem: 'macOS CUPS'
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

// Direct printer endpoints
app.get('/api/printers', async (req, res) => {
    try {
        const printers = await PrintHandler.getAvailablePrinters();
        const defaultPrinter = await PrintHandler.getDefaultPrinter();
        
        // Mark default printer
        printers.forEach(printer => {
            printer.isDefault = printer.name === defaultPrinter;
        });
        
        res.json({
            status: 'success',
            printers: printers,
            count: printers.length,
            defaultPrinter: defaultPrinter
        });
    } catch (error) {
        res.status(500).json({ 
            status: 'error',
            message: 'Failed to get printers from system'
        });
    }
});

app.get('/api/print-test', async (req, res) => {
    try {
        const { printer } = req.query;
        const result = await PrintHandler.printTestPage(printer);
        
        res.json({
            success: result.success,
            message: result.message,
            printer: printer || 'Default'
        });
    } catch (error) {
        res.status(500).json({ 
            success: false,
            error: 'Failed to execute print test'
        });
    }
});

app.post('/api/print', async (req, res) => {
    try {
        const { printer, content } = req.body;
        
        if (!content) {
            return res.status(400).json({ 
                success: false,
                error: 'Content is required' 
            });
        }
        
        const result = await PrintHandler.printText(printer, content);
        
        res.json({
            success: result.success,
            message: result.message,
            printer: printer || 'Default'
        });
    } catch (error) {
        res.status(500).json({ 
            success: false,
            error: 'Failed to execute print job'
        });
    }
});

// Generate unique client ID
function generateClientId() {
    return 'client-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
}

// Start server
const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
    console.log(`🚀 Node.js Print Server running on port ${PORT}`);
    console.log(`📡 WebSocket server: ws://localhost:${PORT}`);
    console.log(`🌐 HTTP API: http://localhost:${PORT}/api`);
    console.log(`🖨️  Print System: macOS CUPS (native)`);
    console.log(`📄 Static files: http://localhost:${PORT}`);
    console.log(`\n📋 Available endpoints:`);
    console.log(`   GET  /api/printers    - List available printers`);
    console.log(`   GET  /api/print-test - Print test page`);
    console.log(`   POST /api/print      - Print custom content`);
    console.log(`   GET  /api/status     - Server status`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('Shutting down gracefully...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});