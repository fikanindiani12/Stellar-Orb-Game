# game_levels.py

import pygame
import sys
import math
import random
from game_objects import CosmicCat, OrbPeluru, ChainOrb, draw_aiming_line, get_position_on_path

# --- IMPORT SEMUA KONSTANTA DARI config.py ---
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ORB_RADIUS, ORB_GAP, HOLE_SIZE, CAT_FINAL_SIZE, 
    FPS, WAYPOINTS, HOLE_CENTER, segment_lengths
)

# --- INISIALISASI GROUP & VARIABEL GLOBAL GAME ---
all_sprites = pygame.sprite.Group()
shooting_orbs = pygame.sprite.Group()
chain_orbs_group = pygame.sprite.Group()
chain_orbs_list = [] # List untuk menjaga urutan dan memudahkan manipulasi

cat = None
score = 0
chain_is_split = False
split_point_index = -1 # Index orb di mana rantai terpecah (jika ada)

# --- KONSTANTA VISUAL UNTUK JALUR ORB & PARTIKEL ---
PATH_COLOR_CORE = (150, 230, 255) # Lebih terang, lebih ke cyan
PATH_THICKNESS_CORE = 5           

PATH_COLOR_GLOW1 = (80, 180, 255, 180) 
PATH_THICKNESS_GLOW1 = 16            

PATH_COLOR_GLOW2 = (40, 140, 200, 100)
PATH_THICKNESS_GLOW2 = 30            

PARTICLE_COLOR = (255, 255, 255, 220)
PARTICLE_GLOW_COLOR = (180, 220, 255, 70)

PARTICLE_SPEED_MULTIPLIER = 0.6    
PARTICLE_COUNT = 150              
PARTICLE_SIZE_MIN = 2             
PARTICLE_SIZE_MAX = 4             

path_particles = [] # List untuk partikel yang bergerak di sepanjang jalur


# --- FUNGSI LOGIKA BANTU ---

def create_initial_chain(num_orbs, available_colors_for_difficulty, orb_images, waypoints, segment_lengths, orb_radius, orb_gap):
    """Membuat rantai orb awal yang diletakkan di sepanjang jalur."""
    chain = []
    
    total_path_length_calc = sum(segment_lengths)
    if total_path_length_calc == 0: # Hindari pembagian nol
        print("Peringatan: Total panjang jalur nol saat membuat rantai.")
        return []

    # Jarak antar pusat orb di jalur
    orb_spacing_distance = (orb_radius * 2 + orb_gap)
    # Konversi jarak ke dalam satuan 'progress' di jalur
    orb_spacing_progress = orb_spacing_distance / total_path_length_calc
    
    # Orb pertama dimulai sedikit ke dalam jalur (agar tidak langsung di tepi)
    start_safe_progress = 0.01 

    for i in range(num_orbs):
        color = random.choice(available_colors_for_difficulty)
        # Orb yang lebih 'depan' di rantai (lebih dekat ke titik awal jalur)
        # memiliki progress yang lebih besar.
        # Kita mulai dari yang paling belakang di jalur (progress paling kecil)
        path_progress = 1.0 - (i * orb_spacing_progress) # Dimulai dari 1.0 dan bergerak mundur
        
        orb = ChainOrb(color, path_progress, orb_images, waypoints, segment_lengths, orb_radius)
        chain.insert(0, orb) # Masukkan ke depan list agar orb dengan progress kecil ada di awal
        chain_orbs_group.add(orb)
    return chain

def check_for_matches(orb_chain_list, inserted_index, match_sound):
    """
    Cek kecocokan 3 atau lebih orb di rantai setelah orb baru dimasukkan.
    Mengembalikan orb yang cocok dan indeks awal serta akhir kecocokan.
    """
    if not orb_chain_list:
        return [], -1, -1

    matched_orbs = []
    
    # Check to the left
    left_index = inserted_index
    while left_index >= 0 and orb_chain_list[left_index].color_key == orb_chain_list[inserted_index].color_key:
        matched_orbs.append(orb_chain_list[left_index])
        left_index -= 1
    
    # Check to the right (start from after the inserted orb)
    right_index = inserted_index + 1
    while right_index < len(orb_chain_list) and orb_chain_list[right_index].color_key == orb_chain_list[inserted_index].color_key:
        matched_orbs.append(orb_chain_list[right_index])
        right_index += 1
    
    # Jika ada 3 atau lebih orb yang cocok
    if len(matched_orbs) >= 3:
        match_sound.play()
        return matched_orbs, left_index + 1, right_index - 1
    
    return [], -1, -1

def remove_matched_orbs(orb_chain_list, start_idx, end_idx, orb_group):
    """Menghapus orb yang cocok dari rantai dan sprite group."""
    global chain_is_split, split_point_index
    
    removed_count = 0
    # Iterasi terbalik agar penghapusan tidak mengganggu indeks yang belum dihapus
    for i in range(end_idx, start_idx - 1, -1):
        orb = orb_chain_list.pop(i)
        orb_group.remove(orb)
        removed_count += 1

    # Cek apakah rantai terbelah menjadi dua segmen yang tidak terhubung
    # Ini terjadi jika orb yang dihapus berada di tengah rantai
    # dan masih ada orb di kedua sisi titik penghapusan
    if start_idx > 0 and start_idx < len(orb_chain_list): # Jika ada orb di kiri dan kanan titik penghapusan
        chain_is_split = True
        split_point_index = start_idx # Titik di mana rantai terpisah
    else:
        chain_is_split = False
        split_point_index = -1 # Tidak terpecah atau hanya di ujung

    return removed_count

def shift_chain_on_match(orb_chain_list, start_idx, end_idx, orb_radius, orb_gap):
    """Menggeser rantai setelah orb dihapus untuk menutup celah."""
    
    # total_path_length digunakan untuk mengkonversi jarak fisik ke progress
    total_path_length = sum(segment_lengths)
    if total_path_length == 0: return

    # Jarak progress yang harus ditutup
    gap_progress_to_close = ( (end_idx - start_idx + 1) * (orb_radius * 2 + orb_gap) ) / total_path_length
    
    # Semua orb di bagian "depan" (lebih dekat ke lubang) dari titik penghapusan
    # perlu bergerak mundur untuk menutup celah.
    for i in range(start_idx):
        orb_chain_list[i].path_progress += gap_progress_to_close

    # Orb di bagian "belakang" (lebih jauh dari lubang) dari titik penghapusan
    # akan tetap di posisinya relatif terhadap satu sama lain, tetapi keseluruhan
    # segmen ini akan "ditarik" ke depan oleh segmen yang bergerak mundur,
    # jika chain_is_split adalah False.
    # Jika chain_is_split True, maka orb di kedua sisi celah akan bergerak berlawanan arah.
    # Logika di update() akan menangani gerakan ini secara berkelanjutan.

def handle_split_chain_collision(orb_chain_list, split_idx, orb_radius, orb_gap, match_sound):
    """
    Menangani jika dua ujung rantai yang terpisah bertabrakan dan membentuk kecocokan baru.
    """
    global score, chain_is_split, split_point_index

    # Kondisi untuk tabrakan split chain:
    # 1. chain_is_split harus True
    # 2. split_idx harus valid dan ada orb di kedua sisi split_idx
    # (split_idx adalah indeks orb pertama di segmen kanan, atau orb terakhir di segmen kiri + 1)
    if not chain_is_split or \
       split_idx < 0 or split_idx + 1 >= len(orb_chain_list): # Perbaiki kondisi indeks
        return

    orb1 = orb_chain_list[split_idx]
    orb2 = orb_chain_list[split_idx + 1]

    # Hanya jika orb1 dan orb2 memiliki warna yang sama
    if orb1.color_key == orb2.color_key:
        total_path_length = sum(segment_lengths)
        if total_path_length == 0: return

        # Hitung jarak visual antara pusat orb1 dan orb2
        dist_visual = math.hypot(orb2.rect.centerx - orb1.rect.centerx,
                                 orb2.rect.centery - orb1.rect.centery)
        
        # Jarak yang dianggap bertabrakan adalah ketika mereka berdekatan
        # Misalnya, sedikit lebih besar dari diameter orb + gap
        collision_threshold_distance = (ORB_RADIUS * 2) + (ORB_GAP * 0.5) 

        if dist_visual <= collision_threshold_distance:
            # Orb-orb ini bertabrakan dan memiliki warna yang sama, cek match
            
            # Cari ke kiri dari orb1
            left_match_idx = split_idx
            while left_match_idx >= 0 and orb_chain_list[left_match_idx].color_key == orb1.color_key:
                left_match_idx -= 1
            left_match_idx += 1 

            # Cari ke kanan dari orb2
            right_match_idx = split_idx + 1
            while right_match_idx < len(orb_chain_list) and orb_chain_list[right_match_idx].color_key == orb2.color_key:
                right_match_idx += 1
            right_match_idx -= 1 

            num_matched_total = (right_match_idx - left_match_idx + 1)
            
            if num_matched_total >= 3:
                # Ada kecocokan baru akibat tabrakan
                match_sound.play()
                removed_count = remove_matched_orbs(orb_chain_list, left_match_idx, right_match_idx, chain_orbs_group)
                score += removed_count * 10
                
                chain_is_split = False
                split_point_index = -1 
                
                if left_match_idx > 0 and left_match_idx < len(orb_chain_list):
                    handle_split_chain_collision(orb_chain_list, left_match_idx -1, orb_radius, orb_gap, match_sound) 


def generate_path_particles(num_particles, waypoints, segment_lengths, particle_size_min, particle_size_max):
    """Menghasilkan partikel di sepanjang jalur."""
    particles = []
    total_len = sum(segment_lengths)
    if total_len == 0: return []

    for _ in range(num_particles):
        progress = random.uniform(0.0, 1.0)
        size = random.randint(particle_size_min, particle_size_max)
        particles.append({'progress': progress, 'size': size})
    return particles

def update_path_particles(particles, speed_multiplier):
    """Memperbarui posisi partikel di sepanjang jalur."""
    for p in particles:
        p['progress'] += 0.001 * speed_multiplier * PARTICLE_SPEED_MULTIPLIER
        if p['progress'] > 1.0:
            p['progress'] = 0.0 # Reset ke awal jalur
            p['size'] = random.randint(PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX) # Ukuran acak lagi


# --- FUNGSI DRAWING BANTU ---

def draw_path(screen, waypoints, glow_surface):
    """Menggambar jalur orb dengan efek glow."""
    glow_surface.fill((0, 0, 0, 0)) # Bersihkan glow surface

    if len(waypoints) < 2:
        return

    # Gambar glow layers dari paling buram ke paling jelas
    pygame.draw.lines(glow_surface, PATH_COLOR_GLOW2, False, waypoints, PATH_THICKNESS_GLOW2)
    pygame.draw.lines(glow_surface, PATH_COLOR_GLOW1, False, waypoints, PATH_THICKNESS_GLOW1)
    
    # Gambar core path
    pygame.draw.lines(screen, PATH_COLOR_CORE, False, waypoints, PATH_THICKNESS_CORE)

    screen.blit(glow_surface, (0, 0)) # Blit glow ke layar utama


def draw_game_over_screen(screen, final_score, difficulty_level, cat_image, title_font, option_font, screen_width, screen_height):
    """Menampilkan layar Game Over."""
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Dark overlay
    screen.blit(overlay, (0, 0))

    title_text = title_font.render("GAME OVER", True, (255, 0, 0))
    title_rect = title_text.get_rect(center=(screen_width // 2, screen_height // 4))
    screen.blit(title_text, title_rect)

    score_text = option_font.render(f"Score: {final_score}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(screen_width // 2, screen_height // 2 - 30))
    screen.blit(score_text, score_rect)
    
    diff_text = option_font.render(f"Difficulty: {difficulty_level}", True, (200, 200, 255))
    diff_rect = diff_text.get_rect(center=(screen_width // 2, screen_height // 2 + 10))
    screen.blit(diff_text, diff_rect)

    # Gambar kucing di layar game over (opsional)
    if cat_image:
        cat_rect = cat_image.get_rect(midtop=(screen_width // 2, title_rect.bottom + 10))
        screen.blit(cat_image, cat_rect)

    # Tombol Restart
    restart_text = option_font.render("RESTART", True, (255, 255, 255))
    restart_rect = restart_text.get_rect(center=(screen_width // 2, screen_height * 0.75))
    pygame.draw.rect(screen, (50, 150, 200), restart_rect.inflate(40, 20), border_radius=10)
    screen.blit(restart_text, restart_rect)

    # Tombol Menu Utama
    menu_text = option_font.render("MAIN MENU", True, (255, 255, 255))
    menu_rect = menu_text.get_rect(center=(screen_width // 2, screen_height * 0.85))
    pygame.draw.rect(screen, (150, 50, 200), menu_rect.inflate(40, 20), border_radius=10)
    screen.blit(menu_text, menu_rect)
    
    return restart_rect, menu_rect


def draw_pause_screen(screen, current_score, difficulty_level, cat_image, title_font, option_font, screen_width, screen_height):
    """Menampilkan layar Pause."""
    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) # Darker overlay
    screen.blit(overlay, (0, 0))

    title_text = title_font.render("PAUSED", True, (255, 255, 0))
    title_rect = title_text.get_rect(center=(screen_width // 2, screen_height // 4))
    screen.blit(title_text, title_rect)

    score_text = option_font.render(f"Score: {current_score}", True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(screen_width // 2, screen_height // 2 - 30))
    screen.blit(score_text, score_rect)
    
    diff_text = option_font.render(f"Difficulty: {difficulty_level}", True, (200, 200, 255))
    diff_rect = diff_text.get_rect(center=(screen_width // 2, screen_height // 2 + 10))
    screen.blit(diff_text, diff_rect)

    # Gambar kucing (opsional)
    if cat_image:
        cat_rect = cat_image.get_rect(midtop=(screen_width // 2, title_rect.bottom + 10))
        screen.blit(cat_image, cat_rect)

    # Tombol Resume
    resume_text = option_font.render("RESUME", True, (255, 255, 255))
    resume_rect = resume_text.get_rect(center=(screen_width // 2, screen_height * 0.75))
    pygame.draw.rect(screen, (0, 200, 0), resume_rect.inflate(40, 20), border_radius=10)
    screen.blit(resume_text, resume_rect)

    # Tombol Menu Utama
    menu_text = option_font.render("MAIN MENU", True, (255, 255, 255))
    menu_rect = menu_text.get_rect(center=(screen_width // 2, screen_height * 0.85))
    pygame.draw.rect(screen, (150, 50, 200), menu_rect.inflate(40, 20), border_radius=10)
    screen.blit(menu_text, menu_rect)
    
    return resume_rect, menu_rect


# --- FUNGSI UTAMA UNTUK MENJALANKAN LEVEL ---
def run_level(difficulty, screen, clock, settings, available_orb_colors, cat_center, orb_radius, orb_gap, glow_surface, font, waypoints, hole_center, segment_lengths, cat_image_for_level, cat_size_tuple, bg_image, orb_images, next_orb_frame, shoot_sound, match_sound, title_font, option_font, hole_image, score_panel_image): # <-- Tambahkan score_panel_image
    """
    Fungsi utama untuk menjalankan logika permainan Zuma untuk satu level.
    Menerima semua aset dan pengaturan yang diperlukan.
    """
    global cat, score, chain_orbs_list, chain_is_split, split_point_index, all_sprites, shooting_orbs, chain_orbs_group, path_particles

    # Reset game state for a new game
    all_sprites.empty()
    shooting_orbs.empty()
    chain_orbs_group.empty()
    chain_orbs_list.clear()
    path_particles.clear()
    score = 0
    chain_is_split = False
    split_point_index = -1

    # Inisialisasi Kucing (CosmicCat) dengan CAT_FINAL_SIZE yang sudah menjadi tuple
    cat = CosmicCat(cat_center, available_orb_colors, cat_image_for_level, orb_images, shoot_sound, next_orb_frame, cat_size_tuple, orb_radius)
    all_sprites.add(cat)

    # Buat rantai orb awal
    num_initial_orbs = settings[difficulty]['initial_orbs']
    chain_orbs_list = create_initial_chain(num_initial_orbs, available_orb_colors[:settings[difficulty]['num_orb_colors']], orb_images, waypoints, segment_lengths, orb_radius, orb_gap)
    
    # Inisialisasi partikel jalur
    path_particles = generate_path_particles(PARTICLE_COUNT, waypoints, segment_lengths, PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX)

    game_over = False
    paused = False

    # Muat dan putar musik latar sesuai kesulitan
    pygame.mixer.music.load(settings[difficulty]['bg_music'])
    pygame.mixer.music.set_volume(0.6)
    pygame.mixer.music.play(-1) # Putar berulang

    # Load UI elements for score panel
    # Posisikan di kiri bawah, mirip gambar referensi
    score_panel_rect = score_panel_image.get_rect(bottomleft=(20, SCREEN_HEIGHT - 20)) # Posisikan di kiri bawah, dengan padding 20
    
    # UI Fonts for game_loop display (menggunakan font yang diteruskan)
    GAME_UI_FONT_LARGE = title_font # Menggunakan title_font dari parameter
    GAME_UI_FONT_MEDIUM = font      # Menggunakan font (GAME_FONT) dari parameter

    # Tombol Back dan Pause
    button_back_img = pygame.image.load('assets/button_back.png').convert_alpha()
    button_back_img = pygame.transform.scale(button_back_img, (50, 50))
    back_button_rect = button_back_img.get_rect(topleft=(20, 20))

    button_pause_img = pygame.image.load('assets/button_pause.png').convert_alpha()
    button_pause_img = pygame.transform.scale(button_pause_img, (50, 50))
    pause_button_rect = button_pause_img.get_rect(topleft=(80, 20))

    # Posisi untuk Next Orb Display (lebih dekat ke kucing, sedikit di bawah kanan)
    next_orb_display_pos = (cat_center[0] + CAT_FINAL_SIZE[0]//2 + 25, cat_center[1] + CAT_FINAL_SIZE[1]//2 - 10) 


    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return "exit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Klik kiri
                    if game_over:
                        restart_button, menu_button = draw_game_over_screen(screen, score, difficulty.upper(), cat_image_for_level, title_font, option_font, SCREEN_WIDTH, SCREEN_HEIGHT)
                        if restart_button.collidepoint(event.pos):
                            pygame.mixer.music.stop()
                            return difficulty # Restart level saat ini
                        if menu_button.collidepoint(event.pos):
                            pygame.mixer.music.stop()
                            return "menu"
                    elif paused:
                        resume_button, menu_button = draw_pause_screen(screen, score, difficulty.upper(), cat_image_for_level, title_font, option_font, SCREEN_WIDTH, SCREEN_HEIGHT)
                        if resume_button.collidepoint(event.pos):
                            paused = False
                            pygame.mixer.music.unpause()
                        if menu_button.collidepoint(event.pos):
                            pygame.mixer.music.stop()
                            return "menu"
                    else: # Game sedang berjalan
                        if back_button_rect.collidepoint(event.pos):
                            pygame.mixer.music.stop()
                            return "menu"
                        if pause_button_rect.collidepoint(event.pos):
                            paused = True
                            pygame.mixer.music.pause()
                        else:
                            # Tembak orb
                            new_orb = cat.shoot(event.pos, OrbPeluru)
                            if new_orb:
                                shooting_orbs.add(new_orb)
                                all_sprites.add(new_orb)
            if event.type == pygame.MOUSEMOTION:
                if not paused and not game_over:
                    cat.mouse_target_pos = event.pos

        if not game_over and not paused:
            # Update semua sprite
            all_sprites.update()
            
            # Update rantai orb
            game_speed = settings[difficulty]['speed_multiplier']
            for orb in chain_orbs_list:
                orb.update(game_speed)
            
            # Update partikel jalur
            update_path_particles(path_particles, game_speed)

            # --- Deteksi Tabrakan OrbPeluru dengan ChainOrb ---
            for s_orb in list(shooting_orbs): # Iterate over a copy to allow modification
                # Cek tabrakan dengan setiap orb di rantai
                collided_orbs = pygame.sprite.spritecollide(s_orb, chain_orbs_group, False, pygame.sprite.collide_circle)
                
                if collided_orbs:
                    s_orb.kill() # Hapus orb yang ditembakkan
                    shooting_orbs.remove(s_orb)

                    closest_orb = min(collided_orbs, key=lambda orb: math.hypot(orb.rect.centerx - s_orb.rect.centerx, orb.rect.centery - s_orb.rect.centery))
                    
                    try:
                        closest_orb_idx = chain_orbs_list.index(closest_orb)
                    except ValueError:
                        continue 
                    
                    # Tentukan posisi insertion
                    insert_idx = closest_orb_idx
                    
                    # Kita ingin orb ditembakkan dan masuk di "celah" antara dua orb,
                    # atau di salah satu ujung. Paling logis adalah di titik tabrakan
                    # di sepanjang jalur.
                    
                    # Untuk menyederhanakan, kita akan memasukkan setelah orb yang ditabrak
                    # dan kemudian menyesuaikan path_progress-nya relatif.
                    # Asumsi: orb yang ditembakkan akan memiliki path_progress sedikit lebih kecil
                    # dari orb yang ditabrak, jika ditembakkan dari arah "belakang" rantai
                    # (yaitu dari kucing menuju lubang).
                    
                    # Jika orb ditembakkan ke arah 'depan' (menuju awal jalur), maka progress-nya
                    # harus lebih besar dari orb yang ditabrak.
                    
                    # Ini adalah bagian yang tricky. Cara paling aman:
                    # Tentukan apakah s_orb secara fisik "lebih dekat" ke orb di sebelah kiri (mendekati lubang)
                    # atau orb di sebelah kanan (mendekati awal jalur) dari closest_orb.
                    
                    # Coba cara sederhana:
                    # Jika rantai kosong, masukkan di awal.
                    if not chain_orbs_list:
                        insert_idx = 0
                        new_progress = 1.0 # Paling jauh dari lubang
                    elif closest_orb_idx == len(chain_orbs_list) - 1: # Orb terakhir di rantai (paling dekat ke awal jalur)
                        insert_idx = closest_orb_idx + 1 # Masukkan di paling akhir rantai
                        new_progress = closest_orb.path_progress + ( (ORB_RADIUS*2 + ORB_GAP) / sum(segment_lengths) )
                    elif closest_orb_idx == 0: # Orb pertama di rantai (paling dekat ke lubang)
                        # Jika ditembak ke orb paling depan, dan posisi tabrakan lebih dekat ke lubang
                        # dari orb itu sendiri, masukkan sebelum.
                        dist_to_hole_from_s_orb = math.hypot(s_orb.rect.centerx - HOLE_CENTER[0], s_orb.rect.centery - HOLE_CENTER[1])
                        dist_to_hole_from_first_orb = math.hypot(closest_orb.rect.centerx - HOLE_CENTER[0], closest_orb.rect.centery - HOLE_CENTER[1])
                        
                        if dist_to_hole_from_s_orb < dist_to_hole_from_first_orb:
                            insert_idx = 0 # Masukkan sebelum orb pertama
                            new_progress = closest_orb.path_progress - ( (ORB_RADIUS*2 + ORB_GAP) / sum(segment_lengths) )
                        else:
                            insert_idx = 1 # Masukkan setelah orb pertama
                            new_progress = (closest_orb.path_progress + chain_orbs_list[1].path_progress) / 2
                    else: # Di tengah rantai
                        # Tentukan insertion point berdasarkan posisi fisik
                        prev_orb = chain_orbs_list[closest_orb_idx - 1] # Orb lebih dekat ke lubang
                        next_orb = chain_orbs_list[closest_orb_idx] # Orb yang ditabrak

                        # Hitung jarak tembakan orb ke pusat prev_orb dan next_orb
                        dist_to_prev = math.hypot(s_orb.rect.centerx - prev_orb.rect.centerx, s_orb.rect.centery - prev_orb.rect.centery)
                        dist_to_next = math.hypot(s_orb.rect.centerx - next_orb.rect.centerx, s_orb.rect.centery - next_orb.rect.centery)

                        if dist_to_prev < dist_to_next: # Lebih dekat ke prev_orb, masukkan setelah prev_orb (sebelum next_orb)
                            insert_idx = closest_orb_idx 
                            new_progress = (prev_orb.path_progress + next_orb.path_progress) / 2
                        else: # Lebih dekat ke next_orb, masukkan setelah next_orb
                            insert_idx = closest_orb_idx + 1
                            if insert_idx < len(chain_orbs_list):
                                new_progress = (next_orb.path_progress + chain_orbs_list[insert_idx].path_progress) / 2
                            else: # Masukkan di akhir
                                new_progress = next_orb.path_progress + ( (ORB_RADIUS*2 + ORB_GAP) / sum(segment_lengths) )
                    
                    new_progress = max(0.0, min(1.0, new_progress)) # Pastikan progress dalam batas
                    
                    new_chain_orb = ChainOrb(s_orb.color_key, new_progress, orb_images, waypoints, segment_lengths, orb_radius)
                    chain_orbs_list.insert(insert_idx, new_chain_orb)
                    chain_orbs_group.add(new_chain_orb)
                    all_sprites.add(new_chain_orb) # Tambahkan ke all_sprites jika diperlukan untuk drawing umum

                    # Setelah memasukkan orb, geser semua orb di kedua sisi agar tetap rapat
                    # Ini dilakukan dengan menyesuaikan path_progress mereka secara relatif
                    # Untuk saat ini, kita akan biarkan logika update() dari ChainOrb menangani pergeseran secara otomatis
                    # Ini mungkin perlu penyesuaian lebih lanjut jika ada celah yang tidak diinginkan

                    # Cek kecocokan setelah penyisipan
                    matched, start_match_idx, end_match_idx = check_for_matches(chain_orbs_list, insert_idx, match_sound)
                    if matched:
                        removed_count = remove_matched_orbs(chain_orbs_list, start_match_idx, end_match_idx, chain_orbs_group)
                        score += removed_count * 10
                        
                        # Geser orb yang tersisa untuk menutup celah
                        if chain_orbs_list:
                            shift_chain_on_match(chain_orbs_list, start_match_idx, end_match_idx, orb_radius, orb_gap)
                        
                        # Cek kembali apakah penghapusan orb memicu tabrakan dua ujung rantai
                        if chain_is_split and split_point_index != -1:
                            if split_point_index > start_match_idx: # Jika split point ada di kanan dari yang dihapus
                                new_split_idx = start_match_idx # Split point baru adalah awal dari segmen kanan
                                handle_split_chain_collision(chain_orbs_list, new_split_idx -1, orb_radius, orb_gap, match_sound) 
                            else: # Split point ada di kiri atau sama
                                handle_split_chain_collision(chain_orbs_list, split_point_index -1, orb_radius, orb_gap, match_sound) # Tetap cek di split point yang sama

                    # Jika setelah insertion dan match check, rantai terpecah dan ada orb di kedua sisi celah
                    if chain_is_split and split_point_index != -1 and len(chain_orbs_list) > 1:
                        handle_split_chain_collision(chain_orbs_list, split_point_index, orb_radius, orb_gap, match_sound)
            
            # Cek Game Over: Jika orb pertama mencapai lubang
            if chain_orbs_list and chain_orbs_list[0].path_progress <= 0:
                game_over = True
                pygame.mixer.music.stop() # Hentikan musik saat game over
        
        # --- DRAWING ---
        screen.blit(bg_image, (0, 0)) # Gambar background
        draw_path(screen, waypoints, glow_surface) # Gambar jalur orb
        
        # Gambar partikel jalur
        for p in path_particles:
            pos = get_position_on_path(p['progress'], waypoints, segment_lengths)
            # Gambar glow partikel
            pygame.draw.circle(screen, PARTICLE_GLOW_COLOR, pos, p['size'] + 3)
            # Gambar inti partikel
            pygame.draw.circle(screen, PARTICLE_COLOR, pos, p['size'])

        # Gambar lubang
        hole_rect = hole_image.get_rect(center=hole_center)
        screen.blit(hole_image, hole_rect)

        # Gambar rantai orb
        chain_orbs_group.draw(screen) 
        
        # Gambar semua sprite lainnya (termasuk kucing dan orb yang ditembakkan)
        all_sprites.draw(screen)
        
        # Gambar garis bidik jika mouse tidak berada di atas kucing
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if not cat.rect.collidepoint(mouse_x, mouse_y):
            draw_aiming_line(screen, cat.rect.center, (mouse_x, mouse_y), ORB_RADIUS)

        # Gambar Next Orb
        cat.draw_next_orb(screen, next_orb_display_pos)


        # Gambar Panel Skor & Level
        screen.blit(score_panel_image, score_panel_rect)

        # Render teks skor dan level di atas panel
        score_text = GAME_UI_FONT_MEDIUM.render("SCORE: ", True, (255, 255, 255))
        score_value_text = GAME_UI_FONT_LARGE.render(str(score), True, (255, 255, 0)) # Kuning cerah
        level_text = GAME_UI_FONT_MEDIUM.render("LEVEL: ", True, (255, 255, 255))
        level_value_text = GAME_UI_FONT_LARGE.render(difficulty.upper(), True, (255, 255, 0)) # Kuning cerah

        # Hitung posisi teks agar berada di tengah panel skor
        score_text_x = score_panel_rect.x + 20
        score_text_y = score_panel_rect.y + 25
        score_value_text_rect = score_value_text.get_rect(midleft=(score_text_x + score_text.get_width() - 5, score_text_y + 5))

        level_text_x = score_panel_rect.x + 20
        level_text_y = score_panel_rect.y + score_text.get_height() + 25 # Di bawah skor
        level_value_text_rect = level_value_text.get_rect(midleft=(level_text_x + level_text.get_width() - 5, level_text_y + 5))


        screen.blit(score_text, (score_text_x, score_text_y))
        screen.blit(score_value_text, score_value_text_rect)
        screen.blit(level_text, (level_text_x, level_text_y))
        screen.blit(level_value_text, level_value_text_rect)


        # Gambar tombol Back dan Pause
        screen.blit(button_back_img, back_button_rect)
        screen.blit(button_pause_img, pause_button_rect)

        # Draw Game Over atau Pause overlay
        if game_over:
            restart_button, menu_button = draw_game_over_screen(screen, score, difficulty.upper(), cat_image_for_level, title_font, option_font, SCREEN_WIDTH, SCREEN_HEIGHT)
        elif paused:
            resume_button, menu_button = draw_pause_screen(screen, score, difficulty.upper(), cat_image_for_level, title_font, option_font, SCREEN_WIDTH, SCREEN_HEIGHT)

        pygame.display.flip()
        clock.tick(FPS)

        pygame.mixer.music.stop() # Hentikan musik jika keluar dari loop secara paksa (misal, karena menang)
    return "menu" # Kembali ke menu jika loop berakhir (misal, karena menang atau game selesai)