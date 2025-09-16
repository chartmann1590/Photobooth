# Immich Gallery Sync Documentation

## Overview

The PhotoBooth Immich sync feature provides seamless automatic backup of all captured photos to your personal [Immich](https://immich.app/) photo server. This ensures your wedding memories are safely stored in your own cloud infrastructure with full privacy and control.

## ✨ Key Features

- **🔄 Real-time Sync**: Photos uploaded immediately after capture
- **📁 Smart Album Management**: Automatically creates albums if they don't exist
- **🔍 Duplicate Detection**: SHA1 checksums prevent redundant uploads
- **📦 Bulk Sync**: Upload existing photo libraries with one click
- **⚙️ Configurable Options**: Full control over sync behavior
- **🧪 Connection Testing**: Built-in connectivity and album browsing
- **🔒 Privacy-Focused**: Uses your own server, no third-party services
- **⚡ Non-blocking**: Background operations don't affect booth performance

## 🏗️ Prerequisites

Before setting up Immich sync, you'll need:

### 1. Immich Server
- **Running Immich instance** on your network or cloud
- **Version compatibility**: Tested with Immich v1.90+ (should work with most recent versions)
- **Network access** from PhotoBooth Pi to Immich server
- **Storage space** for your photo collection

### 2. API Authentication
- **User account** on your Immich server
- **API key** generated from user settings
- **Appropriate permissions** for album creation and asset upload

### 3. Network Configuration
- **HTTP/HTTPS access** to Immich server from PhotoBooth
- **Firewall rules** allowing outbound connections (if applicable)
- **DNS resolution** if using domain names

## 🚀 Installation & Setup

### Step 1: Install Immich Server

Follow the [official Immich installation guide](https://immich.app/docs/install/requirements) for your platform:

**Docker Compose (Recommended):**
```bash
# Download official docker-compose.yml
curl -o docker-compose.yml https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml

# Start Immich stack
docker-compose up -d
```

**Other Installation Methods:**
- [Docker](https://immich.app/docs/install/docker-compose)
- [Unraid](https://immich.app/docs/install/unraid)
- [Proxmox](https://immich.app/docs/install/proxmox)

### Step 2: Create User Account

1. **Access Immich web interface** (typically `http://your-server:2283`)
2. **Create admin account** during first setup
3. **Add user account** for PhotoBooth (optional, can use admin)
4. **Note login credentials** for API key generation

### Step 3: Generate API Key

1. **Log into Immich web interface**
2. **Go to User Settings** (profile icon → Account Settings)
3. **Navigate to API Keys section**
4. **Click "Create API Key"**
5. **Give it a descriptive name** (e.g., "PhotoBooth Sync")
6. **Copy the generated API key** (you won't see it again!)

### Step 4: Configure PhotoBooth

1. **Access PhotoBooth Settings**: `https://192.168.50.1/settings`
2. **Navigate to Gallery section**
3. **Click "Immich Gallery Sync (Optional)"** to expand the configuration panel
4. **Fill in connection details**:
   - **Server URL**: Full URL to your Immich server (e.g., `https://immich.example.com` or `http://192.168.1.100:2283`)
   - **API Key**: Paste the API key from Step 3
   - **Album Name**: Name for PhotoBooth album (e.g., "Wedding PhotoBooth", "Party Photos")

5. **Configure sync options**:
   - **Enable Immich Sync**: Master on/off switch
   - **Auto Sync**: Automatically sync all existing photos
   - **Sync on Capture**: Upload new photos immediately after capture

6. **Test connection** using the "Test Connection" button
7. **Save settings** once connection is verified

## ⚙️ Configuration Options

### Sync Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Enable Immich Sync** | Master switch for all sync functionality | `false` |
| **Server URL** | Full HTTP/HTTPS URL to your Immich server | `""` |
| **API Key** | Authentication key from Immich user settings | `""` |
| **Album Name** | Target album for PhotoBooth photos | `"PhotoBooth"` |
| **Auto Sync** | Sync all photos in library automatically | `true` |
| **Sync on Capture** | Upload photos immediately after taking them | `true` |

### Advanced Configuration

For advanced users, additional settings can be configured in the database:

```sql
-- Example: Disable sync temporarily
UPDATE settings SET value = 'false' WHERE key = 'immich_enabled';

-- Example: Change album name
UPDATE settings SET value = 'Wedding2024' WHERE key = 'immich_album_name';
```

## 🎯 Usage Scenarios

### Scenario 1: Real-time Wedding Backup

**Goal**: Automatically backup every photo as guests take them

**Configuration**:
- Enable Immich Sync: ✅
- Sync on Capture: ✅
- Auto Sync: ✅
- Album Name: "Wedding - Smith & Jones"

**Behavior**:
- Photos upload immediately after capture
- Album created automatically if needed
- Duplicates detected and skipped
- Background operation, no delays for guests

### Scenario 2: Manual Batch Sync

**Goal**: Sync photos manually at end of event

**Configuration**:
- Enable Immich Sync: ✅
- Sync on Capture: ❌
- Auto Sync: ❌
- Album Name: "Event Photos"

**Usage**:
- Take photos normally during event
- Use "Sync All Photos" button when ready
- Monitor progress in admin interface

### Scenario 3: Selective Sync

**Goal**: Only sync specific photos, not all captures

**Configuration**:
- Enable Immich Sync: ✅
- Sync on Capture: ❌
- Auto Sync: ❌
- Album Name: "Best Photos"

**Usage**:
- Review photos in gallery
- Manually trigger sync for selected photos
- Custom album organization on Immich server

## 🧪 Testing & Verification

### Connection Testing

Use the built-in test functionality:

1. **Test Connection**: Verifies API key and server access
2. **Load Albums**: Lists existing albums on server
3. **Test Upload**: Upload a sample photo (manual testing)

### Manual Verification

```bash
# Test Immich connection from command line
curl -H "x-api-key: YOUR_API_KEY" https://your-immich-server.com/api/server-info/ping

# Check PhotoBooth logs for sync activity
tail -f /opt/photobooth/photobooth.log | grep -i immich
```

### Troubleshooting Commands

```bash
# Test DNS resolution
nslookup your-immich-server.com

# Test network connectivity
ping your-immich-server.com
telnet your-immich-server.com 2283

# Check PhotoBooth service logs
sudo journalctl -u photobooth -f
```

## 🔧 Troubleshooting

### Common Issues

#### "Connection Failed" Error

**Symptoms**: Test connection fails, photos not syncing

**Causes & Solutions**:
1. **Network connectivity**:
   - Check if server is reachable: `ping your-immich-server.com`
   - Verify firewall rules allow outbound connections
   - Test with curl: `curl -I https://your-immich-server.com`

2. **Wrong server URL**:
   - Include protocol: `https://` or `http://`
   - Include port if non-standard: `:2283`
   - Check for typos in domain/IP

3. **Invalid API key**:
   - Regenerate API key in Immich settings
   - Ensure key is copied completely (no spaces)
   - Check if user account has proper permissions

#### "Album Creation Failed" Error

**Symptoms**: Photos upload but aren't added to album

**Causes & Solutions**:
1. **Duplicate album names**:
   - Album with same name exists but is owned by different user
   - Use unique album name or check existing albums

2. **Permissions issue**:
   - API key user doesn't have album creation rights
   - Use admin API key or grant appropriate permissions

3. **Special characters**:
   - Album name contains unsupported characters
   - Use alphanumeric names with spaces/hyphens only

#### "Photos Not Syncing" Issue

**Symptoms**: Settings look correct but sync doesn't happen

**Causes & Solutions**:
1. **Sync disabled**:
   - Check "Enable Immich Sync" is checked
   - Verify "Sync on Capture" if expecting real-time sync

2. **File permissions**:
   - Ensure PhotoBooth can read photo files
   - Check `/opt/photobooth/data/photos/all/` permissions

3. **Network issues**:
   - Intermittent connectivity problems
   - Check logs for timeout errors
   - Consider increasing timeout values

#### "Duplicate Detection" Confusion

**Symptoms**: Photos appear multiple times or sync reports duplicates

**Understanding**:
- Immich uses SHA1 checksums to detect duplicates
- Same photo uploaded twice = 1 duplicate, 1 skipped
- Different photos with same name = 2 separate uploads
- This is normal and expected behavior

### Debug Mode

Enable detailed logging for troubleshooting:

```python
# In PhotoBooth console
import logging
logging.getLogger('photobooth.immich').setLevel(logging.DEBUG)
```

### Log Analysis

Important log messages to look for:

```bash
# Successful connection
grep "Connection to Immich server successful" /opt/photobooth/photobooth.log

# Album creation
grep "Created Immich album" /opt/photobooth/photobooth.log

# Photo uploads
grep "Uploaded photo.*to Immich" /opt/photobooth/photobooth.log

# Errors
grep "ERROR.*immich" /opt/photobooth/photobooth.log
```

## 🔒 Security Considerations

### API Key Security

- **Store securely**: API keys are stored in database, not plain text files
- **Rotate regularly**: Generate new keys periodically
- **Limit permissions**: Create dedicated user with minimal required permissions
- **Monitor usage**: Check Immich logs for unexpected API activity

### Network Security

- **Use HTTPS**: Always use encrypted connections for remote servers
- **VPN access**: Consider VPN for remote Immich servers
- **Firewall rules**: Limit outbound connections to only necessary ports
- **Private networks**: Keep Immich on private networks when possible

### Privacy Considerations

- **Self-hosted**: Photos stay on your infrastructure
- **No third parties**: Direct connection, no external services
- **Access control**: Manage who can access your Immich server
- **Backup policies**: Immich becomes another backup location, not replacement

## 🚀 Performance Optimization

### Upload Performance

**Network optimization**:
- Use wired ethernet for PhotoBooth Pi when possible
- Consider 5GHz WiFi if Pi supports it (Pi 4+ only)
- Position Pi close to router for strong signal

**Server optimization**:
- Use SSD storage for Immich database
- Adequate RAM for Immich containers
- Consider geographic proximity for cloud servers

### Resource Management

**PhotoBooth Pi resources**:
- Sync operations use minimal CPU (background threads)
- Network usage peaks during uploads (~2MB per photo)
- No significant memory impact

**Monitoring**:
```bash
# Check system resources during sync
htop
iotop
nethogs
```

## 📊 Sync Statistics & Monitoring

### Built-in Monitoring

The PhotoBooth interface provides:
- **Connection status**: Green/red indicator
- **Last sync time**: When last photo was uploaded
- **Sync success/failure counts**: Basic statistics
- **Album information**: Current album details

### Advanced Monitoring

**Immich server metrics**:
- Check Immich admin dashboard for storage usage
- Monitor API usage in Immich logs
- Track album growth and photo counts

**PhotoBooth logs analysis**:
```bash
# Count successful uploads today
grep "$(date '+%Y-%m-%d')" /opt/photobooth/photobooth.log | grep "Uploaded photo.*to Immich" | wc -l

# Check for recent errors
grep "$(date '+%Y-%m-%d')" /opt/photobooth/photobooth.log | grep -i "error.*immich"
```

## 🛡️ Backup & Recovery

### PhotoBooth Backup

**Critical settings to backup**:
- Database: `/opt/photobooth/data/photobooth.db`
- Configuration: `/opt/photobooth/.env`
- Photos: `/opt/photobooth/data/photos/`

**Backup command**:
```bash
tar -czf photobooth-backup-$(date +%Y%m%d).tar.gz \
  /opt/photobooth/data/ \
  /opt/photobooth/.env
```

### Immich Server Backup

Follow [Immich backup documentation](https://immich.app/docs/administration/backup-and-restore):

```bash
# Backup Immich database
docker-compose exec database pg_dump -U postgres immich > immich-db-backup.sql

# Backup uploaded photos
cp -r /path/to/immich/upload /backup/location/
```

### Recovery Scenarios

**Scenario 1: PhotoBooth failure**
- Restore from backup
- Reconfigure Immich settings
- Photos already safely stored in Immich

**Scenario 2: Immich server failure**
- Photos remain on PhotoBooth Pi
- Re-sync after Immich restoration
- Duplicate detection prevents re-upload issues

## 🎯 Best Practices

### Pre-Event Setup

1. **Test thoroughly** at least 1 week before event
2. **Verify album creation** with test photos
3. **Check network stability** with sustained uploads
4. **Monitor resource usage** during test runs
5. **Have fallback plan** if sync fails during event

### Event Day Operations

1. **Enable real-time sync** for automatic backup
2. **Monitor connection status** periodically
3. **Check storage space** on both PhotoBooth and Immich
4. **Have backup storage** ready (USB drive, etc.)
5. **Don't rely solely on sync** - local photos are primary

### Post-Event Management

1. **Verify all photos synced** using bulk sync feature
2. **Organize albums** on Immich server as needed
3. **Share access** with couple/family as appropriate
4. **Create backups** of both systems
5. **Document sync statistics** for future events

## 🔗 Integration Examples

### Wedding Photographer Workflow

```python
# Custom script for photographer integration
from photobooth.immich import get_immich_sync

sync = get_immich_sync()
result = sync.sync_all_photos('/path/to/photographer/selects')
print(f"Synced {result['uploaded']} professional photos")
```

### Multi-Event Management

```bash
# Change album name for different events
# Via web interface or database update
sqlite3 /opt/photobooth/data/photobooth.db \
  "UPDATE settings SET value='Birthday2024' WHERE key='immich_album_name'"
```

### API Integration

**Custom sync triggers**:
```python
# Sync specific photo programmatically
from photobooth.immich import sync_photo_to_immich

result = sync_photo_to_immich('/path/to/special/photo.jpg')
if result['success']:
    print("Photo synced successfully!")
```

## 📞 Support & Community

### Getting Help

1. **Check logs first**: Most issues show up in PhotoBooth logs
2. **Test connection**: Use built-in test functionality
3. **Check Immich docs**: [Official Immich documentation](https://immich.app/docs)
4. **Community support**: Immich Discord server

### Contributing

Found a bug or want to improve the sync feature?

1. **Document the issue** with logs and reproduction steps
2. **Test fixes** thoroughly on Raspberry Pi
3. **Maintain compatibility** with existing Immich versions
4. **Follow PhotoBooth coding standards**

### Feature Requests

Common requested features:
- **Multiple album support**: Different albums for different events
- **Selective sync**: Choose specific photos to sync
- **Sync scheduling**: Time-based sync operations
- **Progress indicators**: Real-time upload progress
- **Metadata preservation**: EXIF data and timestamps

---

## 📚 Additional Resources

- **[Immich Official Docs](https://immich.app/docs)**
- **[Immich Installation Guide](https://immich.app/docs/install/requirements)**
- **[PhotoBooth Main Documentation](../README.md)**
- **[SMS Photo Sharing Guide](sms_photo_sharing.md)**

---

*Last updated: September 2025*

*This documentation covers Immich sync integration for PhotoBooth v2.0+. For older versions, some features may not be available.*