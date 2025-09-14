// PhotoBooth JavaScript
class PhotoBooth {
    constructor() {
        console.log('PhotoBooth constructor called');
        this.stream = null;
        this.video = document.getElementById('cameraPreview');
        this.captureBtn = document.getElementById('captureBtn');
        this.frameOverlay = document.getElementById('frameOverlay');
        this.currentPhoto = null;
        
        console.log('Elements found:', {
            video: !!this.video,
            captureBtn: !!this.captureBtn,
            frameOverlay: !!this.frameOverlay
        });
        
        if (!this.video) {
            throw new Error('cameraPreview element not found');
        }
        
        if (!this.captureBtn) {
            throw new Error('captureBtn element not found');
        }
        
        this.init().catch(error => {
            console.error('PhotoBooth init failed:', error);
            this.showCameraError(error);
        });
    }

    async init() {
        try {
            console.log('Starting PhotoBooth init...');
            await this.initCamera();
            this.setupEventListeners();
            
            // Load frame overlay
            await this.loadFrameOverlay();
            console.log('PhotoBooth init completed');
        } catch (error) {
            console.error('Init error:', error);
            throw error;
        }
    }

    async initCamera() {
        try {
            console.log('Requesting camera access...');
            
            // Check if getUserMedia is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('getUserMedia not supported by this browser');
            }
            
            // Check for available cameras
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const cameras = devices.filter(device => device.kind === 'videoinput');
                console.log(`Found ${cameras.length} camera(s):`, cameras);
                
                if (cameras.length === 0) {
                    throw new Error('No cameras found on this device');
                }
            } catch (enumError) {
                console.warn('Could not enumerate devices:', enumError);
            }
            
            // Try with high resolution first, then fallback to lower resolution
            let constraints = {
                video: {
                    width: { ideal: 1920, min: 640 },
                    height: { ideal: 1080, min: 480 },
                    facingMode: 'user'
                },
                audio: false
            };

            try {
                this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            } catch (highResError) {
                console.warn('High resolution failed, trying basic constraints:', highResError);
                // Fallback to basic constraints
                constraints = {
                    video: {
                        width: { ideal: 1280, min: 640 },
                        height: { ideal: 720, min: 480 }
                    },
                    audio: false
                };
                
                try {
                    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
                } catch (mediumResError) {
                    console.warn('Medium resolution failed, trying minimal constraints:', mediumResError);
                    // Final fallback - minimal constraints
                    constraints = { video: true, audio: false };
                    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
                }
            }
            this.video.srcObject = this.stream;
            
            this.video.addEventListener('loadedmetadata', () => {
                console.log('Video metadata loaded:', {
                    videoWidth: this.video.videoWidth,
                    videoHeight: this.video.videoHeight,
                    readyState: this.video.readyState,
                    srcObject: !!this.video.srcObject
                });
                
                this.video.play().then(() => {
                    console.log('Video play started successfully');
                    console.log('Video element state:', {
                        paused: this.video.paused,
                        muted: this.video.muted,
                        currentTime: this.video.currentTime,
                        duration: this.video.duration
                    });
                    this.enableCaptureButton();
                }).catch(error => {
                    console.error('Video play failed:', error);
                    this.showCameraError(error);
                });
            });
            
            console.log('Camera initialized successfully');
            
        } catch (error) {
            console.error('Camera initialization failed:', error);
            this.showCameraError(error);
        }
    }

    setupEventListeners() {
        this.captureBtn.addEventListener('click', () => this.startPhotoSession());
        
        // Modal buttons - add safe event listeners
        const printBtn = document.getElementById('printBtn');
        const retakeBtn = document.getElementById('retakeBtn');
        
        if (printBtn) {
            printBtn.addEventListener('click', () => this.printPhoto());
            console.log('Print button event listener added');
        } else {
            console.warn('Print button not found');
        }
        
        if (retakeBtn) {
            retakeBtn.addEventListener('click', () => this.retakePhoto());
            console.log('Retake button event listener added');
        } else {
            console.warn('Retake button not found');
        }
        
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
        console.log('Camera ready, capture button enabled');
    }

    showCameraError(error = null) {
        const errorDiv = document.getElementById('cameraError');
        if (errorDiv) {
            errorDiv.classList.remove('hidden');
        }
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
        
        // Check if printing is allowed
        const printBtn = document.getElementById('printBtn');
        if (printBtn && printBtn.disabled) {
            this.showError('Printing is currently disabled. ' + (printBtn.title || 'Please check ink cartridge.'));
            return;
        }

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
        console.log('Retake photo initiated');
        
        if (!this.currentPhoto) {
            console.error('No current photo to retake');
            this.showError('No photo to retake');
            return;
        }

        console.log('Retaking photo:', this.currentPhoto.filename);
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

            console.log('Retake response status:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Retake response data:', data);

            if (data.success) {
                console.log('Retake successful, closing preview and resetting');
                this.closePreview();
                this.enableCaptureButton();
                this.currentPhoto = null;
                console.log('Retake complete - ready for new photo');
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
        console.log('Closing preview modal');
        const previewModal = document.getElementById('previewModal');
        const previewImage = document.getElementById('previewImage');
        
        if (previewModal) {
            previewModal.classList.add('hidden');
            previewModal.classList.remove('modal-enter');
        }
        
        if (previewImage) {
            previewImage.src = ''; // Clear image source
        }
        
        console.log('Preview modal closed');
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

    async loadFrameOverlay() {
        if (!this.frameOverlay) {
            console.warn('Frame overlay element not found');
            return;
        }
        
        try {
            console.log('Loading frame overlay...');
            const response = await fetch('/settings/api/frame/current');
            console.log('Frame API response:', response.status, response.statusText);
            
            if (response.ok) {
                // Frame exists, show the overlay
                const timestamp = Date.now();
                this.frameOverlay.src = `/settings/api/frame/current?v=${timestamp}`;
                this.frameOverlay.classList.remove('hidden');
                
                // Add load event listener
                this.frameOverlay.onload = () => {
                    console.log('Frame overlay image loaded successfully:', {
                        naturalWidth: this.frameOverlay.naturalWidth,
                        naturalHeight: this.frameOverlay.naturalHeight,
                        visible: !this.frameOverlay.classList.contains('hidden')
                    });
                };
                
                this.frameOverlay.onerror = (e) => {
                    console.error('Frame overlay failed to load:', e);
                    this.frameOverlay.classList.add('hidden');
                };
                
                console.log('Frame overlay setup complete');
            } else {
                // No frame available, hide overlay
                this.frameOverlay.classList.add('hidden');
                console.log('No frame overlay available (HTTP ' + response.status + ')');
            }
        } catch (error) {
            console.error('Could not load frame overlay:', error);
            this.frameOverlay.classList.add('hidden');
        }
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