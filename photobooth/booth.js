// PhotoBooth JavaScript
class PhotoBooth {
    constructor() {
        this.debugLogger = window.cameraDebugLogger;
        this.debugLogger.info('=== PhotoBooth Constructor Started ===');
        
        this.stream = null;
        this.video = document.getElementById('cameraPreview');
        this.captureBtn = document.getElementById('captureBtn');
        this.currentPhoto = null;
        
        // Log DOM state
        this.debugLogger.logDOMState();
        
        if (!this.video) {
            this.debugLogger.error('cameraPreview element not found in DOM');
            throw new Error('cameraPreview element not found');
        }
        
        if (!this.captureBtn) {
            this.debugLogger.error('captureBtn element not found in DOM');
            throw new Error('captureBtn element not found');
        }
        
        this.debugLogger.info('PhotoBooth DOM elements validated successfully');
        
        // Start initialization
        this.init().catch(error => {
            this.debugLogger.error('PhotoBooth initialization failed', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            this.showCameraError(error);
        });
    }

    async init() {
        try {
            this.debugLogger.info('Starting PhotoBooth initialization process');
            
            // First run camera capabilities test
            this.debugLogger.info('Running camera capabilities test');
            const capabilitiesTest = await this.debugLogger.testCameraCapabilities();
            if (!capabilitiesTest) {
                throw new Error('Camera capabilities test failed');
            }
            
            // Initialize camera
            this.debugLogger.info('Starting camera initialization');
            await this.initCamera();
            
            // Setup event listeners
            this.debugLogger.info('Setting up event listeners');
            this.setupEventListeners();
            
            // Hide loading state
            this.debugLogger.info('Hiding loading state');
            this.hideLoading();
            
            this.debugLogger.info('PhotoBooth initialization completed successfully');
            
        } catch (error) {
            this.debugLogger.error('PhotoBooth init failed', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            throw error;
        }
    }

    async initCamera() {
        try {
            this.debugLogger.info('=== Camera Initialization Started ===');
            
            // Check if getUserMedia is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.debugLogger.error('getUserMedia not supported', {
                    mediaDevices: !!navigator.mediaDevices,
                    getUserMedia: !!navigator.mediaDevices?.getUserMedia
                });
                throw new Error('getUserMedia not supported by this browser');
            }
            this.debugLogger.info('getUserMedia is supported');
            
            // Check connection security
            const isSecure = location.protocol === 'https:' || location.hostname === 'localhost';
            this.debugLogger.info('Connection security check', {
                protocol: location.protocol,
                hostname: location.hostname,
                isSecure: isSecure
            });
            
            if (!isSecure) {
                throw new Error('Camera requires HTTPS connection');
            }
            
            // Check for available cameras
            this.debugLogger.info('Enumerating camera devices');
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const cameras = devices.filter(device => device.kind === 'videoinput');
                this.debugLogger.info(`Found ${cameras.length} camera device(s)`, {
                    cameras: cameras.map(c => ({
                        deviceId: c.deviceId,
                        label: c.label || 'Unknown',
                        groupId: c.groupId
                    }))
                });
                
                if (cameras.length === 0) {
                    throw new Error('No cameras found on this device');
                }
            } catch (enumError) {
                this.debugLogger.warn('Could not enumerate devices', {
                    error: enumError.message,
                    name: enumError.name
                });
            }
            
            // Try with different constraint levels
            this.debugLogger.info('Attempting camera access with different constraints');
            
            const constraintOptions = [
                {
                    name: 'High Resolution',
                    constraints: {
                        video: {
                            width: { ideal: 1920, min: 640 },
                            height: { ideal: 1080, min: 480 },
                            facingMode: 'user'
                        },
                        audio: false
                    }
                },
                {
                    name: 'Medium Resolution', 
                    constraints: {
                        video: {
                            width: { ideal: 1280, min: 640 },
                            height: { ideal: 720, min: 480 }
                        },
                        audio: false
                    }
                },
                {
                    name: 'Basic Constraints',
                    constraints: { video: true, audio: false }
                }
            ];

            let streamSuccess = false;
            
            for (const option of constraintOptions) {
                try {
                    this.debugLogger.info(`Trying ${option.name}`, { constraints: option.constraints });
                    this.stream = await navigator.mediaDevices.getUserMedia(option.constraints);
                    this.debugLogger.info(`✓ ${option.name} successful`);
                    streamSuccess = true;
                    break;
                } catch (error) {
                    this.debugLogger.warn(`✗ ${option.name} failed`, {
                        name: error.name,
                        message: error.message,
                        constraint: error.constraint
                    });
                }
            }
            
            if (!streamSuccess) {
                throw new Error('All camera constraint attempts failed');
            }
            
            // Set up video element
            this.debugLogger.info('Setting up video element with stream');
            this.video.srcObject = this.stream;
            
            // Get stream info
            const videoTrack = this.stream.getVideoTracks()[0];
            if (videoTrack) {
                const settings = videoTrack.getSettings();
                this.debugLogger.info('Video track settings', settings);
            }
            
            // Set up video event handlers
            this.video.addEventListener('loadedmetadata', () => {
                this.debugLogger.info('Video metadata loaded', {
                    videoWidth: this.video.videoWidth,
                    videoHeight: this.video.videoHeight,
                    duration: this.video.duration
                });
                
                this.video.play().then(() => {
                    this.debugLogger.info('Video play started successfully');
                    this.enableCaptureButton();
                }).catch(playError => {
                    this.debugLogger.error('Video play failed', {
                        name: playError.name,
                        message: playError.message
                    });
                });
            });
            
            this.video.addEventListener('error', (event) => {
                this.debugLogger.error('Video element error', {
                    error: event.error,
                    message: event.message
                });
            });

            this.debugLogger.info('✓ Camera initialization completed successfully');
            
        } catch (error) {
            this.debugLogger.error('✗ Camera initialization failed completely', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            this.showCameraError(error);
        }
    }

    setupEventListeners() {
        this.captureBtn.addEventListener('click', () => this.startPhotoSession());
        
        document.getElementById('printBtn').addEventListener('click', () => this.printPhoto());
        document.getElementById('retakeBtn').addEventListener('click', () => this.retakePhoto());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !this.captureBtn.disabled) {
                e.preventDefault();
                this.startPhotoSession();
            }
        });
    }

    enableCaptureButton() {
        this.captureBtn.disabled = false;
        this.captureBtn.innerHTML = '<i class="fas fa-camera mr-4"></i>Start Photo Session';
        document.getElementById('cameraLoading').style.display = 'none';
    }

    showCameraError(error = null) {
        document.getElementById('cameraLoading').style.display = 'none';
        document.getElementById('cameraError').classList.remove('hidden');
        this.captureBtn.disabled = true;
        this.captureBtn.innerHTML = '<i class="fas fa-exclamation-triangle mr-4"></i>Camera Error';
        
        // Add detailed error information for debugging
        if (error) {
            const errorDiv = document.getElementById('cameraError');
            const existingDetail = errorDiv.querySelector('.error-detail');
            if (existingDetail) existingDetail.remove();
            
            const errorDetail = document.createElement('div');
            errorDetail.className = 'error-detail mt-2 text-xs text-red-200 bg-red-800 rounded p-2';
            errorDetail.textContent = `Error: ${error.name || 'Unknown'} - ${error.message || 'Camera access failed'}`;
            errorDiv.appendChild(errorDetail);
            
            console.error('Detailed camera error:', error);
        }
    }

    async startPhotoSession() {
        if (this.captureBtn.disabled) return;

        this.disableCaptureButton();
        
        // Start countdown with TTS
        await this.playCountdown();
        
        // Capture photo
        await this.capturePhoto();
    }

    disableCaptureButton() {
        this.captureBtn.disabled = true;
        this.captureBtn.innerHTML = '<i class="fas fa-hourglass-half mr-4"></i>Please Wait...';
    }

    async playCountdown() {
        const countdownOverlay = document.getElementById('countdownOverlay');
        const countdownNumber = document.getElementById('countdownNumber');
        
        countdownOverlay.classList.remove('hidden');
        
        // Trigger TTS countdown
        try {
            await fetch('/booth/api/countdown', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: '3, 2, 1, smile!'
                })
            });
        } catch (error) {
            console.warn('TTS countdown failed:', error);
        }

        // Visual countdown
        for (let i = 3; i > 0; i--) {
            countdownNumber.textContent = i;
            countdownNumber.className = 'text-white text-[20rem] md:text-[25rem] font-bold leading-none animate-countdown-pulse drop-shadow-2xl';
            
            await this.sleep(1000);
        }

        countdownNumber.textContent = 'Smile!';
        countdownNumber.className = 'text-white text-[10rem] md:text-[12rem] font-bold leading-none animate-bounce drop-shadow-2xl';
        
        await this.sleep(500);
        countdownOverlay.classList.add('hidden');
    }

    async capturePhoto() {
        this.showLoading('Capturing your beautiful photo...');

        try {
            // Create canvas to capture photo
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = this.video.videoWidth;
            canvas.height = this.video.videoHeight;
            
            ctx.drawImage(this.video, 0, 0);
            
            // Convert to blob
            const blob = await new Promise(resolve => {
                canvas.toBlob(resolve, 'image/jpeg', 0.95);
            });

            // Send to server
            const formData = new FormData();
            formData.append('photo', blob, 'photo.jpg');

            const response = await fetch('/booth/api/capture', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.currentPhoto = data;
                this.showPreview(data.preview_url);
            } else {
                throw new Error(data.error || 'Photo capture failed');
            }

        } catch (error) {
            console.error('Photo capture failed:', error);
            this.showError('Failed to capture photo: ' + error.message);
            this.enableCaptureButton();
        } finally {
            this.hideLoading();
        }
    }

    showPreview(previewUrl) {
        const previewModal = document.getElementById('previewModal');
        const previewImage = document.getElementById('previewImage');
        
        previewImage.src = previewUrl;
        previewModal.classList.remove('hidden');
        previewModal.classList.add('modal-enter');
    }

    async printPhoto() {
        if (!this.currentPhoto) return;

        this.showLoading('Sending to printer...');

        try {
            const response = await fetch('/booth/api/print', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: this.currentPhoto.filename
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Photo sent to printer! Check the printer for your beautiful photo.');
                this.closePreview();
                this.enableCaptureButton();
            } else {
                throw new Error(data.error || 'Print failed');
            }

        } catch (error) {
            console.error('Print failed:', error);
            this.showError('Failed to print photo: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async retakePhoto() {
        if (!this.currentPhoto) return;

        this.showLoading('Preparing for retake...');

        try {
            const response = await fetch('/booth/api/retake', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: this.currentPhoto.filename
                })
            });

            const data = await response.json();

            if (data.success) {
                this.closePreview();
                this.enableCaptureButton();
                this.currentPhoto = null;
            } else {
                throw new Error(data.error || 'Retake failed');
            }

        } catch (error) {
            console.error('Retake failed:', error);
            this.showError('Failed to retake photo: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    closePreview() {
        document.getElementById('previewModal').classList.add('hidden');
    }

    showLoading(text = 'Processing...') {
        const loadingOverlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        
        loadingText.textContent = text;
        loadingOverlay.classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }

    showSuccess(message) {
        const successMessage = document.getElementById('successMessage');
        const successText = document.getElementById('successText');
        
        successText.textContent = message;
        successMessage.classList.remove('hidden');
        successMessage.classList.add('success-bounce');
        
        setTimeout(() => {
            successMessage.classList.add('hidden');
            successMessage.classList.remove('success-bounce');
        }, 5000);
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
        
        setTimeout(() => {
            errorMessage.classList.add('hidden');
        }, 5000);
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Cleanup method
    destroy() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}

// Initialize PhotoBooth when page loads
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Initializing PhotoBooth...');
        window.photoBooth = new PhotoBooth();
        console.log('PhotoBooth initialized successfully');
    } catch (error) {
        console.error('Failed to initialize PhotoBooth:', error);
        // Show error message to user
        const errorDiv = document.getElementById('cameraError');
        if (errorDiv) {
            document.getElementById('cameraLoading').style.display = 'none';
            errorDiv.classList.remove('hidden');
            const errorDetail = document.createElement('div');
            errorDetail.className = 'error-detail mt-2 text-xs text-red-200 bg-red-800 rounded p-2';
            errorDetail.textContent = `Initialization Error: ${error.message}`;
            errorDiv.appendChild(errorDetail);
        }
    }
});

// Cleanup when page unloads
window.addEventListener('beforeunload', () => {
    if (window.photoBooth) {
        window.photoBooth.destroy();
    }
});

// Handle page visibility changes (pause/resume camera)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, could pause camera if needed
        console.log('Page hidden');
    } else {
        // Page is visible again
        console.log('Page visible');
    }
});

// Add touch feedback for mobile
document.addEventListener('touchstart', (e) => {
    if (e.target.matches('button')) {
        e.target.style.transform = 'scale(0.95)';
    }
});

document.addEventListener('touchend', (e) => {
    if (e.target.matches('button')) {
        setTimeout(() => {
            e.target.style.transform = '';
        }, 150);
    }
});

// Prevent zoom on double tap for iOS
let lastTouchEnd = 0;
document.addEventListener('touchend', (e) => {
    const now = (new Date()).getTime();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, false);

// Add keyboard navigation hints
document.addEventListener('keydown', (e) => {
    if (e.code === 'KeyH' || e.code === 'F1') {
        e.preventDefault();
        alert('PhotoBooth Controls:\n\nSPACE: Take photo\nESC: Close modals\nH/F1: Show this help');
    }
    
    if (e.code === 'Escape') {
        // Close any open modals
        document.querySelectorAll('.fixed.inset-0:not(.hidden)').forEach(modal => {
            modal.classList.add('hidden');
        });
        
        // Reset capture button if needed
        if (window.photoBooth && window.photoBooth.captureBtn.disabled) {
            window.photoBooth.enableCaptureButton();
        }
    }
});