import pygame
import sys
import math

def show_game_over(screen, clock, final_score):
    
    screen_width, screen_height = screen.get_size()
    
    # Font yang lebih besar
    title_font = pygame.font.Font(None, 100)
    score_font = pygame.font.Font(None, 60)
    
    # Hentikan musik permainan
    pygame.mixer.music.stop()
    
    # Teks
    game_over_text = title_font.render("GAME OVER", True, (255, 0, 0))
    score_text = score_font.render(f"Final Score: {final_score}", True, (255, 255, 255))
    
    # Posisi
    go_rect = game_over_text.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
    score_rect = score_text.get_rect(center=(screen_width // 2, screen_height // 2 + 50))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                # Kembali ke Menu Utama atau Keluar
                pygame.quit()
                sys.exit()

        screen.fill((0, 0, 0)) # Latar belakang hitam
        screen.blit(game_over_text, go_rect)
        screen.blit(score_text, score_rect)

        pygame.display.flip()
        clock.tick(60)