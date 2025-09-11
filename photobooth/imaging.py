"""
Image processing utilities for frame overlays and photo manipulation
"""
import os
import logging
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps
from flask import current_app

logger = logging.getLogger(__name__)

def apply_frame_overlay(photo_path: str, frame_path: str) -> str:
    """Apply frame overlay to photo"""
    try:
        # Open photo and frame
        with Image.open(photo_path) as photo, Image.open(frame_path) as frame:
            # Get target dimensions
            target_width = current_app.config.get('PHOTO_WIDTH', 1800)
            target_height = current_app.config.get('PHOTO_HEIGHT', 1200)
            
            # Resize photo to target size
            photo_resized = resize_and_crop(photo, (target_width, target_height))
            
            # Resize frame to match photo
            frame_resized = frame.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Ensure photo is in RGB mode
            if photo_resized.mode != 'RGB':
                photo_resized = photo_resized.convert('RGB')
            
            # Apply frame overlay
            if frame_resized.mode == 'RGBA':
                # Frame has transparency
                result = Image.new('RGB', (target_width, target_height), (255, 255, 255))
                result.paste(photo_resized, (0, 0))
                result.paste(frame_resized, (0, 0), frame_resized)
            else:
                # Frame is opaque, blend with photo
                frame_rgb = frame_resized.convert('RGB')
                result = Image.blend(photo_resized, frame_rgb, 0.1)  # Light overlay
            
            # Save the result
            result.save(photo_path, 'JPEG', quality=95, optimize=True)
            
        logger.info(f"Applied frame overlay to: {photo_path}")
        return photo_path
        
    except Exception as e:
        logger.error(f"Failed to apply frame overlay: {e}")
        raise

def resize_and_crop(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    """Resize and crop image to exact target size while maintaining aspect ratio"""
    target_width, target_height = target_size
    image_width, image_height = image.size
    
    # Calculate aspect ratios
    target_aspect = target_width / target_height
    image_aspect = image_width / image_height
    
    if image_aspect > target_aspect:
        # Image is wider than target, crop width
        new_height = target_height
        new_width = int(new_height * image_aspect)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to center
        left = (new_width - target_width) // 2
        top = 0
        right = left + target_width
        bottom = target_height
        
        result = resized.crop((left, top, right, bottom))
    else:
        # Image is taller than target, crop height
        new_width = target_width
        new_height = int(new_width / image_aspect)
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to center
        left = 0
        top = (new_height - target_height) // 2
        right = target_width
        bottom = top + target_height
        
        result = resized.crop((left, top, right, bottom))
    
    return result

def create_thumbnail(photo_path: str, size: int = None) -> str:
    """Create thumbnail from photo"""
    try:
        if size is None:
            size = current_app.config.get('THUMBNAIL_SIZE', 300)
        
        # Get thumbnail path
        from .storage import get_thumbnail_path
        filename = os.path.basename(photo_path)
        thumbnail_path = get_thumbnail_path(filename)
        
        # Create thumbnail
        with Image.open(photo_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Create square thumbnail with center crop
            thumbnail = ImageOps.fit(img, (size, size), Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            # Save thumbnail
            thumbnail.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
        
        logger.info(f"Created thumbnail: {thumbnail_path}")
        return thumbnail_path
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {photo_path}: {e}")
        raise

def validate_frame(frame_file) -> Dict[str, Any]:
    """Validate uploaded frame file"""
    try:
        # Check file extension
        filename = frame_file.filename.lower()
        if not filename.endswith('.png'):
            return {'valid': False, 'error': 'Frame must be a PNG file'}
        
        # Save current file position
        original_position = frame_file.tell()
        
        # Check image
        try:
            with Image.open(frame_file) as img:
                width, height = img.size
                
                # Check minimum size
                min_size = 800
                if width < min_size or height < min_size:
                    return {
                        'valid': False, 
                        'error': f'Frame must be at least {min_size}x{min_size} pixels'
                    }
                
                # Check maximum size (to prevent memory issues)
                max_size = 4000
                if width > max_size or height > max_size:
                    return {
                        'valid': False,
                        'error': f'Frame must be no larger than {max_size}x{max_size} pixels'
                    }
                
                # Check if it has transparency (recommended)
                has_transparency = img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                
                return {
                    'valid': True,
                    'width': width,
                    'height': height,
                    'has_transparency': has_transparency,
                    'recommended_size': f"{current_app.config.get('PHOTO_WIDTH', 1800)}x{current_app.config.get('PHOTO_HEIGHT', 1200)}"
                }
                
        except Exception as e:
            return {'valid': False, 'error': 'Invalid image file'}
        finally:
            # Reset file pointer to original position
            frame_file.seek(original_position)
        
    except Exception as e:
        logger.error(f"Frame validation error: {e}")
        return {'valid': False, 'error': 'Validation failed'}

def create_test_print_image() -> str:
    """Create a branded test print image"""
    try:
        # Get print dimensions
        width = current_app.config.get('PHOTO_WIDTH', 1800)
        height = current_app.config.get('PHOTO_HEIGHT', 1200)
        
        # Create image
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        font_size = 72
        try:
            # Try to use a system font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Colors
        primary_color = (139, 69, 19)  # Saddle brown - wedding appropriate
        secondary_color = (255, 215, 0)  # Gold
        text_color = (0, 0, 0)  # Black
        
        # Draw border
        border_width = 20
        draw.rectangle([0, 0, width-1, height-1], outline=primary_color, width=border_width)
        draw.rectangle([border_width, border_width, width-border_width-1, height-border_width-1], 
                      outline=secondary_color, width=10)
        
        # Draw title
        title = "PhotoBooth Test Print"
        if font:
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(title) * 12  # Rough estimate
            text_height = 24
        
        title_x = (width - text_width) // 2
        title_y = height // 3
        
        if font:
            draw.text((title_x, title_y), title, fill=text_color, font=font)
        else:
            draw.text((title_x, title_y), title, fill=text_color)
        
        # Draw timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if font:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            bbox = draw.textbbox((0, 0), timestamp, font=small_font)
            text_width = bbox[2] - bbox[0]
        else:
            small_font = font
            text_width = len(timestamp) * 8
        
        timestamp_x = (width - text_width) // 2
        timestamp_y = title_y + 100
        
        draw.text((timestamp_x, timestamp_y), timestamp, fill=text_color, font=small_font)
        
        # Draw printer info
        info_lines = [
            "Printer Test Successful",
            f"Image Size: {width}x{height}",
            "PhotoBooth System Ready"
        ]
        
        info_y = timestamp_y + 80
        for line in info_lines:
            if font:
                bbox = draw.textbbox((0, 0), line, font=small_font)
                text_width = bbox[2] - bbox[0]
            else:
                text_width = len(line) * 8
            
            line_x = (width - text_width) // 2
            draw.text((line_x, info_y), line, fill=text_color, font=small_font)
            info_y += 50
        
        # Save test image
        test_image_path = os.path.join(current_app.config['PHOTOS_ALL_DIR'], 'test_print.jpg')
        img.save(test_image_path, 'JPEG', quality=95)
        
        logger.info(f"Created test print image: {test_image_path}")
        return test_image_path
        
    except Exception as e:
        logger.error(f"Failed to create test print image: {e}")
        raise

def optimize_image_for_print(image_path: str, quality: int = None) -> str:
    """Optimize image for printing"""
    try:
        if quality is None:
            quality = int(current_app.config.get('PHOTO_QUALITY', 95))
        
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Enhance for print
            from PIL import ImageEnhance
            
            # Slight sharpening for print
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)
            
            # Slight contrast boost
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)
            
            # Save optimized version
            optimized_path = image_path.replace('.jpg', '_print.jpg')
            img.save(optimized_path, 'JPEG', quality=quality, optimize=True, dpi=(300, 300))
        
        logger.info(f"Optimized image for print: {optimized_path}")
        return optimized_path
        
    except Exception as e:
        logger.error(f"Failed to optimize image for print: {e}")
        return image_path  # Return original if optimization fails

def add_watermark(image_path: str, text: str = "PhotoBooth") -> str:
    """Add subtle watermark to image"""
    try:
        with Image.open(image_path) as img:
            # Create watermark
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Try to load font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Calculate position (bottom right)
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = len(text) * 12
                text_height = 20
            
            x = img.width - text_width - 20
            y = img.height - text_height - 20
            
            # Draw watermark (semi-transparent white)
            draw.text((x, y), text, fill=(255, 255, 255, 128), font=font)
            
            # Composite with original image
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            result = Image.alpha_composite(img, watermark)
            
            # Convert back to RGB and save
            if result.mode == 'RGBA':
                result = result.convert('RGB')
            
            result.save(image_path, 'JPEG', quality=95)
        
        logger.info(f"Added watermark to: {image_path}")
        return image_path
        
    except Exception as e:
        logger.warning(f"Failed to add watermark: {e}")
        return image_path  # Return original if watermarking fails