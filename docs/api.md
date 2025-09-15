# API Documentation

This document provides comprehensive API documentation for the PhotoBooth Flask application.

## Overview

The PhotoBooth application provides RESTful APIs for photo capture, gallery management, printing, SMS sharing, and system configuration. All APIs use JSON for data exchange and implement proper error handling.

### Base URL
```
https://192.168.50.1/
```

### Authentication
Admin endpoints require session authentication via the settings password.

## API Endpoints

### Health Check

#### GET /healthz
Check application health status.

**Response:**
```json
{
  "status": "healthy",
  "app": "photobooth"
}
```

## PhotoBooth Routes (/booth)

### Main Interface

#### GET /booth/
Serve the main photobooth interface.

**Response:** HTML page with camera interface

#### GET /booth/capture
Capture photo endpoint for the booth interface.

**Response:** HTML page with capture functionality

### Photo Capture

#### POST /booth/capture
Capture and save a photo.

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "apply_frame": true
}
```

**Response (Success):**
```json
{
  "success": true,
  "photo_id": 123,
  "filename": "photo_20240315_143022.jpg",
  "timestamp": "2024-03-15T14:30:22.123456",
  "thumbnail_url": "/booth/photo/123/thumbnail"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Failed to process image",
  "details": "Invalid image format"
}
```

### Photo Management

#### GET /booth/photo/<int:photo_id>
Get photo by ID.

**Parameters:**
- `photo_id` (int): Photo ID

**Response:**
- Returns image file (JPEG)
- 404 if photo not found

#### GET /booth/photo/<int:photo_id>/thumbnail
Get photo thumbnail.

**Parameters:**
- `photo_id` (int): Photo ID

**Response:**
- Returns thumbnail image (JPEG, 300x200)
- 404 if photo not found

#### DELETE /booth/photo/<int:photo_id>
Delete photo (admin only).

**Parameters:**
- `photo_id` (int): Photo ID

**Response:**
```json
{
  "success": true,
  "message": "Photo deleted successfully"
}
```

### Gallery

#### GET /booth/gallery
Get all photos for gallery display.

**Query Parameters:**
- `limit` (int, optional): Maximum number of photos (default: 50)
- `offset` (int, optional): Pagination offset (default: 0)
- `sort` (string, optional): Sort order ('date_desc', 'date_asc')

**Response:**
```json
{
  "photos": [
    {
      "id": 123,
      "filename": "photo_20240315_143022.jpg",
      "timestamp": "2024-03-15T14:30:22.123456",
      "thumbnail_url": "/booth/photo/123/thumbnail",
      "full_url": "/booth/photo/123",
      "printed": false,
      "print_count": 0,
      "sms_sent": true
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

#### GET /booth/gallery/download
Download all photos as ZIP archive.

**Response:**
- Returns ZIP file containing all photos
- Content-Type: application/zip
- Content-Disposition: attachment; filename="photobooth_photos.zip"

## Printing Routes

### Print Management

#### POST /booth/print/<int:photo_id>
Print a photo.

**Parameters:**
- `photo_id` (int): Photo ID to print

**Request Body (optional):**
```json
{
  "copies": 1,
  "printer": "Canon_SELPHY_CP760"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": 456,
  "message": "Print job submitted",
  "queue_position": 2
}
```

#### GET /booth/print/status/<int:job_id>
Get print job status.

**Parameters:**
- `job_id` (int): Print job ID

**Response:**
```json
{
  "job_id": 456,
  "status": "printing",
  "photo_id": 123,
  "printer": "Canon_SELPHY_CP760",
  "submitted_at": "2024-03-15T14:30:22.123456",
  "started_at": "2024-03-15T14:30:25.123456",
  "queue_position": 0
}
```

**Status Values:**
- `queued`: Waiting in print queue
- `printing`: Currently printing
- `completed`: Print job finished successfully
- `failed`: Print job failed
- `cancelled`: Print job cancelled

#### GET /booth/print/queue
Get current print queue.

**Response:**
```json
{
  "queue": [
    {
      "job_id": 456,
      "photo_id": 123,
      "status": "printing",
      "submitted_at": "2024-03-15T14:30:22.123456",
      "position": 0
    },
    {
      "job_id": 457,
      "photo_id": 124,
      "status": "queued",
      "submitted_at": "2024-03-15T14:31:15.123456",
      "position": 1
    }
  ],
  "total_jobs": 2
}
```

## SMS Sharing Routes

### SMS Management

#### POST /booth/sms/send/<int:photo_id>
Send photo via SMS.

**Parameters:**
- `photo_id` (int): Photo ID to send

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "country_code": "US"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "sms_id": 789,
  "image_url": "https://i.ibb.co/abc123/photo.jpg"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "SMS gateway unreachable",
  "details": "Connection timeout to SMS gateway"
}
```

#### GET /booth/sms/status/<int:sms_id>
Get SMS delivery status.

**Parameters:**
- `sms_id` (int): SMS message ID

**Response:**
```json
{
  "sms_id": 789,
  "phone_number": "+1234567890",
  "status": "delivered",
  "image_url": "https://i.ibb.co/abc123/photo.jpg",
  "sent_at": "2024-03-15T14:30:22.123456",
  "delivered_at": "2024-03-15T14:30:25.123456"
}
```

**Status Values:**
- `pending`: SMS queued for sending
- `sent`: SMS sent to gateway
- `delivered`: SMS confirmed delivered
- `failed`: SMS delivery failed

## Settings Routes (/settings)

### Authentication

#### GET /settings/
Settings login page.

**Response:** HTML login form

#### POST /settings/login
Authenticate admin user.

**Request Body:**
```json
{
  "password": "admin123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Login successful"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Invalid password"
}
```

#### POST /settings/logout
Logout admin user.

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### System Configuration

#### GET /settings/system
Get system status and configuration.

**Response:**
```json
{
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 67.2,
    "disk_usage": 45.1,
    "uptime": "2 days, 14:32:15",
    "temperature": 52.3
  },
  "services": {
    "photobooth": "active",
    "nginx": "active",
    "hostapd": "active",
    "dnsmasq": "active",
    "cups": "active"
  },
  "network": {
    "ssid": "PhotoBooth",
    "connected_devices": 5,
    "ip_address": "192.168.50.1"
  }
}
```

#### POST /settings/system/restart
Restart PhotoBooth service.

**Response:**
```json
{
  "success": true,
  "message": "Service restart initiated"
}
```

### Photo Settings

#### GET /settings/photos
Get photo configuration.

**Response:**
```json
{
  "config": {
    "photo_width": 1800,
    "photo_height": 1200,
    "photo_quality": 85,
    "frame_enabled": true,
    "current_frame": "wedding_frame_2024.png"
  },
  "stats": {
    "total_photos": 156,
    "storage_used": "2.3 GB",
    "storage_available": "12.7 GB"
  }
}
```

#### POST /settings/photos
Update photo configuration.

**Request Body:**
```json
{
  "photo_width": 1800,
  "photo_height": 1200,
  "photo_quality": 85,
  "frame_enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Photo settings updated"
}
```

### Frame Management

#### GET /settings/frame
Get current frame configuration.

**Response:**
```json
{
  "current_frame": "wedding_frame_2024.png",
  "frame_enabled": true,
  "available_frames": [
    "default_frame.png",
    "wedding_frame_2024.png",
    "vintage_frame.png"
  ]
}
```

#### POST /settings/frame/upload
Upload new frame overlay.

**Request:** Multipart form data
- `frame` (file): PNG file with transparency

**Response:**
```json
{
  "success": true,
  "filename": "new_frame.png",
  "message": "Frame uploaded successfully"
}
```

#### POST /settings/frame/set
Set active frame.

**Request Body:**
```json
{
  "frame": "wedding_frame_2024.png"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Frame set successfully"
}
```

### Printer Settings

#### GET /settings/printer
Get printer configuration and status.

**Response:**
```json
{
  "printers": [
    {
      "name": "Canon_SELPHY_CP760",
      "status": "idle",
      "is_default": true,
      "description": "Canon SELPHY CP760 Photo Printer"
    },
    {
      "name": "HP_DeskJet_3700",
      "status": "offline",
      "is_default": false,
      "description": "HP DeskJet 3700 series"
    }
  ],
  "print_stats": {
    "total_prints": 89,
    "successful_prints": 87,
    "failed_prints": 2,
    "queue_length": 0
  }
}
```

#### POST /settings/printer/set_default
Set default printer.

**Request Body:**
```json
{
  "printer_name": "Canon_SELPHY_CP760"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Default printer set"
}
```

#### POST /settings/printer/test
Print test page.

**Request Body (optional):**
```json
{
  "printer_name": "Canon_SELPHY_CP760"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": 999,
  "message": "Test print submitted"
}
```

### Audio Settings

#### GET /settings/audio
Get audio and TTS configuration.

**Response:**
```json
{
  "tts_enabled": true,
  "tts_voice": "en+f3",
  "tts_rate": 150,
  "available_voices": [
    {"id": "en", "name": "English (default)"},
    {"id": "en+f3", "name": "English female 3"},
    {"id": "en+m4", "name": "English male 4"}
  ],
  "audio_status": {
    "device": "Built-in audio",
    "volume": 80,
    "working": true
  }
}
```

#### POST /settings/audio
Update audio configuration.

**Request Body:**
```json
{
  "tts_enabled": true,
  "tts_voice": "en+f3",
  "tts_rate": 150
}
```

**Response:**
```json
{
  "success": true,
  "message": "Audio settings updated"
}
```

#### POST /settings/audio/test
Test TTS functionality.

**Request Body:**
```json
{
  "message": "Test message for text-to-speech",
  "voice": "en+f3",
  "rate": 150
}
```

**Response:**
```json
{
  "success": true,
  "message": "TTS test completed"
}
```

### SMS Settings

#### GET /settings/sms
Get SMS configuration and status.

**Response:**
```json
{
  "sms_enabled": true,
  "gateway_status": "connected",
  "gateway_config": {
    "host": "192.168.50.101",
    "port": 8080,
    "username": "photobooth"
  },
  "stats": {
    "total_sent": 34,
    "successful": 32,
    "failed": 2
  },
  "supported_countries": [
    {"code": "US", "name": "United States", "prefix": "+1"},
    {"code": "CA", "name": "Canada", "prefix": "+1"},
    {"code": "GB", "name": "United Kingdom", "prefix": "+44"}
  ]
}
```

#### POST /settings/sms
Update SMS configuration.

**Request Body:**
```json
{
  "sms_enabled": true,
  "gateway_host": "192.168.50.101",
  "gateway_port": 8080,
  "gateway_username": "photobooth",
  "gateway_password": "secure_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SMS settings updated"
}
```

#### POST /settings/sms/test
Test SMS gateway connection.

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "test_message": "PhotoBooth SMS test"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SMS test sent successfully"
}
```

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "success": false,
  "error": "Error type",
  "message": "Human-readable error message",
  "details": "Additional error details",
  "code": "ERROR_CODE",
  "timestamp": "2024-03-15T14:30:22.123456"
}
```

### Common Error Codes
- `INVALID_IMAGE`: Image format or size invalid
- `PHOTO_NOT_FOUND`: Requested photo doesn't exist
- `PRINTER_OFFLINE`: Selected printer not available
- `SMS_GATEWAY_ERROR`: SMS gateway connection failed
- `STORAGE_FULL`: Insufficient disk space
- `AUTHENTICATION_FAILED`: Invalid credentials
- `VALIDATION_ERROR`: Request data validation failed

## Rate Limiting

### Limits
- Photo capture: 10 requests per minute per IP
- SMS sending: 5 requests per minute per IP
- API calls: 100 requests per minute per IP
- File uploads: 3 requests per minute per IP

### Rate Limit Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1710511822
```

## WebSocket Events

### Real-time Updates
The application supports WebSocket connections for real-time updates.

**Connection:** `wss://192.168.50.1/ws`

### Event Types

#### print_status
Print job status updates.
```json
{
  "event": "print_status",
  "data": {
    "job_id": 456,
    "status": "printing",
    "progress": 75
  }
}
```

#### sms_status
SMS delivery status updates.
```json
{
  "event": "sms_status",
  "data": {
    "sms_id": 789,
    "status": "delivered",
    "phone_number": "+1234567890"
  }
}
```

#### system_status
System health updates.
```json
{
  "event": "system_status",
  "data": {
    "cpu_usage": 30.5,
    "memory_usage": 70.2,
    "connected_devices": 8
  }
}
```

## SDK Examples

### JavaScript (Browser)
```javascript
// Capture photo
async function capturePhoto(imageData) {
  const response = await fetch('/booth/capture', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image: imageData,
      apply_frame: true
    })
  });
  
  return await response.json();
}

// Print photo
async function printPhoto(photoId) {
  const response = await fetch(`/booth/print/${photoId}`, {
    method: 'POST'
  });
  
  return await response.json();
}

// Send SMS
async function sendSMS(photoId, phoneNumber) {
  const response = await fetch(`/booth/sms/send/${photoId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      phone_number: phoneNumber,
      country_code: 'US'
    })
  });
  
  return await response.json();
}
```

### Python
```python
import requests
import base64

class PhotoBoothAPI:
    def __init__(self, base_url="https://192.168.50.1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Self-signed certificate
    
    def capture_photo(self, image_data, apply_frame=True):
        url = f"{self.base_url}/booth/capture"
        data = {
            "image": image_data,
            "apply_frame": apply_frame
        }
        response = self.session.post(url, json=data)
        return response.json()
    
    def get_gallery(self, limit=50, offset=0):
        url = f"{self.base_url}/booth/gallery"
        params = {"limit": limit, "offset": offset}
        response = self.session.get(url, params=params)
        return response.json()
    
    def print_photo(self, photo_id, copies=1):
        url = f"{self.base_url}/booth/print/{photo_id}"
        data = {"copies": copies}
        response = self.session.post(url, json=data)
        return response.json()

# Usage example
api = PhotoBoothAPI()

# Capture photo
with open("photo.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()
    image_data = f"data:image/jpeg;base64,{image_data}"

result = api.capture_photo(image_data)
print(f"Photo captured: {result}")

# Print photo
if result["success"]:
    print_result = api.print_photo(result["photo_id"])
    print(f"Print job: {print_result}")
```

## Security Considerations

### HTTPS Only
All API endpoints require HTTPS. HTTP requests are automatically redirected.

### Input Validation
- All file uploads are validated for type and size
- Phone numbers are validated for format
- Image data is validated for format and content

### Rate Limiting
API endpoints implement rate limiting to prevent abuse.

### Session Management
Admin sessions expire after inactivity and require re-authentication.

### Data Sanitization
All user inputs are sanitized to prevent XSS and injection attacks.