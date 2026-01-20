import pygame
import sys
import math

# --- IMPORT SEMUA KONSTANTA DARI config.py ---
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    DIFFICULTY_SETTINGS,
    ORB_RADIUS # Diperlukan untuk gambar orb di menu
)

# --- FUNGSI UTAMA MENU ---
# PERBAIKAN: TAMBAHKAN mixer_initialized KE DEFINISI FUNGSI
def main_menu(screen, clock, menu_music_path, screen_width, screen_height, title_font, option_font, menu_bg_image, fps, mixer_initialized):
    menu_running = True
    
    # <--- BAGIAN PERBAIKAN MUSIK: CEK mixer_initialized SEBELUM MEMUTAR MUSIK ---
    if mixer_initialized:
        try:
            pygame.mixer.music.load(menu_music_path)
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play(-1) # Putar berulang
            print(f"Playing menu music: {menu_music_path}")
        except pygame.error as e:
            print(f"Error loading or playing menu music: {e}. Menu music will not play.")
            # Jika musik menu gagal dimuat/diputar, set mixer_initialized menjadi False lokal untuk menu ini
            # Agar tidak ada panggilan mixer.music berikutnya yang gagal
            mixer_initialized = False 
    else:
        print("Mixer not initialized, skipping menu music playback.")
    # --- AKHIR BAGIAN PERBAIKAN MUSIK ---

    # --- PALET WARNA UMUM (Untuk Judul & Tombol Level) ---
    COLOR_DEFAULT = (255, 230, 150)             
    COLOR_HIGHLIGHT = (255, 255, 255)           
    
    BUTTON_BASE_COLOR = (80, 40, 0, 180)        
    BUTTON_OUTER_GLOW = (255, 120, 0, 120)      
    BUTTON_INNER_OUTLINE = (255, 180, 50, 255)  
    BUTTON_HOVER_GLOW_EFFECT = (255, 200, 100, 100) 
    BUTTON_HOVER_OUTLINE = (255, 255, 200, 255) 

    COLOR_TEXT_SHADOW = (0, 0, 0)               

    # --- PALET WARNA KHUSUS UNTUK TOMBOL EXIT (Merah Menyala/Kosmik) ---
    EXIT_COLOR_DEFAULT = (255, 100, 100)        # Teks merah muda untuk normal
    EXIT_COLOR_HIGHLIGHT = (255, 255, 255)      # Teks putih terang saat hover
    EXIT_BUTTON_BASE_COLOR = (120, 0, 0, 180)   # Background merah gelap transparan
    EXIT_BUTTON_OUTER_GLOW = (255, 0, 0, 120)   # Glow merah menyala terluar
    EXIT_BUTTON_INNER_OUTLINE = (255, 100, 100, 255) # Garis dalam merah terang
    EXIT_BUTTON_HOVER_GLOW_EFFECT = (255, 0, 0, 100) # Efek glow saat hover
    EXIT_BUTTON_HOVER_OUTLINE = (255, 150, 150, 255) # Garis saat hover (merah lebih terang)

    current_title_font = title_font if title_font else pygame.font.Font(None, 85)
    current_option_font = option_font if option_font else pygame.font.Font(None, 45) 

    # --- JUDUL GAME BARU ---
    title_text_1 = current_title_font.render("ZUMA PLANET", True, COLOR_HIGHLIGHT)
    title_text_2 = current_title_font.render("THE CAT GUARDIAN", True, COLOR_DEFAULT)
    title_text_3 = current_title_font.render("OF THE GALAXY", True, COLOR_DEFAULT)

    # --- UKURAN TOMBOL ---
    button_height = 80 
    button_width = 280 

    # --- PENGATURAN TATA LETAK TOMBOL ---
    y_start_level_buttons = screen_height - 250 

    gap_between_buttons = 30 
    
    total_level_buttons_width = (3 * button_width) + (2 * gap_between_buttons)
    
    start_x_for_first_button = (screen_width - total_level_buttons_width) // 2 + (button_width // 2)

    button_texts = {
        'easy': 'EASY', 
        'medium': 'MEDIUM ',
        'hard': 'HARD',
        'exit': 'EXIT' 
    }

    button_info = {}

    # Tombol EASY (kiri)
    easy_rect = pygame.Rect(0, 0, button_width, button_height)
    easy_rect.center = (start_x_for_first_button, y_start_level_buttons)
    button_info['easy'] = {'text': button_texts['easy'], 'rect': easy_rect, 'is_exit': False}

    # Tombol MEDIUM  (tengah)
    medium_rect = pygame.Rect(0, 0, button_width, button_height)
    medium_rect.center = (start_x_for_first_button + button_width + gap_between_buttons, y_start_level_buttons)
    button_info['medium'] = {'text': button_texts['medium'], 'rect': medium_rect, 'is_exit': False}
    
    # Tombol HARD (kanan)
    hard_rect = pygame.Rect(0, 0, button_width, button_height)
    hard_rect.center = (start_x_for_first_button + 2 * (button_width + gap_between_buttons), y_start_level_buttons)
    button_info['hard'] = {'text': button_texts['hard'], 'rect': hard_rect, 'is_exit': False}

    # Tombol EXIT GAME (di bawah tengah tombol level)
    exit_rect = pygame.Rect(0, 0, button_width, button_height)
    exit_rect.center = (screen_width // 2, y_start_level_buttons + button_height + 30) 
    button_info['exit'] = {'text': button_texts['exit'], 'rect': exit_rect, 'is_exit': True} # Tambahkan flag is_exit


    while menu_running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if mixer_initialized: # <--- CEK mixer_initialized sebelum menghentikan musik
                    pygame.mixer.music.stop()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for diff, info in button_info.items():
                    if info['rect'].collidepoint(mouse_pos):
                        if mixer_initialized: # <--- CEK mixer_initialized sebelum menghentikan musik
                            pygame.mixer.music.stop() 
                        if info['is_exit']: # Gunakan flag is_exit
                            pygame.quit()
                            sys.exit()
                        else:
                            return diff 

        # --- DRAWING BACKGROUND & JUDUL ---
        if menu_bg_image: 
            screen.blit(menu_bg_image, (0, 0))
        else: 
            screen.fill((20, 0, 30)) 
        
        # Gambar Judul (Penempatan Disesuaikan untuk Font Besar)
        t1_rect = title_text_1.get_rect(center=(screen_width // 2, screen_height // 4 - 90)) 
        t2_rect = title_text_2.get_rect(center=(screen_width // 2, screen_height // 4 - 10))
        t3_rect = title_text_3.get_rect(center=(screen_width // 2, screen_height // 4 + 70))
        
        # Gambar Bayangan (Shadow)
        shadow_offset = 4 
        screen.blit(current_title_font.render("ZUMA PLANET", True, COLOR_TEXT_SHADOW), (t1_rect.x+shadow_offset, t1_rect.y+shadow_offset))
        screen.blit(current_title_font.render("THE CAT GUARDIAN", True, COLOR_TEXT_SHADOW), (t2_rect.x+shadow_offset, t2_rect.y+shadow_offset))
        screen.blit(current_title_font.render("OF THE GALAXY", True, COLOR_TEXT_SHADOW), (t3_rect.x+shadow_offset, t3_rect.y+shadow_offset))

        # Gambar Teks Utama
        screen.blit(title_text_1, t1_rect)
        screen.blit(title_text_2, t2_rect)
        screen.blit(title_text_3, t3_rect)

        # --- DRAWING TOMBOL (Sekarang dengan penyesuaian untuk EXIT) ---
        for diff, info in button_info.items():
            rect = info['rect']
            text = info['text']
            is_exit_button = info['is_exit'] # Ambil flag is_exit

            # Tentukan palet warna yang akan digunakan (normal atau exit)
            if is_exit_button:
                current_color_default = EXIT_COLOR_DEFAULT
                current_color_highlight = EXIT_COLOR_HIGHLIGHT
                current_button_base_color = EXIT_BUTTON_BASE_COLOR
                current_button_outer_glow = EXIT_BUTTON_OUTER_GLOW
                current_button_inner_outline = EXIT_BUTTON_INNER_OUTLINE
                current_button_hover_glow_effect = EXIT_BUTTON_HOVER_GLOW_EFFECT
                current_button_hover_outline = EXIT_BUTTON_HOVER_OUTLINE
            else:
                current_color_default = COLOR_DEFAULT
                current_color_highlight = COLOR_HIGHLIGHT
                current_button_base_color = BUTTON_BASE_COLOR
                current_button_outer_glow = BUTTON_OUTER_GLOW
                current_button_inner_outline = BUTTON_INNER_OUTLINE
                current_button_hover_glow_effect = BUTTON_HOVER_GLOW_EFFECT
                current_button_hover_outline = BUTTON_HOVER_OUTLINE
            
            is_hovered = rect.collidepoint(mouse_pos)
            text_color = current_color_highlight if is_hovered else current_color_default
            
            button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            
            # 1. Gambar Outer Glow (Lapisan Paling Luar, Transparan)
            if is_hovered:
                # Perbaikan: inflate harus lebih kecil dari ukuran rect_size untuk menghindari artefak
                # atau gambar glow harus dibuat terpisah dan diletakkan di bawah button_surface
                # Untuk kesederhanaan, mari kita gambar glow di screen langsung, bukan di button_surface.
                glow_rect = rect.inflate(8, 8) # Rect yang lebih besar untuk glow
                # Gambar glow di screen, di bawah button_surface
                pygame.draw.rect(screen, current_button_outer_glow, glow_rect, border_radius=18)
            
            # 2. Gambar Background Tombol (Base Color)
            pygame.draw.rect(button_surface, current_button_base_color, button_surface.get_rect(), border_radius=15)
            
            # 3. Gambar Inner Outline (Garis Solid di Dalam)
            outline_color = current_button_hover_outline if is_hovered else current_button_inner_outline
            outline_thickness = 4 if is_hovered else 2
            pygame.draw.rect(button_surface, outline_color, button_surface.get_rect(), outline_thickness, border_radius=15) 
            
            # 4. Tambahkan Efek Glow saat Hover di Atas Base
            if is_hovered:
                hover_glow = pygame.Surface(rect.size, pygame.SRCALPHA)
                hover_glow.fill(current_button_hover_glow_effect)
                button_surface.blit(hover_glow, (0, 0))
            
            # 5. Gambar Teks Tombol
            rendered_text = current_option_font.render(text, True, text_color)
            text_rect = rendered_text.get_rect(center=(rect.width // 2, rect.height // 2))
            button_surface.blit(rendered_text, text_rect)
            
            screen.blit(button_surface, rect.topleft)

        pygame.display.flip()
        clock.tick(fps)
    
    # Perbaikan: Mengembalikan "exit" jika loop berakhir tanpa pilihan kesulitan (misal, karena QUIT)
    # Atau mengembalikan default 'easy' jika memang ada skenario fallback lain yang diinginkan
    if mixer_initialized:
        pygame.mixer.music.stop()
    return 'exit' # Lebih aman mengembalikan exit jika tidak ada pilihan yang dibuat secara eksplisit