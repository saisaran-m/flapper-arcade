import pygame
import random
import math
import sys
import os
import json
import asyncio

# Initialize pygame with stabilized mixer settings (forces 44.1 kHz stereo with a larger 4096 buffer to prevent browser audio crackling)
pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.init()
pygame.mixer.init()

# Virtual Game Coordinates (everything renders onto this virtual surface first)
WIDTH = 500
HEIGHT = 750
FPS = 60
GROUND_HEIGHT = 100
Y_GROUND = HEIGHT - GROUND_HEIGHT

# Day-Night Cycle Constants (Slowing down the cycle by 4x)
SKY_CYCLE_LEN = 14400 # 240 seconds at 60 FPS (4 minutes per full cycle)
SKY_PHASE_LEN = 3600  # 60 seconds per phase (Day, Sunset, Night, Sunrise)

# Actual Window Dimensions (Starts at default, but is RESIZABLE)
window_w = WIDTH
window_h = HEIGHT
screen = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
pygame.display.set_caption("Forest Flapper Arcade")
clock = pygame.time.Clock()

# File paths
LEADERBOARD_FILE = "leaderboard.json"
USERNAME_FILE = "username.txt"

# Game Modes
# "normal", "night" (synthwave), "city", "winter"

# Colors (RGB)
# Twilight sunset sky gradient colors
SKY_TOP = (36, 36, 62)
SKY_BOT = (255, 126, 95)

# Mountains & hills
COLOR_MNT_BACK = (55, 48, 79)
COLOR_MNT_FRONT = (78, 59, 94)

# Pine trees (various shades of teal/green for depth)
TREE_COLORS = [
    (24, 46, 45),   # Back layer tree
    (33, 62, 59),   # Mid layer tree
    (42, 79, 75)    # Front layer tree
]

# Cabin colors
COLOR_CABIN_WALL = (112, 72, 48)
COLOR_CABIN_ROOF = (168, 62, 62)
COLOR_CABIN_DOOR = (64, 40, 24)
COLOR_CABIN_WINDOW = (255, 235, 120)  # Golden glow
COLOR_CABIN_CHIMNEY = (80, 80, 80)

# Pipe colors (nature green with highlights)
COLOR_PIPE_BODY = (46, 125, 50)
COLOR_PIPE_LIP = (56, 142, 60)
COLOR_PIPE_HIGHLIGHT = (129, 199, 132)
COLOR_PIPE_SHADOW = (27, 94, 32)
COLOR_PIPE_OUTLINE = (20, 40, 20)

# Ground colors
COLOR_GRASS_TOP = (76, 175, 80)
COLOR_DIRT = (100, 70, 50)
COLOR_DIRT_DARK = (75, 50, 35)

# Fonts
def get_font(name, size, bold=True):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except:
        return pygame.font.Font(None, size)

font_title = get_font("Trebuchet MS", 46, True)
font_ui = get_font("Trebuchet MS", 24, True)
font_score = get_font("Trebuchet MS", 64, True)
font_small = get_font("Trebuchet MS", 16, False)
font_bold_small = get_font("Trebuchet MS", 18, True)

# Sound Playback Setup
jump_sfx = None
point_sfx = None
collision_sfx = None
shield_break_sfx = None
powerup_pickup_sfx = None
coin_pickup_sfx = None
ambient_playing = False
current_ambient_track = None

try:
    if os.path.exists("assets/sounds/jump.ogg"):
        jump_sfx = pygame.mixer.Sound("assets/sounds/jump.ogg")
        jump_sfx.set_volume(0.3)
    if os.path.exists("assets/sounds/point.ogg"):
        point_sfx = pygame.mixer.Sound("assets/sounds/point.ogg")
        point_sfx.set_volume(0.35)
    if os.path.exists("assets/sounds/collision.ogg"):
        collision_sfx = pygame.mixer.Sound("assets/sounds/collision.ogg")
        collision_sfx.set_volume(0.5)
    if os.path.exists("assets/sounds/shield_break.ogg"):
        shield_break_sfx = pygame.mixer.Sound("assets/sounds/shield_break.ogg")
        shield_break_sfx.set_volume(0.45)
    if os.path.exists("assets/sounds/powerup_pickup.ogg"):
        powerup_pickup_sfx = pygame.mixer.Sound("assets/sounds/powerup_pickup.ogg")
        powerup_pickup_sfx.set_volume(0.35)
    if os.path.exists("assets/sounds/coin_pickup.ogg"):
        coin_pickup_sfx = pygame.mixer.Sound("assets/sounds/coin_pickup.ogg")
        coin_pickup_sfx.set_volume(0.4)
except Exception as e:
    print(f"Error setting up SFX: {e}")

def play_ambient(volume=0.2, track_name="nature_ambient"):
    global ambient_playing, current_ambient_track
    if current_ambient_track == track_name:
        pygame.mixer.music.set_volume(volume)
        return
    try:
        path = f"assets/sounds/{track_name}.ogg"
        if os.path.exists(path):
            if current_ambient_track is not None:
                pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(volume)
            current_ambient_track = track_name
            ambient_playing = True
    except Exception as e:
        print(f"Error playing ambient {track_name}: {e}")


# Data Managers
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                return json.load(f)
            # Ensure it is sorted
        except:
            pass
    # Default scores
    default_board = [
        {"name": "SkyKing", "score": 15},
        {"name": "Aviator", "score": 12},
        {"name": "Birdie", "score": 8},
        {"name": "Fledgling", "score": 5},
        {"name": "Chirpy", "score": 2}
    ]
    save_leaderboard(default_board)
    return default_board

def save_leaderboard(data):
    try:
        # Keep only top 5, sorted descending
        sorted_data = sorted(data, key=lambda x: x["score"], reverse=True)[:5]
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(sorted_data, f, indent=4)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")

def load_username():
    if os.path.exists(USERNAME_FILE):
        try:
            with open(USERNAME_FILE, "r") as f:
                name = f.read().strip()
                if name:
                    return name[:12]
        except:
            pass
    return "Player"

def save_username(name):
    try:
        with open(USERNAME_FILE, "w") as f:
            f.write(name.strip()[:12])
    except:
        pass

EQUIPPED_SKIN_FILE = "equipped_skin.txt"

def load_equipped_skin():
    if os.path.exists(EQUIPPED_SKIN_FILE):
        try:
            with open(EQUIPPED_SKIN_FILE, "r") as f:
                skin = f.read().strip()
                if skin in ["classic", "ninja", "mech", "phoenix"]:
                    return skin
        except:
            pass
    return "classic"

def save_equipped_skin(skin):
    try:
        with open(EQUIPPED_SKIN_FILE, "w") as f:
            f.write(skin.strip())
    except:
        pass

def get_profile_filename(username):
    # Sanitize username to prevent invalid characters in file names
    safe_name = "".join(c for c in username if c.isalnum() or c in ("-", "_")).lower()
    if not safe_name:
        safe_name = "default"
    return f"profile_{safe_name}.json"

def load_profile_data(username):
    filename = get_profile_filename(username)
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                # Ensure all required keys exist
                if "high_score" not in data: data["high_score"] = 0
                if "coins" not in data: data["coins"] = 0
                if "unlocked_skins" not in data: data["unlocked_skins"] = ["classic"]
                return data
        except Exception as e:
            print(f"Error loading profile: {e}")
    # Default data if file doesn't exist or is corrupted
    return {
        "high_score": 0,
        "coins": 0,
        "unlocked_skins": ["classic"]
    }

def save_profile_data(username, data):
    filename = get_profile_filename(username)
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving profile: {e}")




# Optimized Dynamic Sky Gradients (Caching vertical gradient bands)
def make_sky_surface(top_color, bot_color):
    surf = pygame.Surface((WIDTH, HEIGHT))
    # We draw onto a tiny 15px tall strip and scale it up for high performance
    tiny_surf = pygame.Surface((1, 15))
    for y in range(15):
        t = y / 14
        r = int(top_color[0] * (1 - t) + bot_color[0] * t)
        g = int(top_color[1] * (1 - t) + bot_color[1] * t)
        b = int(top_color[2] * (1 - t) + bot_color[2] * t)
        tiny_surf.set_at((0, y), (r, g, b))
    pygame.transform.scale(tiny_surf, (WIDTH, HEIGHT), surf)
    return surf

# Gradient Cache
sky_cache = {
    # Normal Day
    "day": make_sky_surface((100, 160, 240), (190, 220, 255)),
    # Normal Sunset
    "sunset": make_sky_surface((36, 36, 62), (255, 126, 95)),
    # Normal Night
    "night": make_sky_surface((10, 10, 25), (25, 25, 55)),
    # Normal Sunrise
    "sunrise": make_sky_surface((55, 40, 80), (255, 195, 120)),
    # Synthwave (Night mode sky is static dark neon violet)
    "synthwave": make_sky_surface((15, 10, 28), (40, 15, 60)),
    # City (Twilight Sunset)
    "city": make_sky_surface((20, 24, 48), (220, 95, 80)),
    # Winter (Snowy Sky)
    "winter": make_sky_surface((145, 165, 185), (200, 215, 225))
}

# LERP function for colors
def lerp_color(c1, c2, t):
    return (
        int(c1[0] * (1 - t) + c2[0] * t),
        int(c1[1] * (1 - t) + c2[1] * t),
        int(c1[2] * (1 - t) + c2[2] * t)
    )

# Classes
class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, decay_type='linear', shape='circle'):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.max_life = life
        self.life = life
        self.shape = shape
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.97
        self.vy *= 0.97
        self.life -= 1
        
    def draw(self, surface):
        if self.life <= 0:
            return
        alpha = int((self.life / self.max_life) * 255)
        p_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        c = list(self.color)
        if len(c) == 3:
            c.append(alpha)
        else:
            c[3] = int(c[3] * (self.life / self.max_life))
            
        if self.shape == 'circle':
            pygame.draw.circle(p_surf, c, (int(self.size), int(self.size)), int(self.size))
        elif self.shape == 'square':
            pygame.draw.rect(p_surf, c, (0, 0, int(self.size * 2), int(self.size * 2)))
        surface.blit(p_surf, (int(self.x - self.size), int(self.y - self.size)))

class SnowParticle:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(-HEIGHT, 0)
        self.size = random.uniform(1.5, 4.5)
        self.speed = random.uniform(1.0, 2.5)
        self.angle = random.uniform(0, 2 * math.pi)
        
    def update(self):
        self.y += self.speed
        self.x += math.sin(self.angle) * 0.4
        self.angle += 0.04
        if self.y > Y_GROUND or self.x < 0 or self.x > WIDTH:
            self.y = random.uniform(-50, -5)
            self.x = random.uniform(0, WIDTH)
            self.speed = random.uniform(1.0, 2.5)

    def draw(self, surface):
        # Soft transparent white circle
        s_surf = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
        pygame.draw.circle(s_surf, (255, 255, 255, 180), (int(self.size), int(self.size)), int(self.size))
        surface.blit(s_surf, (int(self.x - self.size), int(self.y - self.size)))

class RainParticle:
    """Realistic rain drop — fast diagonal line representing slanted wind-driven rain."""
    def __init__(self, initial=False):
        self.reset(initial)
        
    def reset(self, initial=False):
        # Since rain falls slanted to the left, spawn drops from X=0 to WIDTH+150 to sweep across the screen
        self.x = random.uniform(0, WIDTH + 150)
        self.y = random.uniform(0, Y_GROUND) if initial else random.uniform(-100, -10)
        
        # Depth layers: 0=far (background, small, fast), 1=mid (playfield), 2=near (foreground, large, very fast)
        self.layer = random.choices([0, 1, 2], weights=[30, 45, 25])[0]
        
        if self.layer == 0:
            # Far background drops: thin, shorter, slightly slower
            self.speed_y = random.uniform(15.0, 19.0)
            self.speed_x = random.uniform(-3.5, -2.5)  # slanted wind
            self.thickness = 1
            self.color = (130, 145, 160)
        elif self.layer == 1:
            # Mid playfield drops
            self.speed_y = random.uniform(20.0, 25.0)
            self.speed_x = random.uniform(-5.0, -3.5)
            self.thickness = 1
            self.color = (160, 180, 200)
        else:
            # Near foreground drops: thicker, longest, extremely fast
            self.speed_y = random.uniform(26.0, 32.0)
            self.speed_x = random.uniform(-6.5, -5.0)
            self.thickness = 2
            self.color = (190, 210, 230)
        
        self.splash_timer = 0
        self.splash_x = 0
        self.splash_y = 0
        self.splashing = False
        
    def update(self):
        if self.splashing:
            self.splash_timer -= 1
            if self.splash_timer <= 0:
                self.splashing = False
                self.reset()
            return
        
        self.y += self.speed_y
        self.x += self.speed_x
        
        # When drop hits the ground, trigger splash
        if self.y >= Y_GROUND - 2:
            self.splash_x = self.x
            self.splash_y = Y_GROUND - 2
            self.splashing = True
            self.splash_timer = 5  # brief splash animation
            return
        
        # Reset if off-screen (slanted rain drifts left, so check left bound and bottom)
        if self.x < -20 or self.x > WIDTH + 170:
            self.reset()

    def draw(self, surface):
        if self.splashing:
            # Draw tiny expanding splash ring and ripples at ground level
            splash_r = 5 - self.splash_timer + 2
            splash_color = (180, 200, 220)
            sx = int(self.splash_x)
            sy = int(self.splash_y)
            
            # Draw tiny expanding ripple ellipse
            if splash_r > 0:
                pygame.draw.ellipse(surface, splash_color, (sx - splash_r, sy - 1, splash_r * 2, 2), 1)
            # Upward splash droplets
            pygame.draw.line(surface, splash_color, (sx - splash_r // 2, sy), (sx - splash_r, sy - 3), 1)
            pygame.draw.line(surface, splash_color, (sx + splash_r // 2, sy), (sx + splash_r, sy - 3), 1)
        else:
            # Draw raindrop as a line along its velocity vector (motion blur)
            x1 = int(self.x)
            y1 = int(self.y)
            x2 = int(self.x + self.speed_x * 0.9)
            y2 = int(self.y + self.speed_y * 0.9)
            pygame.draw.line(surface, self.color, (x1, y1), (x2, y2), self.thickness)

class Car:
    def __init__(self, y):
        self.y = y
        self.reset(to_left=random.choice([True, False]))
        
    def reset(self, to_left):
        self.to_left = to_left
        self.speed = random.uniform(0.8, 1.8)
        self.w = 12
        self.h = 6
        if self.to_left:
            self.x = WIDTH + random.uniform(10, 100)
        else:
            self.x = -random.uniform(10, 100)
            
    def update(self):
        if self.to_left:
            self.x -= self.speed
            if self.x + self.w < 0:
                self.reset(to_left=True)
        else:
            self.x += self.speed
            if self.x > WIDTH:
                self.reset(to_left=False)
                
    def draw(self, surface):
        cx = int(self.x)
        # Draw car body silhouette (dark blue-grey)
        pygame.draw.rect(surface, (25, 25, 40), (cx, self.y, self.w, self.h))
        # Draw lights
        if self.to_left:
            # Headlights on left (yellow)
            pygame.draw.rect(surface, (255, 235, 150), (cx, self.y + 1, 2, 2))
            # Taillight on right (red)
            pygame.draw.rect(surface, (230, 50, 50), (cx + self.w - 1, self.y + 1, 1, 2))
        else:
            # Headlights on right
            pygame.draw.rect(surface, (255, 235, 150), (cx + self.w - 2, self.y + 1, 2, 2))
            # Taillight on left
            pygame.draw.rect(surface, (230, 50, 50), (cx, self.y + 1, 1, 2))

class Building:
    def __init__(self, x, width, height, layer, is_burj=False):
        self.x = x
        self.width = width
        self.height = height
        self.layer = layer  # 0: Back (slowest), 1: Mid (faster)
        self.speed = 0.1 if layer == 0 else 0.35
        self.is_burj = is_burj
        
        # Color based on layer (dark grey silhouettes)
        self.color = (33, 33, 48) if layer == 0 else (46, 46, 64)
        
        # Pre-generate window coordinates
        self.windows = []
        if not is_burj:
            rows = height // 20
            cols = width // 15
            for r in range(1, rows - 1):
                for c in range(1, cols - 1):
                    # Randomize window state: 1: On, 0: Off
                    if random.random() < 0.22:
                        # Color: Yellow glow or Cyan glow
                        win_color = random.choice([(255, 220, 110), (120, 240, 255)])
                        self.windows.append((c * 15, r * 20, win_color))
                        
    def update(self):
        self.x -= self.speed
        if self.x + self.width < 0:
            self.x = WIDTH + random.uniform(20, 150)
            
    def draw(self, surface):
        y_base = Y_GROUND
        bx = int(self.x)
        
        if self.is_burj:
            # Burj Khalifa stylized stepped skyscraper spire
            # Segment 1 (Base)
            w1 = self.width
            h1 = self.height // 4
            y1 = y_base - h1
            pygame.draw.rect(surface, self.color, (bx, y1, w1, h1))
            
            # Segment 2
            w2 = int(w1 * 0.75)
            h2 = self.height // 3
            y2 = y1 - h2
            pygame.draw.rect(surface, self.color, (bx + (w1-w2)//2, y2, w2, h2))
            
            # Segment 3
            w3 = int(w1 * 0.45)
            h3 = self.height // 3
            y3 = y2 - h3
            pygame.draw.rect(surface, self.color, (bx + (w1-w3)//2, y3, w3, h3))
            
            # Spire Tip
            spire_w = 4
            spire_h = 45
            sy = y3 - spire_h
            sx = bx + w1 // 2 - spire_w // 2
            pygame.draw.rect(surface, self.color, (sx, sy, spire_w, spire_h))
            
            # Flashing warning aircraft red light on Burj tip
            if pygame.time.get_ticks() % 600 < 300:
                pygame.draw.circle(surface, (255, 40, 40), (int(sx + spire_w // 2), int(sy)), 3)
        else:
            # Regular building
            pygame.draw.rect(surface, self.color, (bx, y_base - self.height, self.width, self.height))
            # Outline
            pygame.draw.rect(surface, (20, 20, 30), (bx, y_base - self.height, self.width, self.height), 1)
            
            # Windows
            for wx, wy, win_color in self.windows:
                # Offset by building position
                actual_wx = bx + wx
                actual_wy = y_base - self.height + wy
                # Window size: 4x6
                pygame.draw.rect(surface, win_color, (actual_wx, actual_wy, 4, 6))

class Cabin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 65
        self.height = 45
        self.speed = 0.2
        
    def update(self):
        self.x -= self.speed
        if self.x + self.width + 45 < 0:
            self.x = WIDTH + random.uniform(800, 1500)
            
    def get_chimney_pos(self):
        return (self.x + self.width - 15, self.y - self.height + 5)
            
    def draw(self, surface, mode, tint_t, is_raining=False):
        cx = int(self.x)
        # Dynamically set colors based on day-night LERP tinting
        hill_color = COLOR_MNT_FRONT
        wall_color = COLOR_CABIN_WALL
        roof_color = COLOR_CABIN_ROOF
        window_color = COLOR_CABIN_WINDOW
        
        # If in winter mode, the roof is white with snow!
        if mode == "winter":
            wall_color = (95, 68, 55)
            roof_color = (230, 235, 240) # Snow roof!
            hill_color = (215, 222, 230)
            window_color = (255, 215, 80)
        elif mode == "normal":
            # Apply normal day/sunset/night color shifts
            if tint_t == 2: # Night
                wall_color = lerp_color(wall_color, (20, 20, 35), 0.75)
                roof_color = lerp_color(roof_color, (15, 15, 30), 0.75)
                window_color = (240, 180, 50)
            elif tint_t == 1: # Sunset
                wall_color = lerp_color(wall_color, (80, 50, 45), 0.45)
                roof_color = lerp_color(roof_color, (70, 40, 45), 0.45)
            elif tint_t == 3: # Sunrise
                wall_color = lerp_color(wall_color, (75, 60, 50), 0.35)
                roof_color = lerp_color(roof_color, (70, 50, 45), 0.35)
                
            if is_raining:
                wall_color = lerp_color(wall_color, (40, 42, 50), 0.4)
                roof_color = lerp_color(roof_color, (35, 38, 45), 0.4)
            
        # 1. Grassy/Snow hill
        pygame.draw.ellipse(surface, hill_color, (cx - 30, self.y - 12, self.width + 60, 25))
        
        # 2. Main structure
        pygame.draw.rect(surface, wall_color, (cx, self.y - self.height, self.width, self.height))
        # Log lines
        for i in range(1, 5):
            ly = self.y - self.height + i * 9
            line_c = (55, 38, 25) if mode != "winter" else (48, 34, 25)
            pygame.draw.line(surface, line_c, (cx, ly), (cx + self.width, ly), 1)
            
        # 3. Chimney
        cx_ch = cx + self.width - 15
        cy = self.y - self.height - 10
        pygame.draw.rect(surface, COLOR_CABIN_CHIMNEY, (cx_ch, cy, 8, 15))
        pygame.draw.rect(surface, (30, 30, 30), (cx_ch - 1, cy, 10, 3))
        
        # 4. Roof
        roof_pts = [
            (cx - 6, self.y - self.height + 2),
            (cx + self.width // 2, self.y - self.height - 18),
            (cx + self.width + 6, self.y - self.height + 2)
        ]
        pygame.draw.polygon(surface, roof_color, roof_pts)
        pygame.draw.polygon(surface, (30, 30, 30), roof_pts, 2)
        
        # Draw icicles hanging in winter mode
        if mode == "winter":
            for ix in range(cx - 4, cx + self.width + 5, 8):
                pygame.draw.polygon(surface, (255, 255, 255), [(ix, self.y - self.height + 2), (ix + 3, self.y - self.height + 2), (ix + 1, self.y - self.height + 9)])
        
        # 5. Door
        door_w = 14
        door_h = 24
        dx = cx + 10
        dy = self.y - door_h
        pygame.draw.rect(surface, COLOR_CABIN_DOOR, (dx, dy, door_w, door_h))
        pygame.draw.circle(surface, (200, 180, 50), (int(dx + door_w - 3), int(dy + door_h // 2)), 2)
        
        # 6. Window
        wx = cx + 36
        wy = self.y - self.height + 12
        pygame.draw.rect(surface, window_color, (wx, wy, 16, 16))
        pygame.draw.rect(surface, (30, 30, 30), (wx, wy, 16, 16), 1)
        pygame.draw.line(surface, (30, 30, 30), (wx + 8, wy), (wx + 8, wy + 16), 1)
        pygame.draw.line(surface, (30, 30, 30), (wx, wy + 8), (wx + 16, wy + 8), 1)

class Tree:
    def __init__(self, x, layer):
        self.x = x
        self.layer = layer  # 0: Back, 1: Mid, 2: Front
        self.speed = [0.4, 0.7, 1.1][layer]
        self.w = [25, 35, 48][layer]
        self.h = [50, 75, 105][layer]
        
    def update(self):
        self.x -= self.speed
        if self.x + self.w < 0:
            self.x = WIDTH + random.uniform(30, 150)
            base_w = [25, 35, 48][self.layer]
            base_h = [50, 75, 105][self.layer]
            self.w = int(base_w * random.uniform(0.85, 1.15))
            self.h = int(base_h * random.uniform(0.85, 1.15))
            
    def draw(self, surface, mode, tint_t, is_raining=False):
        y_base = Y_GROUND
        tx = int(self.x)
        # Trunk
        trunk_w = max(2, self.w // 6)
        trunk_h = self.h // 5
        pygame.draw.rect(surface, (45, 30, 20), (tx + self.w // 2 - trunk_w // 2, y_base - trunk_h, trunk_w, trunk_h))
        
        y_leaf_base = y_base - trunk_h
        seg_h = self.h - trunk_h
        
        # Color based on mode
        if mode == "winter":
            # Snow capped pine trees: soft light blue and white
            base_color = [(180, 200, 220), (140, 165, 190), (110, 135, 160)][self.layer]
        else:
            # Normal green layers
            base_color = TREE_COLORS[self.layer]
            # Dynamic LERP to Night/Sunset if normal mode
            if mode == "normal":
                # We can tint to dark blue-grey at night (tint_t: 0: day, 1: sunset, 2: night, 3: sunrise)
                if tint_t == 2:  # Night
                    base_color = lerp_color(base_color, (15, 20, 35), 0.75)
                elif tint_t == 1:  # Sunset
                    base_color = lerp_color(base_color, (90, 45, 50), 0.5)
                elif tint_t == 3:  # Sunrise
                    base_color = lerp_color(base_color, (85, 75, 60), 0.4)
                
                if is_raining:
                    base_color = lerp_color(base_color, (25, 35, 45), 0.45)
            
        # Draw segments
        for i in range(3):
            factor = 1.0 - (i * 0.2)
            seg_w = int(self.w * factor)
            seg_bottom = y_leaf_base - int(i * (seg_h * 0.28))
            seg_top = seg_bottom - int(seg_h * 0.45)
            
            # Split shading colors (light left, dark right)
            light_color = lerp_color(base_color, (255, 255, 255), 0.12)
            dark_color = lerp_color(base_color, (0, 0, 0), 0.15)
            
            pts_left = [
                (tx + self.w // 2 - seg_w // 2, seg_bottom),
                (tx + self.w // 2, seg_top),
                (tx + self.w // 2, seg_bottom)
            ]
            pts_right = [
                (tx + self.w // 2, seg_bottom),
                (tx + self.w // 2, seg_top),
                (tx + self.w // 2 + seg_w // 2, seg_bottom)
            ]
            
            pygame.draw.polygon(surface, light_color, pts_left)
            pygame.draw.polygon(surface, dark_color, pts_right)
            
            pts_outline = [
                (tx + self.w // 2 - seg_w // 2, seg_bottom),
                (tx + self.w // 2, seg_top),
                (tx + self.w // 2 + seg_w // 2, seg_bottom)
            ]
            pygame.draw.polygon(surface, (20, 30, 25), pts_outline, 1)
            
            # In winter mode, draw a little snow pile on the edges of each branch segment
            if mode == "winter":
                pygame.draw.polygon(surface, (245, 250, 255), [
                    (tx + self.w // 2 - seg_w // 2, seg_bottom),
                    (tx + self.w // 2 - seg_w // 2 + 5, seg_bottom - 3),
                    (tx + self.w // 2, seg_top),
                    (tx + self.w // 2 + seg_w // 2 - 5, seg_bottom - 3),
                    (tx + self.w // 2 + seg_w // 2, seg_bottom)
                ])

class Mountain:
    def __init__(self, layer):
        self.layer = layer
        self.speed = 0.05 if layer == 0 else 0.1
        self.heights = []
        self.offset = 0
        
        num_peaks = 7
        segment_w = WIDTH // (num_peaks - 2)
        for i in range(num_peaks):
            px = (i - 1) * segment_w
            py = Y_GROUND - (120 if layer == 0 else 80) + random.uniform(-35, 35)
            self.heights.append((px, py))
            
    def update(self):
        self.x_offset = self.speed
        self.offset += self.speed
        if self.offset >= (self.heights[2][0] - self.heights[1][0]):
            self.offset = 0
            first_x = self.heights[0][0]
            dx = self.heights[1][0] - first_x
            self.heights.pop(0)
            
            new_heights = []
            for i, (px, py) in enumerate(self.heights):
                new_heights.append(((i - 1) * dx, py))
            self.heights = new_heights
            
            last_x = self.heights[-1][0]
            new_y = Y_GROUND - (120 if self.layer == 0 else 80) + random.uniform(-35, 35)
            self.heights.append((last_x + dx, new_y))

    def draw(self, surface, mode, tint_t, is_raining=False):
        # Base colors
        base_color = COLOR_MNT_BACK if self.layer == 0 else COLOR_MNT_FRONT
        
        if mode == "winter":
            # Snowy mountains (white-capped)
            base_color = (130, 155, 175) if self.layer == 0 else (175, 195, 215)
        elif mode == "normal":
            if tint_t == 2:  # Night
                base_color = lerp_color(base_color, (15, 15, 30), 0.75)
            elif tint_t == 1:  # Sunset
                base_color = lerp_color(base_color, (70, 40, 55), 0.5)
            elif tint_t == 3:  # Sunrise
                base_color = lerp_color(base_color, (75, 55, 65), 0.4)
                
            if is_raining:
                base_color = lerp_color(base_color, (45, 50, 60), 0.45)
                
        points = []
        for px, py in self.heights:
            points.append((int(px - self.offset), int(py)))
            
        points.append((int(points[-1][0]), int(Y_GROUND)))
        points.append((int(points[0][0]), int(Y_GROUND)))
        
        # Base mountain polygon
        pygame.draw.polygon(surface, base_color, points)
        
        # Draw shadow facets on right-facing slopes (creating light coming from top-left)
        shadow_color = lerp_color(base_color, (0, 0, 0), 0.12)
        for i in range(len(self.heights) - 1):
            p1 = points[i]
            p2 = points[i+1]
            if p2[1] > p1[1]:
                facet_pts = [
                    (p1[0], p1[1]),
                    (p2[0], p2[1]),
                    (p2[0], int(Y_GROUND)),
                    (p1[0], int(Y_GROUND))
                ]
                pygame.draw.polygon(surface, shadow_color, facet_pts)
        
        # Draw snow peaks in winter mode
        if mode == "winter":
            # For each peak, draw a small white triangle top
            for i in range(len(self.heights) - 1):
                px, py = self.heights[i][0] - self.offset, self.heights[i][1]
                # Peak cap
                cap_pts = [
                    (int(px - 16), int(py + 14)),
                    (int(px), int(py)),
                    (int(px + 16), int(py + 14)),
                    (int(px + 6), int(py + 9)),
                    (int(px - 6), int(py + 9))
                ]
                # Clip coordinates to screen boundaries to avoid draw errors
                pygame.draw.polygon(surface, (245, 250, 255), cap_pts)

class Bird:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = 120
        self.y = HEIGHT // 2
        self.radius = 16
        self.vel = 0.0
        self.gravity = 0.42
        self.jump_force = -7.8
        self.max_vel = 10.0
        self.angle = 0.0
        
    def jump(self, particles, mode):
        self.vel = self.jump_force
        if jump_sfx:
            jump_sfx.play()
            
        # Tail particles based on mode
        p_color = (0, 255, 255) if mode == "night" else (255, 255, 240, 160)
        if mode == "winter":
            p_color = (240, 245, 255, 200) # snowy puffs
            
        for _ in range(5):
            px = self.x - 12
            py = self.y + 4
            vx = -1.5 - random.uniform(0.0, 1.5)
            vy = random.uniform(-1.0, 1.0)
            size = random.uniform(3, 7)
            life = random.randint(15, 30)
            particles.append(Particle(px, py, vx, vy, p_color, size, life, 'circle'))
            
    def update(self, multiplier=1.0):
        self.vel = min(self.vel + self.gravity * multiplier, self.max_vel)
        self.y += self.vel * multiplier
        
        if self.vel < 0:
            target_angle = 25.0
        else:
            target_angle = max(-80.0, -self.vel * 9.0)
            
        self.angle += (target_angle - self.angle) * 0.15
        
    def draw(self, surface, mode, skin):
        size = 56
        bird_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        
        flap_speed = 0.012 if self.vel >= 0 else 0.025
        wing_y = cy + int(math.sin(pygame.time.get_ticks() * flap_speed) * 4)
        
        # Colors based on skin
        body_color = (255, 204, 0)
        wing_color = (255, 140, 0)
        beak_color = (255, 102, 0)
        outline_color = (40, 30, 20)
        
        if skin == "ninja":
            body_color = (45, 45, 52)
            wing_color = (180, 30, 30)
            beak_color = (230, 90, 20)
            outline_color = (20, 20, 20)
        elif skin == "mech":
            body_color = (130, 135, 145)
            wing_color = (0, 240, 255)
            beak_color = (180, 190, 200)
            outline_color = (35, 35, 45)
        elif skin == "phoenix":
            body_color = (220, 45, 30)
            wing_color = (255, 180, 0)
            beak_color = (255, 220, 0)
            outline_color = (50, 15, 15)
        elif mode == "night" and skin == "classic":
            # Neon Cyberpunk bird
            body_color = (255, 0, 180)  # Neon pink
            wing_color = (0, 255, 240)  # Neon cyan
            beak_color = (255, 230, 0)
            outline_color = (255, 255, 255)
            
        # 1. Beak
        pygame.draw.polygon(bird_surf, beak_color, [(cx + 12, cy - 3), (cx + 21, cy), (cx + 12, cy + 5)])
        pygame.draw.polygon(bird_surf, outline_color, [(cx + 12, cy - 3), (cx + 21, cy), (cx + 12, cy + 5)], 1 if (mode == "night" and skin == "classic") else 2)
        
        # 2. Main Body
        pygame.draw.circle(bird_surf, body_color, (cx, cy), self.radius)
        pygame.draw.circle(bird_surf, outline_color, (cx, cy), self.radius, 1 if (mode == "night" and skin == "classic") else 2)
        
        # Accessories
        if skin == "ninja":
            # Red headband
            pygame.draw.rect(bird_surf, (180, 30, 30), (cx - 14, cy - 9, 26, 4))
            pygame.draw.polygon(bird_surf, (180, 30, 30), [(cx - 14, cy - 7), (cx - 22, cy - 4), (cx - 20, cy - 9)])
            pygame.draw.polygon(bird_surf, (180, 30, 30), [(cx - 14, cy - 7), (cx - 24, cy - 10), (cx - 19, cy - 12)])
        elif skin == "mech":
            # Panel cross lines
            pygame.draw.line(bird_surf, outline_color, (cx - 10, cy), (cx + 10, cy), 1)
            pygame.draw.line(bird_surf, outline_color, (cx, cy - 10), (cx, cy + 10), 1)
        elif skin == "phoenix":
            # Flame feathers on head top
            pygame.draw.polygon(bird_surf, (255, 120, 0), [(cx - 8, cy - 14), (cx - 18, cy - 24), (cx - 2, cy - 15)])
            pygame.draw.polygon(bird_surf, (220, 45, 30), [(cx - 2, cy - 15), (cx - 8, cy - 28), (cx + 4, cy - 15)])
            
        if skin in ["classic", "phoenix"] and not (mode == "night" and skin == "classic"):
            # Belly highlight
            pygame.draw.arc(bird_surf, (255, 255, 255), (cx - self.radius + 3, cy - 2, self.radius * 2 - 6, self.radius), 0, math.pi, 2)
            
        # 3. Eye
        eye_x = cx + 6
        eye_y = cy - 5
        if skin == "mech":
            # Red glowing visor
            pygame.draw.rect(bird_surf, (0, 240, 255), (eye_x - 3, eye_y - 2, 8, 4), 0, 1)
            pygame.draw.rect(bird_surf, outline_color, (eye_x - 3, eye_y - 2, 8, 4), 1, 1)
        else:
            pygame.draw.circle(bird_surf, (255, 255, 255), (eye_x, eye_y), 5)
            pygame.draw.circle(bird_surf, outline_color, (eye_x, eye_y), 5, 1)
            pygame.draw.circle(bird_surf, (0, 0, 0), (eye_x + 1, eye_y), 2)
            if skin != "ninja":
                pygame.draw.circle(bird_surf, (255, 255, 255), (eye_x - 1, eye_y - 1), 1)
            
        # 4. Wing
        wing_w = 13
        wing_h = 10
        pygame.draw.ellipse(bird_surf, wing_color, (cx - 11, wing_y - wing_h // 2, wing_w, wing_h))
        pygame.draw.ellipse(bird_surf, outline_color, (cx - 11, wing_y - wing_h // 2, wing_w, wing_h), 1 if (mode == "night" and skin == "classic") else 2)
        
        # 5. Santa Hat in Winter Mode!
        if mode == "winter":
            # Red triangle
            pygame.draw.polygon(bird_surf, (220, 40, 40), [(cx - 14, cy - 10), (cx - 2, cy - 23), (cx + 4, cy - 12)])
            # White fluffy brim
            pygame.draw.rect(bird_surf, (255, 255, 255), (cx - 14, cy - 13, 19, 4), 0, 2)
            # Pom-pom (white circle at tip)
            pygame.draw.circle(bird_surf, (255, 255, 255), (cx - 2, cy - 24), 3)
            
        # Rotate
        rotated_surf = pygame.transform.rotate(bird_surf, self.angle)
        new_rect = rotated_surf.get_rect(center=(self.x, self.y))
        
        # Neon glow filter in night mode
        if mode == "night" and skin == "classic":
            # Blit slightly larger cyan outline underneath for a neon shadow
            glow = pygame.transform.scale(rotated_surf, (int(new_rect.width * 1.1), int(new_rect.height * 1.1)))
            glow_rect = glow.get_rect(center=(self.x, self.y))
            # Blit white core on top
            surface.blit(rotated_surf, new_rect.topleft)
        else:
            surface.blit(rotated_surf, new_rect.topleft)

class Pipe:
    def __init__(self, x, mode):
        self.x = x
        self.width = 76
        self.gap = 155
        self.mode = mode
        self.gap_y = random.randint(180, Y_GROUND - 180)
        self.speed = 3.0
        self.passed = False
        
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.gap_y - self.gap // 2)
        self.bot_rect = pygame.Rect(self.x, self.gap_y + self.gap // 2, self.width, Y_GROUND - (self.gap_y + self.gap // 2))

    def update(self, speed=3.0):
        self.x -= speed
        self.top_rect.x = self.x
        self.bot_rect.x = self.x

    def draw(self, surface):
        # Top Pipe
        self.draw_single_pipe(surface, self.top_rect, is_top=True)
        # Bottom Pipe
        self.draw_single_pipe(surface, self.bot_rect, is_top=False)
        
    def draw_single_pipe(self, surface, rect, is_top):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        if h <= 0:
            return
            
        if self.mode == "night":
            # Neon Synthwave Style Pipes (outlines of cyan/pink)
            color_neon = (0, 255, 255) if is_top else (255, 0, 180)
            pygame.draw.rect(surface, (10, 10, 20), (x, y, w, h))  # dark center
            pygame.draw.rect(surface, color_neon, (x, y, w, h), 2)  # wire outline
            
            # Caps
            lip_h = 24
            lip_w = w + 10
            lip_x = x - 5
            lip_y = (y + h - lip_h) if is_top else y
            pygame.draw.rect(surface, (10, 10, 20), (lip_x, lip_y, lip_w, lip_h))
            pygame.draw.rect(surface, color_neon, (lip_x, lip_y, lip_w, lip_h), 2)
            
        elif self.mode == "city":
            # Steel construction girders with diagonal warning stripes
            pygame.draw.rect(surface, (80, 85, 95), (x, y, w, h)) # Iron core
            # Draw trusses (X patterns)
            for ty in range(y, y + h - 30, 30):
                pygame.draw.line(surface, (50, 55, 65), (x, ty), (x + w, ty + 30), 2)
                pygame.draw.line(surface, (50, 55, 65), (x + w, ty), (x, ty + 30), 2)
            pygame.draw.rect(surface, (30, 32, 36), (x, y, w, h), 2) # outline
            
            # Caps (Lip) with hazard black/yellow warning stripes
            lip_h = 24
            lip_w = w + 10
            lip_x = x - 5
            lip_y = (y + h - lip_h) if is_top else y
            
            # Yellow cap base
            pygame.draw.rect(surface, (240, 195, 30), (lip_x, lip_y, lip_w, lip_h))
            # Black diagonal stripes
            for sx in range(lip_x - 10, lip_x + lip_w + 10, 12):
                pygame.draw.polygon(surface, (30, 30, 30), [
                    (sx, lip_y), (sx + 6, lip_y),
                    (sx + 6 - 8, lip_y + lip_h), (sx - 8, lip_y + lip_h)
                ])
            pygame.draw.rect(surface, (30, 30, 30), (lip_x, lip_y, lip_w, lip_h), 2) # Outline
            
        else:
            # Nature Green Pipes (Normal / Winter)
            s_w = int(w * 0.15)
            pygame.draw.rect(surface, COLOR_PIPE_SHADOW, (x, y, s_w, h))
            hl_x = x + s_w
            hl_w = int(w * 0.10)
            pygame.draw.rect(surface, COLOR_PIPE_HIGHLIGHT, (hl_x, y, hl_w, h))
            mb_x = hl_x + hl_w
            mb_w = w - s_w - hl_w
            pygame.draw.rect(surface, COLOR_PIPE_BODY, (mb_x, y, mb_w, h))
            pygame.draw.rect(surface, (36, 100, 40), (x + w - int(w*0.15), y, int(w*0.15), h))
            
            # Cap
            lip_h = 24
            lip_w = w + 10
            lip_x = x - 5
            lip_y = (y + h - lip_h) if is_top else y
            
            pygame.draw.rect(surface, COLOR_PIPE_SHADOW, (lip_x, lip_y, int(lip_w * 0.15), lip_h))
            pygame.draw.rect(surface, COLOR_PIPE_HIGHLIGHT, (lip_x + int(lip_w * 0.15), lip_y, int(lip_w * 0.10), lip_h))
            pygame.draw.rect(surface, COLOR_PIPE_LIP, (lip_x + int(lip_w * 0.25), lip_y, lip_w - int(lip_w * 0.25), lip_h))
            pygame.draw.rect(surface, (36, 100, 40), (lip_x + lip_w - int(lip_w * 0.15), lip_y, int(lip_w * 0.15), lip_h))
            
            # Outlines
            pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, (x, y, w, h), 2)
            pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, (lip_x, lip_y, lip_w, lip_h), 2)
            
            # If Winter mode, draw a snow pile layer sitting on top of the caps!
            if self.mode == "winter":
                snow_y = lip_y - 6 if is_top else lip_y - 6
                # Top pipe: snow on the bottom lip. Bottom pipe: snow on the top lip.
                if is_top:
                    # Snow is at the very bottom edge of top pipe, resting on the top lip overhang
                    pygame.draw.rect(surface, (255, 255, 255), (lip_x + 1, lip_y - 4, lip_w - 2, 5), 0, 2)
                else:
                    # Bottom pipe snow on top lip
                    pygame.draw.rect(surface, (255, 255, 255), (lip_x + 1, lip_y - 5, lip_w - 2, 6), 0, 3)


class FlyingObstacle:
    """A flying bird or bat obstacle that crosses the screen horizontally."""
    def __init__(self, x, y, mode, speed=4.0):
        self.x = x
        self.y = y
        self.base_y = y
        self.mode = mode
        self.speed = speed
        self.radius = 12
        self.width = 28
        self.height = 20
        self.active = True
        self.wing_angle = 0.0
        self.wobble_offset = random.uniform(0, math.pi * 2)
        # Bird in forest/city, bat in night/winter
        self.is_bat = mode in ("night", "winter")
        
    def update(self, speed_multiplier=1.0):
        self.x -= self.speed * speed_multiplier
        # Gentle sine-wave vertical wobble
        self.wing_angle += 0.18
        self.y = self.base_y + math.sin(self.wing_angle + self.wobble_offset) * 18
        
    def draw(self, surface):
        if not self.active:
            return
        px = int(self.x)
        py = int(self.y)
        
        # Wing flap animation
        wing_flap = math.sin(self.wing_angle * 2.5) * 10
        
        if self.is_bat:
            # Bat: dark purple body with angular wings
            body_color = (60, 30, 80) if self.mode == "night" else (50, 40, 55)
            wing_color = (90, 50, 120) if self.mode == "night" else (70, 55, 75)
            
            # Body (oval)
            pygame.draw.ellipse(surface, body_color, (px - 7, py - 5, 14, 10))
            # Eyes (tiny red dots)
            pygame.draw.circle(surface, (255, 50, 50), (px - 3, py - 2), 1)
            pygame.draw.circle(surface, (255, 50, 50), (px + 3, py - 2), 1)
            # Left wing (angular)
            wing_y_offset = int(wing_flap)
            pts_l = [(px - 6, py), (px - 20, py - 4 + wing_y_offset), (px - 14, py + 3 + wing_y_offset // 2)]
            pygame.draw.polygon(surface, wing_color, pts_l)
            # Right wing (angular)
            pts_r = [(px + 6, py), (px + 20, py - 4 + wing_y_offset), (px + 14, py + 3 + wing_y_offset // 2)]
            pygame.draw.polygon(surface, wing_color, pts_r)
            # Wing membrane lines
            pygame.draw.line(surface, body_color, (px - 6, py), (px - 18, py - 2 + wing_y_offset), 1)
            pygame.draw.line(surface, body_color, (px + 6, py), (px + 18, py - 2 + wing_y_offset), 1)
        else:
            # Bird: warm brown body with feathered wings
            body_color = (140, 90, 50)
            wing_color = (170, 120, 70)
            belly_color = (220, 190, 150)
            beak_color = (255, 180, 50)
            
            # Body
            pygame.draw.ellipse(surface, body_color, (px - 8, py - 5, 16, 11))
            # Belly
            pygame.draw.ellipse(surface, belly_color, (px - 5, py - 1, 10, 7))
            # Head
            pygame.draw.circle(surface, body_color, (px + 7, py - 3), 5)
            # Eye
            pygame.draw.circle(surface, (255, 255, 255), (px + 9, py - 4), 2)
            pygame.draw.circle(surface, (0, 0, 0), (px + 9, py - 4), 1)
            # Beak
            pygame.draw.polygon(surface, beak_color, [(px + 12, py - 3), (px + 17, py - 2), (px + 12, py - 1)])
            # Wings
            wing_y_offset = int(wing_flap)
            # Left wing
            pts_l = [(px - 4, py - 3), (px - 16, py - 8 + wing_y_offset), (px - 10, py + 1)]
            pygame.draw.polygon(surface, wing_color, pts_l)
            # Right wing (behind body, just top shows)
            pts_r = [(px + 2, py - 3), (px + 8, py - 12 + wing_y_offset), (px + 12, py - 4)]
            pygame.draw.polygon(surface, wing_color, pts_r)
    
    def get_rect(self):
        return pygame.Rect(int(self.x) - 12, int(self.y) - 8, 24, 16)


class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type  # 'shield' or 'slow'
        self.radius = 12
        self.angle = 0.0
        self.active = True
        self.width = self.radius * 2
        self.height = self.radius * 2
        
    def update(self, speed):
        self.x -= speed
        self.angle += 0.05
        
    def draw(self, surface):
        if not self.active:
            return
            
        px = int(self.x)
        py = int(self.y)
        r = self.radius
        
        # Spin rotation offsets
        offset_x = int(math.cos(self.angle) * 4)
        offset_y = int(math.sin(self.angle) * 4)
        
        if self.type == 'shield':
            # Blue orb with spinning shield rings
            pygame.draw.circle(surface, (0, 150, 255), (px, py), r - 3)
            pygame.draw.circle(surface, (0, 230, 255), (px + offset_x, py + offset_y), r, 2)
            pygame.draw.circle(surface, (255, 255, 255), (px - 2, py - 2), 3)
        elif self.type == 'slow':
            # Green hourglass
            pygame.draw.circle(surface, (46, 125, 50), (px, py), r - 2)
            c = (120, 255, 120)
            sin_a = math.sin(self.angle)
            cos_a = math.cos(self.angle)
            
            def rotate_pt(lx, ly):
                rx = px + int(lx * cos_a - ly * sin_a)
                ry = py + int(lx * sin_a + ly * cos_a)
                return rx, ry
                
            p1 = rotate_pt(-6, -8)
            p2 = rotate_pt(6, -8)
            p3 = rotate_pt(-1, 0)
            p4 = rotate_pt(1, 0)
            p5 = rotate_pt(-6, 8)
            p6 = rotate_pt(6, 8)
            
            pygame.draw.polygon(surface, c, [p1, p2, p4, p6, p5, p3])
            pygame.draw.circle(surface, (120, 255, 120), (px, py), r, 1)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.angle = random.uniform(0, 2 * math.pi)  # randomized starting angle
        self.spin_speed = 0.08
        self.active = True
        self.width = self.radius * 2
        self.height = self.radius * 2
        
    def update(self, speed):
        self.x -= speed
        self.angle += self.spin_speed
        
    def draw(self, surface, mode):
        if not self.active:
            return
            
        px = int(self.x)
        py = int(self.y)
        r = self.radius
        
        # Calculate horizontal scaling factor for 3D rotation
        scale_x = abs(math.cos(self.angle))
        
        # Ellipse width must be at least 2 pixels and must be cast to an integer
        ellipse_w = int(max(2, int(r * 2 * scale_x)))
        ellipse_h = int(r * 2)
        
        # Center the ellipse at (px, py)
        ellipse_rect = pygame.Rect(px - ellipse_w // 2, py - ellipse_h // 2, ellipse_w, ellipse_h)
        
        # Determine colors based on mode
        if mode == "night":
            # Synthwave: Neon Cyan core with Neon Pink border
            color_center = (0, 255, 255)
            color_border = (255, 0, 180)
            color_highlight = (255, 255, 255)
        elif mode == "city":
            # City: Sleek Silver with steel border
            color_center = (220, 220, 225)
            color_border = (120, 125, 135)
            color_highlight = (255, 255, 255)
        elif mode == "winter":
            # Winter: Ice blue with steel blue border
            color_center = (180, 225, 255)
            color_border = (60, 120, 170)
            color_highlight = (255, 255, 255)
        else:
            # Forest (normal): Gold
            color_center = (255, 215, 0)
            color_border = (212, 175, 55)
            color_highlight = (255, 245, 150)
        
        # Draw the coin body (filled ellipse)
        pygame.draw.ellipse(surface, color_center, ellipse_rect)
        
        # Draw the coin border
        border_width = 2
        if ellipse_w > border_width * 2:
            pygame.draw.ellipse(surface, color_border, ellipse_rect, border_width)
        else:
            pygame.draw.ellipse(surface, color_border, ellipse_rect, 1)
            
        # Draw a small vertical inner highlight line if wide enough to look shiny
        if ellipse_w > 8:
            highlight_w = int(ellipse_w * 0.2)
            highlight_rect = pygame.Rect(
                px - highlight_w // 2 - int(ellipse_w * 0.1),
                py - ellipse_h // 3,
                max(1, highlight_w),
                int(ellipse_h * 0.6)
            )
            pygame.draw.ellipse(surface, color_highlight, highlight_rect)

class Ground:
    def __init__(self):
        self.offset = 0
        self.speed = 3.0
        
    def update(self):
        self.offset += self.speed
        if self.offset >= 24:
            self.offset = 0
            
    def draw(self, surface, mode):
        if mode == "night":
            # Neon Synthwave Ground (Scrolling grid mesh)
            pygame.draw.rect(surface, (10, 10, 20), (0, Y_GROUND, WIDTH, GROUND_HEIGHT))
            pygame.draw.line(surface, (255, 0, 180), (0, Y_GROUND), (WIDTH, Y_GROUND), 3) # magenta horizon
            
            # Draw scrolling grid lines
            for i in range(12):
                ly = int(Y_GROUND + int(1.4**i * 2.0) + (self.offset % 20))
                if ly < HEIGHT:
                    pygame.draw.line(surface, (255, 0, 180), (0, ly), (WIDTH, ly), 1)
                    
            # Radiating vertical perspective lines
            for gx in range(-150, WIDTH + 150, 45):
                pygame.draw.line(surface, (0, 255, 255), (WIDTH // 2, Y_GROUND), (gx, HEIGHT), 1)
                
        elif mode == "city":
            # Asphalt/Road Ground
            pygame.draw.rect(surface, (45, 45, 50), (0, Y_GROUND, WIDTH, GROUND_HEIGHT)) # grey road
            pygame.draw.rect(surface, (120, 120, 120), (0, Y_GROUND, WIDTH, 8)) # curb
            
            # Scrolling road dashes (yellow dashed lane lines)
            num_dashes = (WIDTH // 35) + 2
            for i in range(num_dashes):
                dx = int(i * 35 - self.offset)
                pygame.draw.rect(surface, (240, 200, 30), (dx, Y_GROUND + GROUND_HEIGHT // 2 - 2, 18, 4))
                
        elif mode == "winter":
            # Snow covered ground
            pygame.draw.rect(surface, (220, 225, 235), (0, Y_GROUND, WIDTH, GROUND_HEIGHT))
            # Moving grey texture marks
            num_patterns = (WIDTH // 24) + 2
            for i in range(num_patterns):
                px = int(i * 24 - self.offset)
                pygame.draw.line(surface, (180, 190, 205), (px, Y_GROUND + 20), (px + 8, Y_GROUND + 35), 2)
                
            # Solid pure white snow top border with smooth mounds
            pygame.draw.rect(surface, (255, 255, 255), (0, Y_GROUND, WIDTH, 12))
            for i in range(0, WIDTH + 20, 20):
                px = i - int(self.offset) % 20
                # Curved snow mounds
                pygame.draw.ellipse(surface, (255, 255, 255), (px, Y_GROUND + 3, 26, 12))
                
        else:
            # Normal Grass Ground
            pygame.draw.rect(surface, COLOR_DIRT, (0, Y_GROUND, WIDTH, GROUND_HEIGHT))
            
            num_patterns = (WIDTH // 24) + 2
            for i in range(num_patterns):
                px = int(i * 24 - self.offset)
                pygame.draw.line(surface, COLOR_DIRT_DARK, (px, Y_GROUND + 15), (px + 10, Y_GROUND + 40), 3)
                
            pygame.draw.rect(surface, COLOR_GRASS_TOP, (0, Y_GROUND, WIDTH, 12))
            pygame.draw.line(surface, (50, 120, 50), (0, Y_GROUND), (WIDTH, Y_GROUND), 2)
            
            for i in range(0, WIDTH + 20, 15):
                px = i - int(self.offset) % 15
                pygame.draw.polygon(surface, COLOR_GRASS_TOP, [(px, Y_GROUND + 12), (px + 7, Y_GROUND + 4), (px + 14, Y_GROUND + 12)])

# Main Controller
class Game:
    def __init__(self):
        self.state = "START"  # START, PLAYING, GAMEOVER, LOGIN
        self.mode = "normal"  # normal, night, city, winter
        
        self.username = load_username()
        self.leaderboard = load_leaderboard()
        
        self.bird = Bird()
        self.ground = Ground()
        
        # Parallax components
        self.mountains_back = Mountain(0)
        self.mountains_front = Mountain(1)
        self.cabin = Cabin(350, Y_GROUND)
        
        self.trees = []
        for i in range(4): self.trees.append(Tree(random.uniform(50, WIDTH + 100) + i * 140, 0))
        for i in range(4): self.trees.append(Tree(random.uniform(50, WIDTH + 100) + i * 140, 1))
        for i in range(4): self.trees.append(Tree(random.uniform(50, WIDTH + 100) + i * 140, 2))
        
        # City Mode Elements
        self.buildings = []
        # Burj Khalifa (unique)
        self.buildings.append(Building(280, 55, 320, 0, is_burj=True))
        # Silhouette skyscrapers
        for i in range(4):
            self.buildings.append(Building(random.uniform(50, WIDTH+100) + i * 130, random.randint(45, 75), random.randint(180, 290), 0))
            self.buildings.append(Building(random.uniform(50, WIDTH+100) + i * 130, random.randint(40, 65), random.randint(110, 200), 1))
            
        self.cars = [Car(Y_GROUND - 12), Car(Y_GROUND - 18)]
        
        # Winter Mode snow particles
        self.snowflakes = [SnowParticle() for _ in range(45)]
        
        # Weather variables
        self.is_raining = False
        self.rain_particles = []
        self.lightning_flash_timer = 0
        
        self.pipes = []
        self.particles = []
        self.coins = []
        self.session_coins = 0
        
        self.score = 0
        self.high_score = self.get_player_high_score()
        self.is_new_high_score = False
        self.shake_timer = 0
        
        # Modals
        self.show_leaderboard = False
        self.show_skins_shop = False
        self.show_about = False
        
        # Text input controller
        self.login_input = ""
        
        # Day-night clock tick for Normal Mode
        self.sky_ticks = 0
        self.sky_phase = 0  # 0: Day, 1: Sunset, 2: Night, 3: Sunrise
        self.tint_t = 0     # LERP color index Reference
        
        # Volume settings
        self.volume_level = 0.5
        self.apply_volume()
        
        # Equipped Skin & Floating Popups
        self.equipped_skin = load_equipped_skin()
        self.load_player_profile()
        self.score_popups = []
        self.first_flap = False
        
        # Power-Ups System
        self.powerups = []
        self.shield_active = False
        self.slow_timer = 0
        self.immunity_timer = 0
        
        # Flying Obstacles System
        self.flying_obstacles = []
        
        # Difficulty Progression
        self.current_tier = "EASY"
        self.tier_popup_timer = 0
        self.tier_popup_text = ""
        self.tier_popup_color = (0, 0, 0)

        
    def get_player_high_score(self):
        for entry in self.leaderboard:
            if entry["name"].lower() == self.username.lower():
                return entry["score"]
        return 0

    def load_player_profile(self):
        self.profile = load_profile_data(self.username)
        # Synchronize/initialize high score with leaderboard if profile is new or lower
        leaderboard_hs = self.get_player_high_score()
        if leaderboard_hs > self.profile["high_score"]:
            self.profile["high_score"] = leaderboard_hs
            save_profile_data(self.username, self.profile)
        self.high_score = self.profile["high_score"]
        
        # Verify equipped skin is unlocked, otherwise reset to classic
        if self.equipped_skin not in self.profile["unlocked_skins"]:
            self.equipped_skin = "classic"
            save_equipped_skin("classic")

    def apply_volume(self):
        # Update background music
        pygame.mixer.music.set_volume(self.volume_level * 0.4)
        
        # Update sound effects
        if jump_sfx:
            jump_sfx.set_volume(self.volume_level * 0.3)
        if point_sfx:
            point_sfx.set_volume(self.volume_level * 0.35)
        if collision_sfx:
            collision_sfx.set_volume(self.volume_level * 0.5)
        if shield_break_sfx:
            shield_break_sfx.set_volume(self.volume_level * 0.45)
        if powerup_pickup_sfx:
            powerup_pickup_sfx.set_volume(self.volume_level * 0.35)
        if coin_pickup_sfx:
            coin_pickup_sfx.set_volume(self.volume_level * 0.4)

    def cycle_volume(self):
        if self.volume_level == 0.5:
            self.volume_level = 1.0
        elif self.volume_level == 1.0:
            self.volume_level = 0.0
        elif self.volume_level == 0.0:
            self.volume_level = 0.2
        else:
            self.volume_level = 0.5
        self.apply_volume()

    def spawn_items_for_pipe(self, pipe):
        roll = random.random()
        px = pipe.x + pipe.width // 2
        py = pipe.gap_y
        if roll < 0.15:
            p_type = random.choice(['shield', 'slow'])
            self.powerups.append(PowerUp(px, py, p_type))
        elif roll < 0.65:  # 0.15 + 0.50
            self.coins.append(Coin(px, py))

    def get_ambient_track(self):
        """Returns the ambient track name with intensity suffix based on difficulty tier."""
        # Determine base track
        if self.mode == "normal":
            if getattr(self, "is_raining", False):
                base = "rain_ambient"
            else:
                base = "nature_ambient"
        elif self.mode == "night":
            base = "synthwave_ambient"
        elif self.mode == "city":
            base = "city_ambient"
        elif self.mode == "winter":
            base = "winter_ambient"
        else:
            base = "nature_ambient"
        
        # Append intensity suffix based on tier
        tier = getattr(self, "current_tier", "EASY")
        if tier == "EASY":
            return base + "_calm"
        elif tier == "MEDIUM":
            return base + "_mid"
        else:  # HARD or INSANE
            return base + "_intense"

    def get_difficulty_tier(self):
        """Returns (tier_name, color, pipe_speed, pipe_gap) based on current score."""
        if self.score >= 25:
            return ("INSANE", (255, 50, 50), 4.8, 118)
        elif self.score >= 15:
            return ("HARD", (255, 140, 30), 4.2, 128)
        elif self.score >= 5:
            return ("MEDIUM", (255, 220, 50), 3.6, 140)
        else:
            return ("EASY", (80, 220, 80), 3.0, 155)

    def start_game(self):
        self.state = "PLAYING"
        self.bird.reset()
        self.pipes = [Pipe(WIDTH + 100, self.mode), Pipe(WIDTH + 335, self.mode)]
        self.score = 0
        self.is_new_high_score = False
        self.particles = []
        self.score_popups = []
        self.first_flap = False
        self.powerups = []
        self.coins = []
        self.session_coins = 0
        self.shield_active = False
        self.slow_timer = 0
        self.immunity_timer = 0
        self.flying_obstacles = []
        self.current_tier = "EASY"
        self.tier_popup_timer = 0
        self.tier_popup_text = ""
        self.tier_popup_color = (0, 0, 0)
        
        # Rainy Round check: 35% chance when in normal mode
        if self.mode == "normal" and random.random() < 0.35:
            self.is_raining = True
            self.rain_particles = [RainParticle(initial=True) for _ in range(120)]
        else:
            self.is_raining = False
            self.rain_particles = []
        self.lightning_flash_timer = 0
        
        # Spawn initial items for both pipes
        self.spawn_items_for_pipe(self.pipes[0])
        self.spawn_items_for_pipe(self.pipes[1])
            
        play_ambient(self.volume_level * 0.85, self.get_ambient_track())

    def trigger_game_over(self):
        self.state = "GAMEOVER"
        self.shake_timer = 18
        
        # Add session coins to lifetime profile and update high score
        self.profile["coins"] += self.session_coins
        if self.score > self.profile["high_score"]:
            self.profile["high_score"] = self.score
        save_profile_data(self.username, self.profile)
        
        
        if collision_sfx:
            collision_sfx.play()
            
        # Particles burst
        burst_c = (255, 215, 0)
        if self.mode == "night":
            burst_c = (0, 255, 255)
        elif self.mode == "winter":
            burst_c = (245, 250, 255)
            
        for _ in range(35):
            px = self.bird.x
            py = self.bird.y
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3.0, 7.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([
                burst_c,
                (255, 100, 30),
                (255, 255, 255),
                (100, 210, 100) if self.mode != "night" else (255, 0, 180)
            ])
            size = random.uniform(3, 6)
            life = random.randint(20, 45)
            self.particles.append(Particle(px, py, vx, vy, color, size, life, 'circle'))
            
        # Add to leaderboard if score fits
        self.update_leaderboard()

    def update_leaderboard(self):
        # Update high score cache
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_high_score = True

            
        # Update JSON list
        name_exists = False
        for entry in self.leaderboard:
            if entry["name"].lower() == self.username.lower():
                name_exists = True
                if self.score > entry["score"]:
                    entry["score"] = self.score
                break
                
        if not name_exists:
            self.leaderboard.append({"name": self.username, "score": self.score})
            
        save_leaderboard(self.leaderboard)
        # Reload sorted list
        self.leaderboard = load_leaderboard()

    def handle_events(self):
        global window_w, window_h, screen
        
        # Scaling parameters for coordinate mapping
        scale = min(window_w / WIDTH, window_h / HEIGHT)
        dx = (window_w - WIDTH * scale) // 2
        dy = (window_h - HEIGHT * scale) // 2
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.VIDEORESIZE:
                window_w, window_h = event.w, event.h
                screen = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)
                
            # Key Inputs
            if event.type == pygame.KEYDOWN:
                if self.state == "LOGIN":
                    if event.key == pygame.K_BACKSPACE:
                        self.login_input = self.login_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.login_input.strip():
                            self.username = self.login_input.strip()[:12]
                            save_username(self.username)
                            self.load_player_profile()
                            self.state = "START"
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "START"
                    else:
                        # Character text entry
                        if len(self.login_input) < 12 and event.unicode.isalnum() or event.key == pygame.K_SPACE:
                            self.login_input += event.unicode
                            
                elif event.key == pygame.K_SPACE:
                    if not self.show_leaderboard and not self.show_skins_shop and not self.show_about:
                        self.perform_action()
                        
            # Mouse / Touch Inputs (fully mobile responsive translate coordinates)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mx, my = event.pos
                    # Map to virtual coords dynamically using actual current window size
                    scr_w, scr_h = screen.get_size()
                    cur_scale = min(scr_w / WIDTH, scr_h / HEIGHT)
                    cur_dx = (scr_w - WIDTH * cur_scale) // 2
                    cur_dy = (scr_h - HEIGHT * cur_scale) // 2
                    if cur_scale > 0:
                        vmx = (mx - cur_dx) / cur_scale
                        vmy = (my - cur_dy) / cur_scale
                    else:
                        vmx, vmy = mx, my
                        
                    # Handle HUD click overrides first
                    if self.state == "START":
                        if self.show_about:
                            card_w = 360
                            card_h = 320
                            card_x = WIDTH // 2 - card_w // 2
                            card_y = HEIGHT // 2 - card_h // 2 - 30
                            close_btn = pygame.Rect(WIDTH // 2 - 60, card_y + card_h - 45, 120, 32)
                            if close_btn.collidepoint(vmx, vmy):
                                self.show_about = False
                            return

                        if self.show_leaderboard:
                            # Close leaderboard modal check
                            card_h = 320
                            card_y = HEIGHT // 2 - card_h // 2 - 30
                            close_btn = pygame.Rect(WIDTH // 2 - 60, card_y + card_h - 45, 120, 32)
                            if close_btn.collidepoint(vmx, vmy):
                                self.show_leaderboard = False
                            return
                            
                        if self.show_skins_shop:
                            card_w = 380
                            card_h = 360
                            card_x = WIDTH // 2 - card_w // 2
                            card_y = HEIGHT // 2 - card_h // 2 - 20
                            
                            close_btn = pygame.Rect(WIDTH // 2 - 60, card_y + card_h - 45, 120, 32)
                            if close_btn.collidepoint(vmx, vmy):
                                self.show_skins_shop = False
                                return
                                
                            for i, skin_name in enumerate(["classic", "ninja", "mech", "phoenix"]):
                                cost = 0
                                if skin_name == "classic": unlocked = True
                                elif skin_name == "ninja":
                                    cost = 25
                                    unlocked = (skin_name in self.profile["unlocked_skins"]) or (self.high_score >= 5)
                                elif skin_name == "mech":
                                    cost = 75
                                    unlocked = (skin_name in self.profile["unlocked_skins"]) or (self.high_score >= 12)
                                elif skin_name == "phoenix":
                                    cost = 150
                                    unlocked = (skin_name in self.profile["unlocked_skins"]) or (self.high_score >= 20)
                                
                                row_y = card_y + 70 + i * 62
                                btn_rect = pygame.Rect(card_x + card_w - 95, row_y + 12, 80, 28)
                                
                                if unlocked:
                                    if skin_name != self.equipped_skin and btn_rect.collidepoint(vmx, vmy):
                                        self.equipped_skin = skin_name
                                        save_equipped_skin(skin_name)
                                        return
                                else:
                                    if self.profile["coins"] >= cost and btn_rect.collidepoint(vmx, vmy):
                                        self.profile["coins"] -= cost
                                        self.profile["unlocked_skins"].append(skin_name)
                                        save_profile_data(self.username, self.profile)
                                        self.equipped_skin = skin_name
                                        save_equipped_skin(skin_name)
                                        if powerup_pickup_sfx:
                                            powerup_pickup_sfx.play()
                                        return
                            return
                            
                        # About Click (top-right)
                        about_btn = pygame.Rect(WIDTH - 115, 15, 100, 35)
                        if about_btn.collidepoint(vmx, vmy):
                            self.show_about = True
                            return

                        # Profile Click (top bar)
                        prof_btn = pygame.Rect(15, 15, 160, 35)
                        if prof_btn.collidepoint(vmx, vmy):
                            self.login_input = self.username
                            self.state = "LOGIN"
                            return
                            
                        # Leaderboard Click
                        lead_btn = pygame.Rect(32, 645, 135, 40)
                        if lead_btn.collidepoint(vmx, vmy):
                            self.show_leaderboard = True
                            return
                            
                        # Skins Click
                        skins_btn = pygame.Rect(182, 645, 135, 40)
                        if skins_btn.collidepoint(vmx, vmy):
                            self.show_skins_shop = True
                            return
                            
                        # Volume Click
                        vol_btn = pygame.Rect(332, 645, 135, 40)
                        if vol_btn.collidepoint(vmx, vmy):
                            self.cycle_volume()
                            return
                            
                        # Mode Buttons
                        btn_forest = pygame.Rect(40, 520, 200, 45)
                        btn_synth = pygame.Rect(260, 520, 200, 45)
                        btn_city = pygame.Rect(40, 580, 200, 45)
                        btn_winter = pygame.Rect(260, 580, 200, 45)
                        
                        if btn_forest.collidepoint(vmx, vmy):
                            self.mode = "normal"
                        elif btn_synth.collidepoint(vmx, vmy):
                            self.mode = "night"
                        elif btn_city.collidepoint(vmx, vmy):
                            self.mode = "city"
                        elif btn_winter.collidepoint(vmx, vmy):
                            self.mode = "winter"
                        else:
                            # click anywhere else triggers start
                            self.perform_action()
                            
                    elif self.state == "LOGIN":
                        # Confirm or Cancel buttons
                        btn_back = pygame.Rect(40, HEIGHT - 100, 160, 45)
                        btn_confirm = pygame.Rect(300, HEIGHT - 100, 160, 45)
                        if btn_back.collidepoint(vmx, vmy):
                            self.state = "START"
                        elif btn_confirm.collidepoint(vmx, vmy):
                            if self.login_input.strip():
                                self.username = self.login_input.strip()[:12]
                                save_username(self.username)
                                self.load_player_profile()
                            self.state = "START"
                    elif self.state == "GAMEOVER":
                        card_h = 245
                        card_y = HEIGHT // 2 - card_h // 2 - 40
                        btn_restart = pygame.Rect(60, card_y + card_h + 20, 180, 45)
                        btn_home = pygame.Rect(260, card_y + card_h + 20, 180, 45)
                        if btn_restart.collidepoint(vmx, vmy):
                            self.start_game()
                        elif btn_home.collidepoint(vmx, vmy):
                            self.state = "START"
                    else:
                        self.perform_action()

    def perform_action(self):
        if self.state == "START":
            self.start_game()
        elif self.state == "PLAYING":
            self.first_flap = True
            self.bird.jump(self.particles, self.mode)
        elif self.state == "GAMEOVER":
            self.start_game()

    def check_collisions(self):
        bird_circle = (self.bird.x, self.bird.y, self.bird.radius - 2)
        
        # 1. Check Powerup Collections
        for pu in self.powerups:
            if pu.active:
                dx = self.bird.x - pu.x
                dy = self.bird.y - pu.y
                dist_sq = dx*dx + dy*dy
                col_dist = (self.bird.radius + pu.radius - 1)
                if dist_sq < col_dist * col_dist:
                    pu.active = False
                    if powerup_pickup_sfx:
                        powerup_pickup_sfx.play()
                    
                    if pu.type == 'shield':
                        self.shield_active = True
                        self.score_popups.append({"x": int(pu.x), "y": int(pu.y - 15), "life": 40, "max_life": 40, "text": "+SHIELD", "color": (0, 200, 255)})
                    elif pu.type == 'slow':
                        self.slow_timer = 300  # 5 seconds at 60 FPS
                        self.score_popups.append({"x": int(pu.x), "y": int(pu.y - 15), "life": 40, "max_life": 40, "text": "SLOW-MO", "color": (120, 255, 120)})

        # Check Coin Collections
        for coin in self.coins:
            if coin.active:
                dx = self.bird.x - coin.x
                dy = self.bird.y - coin.y
                dist_sq = dx*dx + dy*dy
                col_dist = (self.bird.radius + coin.radius - 1)
                if dist_sq < col_dist * col_dist:
                    coin.active = False
                    self.session_coins += 1
                    if coin_pickup_sfx:
                        coin_pickup_sfx.play()
                    self.score_popups.append({
                        "x": int(coin.x),
                        "y": int(coin.y),
                        "life": 40,
                        "max_life": 40,
                        "text": "+1",
                        "color": (255, 215, 0)
                    })

        # 2. Check Immunity
        if self.immunity_timer > 0:
            return

        # 3. Ceiling & Ground
        if self.bird.y - self.bird.radius <= 0:
            if self.shield_active:
                self.break_shield()
                self.bird.vel = 1.0  # drop down gently
                self.bird.y = self.bird.radius + 5
            else:
                self.trigger_game_over()
            return
        if self.bird.y + self.bird.radius >= Y_GROUND:
            if self.shield_active:
                self.break_shield()
                self.bird.vel = -5.0  # bounce up
                self.bird.y = Y_GROUND - self.bird.radius - 5
            else:
                self.trigger_game_over()
            return
            
        # 4. Pipes
        for pipe in self.pipes:
            if self.rect_circle_collide(pipe.top_rect, bird_circle) or self.rect_circle_collide(pipe.bot_rect, bird_circle):
                if self.shield_active:
                    self.break_shield()
                else:
                    self.trigger_game_over()
                return
        
        # 5. Flying Obstacles
        for fo in self.flying_obstacles:
            if fo.active:
                fo_rect = fo.get_rect()
                if self.rect_circle_collide(fo_rect, bird_circle):
                    fo.active = False
                    if self.shield_active:
                        self.break_shield()
                    else:
                        self.trigger_game_over()
                    return

    def break_shield(self):
        self.shield_active = False
        self.immunity_timer = 60  # 1 second of absolute immunity
        self.shake_timer = 12
        if shield_break_sfx:
            shield_break_sfx.play()
            
        # Spawn glowing blue debris particles
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 5.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([(0, 150, 255), (0, 230, 255), (255, 255, 255)])
            size = random.uniform(2, 5)
            life = random.randint(15, 30)
            self.particles.append(Particle(self.bird.x, self.bird.y, vx, vy, color, size, life, 'circle'))
            
        # Alert text
        self.score_popups.append({"x": int(self.bird.x), "y": int(self.bird.y - 25), "life": 45, "max_life": 45, "text": "SHIELD BROKEN!", "color": (255, 100, 100)})

    def rect_circle_collide(self, rect, circle):
        cx, cy, r = circle
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top, min(cy, rect.bottom))
        dx = cx - closest_x
        dy = cy - closest_y
        return (dx*dx + dy*dy) < (r * r)

    def update(self):
        play_ambient(self.volume_level * 0.85, self.get_ambient_track())
        
        if self.shake_timer > 0:
            self.shake_timer -= 1
            
        # Update Day-Night Clock (Slowed down cycle using constants)
        if self.mode == "normal":
            self.sky_ticks = (self.sky_ticks + 1) % SKY_CYCLE_LEN
            # Phase transitions
            self.sky_phase = self.sky_ticks // SKY_PHASE_LEN
            self.tint_t = self.sky_phase
            
        # Update backgrounds
        if self.mode == "city":
            for b in self.buildings:
                b.update()
            for c in self.cars:
                c.update()
        else:
            self.mountains_back.update()
            self.mountains_front.update()
            self.cabin.update()
            for tree in self.trees:
                tree.update()
                
        # Snowfall / Weather updates
        if self.mode == "winter":
            for flake in self.snowflakes:
                flake.update()
        elif self.mode == "normal" and getattr(self, "is_raining", False):
            for drop in self.rain_particles:
                drop.update()
            # Lightning updates
            if getattr(self, "lightning_flash_timer", 0) > 0:
                self.lightning_flash_timer -= 1
            else:
                if random.random() < 0.0015:
                    self.lightning_flash_timer = 2
                
        if self.state == "START":
            self.is_raining = False
            self.rain_particles = []
            self.lightning_flash_timer = 0
            self.ground.update()
            self.bird.y = HEIGHT // 2 + math.sin(pygame.time.get_ticks() * 0.007) * 12
            self.bird.angle = math.sin(pygame.time.get_ticks() * 0.005) * 8.0
            
            # Smoke particles
            if self.mode != "city" and pygame.time.get_ticks() % 20 == 0:
                cx, cy = self.cabin.get_chimney_pos()
                self.particles.append(Particle(
                    cx, cy, 
                    0.5 + random.uniform(-0.1, 0.1), 
                    -0.8 - random.uniform(0.1, 0.3), 
                    (200, 200, 200, 90), 
                    random.uniform(3, 7), 
                    random.randint(60, 100)
                ))
                
        elif self.state == "PLAYING":
            # --- Difficulty Progression ---
            tier_name, tier_color, tier_speed, tier_gap = self.get_difficulty_tier()
            old_tier = self.current_tier
            if tier_name != old_tier:
                self.current_tier = tier_name
                # Trigger tier change popup
                self.tier_popup_timer = 90  # 1.5 seconds
                if tier_name == "MEDIUM":
                    self.tier_popup_text = "\u26a0 MEDIUM MODE!"
                elif tier_name == "HARD":
                    self.tier_popup_text = "\u26a0 HARD MODE!"
                elif tier_name == "INSANE":
                    self.tier_popup_text = "\ud83d\udd25 INSANE MODE!"
                self.tier_popup_color = tier_color
                self.shake_timer = 10
                # Switch ambient music to match new intensity
                play_ambient(self.volume_level * 0.85, self.get_ambient_track())
            
            speed_multiplier = 0.5 if self.slow_timer > 0 else 1.0
            scroll_speed = tier_speed * speed_multiplier
            self.ground.speed = scroll_speed
            
            # Decrement tier popup
            if self.tier_popup_timer > 0:
                self.tier_popup_timer -= 1
            
            if self.first_flap:
                if self.slow_timer > 0:
                    self.slow_timer -= 1
                if self.immunity_timer > 0:
                    self.immunity_timer -= 1
                    
                self.bird.update(speed_multiplier)
                
                # Emit speed trail based on skin
                if pygame.time.get_ticks() % 2 == 0:
                    tx = self.bird.x - 10
                    ty = self.bird.y + int(math.sin(pygame.time.get_ticks() * 0.05) * 4) # slight wiggle
                    
                    if self.equipped_skin == "classic":
                        self.particles.append(Particle(tx, ty, -2.5 * speed_multiplier, random.uniform(-0.3, 0.3) * speed_multiplier, (255, 255, 255, 90), random.uniform(3, 5), 18))
                    elif self.equipped_skin == "ninja":
                        self.particles.append(Particle(tx, ty, -2.2 * speed_multiplier, random.uniform(-0.5, 0.0) * speed_multiplier, (35, 35, 38, 140), random.uniform(4, 6), 22))
                    elif self.equipped_skin == "mech":
                        self.particles.append(Particle(tx, ty, -3.0 * speed_multiplier, random.uniform(-0.8, 0.8) * speed_multiplier, (0, 240, 255, 200), random.uniform(2, 3), 12, shape='square'))
                    elif self.equipped_skin == "phoenix":
                        fc = random.choice([(255, 100, 30, 200), (255, 200, 0, 200)])
                        self.particles.append(Particle(tx, ty, -2.0 * speed_multiplier, (-0.6 - random.uniform(0.0, 0.5)) * speed_multiplier, fc, random.uniform(3, 4.5), 15))
                
                # Pipes updates
                for pipe in self.pipes:
                    pipe.update(scroll_speed)
                    
                # Powerups updates
                for pu in self.powerups[:]:
                    pu.update(scroll_speed)
                    if pu.x + pu.radius * 2 < 0 or not pu.active:
                        self.powerups.remove(pu)
                        
                # Coins updates
                for coin in self.coins[:]:
                    coin.update(scroll_speed)
                    if coin.x + coin.radius * 2 < 0 or not coin.active:
                        self.coins.remove(coin)
                
                # Flying obstacles updates
                for fo in self.flying_obstacles[:]:
                    fo.update(speed_multiplier)
                    if fo.x + 30 < 0 or not fo.active:
                        self.flying_obstacles.remove(fo)
                    
                if self.pipes[0].x + self.pipes[0].width < 0:
                    self.pipes.pop(0)
                    last_x = self.pipes[-1].x
                    new_pipe = Pipe(last_x + 235, self.mode)
                    # Apply dynamic gap based on current difficulty
                    new_pipe.gap = tier_gap
                    new_pipe.gap_y = random.randint(180, Y_GROUND - 180)
                    new_pipe.top_rect = pygame.Rect(new_pipe.x, 0, new_pipe.width, new_pipe.gap_y - new_pipe.gap // 2)
                    new_pipe.bot_rect = pygame.Rect(new_pipe.x, new_pipe.gap_y + new_pipe.gap // 2, new_pipe.width, Y_GROUND - (new_pipe.gap_y + new_pipe.gap // 2))
                    self.pipes.append(new_pipe)
                    
                    # Spawn items for new pipe
                    self.spawn_items_for_pipe(new_pipe)
                    
                for pipe in self.pipes:
                    if not pipe.passed and self.bird.x > pipe.x + pipe.width // 2:
                        pipe.passed = True
                        self.score += 1
                        if point_sfx:
                            point_sfx.play()
                        # Spawn +1 score popup centered in the gap
                        self.score_popups.append({"x": pipe.x + pipe.width // 2, "y": pipe.gap_y, "life": 40, "max_life": 40})
                        
                        # Chance to spawn a flying obstacle (15% chance, only after score >= 5)
                        if self.score >= 5 and random.random() < 0.15:
                            fly_y = random.randint(120, Y_GROUND - 120)
                            fly_speed = tier_speed * 1.3
                            self.flying_obstacles.append(FlyingObstacle(WIDTH + 40, fly_y, self.mode, fly_speed))
                            
                self.check_collisions()
            else:
                # Hover the bird gently in ready state
                self.bird.y = HEIGHT // 2 + math.sin(pygame.time.get_ticks() * 0.007) * 12
                self.bird.angle = math.sin(pygame.time.get_ticks() * 0.005) * 8.0

            self.ground.update()
            
            # Smoke particles
            if self.mode != "city" and pygame.time.get_ticks() % 20 == 0:
                cx, cy = self.cabin.get_chimney_pos()
                self.particles.append(Particle(
                    cx, cy, 
                    (0.5 + random.uniform(-0.1, 0.1)) * speed_multiplier, 
                    (-0.8 - random.uniform(0.1, 0.3)) * speed_multiplier, 
                    (200, 200, 200, 90), 
                    random.uniform(3, 7), 
                    random.randint(60, 100)
                ))
            
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
                
        # Update floating score popups
        for popup in self.score_popups[:]:
            popup["y"] -= 0.8
            popup["life"] -= 1
            if popup["life"] <= 0:
                self.score_popups.remove(popup)

    def draw(self):
        # 1. Draw virtual screen
        draw_surf = pygame.Surface((WIDTH, HEIGHT))
        
        # Draw sky gradient based on mode/time
        if self.mode == "normal":
            # Select gradient map based on phase
            phase = self.sky_phase
            # LERP blending between gradient strips
            if phase == 0:
                draw_surf.blit(sky_cache["day"], (0, 0))
            elif phase == 1:
                # Fade Day to Sunset
                t = (self.sky_ticks % SKY_PHASE_LEN) / SKY_PHASE_LEN
                draw_surf.blit(sky_cache["day"], (0, 0))
                overlay = sky_cache["sunset"].copy()
                overlay.set_alpha(int(t * 255))
                draw_surf.blit(overlay, (0, 0))
            elif phase == 2:
                # Fade Sunset to Night
                t = (self.sky_ticks % SKY_PHASE_LEN) / SKY_PHASE_LEN
                draw_surf.blit(sky_cache["sunset"], (0, 0))
                overlay = sky_cache["night"].copy()
                overlay.set_alpha(int(t * 255))
                draw_surf.blit(overlay, (0, 0))
            else:
                # Fade Night to Sunrise to Day
                t = (self.sky_ticks % SKY_PHASE_LEN) / SKY_PHASE_LEN
                draw_surf.blit(sky_cache["night"], (0, 0))
                overlay = sky_cache["sunrise"].copy()
                overlay.set_alpha(int(t * 255))
                draw_surf.blit(overlay, (0, 0))
                
            # Overcast overlay if raining
            if getattr(self, "is_raining", False):
                storm_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                storm_overlay.fill((90, 100, 110, 140))
                draw_surf.blit(storm_overlay, (0, 0))
        else:
            # Static mode gradients
            if self.mode == "night":
                draw_surf.blit(sky_cache["synthwave"], (0, 0))
            elif self.mode == "city":
                draw_surf.blit(sky_cache["city"], (0, 0))
            elif self.mode == "winter":
                draw_surf.blit(sky_cache["winter"], (0, 0))
                
        # 2. Celestial Bodies (Sun / Moon / Stars)
        self.draw_celestial(draw_surf)
        
        # 3. Mode Background rendering
        if self.mode == "city":
            # Render city silhouettes
            for b in self.buildings:
                if b.layer == 0: b.draw(draw_surf)
            for b in self.buildings:
                if b.layer == 1: b.draw(draw_surf)
            # Render background cars
            for c in self.cars:
                c.draw(draw_surf)
        else:
            # Nature backgrounds
            is_rain = getattr(self, "is_raining", False)
            self.mountains_back.draw(draw_surf, self.mode, self.tint_t, is_rain)
            self.mountains_front.draw(draw_surf, self.mode, self.tint_t, is_rain)
            
            # Draw Lake behind cabin/trees
            if self.mode == "normal":
                self.draw_lake(draw_surf)
                
            self.cabin.draw(draw_surf, self.mode, self.tint_t, is_rain)
            for tree in self.trees:
                tree.draw(draw_surf, self.mode, self.tint_t, is_rain)
                
        # 4. Active snowfall / rainfall
        if self.mode == "winter":
            for flake in self.snowflakes:
                flake.draw(draw_surf)
        elif self.mode == "normal" and getattr(self, "is_raining", False):
            for drop in self.rain_particles:
                drop.draw(draw_surf)
                
        # 5. Pipes
        if self.state in ["PLAYING", "GAMEOVER"]:
            for pipe in self.pipes:
                pipe.draw(draw_surf)
            for pu in self.powerups:
                pu.draw(draw_surf)
            for coin in self.coins:
                coin.draw(draw_surf, self.mode)
            # Flying obstacles
            for fo in self.flying_obstacles:
                fo.draw(draw_surf)
                 
        # 6. Ground
        self.ground.draw(draw_surf, self.mode)
        
        # 7. Particles
        for p in self.particles:
            p.draw(draw_surf)
            

        # 8. Bird
        self.bird.draw(draw_surf, self.mode, self.equipped_skin)
        
        # Draw shield bubble overlay if active
        if self.shield_active:
            pulse = int(math.sin(pygame.time.get_ticks() * 0.015) * 3)
            pygame.draw.circle(draw_surf, (0, 230, 255), (int(self.bird.x), int(self.bird.y)), self.bird.radius + 6 + pulse, 2)
            pygame.draw.circle(draw_surf, (0, 150, 255), (int(self.bird.x), int(self.bird.y)), self.bird.radius + 9 + pulse, 1)
        
        # Draw floating score popups
        for popup in self.score_popups:
            alpha = int((popup["life"] / popup["max_life"]) * 255)
            text = popup.get("text", "+1")
            color = popup.get("color", (255, 230, 100))
            popup_surf = font_ui.render(text, True, color)
            popup_surf.set_alpha(alpha)
            draw_surf.blit(popup_surf, (popup["x"] - popup_surf.get_width() // 2, popup["y"] - popup_surf.get_height() // 2))
        
        # Draw slow-motion screen vignette overlay
        if self.slow_timer > 0:
            pygame.draw.rect(draw_surf, (120, 255, 120), (0, 0, WIDTH, HEIGHT), 6)
            pygame.draw.rect(draw_surf, (46, 125, 50), (6, 6, WIDTH - 12, HEIGHT - 12), 3)
            
        # 9. UI Screens
        if self.state == "START":
            self.draw_start_screen(draw_surf)
        elif self.state == "PLAYING":
            self.draw_hud(draw_surf)
            if not self.first_flap:
                pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.007))
                ready_c = (pulse, 255, pulse) if self.mode != "night" else (0, pulse, 255)
                ready_lbl = font_title.render("GET READY", True, ready_c)
                hint_lbl = font_ui.render("Press SPACE or Tap to Flap", True, (230, 230, 230))
                draw_surf.blit(ready_lbl, (WIDTH // 2 - ready_lbl.get_width() // 2, HEIGHT // 3))
                draw_surf.blit(hint_lbl, (WIDTH // 2 - hint_lbl.get_width() // 2, HEIGHT // 3 + 60))
        elif self.state == "GAMEOVER":
            self.draw_gameover_screen(draw_surf)
        elif self.state == "LOGIN":
            self.draw_login_screen(draw_surf)
            
        # Apply lightning flash
        if getattr(self, "lightning_flash_timer", 0) > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT))
            flash_surf.fill((255, 255, 255))
            if self.lightning_flash_timer == 1:
                flash_surf.set_alpha(180)
            draw_surf.blit(flash_surf, (0, 0))
            
        # 10. Letterbox Scale virtual screen onto actual window resizes
        scale = min(window_w / WIDTH, window_h / HEIGHT)
        scaled_w = int(WIDTH * scale)
        scaled_h = int(HEIGHT * scale)
        dx = (window_w - scaled_w) // 2
        dy = (window_h - scaled_h) // 2
        
        # Apply screenshake
        shake_x = dx
        shake_y = dy
        if self.shake_timer > 0:
            shake_x += random.randint(-4, 4)
            shake_y += random.randint(-4, 4)
            
        scaled_surf = pygame.transform.smoothscale(draw_surf, (scaled_w, scaled_h))
        
        screen.fill((0, 0, 0))
        screen.blit(scaled_surf, (shake_x, shake_y))
        pygame.display.flip()

    def draw_celestial(self, surface):
        if self.mode == "night":
            # 1. Synthwave Grid Sun
            # Draw big glowing magenta/orange sun at horizon
            sun_x, sun_y, r = 250, 420, 75
            
            # Sun glow
            g_surf = pygame.Surface((r*3, r*3), pygame.SRCALPHA)
            pygame.draw.circle(g_surf, (255, 0, 180, 45), (int(r*1.5), int(r*1.5)), int(r*1.2))
            pygame.draw.circle(g_surf, (255, 100, 0, 90), (int(r*1.5), int(r*1.5)), r)
            surface.blit(g_surf, (int(sun_x - r*1.5), int(sun_y - r*1.5)))
            
            # Main sun core
            pygame.draw.circle(surface, (255, 160, 0), (sun_x, sun_y), r)
            
            # Overlay horizontal black lines (retro scanlines)
            for sy in range(sun_y - r, sun_y + r, 8):
                # thicker line gaps at bottom
                th = int(2 + (sy - (sun_y - r)) / 15)
                pygame.draw.rect(surface, (15, 10, 28), (sun_x - r - 5, sy, r*2 + 10, th))
                
        elif self.mode == "city":
            # Big golden sunset sun sinking behind towers
            pygame.draw.circle(surface, (255, 235, 130), (120, 400), 50)
            
        elif self.mode == "winter":
            # Soft pale white winter sun
            pygame.draw.circle(surface, (235, 240, 245), (380, 150), 30)
            
        elif self.mode == "normal":
            # Dynamic Sun/Moon orbiting coordinates
            # Angle moves based on clock ticks
            angle_rad = (self.sky_ticks / SKY_CYCLE_LEN) * 2 * math.pi - math.pi / 2
            # Center of orbit is around Y_GROUND
            cx = WIDTH // 2
            cy = Y_GROUND
            orbit_rx = 220
            orbit_ry = 320
            
            x = int(cx + orbit_rx * math.cos(angle_rad))
            y = int(cy + orbit_ry * math.sin(angle_rad))
            
            if y < Y_GROUND + 100:
                if self.sky_phase in [0, 1, 3]: # Day/Sunset/Sunrise shows sun
                    # Draw Sun with dynamic color (yellow to deep orange-red)
                    sun_c = (255, 220, 100)
                    if self.sky_phase == 1:
                        sun_c = lerp_color((255, 220, 100), (240, 80, 50), (self.sky_ticks % SKY_PHASE_LEN)/SKY_PHASE_LEN)
                    elif self.sky_phase == 3:
                        sun_c = lerp_color((220, 60, 40), (255, 220, 100), (self.sky_ticks % SKY_PHASE_LEN)/SKY_PHASE_LEN)
                        
                    # Sun core
                    pygame.draw.circle(surface, sun_c, (x, y), 24)
                    # Corona glow
                    c_surf = pygame.Surface((70, 70), pygame.SRCALPHA)
                    pygame.draw.circle(c_surf, list(sun_c) + [40], (35, 35), 32)
                    pygame.draw.circle(c_surf, list(sun_c) + [80], (35, 35), 24)
                    surface.blit(c_surf, (x - 35, y - 35))
                else: # Night shows crescent moon
                    # Draw Moon
                    pygame.draw.circle(surface, (230, 240, 255), (x, y), 18)
                    # Mask crescent
                    pygame.draw.circle(surface, (10, 10, 25), (x - 8, y), 18)
                    
            # Twinkling stars at night
            # Fade stars in during sunset (phase 1) and out during sunrise (phase 3)
            star_alpha = 0
            if self.sky_phase == 2:
                star_alpha = 200
            elif self.sky_phase == 1:
                star_alpha = int(((self.sky_ticks % SKY_PHASE_LEN) / SKY_PHASE_LEN) * 200)
            elif self.sky_phase == 3:
                star_alpha = int((1 - (self.sky_ticks % SKY_PHASE_LEN) / SKY_PHASE_LEN) * 200)
                
            if star_alpha > 0:
                random.seed(42) # Deterministic stars
                for _ in range(35):
                    sx = random.randint(5, WIDTH - 5)
                    sy = random.randint(5, Y_GROUND - 80)
                    # Twinkle sizing
                    twinkle = math.sin(pygame.time.get_ticks() * 0.005 + sx) * 1.5 + 2.0
                    
                    s_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                    pygame.draw.circle(s_surf, (255, 255, 255, star_alpha), (3, 3), max(1, int(twinkle)))
                    surface.blit(s_surf, (sx - 3, sy - 3))

    def draw_lake(self, surface):
        # Position river touching the ground (618 to 650)
        river_y = Y_GROUND - 32
        river_h = 32
        
        is_rain = getattr(self, "is_raining", False)
        
        # Determine colors (darkened/stormy if raining)
        if is_rain:
            water_top = (18, 45, 60)
            water_bot = (30, 68, 85)
            bank_soil = (50, 40, 35)
            bank_grass = (40, 65, 50)
            ripple_c = (55, 110, 130)
        else:
            water_top = (25, 75, 105)
            water_bot = (45, 120, 155)
            bank_soil = (90, 65, 45)
            bank_grass = (50, 115, 65)
            ripple_c = (80, 180, 210)

        # Draw water body gradient (2 horizontal bands for retro 16-bit look)
        pygame.draw.rect(surface, water_top, (0, river_y, WIDTH, river_h // 2))
        pygame.draw.rect(surface, water_bot, (0, river_y + river_h // 2, WIDTH, river_h // 2))
        
        # Draw far-side riverbank (top edge)
        # Soil layer (2px)
        pygame.draw.rect(surface, bank_soil, (0, river_y - 2, WIDTH, 2))
        # Grass layer (2px)
        pygame.draw.rect(surface, bank_grass, (0, river_y - 4, WIDTH, 2))
        
        # Draw dynamic shimmery ripples
        ticks = pygame.time.get_ticks()
        for row in range(3):
            y_pos = river_y + 4 + row * 9
            speed = 0.04 * (row + 1)
            spacing = 110
            offset = (ticks * speed) % spacing
            
            for x in range(-spacing, WIDTH + spacing, spacing):
                rx = x - offset
                rw = 30 + 15 * math.sin(ticks * 0.003 + row * 1.5)
                pygame.draw.line(surface, ripple_c, (rx, y_pos), (rx + rw, y_pos), 2)

    def draw_start_screen(self, surface):
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 15, 25, 90))
        surface.blit(overlay, (0, 0))
        
        # Get theme color
        theme_color = (46, 125, 50)
        if self.mode == "night":
            theme_color = (255, 0, 180)
        elif self.mode == "city":
            theme_color = (220, 95, 80)
        elif self.mode == "winter":
            theme_color = (140, 175, 205)

        # Profile Top Bar
        pygame.draw.rect(surface, (30, 30, 45, 200), (15, 15, 160, 35), 0, 6)
        pygame.draw.rect(surface, theme_color, (15, 15, 160, 35), 1, 6)
        name_lbl = font_bold_small.render(self.username, True, (255, 255, 255))
        change_lbl = font_small.render("Change Profile", True, theme_color)
        surface.blit(name_lbl, (25, 22))
        surface.blit(change_lbl, (185, 23))
        
        # About Button (top-right)
        about_btn = pygame.Rect(WIDTH - 115, 15, 100, 35)
        pygame.draw.rect(surface, (30, 30, 45, 200), about_btn, 0, 6)
        pygame.draw.rect(surface, theme_color, about_btn, 1, 6)
        about_lbl = font_bold_small.render("About", True, (255, 255, 255))
        surface.blit(about_lbl, (about_btn.centerx - about_lbl.get_width() // 2, about_btn.centery - about_lbl.get_height() // 2))
        
        # Title Card
        title_text = "FOREST FLAPPER"
        glow_c = (46, 125, 50)
        
        if self.mode == "night":
            title_text = "NEON ARCADE"
            glow_c = (255, 0, 180)
        elif self.mode == "city":
            title_text = "METRO FLAPPER"
            glow_c = (230, 90, 40)
        elif self.mode == "winter":
            title_text = "WINTER FLAPPER"
            glow_c = (140, 175, 205)
            
        glow_surf = font_title.render(title_text, True, glow_c)
        main_surf = font_title.render(title_text, True, (255, 255, 255))
        tx = WIDTH // 2 - main_surf.get_width() // 2
        ty = HEIGHT // 4 - 35
        
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)]:
            surface.blit(glow_surf, (tx + dx, ty + dy))
        surface.blit(main_surf, (tx, ty))
        
        # Pulsing Start Text
        pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.007))
        pulse_c = (pulse, 255, pulse) if self.mode != "night" else (0, pulse, 255)
        inst_surf = font_ui.render("Press SPACE or CLICK to Fly", True, pulse_c)
        surface.blit(inst_surf, (WIDTH // 2 - inst_surf.get_width() // 2, HEIGHT // 2 - 20))
        
        # High score display
        hs_surf = font_ui.render(f"Your Best: {self.high_score}", True, (255, 230, 100))
        surface.blit(hs_surf, (WIDTH // 2 - hs_surf.get_width() // 2, HEIGHT // 2 + 25))
        
        # Lifetime coins display
        coins_surf = font_ui.render(f"Coins: {self.profile['coins']}", True, (255, 215, 0))
        surface.blit(coins_surf, (WIDTH // 2 - coins_surf.get_width() // 2, HEIGHT // 2 + 65))
        
        # Mode Selection Header
        mode_hdr = font_bold_small.render("--- SELECT ARCADE MODE ---", True, (230, 230, 230))
        surface.blit(mode_hdr, (WIDTH // 2 - mode_hdr.get_width() // 2, 480))
        
        # 4 Mode buttons
        btn_forest = pygame.Rect(40, 520, 200, 45)
        btn_synth = pygame.Rect(260, 520, 200, 45)
        btn_city = pygame.Rect(40, 580, 200, 45)
        btn_winter = pygame.Rect(260, 580, 200, 45)
        
        self.draw_button(surface, btn_forest, "Forest (Day-Night)", self.mode == "normal", (46, 125, 50))
        self.draw_button(surface, btn_synth, "Synthwave Night", self.mode == "night", (255, 0, 180))
        self.draw_button(surface, btn_city, "City Metropolis", self.mode == "city", (220, 95, 80))
        self.draw_button(surface, btn_winter, "Winter Snow", self.mode == "winter", (140, 175, 205))
        
        # Leaderboard & Volume buttons side-by-side
        lead_btn = pygame.Rect(32, 645, 135, 40)
        skins_btn = pygame.Rect(182, 645, 135, 40)
        vol_btn = pygame.Rect(332, 645, 135, 40)
        
        self.draw_button(surface, lead_btn, "Trophies", False, (100, 210, 100))
        self.draw_button(surface, skins_btn, "Skins", False, (100, 210, 100))
        
        # Dynamic volume button text
        vol_text = "Vol: 50%"
        if self.volume_level == 0.0:
            vol_text = "Muted"
        elif self.volume_level == 0.2:
            vol_text = "Vol: 20%"
        elif self.volume_level == 1.0:
            vol_text = "Vol: 100%"
        self.draw_button(surface, vol_btn, vol_text, False, (100, 210, 100))
        
        # Show Leaderboard Modal if active
        if self.show_leaderboard:
            self.draw_leaderboard_modal(surface)
            
        # Show Skins Modal if active
        if self.show_skins_shop:
            self.draw_skins_modal(surface)

        # Show About Modal if active
        if self.show_about:
            self.draw_about_modal(surface)

    def draw_button(self, surface, rect, text, is_active, color):
        # Glow active button
        bg_color = (25, 25, 35, 220)
        border_color = (80, 80, 90)
        text_color = (200, 200, 200)
        
        if is_active:
            border_color = color
            text_color = color
            
        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, bg_color, (0, 0, rect.width, rect.height), 0, 8)
        pygame.draw.rect(btn_surf, border_color, (0, 0, rect.width, rect.height), 2, 8)
        
        surface.blit(btn_surf, rect.topleft)
        
        lbl = font_ui.render(text, True, text_color)
        surface.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

    def draw_leaderboard_modal(self, surface):
        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 220))
        surface.blit(overlay, (0, 0))
        
        card_w = 360
        card_h = 320
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2 - 30
        
        pygame.draw.rect(surface, (100, 210, 100), (card_x - 3, card_y - 3, card_w + 6, card_h + 6), 0, 12)
        pygame.draw.rect(surface, (20, 20, 30), (card_x, card_y, card_w, card_h), 0, 10)
        
        title = font_title.render("LEADERBOARD", True, (100, 210, 100))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, card_y + 15))
        
        # Print rankings
        for idx, entry in enumerate(self.leaderboard):
            ry = card_y + 75 + idx * 32
            rank_str = f"{idx + 1}."
            name_str = entry["name"]
            score_str = str(entry["score"])
            
            # Gold, Silver, Bronze color indicators
            lbl_c = (235, 235, 235)
            if idx == 0: lbl_c = (255, 215, 0)
            elif idx == 1: lbl_c = (200, 200, 200)
            elif idx == 2: lbl_c = (205, 127, 50)
            
            r_lbl = font_bold_small.render(rank_str, True, lbl_c)
            n_lbl = font_bold_small.render(name_str, True, lbl_c)
            s_lbl = font_bold_small.render(score_str, True, lbl_c)
            
            surface.blit(r_lbl, (card_x + 30, ry))
            surface.blit(n_lbl, (card_x + 70, ry))
            surface.blit(s_lbl, (card_x + card_w - 70, ry))
            
        # Close Button
        close_btn = pygame.Rect(WIDTH // 2 - 60, card_y + card_h - 45, 120, 32)
        pygame.draw.rect(surface, (100, 210, 100), close_btn, 0, 6)
        c_lbl = font_bold_small.render("Close", True, (20, 20, 30))
        surface.blit(c_lbl, (close_btn.centerx - c_lbl.get_width() // 2, close_btn.centery - c_lbl.get_height() // 2))

    def draw_about_modal(self, surface):
        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 220))
        surface.blit(overlay, (0, 0))
        
        card_w = 360
        card_h = 320
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2 - 30
        
        # Get theme color
        theme_color = (46, 125, 50)
        if self.mode == "night":
            theme_color = (255, 0, 180)
        elif self.mode == "city":
            theme_color = (220, 95, 80)
        elif self.mode == "winter":
            theme_color = (140, 175, 205)
            
        pygame.draw.rect(surface, theme_color, (card_x - 3, card_y - 3, card_w + 6, card_h + 6), 0, 12)
        pygame.draw.rect(surface, (20, 20, 30), (card_x, card_y, card_w, card_h), 0, 10)
        
        title = font_title.render("ABOUT GAME", True, theme_color)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, card_y + 15))
        
        # Info lines inside the modal
        # 1. Developer
        dev_lbl = font_bold_small.render("DEVELOPER:", True, (150, 150, 160))
        dev_val = font_ui.render("SAISARAN", True, (255, 215, 0)) # Bold, beautiful gold
        
        # 2. Engine
        eng_lbl = font_bold_small.render("BUILT WITH:", True, (150, 150, 160))
        eng_val = font_bold_small.render("Pygame + WebAssembly", True, (255, 255, 255))
        
        # 3. Version
        ver_lbl = font_bold_small.render("VERSION:", True, (150, 150, 160))
        ver_val = font_bold_small.render("v1.2.0 (Stable)", True, (255, 255, 255))
        
        # 4. Platform
        plat_lbl = font_bold_small.render("PLATFORM:", True, (150, 150, 160))
        plat_val = font_bold_small.render("Web & Mobile (Android)", True, (255, 255, 255))

        # Blit them nicely spaced
        start_y = card_y + 75
        spacing = 42
        
        # Line 1: Developer
        surface.blit(dev_lbl, (card_x + 30, start_y))
        surface.blit(dev_val, (card_x + 150, start_y - 4)) # Adjust slightly for larger font size
        
        # Line 2: Engine
        surface.blit(eng_lbl, (card_x + 30, start_y + spacing))
        surface.blit(eng_val, (card_x + 150, start_y + spacing))
        
        # Line 3: Version
        surface.blit(ver_lbl, (card_x + 30, start_y + spacing * 2))
        surface.blit(ver_val, (card_x + 150, start_y + spacing * 2))
        
        # Line 4: Platform
        surface.blit(plat_lbl, (card_x + 30, start_y + spacing * 3))
        surface.blit(plat_val, (card_x + 150, start_y + spacing * 3))
        
        # Close Button
        close_btn = pygame.Rect(WIDTH // 2 - 60, card_y + card_h - 45, 120, 32)
        pygame.draw.rect(surface, theme_color, close_btn, 0, 6)
        c_lbl = font_bold_small.render("Close", True, (20, 20, 30))
        surface.blit(c_lbl, (close_btn.centerx - c_lbl.get_width() // 2, close_btn.centery - c_lbl.get_height() // 2))

    def draw_skins_modal(self, surface):
        card_w = 380
        card_h = 360
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2 - 20
        
        # Outer border
        theme_color = (100, 210, 100)
        pygame.draw.rect(surface, theme_color, (card_x - 3, card_y - 3, card_w + 6, card_h + 6), 0, 12)
        pygame.draw.rect(surface, (20, 20, 30), (card_x, card_y, card_w, card_h), 0, 10)
        
        title = font_title.render("SKINS SHOP", True, theme_color)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, card_y + 12))
        
        # Display lifetime coins
        coins_txt = font_bold_small.render(f"Your Coins: {self.profile['coins']}", True, (255, 215, 0))
        surface.blit(coins_txt, (WIDTH // 2 - coins_txt.get_width() // 2, card_y + 44))
        
        for i, skin_name in enumerate(["classic", "ninja", "mech", "phoenix"]):
            row_y = card_y + 70 + i * 62
            
            # Row container
            pygame.draw.rect(surface, (30, 30, 45), (card_x + 15, row_y, card_w - 30, 52), 0, 6)
            
            # Draw preview bird
            bx = card_x + 40
            by = row_y + 26
            br = 12
            
            if skin_name == "classic":
                pygame.draw.circle(surface, (255, 204, 0), (bx, by), br)
                pygame.draw.circle(surface, (255, 255, 255), (bx + 4, by - 4), 3)
                pygame.draw.circle(surface, (0, 0, 0), (bx + 5, by - 4), 1)
                pygame.draw.polygon(surface, (255, 102, 0), [(bx + 9, by - 2), (bx + 15, by), (bx + 9, by + 4)])
            elif skin_name == "ninja":
                pygame.draw.circle(surface, (45, 45, 52), (bx, by), br)
                pygame.draw.rect(surface, (180, 30, 30), (bx - 10, by - 7, 20, 3))
                pygame.draw.circle(surface, (255, 255, 255), (bx + 4, by - 3), 3)
                pygame.draw.circle(surface, (0, 0, 0), (bx + 5, by - 3), 1)
                pygame.draw.polygon(surface, (230, 90, 20), [(bx + 9, by - 2), (bx + 15, by), (bx + 9, by + 4)])
            elif skin_name == "mech":
                pygame.draw.circle(surface, (130, 135, 145), (bx, by), br)
                pygame.draw.rect(surface, (0, 240, 255), (bx + 2, by - 5, 6, 3), 0, 1)
            elif skin_name == "phoenix":
                pygame.draw.circle(surface, (220, 45, 30), (bx, by), br)
                pygame.draw.polygon(surface, (255, 120, 0), [(bx - 5, by - 10), (bx - 12, by - 18), (bx - 2, by - 11)])
                pygame.draw.circle(surface, (255, 255, 255), (bx + 4, by - 3), 3)
                pygame.draw.circle(surface, (0, 0, 0), (bx + 5, by - 3), 1)
                pygame.draw.polygon(surface, (255, 220, 0), [(bx + 9, by - 2), (bx + 15, by), (bx + 9, by + 4)])
                
            pygame.draw.circle(surface, (20, 20, 20), (bx, by), br, 1)
            
            # Names
            names = {"classic": "Classic Yellow", "ninja": "Midnight Ninja", "mech": "Cyber-Mech", "phoenix": "Cosmic Phoenix"}
            name_surf = font_bold_small.render(names[skin_name], True, (255, 255, 255))
            surface.blit(name_surf, (card_x + 65, row_y + 10))
            
            # Status / Unlock
            unlocked = False
            high_score_met = False
            req_txt = ""
            cost = 0
            if skin_name == "classic":
                unlocked = True
            elif skin_name == "ninja":
                high_score_met = self.high_score >= 5
                req_txt = "Unlock: Score 5+"
                cost = 25
            elif skin_name == "mech":
                high_score_met = self.high_score >= 12
                req_txt = "Unlock: Score 12+"
                cost = 75
            elif skin_name == "phoenix":
                high_score_met = self.high_score >= 20
                req_txt = "Unlock: Score 20+"
                cost = 150
                
            if high_score_met and skin_name not in self.profile["unlocked_skins"]:
                self.profile["unlocked_skins"].append(skin_name)
                save_profile_data(self.username, self.profile)
                
            unlocked = skin_name in self.profile["unlocked_skins"]
                
            if unlocked:
                if skin_name == self.equipped_skin:
                    status_surf = font_bold_small.render("Equipped", True, (100, 210, 100))
                    surface.blit(status_surf, (card_x + card_w - 95, row_y + 16))
                else:
                    eb_rect = pygame.Rect(card_x + card_w - 95, row_y + 12, 80, 28)
                    pygame.draw.rect(surface, (100, 210, 100), eb_rect, 0, 6)
                    eb_lbl = font_small.render("Equip", True, (20, 20, 30))
                    surface.blit(eb_lbl, (eb_rect.centerx - eb_lbl.get_width() // 2, eb_rect.centery - eb_lbl.get_height() // 2))
            else:
                req_surf = font_small.render(req_txt, True, (220, 90, 90))
                surface.blit(req_surf, (card_x + 65, row_y + 30))
                
                # Buy button
                btn_rect = pygame.Rect(card_x + card_w - 95, row_y + 12, 80, 28)
                if self.profile["coins"] >= cost:
                    pygame.draw.rect(surface, (46, 125, 50), btn_rect, 0, 6)
                    buy_lbl = font_small.render(f"Buy {cost}", True, (255, 255, 255))
                    surface.blit(buy_lbl, (btn_rect.centerx - buy_lbl.get_width() // 2, btn_rect.centery - buy_lbl.get_height() // 2))
                else:
                    pygame.draw.rect(surface, (60, 60, 65), btn_rect, 0, 6)
                    lock_lbl = font_small.render(f"{cost} C", True, (170, 170, 170))
                    surface.blit(lock_lbl, (btn_rect.centerx - lock_lbl.get_width() // 2, btn_rect.centery - lock_lbl.get_height() // 2))
                
        # Close button
        close_btn = pygame.Rect(WIDTH // 2 - 60, card_y + card_h - 45, 120, 32)
        pygame.draw.rect(surface, (100, 210, 100), close_btn, 0, 6)
        c_lbl = font_bold_small.render("Close", True, (20, 20, 30))
        surface.blit(c_lbl, (close_btn.centerx - c_lbl.get_width() // 2, close_btn.centery - c_lbl.get_height() // 2))

    def draw_login_screen(self, surface):
        # Background
        surface.blit(sky_cache["synthwave"], (0, 0))
        
        # Card container
        card_w = 400
        card_h = 280
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2 - 50
        
        pygame.draw.rect(surface, (100, 210, 100), (card_x - 2, card_y - 2, card_w + 4, card_h + 4), 0, 10)
        pygame.draw.rect(surface, (25, 25, 35), (card_x, card_y, card_w, card_h), 0, 8)
        
        title = font_title.render("EDIT PROFILE", True, (255, 255, 255))
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, card_y + 20))
        
        instr = font_small.render("Enter your arcade pilot username:", True, (180, 180, 180))
        surface.blit(instr, (WIDTH // 2 - instr.get_width() // 2, card_y + 80))
        
        # Interactive Textbox
        box = pygame.Rect(WIDTH // 2 - 150, card_y + 115, 300, 48)
        pygame.draw.rect(surface, (15, 15, 20), box, 0, 6)
        pygame.draw.rect(surface, (100, 210, 100), box, 2, 6)
        
        # Text alignment
        cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
        disp_text = self.login_input + cursor
        
        text_surf = font_ui.render(disp_text, True, (255, 255, 255))
        surface.blit(text_surf, (box.x + 15, box.centery - text_surf.get_height() // 2))
        
        limit_lbl = font_small.render("Limit: 12 alphanumeric characters", True, (130, 130, 130))
        surface.blit(limit_lbl, (WIDTH // 2 - limit_lbl.get_width() // 2, card_y + 175))
        
        # Back & Confirm buttons
        btn_back = pygame.Rect(40, HEIGHT - 100, 160, 45)
        btn_confirm = pygame.Rect(300, HEIGHT - 100, 160, 45)
        
        self.draw_button(surface, btn_back, "Cancel", False, (220, 70, 70))
        self.draw_button(surface, btn_confirm, "Save Name", True, (100, 210, 100))

    def draw_hud(self, surface):
        score_str = str(self.score)
        shadow_surf = font_score.render(score_str, True, (0, 0, 0))
        main_surf = font_score.render(score_str, True, (255, 255, 255))
        sx = WIDTH // 2 - main_surf.get_width() // 2
        sy = 45
        surface.blit(shadow_surf, (sx + 3, sy + 3))
        surface.blit(main_surf, (sx, sy))
        
        # Difficulty Tier Badge (pill shape below score)
        tier_name, tier_color, _, _ = self.get_difficulty_tier()
        if tier_name == "INSANE":
            # Pulsing color for INSANE
            pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.012))
            tier_color = (255, pulse // 3, pulse // 5)
        tier_surf = font_small.render(tier_name, True, (0, 0, 0))
        tw = tier_surf.get_width() + 16
        th = tier_surf.get_height() + 6
        tier_x = WIDTH // 2 - tw // 2
        tier_y = sy + main_surf.get_height() + 2
        # Pill background
        pill_rect = pygame.Rect(tier_x, tier_y, tw, th)
        pygame.draw.rect(surface, tier_color, pill_rect, 0, 8)
        pygame.draw.rect(surface, (0, 0, 0), pill_rect, 1, 8)
        surface.blit(tier_surf, (tier_x + 8, tier_y + 3))
        
        # Tier Change Popup Banner (centered, fades out)
        if self.tier_popup_timer > 0:
            popup_alpha = int((self.tier_popup_timer / 90) * 255)
            popup_text_surf = font_title.render(self.tier_popup_text, True, self.tier_popup_color)
            popup_text_surf.set_alpha(popup_alpha)
            # Background bar
            bar_w = popup_text_surf.get_width() + 40
            bar_h = popup_text_surf.get_height() + 16
            bar_x = WIDTH // 2 - bar_w // 2
            bar_y = HEIGHT // 3 - bar_h // 2
            bar_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
            bar_surf.fill((0, 0, 0, min(180, popup_alpha)))
            pygame.draw.rect(bar_surf, (*self.tier_popup_color, min(200, popup_alpha)), (0, 0, bar_w, bar_h), 3, 6)
            surface.blit(bar_surf, (bar_x, bar_y))
            surface.blit(popup_text_surf, (WIDTH // 2 - popup_text_surf.get_width() // 2, bar_y + 8))
        
        # Current active pilot HUD display
        pilot_surf = font_small.render(f"Pilot: {self.username}", True, (230, 230, 230))
        surface.blit(pilot_surf, (15, 15))
        
        # Draw session coins display on top right
        coin_x = WIDTH - 80
        coin_y = 15
        pygame.draw.ellipse(surface, (255, 215, 0), (coin_x, coin_y + 2, 16, 16))
        pygame.draw.ellipse(surface, (212, 175, 55), (coin_x, coin_y + 2, 16, 16), 1)
        coin_lbl = font_bold_small.render(f"x {self.session_coins}", True, (255, 215, 0))
        surface.blit(coin_lbl, (coin_x + 22, coin_y + 1))

    def draw_gameover_screen(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 10, 20, 170))
        surface.blit(overlay, (0, 0))
        
        card_w = 340
        card_h = 245
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2 - 40
        
        # Dynamic color highlights
        theme_c = (220, 60, 60)
        if self.mode == "night": theme_c = (0, 255, 255)
        elif self.mode == "winter": theme_c = (140, 175, 205)
        
        pygame.draw.rect(surface, theme_c, (card_x - 3, card_y - 3, card_w + 6, card_h + 6), 0, 12)
        pygame.draw.rect(surface, (20, 15, 25), (card_x, card_y, card_w, card_h), 0, 10)
        
        go_surf = font_title.render("GAME OVER", True, (220, 60, 60))
        surface.blit(go_surf, (WIDTH // 2 - go_surf.get_width() // 2, card_y + 15))
        
        score_label = font_ui.render(f"Score: {self.score}", True, (255, 255, 255))
        surface.blit(score_label, (WIDTH // 2 - score_label.get_width() // 2, card_y + 80))
        
        hs_label = font_ui.render(f"Your Best: {self.high_score}", True, (240, 220, 100))
        surface.blit(hs_label, (WIDTH // 2 - hs_label.get_width() // 2, card_y + 125))
        
        # New best indicator!
        if self.is_new_high_score:
            pulse = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.015))
            best_color = (255, pulse, 0)
            best_surf = font_ui.render("NEW HIGH SCORE!", True, best_color)
            surface.blit(best_surf, (WIDTH // 2 - best_surf.get_width() // 2, card_y + 170))
            
        # Draw Play Again and Main Menu buttons below the card
        btn_restart = pygame.Rect(60, card_y + card_h + 20, 180, 45)
        btn_home = pygame.Rect(260, card_y + card_h + 20, 180, 45)
        
        self.draw_button(surface, btn_restart, "Play Again", True, theme_c)
        self.draw_button(surface, btn_home, "Main Menu", False, theme_c)
        
        # Keyboard shortcut tip
        helper_surf = font_small.render("Keyboard: Press SPACE to Play Again", True, (160, 160, 160))
        surface.blit(helper_surf, (WIDTH // 2 - helper_surf.get_width() // 2, card_y + card_h + 80))

async def main():
    if sys.platform == "emscripten":
        import platform
        try:
            platform.window.eval("""
                // 1. Inject styling to force canvas to fill the viewport
                var style = document.createElement('style');
                style.innerHTML = `
                    html, body {
                        margin: 0 !important;
                        padding: 0 !important;
                        width: 100% !important;
                        height: 100% !important;
                        overflow: hidden !important;
                        background-color: #0b0c10 !important;
                        display: flex !important;
                        align-items: center !important;
                        justify-content: center !important;
                    }
                    #canvas {
                        width: 100vw !important;
                        height: 100vh !important;
                        display: block !important;
                        image-rendering: auto !important;
                    }
                `;
                document.head.appendChild(style);

                // 2. High-DPI Auto-Resizer for SDL2 Canvas
                function syncCanvasSize() {
                    var canvas = document.getElementById('canvas');
                    if (canvas) {
                        var rect = canvas.getBoundingClientRect();
                        var dpr = Math.min(window.devicePixelRatio || 1, 2);
                        var targetW = Math.floor(rect.width * dpr);
                        var targetH = Math.floor(rect.height * dpr);
                        if (canvas.width !== targetW || canvas.height !== targetH) {
                            canvas.width = targetW;
                            canvas.height = targetH;
                            // Dispatch a window resize event to force Pygame/SDL2 to detect it
                            window.dispatchEvent(new Event('resize'));
                        }
                    }
                }

                // Run periodically to catch size shifts and orientation changes
                setInterval(syncCanvasSize, 300);
                window.addEventListener('resize', syncCanvasSize);
                syncCanvasSize();
            """)
        except Exception as e:
            print("Failed to inject fullscreen style:", e)

    game = Game()
    play_ambient(game.volume_level * 0.85, game.get_ambient_track())
    
    while True:
        game.handle_events()
        game.update()
        game.draw()
        clock.tick(FPS)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
