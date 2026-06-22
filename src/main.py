# dungeons and data - cameron lucas
# main.py
# cs244 final project
# 6/4/2026
#
# main game loop and all the top level logic
# game_objects.py has all the classes and room builders
#
# controls:
#   wasd or arrow keys to move
#   space to attack (need to pick up the sword first)
#
# how the game works:
#   - start in spawn room, sword is sitting at the bottom
#   - go left into the overworld to find the first key (bottom left of the map)
#   - go right into the graveyard to find the second key (top left of the map)
#   - bring both keys back to spawn and walk into the north door to win

import pygame, sys, math
from game_objects import (
    Player, Enemy, Slime, GraveyardSkeleton, Item, Tile, HUD,
    Room, ScrollRoom, build_all_rooms,
    MAP_OFFSET_X, MAP_OFFSET_Y, COLS, ROWS,
    EXIT_NORTH, EXIT_SOUTH, EXIT_EAST, EXIT_WEST,
    TILE_SIZE, SCREEN_W, SCREEN_H, HUD_H,
    make_open_door_tile,
)

FPS          = 60
WINDOW_TITLE = "Dungeons and Data"
COLOR_BLACK  = (0,0,0)
TRANS_FRAMES = 30   # fade transition takes 30 frames (half a second)


# =============================================================================
# audio setup
# all sounds loaded at startup so there's no lag when they play
# uses paths relative to the script file so it works from any directory
# =============================================================================

import os as _os

def _sfx(path):
    # load a sound effect - returns None if the file is missing instead of crashing
    if _os.path.exists(path):
        return pygame.mixer.Sound(path)
    print(f"[audio] missing: {path}")
    return None

def load_audio():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    base = _os.path.dirname(_os.path.abspath(__file__))
    def p(name): return _os.path.join(base, name)
    audio = {
        'menu_music':  p('MainMenuTheme.mp3'),
        'game_music':  p('GameMusic.mp3'),
        'game_over':   p('GameOver.mp3'),
        'start_sfx':   _sfx(p('GameStartSoundEffect.mp3')),
        'enemy_hit':   _sfx(p('EnemyHit.mp3')),
        'item_grab':   _sfx(p('ItemGrab.mp3')),
        'player_hit':  _sfx(p('PlayerHit.mp3')),
    }
    return audio

def play_music(path, loops=-1, volume=0.7):
    # loops=-1 means loop forever
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
    except Exception as e:
        print(f"[audio] music error: {e}")

def play_sfx(sound, volume=1.0):
    if sound:
        sound.set_volume(volume)
        sound.play()


# =============================================================================
# room type helpers
# =============================================================================

def is_scroll(room): return isinstance(room, ScrollRoom)

def solid_tiles(room): return [t for t in room.tiles if t.solid]


# =============================================================================
# spawn position helpers
# figure out where to place the player when entering a new room
# entry_from is the direction we came from (opposite of the exit we used)
# =============================================================================

def spawn_pos_room(entry_from):
    # center x/y of the playable area
    cx = MAP_OFFSET_X + (COLS//2)*TILE_SIZE - TILE_SIZE//2
    cy = MAP_OFFSET_Y + (ROWS//2)*TILE_SIZE - TILE_SIZE//2
    # edge positions one tile inward from each wall
    top    = MAP_OFFSET_Y + TILE_SIZE + 8
    bottom = MAP_OFFSET_Y + (ROWS-2)*TILE_SIZE - TILE_SIZE - 8
    left   = MAP_OFFSET_X + TILE_SIZE + 8
    right  = MAP_OFFSET_X + (COLS-2)*TILE_SIZE - TILE_SIZE - 8
    # came from north = entered from the south side = spawn near bottom, etc.
    return {'north':(cx,bottom),'south':(cx,top),
            'east':(right,cy),'west':(left,cy),None:(cx,cy)}.get(entry_from,(cx,cy))

def spawn_pos_scroll(room, entry_from):
    # for scroll rooms, spawn near the edge we entered from
    wmid=room.world_w//2; hmid=room.world_h//2; m=TILE_SIZE*2
    return {'east': (room.world_w-m, hmid),
            'west': (m,              hmid),
            'north':(wmid,           m),
            'south':(wmid,           room.world_h-m),
            None:   (wmid,           hmid)}.get(entry_from,(wmid,hmid))


# =============================================================================
# input handling
# reads keyboard state each frame and moves/attacks the player
# =============================================================================

def handle_input(player, keys, tiles):
    dx=dy=0
    if keys[pygame.K_w] or keys[pygame.K_UP]:    dy=-player.speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy= player.speed
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx=-player.speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx= player.speed
    if dx or dy: player.move(dx,dy,tiles)
    if keys[pygame.K_SPACE]: player.attack()


# =============================================================================
# player clamping
# keeps the player inside the room bounds
# exit sides allow the player to reach the wall row so they can trigger exits
# =============================================================================

def clamp_room(player, room):
    # hard walls = one tile inside the border (player cant reach exit from here)
    # soft walls = right at the border (allows reaching the exit trigger)
    lw_hard = MAP_OFFSET_X + TILE_SIZE
    rw_hard = MAP_OFFSET_X + (COLS-1)*TILE_SIZE - player.rect.width
    tw_hard = MAP_OFFSET_Y + TILE_SIZE
    bw_hard = MAP_OFFSET_Y + (ROWS-1)*TILE_SIZE - player.rect.height

    lw_soft = MAP_OFFSET_X
    rw_soft = MAP_OFFSET_X + COLS*TILE_SIZE - player.rect.width
    tw_soft = MAP_OFFSET_Y
    bw_soft = MAP_OFFSET_Y + ROWS*TILE_SIZE - player.rect.height

    # use soft bounds on sides with exits so the player can walk into them
    lw = lw_soft if (room.exits & EXIT_WEST)  else lw_hard
    rw = rw_soft if (room.exits & EXIT_EAST)  else rw_hard
    tw = tw_soft if (room.exits & EXIT_NORTH) else tw_hard
    bw = bw_soft if (room.exits & EXIT_SOUTH) else bw_hard

    player.rect.x = max(lw, min(player.rect.x, rw))
    player.rect.y = max(tw, min(player.rect.y, bw))

def clamp_scroll(player, room):
    # for scroll rooms - same idea but dont clamp on exit sides
    # tile collision handles the border walls, we just need to stop
    # the player going past the world edge on non-exit sides
    m = TILE_SIZE
    hard_min_x = m if not (room.exits & EXIT_WEST)  else 0
    hard_max_x = (room.world_w - m - player.rect.width)  if not (room.exits & EXIT_EAST)  else (room.world_w - player.rect.width)
    hard_min_y = m if not (room.exits & EXIT_NORTH) else 0
    hard_max_y = (room.world_h - m - player.rect.height) if not (room.exits & EXIT_SOUTH) else (room.world_h - player.rect.height)
    player.rect.x = max(hard_min_x, min(player.rect.x, hard_max_x))
    player.rect.y = max(hard_min_y, min(player.rect.y, hard_max_y))


# =============================================================================
# collision detection
# checks player vs items and player/sword vs enemies each frame
# =============================================================================

def check_collisions(player, room, audio=None):
    # item pickup
    for item in room.items:
        if item.collected: continue
        if player.rect.colliderect(item.rect):
            item.collected = True
            play_sfx(audio['item_grab'] if audio else None, volume=0.8)
            if   item.item_type == 'heart':         player.heal(1)
            elif item.item_type == 'sword_upgrade':  player.apply_upgrade()
            elif item.item_type == 'sword':          player.has_sword = True
            elif item.item_type == 'key':            player.keys = min(player.keys+1,2)

    # build the sword hitbox one tile in front of the player while attacking
    attack_rect = None
    if player.is_attacking:
        ox,oy = {'right':(player.rect.right,          player.rect.y),
                 'left': (player.rect.left-TILE_SIZE,  player.rect.y),
                 'down': (player.rect.x,               player.rect.bottom),
                 'up':   (player.rect.x,               player.rect.top-TILE_SIZE)
                 }[player.direction]
        attack_rect = pygame.Rect(ox,oy,TILE_SIZE,TILE_SIZE)

    for enemy in room.enemies:
        if enemy.state=='ash': continue
        # enemy touching player = damage + iframes
        if player.rect.colliderect(enemy.rect):
            was_invincible = player.invincible
            player.take_damage(enemy.damage)
            if not was_invincible:
                play_sfx(audio['player_hit'] if audio else None, volume=1.0)
        # sword hitting enemy = deal damage, maybe drop loot on death
        if attack_rect and attack_rect.colliderect(enemy.rect):
            prev_state = enemy.state
            enemy.take_damage(player.sword_damage)
            if prev_state != 'ash':
                play_sfx(audio['enemy_hit'] if audio else None, volume=0.9)
            if enemy.state=='ash':
                loot = enemy.drop_loot()
                if loot:
                    room.items.append(Item(enemy.rect.x+12, enemy.rect.y+12, loot))


# =============================================================================
# locked door / exit logic
# try_exit returns True if the player is blocked (locked door, not enough keys)
# =============================================================================

def try_exit(player, room, direction):
    if direction in room.locked_exits:
        # north exit from spawn needs 2 keys, any other locked exit needs 1
        needed = 2 if (room.room_id == 'spawn' and direction == 'north') else 1
        if player.keys >= needed:
            player.keys -= needed
            room.locked_exits.discard(direction)
            # swap locked door tiles to open door visuals
            for t in room.tiles:
                if t.tile_type == 'locked_door':
                    t.tile_type='open_door'; t.solid=False
                    t.image=make_open_door_tile()
            return False   # door is now open
        return True   # still locked
    return False   # not a locked exit


def check_exits(player, room):
    # check if player is standing in any exit trigger zone
    for direction, rect in room.get_exit_rects().items():
        if player.rect.colliderect(rect):
            return direction
    return None


# =============================================================================
# draw functions
# separate functions for single-screen rooms and scrolling rooms
# =============================================================================

def draw_room(screen, room, player, hud, locked_flash, font_small, font_locked, fade=0):
    screen.fill(COLOR_BLACK)
    room.draw(screen)
    player.draw_attack(screen)
    player.draw(screen)
    hud.draw(screen)
    _draw_room_label(screen, room.room_id, font_small)
    _draw_locked_flash(screen, locked_flash, font_locked)
    if fade > 0:
        ov = pygame.Surface((SCREEN_W,SCREEN_H)); ov.fill(COLOR_BLACK); ov.set_alpha(int(fade))
        screen.blit(ov,(0,0))
    pygame.display.flip()

def draw_scroll(screen, room, player, hud, locked_flash, font_small, font_locked, fade=0):
    # room.draw handles the background fill so we dont call screen.fill here
    # (calling screen.fill before caused black flashing at the top edge)
    room.draw(screen)
    # convert player world position to screen position using camera offset
    sx = player.rect.x - room.cam_x
    sy = player.rect.y - room.cam_y + HUD_H
    player.draw_attack(screen, room.cam_x, room.cam_y-HUD_H)
    if not (player.invincible and player.invincible_timer % 6 < 3):
        screen.blit(player.image, (sx, sy))
    hud.draw(screen)
    _draw_minimap(screen, room, player)
    _draw_room_label(screen, room.room_id, font_small)
    _draw_locked_flash(screen, locked_flash, font_locked)
    if fade > 0:
        ov = pygame.Surface((SCREEN_W,SCREEN_H)); ov.fill(COLOR_BLACK); ov.set_alpha(int(fade))
        screen.blit(ov,(0,0))
    pygame.display.flip()

def _draw_room_label(screen, room_id, font):
    # small room name in the bottom right corner
    if font is None: return
    s = font.render(f"[ {room_id.replace('_',' ').upper()} ]", True, (180,180,180))
    screen.blit(s, (SCREEN_W-s.get_width()-8, SCREEN_H-20))

def _draw_locked_flash(screen, timer_ref, font):
    # flash a message when the player tries a locked door without enough keys
    t = timer_ref[0]
    if t > 0:
        alpha = min(255, t*4)
        needed = timer_ref[1] if len(timer_ref) > 1 else 1
        txt = f"LOCKED  —  need {needed} key{'s' if needed>1 else ''}!"
        msg = font.render(txt, True, (255,80,80))
        msg.set_alpha(alpha)
        screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H//2 - 40))
        timer_ref[0] -= 1

def _draw_minimap(screen, room, player):
    # small minimap in the bottom left corner for scroll rooms
    # shows player position and key location
    mm_w,mm_h = 96,64
    mm_x,mm_y = 8, SCREEN_H-mm_h-8
    mm = pygame.Surface((mm_w,mm_h),pygame.SRCALPHA)
    mm.fill((0,0,0,140))
    # player dot
    px_f = player.rect.centerx/room.world_w
    py_f = player.rect.centery/room.world_h
    pygame.draw.rect(mm,(80,200,80),(int(px_f*mm_w)-2, int(py_f*mm_h)-2, 4,4))
    # key dot if not yet collected
    for item in room.items:
        if not item.collected and item.item_type=='key':
            kx=int(item.rect.centerx/room.world_w*mm_w)
            ky=int(item.rect.centery/room.world_h*mm_h)
            pygame.draw.rect(mm,(220,185,50),(kx-2,ky-2,4,4))
    pygame.draw.rect(mm,(120,120,120),(0,0,mm_w,mm_h),1)
    screen.blit(mm,(mm_x,mm_y))


# =============================================================================
# room transition
# fades out, swaps the room, places the player, fades in
# =============================================================================

def fade_frames(screen, room, player, hud, font_small, font_locked,
                fade_out=True, scroll=False, locked_flash=None):
    lf = locked_flash or [0]
    for f in range(TRANS_FRAMES):
        t = f/TRANS_FRAMES
        alpha = int(255*t) if fade_out else int(255*(1-t))
        if scroll: draw_scroll(screen,room,player,hud,lf,font_small,font_locked,fade=alpha)
        else:      draw_room(  screen,room,player,hud,lf,font_small,font_locked,fade=alpha)
        pygame.event.pump()

def transition(screen, clock, rooms, cur, direction, player, hud, font_small, font_locked):
    nid = cur.next_rooms.get(direction)
    if not nid or nid not in rooms: return cur
    fade_frames(screen,cur,player,hud,font_small,font_locked,fade_out=True,scroll=is_scroll(cur))
    new = rooms[nid]
    # opposite direction = which side of the new room we spawn near
    opp = {'north':'south','south':'north','east':'west','west':'east'}
    entry = opp.get(direction)
    if is_scroll(new):
        player.rect.topleft = spawn_pos_scroll(new, entry)
        new.update_camera(player)
    else:
        player.rect.topleft = spawn_pos_room(entry)
    hud.update(player)
    fade_frames(screen,new,player,hud,font_small,font_locked,fade_out=False,scroll=is_scroll(new))
    return new

def nudge_back(player, direction):
    # push player away from a locked exit so they dont keep retriggering it
    push = TILE_SIZE // 2
    if   direction=='north': player.rect.y += push
    elif direction=='south': player.rect.y -= push
    elif direction=='east':  player.rect.x -= push
    elif direction=='west':  player.rect.x += push


# =============================================================================
# screens
# =============================================================================

def show_win_screen(screen, clock, audio=None):
    # you win! white background, pulsing gold text
    # todo: replace this with an actual boss fight cutscene if i come back to this
    ft = pygame.font.SysFont("Arial", 64, bold=True)
    fs = pygame.font.SysFont("Arial", 24)
    fh = pygame.font.SysFont("Arial", 18)
    if audio:
        pygame.mixer.music.stop()
        play_sfx(audio.get('item_grab'), volume=1.0)
    tick = 0
    while True:
        screen.fill((255, 255, 255))
        tick += 1
        pulse = 200 + int(55 * abs(math.sin(tick * 0.04)))
        title_surf = ft.render("YOU  WIN!", True, (pulse, 180, 0))
        sub_surf   = fs.render("Congratulations, hero!", True, (60, 60, 60))
        hint_surf  = fh.render("Press ENTER to return to spawn", True, (120, 120, 120))
        screen.blit(title_surf, (SCREEN_W//2 - title_surf.get_width()//2, 180))
        screen.blit(sub_surf,   (SCREEN_W//2 - sub_surf.get_width()//2,   280))
        screen.blit(hint_surf,  (SCREEN_W//2 - hint_surf.get_width()//2,  330))
        # little sword trophy
        sx = SCREEN_W//2 - 8
        pygame.draw.rect(screen, (200,210,230), (sx, 370, 8, 50))
        pygame.draw.rect(screen, (240,245,255), (sx+1,370, 3, 50))
        pygame.draw.rect(screen, (255,215,0),   (sx-14,418,36, 6))
        pygame.draw.rect(screen, (200,170,40),  (sx,  424, 8, 12))
        pygame.display.flip()
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                if audio: play_music(audio['game_music'], volume=0.55)
                return

def show_title(screen, clock, audio=None):
    ft = pygame.font.SysFont("Arial",52,bold=True)
    fs = pygame.font.SysFont("Arial",22)
    fh = pygame.font.SysFont("Arial",16)
    tick=0

    if audio:
        play_music(audio['menu_music'], volume=0.6)

    def _draw_title_frame(alpha_overlay=0):
        screen.fill(COLOR_BLACK)
        flicker=200+int(55*abs(math.sin(tick*0.04)))
        screen.blit(ft.render("Dungeons and Data",True,(flicker,160,30)),
                    (SCREEN_W//2-ft.size("Dungeons and Data")[0]//2,200))
        screen.blit(fs.render("Press ENTER to Start",True,(220,220,220)),
                    (SCREEN_W//2-fs.size("Press ENTER to Start")[0]//2,290))
        screen.blit(fh.render("WASD / Arrows  |  SPACE to attack",True,(120,120,120)),
                    (SCREEN_W//2-fh.size("WASD / Arrows  |  SPACE to attack")[0]//2,340))
        # pixel art sword decoration
        sx=SCREEN_W//2-8
        pygame.draw.rect(screen,(200,210,230),(sx,380,8,60))
        pygame.draw.rect(screen,(240,245,255),(sx+1,380,3,60))
        pygame.draw.rect(screen,(180,140,50),(sx-14,438,36,6))
        pygame.draw.rect(screen,(120,80,30),(sx,444,8,14))
        if alpha_overlay > 0:
            ov=pygame.Surface((SCREEN_W,SCREEN_H)); ov.fill(COLOR_BLACK); ov.set_alpha(alpha_overlay)
            screen.blit(ov,(0,0))
        pygame.display.flip()

    while True:
        tick+=1
        _draw_title_frame()
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN:
                # play the start sfx and fade to black over 5 seconds before starting
                play_sfx(audio['start_sfx'] if audio else None, volume=1.0)
                fade_frames_title = 300   # 300 frames = 5 seconds at 60fps
                for f in range(fade_frames_title):
                    tick+=1
                    alpha = int(255 * f / fade_frames_title)
                    _draw_title_frame(alpha_overlay=alpha)
                    clock.tick(FPS)
                    pygame.event.pump()
                return

def show_game_over(screen, clock, audio=None):
    ft=pygame.font.SysFont("Arial",52,bold=True); fs=pygame.font.SysFont("Arial",22)
    tick=0
    if audio:
        play_music(audio['game_over'], loops=0, volume=0.8)
    while True:
        screen.fill((10,0,0)); tick+=1
        r=160+int(60*abs(math.sin(tick*0.05)))
        screen.blit(ft.render("GAME OVER",True,(r,0,0)),
                    (SCREEN_W//2-ft.size("GAME OVER")[0]//2,220))
        screen.blit(fs.render("Press ENTER to Quit",True,(180,180,180)),
                    (SCREEN_W//2-fs.size("Press ENTER to Quit")[0]//2,310))
        pygame.display.flip(); clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN: pygame.quit(); sys.exit()


# =============================================================================
# main game loop
# =============================================================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(WINDOW_TITLE)
    clock  = pygame.time.Clock()
    font_small  = pygame.font.SysFont(None, 18)
    font_locked = pygame.font.SysFont(None, 30)

    # load audio before showing the title so the menu music starts right away
    audio = load_audio()
    show_title(screen, clock, audio)
    play_music(audio['game_music'], volume=0.55)

    # build all rooms and create the player
    rooms = build_all_rooms()
    px = MAP_OFFSET_X + (COLS//2)*TILE_SIZE - TILE_SIZE//2
    py = MAP_OFFSET_Y + (ROWS//2)*TILE_SIZE - TILE_SIZE//2
    player = Player(px, py, {})
    hud    = HUD(player)
    cur    = rooms['spawn']
    locked_flash = [0, 1]   # [frames_remaining, keys_needed_for_message]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT: running=False

        keys = pygame.key.get_pressed()
        handle_input(player, keys, solid_tiles(cur))
        player.update()
        cur.update(player)
        hud.update(player)
        check_collisions(player, cur, audio)

        # movement and exit checking - scroll rooms vs single screen rooms work a bit differently
        if is_scroll(cur):
            clamp_scroll(player, cur)
            exit_dir = check_exits(player, cur)
            if exit_dir:
                if try_exit(player, cur, exit_dir):
                    locked_flash[0] = 90
                    locked_flash[1] = (2 if (cur.room_id=='spawn' and exit_dir=='north') else 1)
                    nudge_back(player, exit_dir)
                else:
                    cur = transition(screen,clock,rooms,cur,exit_dir,
                                     player,hud,font_small,font_locked)
        else:
            clamp_room(player, cur)
            exit_dir = check_exits(player, cur)
            if exit_dir:
                if try_exit(player, cur, exit_dir):
                    locked_flash[0] = 90
                    locked_flash[1] = (2 if (cur.room_id=='spawn' and exit_dir=='north') else 1)
                    nudge_back(player, exit_dir)
                else:
                    cur = transition(screen,clock,rooms,cur,exit_dir,
                                     player,hud,font_small,font_locked)

        # re-check room type after transition since it might have changed
        if is_scroll(cur):
            draw_scroll(screen,cur,player,hud,locked_flash,font_small,font_locked)
        else:
            draw_room(screen,cur,player,hud,locked_flash,font_small,font_locked)

        # death check
        if player.hp_float <= 0:
            show_game_over(screen, clock, audio)

        # win check - boss_room has is_win_room=True
        if getattr(cur, 'is_win_room', False):
            show_win_screen(screen, clock, audio)
            # send the player back to spawn after the win screen
            cur = rooms['spawn']
            px2 = MAP_OFFSET_X + (COLS//2)*TILE_SIZE - TILE_SIZE//2
            py2 = MAP_OFFSET_Y + (ROWS//2)*TILE_SIZE - TILE_SIZE//2
            player.rect.topleft = (px2, py2)
            hud.update(player)

        clock.tick(FPS)

    pygame.quit(); sys.exit()


if __name__=='__main__':
    main()
