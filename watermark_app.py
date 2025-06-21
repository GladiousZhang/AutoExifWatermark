#!/usr/bin/env python3
import os
import sys
import time
import logging
from PIL import Image, ImageDraw, ImageFont, ExifTags
import numpy as np
from sklearn.cluster import KMeans

# --- 配置区 (已按您的要求更新) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_FOLDER = os.path.join(BASE_DIR, "source")
DEST_FOLDER = os.path.join(BASE_DIR, "target")
FONT_FILE = os.path.join(BASE_DIR, "fonts/DejaVuSans.ttf")
LOGOS_FOLDER = os.path.join(BASE_DIR, "logos")
POLLING_INTERVAL = 10

# --- 动态缩放基准 ---
BASE_IMAGE_WIDTH = 4000 
BASE_WATERMARK_AREA_HEIGHT = 400
BASE_LOGO_HEIGHT = 80
BASE_TEXT_FONT_SIZE = 60
BASE_COLOR_SWATCH_SIZE = 80
BASE_PADDING = 80
NUM_COLORS = 5
# --- 配置区结束 ---

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - [%(levelname)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- 辅助函数 ---
def clean_exif_string(s):
    if not isinstance(s, str): return ""
    return s.replace('\x00', '').strip()

def get_exif_data(image):
    try:
        exif_data = image._getexif()
        if not exif_data: return {}
        return { ExifTags.TAGS[k]: v for k, v in exif_data.items() if k in ExifTags.TAGS }
    except Exception: return {}

def format_shutter_speed(value):
    if not isinstance(value, (int, float)) or value == 0: return ""
    if value >= 1: return f"{int(round(value))}\""
    return f"1/{int(1/value)}s"

def format_aperture(value):
    if not isinstance(value, (int, float)) or value == 0: return ""
    return f"f/{value:.1f}"

def extract_dominant_colors(image, num_colors=5):
    try:
        img_small = image.copy()
        img_small.thumbnail((100, 100))
        img_np = np.array(img_small.convert('RGB'))
        pixels = img_np.reshape(-1, 3)
        kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init='auto')
        kmeans.fit(pixels)
        return [tuple(map(int, color)) for color in kmeans.cluster_centers_]
    except Exception: return []

def darken_color(rgb, factor=0.7):
    return tuple(int(c * factor) for c in rgb)

def add_watermark_and_cleanup(source_path):
    filename = os.path.basename(source_path)
    dest_path = os.path.join(DEST_FOLDER, filename)
    
    logging.info(f"开始处理: {filename}")
    
    try:
        original_img = Image.open(source_path)
        original_width, original_height = original_img.size

        # --- 动态尺寸计算 ---
        scale_factor = original_width / BASE_IMAGE_WIDTH
        wm_area_h = int(BASE_WATERMARK_AREA_HEIGHT * scale_factor)
        logo_h = int(BASE_LOGO_HEIGHT * scale_factor)
        text_font_size = int(BASE_TEXT_FONT_SIZE * scale_factor)
        swatch_size = int(BASE_COLOR_SWATCH_SIZE * scale_factor)
        padding = int(BASE_PADDING * scale_factor)

        # --- EXIF处理 ---
        exif = get_exif_data(original_img)
        brand_name = clean_exif_string(exif.get('Make', ''))
        camera_model = clean_exif_string(exif.get('Model', ''))
        
        focal_length_val = float(exif.get('FocalLength', 0.0))
        aperture_val = float(exif.get('FNumber', 0.0))
        shutter_val = float(exif.get('ExposureTime', 0.0))
        iso_val = exif.get('ISOSpeedRatings', 0)
        
        focal_length = f"{focal_length_val:.0f}mm" if focal_length_val > 0 else ""
        aperture = format_aperture(aperture_val)
        shutter = format_shutter_speed(shutter_val)
        iso = f"ISO {iso_val}" if iso_val > 0 else ""
        
        exif_parts = [camera_model, focal_length, aperture, shutter, iso]
        exif_text = "  ".join(part for part in exif_parts if part)

        # --- 素材准备 ---
        font = ImageFont.truetype(FONT_FILE, text_font_size)
        colors = extract_dominant_colors(original_img, NUM_COLORS)
        logo_img = None
        if brand_name:
            print("brand_name:",brand_name)
            png_path = os.path.join(LOGOS_FOLDER, f"{brand_name}.png")
            if os.path.exists(png_path):
                try:
                    logo_to_process = Image.open(png_path)
                    if logo_to_process.mode != 'RGBA':
                        logo_to_process = logo_to_process.convert('RGBA')
                    aspect_ratio = logo_to_process.width / logo_to_process.height
                    new_width = int(logo_h * aspect_ratio)
                    logo_img = logo_to_process.resize((new_width, logo_h), Image.Resampling.LANCZOS)
                except Exception as e:
                    logging.error(f"加载或转换PNG Logo失败: {png_path}, 错误: {e}")

        # --- 绘制 ---
        new_height = original_height + wm_area_h
        new_img = Image.new('RGB', (original_width, new_height), 'white')
        draw = ImageDraw.Draw(new_img)
        new_img.paste(original_img, (0, 0))
        y_center = original_height + (wm_area_h - swatch_size - padding) // 2
        
        if logo_img:
            logo_y = y_center - logo_img.height // 2
            new_img.paste(logo_img, (padding, logo_y), logo_img) 
        else:
            draw.text((padding, y_center), brand_name, fill='black', font=font, anchor='lm')

        text_bbox = draw.textbbox((0,0), exif_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = original_width - padding - text_width
        draw.text((text_x, y_center), exif_text, fill='black', font=font, anchor='lm')

        if colors:
            total_swatch_width = (swatch_size * len(colors)) + (padding // 2 * (len(colors) - 1))
            start_x = (original_width - total_swatch_width) // 2
            swatch_y = original_height + wm_area_h - swatch_size - padding // 2
            for i, color in enumerate(colors):
                darker_color = darken_color(color)
                current_x = start_x + i * (swatch_size + padding // 2)
                draw.rectangle([current_x, swatch_y, current_x + swatch_size, swatch_y + swatch_size/2], fill=color)
                draw.rectangle([current_x, swatch_y + swatch_size/2, current_x + swatch_size, swatch_y + swatch_size], fill=darker_color)

        # --- 保存与清理 ---
        new_img.save(dest_path, "JPEG", quality=95, exif=original_img.info.get('exif', b''))
        os.remove(source_path)
        
        logging.info(f"处理完成: {filename} -> {dest_path}")
        return True

    except Exception as e:
        logging.error(f"处理文件 {filename} 时发生严重错误: {e}", exc_info=True)
        error_folder = os.path.join(BASE_DIR, "failed_photos")
        os.makedirs(error_folder, exist_ok=True)
        if os.path.exists(source_path):
             os.rename(source_path, os.path.join(error_folder, filename))
        return False

# --- 主循环 ---
if __name__ == "__main__":
    os.makedirs(SOURCE_FOLDER, exist_ok=True)
    os.makedirs(DEST_FOLDER, exist_ok=True)
    os.makedirs(LOGOS_FOLDER, exist_ok=True)
    
    logging.info(f"启动终极版水印服务（统一路径），每 {POLLING_INTERVAL} 秒扫描一次文件夹: {SOURCE_FOLDER}")
    
    try:
        while True:
            files_to_process = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.jpg', '.jpeg'))]
            if files_to_process:
                logging.info(f"发现 {len(files_to_process)} 个新文件，开始处理...")
                for filename in files_to_process:
                    full_path = os.path.join(SOURCE_FOLDER, filename)
                    if os.path.exists(full_path):
                        add_watermark_and_cleanup(full_path)
            time.sleep(POLLING_INTERVAL)
    except KeyboardInterrupt:
        logging.info("程序已停止。")