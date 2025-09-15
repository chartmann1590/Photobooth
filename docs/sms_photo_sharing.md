# SMS Photo Sharing Feature

## Overview

The PhotoBooth SMS feature allows users to share photos via SMS using a combination of free image hosting and local SMS gateway integration. This feature provides seamless photo sharing directly from the gallery interface.

## Architecture

### Components

1. **SMS Service Module** (`photobooth/sms.py`)
   - Handles image upload to ImgBB
   - Manages SMS sending via SMS-Gate
   - Provides connectivity testing and status checking

2. **Database Integration** (`photobooth/models.py`)
   - SMS message tracking and logging
   - Statistics collection and reporting
   - Message history management

3. **Admin Interface** (`/settings/sms`)
   - SMS-Gate configuration
   - Gateway status monitoring
   - Message statistics dashboard

4. **User Interface** (Gallery SMS Modal)
   - Phone number input
   - Custom message composition
   - Real-time sending feedback

## Technical Implementation

### Image Hosting - ImgBB Integration

**Service**: [ImgBB](https://imgbb.com/) - Free image hosting
**API Endpoint**: `https://api.imgbb.com/1/upload`
**Features**:
- No registration required
- 24-hour image expiration (free tier)
- Direct image URLs for SMS sharing
- Base64 image upload support

**Implementation Details**:
```python
def upload_image_to_imgbb(image_path: str) -> Dict[str, Any]:
    # Read and encode image as base64
    with open(image_path, 'rb') as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Upload to ImgBB with 24-hour expiration
    payload = {
        'image': image_data,
        'expiration': 86400  # 24 hours
    }
```

### SMS Gateway - SMS-Gate Integration

**Service**: [SMS-Gate](https://docs.sms-gate.app/) - Local SMS server
**Requirements**: 
- Local SMS-Gate server running on network
- Android device with SMS-Gate app
- Network connectivity between PhotoBooth and SMS-Gate

**API Integration**:
```python
def send_sms_via_gateway(phone_number: str, message: str) -> Dict[str, Any]:
    api_url = f"http://{gateway_host}/api/3rdparty/v1/message"
    payload = {
        'message': message,
        'phoneNumbers': [phone_number]
    }
    # HTTP Basic Auth with configured credentials
```

## Setup Guide

### 1. SMS-Gate Server Setup

**Prerequisites**:
- Android device (phone or tablet)
- SMS-Gate app installed
- Device connected to same network as PhotoBooth

**Installation Steps**:

1. **Install SMS-Gate App**:
   - Download from [SMS-Gate Releases](https://github.com/capcom6/sms-gate/releases)
   - Install on Android device
   - Grant SMS permissions

2. **Configure SMS-Gate Server**:
   ```bash
   # Start SMS-Gate server on Android device
   # Note the IP address and port (default: 8080)
   # Create username and password for API access
   ```

3. **Network Configuration**:
   - Ensure Android device has static IP or DHCP reservation
   - Verify PhotoBooth can reach SMS-Gate server
   - Test connectivity: `curl http://[SMS-Gate-IP]:8080/api/3rdparty/v1/health`

### 2. PhotoBooth Configuration

1. **Access SMS Settings**:
   - Navigate to PhotoBooth admin: `/settings/sms`
   - Login with admin credentials

2. **Configure Gateway Settings**:
   - **Gateway Host/IP**: `192.168.1.100:8080` (SMS-Gate server address)
   - **Username**: SMS-Gate API username
   - **Password**: SMS-Gate API password

3. **Test Configuration**:
   - Click "Test SMS Gateway" button
   - Verify "Gateway Connected" status
   - Check connectivity and credentials

### 3. Image Hosting Configuration

ImgBB integration is automatically configured and requires no additional setup:
- **No API key required** (uses free tier)
- **Automatic expiration**: Images expire after 24 hours
- **Privacy notice**: Users are informed about ImgBB hosting

## User Workflow

### Sending Photo via SMS

**From Main Booth Interface (Primary Method)**:

1. **Take Photo**:
   - Use main PhotoBooth interface at `/booth`
   - Take photo with camera

2. **Photo Preview**:
   - Photo preview modal shows with three options:
   - **Print Photo** - Send to printer
   - **Send SMS** - Share via text message
   - **Take Another** - Retake the photo

3. **SMS Sharing**:
   - Click "Send SMS" button
   - Enter recipient phone number
   - Add optional custom message
   - Click "Send SMS"

4. **SMS Delivery**:
   - Photo uploads to ImgBB (progress shown)
   - SMS sent via SMS-Gate with image URL
   - Success/failure notification displayed

**From Admin Gallery (Alternative Method)**:

1. **Access Gallery**:
   - Navigate to `/settings/gallery`
   - View captured photos

2. **Select Photo**:
   - Click on any photo to open preview
   - Click "Send SMS" button

3. **Same SMS process** as above

### SMS Message Format

**Default Message**:
```
Here's your photo from the PhotoBooth! [IMAGE_URL]

(Hosted on ImgBB, expires in 24 hours)
```

**Custom Message Example**:
```
Thanks for celebrating with us! [CUSTOM_MESSAGE]

Your photo: [IMAGE_URL]

(Hosted on ImgBB, expires in 24 hours)
```

## Administrative Features

### SMS Statistics Dashboard

**Available Metrics**:
- Total SMS messages sent
- Successful deliveries
- Failed attempts
- Messages sent today

**Recent Message History**:
- Phone numbers (masked for privacy)
- Delivery status
- Image URLs
- Timestamp
- Error messages (if any)

### Gateway Management

**Status Monitoring**:
- Real-time connectivity checks
- Gateway server availability
- Configuration validation

**Testing Tools**:
- Connection test button
- Health check endpoint
- Error diagnostics

## Database Schema

### SMS Messages Table

```sql
CREATE TABLE sms_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL,
    image_url TEXT,
    status TEXT NOT NULL,  -- 'sent' or 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Settings Integration

SMS configuration stored in main settings table:
- `sms_gateway_host`: SMS-Gate server address
- `sms_gateway_username`: API authentication username  
- `sms_gateway_password`: API authentication password

## API Endpoints

### User Endpoints

**Send Photo SMS**:
```http
POST /booth/api/sms
Content-Type: application/json

{
    "filename": "photo.jpg",
    "phone_number": "+1234567890",
    "message": "Custom message (optional)"
}
```

### Admin Endpoints

**Gateway Status**:
```http
GET /settings/api/sms/status
```

**Update Configuration**:
```http
POST /settings/api/sms/config
Content-Type: application/json

{
    "gateway_host": "192.168.1.100:8080",
    "gateway_username": "admin",
    "gateway_password": "password"
}
```

**Test Gateway**:
```http
POST /settings/api/sms/test
```

## Security Considerations

### Data Privacy

- **Phone Numbers**: Stored temporarily for logging, consider retention policies
- **Images**: Hosted on external service (ImgBB) with 24-hour expiration
- **Messages**: SMS content logged for debugging purposes

### Access Control

- **Admin Interface**: Protected by authentication
- **SMS Endpoints**: Rate limiting recommended
- **Gateway Credentials**: Stored securely in database

### Network Security

- **SMS-Gate Communication**: HTTP (consider HTTPS for production)
- **ImgBB Upload**: HTTPS encrypted
- **Local Network**: Ensure SMS-Gate device security

## Troubleshooting

### Common Issues

**"SMS gateway not configured"**:
- Verify all three settings are filled in `/settings/sms`
- Test gateway connectivity

**"Gateway returned status 401"**:
- Check username/password credentials
- Verify SMS-Gate authentication settings

**"Image upload failed"**:
- Check internet connectivity
- Verify photo file exists and is readable
- ImgBB service availability

**"Connection refused"**:
- Verify SMS-Gate server is running
- Check IP address and port
- Confirm network connectivity

### Debug Steps

1. **Check SMS-Gate Status**:
   ```bash
   curl http://[SMS-Gate-IP]:8080/api/3rdparty/v1/health
   ```

2. **Test Image Upload**:
   - Monitor network traffic during upload
   - Check PhotoBooth logs for ImgBB responses

3. **Verify Phone Number Format**:
   - Ensure proper international format
   - Test with known working numbers

4. **Review Logs**:
   ```bash
   tail -f /opt/photobooth/photobooth.log | grep -i sms
   ```

## Performance Considerations

### Image Upload Optimization

- **File Size**: Photos automatically resized for web sharing
- **Upload Time**: ~2-5 seconds per photo (depending on connection)
- **Concurrent Uploads**: Limited by ImgBB rate limits

### SMS Delivery

- **Delivery Time**: Usually instant via SMS-Gate
- **Queue Management**: SMS-Gate handles message queuing
- **Error Handling**: Automatic retry logic in SMS-Gate

## Future Enhancements

### Potential Improvements

1. **Multiple Image Hosts**: Support for additional hosting services
2. **QR Code Sharing**: Generate QR codes for photo URLs
3. **Batch SMS**: Send multiple photos in single SMS
4. **Custom Expiration**: Configurable image expiration times
5. **SMS Templates**: Predefined message templates
6. **Analytics**: Enhanced usage statistics and reporting

### Integration Opportunities

- **Social Media**: Direct sharing to Instagram/Facebook
- **Email**: Alternative sharing method
- **Cloud Storage**: Integration with Google Drive/Dropbox
- **Print Ordering**: SMS-based print requests

## Support and Resources

### Documentation Links

- [SMS-Gate Official Documentation](https://docs.sms-gate.app/)
- [SMS-Gate GitHub Repository](https://github.com/capcom6/sms-gate)
- [ImgBB API Documentation](https://api.imgbb.com/)

### Community Resources

- [SMS-Gate Community Forum](https://github.com/capcom6/sms-gate/discussions)
- [PhotoBooth Project Issues](https://github.com/your-repo/photobooth/issues)

### Getting Help

For SMS feature support:
1. Check this documentation
2. Review PhotoBooth logs
3. Test SMS-Gate connectivity
4. Submit issue with full error details