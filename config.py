# config.py

import pygame
import math

# --- KONSTANTA LAYAR ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60

# --- KONSTANTA ORB & CAT ---
ORB_RADIUS = 22 # Ukuran Orb diperbesar
ORB_GAP = 5     # Jarak antar orb
CAT_BASE_SIZE = (100, 100) # Ukuran dasar kucing
CAT_FINAL_SIZE = (120, 120) # Ukuran akhir kucing
HOLE_SIZE = 150 # Ukuran lubang diperbesar

# Posisi Kucing dan Lubang
CAT_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) 
HOLE_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# --- WARNA ORB (RGB) ---
ORB_COLORS_RGB = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0)
}
AVAILABLE_ORB_COLORS = ["red", "green", "blue", "yellow", "purple", "orange"] # Urutan sesuai prioritas atau preferensi

# --- PENGATURAN KESULITAN ---
DIFFICULTY_SETTINGS = {
    'easy': {
        'initial_orbs': 20,
        'num_orb_colors': 3,
        'speed_multiplier': 0.5,
        'cat_image_modifier': 1.0, 
        'bg_music': 'assets/background_music_easy.ogg' # Sesuaikan dengan file Anda
    },
    'medium': {
        'initial_orbs': 30,
        'num_orb_colors': 4,
        'speed_multiplier': 0.7,
        'cat_image_modifier': 1.0,
        'bg_music': 'assets/background_music_medium.ogg' # Sesuaikan dengan file Anda
    },
    'hard': {
        'initial_orbs': 40,
        'num_orb_colors': 5,
        'speed_multiplier': 1.0,
        'cat_image_modifier': 1.0,
        'bg_music': 'assets/background_music_hard.ogg' # Sesuaikan dengan file Anda
    }
}

# --- WAYPOINTS JALUR ORB (DIKEMBALIKAN KE SPIRAL AWAL) ---
# Fungsi untuk menghasilkan titik-titik spiral
def generate_spiral_waypoints(center_x, center_y, start_radius, end_radius, num_turns, points_per_turn):
    waypoints = []
    # Memulai dari luar, bergerak ke dalam
    for i in range(int(num_turns * points_per_turn) + 1):
        angle = i * (2 * math.pi / points_per_turn) # Sudut dalam radian
        # Radius berkurang secara linear dari start_radius ke end_radius
        current_radius = start_radius - (i / (num_turns * points_per_turn)) * (start_radius - end_radius)
        
        x = center_x + current_radius * math.cos(angle)
        y = center_y + current_radius * math.sin(angle)
        waypoints.append((int(x), int(y)))
    return waypoints

# Parameter untuk spiral
SPIRAL_CENTER_X = CAT_CENTER[0] 
SPIRAL_CENTER_Y = CAT_CENTER[1] 
SPIRAL_START_RADIUS = 300 # Jauh dari tengah (seperti sebelumnya)
SPIRAL_END_RADIUS = 100    # <--- SESUAIKAN: AKHIR JALUR DEKAT DENGAN KUCING (tidak lagi lubang)
SPIRAL_NUM_TURNS = 2.5    # 2.5 putaran penuh
SPIRAL_POINTS_PER_TURN = 40 # Jumlah titik per putaran untuk kelancaran

# Generate WAYPOINTS
WAYPOINTS = generate_spiral_waypoints(SPIRAL_CENTER_X, SPIRAL_CENTER_Y, 
                                      SPIRAL_START_RADIUS, SPIRAL_END_RADIUS, 
                                      SPIRAL_NUM_TURNS, SPIRAL_POINTS_PER_TURN)

# Hitung panjang segmen jalur
segment_lengths = []
# total_path_length = 0 # <-- Ini yang akan kita ubah namanya
TOTAL_PATH_LENGTH = 0 # <-- Ganti nama variabel menjadi UPPERCASE
for i in range(len(WAYPOINTS) - 1):
    p1 = WAYPOINTS[i]
    p2 = WAYPOINTS[i+1]
    length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    segment_lengths.append(length)
    TOTAL_PATH_LENGTH += length # <-- Ganti nama variabel di sini juga

# Periksa jika jalur terlalu pendek atau kosong
if TOTAL_PATH_LENGTH == 0: # <-- Ganti nama variabel di sini juga
    print("WARNING: Total path length is zero. Ensure WAYPOINTS define a valid path.")
    # Fallback to a minimal path to prevent division by zero errors
    if len(WAYPOINTS) < 2:
        WAYPOINTS = [(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]
        segment_lengths = [math.hypot(WAYPOINTS[1][0] - WAYPOINTS[0][0], WAYPOINTS[1][1] - WAYPOINTS[0][1])]
        TOTAL_PATH_LENGTH = segment_lengths[0] # <-- Ganti nama variabel di sini juga