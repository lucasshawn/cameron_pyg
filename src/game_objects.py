# dungeons and data - cameron lucas
# game_objects.py
# cs244 final project
# 6/4/2026
#
# this file holds all the game objects - player, enemies, items, tiles, rooms, hud
# basically anything that gets drawn or updated lives here
# main.py handles the actual game loop and calls into this

import pygame
import random
import math

# screen/tile size constants - changing tile size will break everything lol
TILE_SIZE = 48
SCREEN_W  = 800
SCREEN_H  = 600
HUD_H     = 52   # pixels reserved at the top for the health/key/sword display


# =============================================================================
# tile sprite functions
# all tiles are drawn with pygame rects - no image files needed
# each function returns a surface that gets cached so we dont remake them every frame
# =============================================================================

def make_grass_tile(variant=0):
    # three slightly different shades of green so the overworld doesnt look
    # like a solid color block
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    bases  = [(34,120,34),(30,110,30),(38,126,38)]
    darks  = [(28,100,28),(24,92,24),(32,106,32)]
    lights = [(50,140,50),(46,132,46),(54,146,54)]
    b,d,l  = bases[variant%3], darks[variant%3], lights[variant%3]
    surf.fill(b)
    # scatter some darker patches and lighter blade highlights
    spots = [(4,6),(20,14),(36,8),(10,30),(28,36),(42,22),(16,44),(38,40)]
    for rx,ry in spots[variant%len(spots):variant%len(spots)+4]:
        pygame.draw.rect(surf,d,(rx,ry,6,4))
    for rx,ry in [(8,10),(24,4),(12,38),(40,28),(32,18)]:
        pygame.draw.rect(surf,l,(rx,ry,3,6))
    return surf

def make_wall_tile():
    # stone brick pattern for the dungeon walls
    # mortar lines split each row into offset bricks like real brickwork
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((110,100,90))
    for y in [16,32]: pygame.draw.line(surf,(80,75,68),(0,y),(TILE_SIZE,y),2)
    for x in [24]:    pygame.draw.line(surf,(80,75,68),(x,0),(x,16),2)
    for x in [12,36]: pygame.draw.line(surf,(80,75,68),(x,16),(x,32),2)
    for x in [24]:    pygame.draw.line(surf,(80,75,68),(x,32),(x,TILE_SIZE),2)
    # left/top edge darker for a shadow effect
    pygame.draw.rect(surf,(70,65,58),(0,0,2,TILE_SIZE))
    pygame.draw.rect(surf,(70,65,58),(0,0,TILE_SIZE,2))
    return surf

def make_stone_wall_tile():
    # darker version of the wall tile used in the overworld area
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((80,72,65))
    for y in [16,32]: pygame.draw.line(surf,(55,50,44),(0,y),(TILE_SIZE,y),2)
    for x in [24]:    pygame.draw.line(surf,(55,50,44),(x,0),(x,16),2)
    for x in [12,36]: pygame.draw.line(surf,(55,50,44),(x,16),(x,32),2)
    for x in [24]:    pygame.draw.line(surf,(55,50,44),(x,32),(x,TILE_SIZE),2)
    pygame.draw.rect(surf,(45,40,36),(0,0,2,TILE_SIZE))
    pygame.draw.rect(surf,(45,40,36),(0,0,TILE_SIZE,2))
    # right/bottom edge lighter so it reads as 3d
    pygame.draw.rect(surf,(110,100,90),(TILE_SIZE-2,0,2,TILE_SIZE))
    pygame.draw.rect(surf,(110,100,90),(0,TILE_SIZE-2,TILE_SIZE,2))
    return surf

def make_water_tile():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((30,80,180))
    # simple horizontal lines to suggest ripples
    for pos in [(4,12),(28,28),(8,40)]:
        pygame.draw.line(surf,(60,120,220),(pos[0],pos[1]),(pos[0]+16,pos[1]),2)
    return surf

def make_path_tile():
    # dirt path tile with some texture spots
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((160,130,80))
    pygame.draw.rect(surf,(140,110,65),(6,10,8,4))
    pygame.draw.rect(surf,(140,110,65),(30,28,10,3))
    pygame.draw.rect(surf,(140,110,65),(16,38,6,5))
    return surf

def make_tree_tile():
    # decorative tree - no collision, just drawn on top of grass
    # layered rectangles to get a chunky 8-bit look
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf,(100,70,30),(18,32,12,16))   # trunk
    pygame.draw.rect(surf,(80,55,20),(20,32,4,16))
    pygame.draw.rect(surf,(20,100,20),(8,20,32,18))    # bottom foliage
    pygame.draw.rect(surf,(30,120,30),(10,22,28,14))
    pygame.draw.rect(surf,(12,100,16),(14,10,20,16))   # top foliage
    pygame.draw.rect(surf,(40,130,40),(16,12,16,12))
    pygame.draw.rect(surf,(60,160,60),(18,14,6,6))     # shine highlight
    return surf

def make_dead_tree_tile():
    # bare spooky tree for the graveyard - gnarled branches, no leaves
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    trunk = (60,50,45)
    dark  = (40,32,30)
    pygame.draw.rect(surf,trunk,(19,24,10,24))
    pygame.draw.rect(surf,dark,(21,24,4,24))
    # branches going left and right
    pygame.draw.line(surf,trunk,(24,28),(8,16),3)
    pygame.draw.line(surf,dark,(24,28),(8,16),1)
    pygame.draw.line(surf,trunk,(24,28),(40,18),3)
    pygame.draw.line(surf,dark,(24,28),(40,18),1)
    pygame.draw.line(surf,trunk,(14,20),(6,12),2)
    pygame.draw.line(surf,trunk,(34,22),(42,12),2)
    pygame.draw.line(surf,trunk,(8,16),(4,10),2)
    pygame.draw.line(surf,trunk,(40,18),(44,12),2)
    return surf

def make_purple_grass_tile(variant=0):
    # dark purple ground tiles for the graveyard zone
    # same structure as regular grass just with spooky colors
    bases  = [(55,30,70),(48,25,62),(62,34,78)]
    darks  = [(40,20,55),(34,16,48),(46,24,62)]
    lights = [(72,44,88),(66,38,82),(78,50,94)]
    b,d,l  = bases[variant%3], darks[variant%3], lights[variant%3]
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(b)
    spots = [(4,6),(20,14),(36,8),(10,30),(28,36),(42,22)]
    for rx,ry in spots[variant%len(spots):variant%len(spots)+3]:
        pygame.draw.rect(surf,d,(rx,ry,6,4))
    for rx,ry in [(8,10),(24,4),(40,28),(32,18)]:
        pygame.draw.rect(surf,l,(rx,ry,3,6))
    return surf

def make_dark_stone_wall_tile():
    # purple tinted wall for graveyard border
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((55,45,65))
    for y in [16,32]: pygame.draw.line(surf,(38,30,48),(0,y),(TILE_SIZE,y),2)
    for x in [24]:    pygame.draw.line(surf,(38,30,48),(x,0),(x,16),2)
    for x in [12,36]: pygame.draw.line(surf,(38,30,48),(x,16),(x,32),2)
    for x in [24]:    pygame.draw.line(surf,(38,30,48),(x,32),(x,TILE_SIZE),2)
    pygame.draw.rect(surf,(30,22,40),(0,0,2,TILE_SIZE))
    pygame.draw.rect(surf,(30,22,40),(0,0,TILE_SIZE,2))
    pygame.draw.rect(surf,(80,68,92),(TILE_SIZE-2,0,2,TILE_SIZE))
    pygame.draw.rect(surf,(80,68,92),(0,TILE_SIZE-2,TILE_SIZE,2))
    return surf

def make_locked_door_tile():
    # brown door with a keyhole and gold lock plate
    # player needs 2 keys to open the one leading to the boss room
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((120,80,30))
    pygame.draw.rect(surf,(80,50,15),(2,2,TILE_SIZE-4,TILE_SIZE-4),3)
    pygame.draw.circle(surf,(40,25,8),(TILE_SIZE//2,TILE_SIZE//2-4),6)
    pygame.draw.rect(surf,(40,25,8),(TILE_SIZE//2-3,TILE_SIZE//2-2,6,10))
    pygame.draw.rect(surf,(200,165,50),(TILE_SIZE//2-8,TILE_SIZE//2-10,16,18),2)
    return surf

def make_open_door_tile():
    # semi-transparent opening once the door is unlocked
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf,(60,40,15),(0,0,TILE_SIZE,TILE_SIZE),4)
    pygame.draw.rect(surf,(80,60,30,80),(4,4,TILE_SIZE-8,TILE_SIZE-8))
    return surf


# =============================================================================
# character and enemy sprite functions
# all drawn pixel by pixel with rects - no external art assets
# =============================================================================

def make_player_sprite(direction='down', frame=0):
    # green tunic hero with walk animation (2 frames)
    # sword arm position changes based on which direction we're facing
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    skin=(230,185,140); tunic=(60,160,60); pants=(80,60,140)
    hair=(80,50,20); sword_c=(200,200,220); boot=(60,40,20)
    ox,oy = 8,6
    # head
    pygame.draw.rect(surf,skin,(ox+8,oy,16,14))
    pygame.draw.rect(surf,hair,(ox+8,oy,16,4))
    if direction=='up':
        pygame.draw.rect(surf,hair,(ox+8,oy,16,8))   # more hair when facing away
    if direction in ('down','left','right'):
        pygame.draw.rect(surf,(30,30,30),(ox+10,oy+6,3,3))   # eyes
        pygame.draw.rect(surf,(30,30,30),(ox+19,oy+6,3,3))
    # body
    pygame.draw.rect(surf,tunic,(ox+6,oy+14,20,14))
    # legs - alternate which foot is forward for the walk cycle
    lf = 2 if frame==0 else 0; rf = 0 if frame==0 else 2
    pygame.draw.rect(surf,pants,(ox+6,  oy+28+lf,8,8))
    pygame.draw.rect(surf,pants,(ox+18, oy+28+rf,8,8))
    pygame.draw.rect(surf,boot, (ox+6,  oy+34+lf,8,4))
    pygame.draw.rect(surf,boot, (ox+18, oy+34+rf,8,4))
    # sword arm - sticks out in the direction we're facing
    if   direction=='right': pygame.draw.rect(surf,tunic,(ox+26,oy+14,8,8)); pygame.draw.rect(surf,sword_c,(ox+30,oy+4,4,14))
    elif direction=='left':  pygame.draw.rect(surf,tunic,(ox-2, oy+14,8,8)); pygame.draw.rect(surf,sword_c,(ox-2, oy+4,4,14))
    elif direction=='up':    pygame.draw.rect(surf,tunic,(ox+26,oy+14,8,8)); pygame.draw.rect(surf,sword_c,(ox+30,oy+2,4,16))
    else:                    pygame.draw.rect(surf,tunic,(ox+26,oy+14,8,8)); pygame.draw.rect(surf,sword_c,(ox+30,oy+14,4,16))
    return surf

def make_skeleton_sprite(frame=0):
    # skeleton enemy with ribcage and swinging arms
    surf = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
    bone=(220,215,200); dark=(140,130,110); eye=(180,20,20)
    ox,oy=10,4
    pygame.draw.rect(surf,bone,(ox+4,oy,20,18))     # skull
    pygame.draw.rect(surf,eye,(ox+6,oy+6,4,4))
    pygame.draw.rect(surf,eye,(ox+14,oy+6,4,4))
    pygame.draw.rect(surf,dark,(ox+8,oy+14,12,4))   # jaw line
    pygame.draw.rect(surf,bone,(ox+4,oy+18,20,12))  # ribcage
    for rx in [ox+6,ox+12,ox+18]: pygame.draw.rect(surf,dark,(rx,oy+18,2,12))
    # arms swing opposite each other per frame
    anim=2 if frame==0 else -2
    pygame.draw.rect(surf,bone,(ox,   oy+18+anim,6,10))
    pygame.draw.rect(surf,bone,(ox+22,oy+18-anim,6,10))
    pygame.draw.rect(surf,bone,(ox+6, oy+30,6,12))  # legs
    pygame.draw.rect(surf,bone,(ox+16,oy+30,6,12))
    return surf

def make_slime_sprite(frame=0):
    # 8-bit green slime with a bounce animation
    # frame 0 = squished wide, frame 1 = stretched tall
    surf = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
    if frame == 0:
        bx,by,bw,bh = 6,20,36,20   # squished on landing
        ex,ey = 12,24
    else:
        bx,by,bw,bh = 10,14,28,26  # stretched mid-hop
        ex,ey = 14,20

    body   = (40,180,40)
    dark   = (20,130,20)
    shine  = (120,230,120)
    eye_c  = (10,40,10)
    pupils = (0,0,0)

    pygame.draw.rect(surf,body,(bx,by,bw,bh))
    pygame.draw.rect(surf,body,(bx+4,by-4,bw-8,6))   # rounded top
    pygame.draw.rect(surf,body,(bx+8,by-8,bw-16,6))
    pygame.draw.rect(surf,dark,(bx,by+bh-6,bw,6))    # darker underbelly
    pygame.draw.rect(surf,shine,(bx+6,by+2,8,6))      # shine
    pygame.draw.rect(surf,shine,(bx+4,by+2,4,4))
    # eyes
    pygame.draw.rect(surf,(220,240,220),(ex,   ey,8,8))
    pygame.draw.rect(surf,(220,240,220),(ex+14,ey,8,8))
    pygame.draw.rect(surf,pupils,(ex+2,  ey+2,4,4))
    pygame.draw.rect(surf,pupils,(ex+16, ey+2,4,4))
    # little drips at the bottom
    pygame.draw.rect(surf,body,(bx+4, by+bh,4,6))
    pygame.draw.rect(surf,body,(bx+bw-10,by+bh,4,4))
    pygame.draw.ellipse(surf,(0,60,0,60),(bx+4,by+bh+2,bw-8,6))  # shadow
    return surf

def make_skull_sprite(frame=0):
    # floating skull - bobs up and down
    surf = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
    bone=(200,190,175); eye=(220,50,50); dark=(120,110,90)
    ox,oy=8,10
    bob=2 if frame==0 else -2   # vertical bobbing offset
    pygame.draw.rect(surf,bone,(ox+4,oy+bob,24,22))
    pygame.draw.rect(surf,bone,(ox+8,oy+bob+22,16,6))   # jaw
    pygame.draw.rect(surf,eye,(ox+6,oy+bob+6,6,7))
    pygame.draw.rect(surf,eye,(ox+20,oy+bob+6,6,7))
    pygame.draw.rect(surf,dark,(ox+13,oy+bob+14,6,4))   # nose cavity
    pygame.draw.line(surf,dark,(ox+16,oy+bob),(ox+18,oy+bob+8),1)  # crack
    return surf

def make_ash_sprite():
    # grey ash pile left when an enemy dies
    surf = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
    pygame.draw.ellipse(surf,(90,85,80),(8,28,32,12))
    pygame.draw.ellipse(surf,(70,65,60),(12,30,22,7))
    return surf

def make_slime_death_sprite():
    # green goop splat that replaces the slime when it dies
    surf = pygame.Surface((TILE_SIZE,TILE_SIZE),pygame.SRCALPHA)
    pygame.draw.ellipse(surf,(20,130,20,180),(6,30,36,12))
    pygame.draw.ellipse(surf,(40,180,40,160),(10,32,24,7))
    pygame.draw.rect(surf,(20,130,20,140),(4,28,6,8))
    pygame.draw.rect(surf,(20,130,20,140),(36,26,6,10))
    return surf


# =============================================================================
# item sprites
# =============================================================================

def make_heart_sprite():
    # classic 8-bit heart shape built from rectangles
    surf = pygame.Surface((24,24),pygame.SRCALPHA)
    red=(220,50,50)
    pygame.draw.rect(surf,red,(4,2,6,6))
    pygame.draw.rect(surf,red,(14,2,6,6))
    pygame.draw.rect(surf,red,(2,6,20,8))
    pygame.draw.rect(surf,red,(4,14,16,6))
    pygame.draw.rect(surf,red,(8,20,8,2))
    pygame.draw.rect(surf,red,(10,22,4,2))
    pygame.draw.rect(surf,(160,20,20),(4,2,2,2))
    pygame.draw.rect(surf,(160,20,20),(14,2,2,2))
    return surf

def make_half_heart_sprite():
    # left half is full red, right half is dark red (empty)
    # shows up in the hud when hp_float is like 2.5
    surf = pygame.Surface((24,24),pygame.SRCALPHA)
    red=(220,50,50); empty=(80,20,20)
    # draw the empty shape first
    pygame.draw.rect(surf,empty,(4,2,6,6))
    pygame.draw.rect(surf,empty,(14,2,6,6))
    pygame.draw.rect(surf,empty,(2,6,20,8))
    pygame.draw.rect(surf,empty,(4,14,16,6))
    pygame.draw.rect(surf,empty,(8,20,8,2))
    pygame.draw.rect(surf,empty,(10,22,4,2))
    # fill in the left half only
    pygame.draw.rect(surf,red,(4,2,6,6))
    pygame.draw.rect(surf,red,(2,6,10,8))
    pygame.draw.rect(surf,red,(4,14,8,6))
    pygame.draw.rect(surf,red,(8,20,4,2))
    return surf

def make_sword_item_sprite():
    # large floor sword that bobs up and down in the spawn room
    # player has to walk over it to pick it up before they can attack
    surf = pygame.Surface((32,48),pygame.SRCALPHA)
    blade=(200,210,230); shine=(240,245,255); hilt=(200,170,60); grip=(120,80,40)
    pygame.draw.rect(surf,blade,(12,0,8,34))
    pygame.draw.rect(surf,shine,(13,0,3,34))   # shine on the blade
    # pointy tip
    pygame.draw.rect(surf,blade,(13,34,6,4))
    pygame.draw.rect(surf,blade,(14,38,4,3))
    pygame.draw.rect(surf,blade,(15,41,2,2))
    # crossguard
    pygame.draw.rect(surf,hilt,(2,32,28,6))
    pygame.draw.rect(surf,(240,200,80),(4,33,4,4))
    pygame.draw.rect(surf,(240,200,80),(24,33,4,4))
    # grip and pommel
    pygame.draw.rect(surf,grip,(12,38,8,10))
    pygame.draw.rect(surf,(90,60,30),(13,40,2,6))
    pygame.draw.rect(surf,(90,60,30),(17,40,2,6))
    pygame.draw.rect(surf,hilt,(11,44,10,4))
    return surf

def make_sword_upgrade_sprite():
    # gold version of the sword for the upgrade item
    # todo - havent placed this in a room yet, was going to add it somewhere
    surf = pygame.Surface((24,24),pygame.SRCALPHA)
    pygame.draw.rect(surf,(255,215,0),(10,0,4,16))
    pygame.draw.rect(surf,(255,235,80),(11,0,2,16))
    pygame.draw.rect(surf,(200,170,40),(2,14,20,4))
    pygame.draw.rect(surf,(160,120,30),(10,18,4,6))
    return surf

def make_potion_sprite():
    # invisibility potion - purple bottle
    # todo - didnt get to implement the invisibility effect, ran out of time
    surf = pygame.Surface((24,24),pygame.SRCALPHA)
    pygame.draw.rect(surf,(180,80,200),(8,8,8,12))
    pygame.draw.rect(surf,(200,100,220),(6,12,12,6))
    pygame.draw.rect(surf,(220,180,240),(9,10,4,4))
    pygame.draw.rect(surf,(140,60,160),(10,2,4,8))
    pygame.draw.rect(surf,(180,160,80),(8,0,8,4))
    return surf

def make_key_sprite():
    # gold key - one in the overworld (bottom left), one in the graveyard (top left)
    # need both to unlock the boss door
    surf = pygame.Surface((28,28),pygame.SRCALPHA)
    gold=(220,185,50); dark=(140,110,20); shine=(255,230,100)
    pygame.draw.circle(surf,gold,(10,10),8)
    pygame.draw.circle(surf,(0,0,0,0),(10,10),5)   # hollow ring
    pygame.draw.circle(surf,gold,(10,10),8,3)
    pygame.draw.circle(surf,dark,(10,10),8,1)
    pygame.draw.circle(surf,shine,(7,7),3)          # shine
    pygame.draw.rect(surf,gold,(14,8,14,4))         # shaft
    pygame.draw.rect(surf,gold,(20,12,4,4))         # teeth
    pygame.draw.rect(surf,gold,(26,12,2,4))
    pygame.draw.rect(surf,dark,(14,8,14,1))
    return surf


# =============================================================================
# class: Tile
# single tile on the map grid - knows its type, whether its solid, and how to draw
# =============================================================================
class Tile(pygame.sprite.Sprite):
    # tile code lookup - maps integer codes from the grid arrays to properties
    TILE_DEFS = {
        0:  {'name':'floor',          'solid':False, 'make': lambda: make_grass_tile(0)},
        1:  {'name':'wall',           'solid':True,  'make': make_wall_tile},
        2:  {'name':'water',          'solid':True,  'make': make_water_tile},
        3:  {'name':'path',           'solid':False, 'make': make_path_tile},
        4:  {'name':'stone_wall',     'solid':True,  'make': make_stone_wall_tile},
        5:  {'name':'tree',           'solid':False, 'make': make_tree_tile},        # decorative only
        6:  {'name':'locked_door',    'solid':False, 'make': make_locked_door_tile}, # not solid - exit logic handles blocking
        7:  {'name':'open_door',      'solid':False, 'make': make_open_door_tile},
        8:  {'name':'grass2',         'solid':False, 'make': lambda: make_grass_tile(1)},
        9:  {'name':'grass3',         'solid':False, 'make': lambda: make_grass_tile(2)},
        10: {'name':'purple_grass',   'solid':False, 'make': lambda: make_purple_grass_tile(0)},
        11: {'name':'purple_grass2',  'solid':False, 'make': lambda: make_purple_grass_tile(1)},
        12: {'name':'purple_grass3',  'solid':False, 'make': lambda: make_purple_grass_tile(2)},
        13: {'name':'dead_tree',      'solid':False, 'make': make_dead_tree_tile},   # decorative
        14: {'name':'dark_stone_wall','solid':True,  'make': make_dark_stone_wall_tile},
    }
    _cache = {}  # shared across all tiles so we only make each surface once

    def __init__(self, grid_x, grid_y, tile_code, world_offset_x=0, world_offset_y=0):
        super().__init__()
        td = Tile.TILE_DEFS.get(tile_code, Tile.TILE_DEFS[0])
        self.tile_type = td['name']
        self.solid     = td['solid']
        self.world_x   = grid_x * TILE_SIZE + world_offset_x
        self.world_y   = grid_y * TILE_SIZE + world_offset_y
        self.rect      = pygame.Rect(self.world_x, self.world_y, TILE_SIZE, TILE_SIZE)
        # cache the surface so we dont redraw the same tile over and over
        if tile_code not in Tile._cache:
            Tile._cache[tile_code] = td['make']()
        self.image = Tile._cache[tile_code]

    def draw(self, surface, camera_x=0, camera_y=0):
        surface.blit(self.image, (self.world_x - camera_x, self.world_y - camera_y))

    def screen_rect(self, camera_x=0, camera_y=0):
        return pygame.Rect(self.world_x-camera_x, self.world_y-camera_y, TILE_SIZE, TILE_SIZE)


# =============================================================================
# class: Player
# the main character - handles movement, combat, health, and drawing
# =============================================================================
class Player(pygame.sprite.Sprite):
    ATTACK_FRAMES = 20

    def __init__(self, x, y, assets):
        super().__init__()
        # hitbox is slightly smaller than tile size so corners dont snag on walls
        self.rect  = pygame.Rect(x, y, TILE_SIZE-4, TILE_SIZE-4)

        # stats
        self.hp_float     = 3.0   # single float for health - avoids rounding bugs with half-hearts
        self.max_hp       = 3
        self.sword_damage = 1     # becomes 2 if sword upgrade is collected
        self.has_upgrade  = False
        self.has_sword    = False  # player starts unarmed, sword is in the spawn room
        self.keys         = 0     # collected keys, max 2

        # movement
        self.speed        = 3
        self.direction    = 'down'

        # combat state
        self.is_attacking     = False
        self.attack_timer     = 0    # counts down from ATTACK_FRAMES per swing
        self.invincible       = False
        self.invincible_timer = 0    # 90 frames = 1.5 seconds of iframes after getting hit

        # animation state
        self._walk_timer  = 0
        self._walk_frame  = 0
        self._moving      = False

        # pre-build all 8 sprites (4 directions x 2 walk frames)
        self._sprites = {(d,f): make_player_sprite(d,f)
                         for d in ('up','down','left','right') for f in (0,1)}
        self.image = self._sprites[('down',0)]

    # hp and hp_frac are computed properties so the hud always has correct values
    @property
    def hp(self):
        return math.ceil(self.hp_float)   # integer hearts for game-over checks

    @property
    def hp_frac(self):
        # fractional part - 0.5 means a half heart is showing in the hud
        f = self.hp_float % 1.0
        return round(f, 6)

    def move(self, dx, dy, tiles):
        self._moving = True
        # move x axis first, resolve collisions, then y axis
        # doing them separately prevents getting stuck in corners
        self.rect.x += dx
        for t in tiles:
            if t.solid and self.rect.colliderect(t.rect):
                if dx > 0: self.rect.right  = t.rect.left
                if dx < 0: self.rect.left   = t.rect.right
        self.rect.y += dy
        for t in tiles:
            if t.solid and self.rect.colliderect(t.rect):
                if dy > 0: self.rect.bottom = t.rect.top
                if dy < 0: self.rect.top    = t.rect.bottom
        # update facing direction
        if   dx > 0: self.direction = 'right'
        elif dx < 0: self.direction = 'left'
        elif dy > 0: self.direction = 'down'
        elif dy < 0: self.direction = 'up'

    def attack(self):
        # cant swing if already mid-swing or no sword
        if self.is_attacking or not self.has_sword: return None
        self.is_attacking = True; self.attack_timer = self.ATTACK_FRAMES
        # return a hitbox rect one tile in front of the player
        ox,oy = {'right':(self.rect.right,self.rect.y),
                 'left': (self.rect.left-TILE_SIZE,self.rect.y),
                 'down': (self.rect.x,self.rect.bottom),
                 'up':   (self.rect.x,self.rect.top-TILE_SIZE)}[self.direction]
        return pygame.Rect(ox,oy,TILE_SIZE,TILE_SIZE)

    def take_damage(self, amount):
        # skip if still in the invincibility window from a previous hit
        if self.invincible: return
        self.hp_float = max(self.hp_float - amount, 0.0)
        # start invincibility frames so you dont take rapid damage
        self.invincible = True; self.invincible_timer = 90

    def heal(self, amount):
        self.hp_float = min(self.hp_float + amount, float(self.max_hp))

    def apply_upgrade(self):
        # called when sword upgrade item is collected
        self.has_upgrade = True; self.sword_damage = 2

    def update(self):
        # tick down attack and invincibility timers
        if self.is_attacking:
            self.attack_timer -= 1
            if self.attack_timer <= 0: self.is_attacking = False
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0: self.invincible = False
        # advance walk animation every 10 frames while moving
        if self._moving:
            self._walk_timer += 1
            if self._walk_timer >= 10:
                self._walk_timer = 0; self._walk_frame = 1-self._walk_frame
        else:
            self._walk_frame = 0; self._walk_timer = 0
        self.image   = self._sprites[(self.direction, self._walk_frame)]
        self._moving = False   # reset each frame, handle_input sets it again if moving

    def draw(self, surface, camera_x=0, camera_y=0):
        # blink during invincibility frames (skip drawing every other few frames)
        if self.invincible and self.invincible_timer % 6 < 3: return
        surface.blit(self.image, (self.rect.x-camera_x, self.rect.y-camera_y))

    def draw_attack(self, surface, camera_x=0, camera_y=0):
        # draw the sword pivoting from the player's hand into the attack tile
        if not self.is_attacking: return
        progress = 1.0 - (self.attack_timer / self.ATTACK_FRAMES)
        eased = 0.5 - 0.5 * math.cos(progress * math.pi)
        hand_x, hand_y, start_angle, end_angle = {
            'right': (self.rect.right,      self.rect.y + 20, -65, 45),
            'left':  (self.rect.left,       self.rect.y + 20, 245, 135),
            'down':  (self.rect.x + 38,     self.rect.bottom, 25, 115),
            'up':    (self.rect.x + 38,     self.rect.y + 8,  335, 225),
        }[self.direction]
        angle = math.radians(start_angle + (end_angle - start_angle) * eased)

        hand = (hand_x - camera_x, hand_y - camera_y)
        blade_len = TILE_SIZE - 8
        grip_len = 8
        tip = (round(hand[0] + math.cos(angle) * blade_len),
               round(hand[1] + math.sin(angle) * blade_len))
        pommel = (round(hand[0] - math.cos(angle) * grip_len),
                  round(hand[1] - math.sin(angle) * grip_len))

        pygame.draw.line(surface,(120,80,35),pommel,hand,6)
        pygame.draw.line(surface,(210,210,230),hand,tip,6)
        pygame.draw.line(surface,(245,250,255),hand,tip,2)
        guard_angle = angle + math.pi / 2
        guard_a = (round(hand[0] + math.cos(guard_angle) * 8),
                   round(hand[1] + math.sin(guard_angle) * 8))
        guard_b = (round(hand[0] - math.cos(guard_angle) * 8),
                   round(hand[1] - math.sin(guard_angle) * 8))
        pygame.draw.line(surface,(205,170,60),guard_a,guard_b,4)


# =============================================================================
# class: Enemy
# base skeleton/skull enemy used in single-screen rooms
# =============================================================================
class Enemy(pygame.sprite.Sprite):

    def __init__(self, x, y, enemy_type, assets, patrol_path=None):
        super().__init__()
        self.rect        = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self._x          = float(x)
        self._y          = float(y)
        self.enemy_type  = enemy_type
        self.hp          = 3
        self.damage      = 1
        self.speed       = 1
        self.state       = 'patrol'   # patrol | chase | ash
        self.patrol_path = patrol_path or []
        self.patrol_index= 0
        self._anim_timer = 0; self._anim_frame = 0
        self._ash        = make_ash_sprite()
        if enemy_type == 'skeleton':
            self._sprites = [make_skeleton_sprite(0), make_skeleton_sprite(1)]
        else:
            self._sprites = [make_skull_sprite(0), make_skull_sprite(1)]
        self.image = self._sprites[0]

    def update(self, player):
        if self.state == 'ash': return
        # advance animation
        self._anim_timer += 1
        if self._anim_timer >= 20:
            self._anim_timer = 0; self._anim_frame = 1-self._anim_frame
        self.image = self._sprites[self._anim_frame]
        # switch to chase if player is within 200 pixels
        dx = player.rect.centerx-self.rect.centerx
        dy = player.rect.centery-self.rect.centery
        dist = (dx**2+dy**2)**0.5
        self.state = 'chase' if dist < 200 else 'patrol'
        if self.state=='chase': self._chase(player)
        else: self._patrol()

    def _patrol(self):
        if not self.patrol_path: return
        tx,ty = self.patrol_path[self.patrol_index]
        dx,dy = tx-self._x, ty-self._y
        dist  = (dx**2+dy**2)**0.5
        if dist < self.speed:
            self.patrol_index = (self.patrol_index+1)%len(self.patrol_path)
        else:
            self._x += self.speed*dx/dist
            self._y += self.speed*dy/dist
            self.rect.x = round(self._x)
            self.rect.y = round(self._y)

    def _chase(self, player):
        dx=player.rect.centerx-(self._x + self.rect.width/2)
        dy=player.rect.centery-(self._y + self.rect.height/2)
        dist=(dx**2+dy**2)**0.5
        if dist>0:
            self._x+=self.speed*dx/dist
            self._y+=self.speed*dy/dist
            self.rect.x=round(self._x)
            self.rect.y=round(self._y)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0: self.hp=0; self.state='ash'

    def drop_loot(self):
        return 'heart' if random.random()<0.5 else None

    def draw(self, surface, camera_x=0, camera_y=0):
        sx=self.rect.x-camera_x; sy=self.rect.y-camera_y
        surface.blit(self._ash if self.state=='ash' else self.image, (sx,sy))


# =============================================================================
# class: Slime
# green slime enemy in the overworld - slow hop movement, half-heart damage
# takes 2 hits to kill, 25% drop chance
# =============================================================================
class Slime(pygame.sprite.Sprite):
    DETECT_RADIUS = 160   # pixels before it starts chasing

    def __init__(self, x, y):
        super().__init__()
        self.rect    = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hp      = 2
        self.damage  = 0.5    # half heart per hit
        self.speed   = 0.8    # slow and steady
        self.state   = 'idle'
        self._timer  = 0; self._frame = 0
        self._death  = make_slime_death_sprite()
        self._sprites= [make_slime_sprite(0), make_slime_sprite(1)]
        self.image   = self._sprites[0]
        self._drift_angle = random.uniform(0, math.pi*2)
        self._drift_timer = 0
        self._hop_timer   = 0   # only moves on hop frames so it looks like actual hopping

    def update(self, player):
        if self.state == 'ash': return
        # advance hop animation - slower than other enemies
        self._hop_timer += 1
        if self._hop_timer >= 30:
            self._hop_timer = 0
            self._frame = 1-self._frame
        self._timer += 1
        if self._timer >= 30:
            self._timer = 0
        self.image = self._sprites[self._frame]

        dx = player.rect.centerx-self.rect.centerx
        dy = player.rect.centery-self.rect.centery
        dist = (dx**2+dy**2)**0.5
        if dist < self.DETECT_RADIUS:
            self.state = 'chase'
        if self.state == 'chase':
            # only actually move on hop frames so it looks like hopping not gliding
            if dist > 0 and self._hop_timer == 0:
                self.rect.x += int(self.speed*dx/dist*6)
                self.rect.y += int(self.speed*dy/dist*6)
        else:
            # wander around randomly when the player is far away
            self._drift_timer += 1
            if self._drift_timer > 90:
                self._drift_timer = 0
                self._drift_angle += random.uniform(-0.8,0.8)
            if self._hop_timer == 0:
                self.rect.x += int(math.cos(self._drift_angle)*4)
                self.rect.y += int(math.sin(self._drift_angle)*4)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0: self.hp=0; self.state='ash'

    def drop_loot(self):
        return 'heart' if random.random()<0.25 else None   # 25% chance

    def draw(self, surface, camera_x=0, camera_y=0):
        sx=self.rect.x-camera_x; sy=self.rect.y-camera_y
        surface.blit(self._death if self.state=='ash' else self.image, (sx,sy))


# =============================================================================
# class: GraveyardSkeleton
# skeleton enemy in the graveyard scrolling area
# same behavior as slime but uses skeleton sprites - 3 hits, half-heart damage
# =============================================================================
class GraveyardSkeleton(pygame.sprite.Sprite):
    DETECT_RADIUS = 160

    def __init__(self, x, y):
        super().__init__()
        self.rect    = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hp      = 3     # takes 3 sword hits to kill - harder than slimes
        self.damage  = 0.5   # still half a heart per hit though
        self.speed   = 0.8
        self.state   = 'idle'
        self._timer  = 0; self._frame = 0
        self._ash    = make_ash_sprite()
        self._sprites= [make_skeleton_sprite(0), make_skeleton_sprite(1)]
        self.image   = self._sprites[0]
        self._drift_angle = random.uniform(0, math.pi*2)
        self._drift_timer = 0
        self._step_timer  = 0

    def update(self, player):
        if self.state == 'ash': return
        self._step_timer += 1
        if self._step_timer >= 25:
            self._step_timer = 0; self._frame = 1-self._frame
        self.image = self._sprites[self._frame]
        dx = player.rect.centerx-self.rect.centerx
        dy = player.rect.centery-self.rect.centery
        dist = (dx**2+dy**2)**0.5
        if dist < self.DETECT_RADIUS: self.state = 'chase'
        if self.state == 'chase':
            if dist > 0 and self._step_timer == 0:
                self.rect.x += int(self.speed*dx/dist*5)
                self.rect.y += int(self.speed*dy/dist*5)
        else:
            self._drift_timer += 1
            if self._drift_timer > 80:
                self._drift_timer = 0
                self._drift_angle += random.uniform(-0.8,0.8)
            if self._step_timer == 0:
                self.rect.x += int(math.cos(self._drift_angle)*3)
                self.rect.y += int(math.sin(self._drift_angle)*3)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0: self.hp=0; self.state='ash'

    def drop_loot(self):
        return 'heart' if random.random()<0.25 else None   # 25% chance

    def draw(self, surface, camera_x=0, camera_y=0):
        sx=self.rect.x-camera_x; sy=self.rect.y-camera_y
        surface.blit(self._ash if self.state=='ash' else self.image, (sx,sy))


# =============================================================================
# class: Item
# collectible objects - hearts, sword, keys, etc.
# sword and key bob up and down using a sine wave
# =============================================================================
class Item(pygame.sprite.Sprite):
    _makers = {
        'heart':         make_heart_sprite,
        'sword_upgrade': make_sword_upgrade_sprite,
        'potion':        make_potion_sprite,
        'sword':         make_sword_item_sprite,
        'key':           make_key_sprite,
    }

    def __init__(self, x, y, item_type):
        super().__init__()
        self.item_type = item_type
        self.image     = self._makers.get(item_type, make_heart_sprite)()
        w,h = self.image.get_size()
        self.rect      = pygame.Rect(x, y, w, h)
        self.collected = False
        self._bob_timer= 0; self._base_y = y

    def update(self):
        # bob animation for sword and key to make them look more inviting
        if self.item_type in ('sword','key'):
            self._bob_timer += 1
            self.rect.y = self._base_y + int(4*abs(math.sin(self._bob_timer*0.05)))

    def draw(self, surface, camera_x=0, camera_y=0):
        if not self.collected:
            surface.blit(self.image,(self.rect.x-camera_x, self.rect.y-camera_y))


# =============================================================================
# class: HUD
# heads up display - hearts, keys, sword icon
# drawn on top of everything else each frame
# =============================================================================
class HUD:

    def __init__(self, player):
        self._sync(player)
        self._font      = pygame.font.SysFont(None, 20)
        self._key_img   = make_key_sprite()
        self._heart_full= make_heart_sprite()
        self._heart_half= make_half_heart_sprite()
        self._heart_empty_surf = self._make_empty_heart()

    def _make_empty_heart(self):
        # dark red empty heart outline
        surf = pygame.Surface((24,24), pygame.SRCALPHA)
        empty=(80,20,20); outline=(130,30,30)
        pygame.draw.rect(surf,empty,(4,2,6,6))
        pygame.draw.rect(surf,empty,(14,2,6,6))
        pygame.draw.rect(surf,empty,(2,6,20,8))
        pygame.draw.rect(surf,empty,(4,14,16,6))
        pygame.draw.rect(surf,empty,(8,20,8,2))
        pygame.draw.rect(surf,empty,(10,22,4,2))
        pygame.draw.rect(surf,outline,(4,2,2,2))
        pygame.draw.rect(surf,outline,(14,2,2,2))
        return surf

    def _sync(self, p):
        self.hp_float=p.hp_float; self.max_hp=p.max_hp
        self.has_upgrade=p.has_upgrade; self.has_sword=p.has_sword; self.keys=p.keys

    def update(self, player): self._sync(player)

    def draw(self, surface):
        # semi-transparent dark bar behind the hud
        bar = pygame.Surface((SCREEN_W, HUD_H), pygame.SRCALPHA)
        bar.fill((0,0,0,130))
        surface.blit(bar,(0,0))

        # hearts - check hp_float to decide full/half/empty per slot
        # slot i is full if hp_float >= i+1, half if >= i+0.5, empty otherwise
        hs=28; hm=6
        for i in range(self.max_hp):
            hx = 12 + i*(hs+hm); hy = 12
            if self.hp_float >= i + 1.0:
                surface.blit(self._heart_full,(hx,hy))
            elif self.hp_float >= i + 0.5:
                surface.blit(self._heart_half,(hx,hy))
            else:
                surface.blit(self._heart_empty_surf,(hx,hy))

        # key slots in the center - shows how many keys have been collected
        for i in range(2):
            kx = SCREEN_W//2 - 30 + i*34; ky = 12
            if i < self.keys:
                surface.blit(self._key_img,(kx,ky))
            else:
                # empty slot with a question mark
                pygame.draw.rect(surface,(50,45,35),(kx,ky,28,28),1)
                empty=self._font.render("?",True,(60,55,45))
                surface.blit(empty,(kx+9,ky+7))

        # sword icon on the right - turns gold when upgraded
        if self.has_sword:
            sx=SCREEN_W-52; sy=8
            bc=(255,215,0) if self.has_upgrade else (200,210,230)
            pygame.draw.rect(surface,bc,(sx+10,sy,8,26))
            pygame.draw.rect(surface,(240,245,255),(sx+11,sy,3,26))
            pygame.draw.rect(surface,(160,120,50),(sx,sy+26,28,5))
            pygame.draw.rect(surface,(120,80,30),(sx+10,sy+31,8,9))
        else:
            # empty slot before sword is picked up
            pygame.draw.rect(surface,(60,60,60),(SCREEN_W-52,8,28,40),1)
            lbl=self._font.render("?",True,(80,80,80))
            surface.blit(lbl,(SCREEN_W-42,18))


# =============================================================================
# room system
# Room = single screen, ScrollRoom = large scrolling area with camera
# =============================================================================

COLS = 16; ROWS = 11
MAP_OFFSET_X = (SCREEN_W - COLS*TILE_SIZE)//2   # centers the 16-tile map horizontally
MAP_OFFSET_Y = HUD_H                             # starts below the hud bar

EXIT_NONE=0; EXIT_NORTH=1; EXIT_SOUTH=2; EXIT_EAST=4; EXIT_WEST=8


# =============================================================================
# class: Room
# fixed single-screen room - 16x11 tiles
# =============================================================================
class Room:
    def __init__(self, room_id, grid, exits=EXIT_NONE, items=None,
                 enemies=None, next_rooms=None, locked_exits=None, is_win_room=False):
        self.room_id      = room_id
        self.exits        = exits
        self.items        = items       or []
        self.enemies      = enemies     or []
        self.next_rooms   = next_rooms  or {}
        self.locked_exits = locked_exits or set()
        self.is_win_room  = is_win_room  # set to true for the boss room
        self.tiles        = []
        self._build_tiles(grid)

    def _build_tiles(self, grid):
        for r,row in enumerate(grid):
            for c,code in enumerate(row):
                self.tiles.append(Tile(c, r, code, MAP_OFFSET_X, MAP_OFFSET_Y))

    def get_exit_rects(self):
        # exit trigger rects overlap the wall row so the player can reach them
        # even when the wall tiles are solid - had a lot of trouble with this
        rects={}
        w=COLS*TILE_SIZE; h=ROWS*TILE_SIZE
        ox=MAP_OFFSET_X;  oy=MAP_OFFSET_Y
        if self.exits&EXIT_NORTH: rects['north']=pygame.Rect(ox+w//2-TILE_SIZE, oy,             TILE_SIZE*2, TILE_SIZE)
        if self.exits&EXIT_SOUTH: rects['south']=pygame.Rect(ox+w//2-TILE_SIZE, oy+h-TILE_SIZE, TILE_SIZE*2, TILE_SIZE)
        if self.exits&EXIT_EAST:  rects['east'] =pygame.Rect(ox+w-TILE_SIZE,    oy+h//2-TILE_SIZE, TILE_SIZE, TILE_SIZE*2)
        if self.exits&EXIT_WEST:  rects['west'] =pygame.Rect(ox,                oy+h//2-TILE_SIZE, TILE_SIZE, TILE_SIZE*2)
        return rects

    def draw(self, surface, camera_x=0, camera_y=0):
        for t in self.tiles:   t.draw(surface)
        for it in self.items:  it.draw(surface)
        for en in self.enemies: en.draw(surface)

    def update(self, player):
        for it in self.items:   it.update()
        for en in self.enemies: en.update(player)


# =============================================================================
# class: ScrollRoom
# large scrolling world area - camera follows the player
# viewport is SCREEN_W x (SCREEN_H - HUD_H)
# =============================================================================
class ScrollRoom:
    VIEWPORT_W = SCREEN_W
    VIEWPORT_H = SCREEN_H - HUD_H

    def __init__(self, room_id, grid, items=None, enemies=None,
                 next_rooms=None, locked_exits=None, exits=EXIT_NONE, bg_color=None):
        self.room_id      = room_id
        self.items        = items       or []
        self.enemies      = enemies     or []
        self.next_rooms   = next_rooms  or {}
        self.locked_exits = locked_exits or set()
        self.exits        = exits
        self._bg_color    = bg_color or (34,120,34)  # fill color between tiles - match the floor
        self.tiles        = []
        self.cols         = len(grid[0]) if grid else 0
        self.rows         = len(grid)
        self.world_w      = self.cols * TILE_SIZE
        self.world_h      = self.rows * TILE_SIZE
        self.explored_tiles = set()
        self._build_tiles(grid)
        self.cam_x = 0; self.cam_y = 0

    def _build_tiles(self, grid):
        for r,row in enumerate(grid):
            for c,code in enumerate(row):
                self.tiles.append(Tile(c, r, code, 0, 0))

    def update_camera(self, player):
        # center camera on player, clamped so we never show outside the world
        self.cam_x = max(0, min(player.rect.centerx - self.VIEWPORT_W//2,
                                self.world_w - self.VIEWPORT_W))
        self.cam_y = max(0, min(player.rect.centery - self.VIEWPORT_H//2,
                                self.world_h - self.VIEWPORT_H))
        self._mark_visible_tiles_explored()

    def _mark_visible_tiles_explored(self):
        start_col = max(0, self.cam_x // TILE_SIZE)
        end_col = min(self.cols, (self.cam_x + self.VIEWPORT_W) // TILE_SIZE + 2)
        start_row = max(0, self.cam_y // TILE_SIZE)
        end_row = min(self.rows, (self.cam_y + self.VIEWPORT_H) // TILE_SIZE + 2)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                self.explored_tiles.add((col, row))

    def get_exit_rects(self):
        # exit rects in world space - placed one tile inward so the player can reach them
        rects={}
        wmid=self.world_w//2; hmid=self.world_h//2
        if self.exits&EXIT_NORTH: rects['north']=pygame.Rect(wmid-TILE_SIZE,0,TILE_SIZE*2,TILE_SIZE)
        if self.exits&EXIT_SOUTH: rects['south']=pygame.Rect(wmid-TILE_SIZE,self.world_h-TILE_SIZE,TILE_SIZE*2,TILE_SIZE)
        if self.exits&EXIT_EAST:  rects['east'] =pygame.Rect(self.world_w-TILE_SIZE,hmid-TILE_SIZE,TILE_SIZE,TILE_SIZE*2)
        if self.exits&EXIT_WEST:  rects['west'] =pygame.Rect(0,hmid-TILE_SIZE,TILE_SIZE,TILE_SIZE*2)
        return rects

    def draw(self, surface):
        cx=self.cam_x; cy=self.cam_y
        # expand the cull rect by one tile on each side to prevent tiles popping in at edges
        vp = pygame.Rect(cx - TILE_SIZE, cy - TILE_SIZE,
                         self.VIEWPORT_W + TILE_SIZE*2, self.VIEWPORT_H + TILE_SIZE*2)
        # fill viewport with floor color first so there are no gaps between tiles
        surface.fill(self._bg_color, pygame.Rect(0, HUD_H, self.VIEWPORT_W, self.VIEWPORT_H))
        for t in self.tiles:
            if vp.colliderect(t.rect):
                sx = t.world_x - cx
                sy = t.world_y - cy + HUD_H
                surface.blit(t.image, (sx, sy))
        for it in self.items:
            if not it.collected and vp.colliderect(it.rect):
                sx = it.rect.x - cx
                sy = it.rect.y - cy + HUD_H
                surface.blit(it.image, (sx, sy))
        for en in self.enemies:
            if vp.colliderect(en.rect):
                sx = en.rect.x - cx
                sy = en.rect.y - cy + HUD_H
                if en.state == 'ash':
                    surface.blit(en._death if hasattr(en,'_death') else en._ash, (sx,sy))
                else:
                    surface.blit(en.image, (sx,sy))

    def update(self, player):
        self.update_camera(player)
        for it in self.items:   it.update()
        for en in self.enemies: en.update(player)


# =============================================================================
# room grid builder helper
# wraps an inner grid with a wall border and cuts exits/locked doors where needed
# wall_code lets graveyard use dark stone instead of regular stone
# =============================================================================
def _wall_border(inner, north_open=False, south_open=False,
                 east_open=False, west_open=False,
                 north_locked=False, south_locked=False,
                 east_locked=False, west_locked=False,
                 wall_code=1):
    rows=ROWS; cols=COLS
    mlo=cols//2-1; mhi=cols//2    # center column range for north/south exits
    rlo=rows//2-1; rhi=rows//2    # center row range for east/west exits
    grid=[]
    for r in range(rows):
        row=[]
        for c in range(cols):
            is_corner = (r in (0,rows-1)) and (c in (0,cols-1))
            top=r==0; bot=r==rows-1; lft=c==0; rgt=c==cols-1
            if is_corner:
                row.append(wall_code)
            elif top:
                if   north_open   and mlo<=c<=mhi: row.append(0)
                elif north_locked and mlo<=c<=mhi: row.append(6)   # locked door tile
                else:                              row.append(wall_code)
            elif bot:
                if   south_open   and mlo<=c<=mhi: row.append(0)
                elif south_locked and mlo<=c<=mhi: row.append(6)
                else:                              row.append(wall_code)
            elif lft:
                if   west_open   and rlo<=r<=rhi: row.append(0)
                elif west_locked and rlo<=r<=rhi: row.append(6)
                else:                             row.append(wall_code)
            elif rgt:
                if   east_open   and rlo<=r<=rhi: row.append(0)
                elif east_locked and rlo<=r<=rhi: row.append(6)
                else:                             row.append(wall_code)
            else:
                ir=r-1; ic=c-1
                row.append(inner[ir][ic] if ir<len(inner) and ic<len(inner[0]) else 0)
        grid.append(row)
    return grid


# =============================================================================
# room builders
# each function builds one room with its tiles, items, and enemy list
# =============================================================================

def build_spawn_room():
    # starting room - sword at the bottom, exits left (overworld) and right (graveyard)
    # north exit is locked and requires both keys to open - leads to boss room
    inner=[[0]*14 for _ in range(10)]
    inner[7][6]=inner[7][7]=inner[8][6]=inner[8][7]=3   # dirt path under the sword
    grid = _wall_border(inner, north_locked=True, east_open=True, west_open=True)
    sword_x = MAP_OFFSET_X + (COLS//2)*TILE_SIZE - 16
    sword_y = MAP_OFFSET_Y + (ROWS-3)*TILE_SIZE
    sword = Item(sword_x, sword_y, 'sword')
    return Room('spawn', grid,
                exits=EXIT_NORTH|EXIT_EAST|EXIT_WEST,
                items=[sword],
                locked_exits={'north'},
                next_rooms={'north':'boss_room','east':'graveyard','west':'overworld'})

def build_boss_room():
    # placeholder for the boss fight - just shows YOU WIN for now
    # todo: implement the actual boss fight here (see bottom of file)
    inner=[[0]*14 for _ in range(10)]
    grid = _wall_border(inner, south_open=True)
    return Room('boss_room', grid,
                exits=EXIT_SOUTH,
                next_rooms={'south':'spawn'},
                is_win_room=True)

# these rooms were removed from the game layout but keeping the builders
# in case i want to add them back as side areas later
def build_forest_room():
    inner=[[0]*14 for _ in range(10)]
    for pos in [(1,1),(2,1),(1,2),(10,1),(11,1),(10,2),(4,4),(8,4),(3,6),(9,6)]:
        c,r=pos; inner[r][c]=1
    grid = _wall_border(inner, south_open=True, east_open=True, west_open=True)
    return Room('forest', grid,
                exits=EXIT_SOUTH|EXIT_EAST|EXIT_WEST,
                next_rooms={'south':'spawn','east':'graveyard','west':'overworld'})

def build_plains_room():
    inner=[[0]*14 for _ in range(10)]
    for r,c in [(2,2),(2,3),(2,4),(3,2),(3,3),(4,2)]: inner[r][c]=2
    grid = _wall_border(inner, east_open=True)
    return Room('plains', grid, exits=EXIT_EAST, next_rooms={'east':'spawn'})

def build_cave_entrance_room():
    inner=[[0]*14 for _ in range(10)]
    for r in range(2,8): inner[r][7]=inner[r][6]=3
    for pos in [(4,2),(11,2),(4,4),(11,4),(4,6),(11,6)]:
        c,r=pos; inner[r][c]=1
    grid = _wall_border(inner, west_open=True)
    return Room('cave_entrance', grid, exits=EXIT_WEST, next_rooms={'west':'spawn'})


# overworld - scrolling grassland to the left of spawn (48x32 tiles)
OW_COLS = 48; OW_ROWS = 32

def _ow_grid():
    import random as _r; _r.seed(42)   # fixed seed = same layout every run
    g=[[0]*OW_COLS for _ in range(OW_ROWS)]
    # solid stone border around the whole map
    for c in range(OW_COLS): g[0][c]=4; g[OW_ROWS-1][c]=4
    for r in range(OW_ROWS): g[r][0]=4; g[r][OW_COLS-1]=4
    # east exit gap (mid rows) - leads back to spawn room
    mid_r=OW_ROWS//2
    g[mid_r-1][OW_COLS-1]=0; g[mid_r][OW_COLS-1]=0
    # stone wall clusters scattered around for obstacles
    for wc,wr in [(4,4),(4,5),(5,4),(10,8),(10,9),(11,8),(6,18),(7,18),(6,19),
                  (20,6),(21,6),(20,7),(30,14),(31,14),(30,15),(38,4),(39,4),
                  (14,24),(15,24),(14,25),(25,20),(26,20),(25,21),(26,21),
                  (35,26),(36,26),(35,27),(42,20),(43,20),(42,21),(8,28),(9,28),(18,28)]:
        if 1<=wr<OW_ROWS-1 and 1<=wc<OW_COLS-1: g[wr][wc]=4
    # decorative trees - no collision
    for tc,tr in [(3,3),(3,7),(7,3),(12,2),(16,5),(22,3),(28,2),(34,3),(40,2),(44,5),
                  (2,12),(7,15),(13,12),(19,14),(24,11),(30,8),(36,11),(42,8),(46,12),
                  (2,20),(6,22),(11,20),(17,22),(23,19),(29,22),(36,19),(41,22),(45,20),
                  (3,28),(8,26),(13,29),(19,26),(23,28),(28,25),(33,28),(38,25),(43,28)]:
        if 1<=tr<OW_ROWS-1 and 1<=tc<OW_COLS-1 and g[tr][tc]==0: g[tr][tc]=5
    # random grass variation so it doesnt look like a flat color
    for r in range(1,OW_ROWS-1):
        for c in range(1,OW_COLS-1):
            if g[r][c]==0 and _r.random()<0.25:
                g[r][c]=8 if _r.random()<0.5 else 9
    return g

def build_overworld():
    grid = _ow_grid()
    # key is hidden in the bottom left corner - player has to explore to find it
    key_item = Item(3*TILE_SIZE+TILE_SIZE//2, (OW_ROWS-4)*TILE_SIZE, 'key')
    slimes=[]
    import random as _r2; _r2.seed(7)
    for ec,er in [(8,6),(15,10),(22,8),(30,6),(38,8),
                  (5,15),(12,18),(20,16),(28,14),(36,17),(44,15),
                  (7,22),(14,25),(21,23),(29,20),(37,24),(44,22),
                  (10,28),(18,27),(26,29),(33,26),(40,28)]:
        if 2<=er<OW_ROWS-2 and 2<=ec<OW_COLS-2 and grid[er][ec] not in (1,4,5):
            slimes.append(Slime(ec*TILE_SIZE, er*TILE_SIZE))
    return ScrollRoom('overworld', grid,
                      items=[key_item], enemies=slimes,
                      exits=EXIT_EAST,
                      next_rooms={'east':'spawn'},
                      bg_color=(34,120,34))


# graveyard - spooky scrolling area to the right of spawn (48x32 tiles)
GY_COLS = 48; GY_ROWS = 32

def _gy_grid():
    import random as _r; _r.seed(99)
    g=[[10]*GY_COLS for _ in range(GY_ROWS)]   # base is purple grass (code 10)
    # dark stone border
    for c in range(GY_COLS): g[0][c]=14; g[GY_ROWS-1][c]=14
    for r in range(GY_ROWS): g[r][0]=14; g[r][GY_COLS-1]=14
    # west exit gap - leads back to spawn
    mid_r=GY_ROWS//2
    g[mid_r-1][0]=10; g[mid_r][0]=10
    # lots of wall clusters to make it feel denser and spookier than the overworld
    clusters=[(4,4),(5,4),(4,5),(12,3),(13,3),(12,4),
              (20,7),(21,7),(20,8),(30,5),(31,5),(30,6),
              (38,3),(39,3),(8,12),(9,12),(8,13),
              (16,10),(17,10),(25,14),(26,14),(25,15),
              (35,11),(36,11),(43,8),(44,8),
              (6,18),(7,18),(6,19),(14,22),(15,22),(14,23),
              (22,20),(23,20),(22,21),(32,18),(33,18),(32,19),
              (40,22),(41,22),(42,22),(46,18),
              (5,26),(6,26),(5,27),(13,28),(14,28),(13,29),
              (22,26),(23,26),(30,28),(31,28),(38,26),(39,26),(44,26)]
    for wc,wr in clusters:
        if 1<=wr<GY_ROWS-1 and 1<=wc<GY_COLS-1: g[wr][wc]=14
    # dead trees scattered around
    for tc,tr in [(3,3),(8,2),(15,4),(22,2),(28,4),(35,2),(42,4),(46,6),
                  (2,10),(7,8),(14,11),(20,9),(27,7),(33,10),(40,8),(46,11),
                  (3,16),(9,18),(16,16),(23,18),(29,16),(36,18),(43,16),
                  (2,24),(8,22),(15,25),(21,23),(28,25),(35,23),(42,25),(46,24),
                  (4,30),(10,29),(17,30),(25,29),(32,30),(39,29),(45,30)]:
        if 1<=tr<GY_ROWS-1 and 1<=tc<GY_COLS-1 and g[tr][tc] in (10,11,12):
            g[tr][tc]=13
    # purple grass variation
    for r in range(1,GY_ROWS-1):
        for c in range(1,GY_COLS-1):
            if g[r][c]==10 and _r.random()<0.3:
                g[r][c]=11 if _r.random()<0.5 else 12
    return g

def build_graveyard():
    grid = _gy_grid()
    # key is in the top left corner - hard to reach since skeletons spawn all over
    key_item = Item(3*TILE_SIZE+TILE_SIZE//2, 3*TILE_SIZE, 'key')
    skeletons=[]
    import random as _r2; _r2.seed(13)
    for ec,er in [(8,6),(15,10),(22,8),(30,6),(38,8),(44,5),
                  (5,15),(12,18),(20,16),(28,14),(36,17),(44,15),
                  (7,22),(14,25),(21,23),(29,20),(37,24),(44,22),
                  (10,28),(18,27),(26,29),(33,26),(40,28)]:
        if 2<=er<GY_ROWS-2 and 2<=ec<GY_COLS-2 and grid[er][ec] not in (14,):
            skeletons.append(GraveyardSkeleton(ec*TILE_SIZE, er*TILE_SIZE))
    return ScrollRoom('graveyard', grid,
                      items=[key_item], enemies=skeletons,
                      exits=EXIT_WEST,
                      next_rooms={'west':'spawn'},
                      bg_color=(48,25,62))


def build_all_rooms():
    return {
        'spawn':     build_spawn_room(),
        'boss_room': build_boss_room(),
        'overworld': build_overworld(),
        'graveyard': build_graveyard(),
    }


def distance(a, b):
    # utility - pixel distance between two rect centers
    dx=a.centerx-b.centerx; dy=a.centery-b.centery
    return (dx**2+dy**2)**0.5


# =============================================================================
# todo: boss fight
#
# ran out of time to finish the boss before the submission deadline
# had the design mostly planned out, just couldnt get it coded in time
#
# what i wanted to do:
#   - large boss sprite (maybe 2x2 tiles) that patrols the boss room
#   - boss has 3 phases based on hp - speeds up and changes attack pattern each phase
#   - phase 1: slow patrol, shoots a projectile toward the player every few seconds
#   - phase 2 (hp < 66%): faster movement, shoots 3 projectiles in a spread
#   - phase 3 (hp < 33%): charges directly at the player, projectiles get faster
#   - boss takes 10 hits to kill (sword damage still applies, upgrade helps)
#   - death animation - boss flashes and explodes into particles before the win screen
#   - boss theme music would play in this room (separate track from game music)
#
# class Boss(pygame.sprite.Sprite):
#   - probably extend Enemy but with a lot more custom logic
#   - need a projectile class too for the attacks
#   - would spawn in the center of the boss_room at game start
#
# for now the boss_room just shows the you win screen when entered
# =============================================================================
