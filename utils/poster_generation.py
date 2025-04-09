import os
import requests
from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import math
from io import BytesIO
import concurrent.futures
from pyaml_env import parse_config

# Canvas dimensions and styling
CANVAS_WIDTH = 2000
CANVAS_HEIGHT = 3000
LINE_SPACING = 25
SHADOW_SIZE = 8
BACKGROUND_COLOR = (0, 0, 0)
OVERLAY_PADDING = 50

def get_font(url, font_dir="./fonts"):
    '''Download ttf from google font css'''

    font_name = url.split("family=")[1].split("&")[0]
    font_name = font_name.replace(":", "_")
    font_name = font_name.replace("@", "_")
    font_name = font_name + ".ttf"
    font_path = os.path.join(font_dir, font_name)

    if os.path.exists(font_path):
        return font_path

    if not os.path.exists(font_dir):
        os.mkdir(font_dir)

    # Download css
    r = requests.get(url)
    r.raise_for_status()
    font_url = r.text.split("url(")[1].split(")")[0]

    # Download font
    r = requests.get(font_url)
    with open(font_path, 'wb') as f:
        f.write(r.content)
    r.raise_for_status()
    return font_path

# --- Data Fetching Functions ---

def fetch_collection_posters(jellyfin_url, api_key, user_id, collection_id):
    """
    Fetches the poster URLs for all items in the specified collection.
    """
    logger.info(f"Fetching posters for collection ID {collection_id}...")
    headers = {'X-Emby-Token': api_key}
    url = f"{jellyfin_url}/Users/{user_id}/Items"
    params = {'parentId': collection_id}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    items = response.json().get('Items', [])
    poster_urls = []
    for item in items:
        if 'ImageTags' in item and 'Primary' in item['ImageTags']:
            poster_url = f"{jellyfin_url}/Items/{item['Id']}/Images/Primary?tag={item['ImageTags']['Primary']}"
            poster_urls.append(poster_url)
    logger.info(f"Found {len(poster_urls)} poster(s) for collection ID {collection_id}.")
    return poster_urls

def safe_download(url, headers):
    """
    Download an image safely; return None if an error occurs.
    """
    try:
        return download_image(url, headers)
    except Exception as e:
        logger.error(f"Error downloading image {url}: {e}")
        return None

def download_image(url, headers):
    """
    Downloads an image from a URL and returns a Pillow Image object.
    """
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content)).convert("RGB")
    return image


# --- Text and Font Functions ---

def wrap_text(text, font, draw, max_width):
    """
    Wrap text into multiple lines so that each line's width doesn't exceed max_width.
    """
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def get_adjusted_font_and_wrapped_text(text, draw, max_width, max_height, font_file, max_font_size=200, min_font_size=20):
    """
    Determines a font size that allows the text to be wrapped within max_width and max_height.
    Returns the chosen font, the wrapped lines, and the total text block height.
    """
    for font_size in range(max_font_size, min_font_size - 1, -1):
        font = ImageFont.truetype(font_file, font_size)
        lines = wrap_text(text, font, draw, max_width)
        ascent, descent = font.getmetrics()
        line_height = ascent + descent
        total_height = line_height * len(lines) + LINE_SPACING * (len(lines) - 1)
        # Check if the text block fits within the limits
        max_line_width = max(draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0] for line in lines)
        if max_line_width <= max_width and total_height <= max_height:
            return font, lines, total_height
    # Fall back to minimum font size
    font = ImageFont.truetype(font_file, min_font_size)
    lines = wrap_text(text, font, draw, max_width)
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    total_height = line_height * len(lines) + LINE_SPACING * (len(lines) - 1)
    logger.info("Using minimum font size.")
    return font, lines, total_height


def draw_text_with_shadow(draw, text, position, font, shadow_size, text_color="white", shadow_color="black"):
    """
    Draw text with a shadow effect at the specified position.
    """
    x, y = position
    # Draw shadow offsets
    for dx in range(-shadow_size, shadow_size + 1):
        for dy in range(-shadow_size, shadow_size + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=shadow_color)
    # Draw main text
    draw.text((x, y), text, font=font, fill=text_color)


def draw_text_block(draw, lines, font, total_text_height, overlay_y, overlay_height):
    """
    Draw the text block centered within the overlay area.
    """
    ascent, descent = font.getmetrics()
    line_height = ascent + descent
    # Adjust starting y using the font metrics
    current_y = overlay_y + (overlay_height - total_text_height) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        text_x = (CANVAS_WIDTH - line_width) // 2
        draw_text_with_shadow(draw, line, (text_x, current_y), font, SHADOW_SIZE)
        current_y += line_height + LINE_SPACING


# --- Mosaic Creation Functions ---

def create_mosaic_background(poster_images):
    """
    Create the mosaic background from poster images.
    Returns a blurred canvas with the images pasted in a grid that fills the entire canvas.
    Some parts of the posters may be cut off to ensure a complete fill.
    """
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND_COLOR)
    num_posters = len(poster_images)
    if num_posters == 0:
        raise ValueError("No poster images available!")

    # Determine the grid dimensions (number of columns and rows)
    grid_cols = math.ceil(math.sqrt(num_posters))
    grid_rows = math.ceil(num_posters / grid_cols)

    # Calculate cell size so that the entire canvas area is used.
    cell_width = CANVAS_WIDTH // grid_cols
    cell_height = CANVAS_HEIGHT // grid_rows

    # Place each poster image into its respective cell.
    # ImageOps.fit will scale and crop the image as necessary to cover the entire cell.
    for idx, img in enumerate(poster_images):
        fitted_img = ImageOps.fit(img, (cell_width, cell_height), method=Image.Resampling.LANCZOS)
        col = idx % grid_cols
        row = idx // grid_cols
        x = col * cell_width   # No horizontal offset
        y = row * cell_height  # No vertical offset
        canvas.paste(fitted_img, (x, y))

    return canvas.filter(ImageFilter.GaussianBlur(radius=10))


def apply_text_overlay(image, collection_name, font_file):
    """
    Applies a semi-transparent overlay and draws the collection name centered within it.
    """
    draw = ImageDraw.Draw(image)
    max_text_width = int(CANVAS_WIDTH * 0.8)
    max_text_height = int(CANVAS_HEIGHT * 0.3)

    font, lines, total_text_height = get_adjusted_font_and_wrapped_text(
        collection_name.upper(), draw, max_text_width, max_text_height, font_file
    )

    overlay_width = max_text_width + OVERLAY_PADDING * 2
    overlay_height = total_text_height + OVERLAY_PADDING * 2
    overlay_x = (CANVAS_WIDTH - overlay_width) // 2
    overlay_y = (CANVAS_HEIGHT - overlay_height) // 2

    # Create a transparent overlay image
    overlay = Image.new('RGBA', (overlay_width, overlay_height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Draw a rounded rectangle on the overlay
    radius = 30  # Adjust the radius for more or less rounding
    overlay_draw.rounded_rectangle([(0, 0), (overlay_width, overlay_height)], radius=radius, fill=(0, 0, 0, 200))

    # Paste the rounded overlay onto the canvas using its alpha channel as mask
    image.paste(overlay, (overlay_x, overlay_y), overlay)

    # Draw text on top of the overlay
    draw = ImageDraw.Draw(image)
    draw_text_block(draw, lines, font, total_text_height, overlay_y, overlay_height)


def create_mosaic(poster_images, collection_name, output_path, font_path):
    """
    Creates the complete mosaic cover by combining the background and text overlay.
    """
    logger.debug("Starting mosaic creation...")
    blurred = create_mosaic_background(poster_images)
    apply_text_overlay(blurred, collection_name, font_path)
    blurred.save(output_path)
    logger.debug(f"Cover art saved to {output_path}")
