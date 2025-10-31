/**
 * WebSocket Client for Real-time Log Streaming
 */
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.isConnected = false;
        this.messageHandlers = {
            connection: [],
            log: [],
            completed: [],
            error: [],
            files_ready: []
        };
    }

    /**
     * Connect to WebSocket for a specific session
     */
    connect(sessionId) {
        this.sessionId = sessionId;
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
        
        console.log(`Connecting to WebSocket: ${wsUrl}`);
        
        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.handleError(error);
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            
            // Send ping to keep connection alive
            this.startPingInterval();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed:', event.code, event.reason);
            this.isConnected = false;
            this.stopPingInterval();
            
            // Attempt to reconnect if not a normal closure
            if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.handleError(error);
        };
    }

    /**
     * Handle incoming messages
     */
    handleMessage(data) {
        const { type, message, timestamp, session_id } = data;
        
        console.log(`WebSocket message [${type}]:`, message);
        
        // Call registered handlers for this message type
        if (this.messageHandlers[type]) {
            this.messageHandlers[type].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${type} handler:`, error);
                }
            });
        }
    }

    /**
     * Register a message handler
     */
    on(messageType, handler) {
        if (this.messageHandlers[messageType]) {
            this.messageHandlers[messageType].push(handler);
        } else {
            console.warn(`Unknown message type: ${messageType}`);
        }
    }

    /**
     * Remove a message handler
     */
    off(messageType, handler) {
        if (this.messageHandlers[messageType]) {
            const index = this.messageHandlers[messageType].indexOf(handler);
            if (index > -1) {
                this.messageHandlers[messageType].splice(index, 1);
            }
        }
    }

    /**
     * Send a message to the server
     */
    send(data) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }

    /**
     * Start ping interval to keep connection alive
     */
    startPingInterval() {
        this.pingInterval = setInterval(() => {
            if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Ping every 30 seconds
    }

    /**
     * Stop ping interval
     */
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        this.reconnectAttempts++;
        
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectDelay}ms`);
        
        setTimeout(() => {
            if (this.sessionId) {
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect(this.sessionId);
            }
        }, this.reconnectDelay);
        
        // Exponential backoff with jitter
        this.reconnectDelay = Math.min(this.reconnectDelay * 2 + Math.random() * 1000, 30000);
    }

    /**
     * Handle WebSocket errors
     */
    handleError(error) {
        console.error('WebSocket error:', error);
        
        // Notify error handlers
        if (this.messageHandlers.error) {
            this.messageHandlers.error.forEach(handler => {
                try {
                    handler({ type: 'error', message: error.message || 'WebSocket connection error' });
                } catch (e) {
                    console.error('Error in error handler:', e);
                }
            });
        }
    }

    /**
     * Close WebSocket connection
     */
    close() {
        console.log('Closing WebSocket connection');
        this.stopPingInterval();
        
        if (this.ws) {
            this.ws.close(1000, 'Client closing connection');
            this.ws = null;
        }
        
        this.isConnected = false;
        this.sessionId = null;
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            sessionId: this.sessionId,
            reconnectAttempts: this.reconnectAttempts,
            readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED
        };
    }
}

// Export for use in other scripts
window.WebSocketClient = WebSocketClient;