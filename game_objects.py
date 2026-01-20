# game_objects.py

import pygame
import math
import random

# --- FUNGSI BANTU UNTUK JALUR ---
def get_position_on_path(distance, waypoints, segment_lengths, total_path_length):
    if total_path_length == 0:
        return waypoints[0] if waypoints else (0, 0)

    distance = max(0, min(distance, total_path_length))

    current_length = 0
    for i in range(len(segment_lengths)):
        if distance <= current_length + segment_lengths[i]:
            segment_start_point = waypoints[i]
            segment_end_point = waypoints[i+1]
            segment_length = segment_lengths[i]

            dist_in_segment = distance - current_length
            
            if segment_length == 0:
                return segment_start_point
            
            t = dist_in_segment / segment_length
            
            x = segment_start_point[0] + t * (segment_end_point[0] - segment_start_point[0])
            y = segment_start_point[1] + t * (segment_end_point[1] - segment_start_point[1])
            return int(x), int(y)
        current_length += segment_lengths[i]
    
    return waypoints[-1] if waypoints else (0, 0)


# --- CLASS ORB PELURU (Untuk Orb yang ditembakkan) ---
class OrbPeluru(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, color, orb_images, orb_radius):
        super().__init__()
        self.color = color
        self.orb_images = orb_images
        self.image = self.orb_images[self.color]
        self.rect = self.image.get_rect(center=start_pos)
        self.pos = pygame.math.Vector2(start_pos)
        self.target_pos = pygame.math.Vector2(target_pos)
        self.speed = 15
        self.direction = (self.target_pos - self.pos).normalize()
        self.radius = orb_radius

    def update(self):
        self.pos += self.direction * self.speed
        self.rect.center = int(self.pos.x), int(self.pos.y)

        if not pygame.Rect(0, 0, pygame.display.get_surface().get_width(), pygame.display.get_surface().get_height()).colliderect(self.rect):
            self.kill()

# --- CLASS CHAIN ORB (Untuk Orb di Jalur) ---
class ChainOrb(pygame.sprite.Sprite):
    def __init__(self, orb_index, color, distance_on_path, orb_radius, orb_images):
        super().__init__()
        self.orb_index = orb_index
        self.color = color
        self.orb_images = orb_images
        self.image = self.orb_images[self.color]
        self.rect = self.image.get_rect(center=(0, 0))
        self.distance_on_path = distance_on_path
        self.radius = orb_radius
        self.is_exploding = False
        self.explosion_frame = 0
        self.explosion_images = self._generate_explosion_images() 

    def _generate_explosion_images(self):
        explosion_frames = []
        explosion_size = int(self.radius * 2.5) 
        for i in range(1, 6):
            surf = pygame.Surface((explosion_size, explosion_size), pygame.SRCALPHA)
            alpha = 255 - (i * 50)
            pygame.draw.circle(surf, (255, 0, 0, max(0, alpha)), (explosion_size // 2, explosion_size // 2), self.radius * (i / 5.0))
            explosion_frames.append(surf)
        return explosion_frames
    
    def update_explosion(self):
        if self.is_exploding:
            self.explosion_frame += 0.3
            if self.explosion_frame >= len(self.explosion_images):
                self.is_exploding = False
                self.kill()
            else:
                original_center = self.rect.center
                self.image = self.explosion_images[int(self.explosion_frame)]
                self.rect = self.image.get_rect(center=original_center)

    def update_position(self, waypoints, segment_lengths, total_path_length):
        if not self.is_exploding:
            pos_x, pos_y = get_position_on_path(self.distance_on_path, waypoints, segment_lengths, total_path_length)
            self.rect.center = (pos_x, pos_y)
        else:
            self.update_explosion()


# --- CLASS KUCING (Shooter) ---
class CosmicCat(pygame.sprite.Sprite):
    def __init__(self, cat_center, available_orb_colors_for_difficulty, cat_image_for_level, orb_images, shoot_sound, next_orb_frame_surface, cat_size_tuple, orb_radius):
        super().__init__()
        
        self.center_pos = cat_center
        self.original_image = cat_image_for_level
        
        self.image = pygame.transform.scale(self.original_image, cat_size_tuple) 
        self.rect = self.image.get_rect(center=self.center_pos)
        # self.original_rect = self.rect.copy() # Tidak diperlukan jika tidak ada rotasi

        self.orb_images = orb_images
        self.available_orb_colors = available_orb_colors_for_difficulty 
        self.shoot_sound = shoot_sound
        self.next_orb_frame_surface = next_orb_frame_surface
        self.orb_radius = orb_radius
        
        self.current_orb_color = self._get_random_orb_color()
        self.next_orb_color = self._get_random_orb_color()
        while self.current_orb_color == self.next_orb_color:
            self.next_orb_color = self._get_random_orb_color()

        # self.rotation_angle = 0 # Tidak diperlukan jika tidak ada rotasi

    def _get_random_orb_color(self):
        return random.choice(self.available_orb_colors)

    def switch_orbs(self):
        temp_color = self.current_orb_color
        self.current_orb_color = self.next_orb_color
        self.next_orb_color = temp_color
        self.next_orb_color = self._get_random_orb_color() 
        while self.next_orb_color == self.current_orb_color:
            self.next_orb_color = self._get_random_orb_color()

    def shoot_orb(self, target_pos, all_sprites, orb_peluru_group):
        if self.shoot_sound:
            self.shoot_sound.play()
        orb = OrbPeluru(self.center_pos, target_pos, self.current_orb_color, self.orb_images, self.orb_radius) 
        all_sprites.add(orb)
        orb_peluru_group.add(orb)
        
        self.current_orb_color = self.next_orb_color
        self.next_orb_color = self._get_random_orb_color()
        while self.next_orb_color == self.current_orb_color:
            self.next_orb_color = self._get_random_orb_color()
        return orb

    def update(self, mouse_pos):
        # Biarkan fungsi ini kosong atau hapus kode rotasi
        # Kucing akan tetap diam karena tidak ada perubahan pada self.image atau self.rect di sini.
        pass # <--- KODE ROTASI DIHAPUS DI SINI

    def draw_next_orb(self, screen, display_pos_tuple):
        frame_rect = self.next_orb_frame_surface.get_rect(center=display_pos_tuple)
        screen.blit(self.next_orb_frame_surface, frame_rect.topleft)

        next_orb_image = self.orb_images[self.next_orb_color]
        next_orb_rect = next_orb_image.get_rect(center=frame_rect.center)
        screen.blit(next_orb_image, next_orb_rect)