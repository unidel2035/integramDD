#!/usr/bin/env python3
"""
Generate architecture diagram for IdeaV service
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create output directory if it doesn't exist
os.makedirs('/tmp/gh-issue-solver-1760191549190/experiments', exist_ok=True)

# Image dimensions
WIDTH = 1600
HEIGHT = 1200
BG_COLOR = (255, 255, 255)
PRIMARY_COLOR = (41, 128, 185)  # Blue
SECONDARY_COLOR = (52, 152, 219)  # Light Blue
ACCENT_COLOR = (231, 76, 60)  # Red
TEXT_COLOR = (44, 62, 80)  # Dark Blue-Gray
BORDER_COLOR = (149, 165, 166)  # Gray
DATABASE_COLOR = (46, 204, 113)  # Green
CLIENT_COLOR = (155, 89, 182)  # Purple

# Create image
img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

# Try to load fonts
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    normal_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
except:
    title_font = ImageFont.load_default()
    header_font = ImageFont.load_default()
    normal_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

def draw_box(x, y, width, height, color, text, font, text_color=TEXT_COLOR):
    """Draw a colored box with text"""
    # Draw shadow
    draw.rectangle([x+5, y+5, x+width+5, y+height+5], fill=(200, 200, 200))
    # Draw main box
    draw.rectangle([x, y, x+width, y+height], fill=color, outline=BORDER_COLOR, width=3)

    # Draw text (multiline support)
    lines = text.split('\n')
    text_y = y + height//2 - (len(lines) * 12)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((x + width//2 - text_width//2, text_y), line, fill=text_color, font=font)
        text_y += 24

def draw_arrow(x1, y1, x2, y2, color=TEXT_COLOR, label=""):
    """Draw an arrow between two points"""
    draw.line([x1, y1, x2, y2], fill=color, width=3)

    # Draw arrowhead
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_size = 15

    arrow_x1 = x2 - arrow_size * math.cos(angle - math.pi/6)
    arrow_y1 = y2 - arrow_size * math.sin(angle - math.pi/6)
    arrow_x2 = x2 - arrow_size * math.cos(angle + math.pi/6)
    arrow_y2 = y2 - arrow_size * math.sin(angle + math.pi/6)

    draw.polygon([x2, y2, arrow_x1, arrow_y1, arrow_x2, arrow_y2], fill=color)

    # Draw label
    if label:
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2
        bbox = draw.textbbox((0, 0), label, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.rectangle([mid_x - text_width//2 - 5, mid_y - 12,
                       mid_x + text_width//2 + 5, mid_y + 12], fill=BG_COLOR)
        draw.text((mid_x - text_width//2, mid_y - 10), label, fill=color, font=small_font)

# Title
title_bbox = draw.textbbox((0, 0), "IdeaV Architecture", font=title_font)
title_width = title_bbox[2] - title_bbox[0]
draw.text((WIDTH//2 - title_width//2, 30), "IdeaV Architecture", fill=PRIMARY_COLOR, font=title_font)

subtitle = "Low-Code Data Management System with Quintet Model"
subtitle_bbox = draw.textbbox((0, 0), subtitle, font=normal_font)
subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
draw.text((WIDTH//2 - subtitle_width//2, 75), subtitle, fill=TEXT_COLOR, font=normal_font)

# Layer 1: Client Layer (Top)
client_y = 130
draw_box(150, client_y, 300, 100, CLIENT_COLOR, "Web Browser\n(Client)", header_font, (255, 255, 255))
draw_box(550, client_y, 300, 100, CLIENT_COLOR, "API Clients\n(External)", header_font, (255, 255, 255))
draw_box(950, client_y, 300, 100, CLIENT_COLOR, "Mobile Apps\n(Future)", header_font, (255, 255, 255))

# Layer 2: Web Server Layer
web_y = 300
draw_box(400, web_y, 600, 120, ACCENT_COLOR, "Apache Web Server\n.htaccess (URL Routing)\nSecurity & Access Control", normal_font, (255, 255, 255))

# Layer 3: Application Layer
app_y = 480
# Main PHP Core
draw_box(100, app_y, 500, 180, PRIMARY_COLOR,
         "PHP Core Application\nindex.php (Main Entry Point)\n" +
         "login.php (Authentication)\n" +
         "include/connection.php (DB Connection)\n" +
         "include/register.php (User Registration)\n" +
         "include/google.php (OAuth)",
         small_font, (255, 255, 255))

# Frontend
draw_box(650, app_y, 400, 180, SECONDARY_COLOR,
         "Frontend Layer\n" +
         "templates/ (HTML Templates)\n" +
         "css/ (Stylesheets)\n" +
         "js/ (JavaScript)\n" +
         "ace/ (Code Editor)",
         small_font, (255, 255, 255))

# Layer 4: Data Model Layer
model_y = 720
draw_box(250, model_y, 900, 100, (230, 126, 34),
         "Quintet Data Model\n" +
         "(id, t, up, ord, val) - Indexed & Linked Values\n" +
         "Supports 500M+ records with 50+ searchable attributes",
         normal_font, (255, 255, 255))

# Layer 5: Database Layer
db_y = 880
draw_box(450, db_y, 500, 100, DATABASE_COLOR,
         "MySQL Database\nsber table (Quintet storage)\n" +
         "Multi-attribute indexing",
         normal_font, (255, 255, 255))

# Layer 6: Storage
storage_y = 1040
draw_box(250, storage_y, 300, 80, (127, 140, 141),
         "logs/\n(System Logs)",
         normal_font, (255, 255, 255))
draw_box(600, storage_y, 300, 80, (127, 140, 141),
         "download/\n(File Storage)",
         normal_font, (255, 255, 255))
draw_box(950, storage_y, 300, 80, (127, 140, 141),
         "templates/\n(Secured)",
         normal_font, (255, 255, 255))

# Draw arrows showing data flow
# Clients to Web Server
draw_arrow(300, client_y + 100, 550, web_y, PRIMARY_COLOR, "HTTP/HTTPS")
draw_arrow(700, client_y + 100, 720, web_y, PRIMARY_COLOR)

# Web Server to Application
draw_arrow(550, web_y + 120, 350, app_y, PRIMARY_COLOR, "Routed Requests")
draw_arrow(750, web_y + 120, 850, app_y, SECONDARY_COLOR)

# Application to Data Model
draw_arrow(350, app_y + 180, 550, model_y, PRIMARY_COLOR, "CRUD Operations")
draw_arrow(850, app_y + 180, 750, model_y, SECONDARY_COLOR, "Templates")

# Data Model to Database
draw_arrow(700, model_y + 100, 700, db_y, DATABASE_COLOR, "Quintet Storage")

# Application to Storage
draw_arrow(200, app_y + 180, 350, storage_y, TEXT_COLOR, "Logs")
draw_arrow(350, app_y + 180, 700, storage_y, TEXT_COLOR, "Files")

# Add key features box
features_x = 50
features_y = 280
draw.rectangle([features_x, features_y, features_x + 280, features_y + 340],
               fill=(236, 240, 241), outline=BORDER_COLOR, width=2)
draw.text((features_x + 10, features_y + 10), "Key Features:", fill=ACCENT_COLOR, font=header_font)

features = [
    "• Low-Code Backend",
    "• 500M+ Records Support",
    "• 50+ Searchable Attributes",
    "• Flexible Data Structures",
    "• Batch Upload Support",
    "• Record-by-Record Insert",
    "• REST API",
    "• OAuth Integration",
    "• Multi-User Support",
    "• Role-Based Access",
    "• Friendly URLs",
    "• XSRF Protection"
]

y_offset = features_y + 45
for feature in features:
    draw.text((features_x + 15, y_offset), feature, fill=TEXT_COLOR, font=small_font)
    y_offset += 25

# Add technology stack box
tech_x = 1320
tech_y = 280
draw.rectangle([tech_x, tech_y, tech_x + 230, tech_y + 240],
               fill=(236, 240, 241), outline=BORDER_COLOR, width=2)
draw.text((tech_x + 10, tech_y + 10), "Tech Stack:", fill=ACCENT_COLOR, font=header_font)

technologies = [
    "• PHP 7.3+",
    "• MySQL/MariaDB",
    "• Apache HTTP Server",
    "• JavaScript",
    "• HTML5/CSS3",
    "• ACE Editor",
    "• OAuth 2.0",
    "• REST API"
]

y_offset = tech_y + 45
for tech in technologies:
    draw.text((tech_x + 15, y_offset), tech, fill=TEXT_COLOR, font=small_font)
    y_offset += 25

# Save the image
output_path = '/tmp/gh-issue-solver-1760191549190/ideav_architecture.png'
img.save(output_path, 'PNG', quality=95)
print(f"Architecture diagram saved to: {output_path}")
