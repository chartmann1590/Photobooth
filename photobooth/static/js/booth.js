// PhotoBooth JavaScript
class PhotoBooth {
    constructor() {
        this.stream = null;
        this.video = document.getElementById('cameraPreview');
        this.captureBtn = document.getElementById('captureBtn');
        this.currentPhoto = null;
        
        this.init();
    }

    async init() {
        await this.initCamera();
        this.setupEventListeners();
        this.hideLoading();
    }

    async initCamera() {
        try {
            console.log('Requesting camera access...');
            
            const constraints = {
                video: {
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                    facingMode: 'user'
                },
                audio: false
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            
            this.video.addEventListener('loadedmetadata', () => {
                this.video.play();
                this.enableCaptureButton();
            });

            console.log('Camera initialized successfully');
            
        } catch (error) {
            console.error('Camera initialization failed:', error);
            this.showCameraError();
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

    showCameraError() {
        document.getElementById('cameraLoading').style.display = 'none';
        document.getElementById('cameraError').classList.remove('hidden');
        this.captureBtn.disabled = true;
        this.captureBtn.innerHTML = '<i class="fas fa-exclamation-triangle mr-4"></i>Camera Error';
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
    window.photoBooth = new PhotoBooth();
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