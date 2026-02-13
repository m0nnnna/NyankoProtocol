#!/usr/bin/env python3
"""
Simple script to create a cute neko icon for Nyanko Protocol
Creates a .ico file with a simple cat face
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

def create_icon():
    # Create multiple sizes for .ico file
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []
    
    for size in sizes:
        # Create image with transparent background
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Scale factor for drawing
        scale = size[0] / 256.0
        
        # Draw cat face - cute neko style
        # Face circle (pink/magenta)
        face_size = int(180 * scale)
        face_x = (size[0] - face_size) // 2
        face_y = (size[1] - face_size) // 2 + int(20 * scale)
        draw.ellipse([face_x, face_y, face_x + face_size, face_y + face_size], 
                    fill=(255, 100, 200, 255), outline=(200, 50, 150, 255), width=int(3 * scale))
        
        # Left ear
        ear_size = int(40 * scale)
        ear1_x = face_x + int(30 * scale)
        ear1_y = face_y + int(10 * scale)
        draw.polygon([
            (ear1_x, ear1_y),
            (ear1_x + ear_size, ear1_y - int(25 * scale)),
            (ear1_x + int(ear_size * 1.5), ear1_y + int(15 * scale))
        ], fill=(255, 100, 200, 255), outline=(200, 50, 150, 255), width=int(2 * scale))
        
        # Right ear
        ear2_x = face_x + face_size - int(30 * scale) - ear_size
        ear2_y = face_y + int(10 * scale)
        draw.polygon([
            (ear2_x, ear2_y),
            (ear2_x + ear_size, ear2_y - int(25 * scale)),
            (ear2_x + int(ear_size * 1.5), ear2_y + int(15 * scale))
        ], fill=(255, 100, 200, 255), outline=(200, 50, 150, 255), width=int(2 * scale))
        
        # Left eye
        eye_size = int(25 * scale)
        eye1_x = face_x + int(60 * scale)
        eye1_y = face_y + int(70 * scale)
        draw.ellipse([eye1_x, eye1_y, eye1_x + eye_size, eye1_y + eye_size], 
                    fill=(255, 255, 255, 255))
        draw.ellipse([eye1_x + int(8 * scale), eye1_y + int(8 * scale), 
                     eye1_x + eye_size - int(8 * scale), eye1_y + eye_size - int(8 * scale)], 
                    fill=(0, 0, 0, 255))
        
        # Right eye
        eye2_x = face_x + face_size - int(60 * scale) - eye_size
        eye2_y = face_y + int(70 * scale)
        draw.ellipse([eye2_x, eye2_y, eye2_x + eye_size, eye2_y + eye_size], 
                    fill=(255, 255, 255, 255))
        draw.ellipse([eye2_x + int(8 * scale), eye2_y + int(8 * scale), 
                     eye2_x + eye_size - int(8 * scale), eye2_y + eye_size - int(8 * scale)], 
                    fill=(0, 0, 0, 255))
        
        # Nose (triangle)
        nose_size = int(15 * scale)
        nose_x = size[0] // 2
        nose_y = face_y + int(110 * scale)
        draw.polygon([
            (nose_x, nose_y),
            (nose_x - nose_size // 2, nose_y + int(12 * scale)),
            (nose_x + nose_size // 2, nose_y + int(12 * scale))
        ], fill=(255, 150, 200, 255))
        
        # Mouth
        mouth_y = nose_y + int(20 * scale)
        draw.arc([nose_x - int(20 * scale), mouth_y - int(10 * scale),
                 nose_x + int(20 * scale), mouth_y + int(10 * scale)],
                start=0, end=180, fill=(200, 50, 150, 255), width=int(3 * scale))
        
        # Add a small star decoration (for the "Star Resonance" theme)
        star_size = int(20 * scale)
        star_x = face_x + int(20 * scale)
        star_y = face_y + int(20 * scale)
        # Simple 5-pointed star
        points = []
        for i in range(10):
            angle = (i * 3.14159) / 5 - 3.14159 / 2
            r = star_size // 2 if i % 2 == 0 else star_size // 4
            points.append((
                star_x + int(r * (1 + 0.5 * (i % 2))) * (1 if i < 5 else -1),
                star_y + int(r * 0.8 * (1 if i % 2 == 0 else 0.5))
            ))
        if len(points) >= 3:
            draw.polygon(points[:5], fill=(255, 255, 100, 255), outline=(255, 200, 0, 255), width=int(2 * scale))
        
        images.append(img)
    
    # Save as .ico file
    images[0].save('nyanko_icon.ico', format='ICO', sizes=[(img.size[0], img.size[1]) for img in images])
    print("Created nyanko_icon.ico successfully!")

if __name__ == "__main__":
    create_icon()
