import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont


def watermark_images(source_folder, dest_folder, watermark_text, font_path=None, font_size=60):
    """Apply a semi-transparent watermark to all images in source_folder and write to dest_folder.

    This function uses relative paths by default. Provide explicit paths via CLI if needed.
    """
    # Check if source folder exists
    if not os.path.exists(source_folder):
        print(f"Source folder does not exist: {source_folder}")
        return

    # Create destination folder if it doesn't exist
    os.makedirs(dest_folder, exist_ok=True)

    # Load font with fallbacks
    font = None
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"Warning: failed to load font '{font_path}': {e}")
            font = None

    if font is None:
        try:
            # Try a common cross-platform font name
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.load_default()
                print("Using PIL default font as fallback.")
            except Exception as e:
                print(f"Error loading fallback font: {e}")
                return

    # Loop through all files in the source folder
    for filename in os.listdir(source_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):  # Check for image files
            image_path = os.path.join(source_folder, filename)

            try:
                # Open the image
                with Image.open(image_path) as img:
                    # Convert the image to RGBA if it's not already
                    img = img.convert('RGBA')

                    # Create a transparent overlay for the watermark
                    watermark_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(watermark_overlay)

                    # Use textbbox to get the bounding box of the text
                    text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                    # Set position for the watermark (bottom right corner)
                    padding = max(10, int(min(img.size) * 0.02))
                    x = img.size[0] - text_width - padding
                    y = img.size[1] - text_height - padding

                    # Draw a subtle outline for the watermark text for visibility
                    outline_range = 1
                    for ox in range(-outline_range, outline_range + 1):
                        for oy in range(-outline_range, outline_range + 1):
                            if ox != 0 or oy != 0:
                                draw.text((x + ox, y + oy), watermark_text, fill=(0, 0, 0, 120), font=font)

                    # Draw the main watermark text
                    draw.text((x, y), watermark_text, fill=(255, 255, 255, 140), font=font)

                    # Combine the original image with the watermark overlay
                    watermarked_img = Image.alpha_composite(img, watermark_overlay)

                    # Save the watermarked image to the destination folder with the original filename
                    dest_path = os.path.join(dest_folder, filename)
                    watermarked_img.convert('RGB').save(dest_path, 'JPEG')  # Save as JPEG

                    print(f'Watermarked image saved to: {dest_path}')

            except Exception as e:
                print(f"Error processing file {filename}: {e}")


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Batch watermark images')
    parser.add_argument('--source', '-s', default='raw-images', help='Source folder with images (default: raw-images)')
    parser.add_argument('--dest', '-d', default='blog-images', help='Destination folder for watermarked images (default: blog-images)')
    parser.add_argument('--text', '-t', default='monoismore.com', help='Watermark text')
    parser.add_argument('--font', '-f', default=None, help='Path to TTF font to use')
    parser.add_argument('--size', type=int, default=60, help='Font size')
    return parser.parse_args(argv)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    watermark_images(args.source, args.dest, args.text, font_path=args.font, font_size=args.size)