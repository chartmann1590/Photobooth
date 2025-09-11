// Camera Debug Logger
class CameraDebugLogger {
    constructor() {
        this.logs = [];
        this.startTime = Date.now();
        this.logToConsole = true;
        this.logToServer = true;
    }

    log(level, message, data = null) {
        const timestamp = new Date().toISOString();
        const relativeTime = Date.now() - this.startTime;
        
        const logEntry = {
            timestamp,
            relativeTime,
            level,
            message,
            data,
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        this.logs.push(logEntry);

        // Console logging
        if (this.logToConsole) {
            const consoleMessage = `[${relativeTime}ms] ${level.toUpperCase()}: ${message}`;
            switch(level) {
                case 'error':
                    console.error(consoleMessage, data || '');
                    break;
                case 'warn':
                    console.warn(consoleMessage, data || '');
                    break;
                case 'info':
                    console.info(consoleMessage, data || '');
                    break;
                default:
                    console.log(consoleMessage, data || '');
            }
        }

        // Send to server
        if (this.logToServer && (level === 'error' || level === 'warn' || this.logs.length % 10 === 0)) {
            this.sendLogsToServer();
        }
    }

    error(message, data) { this.log('error', message, data); }
    warn(message, data) { this.log('warn', message, data); }
    info(message, data) { this.log('info', message, data); }
    debug(message, data) { this.log('debug', message, data); }

    async sendLogsToServer() {
        try {
            await fetch('/booth/api/debug-logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    logs: this.logs.slice(-50), // Send last 50 logs
                    sessionId: this.getSessionId()
                })
            });
        } catch (error) {
            console.error('Failed to send logs to server:', error);
        }
    }

    getSessionId() {
        if (!this.sessionId) {
            this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return this.sessionId;
    }

    async testCameraCapabilities() {
        this.info('=== Starting Camera Capabilities Test ===');
        
        // Test 1: Browser Support
        this.info('Test 1: Checking browser support');
        if (!navigator.mediaDevices) {
            this.error('navigator.mediaDevices not available');
            return false;
        }
        if (!navigator.mediaDevices.getUserMedia) {
            this.error('getUserMedia not available');
            return false;
        }
        this.info('✓ Browser supports getUserMedia');

        // Test 2: HTTPS Check
        this.info('Test 2: Checking connection security');
        const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
        if (!isSecure) {
            this.error('Connection is not secure', { protocol: location.protocol, hostname: location.hostname });
            return false;
        }
        this.info('✓ Connection is secure', { protocol: location.protocol });

        // Test 3: Device Enumeration
        this.info('Test 3: Enumerating media devices');
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(d => d.kind === 'videoinput');
            this.info(`Found ${cameras.length} camera device(s)`, cameras.map(c => ({
                deviceId: c.deviceId,
                label: c.label || 'Unknown Camera',
                groupId: c.groupId
            })));
            
            if (cameras.length === 0) {
                this.error('No camera devices found');
                return false;
            }
        } catch (error) {
            this.warn('Could not enumerate devices', { error: error.message });
        }

        // Test 4: Permission Check
        this.info('Test 4: Checking camera permissions');
        try {
            const permissions = await navigator.permissions.query({ name: 'camera' });
            this.info('Camera permission state', { state: permissions.state });
            
            permissions.addEventListener('change', () => {
                this.info('Camera permission changed', { newState: permissions.state });
            });
        } catch (error) {
            this.warn('Could not check camera permissions', { error: error.message });
        }

        // Test 5: Basic getUserMedia
        this.info('Test 5: Testing basic getUserMedia');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            this.info('✓ Basic camera access successful');
            
            // Get actual video track settings
            const videoTrack = stream.getVideoTracks()[0];
            if (videoTrack) {
                const settings = videoTrack.getSettings();
                this.info('Camera settings', settings);
                
                const capabilities = videoTrack.getCapabilities();
                this.info('Camera capabilities', capabilities);
            }
            
            // Clean up
            stream.getTracks().forEach(track => track.stop());
            this.info('Camera test stream stopped');
            return true;
            
        } catch (error) {
            this.error('Basic camera access failed', {
                name: error.name,
                message: error.message,
                constraint: error.constraint
            });
            return false;
        }
    }

    logDOMState() {
        this.info('=== DOM State Check ===');
        const video = document.getElementById('cameraPreview');
        const captureBtn = document.getElementById('captureBtn');
        const cameraLoading = document.getElementById('cameraLoading');
        const cameraError = document.getElementById('cameraError');

        this.info('DOM Elements Status', {
            video: {
                exists: !!video,
                visible: video ? !video.hidden : false,
                style: video ? video.style.cssText : null
            },
            captureBtn: {
                exists: !!captureBtn,
                disabled: captureBtn ? captureBtn.disabled : null,
                text: captureBtn ? captureBtn.textContent.trim() : null
            },
            cameraLoading: {
                exists: !!cameraLoading,
                hidden: cameraLoading ? cameraLoading.style.display === 'none' : null
            },
            cameraError: {
                exists: !!cameraError,
                hidden: cameraError ? cameraError.classList.contains('hidden') : null
            }
        });
    }
}

// Global debug logger instance
window.cameraDebugLogger = new CameraDebugLogger();