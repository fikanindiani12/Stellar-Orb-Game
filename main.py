import pygame
import sys
import math
import random
from game_objects import CosmicCat, OrbPeluru, ChainOrb, draw_aiming_line_to_sides, get_position_on_path
from score import show_game_over # Import fungsi game over

# Inisialisasi Group dan Variabel Global untuk Game Play
all_sprites = pygame.sprite.Group()
shooting_orbs = pygame.sprite.Group()
chain_orbs_group = pygame.sprite.Group()
chain_orbs_list = []
cat = None
score = 0
chain_is_split = False
split_point_index = -1

# --- NEW: KONSTANTA VISUAL UNTUK JALUR ORB (Disesuaikan untuk LEBIH BERCAHAYA dan HIDUP) ---
# Warna untuk inti jalur (paling terang)
PATH_COLOR_CORE = (150, 230, 255) # Lebih terang, lebih ke cyan
PATH_THICKNESS_CORE = 5            # Sedikit lebih tebal

# Warna untuk glow lapisan 1 (lebih lebar, sedikit transparan)
PATH_COLOR_GLOW1 = (80, 180, 255, 180) # Lebih terang, alpha lebih tinggi
PATH_THICKNESS_GLOW1 = 16            # Lebih tebal

# Warna untuk glow lapisan 2 (paling lebar, paling transparan)
PATH_COLOR_GLOW2 = (40, 140, 200, 100) # Lebih terang, alpha lebih tinggi
PATH_THICKNESS_GLOW2 = 30            # Lebih tebal

# Warna untuk partikel di jalur
PARTICLE_COLOR = (255, 255, 255, 220) # Lebih putih, sedikit lebih solid
PARTICLE_GLOW_COLOR = (180, 220, 255, 70) # Lebih cerah, alpha lebih tinggi

# Kecepatan partikel di jalur (relatif terhadap kecepatan orb)
PARTICLE_SPEED_MULTIPLIER = 0.6    # Sedikit lebih cepat
PARTICLE_COUNT = 150              # Lebih banyak partikel
PARTICLE_SIZE_MIN = 2             # Ukuran minimum partikel sedikit lebih besar
PARTICLE_SIZE_MAX = 4             # Ukuran maksimum partikel sedikit lebih besar

# --- Variabel untuk Partikel (akan diinisialisasi dalam game_loop) ---
path_particles = [] # Pastikan ini diinisialisasi sebagai list kosong


# --- FUNGSI LOGIKA BANTU ---

def create_initial_chain(num_orbs, available_colors_for_difficulty, orb_images, waypoints, segment_lengths, orb_radius, orb_gap):
    chain = []
    
    total_path_length_calc = sum(segment_lengths) if segment_lengths else 1.0

    orb_spacing_progress = (orb_radius * 2 + orb_gap) / total_path_length_calc
    
    for i in range(num_orbs):
        color = random.choice(available_colors_for_difficulty)
        start_safe_progress = 0.01
        path_progress = start_safe_progress - (i * orb_spacing_progress)
        
        orb = ChainOrb(color, path_progress, orb_images, waypoints, segment_lengths)
        chain.append(orb)
        chain_orbs_group.add(orb)
    return chain

def check_for_matches(orb_chain_list, inserted_index, match_sound):
    """Cek apakah ada 3+ orb yang cocok di sekitar inserted_index."""
    if not orb_chain_list or inserted_index < 0 or inserted_index >= len(orb_chain_list):
        return 0

    target_color = orb_chain_list[inserted_index].color_key
    
    left_match_indices = []
    i = inserted_index - 1
    while i >= 0 and orb_chain_list[i].color_key == target_color:
        left_match_indices.append(i)
        i -= 1
    
    right_match_indices = []
    i = inserted_index + 1
    while i < len(orb_chain_list) and orb_chain_list[i].color_key == target_color:
        right_match_indices.append(i)
        i += 1 
        
    all_match_indices = sorted([inserted_index] + left_match_indices + right_match_indices)

    if len(all_match_indices) >= 3:
        match_sound.play()
        
        for index_to_remove in reversed(all_match_indices):
            orb_to_remove = orb_chain_list.pop(index_to_remove)
            orb_to_remove.kill()
        
        return len(all_match_indices)
    return 0

# --- FUNGSI POWER-UP (INI ADALAH FUNGSI BAWAAN, BUKAN BAGIAN DARI PENYESUAIAN UI SAAT INI) ---
def apply_powerup(powerup_type, cat_obj, chain_list, shooting_orbs_group, orb_radius, match_sound):
    if powerup_type == 'slow':
        for orb in chain_list:
            orb.current_speed_multiplier = 0.5
    elif powerup_type == 'stop':
        for orb in chain_list:
            orb.current_speed_multiplier = 0
    elif powerup_type == 'reverse':
        for orb in chain_list:
            orb.current_direction_multiplier *= -1
    elif powerup_type == 'bomb':
        if chain_list:
            if shooting_orbs_group and shooting_orbs_group.sprites():
                last_shot_orb = shooting_orbs_group.sprites()[-1]
                target_orb = None
                min_dist = float('inf')
                for orb in chain_list:
                    dist = math.hypot(orb.rect.centerx - last_shot_orb.rect.centerx,
                                      orb.rect.centery - last_shot_orb.rect.centery)
                    if dist < min_dist:
                        min_dist = dist
                        target_orb = orb
                if target_orb:
                    target_index = chain_list.index(target_orb)
                    start_index = max(0, target_index - 2)
                    end_index = min(len(chain_list), target_index + 3)
                    
                    removed_count = 0
                    for i in reversed(range(start_index, end_index)):
                        if i < len(chain_list):
                            orb_to_remove = chain_list.pop(i)
                            orb_to_remove.kill()
                            removed_count += 1
                    if removed_count > 0:
                        match_sound.play()
                    return removed_count
    elif powerup_type == 'color_bomb':
        if cat_obj.current_orb:
            target_color = cat_obj.current_orb.color_key
            removed_count = 0
            new_chain_list = []
            for orb in chain_list:
                if orb.color_key == target_color:
                    orb.kill()
                    removed_count += 1
                else:
                    new_chain_list.append(orb)
            chain_list[:] = new_chain_list
            if removed_count > 0:
                match_sound.play()
            return removed_count
    elif powerup_type == 'accuracy':
        cat_obj.activate_powerup('accuracy', 5000)
    elif powerup_type == 'laser':
        cat_obj.activate_powerup('laser', 3000)

    return 0

# --- GAME LOOP UTAMA ---

def game_loop(difficulty, screen, clock, settings, available_orb_colors, cat_center, orb_radius, orb_gap, glow_surface, font, waypoints, hole_center, segment_lengths, cat_image_for_level):
    global score, chain_orbs_list, cat, chain_is_split, split_point_index, path_particles

    from main import BG_IMAGE, HOLE_IMAGE, ORB_IMAGES, NEXT_ORB_FRAME, SHOOT_SOUND, MATCH_SOUND, SCREEN_WIDTH, SCREEN_HEIGHT, CAT_SIZE

    # Reset Global Groups dan Variabel
    all_sprites.empty()
    shooting_orbs.empty()
    chain_orbs_group.empty()
    chain_orbs_list.clear()
    score = 0
    chain_is_split = False
    split_point_index = -1

    # Inisialisasi Partikel Jalur
    path_particles = [] # Reset partikel di awal setiap game loop
    total_path_length = sum(segment_lengths)
    if total_path_length == 0: total_path_length = 1 # Hindari pembagian dengan nol

    for _ in range(PARTICLE_COUNT):
        initial_progress = random.uniform(0.0, 1.0)
        size = random.randint(PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX)
        speed = random.uniform(0.8, 1.2) * PARTICLE_SPEED_MULTIPLIER
        path_particles.append({'progress': initial_progress, 'size': size, 'speed': speed})

    current_settings = settings[difficulty]
    current_game_speed_multiplier = current_settings['speed_multiplier']
    num_allowed_colors = current_settings['num_orb_colors']
    initial_orbs_count = current_settings['initial_orbs']
    game_over_threshold = current_settings.get('death_line_progress', 0.99)

    available_colors_for_difficulty = available_orb_colors[:min(num_allowed_colors, len(available_orb_colors))]
    
    try:
        music_path = current_settings['bg_music']
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print(f"WARNING: Gagal memuat musik latar game dari {current_settings['bg_music']}. Error: {e}")
        pass

    # Inisialisasi Cat (melewatkan semua aset yang dibutuhkan)
    cat = CosmicCat(cat_center, available_colors_for_difficulty, cat_image_for_level, ORB_IMAGES, SHOOT_SOUND, NEXT_ORB_FRAME, CAT_SIZE)
    all_sprites.add(cat)

    # Inisialisasi Rantai Orb
    chain_orbs_list = create_initial_chain(initial_orbs_count, available_colors_for_difficulty, ORB_IMAGES, waypoints, segment_lengths, orb_radius, orb_gap)

    # --- FONT UNTUK UI DALAM GAME ---
    GAME_UI_FONT_MEDIUM = pygame.font.Font(None, 28)
    GAME_UI_FONT_LARGE = pygame.font.Font(None, 45)

    # --- Fungsi untuk Memuat Aset UI ---
    def load_asset_ui(path, scale=1.0, alpha=True):
        try:
            image = pygame.image.load(path)
            if alpha:
                image = image.convert_alpha()
            else:
                image = image.convert()
            
            if scale != 1.0:
                original_width, original_height = image.get_size()
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                image = pygame.transform.scale(image, (new_width, new_height))
            return image
        except pygame.error as e:
            print(f"ERROR: Gagal memuat aset UI dari {path}. Error: {e}")
            sys.exit()

    # --- Muat Aset UI ---
    game_bg_new = load_asset_ui('assets/game_bg.png', alpha=True)
    game_bg_new = pygame.transform.scale(game_bg_new, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- PENGATURAN PANEL SCORE (UKURAN & POSISI) ---
    SCORE_PANEL_SCALE = 0.45
    score_panel_frame = load_asset_ui('assets/score_display_panel.png', scale=SCORE_PANEL_SCALE, alpha=True)
    score_panel_width, score_panel_height = score_panel_frame.get_size()
    
    SCORE_PANEL_POS_X = int(SCREEN_WIDTH * 0.05)
    SCORE_PANEL_POS_Y = int(SCREEN_HEIGHT - score_panel_height - (SCREEN_HEIGHT * 0.03))
    score_panel_pos = (SCORE_PANEL_POS_X, SCORE_PANEL_POS_Y)

    # --- PENGATURAN TOMBOL BACK DAN PAUSE (UKURAN & POSISI) ---
    BUTTON_ICON_SCALE = 0.18
    button_back_img = load_asset_ui('assets/button_back.png', scale=BUTTON_ICON_SCALE, alpha=True)
    button_pause_img = load_asset_ui('assets/button_pause.png', scale=BUTTON_ICON_SCALE, alpha=True)
    
    button_icon_width, button_icon_height = button_back_img.get_size()
    
    BUTTON_MARGIN_RIGHT = int(SCREEN_WIDTH * 0.15)
    BUTTON_MARGIN_TOP = int(SCREEN_HEIGHT * 0.03)
    
    BUTTON_GAP_X = 5

    pause_button_rect = pygame.Rect(
        SCREEN_WIDTH - button_icon_width - BUTTON_MARGIN_RIGHT,
        BUTTON_MARGIN_TOP,
        button_icon_width,
        button_icon_height
    )
    back_button_rect = pygame.Rect(
        pause_button_rect.left - button_icon_width - BUTTON_GAP_X,
        BUTTON_MARGIN_TOP,
        button_icon_width,
        button_icon_height
    )

    paused = False

    running = True
    while running:
        if not paused:
            cat.mouse_target_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return "exit"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(pygame.mouse.get_pos()):
                    print("Tombol BACK diklik!")
                    pygame.mixer.music.stop()
                    return "menu"
                if pause_button_rect.collidepoint(pygame.mouse.get_pos()):
                    print("Tombol PAUSE diklik!")
                    paused = not paused
                    if paused:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()

                if not paused and event.button == 1:
                    new_orb_shot = cat.shoot(cat.mouse_target_pos, OrbPeluru)
                    shooting_orbs.add(new_orb_shot)
            
        if not paused:
            cat.update()
            shooting_orbs.update()

            total_path_length_for_spacing = sum(segment_lengths) if segment_lengths else 1.0
            orb_spacing_progress = (orb_radius * 2 + orb_gap) / total_path_length_for_spacing
            
            for i, orb in enumerate(chain_orbs_list):
                if chain_is_split and i >= split_point_index:
                    orb.rect.center = get_position_on_path(orb.path_progress, waypoints, segment_lengths)
                elif chain_is_split and i < split_point_index:
                    orb.update(current_game_speed_multiplier)

                    if split_point_index > 0 and i == split_point_index - 1:
                        pass