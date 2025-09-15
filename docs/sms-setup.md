# SMS Photo Sharing Setup Guide

This guide provides step-by-step instructions for setting up SMS photo sharing functionality using SMS-Gate and ImgBB.

## Overview

The SMS photo sharing feature allows guests to instantly share photos via text message directly from the PhotoBooth interface. The system uses:
- **SMS-Gate**: Android app providing local SMS gateway
- **ImgBB**: Free image hosting service with 24-hour expiration
- **Local network**: All communication stays within the PhotoBooth network

## Prerequisites

### Hardware Requirements
- **Android device** (phone or tablet) with SMS capability
- **Active cellular plan** with sufficient SMS allowance
- **Same network** as PhotoBooth system (connects to PhotoBooth WiFi)

### Software Requirements
- **SMS-Gate app** (latest version from GitHub releases)
- **Android 6.0+** (API level 23 or higher)
- **SMS permissions** granted to SMS-Gate app

## SMS-Gate Installation

### Download and Install

1. **Download SMS-Gate APK:**
   - Visit [SMS-Gate GitHub Releases](https://github.com/capcom6/sms-gate/releases)
   - Download latest `sms-gate-vX.X.X.apk` file
   - Transfer to Android device or download directly

2. **Enable Unknown Sources:**
   - Go to Android Settings → Security
   - Enable "Unknown sources" or "Install unknown apps"
   - Allow installation from your file manager/browser

3. **Install SMS-Gate:**
   - Open downloaded APK file
   - Follow installation prompts
   - Grant necessary permissions when requested

### SMS-Gate Configuration

#### Initial Setup
1. **Open SMS-Gate app**
2. **Grant SMS permissions:**
   - Tap "Allow" when prompted for SMS access
   - Go to Settings → Apps → SMS-Gate → Permissions
   - Ensure SMS permission is enabled

3. **Configure server settings:**
   - **Host**: `0.0.0.0` (listen on all interfaces)
   - **Port**: `8080` (default, can be changed)
   - **Auto-start**: Enable (recommended)

4. **Create authentication:**
   - **Username**: `photobooth` (recommended)
   - **Password**: Create secure password
   - **API Token**: Generated automatically (note for PhotoBooth config)

5. **Start SMS-Gate service:**
   - Tap "Start Service"
   - Verify status shows "Running"
   - Note the IP address displayed (e.g., 192.168.50.101)

#### Advanced Configuration

**Message Settings:**
- **Max message length**: 160 characters (default)
- **Long message handling**: Split into multiple SMS
- **Delivery reports**: Enable for status tracking

**Security Settings:**
- **IP whitelist**: Add PhotoBooth IP (192.168.50.1) for security
- **Rate limiting**: 10 messages per minute (recommended)
- **Log level**: INFO (for troubleshooting)

**Network Settings:**
- **Bind address**: 0.0.0.0 (all interfaces)
- **Port**: 8080 (ensure not blocked by firewall)
- **Keep-alive**: Enable for better connection stability

## ImgBB Setup

### Account Creation

1. **Visit ImgBB:**
   - Go to [imgbb.com](https://imgbb.com)
   - Click "Sign up" to create free account
   - Verify email address

2. **Generate API Key:**
   - Login to ImgBB account
   - Go to [API page](https://api.imgbb.com/)
   - Click "Add API key"
   - Name: "PhotoBooth"
   - Copy the generated API key

### API Configuration
The PhotoBooth system uses ImgBB's free tier:
- **Storage**: Unlimited uploads
- **Expiration**: 24 hours (configurable)
- **File size**: 32MB maximum per image
- **Rate limits**: Generous for event usage

## PhotoBooth Configuration

### Environment Variables

Edit `/opt/photobooth/.env`:
```bash
# SMS Configuration
SMS_ENABLED=true
SMS_GATE_HOST=192.168.50.101
SMS_GATE_PORT=8080
SMS_GATE_USERNAME=photobooth
SMS_GATE_PASSWORD=your-sms-password
SMS_GATE_TOKEN=your-api-token

# ImgBB Configuration
IMGBB_API_KEY=your-imgbb-api-key
IMGBB_EXPIRATION=86400
```

### Settings Interface Configuration

1. **Access admin settings:**
   - Go to `https://192.168.50.1/settings`
   - Login with admin credentials

2. **Navigate to SMS section:**
   - Click "SMS" in settings menu
   - Configure gateway settings

3. **SMS Gateway Settings:**
   - **Host**: IP address of SMS-Gate device (e.g., 192.168.50.101)
   - **Port**: 8080 (or custom port if changed)
   - **Username**: photobooth
   - **Password**: SMS-Gate password

4. **Test connection:**
   - Click "Test Connection" button
   - Should show "Connection successful"
   - If failed, check network connectivity and credentials

### Country Code Configuration

The system supports international SMS with country codes:

```python
# In photobooth/sms.py
SUPPORTED_COUNTRIES = [
    {'code': 'US', 'name': 'United States', 'prefix': '+1'},
    {'code': 'CA', 'name': 'Canada', 'prefix': '+1'},
    {'code': 'GB', 'name': 'United Kingdom', 'prefix': '+44'},
    {'code': 'AU', 'name': 'Australia', 'prefix': '+61'},
    {'code': 'DE', 'name': 'Germany', 'prefix': '+49'},
    {'code': 'FR', 'name': 'France', 'prefix': '+33'},
    {'code': 'ES', 'name': 'Spain', 'prefix': '+34'},
    {'code': 'IT', 'name': 'Italy', 'prefix': '+39'},
    {'code': 'NL', 'name': 'Netherlands', 'prefix': '+31'},
    {'code': 'SE', 'name': 'Sweden', 'prefix': '+46'},
    {'code': 'NO', 'name': 'Norway', 'prefix': '+47'},
    {'code': 'DK', 'name': 'Denmark', 'prefix': '+45'},
    {'code': 'FI', 'name': 'Finland', 'prefix': '+358'},
    {'code': 'BE', 'name': 'Belgium', 'prefix': '+32'},
    {'code': 'CH', 'name': 'Switzerland', 'prefix': '+41'},
    {'code': 'AT', 'name': 'Austria', 'prefix': '+43'},
    {'code': 'IE', 'name': 'Ireland', 'prefix': '+353'},
    {'code': 'PT', 'name': 'Portugal', 'prefix': '+351'},
    {'code': 'GR', 'name': 'Greece', 'prefix': '+30'},
    {'code': 'PL', 'name': 'Poland', 'prefix': '+48'},
    {'code': 'CZ', 'name': 'Czech Republic', 'prefix': '+420'},
    {'code': 'HU', 'name': 'Hungary', 'prefix': '+36'},
    {'code': 'RO', 'name': 'Romania', 'prefix': '+40'},
    {'code': 'BG', 'name': 'Bulgaria', 'prefix': '+359'},
    {'code': 'HR', 'name': 'Croatia', 'prefix': '+385'},
    {'code': 'SI', 'name': 'Slovenia', 'prefix': '+386'},
    {'code': 'SK', 'name': 'Slovakia', 'prefix': '+421'},
    {'code': 'EE', 'name': 'Estonia', 'prefix': '+372'},
    {'code': 'LV', 'name': 'Latvia', 'prefix': '+371'},
    {'code': 'LT', 'name': 'Lithuania', 'prefix': '+370'},
    {'code': 'MT', 'name': 'Malta', 'prefix': '+356'},
    {'code': 'CY', 'name': 'Cyprus', 'prefix': '+357'},
    {'code': 'LU', 'name': 'Luxembourg', 'prefix': '+352'},
    {'code': 'IS', 'name': 'Iceland', 'prefix': '+354'},
    {'code': 'JP', 'name': 'Japan', 'prefix': '+81'},
    {'code': 'KR', 'name': 'South Korea', 'prefix': '+82'},
    {'code': 'CN', 'name': 'China', 'prefix': '+86'},
    {'code': 'IN', 'name': 'India', 'prefix': '+91'},
    {'code': 'SG', 'name': 'Singapore', 'prefix': '+65'},
    {'code': 'HK', 'name': 'Hong Kong', 'prefix': '+852'},
    {'code': 'TW', 'name': 'Taiwan', 'prefix': '+886'},
    {'code': 'MY', 'name': 'Malaysia', 'prefix': '+60'},
    {'code': 'TH', 'name': 'Thailand', 'prefix': '+66'},
    {'code': 'PH', 'name': 'Philippines', 'prefix': '+63'},
    {'code': 'ID', 'name': 'Indonesia', 'prefix': '+62'},
    {'code': 'VN', 'name': 'Vietnam', 'prefix': '+84'},
    {'code': 'MX', 'name': 'Mexico', 'prefix': '+52'},
    {'code': 'BR', 'name': 'Brazil', 'prefix': '+55'},
    {'code': 'AR', 'name': 'Argentina', 'prefix': '+54'},
    {'code': 'CL', 'name': 'Chile', 'prefix': '+56'},
    {'code': 'CO', 'name': 'Colombia', 'prefix': '+57'},
    {'code': 'PE', 'name': 'Peru', 'prefix': '+51'},
    {'code': 'UY', 'name': 'Uruguay', 'prefix': '+598'},
    {'code': 'PY', 'name': 'Paraguay', 'prefix': '+595'},
    {'code': 'BO', 'name': 'Bolivia', 'prefix': '+591'},
    {'code': 'EC', 'name': 'Ecuador', 'prefix': '+593'},
    {'code': 'VE', 'name': 'Venezuela', 'prefix': '+58'},
    {'code': 'ZA', 'name': 'South Africa', 'prefix': '+27'},
    {'code': 'EG', 'name': 'Egypt', 'prefix': '+20'},
    {'code': 'MA', 'name': 'Morocco', 'prefix': '+212'},
    {'code': 'DZ', 'name': 'Algeria', 'prefix': '+213'},
    {'code': 'TN', 'name': 'Tunisia', 'prefix': '+216'},
    {'code': 'LY', 'name': 'Libya', 'prefix': '+218'},
    {'code': 'SD', 'name': 'Sudan', 'prefix': '+249'},
    {'code': 'ET', 'name': 'Ethiopia', 'prefix': '+251'},
    {'code': 'KE', 'name': 'Kenya', 'prefix': '+254'},
    {'code': 'UG', 'name': 'Uganda', 'prefix': '+256'},
    {'code': 'TZ', 'name': 'Tanzania', 'prefix': '+255'},
    {'code': 'RW', 'name': 'Rwanda', 'prefix': '+250'},
    {'code': 'GH', 'name': 'Ghana', 'prefix': '+233'},
    {'code': 'NG', 'name': 'Nigeria', 'prefix': '+234'},
    {'code': 'CI', 'name': 'Ivory Coast', 'prefix': '+225'},
    {'code': 'SN', 'name': 'Senegal', 'prefix': '+221'},
    {'code': 'ML', 'name': 'Mali', 'prefix': '+223'},
    {'code': 'BF', 'name': 'Burkina Faso', 'prefix': '+226'},
    {'code': 'NE', 'name': 'Niger', 'prefix': '+227'},
    {'code': 'TD', 'name': 'Chad', 'prefix': '+235'},
    {'code': 'CF', 'name': 'Central African Republic', 'prefix': '+236'},
    {'code': 'CM', 'name': 'Cameroon', 'prefix': '+237'},
    {'code': 'GQ', 'name': 'Equatorial Guinea', 'prefix': '+240'},
    {'code': 'GA', 'name': 'Gabon', 'prefix': '+241'},
    {'code': 'CG', 'name': 'Republic of the Congo', 'prefix': '+242'},
    {'code': 'CD', 'name': 'Democratic Republic of the Congo', 'prefix': '+243'},
    {'code': 'AO', 'name': 'Angola', 'prefix': '+244'},
    {'code': 'GW', 'name': 'Guinea-Bissau', 'prefix': '+245'},
    {'code': 'IO', 'name': 'British Indian Ocean Territory', 'prefix': '+246'},
    {'code': 'SC', 'name': 'Seychelles', 'prefix': '+248'},
    {'code': 'MU', 'name': 'Mauritius', 'prefix': '+230'},
    {'code': 'MG', 'name': 'Madagascar', 'prefix': '+261'},
    {'code': 'YT', 'name': 'Mayotte', 'prefix': '+262'},
    {'code': 'RE', 'name': 'Réunion', 'prefix': '+262'},
    {'code': 'ZW', 'name': 'Zimbabwe', 'prefix': '+263'},
    {'code': 'NA', 'name': 'Namibia', 'prefix': '+264'},
    {'code': 'MW', 'name': 'Malawi', 'prefix': '+265'},
    {'code': 'LS', 'name': 'Lesotho', 'prefix': '+266'},
    {'code': 'BW', 'name': 'Botswana', 'prefix': '+267'},
    {'code': 'SZ', 'name': 'Eswatini', 'prefix': '+268'},
    {'code': 'KM', 'name': 'Comoros', 'prefix': '+269'},
    {'code': 'SH', 'name': 'Saint Helena', 'prefix': '+290'},
    {'code': 'ER', 'name': 'Eritrea', 'prefix': '+291'},
    {'code': 'AW', 'name': 'Aruba', 'prefix': '+297'},
    {'code': 'FO', 'name': 'Faroe Islands', 'prefix': '+298'},
    {'code': 'GL', 'name': 'Greenland', 'prefix': '+299'},
    {'code': 'GI', 'name': 'Gibraltar', 'prefix': '+350'},
    {'code': 'PT', 'name': 'Portugal', 'prefix': '+351'},
    {'code': 'LU', 'name': 'Luxembourg', 'prefix': '+352'},
    {'code': 'IE', 'name': 'Ireland', 'prefix': '+353'},
    {'code': 'IS', 'name': 'Iceland', 'prefix': '+354'},
    {'code': 'AL', 'name': 'Albania', 'prefix': '+355'},
    {'code': 'MT', 'name': 'Malta', 'prefix': '+356'},
    {'code': 'CY', 'name': 'Cyprus', 'prefix': '+357'},
    {'code': 'FI', 'name': 'Finland', 'prefix': '+358'},
    {'code': 'BG', 'name': 'Bulgaria', 'prefix': '+359'},
    {'code': 'LT', 'name': 'Lithuania', 'prefix': '+370'},
    {'code': 'LV', 'name': 'Latvia', 'prefix': '+371'},
    {'code': 'EE', 'name': 'Estonia', 'prefix': '+372'},
    {'code': 'MD', 'name': 'Moldova', 'prefix': '+373'},
    {'code': 'AM', 'name': 'Armenia', 'prefix': '+374'},
    {'code': 'BY', 'name': 'Belarus', 'prefix': '+375'},
    {'code': 'AD', 'name': 'Andorra', 'prefix': '+376'},
    {'code': 'MC', 'name': 'Monaco', 'prefix': '+377'},
    {'code': 'SM', 'name': 'San Marino', 'prefix': '+378'},
    {'code': 'VA', 'name': 'Vatican City', 'prefix': '+379'},
    {'code': 'UA', 'name': 'Ukraine', 'prefix': '+380'},
    {'code': 'RS', 'name': 'Serbia', 'prefix': '+381'},
    {'code': 'ME', 'name': 'Montenegro', 'prefix': '+382'},
    {'code': 'XK', 'name': 'Kosovo', 'prefix': '+383'},
    {'code': 'HR', 'name': 'Croatia', 'prefix': '+385'},
    {'code': 'SI', 'name': 'Slovenia', 'prefix': '+386'},
    {'code': 'BA', 'name': 'Bosnia and Herzegovina', 'prefix': '+387'},
    {'code': 'MK', 'name': 'North Macedonia', 'prefix': '+389'},
    {'code': 'IT', 'name': 'Italy', 'prefix': '+39'},
    {'code': 'RO', 'name': 'Romania', 'prefix': '+40'},
    {'code': 'CH', 'name': 'Switzerland', 'prefix': '+41'},
    {'code': 'CZ', 'name': 'Czech Republic', 'prefix': '+420'},
    {'code': 'SK', 'name': 'Slovakia', 'prefix': '+421'},
    {'code': 'LI', 'name': 'Liechtenstein', 'prefix': '+423'},
    {'code': 'AT', 'name': 'Austria', 'prefix': '+43'},
    {'code': 'GB', 'name': 'United Kingdom', 'prefix': '+44'},
    {'code': 'DK', 'name': 'Denmark', 'prefix': '+45'},
    {'code': 'SE', 'name': 'Sweden', 'prefix': '+46'},
    {'code': 'NO', 'name': 'Norway', 'prefix': '+47'},
    {'code': 'PL', 'name': 'Poland', 'prefix': '+48'},
    {'code': 'DE', 'name': 'Germany', 'prefix': '+49'},
    {'code': 'FK', 'name': 'Falkland Islands', 'prefix': '+500'},
    {'code': 'BZ', 'name': 'Belize', 'prefix': '+501'},
    {'code': 'GT', 'name': 'Guatemala', 'prefix': '+502'},
    {'code': 'SV', 'name': 'El Salvador', 'prefix': '+503'},
    {'code': 'HN', 'name': 'Honduras', 'prefix': '+504'},
    {'code': 'NI', 'name': 'Nicaragua', 'prefix': '+505'},
    {'code': 'CR', 'name': 'Costa Rica', 'prefix': '+506'},
    {'code': 'PA', 'name': 'Panama', 'prefix': '+507'},
    {'code': 'PM', 'name': 'Saint Pierre and Miquelon', 'prefix': '+508'},
    {'code': 'HT', 'name': 'Haiti', 'prefix': '+509'},
    {'code': 'PE', 'name': 'Peru', 'prefix': '+51'},
    {'code': 'MX', 'name': 'Mexico', 'prefix': '+52'},
    {'code': 'CU', 'name': 'Cuba', 'prefix': '+53'},
    {'code': 'AR', 'name': 'Argentina', 'prefix': '+54'},
    {'code': 'BR', 'name': 'Brazil', 'prefix': '+55'},
    {'code': 'CL', 'name': 'Chile', 'prefix': '+56'},
    {'code': 'CO', 'name': 'Colombia', 'prefix': '+57'},
    {'code': 'VE', 'name': 'Venezuela', 'prefix': '+58'},
    {'code': 'GP', 'name': 'Guadeloupe', 'prefix': '+590'},
    {'code': 'BO', 'name': 'Bolivia', 'prefix': '+591'},
    {'code': 'GY', 'name': 'Guyana', 'prefix': '+592'},
    {'code': 'EC', 'name': 'Ecuador', 'prefix': '+593'},
    {'code': 'GF', 'name': 'French Guiana', 'prefix': '+594'},
    {'code': 'PY', 'name': 'Paraguay', 'prefix': '+595'},
    {'code': 'MQ', 'name': 'Martinique', 'prefix': '+596'},
    {'code': 'SR', 'name': 'Suriname', 'prefix': '+597'},
    {'code': 'UY', 'name': 'Uruguay', 'prefix': '+598'},
    {'code': 'CW', 'name': 'Curaçao', 'prefix': '+599'},
    {'code': 'MY', 'name': 'Malaysia', 'prefix': '+60'},
    {'code': 'AU', 'name': 'Australia', 'prefix': '+61'},
    {'code': 'ID', 'name': 'Indonesia', 'prefix': '+62'},
    {'code': 'PH', 'name': 'Philippines', 'prefix': '+63'},
    {'code': 'NZ', 'name': 'New Zealand', 'prefix': '+64'},
    {'code': 'SG', 'name': 'Singapore', 'prefix': '+65'},
    {'code': 'TH', 'name': 'Thailand', 'prefix': '+66'},
    {'code': 'JP', 'name': 'Japan', 'prefix': '+81'},
    {'code': 'KR', 'name': 'South Korea', 'prefix': '+82'},
    {'code': 'VN', 'name': 'Vietnam', 'prefix': '+84'},
    {'code': 'CN', 'name': 'China', 'prefix': '+86'},
    {'code': 'TR', 'name': 'Turkey', 'prefix': '+90'},
    {'code': 'IN', 'name': 'India', 'prefix': '+91'},
    {'code': 'PK', 'name': 'Pakistan', 'prefix': '+92'},
    {'code': 'AF', 'name': 'Afghanistan', 'prefix': '+93'},
    {'code': 'LK', 'name': 'Sri Lanka', 'prefix': '+94'},
    {'code': 'MM', 'name': 'Myanmar', 'prefix': '+95'},
    {'code': 'MV', 'name': 'Maldives', 'prefix': '+960'},
    {'code': 'LB', 'name': 'Lebanon', 'prefix': '+961'},
    {'code': 'JO', 'name': 'Jordan', 'prefix': '+962'},
    {'code': 'SY', 'name': 'Syria', 'prefix': '+963'},
    {'code': 'IQ', 'name': 'Iraq', 'prefix': '+964'},
    {'code': 'KW', 'name': 'Kuwait', 'prefix': '+965'},
    {'code': 'SA', 'name': 'Saudi Arabia', 'prefix': '+966'},
    {'code': 'YE', 'name': 'Yemen', 'prefix': '+967'},
    {'code': 'OM', 'name': 'Oman', 'prefix': '+968'},
    {'code': 'PS', 'name': 'Palestine', 'prefix': '+970'},
    {'code': 'AE', 'name': 'United Arab Emirates', 'prefix': '+971'},
    {'code': 'IL', 'name': 'Israel', 'prefix': '+972'},
    {'code': 'BH', 'name': 'Bahrain', 'prefix': '+973'},
    {'code': 'QA', 'name': 'Qatar', 'prefix': '+974'},
    {'code': 'BT', 'name': 'Bhutan', 'prefix': '+975'},
    {'code': 'MN', 'name': 'Mongolia', 'prefix': '+976'},
    {'code': 'NP', 'name': 'Nepal', 'prefix': '+977'},
    {'code': 'IR', 'name': 'Iran', 'prefix': '+98'},
    {'code': 'TJ', 'name': 'Tajikistan', 'prefix': '+992'},
    {'code': 'TM', 'name': 'Turkmenistan', 'prefix': '+993'},
    {'code': 'AZ', 'name': 'Azerbaijan', 'prefix': '+994'},
    {'code': 'GE', 'name': 'Georgia', 'prefix': '+995'},
    {'code': 'KG', 'name': 'Kyrgyzstan', 'prefix': '+996'},
    {'code': 'UZ', 'name': 'Uzbekistan', 'prefix': '+998'}
]
```

## Testing SMS Setup

### Connection Testing

1. **SMS-Gate connectivity:**
   ```bash
   # From PhotoBooth system
   ping 192.168.50.101  # SMS-Gate device IP
   
   # Test API endpoint
   curl -X GET http://192.168.50.101:8080/health
   ```

2. **PhotoBooth SMS test:**
   - Access Settings → SMS section
   - Click "Test Connection"
   - Should show "Connection successful"

### End-to-End Testing

1. **Take test photo:**
   - Access PhotoBooth interface
   - Capture test photo
   - Select "Send SMS" option

2. **Send test SMS:**
   - Enter valid phone number
   - Select correct country code
   - Submit SMS request
   - Verify SMS received on test phone

3. **Verify image hosting:**
   - Check SMS contains valid image URL
   - Click link to verify image loads
   - Confirm image expires after 24 hours

## User Experience

### Guest Workflow

1. **Photo capture:**
   - Guest takes photo using PhotoBooth
   - Photo processed with frame overlay
   - Three options presented: Print, Send SMS, Retake

2. **SMS sharing process:**
   - Guest clicks "Send SMS" button
   - Phone number input dialog appears
   - Country code dropdown for international numbers
   - Guest enters phone number and submits

3. **SMS delivery:**
   - Photo uploads to ImgBB automatically
   - SMS sent via SMS-Gate to guest's phone
   - Success message displayed to guest
   - SMS contains download link for photo

### Message Format

**Default SMS message:**
```
🎉 Your PhotoBooth photo from [Event Name] is ready!

Download: https://i.ibb.co/abc123/photo_20240315_143022.jpg

This link expires in 24 hours. Enjoy your memories!
```

**Customizable message template:**
```python
# In photobooth/sms.py
SMS_MESSAGE_TEMPLATE = """🎉 Your PhotoBooth photo from {event_name} is ready!

Download: {image_url}

This link expires in 24 hours. Enjoy your memories!"""
```

## Troubleshooting

### Common Issues

#### SMS-Gate Connection Failed
**Symptoms:**
- "SMS gateway not reachable" error
- Connection test fails
- SMS sending fails immediately

**Solutions:**
1. **Check network connectivity:**
   ```bash
   ping 192.168.50.101  # SMS-Gate device IP
   nmap -p 8080 192.168.50.101  # Check port accessibility
   ```

2. **Verify SMS-Gate configuration:**
   - Ensure SMS-Gate service is running
   - Check IP address matches PhotoBooth config
   - Verify port 8080 is not blocked

3. **Update PhotoBooth configuration:**
   ```bash
   sudo nano /opt/photobooth/.env
   # Check SMS_GATE_HOST, SMS_GATE_PORT values
   sudo systemctl restart photobooth
   ```

#### SMS Delivery Failures
**Symptoms:**
- SMS appears sent but not received
- Delivery status shows "failed"
- Partial message delivery

**Solutions:**
1. **Check SMS-Gate logs:**
   - Open SMS-Gate app
   - Check log section for errors
   - Look for carrier/network issues

2. **Verify phone number format:**
   - Ensure correct international format
   - Include country code prefix
   - Remove any special characters

3. **Check carrier limitations:**
   - Some carriers block automated SMS
   - Verify SMS allowance not exceeded
   - Test with different phone numbers

#### Image Upload Failures
**Symptoms:**
- "Failed to upload image" error
- SMS sent without image link
- ImgBB upload timeouts

**Solutions:**
1. **Check internet connectivity:**
   ```bash
   # Test ImgBB API
   curl -X POST "https://api.imgbb.com/1/upload" \
     -F "key=your-api-key" \
     -F "image=@test.jpg"
   ```

2. **Verify ImgBB API key:**
   - Check API key is correct in .env file
   - Verify ImgBB account is active
   - Check API usage limits

3. **Image size optimization:**
   - Reduce photo quality if images too large
   - Monitor ImgBB file size limits (32MB max)

### Network Troubleshooting

#### Device Not Connecting to PhotoBooth WiFi
1. **SMS-Gate device WiFi:**
   - Connect Android device to PhotoBooth network
   - Verify device gets IP in range 192.168.50.x
   - Check device shows in DHCP leases

2. **IP address conflicts:**
   ```bash
   # Check DHCP leases
   cat /var/lib/dhcp/dhcpd.leases
   
   # Scan network for devices
   nmap -sn 192.168.50.0/24
   ```

#### Firewall Issues
1. **Android device firewall:**
   - Ensure SMS-Gate port 8080 is not blocked
   - Disable any security apps temporarily
   - Check Android hotspot/tethering settings

2. **PhotoBooth system firewall:**
   ```bash
   # Check firewall status
   sudo ufw status
   
   # Allow SMS-Gate port if needed
   sudo ufw allow from 192.168.50.0/24 to any port 8080
   ```

## Performance Optimization

### SMS-Gate Performance
- **Message queue**: Configure appropriate queue size for event volume
- **Rate limiting**: Balance speed with carrier limits
- **Memory usage**: Monitor Android device resources during events
- **Battery optimization**: Disable battery optimization for SMS-Gate app

### Network Performance
- **WiFi optimization**: Position SMS-Gate device for optimal signal
- **Bandwidth management**: Monitor network usage during peak times
- **Connection stability**: Use WiFi over cellular when possible

### ImgBB Optimization
- **Image compression**: Balance quality with upload speed
- **Concurrent uploads**: Limit simultaneous uploads to prevent timeouts
- **Retry logic**: Implement automatic retry for failed uploads

## Security Considerations

### Network Security
- **Device isolation**: SMS-Gate device isolated on PhotoBooth network
- **API authentication**: Secure SMS-Gate with strong credentials
- **Access control**: Limit SMS-Gate API access to PhotoBooth IP

### Data Privacy
- **Image expiration**: All images expire after 24 hours
- **Message logging**: Configure appropriate log retention
- **Phone number handling**: No permanent storage of guest phone numbers

### Event Security
- **Pre-event testing**: Verify all security settings before event
- **Monitoring**: Monitor SMS sending during event
- **Backup plan**: Have alternative sharing method ready

## Event Day Operations

### Pre-Event Setup
1. **SMS-Gate preparation:**
   - Ensure Android device fully charged
   - Connect to PhotoBooth WiFi network
   - Start SMS-Gate service and verify status
   - Test SMS delivery with multiple phone numbers

2. **PhotoBooth configuration:**
   - Verify SMS settings in admin interface
   - Test end-to-end SMS workflow
   - Check ImgBB connectivity and API limits

### During Event Monitoring
- **SMS-Gate status**: Periodically check app shows "Running"
- **Delivery monitoring**: Monitor SMS success rates
- **Network connectivity**: Ensure stable WiFi connection
- **Battery levels**: Monitor Android device battery

### Troubleshooting Support
- **Guest assistance**: Help with phone number entry if needed
- **Delivery issues**: Check SMS-Gate logs for failed messages
- **Alternative sharing**: Offer manual photo delivery if SMS fails

## Advanced Configuration

### Custom Message Templates
Create event-specific SMS messages:
```python
# In photobooth/sms.py
def get_sms_message(event_name, image_url, couple_names=None):
    if couple_names:
        message = f"🎊 Congratulations {couple_names}!\n\n"
    else:
        message = "🎉 "
    
    message += f"Your PhotoBooth photo from {event_name} is ready!\n\n"
    message += f"Download: {image_url}\n\n"
    message += "This link expires in 24 hours. Share the love! 💕"
    
    return message
```

### Multiple SMS Gateways
Configure backup SMS gateways for reliability:
```bash
# Primary SMS gateway
SMS_GATE_PRIMARY_HOST=192.168.50.101
SMS_GATE_PRIMARY_PORT=8080

# Backup SMS gateway
SMS_GATE_BACKUP_HOST=192.168.50.102
SMS_GATE_BACKUP_PORT=8080
```

### Analytics Integration
Track SMS sharing statistics:
```python
# In photobooth/models.py
def log_sms_analytics(photo_id, phone_country, delivery_status):
    # Log SMS usage patterns
    # Track popular sharing countries
    # Monitor delivery success rates
    pass
```

This comprehensive setup guide ensures reliable SMS photo sharing functionality for your PhotoBooth events. The system provides an engaging way for guests to instantly receive and share their PhotoBooth memories.