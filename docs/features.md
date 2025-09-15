# Features Guide

This guide provides detailed information about all PhotoBooth features and how to use them effectively.

## Core PhotoBooth Features

### Photo Capture System

#### Camera Interface
- **Full-screen camera view** optimized for tablets and phones
- **Front/back camera toggle** for selfie or portrait modes
- **Touch-friendly controls** with large, obvious buttons
- **Real-time preview** showing frame overlay before capture
- **Auto-focus and exposure** handled by browser camera API

#### Countdown System
- **Visual countdown** with large numbers (3-2-1)
- **Audio announcements** via text-to-speech
- **Custom countdown messages**:
  - "Get ready for your photo!"
  - "3... 2... 1... Smile!"
  - "Perfect! Your photo is ready!"

#### Photo Processing
- **Instant capture** via HTML5 canvas
- **Automatic resizing** to 1800×1200 pixels (4:3 aspect ratio)
- **Frame overlay application** with transparency support
- **Quality optimization** for Pi 3B performance
- **Immediate preview** with print/SMS/retake options
- **Wedding-themed favicon** for professional mobile app experience

### Frame Overlay System

#### Supported Formats
- **PNG files** with transparency (required)
- **Recommended size**: 1800×1200 pixels
- **Design area**: Transparent center for faces, decorated borders
- **File size limit**: 10MB maximum

#### Upload Process
1. Access Settings → Frame section
2. Choose PNG file with transparency
3. Preview shows overlay on sample photo
4. Save to apply to all future photos
5. Previous frame backed up automatically

#### Design Guidelines
- **Keep center clear** - faces should be visible
- **Use wedding colors** and theme
- **Include couple information**: names, date, venue
- **Add hashtags** or social media handles
- **Test transparency** on different backgrounds

### Printing System

#### Printer Support
- **USB connection** via CUPS integration
- **Auto-detection** of most USB printers
- **Manual configuration** via CUPS web interface
- **4×6 photo optimization** (1800×1200 @ 300 DPI)
- **Queue management** with retry capability

#### Tested Printers
- **Canon SELPHY** CP760, CP800, CP900 series
- **HP DeskJet** 2600, 3700, 4100 series
- **Epson Expression** Home series
- **Generic photo printers** with Linux drivers

#### Print Workflow
1. Guest takes photo
2. Photo processed with frame overlay
3. "Print" button available immediately
4. Photo sent to print queue
5. Status updates in real-time
6. Reprint available from gallery

### SMS Photo Sharing

#### How It Works
- **Instant sharing** after photo capture with audio feedback
- **Dual image hosting** via 0x0.st (primary) and ImgBB (fallback)
- **Local SMS gateway** using SMS-Gate app
- **Wedding-themed messaging** with automated introduction
- **Audio alerts** for success/failure via TTS
- **No external fees** or API keys required (0x0.st)
- **Privacy-conscious** with automatic 24-hour expiration

#### Setup Requirements
- **Android device** with SMS capability
- **SMS-Gate app** installed and configured
- **Same network** as PhotoBooth system
- **Valid phone numbers** for testing

#### User Experience
1. Guest takes photo
2. Three options appear: Print / Send SMS / Retake
3. "Send SMS" opens phone number input with progressive feedback
4. Photo uploads with status messages ("Uploading image...", "Sending SMS...")
5. SMS sent with wedding-themed message and photo link
6. **Audio feedback**: "SMS sent successfully!" or "SMS sending failed. Please try again."
7. Success confirmation shown with service details

### Gallery Management

#### Admin Gallery Features
- **Thumbnail view** of all captured photos
- **Full-size preview** with frame overlay
- **Download individual** photos or bulk ZIP
- **Reprint functionality** for any photo
- **SMS sharing** from gallery
- **Delete photos** with confirmation
- **Sort by date** (newest first)

#### Storage Organization
```
data/photos/
├── all/           # All captured photos
├── printed/       # Backup of printed photos
└── thumbnails/    # Auto-generated thumbnails
```

#### Metadata Tracking
- **Capture timestamp** with timezone
- **Print status** and count
- **SMS delivery** status
- **File information** (size, dimensions)
- **Frame overlay** used

### Audio & Text-to-Speech

#### Voice Features
- **eSpeak NG engine** with multiple voices
- **Customizable speech rate** (80-300 WPM)
- **Non-blocking audio** - UI remains responsive
- **Volume control** via system mixer
- **Voice selection** from available options

#### Available Messages
- **Welcome message**: "Welcome to the PhotoBooth!"
- **Countdown**: "Get ready... 3... 2... 1... Smile!"
- **Capture success**: "Perfect! Your photo is ready!"
- **Print started**: "Your photo is printing!"
- **SMS success**: "SMS sent successfully!"
- **SMS error**: "SMS sending failed. Please try again."

#### Configuration
- **Enable/disable** TTS globally
- **Select voice** from dropdown
- **Adjust speech rate** with slider
- **Test messages** with preview button
- **Custom messages** support

### WiFi Hotspot System

#### Network Configuration
- **SSID**: PhotoBooth (customizable)
- **Password**: photobooth123 (customizable)
- **IP Range**: 192.168.50.0/24
- **Gateway**: 192.168.50.1
- **DHCP**: Automatic IP assignment

#### Captive Portal
- **Automatic redirect** to PhotoBooth interface
- **HTTPS enforcement** for camera access
- **TLS certificate** auto-trusted on devices
- **Cross-platform** compatibility (iOS, Android, Windows, Mac)

#### Network Features
- **Up to 10 concurrent** devices
- **Internet sharing** via ethernet (optional)
- **Device isolation** for privacy
- **Bandwidth management** optimized for photos

## Admin Interface Features

### Settings Dashboard
- **System status** overview
- **Service health** monitoring
- **Storage usage** display
- **Recent activity** log
- **Quick actions** for common tasks

### Security Features
- **Password protection** for admin access
- **Session management** with timeout
- **Secure cookie** settings
- **HTTPS enforcement** throughout
- **Input validation** and sanitization

### Configuration Management
- **Real-time updates** without restart
- **Backup configuration** automatic
- **Restore defaults** option
- **Export settings** for backup
- **Import settings** from backup

## Technical Features

### Performance Optimizations
- **Lazy loading** for gallery thumbnails
- **Image compression** optimized for Pi 3B
- **Caching strategies** for static assets
- **Efficient database** queries
- **Memory management** for long-running operation

### Browser Compatibility
- **Modern browsers** required for camera API
- **iOS Safari** full support (iOS 11+)
- **Android Chrome** full support (Android 6+)
- **Desktop browsers** for admin interface
- **Progressive enhancement** for older devices

### Database Features
- **SQLite backend** for simplicity
- **ACID compliance** for data integrity
- **Automatic backups** before major operations
- **Migration support** for updates
- **Vacuum operations** for performance

### Error Handling
- **Graceful degradation** when features unavailable
- **User-friendly error** messages
- **Automatic retry** for transient failures
- **Detailed logging** for troubleshooting
- **Recovery procedures** for common issues

## Usage Scenarios

### Wedding Reception
- **300+ guests** typical usage
- **4-6 hour** continuous operation
- **2-3 photos per guest** average
- **Mixed device types** (phones, tablets)
- **Low lighting** venue support

### Corporate Events
- **Professional appearance** with custom frames
- **Branded experience** with company colors
- **Lead capture** via optional contact forms
- **Social media** integration ready
- **Multi-day events** supported

### Private Parties
- **Intimate gatherings** (10-50 people)
- **Casual atmosphere** with fun frames
- **Instant gratification** with immediate prints
- **Memory preservation** with automatic gallery
- **Easy sharing** via SMS

## Feature Limitations

### Hardware Constraints
- **Raspberry Pi 3B**: Limited processing power affects photo processing speed
- **2.4GHz WiFi only**: Cannot use 5GHz networks
- **USB 2.0**: Slower data transfer for large photo volumes
- **1GB RAM**: Limits concurrent processing

### Software Limitations
- **Browser camera API**: Requires HTTPS and user interaction
- **Print queue**: Single printer support at a time
- **SMS gateway**: Requires Android device on same network
- **Storage**: Limited by microSD card capacity

### Network Limitations
- **Range**: ~30-50 feet typical indoor coverage
- **Concurrent users**: 10 device recommended maximum
- **Bandwidth**: Optimized for photo sharing, not video
- **Internet**: Offline operation only (unless ethernet connected)

## Accessibility Features

### Visual Accessibility
- **High contrast** UI elements
- **Large touch targets** (44px minimum)
- **Clear typography** with readable fonts
- **Color coding** with additional indicators
- **Zoom support** on mobile devices

### Motor Accessibility
- **Large buttons** easy to press
- **Gesture support** for common actions
- **Voice feedback** for button presses
- **Timeout extensions** for slower users
- **Simplified workflow** with minimal steps

### Cognitive Accessibility
- **Clear instructions** at each step
- **Visual feedback** for all actions
- **Error prevention** with confirmation dialogs
- **Consistent navigation** throughout interface
- **Help text** available context-sensitively

## Future Features

### Planned Enhancements
- **Video recording** support (hardware permitting)
- **Multiple frame** selection per session
- **Social media** direct posting
- **QR code sharing** for photo downloads
- **Analytics dashboard** for event insights

### Community Requests
- **GIF creation** from burst photos
- **Green screen** background replacement
- **Face recognition** for automatic tagging
- **Email sharing** alternative to SMS
- **Multi-language** interface support