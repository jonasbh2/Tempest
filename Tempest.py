import pygame
import random
import sys
import textwrap
import os

pygame.init()

WIDTH, HEIGHT = 1024, 576
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)


clock = pygame.time.Clock()

BG_CLR = (100, 100, 100)

pygame.display.set_caption("Tempest")
pygame.display.set_icon(pygame.image.load("assets/wind_icon.png"))

pygame.mouse.set_visible(False)

cloud_scroll = 0

pygame.init()

pygame.mixer.init()

sfx_tempest = pygame.mixer.Sound("assets/tempest.wav")
sfx_song = pygame.mixer.Sound("assets/pavane.wav")

sfx_collect = pygame.mixer.Sound("assets/collect.wav")
sfx_collect.set_volume(0.2)

sfx_jump = pygame.mixer.Sound("assets/jump.wav")
sfx_jump.set_volume(0.5)

sfx_attack = pygame.mixer.Sound("assets/attack.wav")
sfx_attack.set_volume(0.2)

sfx_fire = pygame.mixer.Sound("assets/fire.wav")

sfx_zap = pygame.mixer.Sound("assets/zap.wav")
sfx_zap.set_volume(0.5)

sfx_bubble = pygame.mixer.Sound("assets/bubble.wav")

sfx_air = pygame.mixer.Sound("assets/air.wav")

sfx_kill = pygame.mixer.Sound("assets/enemy_killed.wav")
sfx_kill.set_volume(0.5)

sfx_renounce = pygame.mixer.Sound("assets/renounce.wav")

sfx_glass = pygame.mixer.Sound("assets/glass.wav")
sfx_glass.set_volume(0.2)

TILE_SIZE = 32

GRAVITY = pygame.Vector2(0, 0.3)

kFont = pygame.font.Font("assets/font/5x5.ttf", 30)
bigFont = pygame.font.Font("assets/font/5x5.ttf", 80)

bg_img = pygame.image.load("assets/background.png").convert()
bg_width, bg_height = bg_img.get_size()

magicUse = 1

coinCount = 0
lives = 5
scorecount = 0

deflevel = 1

magicDefault = 50
magicPoints = magicDefault


def move_and_collide(sprite, dx, dy, platforms):

    landed = bumped_head = False

    sprite.rect.x += dx

    for p in platforms:
        if sprite.rect.colliderect(p.rect):

            if dx > 0:

                sprite.rect.right = p.rect.left

            elif dx < 0:

                sprite.rect.left = p.rect.right

            dx = 0

    sprite.rect.y += dy

    for p in platforms:
        if sprite.rect.colliderect(p.rect):

            if dy > 0:
                sprite.rect.bottom = p.rect.top

                landed = True

            elif dy < 0:
                sprite.rect.top = p.rect.bottom

                bumped_head = True

            dy = 0

    return landed, bumped_head


class Camera:
    def __init__(self, viewport):
        self.offset = pygame.Vector2()

        self.vp = pygame.Rect(0, 0, *viewport)

    def center_on(self, rect):
        self.offset.x = rect.centerx - self.vp.w // 2

        self.offset.y = rect.centery - self.vp.h // 2

    def to_screen(self, rect):
        return rect.move(-self.offset.x, -self.offset.y)

    def visible(self, rect, pad=64):
        r = pygame.Rect(self.offset.x - pad, self.offset.y - pad,

                        self.vp.w + 2 * pad, self.vp.h + 2 * pad)

        return rect.colliderect(r)


def pad_level(rows):
    w = max(len(r) for r in rows)

    return [r.ljust(w) for r in rows]


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, *groups,

                 platforms):

        super().__init__(*groups)

        self.image = pygame.Surface((20, 32))
        self.image.fill((255, 255, 255))
        self.rect = self.image.get_rect(

            topleft=pos)

        self.shieldActive = False
        self.shieldFrameCounter = 0
        self.shieldImage = pygame.image.load("assets/sheild.png").convert_alpha()

        run_frames = [

            pygame.image.load("assets/prospero_run_1.png"),

            pygame.image.load("assets/prospero_run_2.png"),

            pygame.image.load("assets/prospero_run_3.png"),

            pygame.image.load("assets/prospero_run_2.png"),

        ]

        self.image_cache = {

            "idle_left": pygame.image.load("assets/prospero.png"),

            "idle_right": pygame.transform.flip(pygame.image.load("assets/prospero.png"), True, False),

            "run_left": run_frames,

            "run_right": [pygame.transform.flip(img, True, False) for img in run_frames],

        }

        self.platforms = platforms

        self.verticalSpeedMax = 4

        self.frictional = True

        self.vel = pygame.math.Vector2(0, 0)

        self.onGround = False

        self.direction = "left"

        self.shotCooldown = 30

        self.moving = False

        self.shooting = False

        self.shootingCooldown = 30

        self.activeWeapon = 1

        self.shieldDrainTimer = 0

        self.animationCooldown = 15

        self.animationState = 0

        self.speed = 2

        self.speedMax = 4

        self.jumpStrength = 10.2

        self.previousWeapon = 1

        self.keys = [False, False, False]

    def update(self):

        self.shotCooldown -= 1

        self.vel += GRAVITY

        keys = pygame.key.get_pressed()

        if keys[pygame.K_a] and not keys[pygame.K_d]:

            self.vel.x -= self.speed

            self.direction = "left"

            self.moving = True

        elif keys[pygame.K_d] and not keys[pygame.K_a]:

            self.vel.x += self.speed

            self.direction = "right"

            self.moving = True

        else:

            self.moving = False

        if keys[pygame.K_LSHIFT]:

            self.speedMax = 4

        else:

            self.speedMax = 2

        if keys[pygame.K_SPACE] and self.onGround:
            sfx_jump.play()

            self.vel.y -= self.jumpStrength

            self.onGround = False

        if keys[pygame.K_1]:
            self.activeWeapon = 1

        if keys[pygame.K_2]:
            self.activeWeapon = 2

        if keys[pygame.K_3] and deflevel >= 2:
            self.activeWeapon = 3

        if keys[pygame.K_4] and deflevel >= 3:
            self.activeWeapon = 4

        if keys[pygame.K_5] and magicPoints > 0 and deflevel >= 4:

            if not self.shieldActive:
                self.previousWeapon = self.activeWeapon

            self.activeWeapon = 5

            self.shieldActive = True

            self.shieldDrainTimer += 1

            if self.shieldDrainTimer >= 30:
                globals()['magicPoints'] -= 1

                self.shieldDrainTimer = 0

            if magicPoints <= 0:
                self.shieldActive = False

                self.activeWeapon = self.previousWeapon

        else:

            if self.shieldActive:
                self.shieldActive = False

                self.shieldDrainTimer = 0

                self.activeWeapon = self.previousWeapon

        if keys[pygame.K_6] and deflevel >= 5:
            self.activeWeapon = 6

            self.shieldActive = False

            self.shieldDrainTimer = 0

        if self.vel.x > self.speedMax:
            self.vel.x = self.speedMax

        if self.vel.x < -self.speedMax:
            self.vel.x = -self.speedMax

        if self.vel.y > self.verticalSpeedMax:
            self.vel.y = self.verticalSpeedMax

        if self.frictional:
            self.vel.x = (

                    self.vel.x / 1.1)

        self.animate()

        if self.frictional:
            self.vel.x *= 0.9

        self.vel.x = max(-self.speedMax, min(self.speedMax, self.vel.x))

        self.vel.y = max(-self.speedMax * 4, min(self.speedMax * 4, self.vel.y))

        landed, _ = move_and_collide(self, self.vel.x, self.vel.y,

                                     self.platforms)

        self.onGround = landed

        if landed:
            self.vel.y = 0

        self.animate()

    def animate(self):

        if self.shooting and not self.moving:
            self.image = self.image_cache["idle_right" if self.direction == "right" else "idle_left"]

            return

        if not self.moving:

            self.image = self.image_cache["idle_right" if self.direction == "right" else "idle_left"]

        else:

            self.animationCooldown -= 1

            if self.animationCooldown <= 0:
                self.animationState = (self.animationState + 1) % 4

                self.animationCooldown = 40

            key = "run_right" if self.direction == "right" else "run_left"

            self.image = self.image_cache[key][self.animationState]

        if self.shooting:

            self.shootingCooldown -= 1

            if self.shootingCooldown <= 0:
                self.shooting = False

                self.shootingCooldown = 30


class Platform(pygame.sprite.Sprite):
    TILE_SIZE = 32

    def __init__(self, pos, platform_type="platform", *groups):

        super().__init__(*groups)

        mapping = {

            "platform": "assets/tile_oblique_d8.png",

            "crate": "assets/crate_oblique_d8.png",

            "grass": "assets/grass_oblique_d8.png",

            "sand": "assets/sand_oblique_d8.png",

            "rock": "assets/rock_oblique_d8.png",

            "dirt": "assets/dirt_oblique_d8.png",

            "moss": "assets/moss_oblique_d8.png",

        }

        path = mapping.get(platform_type)

        if path and os.path.exists(path):
            self.image = pygame.image.load(path).convert_alpha()

        else:

            self.image = pygame.Surface((self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA)
            self.image.fill((255, 0, 255))

        depth = self.image.get_height() - self.TILE_SIZE

        x, y = pos

        self.rect = pygame.Rect(x, y + depth,

                                self.TILE_SIZE, self.TILE_SIZE)

        self._draw_offset_y = -depth

    def draw(self, surface, camera):
        draw_rect = self.rect.move(0, self._draw_offset_y)

        surface.blit(self.image, camera.to_screen(draw_rect))


class Support(pygame.sprite.Sprite):

    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((32, 32))

        self.image = pygame.image.load('assets/support.png')

        self.rect = self.image.get_rect(topleft=pos)


class Barrier(pygame.sprite.Sprite):

    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)

        self.image.fill((0, 0, 0, 0))

        self.rect = self.image.get_rect(topleft=pos)


class Stephano(pygame.sprite.Sprite):

    def __init__(self, pos, *groups, platforms, players, entities, bullets, renunciationBlocked):

        super().__init__(*groups)

        self.image_cache = {

            "left": [

                pygame.image.load('assets/stephano1.png'),

                pygame.image.load('assets/stephano2.png'),

                pygame.image.load('assets/stephano3.png'),

            ],

            "right": [

                pygame.transform.flip(pygame.image.load('assets/stephano1.png'), True, False),

                pygame.transform.flip(pygame.image.load('assets/stephano2.png'), True, False),

                pygame.transform.flip(pygame.image.load('assets/stephano3.png'), True, False),

            ]

        }

        self.image = self.image_cache["left"][0]
        self.rect = self.image.get_rect(topleft=pos)
        self.rect = self.image.get_rect(topleft=pos)

        self.platforms = platforms

        self.players = players

        self.entities = entities

        self.bullets = bullets

        self.renounced = renunciationBlocked

        self.stunned = 0

        self.health = 1

        self.animationDirection = 0

        self.bulletCooldown = random.randint(80, 120)

        self.animationCooldown = 15

        self.animationState = 0

        self.speed = 1

        self.vel = pygame.math.Vector2(0, 0)

        self.direction = "left"

    def update(self):
        if hasattr(self, "stunned") and self.stunned > 0:
            self.stunned -= 1
            return

        self.vel += GRAVITY

        if self.direction == "left":
            self.vel.x = -self.speed
        else:
            self.vel.x = self.speed

        nearby_platforms = [p for p in self.platforms
                            if abs(p.rect.centerx - self.rect.centerx) < 100 and
                            abs(p.rect.centery - self.rect.centery) < 100]

        lookahead = 10 if self.direction == "right" else -10
        check_x = self.rect.centerx + lookahead
        check_y = self.rect.bottom + 1
        check_rect = pygame.Rect(check_x, check_y, 2, 2)

        on_ground = any(p.rect.colliderect(check_rect) for p in nearby_platforms)

        if not on_ground:
            self.direction = "left" if self.direction == "right" else "right"
            self.vel.x = 0

        landed, _ = move_and_collide(self, self.vel.x, self.vel.y, nearby_platforms)

        if landed:
            self.vel.y = 0

        self.bulletCooldown -= 1
        if self.bulletCooldown <= 0 and self.players:
            self.bulletCooldown = 2 * random.randint(80, 120)
            player = next(iter(self.players), None)
            if player:
                if player.rect.centerx < self.rect.centerx:
                    self.direction = "left"
                else:
                    self.direction = "right"

                if not globals().get("renunciationActive", False) and len(self.bullets) < 20:
                    Bottle((self.rect.centerx, self.rect.centery),
                           self.direction, True, True,
                           self.entities, self.bullets, self.renounced)

        self.animate()

    def animate(self):

        self.animationCooldown -= 1

        if self.animationCooldown <= 0:

            self.animationState += self.animationDirection

            self.animationCooldown = 15

            if self.animationState >= 2:

                self.animationState = 2

                self.animationDirection = -1

            elif self.animationState <= 0:

                self.animationState = 0

                self.animationDirection = 1

        direction_key = "right" if self.direction == "right" else "left"

        self.image = self.image_cache[direction_key][self.animationState]


class Ariel(pygame.sprite.Sprite):

    def __init__(self, pos, *groups):

        super().__init__(*groups)

        self.image = pygame.Surface((32, 32))

        self.image = pygame.image.load('assets/ariel.png')

        self.rect = self.image.get_rect(topleft=pos)

        self.max_health = 5

        self.health = self.max_health

        self.stunned = 0

        self.speed = 2

        self.vel = pygame.math.Vector2(0, 0)

        self.direction = "left"

    def draw_health_bar(self, surface, camera):

        bar_width = 32

        bar_height = 4

        health_ratio = max(self.health, 0) / 5

        health_bar_rect = pygame.Rect(0, 0, bar_width, bar_height)

        health_bar_rect.midbottom = camera.to_screen(self.rect).midtop

        health_bar_rect.y -= 5

        pygame.draw.rect(surface, (60, 0, 0), health_bar_rect)

        current = pygame.Rect(health_bar_rect.left, health_bar_rect.top, int(bar_width * health_ratio), bar_height)

        pygame.draw.rect(surface, (255, 0, 0), current)

    def update(self):

        if hasattr(self, "stunned") and self.stunned > 0:
            self.stunned -= 1

            return

        if self.direction == "left":

            self.image = pygame.image.load('assets/ariel.png')

            self.vel.x = -self.speed

        else:

            self.image = pygame.transform.flip(pygame.image.load('assets/ariel.png'), True, False)

            self.vel.x = self.speed

        self.rect.x += self.vel.x

        self.rect.y += self.vel.y


class SmartEnemyTurnTrigger(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)

        self.image.fill((0, 0, 0, 0))

        self.rect = self.image.get_rect(topleft=pos)


class Caliban(pygame.sprite.Sprite):
    def __init__(self, pos, *groups, platforms, players):

        super().__init__(*groups)

        walk_frames = [

            pygame.image.load("assets/caliban1.png"),

            pygame.image.load("assets/caliban2.png"),

            pygame.image.load("assets/caliban3.png"),

        ]

        self.image_cache = {

            "right": walk_frames,

            "left": [pygame.transform.flip(img, True, False) for img in walk_frames],

        }

        self.image = self.image_cache["left"][0]

        self.rect = self.image.get_rect(topleft=pos)

        self.platforms = platforms

        self.players = players

        self.animationDirection = 1

        self.stunned = 0

        self.max_health = 10

        self.health = self.max_health

        self.vel = pygame.math.Vector2(0, 0)

        self.speed = 1

        self.jump_strength = 8

        self.direction = "left"

        self.jump_cooldown = 90

        self.animationCooldown = 15

        self.animationState = 0

    def draw_health_bar(self, surface, camera):

        bar_width = 32

        bar_height = 4

        health_ratio = max(self.health, 0) / 10

        health_bar_rect = pygame.Rect(0, 0, bar_width, bar_height)

        health_bar_rect.midbottom = camera.to_screen(self.rect).midtop

        health_bar_rect.y -= 5

        pygame.draw.rect(surface, (60, 0, 0), health_bar_rect)

        current = pygame.Rect(health_bar_rect.left, health_bar_rect.top, int(bar_width * health_ratio), bar_height)

        pygame.draw.rect(surface, (255, 0, 0), current)

    def update(self):

        if hasattr(self, "stunned") and self.stunned > 0:
            self.stunned -= 1

            return

        self.vel += GRAVITY

        self.jump_cooldown -= 1

        player = next(iter(self.players), None)

        if player:

            if player.rect.centerx < self.rect.centerx:

                self.direction = "left"

                self.vel.x = -self.speed

            else:

                self.direction = "right"

                self.vel.x = self.speed

        landed, _ = move_and_collide(self, int(self.vel.x), int(self.vel.y), self.platforms)

        if landed:

            self.vel.y = 0

            if self.jump_cooldown <= 0:
                self.vel.y = -self.jump_strength

                self.jump_cooldown = 90

        self.animate()

    def animate(self):

        self.animationCooldown -= 1

        if self.animationCooldown <= 0:

            self.animationState += self.animationDirection

            self.animationCooldown = 15

            if self.animationState >= 2:

                self.animationState = 2

                self.animationDirection = -1

            elif self.animationState <= 0:

                self.animationState = 0

                self.animationDirection = 1

        direction_key = "right" if self.direction == "right" else "left"

        self.image = self.image_cache[direction_key][self.animationState]


class Coin(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((8, 8))

        self.image = pygame.image.load('assets/coin.png')

        self.rect = self.image.get_rect(center=pos)


class Ammo(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((32, 32))

        self.image = pygame.image.load('assets/ammo_pickup.png')

        self.rect = self.image.get_rect(topleft=pos)


class BigAmmo(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((32, 32))

        self.image = pygame.image.load('assets/big_ammo_pickup.png')

        self.rect = self.image.get_rect(topleft=pos)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, up, down, *groups):

        super().__init__(*groups)

        self.original_image = pygame.image.load('assets/gust.png').convert_alpha()

        self.image = self.original_image.copy()

        self.rect = self.image.get_rect(center=pos)

        sfx_air.play()

        self.angle = 0

        self.rotation_speed = 10

        self.speed = 10

        self.vel = pygame.math.Vector2(0, 0)

        if direction == "right":

            self.vel.x = self.speed

        elif direction == "left":

            self.vel.x = -self.speed

        elif direction == "up":

            self.vel.y = -self.speed

        elif direction == "down":

            self.vel.y = self.speed

        if not up:
            self.vel.y -= self.speed

        if not down:
            self.vel.y = self.speed

    def update(self):

        self.rect.x += self.vel.x

        self.rect.y += self.vel.y

        self.angle = (self.angle + self.rotation_speed) % 360

        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect(center=self.rect.center)


class LightningZap(pygame.sprite.Sprite):
    def __init__(self, pos, direction, *groups):

        super().__init__(*groups)

        self.original_image = pygame.image.load('assets/laser.png').convert_alpha()

        self.image = self.original_image.copy()

        self.rect = self.image.get_rect(center=pos)

        sfx_zap.play()

        self.angle = 0

        self.rotation_speed = 20

        self.speed = 7

        self.vel = pygame.Vector2(0, 0)

        if direction == "right":

            self.vel.x = self.speed

        elif direction == "left":

            self.vel.x = -self.speed

    def update(self):

        self.rect.x += self.vel.x

        self.angle = (self.angle + self.rotation_speed) % 360

        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect(center=self.rect.center)


class SpiritBindBubble(pygame.sprite.Sprite):
    def __init__(self, pos, direction, *groups):

        super().__init__(*groups)

        self.original_image = pygame.image.load('assets/spiritbind.png').convert_alpha()

        self.image = self.original_image.copy()

        self.rect = self.image.get_rect(center=pos)

        self.speed = 3

        self.angle = 0

        self.rotation_speed = 5

        sfx_bubble.play()

        self.vel = pygame.Vector2(0, 0)

        if direction == "right":

            self.vel.x = self.speed

        elif direction == "left":

            self.vel.x = -self.speed

    def update(self):

        self.rect.x += self.vel.x

        self.angle = (self.angle + self.rotation_speed) % 360

        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect(center=self.rect.center)


class RoughMagicAOE(pygame.sprite.Sprite):
    def __init__(self, center_pos, *groups, playerkillables, entities, blueKeyCards):

        super().__init__(*groups)

        self.original_image = pygame.image.load("assets/roughmagic.png").convert_alpha()

        self.image = self.original_image.copy()

        self.rect = self.image.get_rect(center=center_pos)

        self.playerkillables = playerkillables

        self.entities = entities

        self.blueKeyCards = blueKeyCards

        sfx_fire.play()

        self.max_radius = TILE_SIZE * 5

        self.current_radius = 10

        self.expand_speed = 3

        self.angle = 0

        self.rotation_speed = 10

        self.center = center_pos

        self.done = False

        self.damaged = set()

    def update(self):

        global scorecount

        if self.done:
            self.kill()

            return

        self.current_radius += self.expand_speed

        if self.current_radius >= self.max_radius:
            self.done = True

        self.angle = (self.angle + self.rotation_speed) % 360

        scale = int(self.current_radius * 2)

        scaled_image = pygame.transform.smoothscale(self.original_image, (scale, scale))

        rotated_image = pygame.transform.rotate(scaled_image, self.angle)

        self.image = rotated_image

        self.rect = self.image.get_rect(center=self.center)

        for enemy in self.playerkillables:

            if enemy not in self.damaged and self.rect.colliderect(enemy.rect):

                if hasattr(enemy, "health"):

                    enemy.health -= 20

                    if enemy.health <= 0:

                        enemy.kill()

                        sfx_kill.play()

                        if isinstance(enemy, Alonso):
                            BlueKey(enemy.rect.center, self.entities, self.blueKeyCards)

                        enemy.kill()

                        scorecount += 25

                else:

                    enemy.kill()

                    sfx_kill.play()

                self.damaged.add(enemy)


class RenunciationFlash(pygame.sprite.Sprite):
    def __init__(self, center_pos, *groups):

        super().__init__(*groups)

        self.original_image = pygame.image.load("assets/renunciation_flash.png").convert_alpha()

        self.image = self.original_image.copy()

        self.rect = self.image.get_rect(center=center_pos)

        self.center = center_pos

        self.current_radius = 10

        self.max_radius = TILE_SIZE * 15

        self.expand_speed = 3

        self.angle = 0

        self.rotation_speed = 6

        self.done = False

    def update(self):

        if self.done:
            self.kill()

            return

        self.current_radius += self.expand_speed

        if self.current_radius >= self.max_radius:
            self.done = True

        scale = int(self.current_radius * 2)

        scaled_image = pygame.transform.smoothscale(self.original_image, (scale, scale))

        rotated_image = pygame.transform.rotate(scaled_image, self.angle)

        self.image = rotated_image

        self.rect = self.image.get_rect(center=self.center)

        self.angle = (self.angle + self.rotation_speed) % 360


class Bottle(pygame.sprite.Sprite):
    rotated_images = []

    @staticmethod
    def preload_rotated_images():

        """Preload rotated frames once to avoid runtime transformation."""

        base_image = pygame.image.load('assets/bullet.png').convert_alpha()

        Bottle.rotated_images = [

            pygame.transform.rotate(base_image, angle)

            for angle in range(0, 360, 30)

        ]

    def __init__(self, pos, direction, up, down, *groups):

        super().__init__(*groups)

        if not Bottle.rotated_images:
            Bottle.preload_rotated_images()

        self.angle_index = 0

        self.image = Bottle.rotated_images[self.angle_index]

        self.rect = self.image.get_rect(center=pos)

        self.speed = 3

        self.vel = pygame.math.Vector2(0, -8)

        if direction == "right":

            self.vel.x = self.speed

        elif direction == "left":

            self.vel.x = -self.speed

        elif direction == "up":

            self.vel.y = -self.speed

        elif direction == "down":

            self.vel.x = self.speed

        if not up:
            self.vel.y -= self.speed

        if not down:
            self.vel.y = self.speed

    def update(self):

        self.vel += GRAVITY

        self.rect.x += self.vel.x

        self.rect.y += self.vel.y

        self.angle_index = (self.angle_index + 1) % len(Bottle.rotated_images)

        center = self.rect.center

        self.image = Bottle.rotated_images[self.angle_index]

        self.rect = self.image.get_rect(center=center)


class Alonso(pygame.sprite.Sprite):
    def __init__(self, pos, *groups, platforms, entities, bullets, playerkillers, renunciationBlocked):

        super().__init__(*groups)

        self.image = pygame.Surface((64, 128))

        self.image = pygame.image.load('assets/king.png')

        self.rect = self.image.get_rect(topleft=pos)

        self.renunciationFrozen = 0

        self.renunciationBlocked = renunciationBlocked

        self.entities = entities

        self.bullets = bullets

        self.playerkillers = playerkillers

        self.platforms = platforms

        self.spawn_x = pos[0]

        self.animationCooldown = 0

        self.animationState = 0

        self.shooting = False

        self.shootingCooldown = 0

        self.max_health = 60

        self.health = self.max_health

        self.jumpStrength = 15

        self.jumpCooldown = 200

        self.bulletCooldown = random.randrange(70, 90)

        self.speed = 2

        self.vel = pygame.math.Vector2(0, 0)

        self.direction = "left"

    def draw_health_bar(self, surface, camera):

        bar_width = 60

        bar_height = 6

        health_ratio = max(self.health, 0) / 60

        health_bar_rect = pygame.Rect(0, 0, bar_width, bar_height)

        health_bar_rect.midbottom = camera.to_screen(self.rect).midtop

        health_bar_rect.y -= 5

        pygame.draw.rect(surface, (60, 0, 0), health_bar_rect)

        current_health_rect = pygame.Rect(

            health_bar_rect.left, health_bar_rect.top,

            int(bar_width * health_ratio), bar_height

        )

        pygame.draw.rect(surface, (255, 0, 0), current_health_rect)

    def update(self):

        if self.renunciationFrozen > 0:
            self.renunciationFrozen -= 1

            return

        self.jumpCooldown -= 1

        self.vel += GRAVITY

        if self.jumpCooldown <= 0:
            self.vel.y -= self.jumpStrength

            self.jumpCooldown = 200

        max_distance = 10 * TILE_SIZE

        if self.direction == "left":

            self.vel.x = -self.speed

        else:

            self.vel.x = self.speed

        if abs(self.rect.centerx - self.spawn_x) > max_distance:

            if self.rect.centerx > self.spawn_x:

                self.direction = "left"

            else:

                self.direction = "right"

        landed, _ = move_and_collide(self, self.vel.x, self.vel.y, self.platforms)

        if landed:
            self.vel.y = 0

        self.bulletCooldown -= 1

        if self.bulletCooldown <= 0:
            self.bulletCooldown = 500

            self.shooting = True

            laser_x = self.rect.right if self.direction == "right" else self.rect.left

            Crown((laser_x, self.rect.centery), self.direction, self.entities, self.bullets, self.playerkillers,

                  self.renunciationBlocked)

        self.animate()

    def animate(self):

        self.animationCooldown -= 1

        if self.animationCooldown <= 0:
            self.animationState += 1

            self.animationCooldown = 15

        if self.direction == "left":

            if self.animationState == 0:

                self.image = pygame.image.load('assets/king.png')

            elif self.animationState == 1:

                self.image = pygame.image.load('assets/king2.png')

            elif self.animationState == 2:

                self.image = pygame.image.load('assets/king3.png')

            elif self.animationState == 3:

                self.image = pygame.image.load('assets/king2.png')

            else:

                self.animationState = 0

        elif self.direction == "right":

            if self.animationState == 0:

                self.image = pygame.transform.flip(pygame.image.load('assets/king.png'), True, False)

            elif self.animationState == 1:

                self.image = pygame.transform.flip(pygame.image.load('assets/king2.png'), True, False)

            elif self.animationState == 2:

                self.image = pygame.transform.flip(pygame.image.load('assets/king3.png'), True, False)

            elif self.animationState == 3:

                self.image = pygame.transform.flip(pygame.image.load('assets/king2.png'), True, False)

            else:

                self.animationState = 0

        if self.shooting:

            self.shootingCooldown -= 1

            if self.direction == "left":

                self.image = pygame.transform.flip(pygame.image.load('assets/king_shoot.png'), True, False)

            else:

                self.image = pygame.image.load('assets/king_shoot.png')

        if self.shootingCooldown <= 0:
            self.shootingCooldown = 30

            self.shooting = False


class MovingPlatform(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):

        super().__init__(*groups)

        self.image = pygame.Surface((96, 32))

        self.image = pygame.image.load('assets/moving_platform.png')

        self.rect = self.image.get_rect(topleft=pos)

        self.speed = 2

        self.vel = pygame.math.Vector2(0, 0)

        self.direction = "left"

    def update(self):

        if self.direction == "left":

            self.vel.x = -self.speed

        else:

            self.vel.x = self.speed

        self.rect.x += self.vel.x

        self.rect.y += self.vel.y


class BlueKey(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((32, 32))

        self.image = pygame.image.load('assets/blue_key.png')

        self.rect = self.image.get_rect(center=pos)


class Crown(pygame.sprite.Sprite):
    def __init__(self, pos, direction, *groups):

        super().__init__(*groups)

        self.image = pygame.Surface((12, 12))

        self.original_image = pygame.image.load('assets/crown.png').convert_alpha()

        self.image = self.original_image.copy()

        self.rect = self.image.get_rect(topleft=pos)

        self.angle = 0

        self.rotation_speed = 3

        self.speed = 5

        self.vel = pygame.math.Vector2(0, 0)

        if direction == "right":
            self.vel.x = self.speed

        if direction == "left":
            self.vel.x = -self.speed

    def update(self):
        self.rect.x += self.vel.x

        self.rect.y += self.vel.y

        self.angle = (self.angle + self.rotation_speed) % 360

        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect(center=self.rect.center)


class BlueDoor(pygame.sprite.Sprite):
    TILE_SIZE = 32

    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.image.load('assets/blue_door_oblique_d8.png').convert_alpha()

        depth = self.image.get_height() - self.TILE_SIZE

        x, y = pos

        self.rect = pygame.Rect(x, y + depth,

                                self.TILE_SIZE, self.TILE_SIZE)

        self._draw_offset_y = -depth

    def draw(self, surface, camera):
        """
        Draw the full oblique image, offset so that
        the 32×32 front face aligns with self.rect.
        """

        draw_rect = self.rect.move(0, self._draw_offset_y)

        surface.blit(self.image, camera.to_screen(draw_rect))


class Trophy(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((32, 32))

        self.image = pygame.image.load('assets/trophy.png')

        self.rect = self.image.get_rect(topleft=pos)


def gameBegin():
    sfx_tempest.play(loops=-1)

    while True:

        clock.tick(60)

        screen.fill((0, 0, 0))

        screen.blit(pygame.image.load("assets/start.png"), (0, 0))

        screen.blit(kFont.render("Press Enter to Begin", True, "white"), (485, 670))

        pygame.display.flip()

        for e in pygame.event.get():

            if e.type == pygame.QUIT:
                sys.exit()

        k = pygame.key.get_pressed()

        if k[pygame.K_RETURN]:
            sfx_song.play(loops=-1)

            return

        if k[pygame.K_ESCAPE]:
            sys.exit()


def gameOver():
    global deflevel
    global lives
    global scorecount
    global magicPoints
    global coinCount

    running = True

    while running:

        clock.tick(60)

        screen.fill((0, 0, 0))

        gameOverText = bigFont.render("GAME OVER", True, (255, 255, 255))

        screen.blit(gameOverText, (440, 300))

        enterToContinue = kFont.render("Press Enter to Continue", True, (255, 255, 255))

        screen.blit(enterToContinue, (450, 620))

        pygame.display.update()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_ESCAPE]:
            sys.exit()

        if keys[pygame.K_RETURN]:
            coinCount = 0

            lives = 5

            scorecount = 0

            deflevel = 1

            magicPoints = magicDefault

            main()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit()


def victory():
    global deflevel
    global lives
    global scorecount
    global magicPoints
    global coinCount

    running = True

    while running:

        clock.tick(60)

        screen.fill((0, 0, 0))

        screen_w, screen_h = screen.get_size()

        victoryText = bigFont.render("CONGRATS! You Win!", True, (255, 255, 255))
        victoryRect = victoryText.get_rect(center=(screen_w // 2, screen_h // 2 - 40))
        screen.blit(victoryText, victoryRect)

        playAgain = kFont.render("Press Enter to Continue", True, (255, 255, 255))
        playAgainRect = playAgain.get_rect(center=(screen_w // 2, screen_h // 2 + 40))
        screen.blit(playAgain, playAgainRect)

        pygame.display.update()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_ESCAPE]:
            sys.exit()

        if keys[pygame.K_RETURN]:
            deflevel += 1

            magicPoints = magicDefault

            callNextCutscene()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit()


def cutscene(title, body_text):
    scroll_speed = 1

    wrap_width = 50

    lines = []

    title_surface = bigFont.render(title, True, (255, 255, 255))

    lines.append((title_surface, title_surface.get_rect(center=(WIDTH // 2, 0))))

    spacing_after_title = 80

    spacing_between_lines = 40

    spacing_between_paragraphs = 60

    normalized = body_text.strip().replace('\r\n', '\n')

    raw_lines = normalized.split('\n')

    paragraphs = []

    current_para = []

    for line in raw_lines:

        if line.strip() == "":

            if current_para:
                paragraphs.append(" ".join(current_para))

                current_para = []

        else:

            current_para.append(line.strip())

    if current_para:
        paragraphs.append(" ".join(current_para))

    for para in paragraphs:

        wrapped = textwrap.wrap(para, width=wrap_width)

        for line in wrapped:
            surf = kFont.render(line, True, (255, 255, 255))

            lines.append((surf, surf.get_rect(center=(WIDTH // 2, 0))))

        lines.append(("PARAGRAPH_BREAK", spacing_between_paragraphs))

    start_y = HEIGHT + 50

    current_y = start_y

    for idx in range(len(lines)):

        item = lines[idx]

        if isinstance(item, tuple) and item[0] == "PARAGRAPH_BREAK":
            current_y += item[1]

            continue

        surf, rect = item

        rect.y = current_y

        if idx == 0:

            current_y += spacing_after_title

        else:

            current_y += spacing_between_lines

        lines[idx] = (surf, rect)

    running = True

    while running:

        clock.tick(40)

        screen.fill((0, 0, 0))

        for i in range(len(lines)):

            if isinstance(lines[i], tuple) and lines[i][0] == "PARAGRAPH_BREAK":
                continue

            surf, rect = lines[i]

            rect.y -= scroll_speed

            distance_from_center = (HEIGHT // 2) - rect.y

            scale = max(0.3, 1 - distance_from_center / 1000)

            scaled_surf = pygame.transform.rotozoom(surf, 0, scale)

            scaled_rect = scaled_surf.get_rect(center=(WIDTH // 2, rect.y))

            screen.blit(scaled_surf, scaled_rect)

        pygame.display.flip()

        for i in reversed(range(len(lines))):

            if isinstance(lines[i], tuple) and lines[i][0] != "PARAGRAPH_BREAK":

                if lines[i][1].bottom < -50:
                    running = False

                break

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                sys.exit()

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    sys.exit()

                elif event.key == pygame.K_RETURN:

                    running = False


def rollCredits():
    running = True

    while running:

        clock.tick(60)

        screen.fill((0, 0, 0))

        startText = bigFont.render("TEMPEST", True, (255, 255, 255))

        end = kFont.render("Written by William Shakespeare", True, (255, 255, 255))

        adapted = kFont.render("Adapted by Jonas Huff", True, (255, 255, 255))

        thanks = kFont.render("Thanks for playing!", True, (255, 255, 255))

        screen.blit(startText, startText.get_rect(center=(WIDTH // 2, 60)))

        screen.blit(end, end.get_rect(center=(WIDTH // 2, 300)))

        screen.blit(adapted, adapted.get_rect(center=(WIDTH // 2, 420)))

        screen.blit(thanks, thanks.get_rect(center=(WIDTH // 2, 470)))

        pygame.display.update()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_ESCAPE]:
            sys.exit()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit()


def printHud(p):
    players = p

    level_text = kFont.render(

        f"ACT: {deflevel}        LIVES: {lives}         GOLD: {coinCount}         SCORE: {scorecount}",

        True, (255, 255, 255))

    screen.blit(level_text, (10, 0))

    global magicUse

    ttColor = (150, 0, 0) if magicPoints <= magicUse else (255, 255, 255)

    player = next(iter(players), None)

    if player is None:
        return

    if player.activeWeapon == 1:
        magicUse = 1

        icon = pygame.image.load("assets/wind_icon.png")

        screen.blit(icon, (10, 40))

        screen.blit(kFont.render("WIND GUST", True, (255, 255, 255)), (50, 40))

        screen.blit(kFont.render(f"MAGIC: {magicPoints}", True, ttColor), (10, 70))

    elif player.activeWeapon == 2:
        magicUse = 5

        icon = pygame.image.load("assets/thunder_icon.png")

        screen.blit(icon, (10, 40))

        screen.blit(kFont.render("LIGHTNING ZAP", True, (255, 255, 255)), (50, 40))

        screen.blit(kFont.render(f"MAGIC: {magicPoints}", True, ttColor), (10, 70))

    elif player.activeWeapon == 3:
        magicUse = 10

        icon = pygame.image.load("assets/spiritbind_icon.png")

        screen.blit(icon, (10, 40))

        screen.blit(kFont.render("SPIRIT BIND", True, (255, 255, 255)), (50, 40))

        screen.blit(kFont.render(f"MAGIC: {magicPoints}", True, ttColor), (10, 70))

    elif player.activeWeapon == 4:
        magicUse = 15

        icon = pygame.image.load("assets/roughmagic.png")

        screen.blit(icon, (10, 40))

        screen.blit(kFont.render("ROUGH MAGIC", True, (255, 255, 255)), (50, 40))

        screen.blit(kFont.render(f"MAGIC: {magicPoints}", True, ttColor), (10, 70))

    elif player.activeWeapon == 5:
        magicUse = 30

        icon = pygame.image.load("assets/sheild.png")

        screen.blit(icon, (10, 40))

        screen.blit(kFont.render("SHEILD", True, (255, 255, 255)), (50, 40))

        screen.blit(kFont.render(f"MAGIC: {magicPoints}", True, ttColor), (10, 70))

    elif player.activeWeapon == 6:
        magicUse = 15

        icon = pygame.image.load("assets/renounce.png")

        screen.blit(icon, (10, 40))

        screen.blit(kFont.render("RENUNCIATION", True, (255, 255, 255)), (50, 40))

        screen.blit(kFont.render(f"MAGIC: {magicPoints}", True, ttColor), (10, 70))

    if player.keys[0]:
        key_img = pygame.image.load("assets/blue_key.png")

        screen.blit(key_img, (WIDTH - 42, 40))

    # fps = int(clock.get_fps())
    # fps_text = kFont.render(f"FPS: {fps}", True, (255, 255, 0))
    # screen.blit(fps_text, (WIDTH - 100, 0))


def main():
    global coinCount, scorecount, lives, deflevel, magicPoints, renunciationActive, renunciationCooldown, level

    global cloud_scroll

    renunciationActive = False

    renunciationCooldown = 0

    camera = Camera((WIDTH, HEIGHT))

    if deflevel == 1:
        level = [
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                      P                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               P   PP      P                 ",
            "                      DP                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              D   DDPPPPPPDPP               ",
            "                     PDD     P                                                                                                                                                                                                                                                                       |                   V                       V              V             |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       DPPPDDDDDDDDDDD               ",
            "                     DDDPPP  D                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        DDDDDDDDDDDDDDDPP  PPP        ",
            "                 PPPPDRDDDDPPD                                                   ***                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  RDDDRRDDDDDDRDDDD PDDDP       ",
            "                 DDDDDRRDDDDDD                                                                                                      *********       E                                                                                                                                        * * * * *                          :              E                                                                                              |       V       |        V         |           V            |                                                                                                                                                                                                                                                                                                                                                                                           RDDDRRRRRRRRRRRDDPDDDDD       ",
            "                PDDDDRRRDDDDDR                                                                                                PP                  PPPPP  P P     PP   PPPP                           >                                                                                                 PPP                    ::::  PPP P  P PPPPPP  PP PPP                 P         P    P                                                                 ***                ***                      ***                                                                                                                                                                                                                                                                                                                                                                                          RRMRRRRRRRRRRRRDDDDDDDDPPP   P",
            "                DDDDDRRRRRRDDR                                                     E                                          DD          PP    PPDDDDDPPD D  PPPDDPP DDDDP                       |  V  |                            E                                                    PP           DDD P             PP  PPPPPPPDDD DPPD DDDDDD  DD DDDPP             PPDP P    PPDP  PDP                                                                             <                                                                                                                                                                                                                                                                                                                                                                                                                           RRRRRRRRRRRRRRRRRDDRRRDDDDPP D",
            "               PDRRRRRRRRRRRRR                                                PP PPPPPP                                    P PDDP         DD  PPDDDDDDDDDDPDPPDDDDDDDPDDDDD                                                       P PPP                                                   DDPPPP   P PPDDDPDP  PP        DDPPDDDDDDDDDDPDDDDPDDDDDDPPDDPDDDDDPP           DDDDPDPPP DDDDP DDDPP     *                                        PPP                         PPP                            PP                                                                                                                                                                                                                                                                                                                                                                                            RRRRRRRRRRRRRRRRRDMRMRRDDDDDPD",
            "            PPPDDRRMRRRRRRRRRR                                         *      DD DDDDDD               |         V       | PDPDDDD P  PP  PDDPPDDDDDDDDDDDDDDDDDDDDDDDDDDDDDP    E <E                                              DPDDD P                                        PP      PDDDDDDPPPDPDDDDDDDDPPDD       PDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDPPP      PPDDDDDDDDDPDDDDDPDDDDD      *                                       DDD                         DDDP               P           DDP                                                                                                                                                                                                                                                                                                                                                                                           RRRRRRRRRRRRRRRRRRRRRMRDDDDDDD",
            "         S SDDDDRRMRRRRRRRRRRR                                        *   PPPPDDPDDDDDDP                                  DDDDRRDPD  DD  DDDDDDDDDRRRRRDDRDRDDDDDRRDDDRRRRDD   PPPPPPP       PPP  P                            PPPDDDDDPDPPP                                    PDDP P  PDDDDDDDDDDDDDDRMRDDDDDDDPP <>  DDDDDDDDDDDDRRRDRDDRDRMRMRRDDRRDRRMDDDDDDDPPPPP DDDDRDDDDDDDDDMDDDDRDDDP      *                                    PPDDDPPP                    PPDDDD         P     DP PP PP PPPDDDP                                                                                                                                                                                                                                                                                                                                                                                          RRRRRRRRRRRRRRRRRRRRMRRRRRDDDR",
            "MRRRRRRRRRRRDDDDRRRRRRRRRRRRRM  P                                    *    DDDDDDDDDDRRDDPP                             PPPDDDDRRDDDPPDDPPDRRDDDDRMRRRRRRRRDRDDRRRRRRRDRRRRRDP  DDDDDDDPP     DDDP DP       PPP            PPPP DDDDDDDDDDDDDPP                                  DDDD D  DDRRDDDDDDDDDDDMRRDRDDDDDDD PP PDRRDDRRRRRRRRRRDRRRRDRRRRMRDDRRDRRRRRDDDDDDDDDDPDDRRRRDRDDDDRRRRDDRRRDDD       *                                   DDDDDDDD        PPP         DDDDDDP P PPPPPDP PPPDD DDPDDPDDDDDDD  P                                                                                                                                                                                                                                                                                                                                                                                       RRRRRRRMRRRRRRRRMRRRRRRRRRRRDR",
            "RRRRRRRRRRRRDDDRRMRRRMRMRRRRRR  D             X                     *   PPDDDDRRDRRRRRRDDD     <E                      DDDDRDRRRRDDDDDDDDDRRDDRRRRRRRRRRMRRRRRRRRRRMRRRRRRRDDPPDDDDDDDDD    PDDDDPDDP   PPPDDD       PPP PDDDDPDDDRDRMRDDDDDDD      |        V          |    PPPDDDDPDPPDDRRRRRRDDDRDRRRRRRRRDDRRDDPDDPDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDDDDDDRMRMRRRRRDRRRRRDRRRRRDPPP     *                             PPPPPDDRMRDDDPPPP    DDD   P PPPPDDRRRDDPDPDDDDDDDPDDDDDPDDDDDDDDDRRDDP DPP                                 E                                                                                                                                                                                                                                                                                                                                                   RRRRRRRRRRRRRMRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRMRRRRRRRRRRR PDP           PPPPP                 *    DDDDDDRRDRRRRRRDDD PPPPPPPPPP       ***      PPDDDRRRRRRRDRDDRRDDRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRMRRRDDDDDDDDDDDDP  PDDDDDDDDDPPPDDDDDDP      DDD DDDDDDDDDRRRRRDRDDDDDPPPP                        PP DDDDRRDDDDDDRMRRRRRRRRRRRRRRRRRRRRRRDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDRRRMRRRRRRRRRRRRRRRRRRMDDDDPP    *                            DDDDDDDRMRDDDDDDD P PDDDPPPDPDDDDDDRMRRDDDDDDDDDDDDDDDRDDDDDDDDDDDMRRDDPDDDP P                         PP PPPPP                                                                                                                                                                                                                                                                                                                                                 RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRMRRRRRRRRMRRRRRRRRRRRRRRRRR DDDP         PDDDDD    *****            PDDRRRRRRRRRRRRRRDDPDDDDDDDDDD    PP       PPPDDDDDRRRMMRRRRDDRRDDRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRDDDRRRRRMRDDDP DDRRRDDRDDDDDDDDDDDD     PDDDPDDDDDDRRRRRRRRRRMRRDDDDDD                        DDPDDDRRRRDRDDRRRRRRRRRRRRRRRRRMRRRRRRRRRDDDDDRRRRRRRRRRRRRRMRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRDRRRRRRRRRRMRRRRRRRRMRRRRDDDDD     * |          V        |   PPDDDDDRRRRRRRRDDDDPD DDDDDDDDDDDDDRRRRRRDDDDDDDDDRDDDDDRRDRRDRRDRRRRRRRDDDDDDPD      E                  DD DDDDDP                                                     E                                                                                                                                                                                              P         *                                                                                 RRRRRRRRRRRRMRRRRRRRRRRMMRRRRR",
            "RRRRRRRRRRRRRRRRRRRMRRRRRRRRMRPDRDD       P DDDDDDPP             <   :PDDDRRRRRRRRRRRRRRMRDDDDDDDDDDDPP  DD:   PPPDDDDDRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRDDRRRRRRRRRDDPDDRRRRDRRDDDDDDDRRRDPP PPDDDDDDRRRRDRRRRRRRRRMRMRRRDDDDPP                     PDDDDDDRRRRDRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRDRRRRRMRRRRRRRMRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDPP    *                       PDDDDDDDRRRRRRRRDDDDDDPDRRRDDDDDDDDDRRRRRRRDRDRRRRRRRDRRMRRDRRRRRRRRRRRRRDDRDDDDDPP P PPPPP             PPDDPDDDDDD                                                P : PPP                                                                            P                                                                                                                D          *                                                                                RRRRRRRRRRRRRMRRRRRRRRRMRRRRRR",
            "MRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDRDDPPPPPPPDPDDDDDDDD           PPPPPPPDDRRRRRRRRRRRRRRRRRRDDDDDDDDDDDDDPPDDPP: DDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRDDDDRRRRRRRRRDDDRRRRRRDDDPDDDRRRDRRMRRRRRRRRRRRRRMRRRRDDDDDDPP   *************   DDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRMRRRRRRRRRRRDDDD                          PPDDDRRRRRRRRRRRRRRRRRDDDDMRRDDDRDRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRDRMRDDDDDPDPDDDDD P         PPDDDDDDDDDDDP        |              V            |     P PPPDPPPDDD           P                        P                                   P   D                                                                             <            E                   PPDPPPP P     *                                                                               MRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "MRRRRRRRRRRRRRRRRMRRRRRRRRRRRRDRRMDDDDDDDDDDDRRRRRDDPP    P PPPDDDDDDDDDRRRRRRRRRRMRRRRRRRRRRRMRRRRRRDDDDDDDDPPDDDDDDRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDRRRRRRRRRRRRRRRRRRRRDDDDDDRRMDRRRRRRRRRRRRMRRRRRMRRRMRMDDDD                  PDRRDRRRRRMRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRDDPPP              <       PDDDDDRRRRMRRMRRRRRRRRRDRDRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRDRDDDDDDDDDDPDP       PDDDDRRDRRRRRDDPP                              P   PP PP D DDDDDDDDDDPP         D                      P DP   P                             PD  PDPP                                                                          PPP        PPPPPP                 DDDDDDDPDP  PP *                                                                             PMRRRRRRRRRRRRRRRRMRRRRRRRRRRRR",
            "MRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDMRRRDDDDDDDDDRRRRRRDDDD    DPDDDDDDDDDDDRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMDDDDRRDDDDDDDRMRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRDRRRRRRRMMRRRRRRRRMRRDDDDDMRRRRRRRRRRRRRRRRRMMMRRRRRRRMRDDDDPPP P           P DDRRRRRRRRRRRMRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRMRRRRRRRRRRRMDDDDDPPP           P       DDDDRRRRRRRRRRRRRRRRRRRRRDRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDDDDDDDD       DDDDDRRDRRRRRRDDDPP                            D PPDDPDDPDPDDDDDDDDRDDDPPPPPPPPPDP         P    P  P  PDPDD PPD                      E   P  DDPPDDDD                                                          P           P   DDD  P     DDDDDDPPP            PPDDRDDDDDDDPPDD   PPP                                                                         DMRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRMRRRMRRRRMRRRRMRRRRRRRRRRRRRDDDDDDDRDRRMRRMRMDDPPPPDDDDDDDDDDDDRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRDDRRDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRDDDDD D           DPDRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRMRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRMRRRRMDDDDDD         P D    PPPDDDRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRMRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRDRRRRRDDDPP    PDDDRRRRRRRMRRRDDDDDPPPPP                      PDPDDDDDDDDDDDDDRDDDRRRDDDDDDDDDDDDD       P D    DPPDPPDDDDDPDDDP                <  PPPP  DPPDDDDDRDDP                   P                                     D           D  PDDDPPD    PDDDDDDDDDPPP P       DDDDRDDDDDDDDDDDP  DDD                                                                     PPPPDRRRRRRRMRRRMRRRRMRRRRMRRRRRRRR",
            "RRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRMRRRRRRRRMRRRRRRRRDDDDDDDDDDDRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRMRRRRRRRRRRDDRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRDDDPDPPP     PPPDDDRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRDDDDDDP        DPDPP  DDDDRRMRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRDDD    DDRRRRRRRRRRRRRRDDDDDDDDD                <     DDDDDDDDDDDRDRRRRRRRRRRDDDDDDDDDDDRDPP     DPDPPPPDDDDDDDDDRDDDDDD               PPPPDDDDPPDDDDRDDDRDDDPP                 D         *                          PDP      PPPPDPPDDDDDDDPP PDDDDDDDDDDDDDPD    P PDDRRRMRRRDRDDDDDD PDDDP                                    PP                         PPPP DDDDDRRRRRRRRRRRRRRRRRMRRRRMRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDDD    :DDDDDMRRRRRMRRRRRMRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRDDDD   P   PDDDDD PDDDRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDP> PDRRRRMRRRRRRRRRRRRDDDDDDDPPPP           PP  PPPDRDDDRRDRRDMDRRRRRRRMRRRRDDDDDDDDDRDDD  PPPDDDDDDDDDDDDDDRDRRDDDRDP             PDDDDDDDDDDDDDRRDDMRRRDDD                PDPP|     *V*           |     P       DDD      DDDDDDDDRRRDDDDD DDMRRRRRDDDDDDDDPP  D DDDRRRRRMRRRRDDRRDPDDDDDP      * * * * * * * *           P  DD            PPP        P DDDDPDDDDMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRR",
            "RRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMDDDDRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRMRMRRRRRRMRRRRRRRRRRRMRRDRDDDPP PPDDDRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRDP  DPPPDDDRDDPDDDDRRRRRRRRRRRRRMMRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDPPDDRRRRRRRRRRRRRRRRRRRDDDDDDDDDPPP  P    PDD  DDDDMDRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRDDPPDDDDDRDDDDRDDRDDRRRRRDRRRDDP            DDDDDDDMDDDRDDRRRMRMRRDDDPPP            PDDDD     *   *           PPPPPDPPP PPPDMDPP PPPDDDDRDDDRRRDDRDDPDDRRRRRRRRRDDDDDDD PDPDRRRRRRRRMRRRRRRRDDDRRRDD  PP                           PDPPDDP          PDDDP         DDDDDDDDDRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRDRDDDDD DDDDDRRRMRRRRMRRRRMRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRDDPPDDDDDRDRDDDDRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRMRRRRRMRRRRRRRRRRRRRRRRDDDDRRRRRRRRRRRRRRRRRRRMRRRRRDDDDDDDPPD    DDDPPDDDMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRDDDDDDDRDRDDDDRRRRRRRRRRRRRRRRDDPP         PDDDDDRRRRDDRMRRRRRRRRRRDDDDD            DDRDDP   *     *         PDDDDDDDDD DDDDRDDDPDDDDDDDRDDRRRRMRRDDDDRRRRRRRRRRRRRDRDDPDDDDRRRRRRRRRRRRRRRRRDDRRRDDP DD PPP           PP          DDDDDDD          DDDDDP           DDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRMRRMRRRRRRRRRRRRRMMRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRMRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRDDPDDRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRDDDDDDDDRRRRRDDRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRMRRRRRRRRRMRRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRRRRRMRRDDDDRMRRRRRRRRRRRRMRRRRMRRRRRDDDDDDDDDDPPPPDDDDDDDDRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDRRRRRRRRRRRRRRRRRRRRRRRDDDD    P    DDRRRRRRRRRRRRRRRRRRRMRMRRDDDPPP       PPDDRDDD           E     PPDDDDDDDDDDPDDDRRRDDDDDDMRRRRRRRRRRRRRRRDRRRRRRRRRRRRRRRRDDDDRDRRRRRRRRRRRRRRRRRRDMRRMRDDPDDPDDD       P   DD  P     PPDDDDRRDP       PPDDDDDDP                RRRRRRRRRRMRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRMRRRRRRRRMRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRMMMRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRMRRDDDDDMRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDDDRDDDRRRRRRDRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRDDRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMDDDDDDDDDDDRRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDSSSSD  SSDRRRRRRRRRRMRRRRRRRRRRRRRRDDDDDD   SSSSDDDRRRRDS S       SSS    DDDDDDDDMDDDDDDDRRRDDDDDDRRRRRRRRRRRRRRRRDRRRRRRRRRRRRRRRRRRDDRDMRRRRRRRRMRRRRRRRRRRRRRRRDDDDDDDDSS    SDS SDDSSDSSS  DDDRDDRRDD   SS  DDDRRRRRRRRR     C       RRRRRRRRMRRRRRRRRRRRRRRRRMRRRRR",
            "RRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRMRRRRRRRRRRRRRMRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRMRRRRRDRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRDDRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRDDRDDDDRRRDDRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRDDRRRRDRRRRDRRRRRRRRRRRRMRRRRRRRRRRRRMRRDDDRRRRRRRDDRRRRRDRRRRRRRRRRRRRRRRRDDDRRRRMRRRRDRRRRRRRRDRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRDRRRRRRRRRRRRRRRMRRRRRRRRRRRRDDRRDDDDRRRRRRRDRRRDDRRDRRRRRDDRRRRRRRDRRRRRRRDDRRRRMRR                 RRRRRRRRMRMRRRRRRRRRRRRRRRRRRR",
            "MRRRMRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRDDDDRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRMRDDDRRRRRRRDDRRRRRRRRRRRRRRRRRRRRRRRDDRRRRRRRRRRDRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRDRRDRRRRRRRRRRDRRRRMRRDRRRRRDDRMRRRRRDMRRRRRRDDRRRRR               RRRRMRRRMRRRRMRRRRRRRRRRRRRRRRRMRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRMRMRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRMRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRMRRRRRRRRRRRMRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR         RRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR           RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR  ^   RRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRMRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRMRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRMMRRRRRRRRRRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRMMRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRMRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRMRMRRRRRRRMRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRMRRMRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRMRRRRRRRRRRRRRMRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRMRMRRRRRRRRRRRRMRRRRRRRRRRRMMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMMRRMRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRMRRRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRR",
            "RRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRMRRRRRRRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRMRRMRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRMRRRRRRRRRRRRRMRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRMRMRRRRRRRRRRRRMRRRRRRRRRRRMMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMMRRMRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRMRRRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRR",
            "RRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRMRRRRRRRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRMRRMRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRMRRRRRRRRRRRRRMRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRMRMRRRRRRRRRRRRMRRRRRRRRRRRMMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMMRRMRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRMRRRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRR",
            "RRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRMRRRRRRRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
        ]

    elif deflevel == 2:
        level = [
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                               ;;;;;;;;;;;;;;;;;;;;;;                                                                                                                                                       ",
            "                                                                                                                               ;                    ;                                                                                                                                                       ",
            "                                                                                                                               ;                    ;                                                                                                                                                       ",
            "                                                                                                                               ;                    ;                                                                                                                                                       ",
            "                                                                                                                               ;   C      C         ;                                                                                                                                                       ",
            "                                                                                                                               ;                    ;                                                                                                                                                       ",
            "                                                                                                                               ;                    ;                                                                                                                                                       ",
            "                                                                                                                               ;;;;;;;;;;;;;;;;;;;;;;                                                                                                                                                       ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                            ",
            "                P                                                                                                                                                                                                                                                                                           ",
            "              PPDPP                                                                                                                                                                                                                                                                                         ",
            "              DDDDDPP P                                                                                                                                                                                                                                                                                     ",
            "             PDDDDDDD D                                                                                                                                                                                                                                                                                     ",
            "             DDDRDDDDPDPP                                                                                                                                                                                                                                                                                   ",
            "           PPDRRRRRDDDDDDP  PP                                                                                                                                                                                                                                                                              ",
            "       PPPPDDDMRRRRRRDRDDDP DD                                                                                                                                                                                                                                                                        P     ",
            "      PDDDDDDRRRRRRRRDRDDDDPDD                                                                                                                                                                                                                                                PPPP     PPPP   P  P  PPD     ",
            "  SS  DDDDDDDMRMRRRRRRRRRDDDDD                                                                                                                                                                                                                                                DDDD     DDDD   DSSD  DDDSSSSS",
            "RMRRRRDDDDDRRRRRRRRRRRRRRRDDRR                                                                                                                                                                                                                                                DDDDRRRRRDDDDRRRDRRDRRDDDRRRRR",
            "RRRRRMDRRMRRRRRRRRRRRRRRRRRDRR                                                                                                                                                         ^               PPP P                                                                  DDDDRRMRRDDDDRRRDRRDRRDDRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRMRRRRR                                                                                                                                                       PPPPP           P DDD D  PP                                                              RRRRRRMMRRRRRRMRRRRMRRMRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                                            *                          *                                                                               DDDDDP    PP    DPDDDPDPPDD     E                                                        RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRMRMRRRRRRRRRRRR                                           * *                        * *                                                                             PDDDDDDPPPPDDP PPDDDDDDDDDDDPPP PPPPP  P                                                  RRRRRRRRRRRRRRRRRRRRRRRRRRRMRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRM                   | V  |        *        *   *      P               *   *                                                                            DDDDDDDDDDDDDD DDDDRRRDRDDDDDDD DDDDDPPDPPPP                                              RRRRRRRRRRRRRRRRRRRRRRRRRRRRRM",
            "RRRRRRRRRRRRRMRRRRRRRRRRMRRRRR                                * *                PPDPP   P        E      ?                                                                       PPPDRDDMDDDDDDDDDPDDRDRRRDRDDRRDDDPDDDDDDDDDDDDPPPP                                          RRRRRRRRRRRRRMRRRRRRRRRRMRRRRR",
            "MRRRRRRRRRRRRRRRRRRRRRRRRRRMMM                               *   *  PP     P     DDDDD   D       PPPPP  ><>                                                                    PPDDDDRRDRRRDDDDRRDDDDRRRRRRRRRRRDDDDDDDDDDDDDDDDDDDD                                          MRRRRRRRRRRRRRRRRRRRRRRRRRRMMM",
            "RRRMRRRRRRRRRRRMRRMRRRRRRRMRRR                                  PPPPDDPP   D    PDDDDDPPPDP     PDDDDDPPPPP                      PP              PP                           PDDDDDRRRRRRRRRRRMRRDRRRRRRRMMRRRRRRRDRRRRRDDRDDDDDDDDP   PP                                    RRRMRRRRRRRRRRRMRRMRRRRRRRMRRR",
            "RRRRRRRMRRRRRRRRRRRMRRRRRRRRRR                                  DDDDDDDDPPPDP   DDDRDDDDDDDPPPP DDDDDDDDDDDP           P       PPDDP         P  PDDPP                         DDDDDDRRRRRRRRRRRRRRDRRRRRRRRRRRRRRRRDRRRRRRRRMRRRDDDDD PPDDPP                      C       P   RRRRRRRMRRRRRRRRRRRMRRRRRRRRRR",
            "RMRRRMRRRRRRRRRRRRMRRRRRRRRMRR                  PPP P        PPPDDDDDDDDDDDDDPPPDRRRRRDDDMDDDDDPDDDDDDDDDDDR           D P   PPDDDDD         DPPDDDDD   PP                    DDDRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRDPDDDDDDPP  P      P                  D   RMRRRMRRRRRRRRRRRRMRRRRRRRRMRR",
            "RRRRRRRRRRRMRMRRRRRRRRRRRRRRRRPP              P DDDPD PP    PDDDDDDDRMDDDDDRDDDDDRRRRRDDDRDDDDDDDRRRRRDDDDRR         PPDPD PPDDDDDDDPP  P  PPDDDDDDDDP  DDP                              =      RRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRDDDDDDDDDD PD      DPPP;;;;;;;;;;;;; PDPP RRRRRRRRRRRMRMRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRMRRRRRRRRDD              DPDDDDDPDD    DDDDRRRRRRRRDDDRDDDDMRRRRRRRRRRDDDDDRRRRRRRRRRRR           RDDPDDDDDDRRDDDPPDP DDDDDDRRDDDXPDDD                              =              RRRRRRRRRRMRRRMRRRRRRRRRMRRRRDDDRRDDDDPDDPPPPPPDDDD:           PPDDDDPRRRRRRRRRRRRRRRRRRRRRMRRRRRRRR",
            "RRRRRRRRRRRRRRRRRMRRRRRRRRRRRRDDP            PDDDDDDDDDDPPPPDDDDRRRRRRRRRRRRMDDDRRRRRRRRRRRRRRRDRRRRMRRR            RRRRRDDDDDDRRRRRDDDDDDPDDRDDRRRRRDPDDDDPP         E                  =                RMRRRRRRRRRRRRRRRRRRRRRRRRRDRRRRRRDDDDDDDDD      =     :     DDDRDDDRRRRRRRRRRRRRRRRRMRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRRRRRRRRRRRRRRRDDD            DDDRRRDRDDDDDDDDRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRR   =           RRRRRRRRDDDRRRRRRRDDDDDDDDDRRRRRRRRDDDMRDDDS  SSSRRRRRRRR              =                       RRRRRRRRMRRRRRRRRMRRRR            =       =     =    SDDDRDDDRRMRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR         RRDRDRRRRMDRRDDDDRRRRRRRRRMMRRRRRMRRRRRRRRRRRRR            =             RRRRRRDRRRRRRRRRRRDDRDDRRRRRRRRRRRDDRRRDDRRRRRRRRRRRRRRRRRRRRR       =                            =                            =       =  :: =    RDDRRMRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRR         RRMRRMRRRRRRDDDDRRRRRRRRRRRRRRRRR     =                   =          RRMMRRRRRRRRRRRRRRRRRRRRMDRRRRRRRRRRRDRRRRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRR                        =                            =       RRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRM        RRRRRRRRRRRRRRMRRRRRRRRRRR            =                   =    RRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                    =     C                     RRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR    RRRRRRRRRRRMRRRR                     =                  RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                =                        MRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRMRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRR    RRRRRMRRRRR                   C      =         < RRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRMM               =                  RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRMRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR        RRRR                             =       RRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR        =       C                      =   MRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRR",
            "RRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRR      =                     RRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRR     =         RRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMMRRRRRR",
            "RRMRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRR",
            "RRRRMRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "MRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRMRRRRRRRRMRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRMRRRMRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RMRRRRRMRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRMMRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRMRRRRRRRRRRMRRRRRRRRRRRRRMRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRR",
            "RMRMRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRMRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRMRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRMRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRMRRRRRMRRRMRRRRMRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRMRRMRRRRRRRMRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRMR",
            "RRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRMRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRMRRRRRRMRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRMRRRRRRRRRRRRRRRRMRMRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRMRRRRRRRRRRRRRRRMRRRRRRR",
            "RRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRMRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRMRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRMRRMRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRMRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRMRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRMRRRRRRRMRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMMMRRRRRRRRRRRRRRRRRRMRRRRRRR",
            "RRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRMRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRR",
            "RMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRMRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRMRRRRRRRMRRMRRRRRRRRRRRRMRMRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRMRMRRRRRRRMRR",
            "RRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRMMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRMRMRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRMRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRR",
            "RRRRRRRRRRRMRMRRRRRRRMRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRMRMRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRR",
            "RMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRMMRRRRMRMRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRR",
            "RRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRMRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRMRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRMRRRRMRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRMRRRMRMMRRRRR",
            "MRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRR",
            "MRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRMMRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMMRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRMRRR",
            "RRRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRMRRRRRMRMRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRMRRRMRMMRRRRRMMMRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRR",
            "RRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRMRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRMRRMRMRRRRRRRRMRRRRRRRRRRRRRMRRRRMRRRRRRRRRRMRRRMMRRRRRRRRRRRR",
            "RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRMRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRR",
            "RRRRRRRRMRRRRMRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRMRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRR",
            "RRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRMRRRRMRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRMRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRMRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRMRRRRRRRRRMRRRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRMRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRR",
        ]

    elif deflevel == 3:
        level = [
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       P   PPP      ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       D  PDDD      ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      PPPP       P    PDPPDDDDP PPPP",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      DDDD     P D   PDDDDDDDDDPDDDD",
            "                                                                                                                                                                                                                                                                                                                                                               ;                                                                                                                      DDDDP    DPDPPPDDRDDDRRRDDDDDD",
            "                                                                                                                                                                                                                                                                                                                                                               ;                                                                                                                      DDDDDPPPPDDDDDDDDRDDRRRRDDDDDD",
            "                                                                                                                                                                                                                                                                                                                                                               ;                                                                                                                      RRRRDDDDDDDRDDDDRRRRRRRRRDRRRR",
            "                                                                                                                                                                                                                                                                                                                                                               ;                                                                                                                      MRRMDDDDDRDRDDDRRRRRRRRRRRRMRR",
            "                                                                                                                                                                                                                                                                                                                                                               ;                                                                                                                      RRRRRDDDDRRRMRRRRRRRRRRRRRRRRR",
            "                                                                                                                                                                                                                                                                                                                                                               ;                                                                                                                      RRRMRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "                                                                                                                                                                                                                * * * * * *                                                                                                                                    ;                                                                       * * * *                                        RRRRRRRRRRRRRRRRRRMRRRRMRRRRRR",
            "                                                                                                                                                                                      * *                                                                                       * * * * * *                                                                    ;                                                                                                                      RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "                                                                                                                                                                                     * * *                                                                                                                                                                     ;                                                                                                                      RRRRRRRRRRRRRRRRRRRRRRRRRMRRRR",
            "                            PP                                              E                                                                            E                                                             <  E                                                                     E                                                              ;                                                                             E                                        RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "                         PPPDD                                       P    PPPP                     PP PPP                               P   P P <    P  PPPP P                                          PPPPP   PPPPPPPPPPPPPPP                             *             PP PPPP P       P PPPPPPPPPP                                                         ;                                                                       P  PPPPPPP                                     MRRRRRRRRRRRRRRRMRRRMRRRRRRRRR",
            "              P          DDDDD                                       DP PPDDDDPP PPPPP             DD DDD P                         PPP D  PDPDPPP PPDP DDDD D  P                  <<        E    PP PPPDDDDD PPDDDDDDDDDDDDDDDPP  P                      *   *       PPPPDDPDDDD DP  PPPPDPDDDDDDDDDD                                                         ;                                                                 P   PPDPPDDDDDDD P                                   RRMRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "              D         PDDDDD                                     PPDDPDDDDDDDD DDDDDP  PP    PP PDDPDDDPD    *      *            PDDDPDP DDDDDDDPDDDDPDDDDPDPPD                 PPPP   PPPPPPP PDD DDDDDDDDPDDDDDDDDDDDDDDDDDDDPPD PP  PP                         PPDDDDDDDDDDDPDD PDDDDDDDDDDDDDDDDPP                                                       ;                                                      *          DPPPDDDDDDDDDDDDPD                                   RRRRRRRRRRRRRRRRRRRRRRRMRMRRRR",
            "            PPDPPPP     DDDDRR                   ?   PP            DDDDDDDDDDDDDPDDDDDDP DDP   DDPDDDDDDDDDP    *    *            PDDDDDDDPDDDDDDDDDDDDDDDDDDDDDDP                DDDD   DDDDDDDPDDDPDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDPDDPPDDPPP            PPPPP   PPDDDDDDDDDDDDDDDDPDDDDDDDDDDDDDDDDDDD        P                                              ;                                                     *         PPDDDDDDDDDDDDDDDDDDP                                PPRRRRRRMRRRRRRRRRRRRRRMRRRRMRRR",
            "  S   SSS SSDDDDDDDSS SSDRRMRR                  ;;; PDD   P    PPPPDDRDDDDRRRRDDDDDDDDDDPDDDPPPDDDDRRDRRRDDDP    *  *       PPP   DDDDDDRDDDRDRDDDDDDRDDRRRRDMDDDD PP PP         PDDDDPPPDDDDDDDDDDDDDDDRRRRRDDDRRRMRRRRMRRRRRRDDDDDDDDDDDDDDDP    P  P   DDDDD   DDDDDDDDRRDRMRRDMDDDDDDDRDRMRRRRRRRRDDP    PPPD  P                                           ;                                                     *         DDDDDDDDRDDRRRRRRRDDDP                               DDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRMRRRRDDRDDDDRRRRRDRRRRR                  ;;;PDDDP PDP   DDDDDDRRDRRRRRRRMDRRRRRDDDDDDDDDDDDDRRDRRRDRDDP    **        DDD PPDDRRRDRDDRRRRRRRDRRRRDRRRRDRDDRDPDDPDDPPP  P   DDDDDDDDDDDDDDRDDRRDRRRRRRRRDRRRRRRRRRRRRRRRMRRRDDRDDDDDDDDDDDPPP D  D PPDDDDDPPPDDDDRRRRRRRRRRRDRRDDRRRRMRRMRRRMRRRRDDD P  DDDDPPD                                           ;                                                    *         PDDMDDDRRRRRRRMRRRRDRDD    P                       PPPDDRRRRRMRRRRRRRRRRRRRRRRRRRRRRMR",
            "RRRRRRRRRRRRDDRDDDDRRRRMRRRRRR                  ;;;DDDDD DDDPPPDDDDMRRRRRRRRRRRRDRRRRRRDDRRDDDDRRDRRRRRRRRRRRRR           PPDDDPDDDRRRRRRRDRRRRRMRRRRRRRRRRRRMRRRDDDDDDDDDD  DP PDRRRRDDDRRMRRRRDRRRDRRRRRRRRRRRRRRRRRRMRRRRRRRRRMMRDRMDDRRDDDDDDDPDPPDPDDDDDDDDDDDDRRRRRRRRRRRRRRRRDRMRRRRRRRRRRRRRRRRRDPDPPDDDDDDDPPP                                        ;                                                   *          DDDRRRRRRRRRRMRRRMRRRDDPP  D                       DDDDDRRRRRRRRRRRRRRRRRRRRRMRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                  RRRMRRRDPDDDDDDDDDDRRRRRRRRRRRRRRRRRRRRRDRRRDDDRRRMRRRRRRRRRRRR   ::    PPDDDDDDDDRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRDDDDDDDDDPPDDPDDRRRRDDDRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDDDDDDDRRRRRDDDRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRDDDDDDDDRDDDDDDP                                       ;                                                   *        PPDRRRMRRRRRRRRRRRRRMRRRDDDPPDPPP                PPPPDDDRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                        RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR   ==    DDDDRRRDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRDRRDDDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRDDDDRDDRDDDRRRRRDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMDDDDRRRRDDRDDDD                                       ;                                                  *       P DDDRRRRRRRRRRRRRRRMRRRRRRDDDDDDDD  P      ^      DDDDDDDRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRMRRRMR                          =               RRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRR   ==   PDDDDRRRDRRRRRMRRRMRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRDDRDDDMRRRRRRRRRRRMRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRMRRRRRRRDRDDRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMDRDDRRRRRRRDDDDP                                      ;                                                          DPDDRRRRRRRRRRRRRMRRRRMRRRRDDDDMDDDP DP    PPP  PPPDDDDRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRR",
            "MRRRRRRRRRRRRRMRRRRRRRRRRRRRRR            P             =        V          =   RRRRRRMRRRRRRRRRRRRRMRRRRRRRRRR   ==   DDDRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDRMDRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRDDPPP                                   ;                                                       P PDDDDRRRRRRRRRRRRRRRRRRRRRRRRMDDRDDDDPDD PP DDD  DDDDDDDRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRMRRRRRRRRRRRRRRRR        X   DP            =  ***   ***        =  *     RRRRRRRRRRRRRRRRRRRRRRRRRRR  ==  RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRDDDDP                                  ;                                             C         D DDDRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRDDDDPDDPDDDPPDDDRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRR",
            "RRMRRRRRMRRMRRRRRRRRRMRRRRRRRR  P  P PPPPPDDPDRRRRRRR   =     ***           =   *        RMRRRRRRRRRRRRRRRRRRRRR  ==  RRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRMRRRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDDDD  :  :                  PP         ;                               C                      PDPDRDRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRMRDDRDDDDDDDDDDDDDRRRRRRRRRRRMRRRRRMRRMRRRRRRRRRMRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR  DP D DDDDDDDDDRRRMRRRRRRRRRRRR              =    *              RMRRRRRRRRRRRRRR  ==  RRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR              =  =  :         PPPP  DD PP  PPP ;             ***                                   PPPDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRDDDDRRRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RMRRRRMRRRMRRRRRRRRRRRRMRRRRRR PDDPDPDDDDDRDDRRRRRRRRRRRRRRRRRRRRRRRR       =     *                    =          ==        =     RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR       =                   =  =  =  :   RRMRRDDPPDDPDDPPDDD ; P          *   *                     P   P        DDDDRDRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRMRRDRRDRRRDDRRRRRRRRRRMRRMRRRRMRRRMRRRRRRRRRRRRMRRRRRR",
            "RRRRRRRRRRRMRRRRMRRRRRRRRRRRRRPDDDDDDDDDDDRRDRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMMR   *                   =          ==        =                    MRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRM                             =                   =  =  =  = RRRRRRRDDDDDDDDDDDDDDPPPDPP       *     *            PP     PD   D P     PDDDDRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRR",
            "MMRMRRRRRRRRRRRRRRRRRRRRRRRRRRDDRDDRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRMRRRRRR   *          *  *    =    *     ==        =                                     =              RRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRMRRRRRRMRRRRRRRR     =                               C   =                   = RRRRRRMRRRRRRRRRRRDDRRDDDDDDDDDDDDDD                          DDP P  DDP PDPD     DDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRRMMRMRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDRRDRDRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR       <            =          ==        =           C        V                =                       RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRR                      =                                   =                   =RRRRRRRRMRRRRRRRRRRDDRMDRRDDRRRDDDDDDPPP          P         PPPDDDPDPPDDD DDDDP  PPDRRRRMRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRMRRRRRRRRRRRRRRRRMRRRRRRRDMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR         =          ==        =                                     =                          RRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                          =                                   =                  RRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDRDDDDDPPPP    P DPPP      DDDDDDDDDDDRDPDRDDDP DDDRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRR        ==        =                                     =                V                 RRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRR                             =                                   =             RRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDD    DSDDDDSSSSSSDDDRRDDDDDRRDDDRDRDDSDDRRRRMRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMMR",
            "RRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR       =                                     =                                       RRRMRRRRRRRRRRR   =                                   C     =                                   =       RRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRDDDDDDDRRRRDRDDDDRRRRRRDDDRRMDRDDMRRDRRRRDDRDDRRRMRRRRMRRRRMRRRMRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRR       <               =                                                         =                                         =                             <    RRRRMRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRDDDDRRRRDMRDDDRRRRRMRRRRRRRRRRRRMDRRRRRDRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRR             =                              C                          =                                         =                         RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRMRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                                                   =                              <          =           RRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRMRRMRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRR                                  =                     RRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRR",
            "RRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRR                         =   RRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRRRRRRRMRRRRRRRRRRRR",
            "RMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRR      >       RRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRMRRRMRRRMRRRRRMRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "MRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRMRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRMRRRRRRMRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRMRMRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRMRRRMRRRRRRMRRMMRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRMRMRRRRRRRRRRRRRRRRRRMRRRRRR",
            "RRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RMRRRRRRRRRRRRRRRRRRRRMRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRMRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMMRRRRRRRRRMRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRR",
            "RRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMMRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRMMRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRR",
            "RRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRMRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMMRRRRMRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRMRRRRRRRRRRMRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMMRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRMRMRRMRRRRRRRRRRMRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRMRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRR",
            "RRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMMRRRRRRRRRRRRRMRRRMRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRR",
            "RRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRMRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRMRRRRRRRMRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRR",
            "RRMRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMMMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRMRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMMRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRM",
            "MRRRMRMRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRMRMMRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRR",
            "RRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRMRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRMRRRRRRRRRMRRRRRRR",
            "RRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRMRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRMMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRMRRRRMRRRMRRRRRRRRRRRRRMRRRRRRRRRRMRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRMRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRR",
        ]

    elif deflevel == 4:
        level = [
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            PPP                     ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      P   PPDDDP                 PPP",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      DP PDDDDDDPP P      PP    PDDD",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      DDPDDDDDDDDD DPP    DD   PDDDD",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      DDDDDDRRRDDDPDDDPPPPDDPPPDDDDD",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      RDDDRRRRRRDDDDDDDDDDDDDDDDDRRR",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      RRDRRRRMRRRRDRDDDDDDRRDDDDRRRR",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      RRRRRRRRRRRRDRRRDDDDRMDDDRRRRM",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                           A                                          RRRRRRRRRRRRRRRRRRRRRRRMRRRRRR",
            "                                                                                                                                                                                                                                                                                                                                            * *                                                                                                                                       MRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      RRRRRRRMRRRRRRRRRRRRRRRRRRRRRR",
            "                             P                                                                                                                                            * * * * * *              E         >                                                                                                                           E                                                                                                                                            RRRRRRRRRRRRRRRRRRRRRMRRRRRRRR",
            "                             D                                                                                                                                                                PP PPPPP     PPPPP  P                                                                                                                    PPPPPPPP  PPP                                                                       PPPPPPP     PPPPPPPP    PPPPP  P                           RRRRRRMMRRRRMRRRRRRRRRRRRRRRRR",
            "   P                       PPD                                                                                                                                           * * * * * * *     PPPDD DDDDDPPP PDDDDD  DP                |     V     |        V    |     V      |                                                           DDDDDDDD PDDDPP       *                                 P                         PPDDDDDDD   PPDDDDDDDDPP PDDDDDPPD                           RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "   DP                  PPPPDDD                                                                                                                                                            PDDDDDPDDDDDDDD DDDDDDPPDD                                                                                         P                        PDDDDDDDDPDDDDDD                                  >      D P                      PDDDDDDDDDPPPDDDDDDDDDDDD DDDDDDDDDPPPPP                  P   RRRRRRRRRRRRRRRRRRRRRMRRRRRRRR",
            "  PDD          P      PDDDDDDM                                                                                                                                     E                      DDDDDDDDDDDDDDDPDDDDDDDDDDP                                                                   *     *              D PPP              P     DDDDDDDDDDDDDDDDPPP       *                      PPP    PDPD           PPP        DDDDDDDDDDDDDDDDDDDDDDDDDPDDDDDDDDDDDDDD                  DPP RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            " SDDDS         DS S   DDDDDDDR                                                                                                                             P  P PPPPPPP                  PDDDDRRDRRRRMDDDDDRMRRRDDRDDP                    *                                                                PPDPDDD              DPPPPPDRRRRRRRRDDRRRDDDDD  >                           DDD   PDDDDPP   PP  PPDDD  PPP  PDDDRMRRRRRDDDDDRRRRRRRRDDDDRMRRRDDRDDDDDP                PDDD RRRRRRRMRRRRRRRRRRRRRMRRRRRRRR",
            "RRDRDRRRRRRRRRRDRRRRRRDDDDDMRR                                                                                                                       <     D PD DDDDDDDPPPPP             DDRRRRRDRRRMRRRRDRRRRRRDDRRDD                                       P           >  P        *     *     *       PPDDDDDDDPP  PPP    PPPDDDDDDDRRRRRRRRDMRRRRRDDDPPPPP     *                  PDDDPPPDDRDDDDPP DD  DDDDDPPDDD  DDRRRRRRRRRDDDRRRRRRRRRRRRDRRRRRRRRRDDDDDD                DDDDPRRRRRRRRRRRMRRMRRRRRRRRRRRRRRR",
            "RRDRRRRRRRRRRRRDRRRRRRDRRRRMRR                                             *                                                                        PPP PPPDPDDPDDDDRDDDDDDD  PPPPP   PPPDRRRRRRRRRRRRRRRDRRRRRRRRRMDDP                *  *  *               DP         PPPPDP                     P   PPDDDDRDDDDDDPPDDDPP PDDDDDDDDDRRRRRRMRRRRRRRRRDDDDDDDD                 P >    DDDDDDDDDRDRDDDDPDDPPDDDDDDDDDDPPDRRRMRRRRRMRRRRRRMRRMRRRRRDRRRRRRRRRRRRRRDP    ;;;     PPPDRDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "MRRRMRRRMRRRRRRRRRRRRRRRRMRRRR                            P    X      P     *                                                     *          PP   PPDDD DDDDDDDDDDDDRDDDDDDDPPDDDDD   DDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRDD   PP                         <     PPDDPP       DDDDDD   P  P         P    DPPPDDDDDDRDRMRDDDDDDDDDPDDDDRDDDDDRRRRRRRRRRRRMRRRRRRDDDDDP       *        DPPP PPDRMRDDDDRRRMDDDDDDDDDDDRRRDDDDDDDDRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRDDP   ;^;   PPDDDDRRRDRRMRRRRRRRRRRRRRRRRRRRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                            DP  PPPP PPPDPP                                                       *           PDDP PDDDDDPDDDRDDRDRRRMRRRDDDDDDDDDDDDPPPDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDP PDDPPP      *  *   *   *    P   PPDDDDDD      PDDDDDDPP DPPD    PP   DP PPDDDDDDDDRRRRRRRDDDDDDDDDDDDDDMRMRRRRRRRRRRRRRRRRRRRRRRDDDDDDPP           > PDDDDPDDDRRRDDDRRRRRRRDDDRRDDRRRRRDDRRRDDRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRDD  PPPPPPPDDDDDRRRRDRRRRRRRRRRRRRRRRRRRRRRRRRRRMRR",
            "RRRRRRRRRRRRRRRRRRRRMRRRRRRRRR       E                   PDDPPDDDDPDDDDDDPPPPPPPP                                             *             DDDDPDDDDDDDDDDRDRRDRRRRMRMRRRRRDDDDDDDDDDDDDRRRRRRRRRMRMRRRRRRRRRRRRRRRRRDD DDDDDD                     PDPPPDDDDRDDDPPPPPPDDDDDRDDDPDDDDPPPPDDP PDD DDDDDDDDRRRRRRRRRRRDDRRRDDDDRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRDDD      P   PPPDDDDDDDDMRRMRRRRRMRRRMRRDRMDDRRRRRRRRRRDDRRRRRMRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRDDP DDDDDDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRMRRRRRRRRRRRRRRRRRRRRR      PPP                  DDDDDDDDDDDDDDDDDDDDDDDD                                           *              PDDDDDDDDRRMDRRRRRRRRRRRRRRRRRRRRDDRRRRRDDDRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRDPDDDDDDP             PP     DDDDDDDDDRRDDDDDDDDDRRRRRRDDDDDDDDDDDDDD DDDPDDRDDDRRRRRRRRRRRRRRRRRRRRDRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRDDDP  P  D   DDDDRDDDDDDRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRDDPDDDDDDDDDRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRRRRRMRRRRRRRRR     PDDDP                PDMDDDDDDDDDDDRDDDDDDDDDDP  * * *     P                           *                DDRRDDDRRRRMDRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDRRDDDD   P        PDD    PDDDDDDDMRRRRRDDDDDDDRRRRRRDDDRDDRDDDDDDDPDRDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRDDD  D PDPPPDDDDRRRRDRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRDDDDDDDDDRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRR",
            "RRRRRRRRRRRMRRRRRRRRRMRRRRRMRM>   PDDDDDPP        PP    DDRRDDRRRRDRMRRRRDDDDDDDDDP           D            *            *             P P PDRRRRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRRRRRDPPPDP       DDDPPPPDDRDDDRRRRRRRRDDDDDDRRRRRRRRRDRRRRDDDDRRDDDRRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDPPDPDDDDDDDDRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRMRM",
            "RRRRRRRRMRRRRMRRRRRMRRRRRRRRRRP>  DDDDDDDDPP    PPDDPPPPDMRRMRRRRRRRRRRRRMRRRRRRRDD         PPDP          * *                       P D DPDDRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRMRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRDRRRRRRDDDDDD    PPPDDDDDDDDRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDRRRDRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRDDDDDDRDDDRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRDRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRMRRRRRRRRRR",
            "RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRDP PDDRRRDDDDD   PDDDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRDDPP <  PPPDDDD P       *   *         <   P      P DPDPDDDRRRRRRRRRRRRRMRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRDDDDDPP  DDDDRRDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRRRMRRRRRRRRRRRRRRRMRMRRRRRMRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRMRRRRRRRDDRDDRDDDRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRMRRRRRRRRRRRRRRMRRRDDPDDRRRRRDDDDPP DDDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRDDDPPPPDDDDDRDPDPP    *     *       PPP PD  PPP DPDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDRDDD PDDDRRRDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDRDRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRMMMRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRR",
            "RRRRRRRRRRRRRRRRRRRRMMRRRRRRRMDDDDRRRRRRRRDDDDPDDDRRDDDDRRRRRMRRRRRRRRRRRRRRRRRRRRRDDDDDDDDDDDRDDDDDP      PPPP     PPDDDPDDPPDDDPDDDDRDRDRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRDDPDDDDRRRRMRRRRRRRRRRRRRRMRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMMRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDRRRRRRRRRRDDDDRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRMDDDDDDDDDRRRRDDDDD      DDDD PPPPDDDDDDDDDDDDDDDDRDRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDDDDRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRMRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "MRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRDRRRRRRRRRRRDDDRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRMDDDDRRRMMRRDRDDDP  PPPDDDDPDDDDDDDDDDDRDDDDDDRDRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRDDRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRMRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRM",
            "RRRRRRRRRRRRMRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRDRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDD  DDDDDDDDDDDDDDRMRDRRDDRRRDRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRMR",
            "RRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRDRRDDDRRRRDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRMDRRDDDRRRRDRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRMRRRRRRRRMRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRMRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRR",
            "RRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRMRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRMRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRR",
            "RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRR",
            "RRRRRRRMRRMRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRMMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRR",
            "RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRMRRRMRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMMRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRR",
            "RRRRRRRRRRRMRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRMMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRRRRMRRRRRRRRMRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRMRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRMRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRMMR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMMMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRMMRRRRRRRMMMRRRRRRRRRRRMRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRMRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRMRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRMRRRRRRRRRRRMMRMRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRMRRRRMMRRRRRRRRRRRRRRRRMRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRMRRRMRRMRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRMRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRMRRRRRRMRRRRRRRRMMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRMMRRRRRMRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRMRRMRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
        ]

    elif deflevel == 5:
        level = [
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ",
            "                                                                                                                                                                                                C                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           ",
            "                                                                                                                                                                                                                                                                                                                 C                                   C                                                                    *                                                                                                                                                                                                                                                                                                 ",
            "                                                                                                                                                                                              *                                                                                     |                                             V                                |                                                    *                                                                                                                                                                                                                                                                                                   ",
            "                                                                                                                                                                                                 *                                                                                                   >                                                                                                                *                                                                                                                                                                                                                                                                                   PP         PPPPPPP",
            "                                                                                                                                                                                        PP P        *                                                                                 PP           PPPPP P                PP                 PP         P   P               *                                       *    PPPPPP PPP                                                                                                                                                                                                                                                                      PDD    PPP PDDDDDDD",
            "                                                                                                                                                                                        DDPDP          *                                                                            P DD        PPPDDDDDPDPPP             DD              PPPDD         D   DPP  PP           *                                   *      DDDDDDPDDD PP           P                             E                                                                                                                                                                                                              P  P    PP DDDP   DDDPDDDDDDDD",
            "              P                                                                                                                                                                        PDDDDD      P      *            *                                                            DPDDPP   PPPDDDDDDDDDDDDDP         PPPDDP PP  >    P PDDDDDPP      PDP PDDD  DD PPP         *                               *       PDDDDDDDDDDPDDP          D                         P PPPP                                                                                                                                                                                                             DP D    DDPDDDDPPPDDDDDDDDDDDD",
            "   P        PPD                                                                                                                                                                     PPPDDDDDDPPPPPPD      PPP       *        *                                                     PDDDDDDP  DDDDDDDDDDDDDDDDDP    PPPPDDDDDD DD PPPP PDPDDDDDDDD    PPDDD DDDDPPDDPDDD           *                           *       PPDDDDDDDDDDDDDDD  P     PPDPPP     ******   PP   P  D DDDDPPPP                 P P                                                                                                                                                                                     DDPDP  PDDDDRRDDDDDDDDDRRMRRRR",
            "  SD SS  SSSDDDSS                                                                                                                                                        *         PDDDDRRDRDDDDDDDDPP    DDD             *                                               PP     PPDDDRRDDDPPDDDDDDRRRRRDMDDDDD    DDDDDDDRRDPDDPDDDD DDDDDDDMRDDPP  DDDRDPDRDDDDDDDDDDP            *                       *         DDDRRRRRRDRRRDDDDPPDPP PPDDDDDDPPP           DDPPPDPPDPDDDDDDDD         PP  P  PDPD                                                                                                                                                                                     DDDDD  DDDDRRRDDDDRRMDRRRMRRRR",
            "RRRDMRRRRRRRDDDRRRRMRRR                                    *                                                                                                                      PDDDDDRRRRRDDDDDDDDDPPPPDDDPP      P                                       C            DD    PDDDRDRRDDDDDDDDRRRMRRRRRRRRRDDPPPPDDDDDDDRRDDDDDDDDDPDDDDRRRRRDDDD PDDDRDDDRRRDDRRDDDDDP  P          *        >          *          PDDDRRRRRRRRRRDRRDDDDDDPDDDDRDDDDDD          PDDDDDDDDDDDDDDDDDDP        DDPPDPPDDDDP                                                                                                                                                                                    RDDRDRRDRRDRRRRDDDRRRRRRRRRRRR",
            "RRRDRRRRRRRRDDMRRRRRRRRR                                  * *                      PP          |      V      |                                                    *     *        PDDDDDRMRRRRDDDDDDRDDDDDDDDDDD    P DP            PPP                                   PDDPP  DDDDRRRRRRDDDRRRRRRMRRRRRRRMRRDDDDDDDDDRRRRRRDRRDDDDDDDMDRRRMMRRRDDPDDDRRRDRRRRDDRRDMRRDD  D P          *     PPP       *       P    DDDRRRRRRRRRRMRRRRDDDDDDDDDDRDDDDDDPP PP    PDDDDDDDDDRDRRRRDDDDD       PDDDDDDDDDDDD                                                                                                                                                                                    RRDRDRRDRRRRRRRMRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRMRRR                                *  *  *                    DD         |        V      |                                                             PPPPPDDDRMRRRRRRRRRRRRRRDDDDDDRRRDDPP  DPDD P          DDD                                   DDDDDPPDDDRRRRRRRRDDRRRRRRRRRRRRRRRRRRDDDDRRRRRRRRRRDRRDRRRRDRRRRRRRRRRRDDDDRRRRRDRRRRRRRRRRRRDDPPDPD    P        PPPDDD               DP PPDRMRRRRRRRRRRRRRRRDDRDDDDDRRRRRRDDDDDPDD    DDRRDDDMDDRDRRRRRRRRDPPP <  DDDDDDDDDRDRDPPPP                                                                                                                                                                                RRRRRRRRRRRRRRRMRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRR                                 * *                     PDDPPP                                                                      *             DDDDDDDRMRRRRMRRRRRRRMRRRRDDDDRRRDDDDPPDDDDPD   <     PDDDP P             * * * * * *       PDMRDDDDDRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRDDDDMRRRRRRMRRRRRMRRRRDRRRRRRRRRRRRRDDRRRRRMRRRRRRRRRRRRRDDDDDDPPP DP       DDDDDDP            PPDDPDDDRRRRRRRRRRRRRRRRRRRRRRDRRRRRRRRRRMDDDDDPPPPDDRRRRRRRRRRRRRRMMRRDDDDPPPPDRRDDRDDRRRRDDDDD               C                                                                                                                          A                                     RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRMRMRRRRRMRRRRRRRRRR                           PP   *  PP                PPDDDDDD                                                                                PPPPDDDDDDRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDRDDDPPPPPP P DDDDD D    P                          DDRRDDDDRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRRRRRRMRMRRRRRRRRRRRDDRDDDDDPDD  PPP PDDDDDDD            DDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRDDDDDDDDDDRRRRRRRRRRRRRRRRRRRRDDDDDDDDRMRRRRRRRRRRDDDDPPP     P                                                                                                                                                                       RRRRRRRRRRRRRRMRRRRRRRMRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR                        DDPPPPPPDDP               DDDRRDDDPP                 E                                                 *          DDDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRDDDDRDRRDDDDDDDD DPDRRRDPDPPP D       * * * * * * *     PDRRRMRDDRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDRDRDDDDDDP DDDPDDDDRRRDPPPPPP     PDDRDDDDRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRDRRDDDDRRRRRRRRRRRRRRRRRRRRRDDDDDDDMRRRRRRRRRRRRDDDDDDD PPPPD                                                   PPP   *             *       PP                                                                                      RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRMRRRRRRRRRRRRRRRMRRR               *    P  PDDDDDDDDDDD             PPDDDRRDDDDD            P > PPP                           * * * *                        PDDDDMRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRDDRRRRDMDDDDDDPDDDRRRDDDDDDPDPPP                   PP DDRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRDDDDRDDPDDDDDRRRRRRDDDDDDD     DDDRRDRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRDDDDRRRRRRRRRRRRMRRRRRRRRRRRDDDDRMRRRRRRMRRRRRRRRDDDPDDDDDPP                                              P  DDD    *           *        DD                                                                                      RRRRRRRRRRMRRRRRRRRRRRRRRRMRRR",
            "RRRRRRRRRRRRRRRRMRRRRMRRRRRRRR              *    PDP DDDDDDDDDDDDP            DDDDRRRRRRDDPP    PP  PPDPPPDDD                                               *          DDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDDDDRRRRRDRDDDDDDDDPP               PPDDPDRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRMDDDDDDDMRRRRRRDDDDDDPP PPDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRMRRRRMRRRRRRRRRRRRMRMRRRRRDDDDDDDDDDD                                             PDPPDDDP    *         *        PDDPP   P                                                                                RRRRRRRRRRRRRRRRMRRRRMRRRRRRRR",
            "RRRRRRRRRRRRMRRRRRRRRRRRRRRMRR             *     DDDPDRRDDDDDDRRDD  P      PPPDDRRRRRRRRDDDD    DD PDDDDDDDDDPP      P                 * * * * *                      PDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRDRDRRRRRDRDDDDRDDDDDP  P          PDDDDDDRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRDDRRRDMRRRRRRRDDDDDDDD DDDRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRMRRRRRMRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMMRRDDDDDRDDP       P                                    DDDDDDDD     *       *      PPPDDDDD   DP                                     PPP                                PP;;;;;RRRRRRRRRRRRMRRRRRRRRRRRRRRMRR",
            "MRRRRRRRRRRRRRRRRRRRRRRRRRRRRR            *     PDDDDDRRRRRRRRRRRDPPD    < DDDDDRRRRRRRRRMDDP  PDDPDDDDDDDDDDDDPPP  PD  PP P P                        E               DDRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRDRRRRRRRRRRRRDRDDDDDDPPDPPP      PDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRDRRRRRRRRRRRRRRRRRRDDPDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRDRRRRRDDDPPPPPP D      <                            PDDDDRRRDP     * * * *       DDDDRRDDPPPDD                                     DDD                              PPDD     MRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRMRRRRRRRRRRRRRRRRRR           *      DDRDDRMRRRRRRRRRRDDDDP  PPPDDDRRRRRRRRRRRRDDDPPDDDDDDDRDDDRRRDDDDDPPDDPPDD DPD                    PPPPPPPPP        PPPDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDDDDP  PPPDDDDRRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRMRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRDDDDDDDPDP   PPPP              C           PDDRDDRRRDDPP           P    PDDDDRRDDDDDDDPP                        P         PDDDPP       PPPPPP       PPP   PPDDDDP ^ PRRRRRRRRRRRMRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRMRRRRRRRMRRRRRRRRRR        X        PDRRRDRRRRRRRMRRRRRDDDDPPDDDDDDRRRRRRRRRMRRRRDDDDRRDDMRRRRRRRRDDDDDDDDDDDDDPDDDP                PPPDDDDDDDDDP     PPDDDDRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRDDDDDDDD  DDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRDRRRMRRRRRRMRRMRMRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRDDDDDDDDDD   DDDD                          DDRRRRRRRRDDDPPP        D    DDDDRRRRRDDDRDDD                       PDP  PP    DDDDDD       DDDDDDPP   PPDDDPPPDDDDDDDPPPDRRRRRRRRRRRMRRRRRRRMRRRRRRRRRR",
            "RRRRRRRRRRRRRMRRRRRRRRRRRRRRRR        PP       DDMRMRRMRRRRRRRRRRRDDRDDDDDDRRMRRRRRRRRMRRRRRDDDDRRDRRRRRRRRRRRRDDDDDDRDDDDDDDDD  P     PP  PPPPDDDDDDDDDDDDDPP   DDDDDRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRDDRDDDDPPDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRDDDDDDDRDPPPDDDDP                      PPPDDRRRRRRRRDDDDDD       PDPPPPDRRRRRRRRDDDRRDDP                      DDD PDD   PDRMRDDP    PPDDDDDDDDP  DDDDDDDDDDDDRRDDDDDRRRRRRRRRRRRRMRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRR    PP  DDPPP PPPDRRRRRRRMRRRRRRRRRRRRMDDDDDDRRRRRRRRRRRRRMRRRRDDRRRRRRRRRRRRRRRRRRRDDRMDDMRDRDRDP DPPPPPDDPPDDDDDDDRDDDDDDRRDDDPPPDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRMRRRRRRRRRRRRRRRDRDDDDDDDDD       P       PPPP PPDDDDRRRRRRRRRRDDDDDPPP    DDDDDDDRRRRRRRRRRRRRDDD P   P  P         PPPPDDDPDDDP  DDRRRDDD PP DDDDDDDDDDDPPDDDDDDDDDDRRRRDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRMMRRRRRRRRRRRRR    DD SDDDDD DDDDMRRRRRRRRRRRRRRRMRRRRRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRDRRRDDSDDDDDDDDDDDDDDDDDRRRRRRRRRDDDDDDDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRDDRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRDDDRRRRDS   SS D     SSDDDDSDDDDDRRRRRRRRRRRRRDDDDDD SSSDRDDDDRRRRRRRRRRRRRRRRDSDSSSD  DSSS SS  SDDDDDRDDDDDDSSDRRRRRRDSDDSDDRRRRRRDDDDDDDRRRDDDRRRRRRRDDDRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRDDRRDDDDDRDDDRMRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRMRRRMRRMRRRRRRRDRDDDDDDDDDDDDDDRRRRRRRRRMRRRDDDDDRRRRRRRRRRRRRRMRRRRRRRRRRMMMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRDDRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDDDRRRRDRRMMMRRDRRRRRRRDDDDRDDDDDRRRRRRRRRRRRRRRRDDDRRRRDRDDDDRRMRRRRRRRRRRRRRDRDRRRDRRDRRRRRRRRRDDDDRRRDDRRDRMDRRRRRRDRDDRDDMRRRRRRRDDDRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRDDRRRRDDDRDDDRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRDRRDDDDDRRDDRRMRRRRRRRRRRRRRRRRDDDRRRRRRRMRMRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRMRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRDRRRRRRRDDDDRDDRRRRRRRRRRRRRRRRMRRDDDRRRRRRRRRMRRRRRRRRRRRRRRRRRRDMRRDRRDRRRRRRRRRDDDDRRRDRRRDRRRRRRRRRRRDDRRRRRRRRRRRRDDRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRMRMMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRR",
            "RRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRMMMRMMRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRMRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRM",
            "RRRMMRRRRRRMRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRR",
            "RRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRMMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRMMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRMRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRR",
            "RRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRMRRRRRRRRRRRRMRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMMRRRRRRRRRRRRMRRRRRRRMRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRMRRRRMRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMRMRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRMMRRRRRMRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRMRRRRRRRMRMRRRRRMRRMRRRMRRRRRRMRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRMRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRMMRRRRRRRRRMRRRRRRRMRRRMRRMRRRRRMRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRMMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "MRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMMRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRR",
            "RMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRMRRRRRRMRRRRRRMRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRMMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "MRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRMRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMMRRRRRRRRRRMRRRRRRRMRRRRRRRRMRRRRRRMRRRRRRRRRRMRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRMRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRMRRRRRMRRRRRRRRRRRRRMRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRMMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMMRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRR",
            "RRRRRRRRMRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRMRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRMRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRMRRRRMRMRRRRRRRMRRRRRRRRRRRRMRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRM",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRMRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRMRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRMRRMRRMRRRRRMRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRMRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRMRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRMRRRRRRRRRRRRRRRRRRMMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRMRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRMMRRRRRRRRRRRRRRR",
            "RMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRMRRRRRRRRMRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRMRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRRRMRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRMRMRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRMRRRRRRRRMMRRRRRRRRRRRMRRRRRMRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRMRMRRMRRRRRRRRRRRRRRRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRMRRRRMRRRRRRMRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
            "RRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRR",
            "RRRRMRRRRRRRRMRRRRRRRRRRMRRRRRRRMMRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRMRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRMRRMRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRMRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRR",
            "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRMRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRR",
            "RRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRMRRRRMRRRRRRRMRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRMRRRRRRRRRRRRRRRRRRMMMRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRMRRMRRRMRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRMRRRRRRRRRRMRMRRRRRRRRRMRRRRRRRRRRRRR",
            "RRRRRRRRRMMMRRRRRRRRRRRRRRRMRRRRRRRRRRRRMRRRRRMRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRMRRRRRRRRRRRRRRMRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRMRRRRRRRRRRMRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRMRRMRRRRRRRRRRRRRRRRRRRRRRMRRRRRMRRRRRRRRRRMRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRMRRMRRRRRRRRRRRR",
            "RRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRMRRMRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRMRRRRMRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRMRRRRRRRMRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMMRRRRRRRMRRRRRRRRRRMRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRMRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
        ]

    elif deflevel == 6:
        callNextCutscene()

    else:
        deflevel = 1
        main()

    level = pad_level(level)

    level_w = len(level[0]) * TILE_SIZE

    level_h = len(level) * TILE_SIZE

    entities = pygame.sprite.Group()

    players = pygame.sprite.Group()

    platforms = pygame.sprite.Group()

    enemies = pygame.sprite.Group()

    hasCollidePhysics = pygame.sprite.Group()

    smartEnemies = pygame.sprite.Group()

    smartEnemyTurnTriggers = pygame.sprite.Group()

    playerKillers = pygame.sprite.Group()

    coins = pygame.sprite.Group()

    bullets = pygame.sprite.Group()

    playerKillables = pygame.sprite.Group()

    playerWindBullets = pygame.sprite.Group()

    playerLightningBullets = pygame.sprite.Group()

    miniBosses = pygame.sprite.Group()

    smartPlatforms = pygame.sprite.Group()

    smallAmmoPickups = pygame.sprite.Group()

    bigAmmoPickups = pygame.sprite.Group()

    blueKeyCards = pygame.sprite.Group()

    turners = pygame.sprite.Group()

    blueDoors = pygame.sprite.Group()

    trophies = pygame.sprite.Group()

    static_tiles = pygame.sprite.Group()

    playerSpiritBindBullets = pygame.sprite.Group()

    renunciationBlocked = pygame.sprite.Group()

    screen.fill((0, 0, 0))

    loading_text = kFont.render("Loading...", True, (255, 255, 255))

    screen.blit(loading_text, (WIDTH - loading_text.get_width() - 20, HEIGHT - loading_text.get_height() - 20))

    pygame.display.flip()

    num_rows = len(level)

    for r in range(num_rows - 1, -1, -1):

        row = level[r]

        for c, ch in enumerate(row):

            x = c * TILE_SIZE

            y = r * TILE_SIZE

            if ch == "X":

                Player((x, y), players, entities, platforms=platforms)

            elif ch == ";":

                BlueDoor((x, y), entities, platforms, blueDoors)

            elif ch == "P":

                Platform((x, y), "grass", static_tiles, platforms)

            elif ch == "S":

                Platform((x, y), "sand", static_tiles, platforms)

            elif ch == "R":

                Platform((x, y), "rock", static_tiles, platforms)

            elif ch == "D":

                Platform((x, y), "dirt", static_tiles, platforms)

            elif ch == "M":

                Platform((x, y), "moss", static_tiles, platforms)

            elif ch == ":":

                Platform((x, y), "crate", static_tiles, platforms)

            elif ch == "=":

                Support((x, y), static_tiles, smartEnemyTurnTriggers)

            elif ch == "]":

                Barrier((x, y), entities, platforms)

            elif ch == "E":

                Stephano((x, y), entities, enemies, playerKillers, playerKillables, platforms=platforms,

                         players=players, entities=entities, bullets=bullets, renunciationBlocked=renunciationBlocked)

            elif ch == "C":

                Caliban((x, y), entities, enemies, playerKillers, playerKillables, platforms=platforms, players=players)

            elif ch == "V":

                Ariel((x, y), entities, smartEnemies, playerKillers, playerKillables)

            elif ch == "|":

                SmartEnemyTurnTrigger((x, y), entities, smartEnemyTurnTriggers)

            elif ch == "*":

                Coin((x + 16, y + 16), entities, coins)

            elif ch == "A":

                Alonso((x + 16, y + 16), entities, hasCollidePhysics, miniBosses, playerKillers, playerKillables,

                       turners, platforms=platforms, entities=entities, bullets=bullets, playerkillers=playerKillers,

                       renunciationBlocked=renunciationBlocked)

            elif ch == "=":

                Support((x, y), entities)

            elif ch == "<":

                Ammo((x, y), entities, smallAmmoPickups)

            elif ch == ">":

                BigAmmo((x, y), entities, bigAmmoPickups)

            elif ch == "-":

                MovingPlatform((x, y), entities, smartEnemies, platforms, smartPlatforms)

            elif ch == "^":

                Trophy((x, y), entities, trophies)

            elif ch == "?":

                BlueKey((x + 16, y + 16), entities, blueKeyCards)

    background = pygame.Surface((level_w, level_h), pygame.SRCALPHA).convert_alpha()

    for t in static_tiles:
        background.blit(t.image, t.rect)

    static_tiles.empty()

    SHADOW_RES = 4

    max_depth = 6

    max_alpha = 230

    shadow_intensity = 0.9

    shadow_cols = level_w // SHADOW_RES

    shadow_rows = level_h // SHADOW_RES

    blocks_per_tile = TILE_SIZE // SHADOW_RES

    shadow_overlay = pygame.Surface((level_w, level_h), pygame.SRCALPHA)

    alpha_map = [[0 for _ in range(shadow_cols)] for _ in range(shadow_rows)]

    for col in range(len(level[0])):
        for row in range(len(level)):

            tile = level[row][col]

            tile_above = level[row - 1][col] if row > 0 else " "

            if tile in "PSRDM" and tile_above not in "PSRDM":

                s_col_start = col * blocks_per_tile

                s_row_start = row * blocks_per_tile

                for i in range(1, max_depth * blocks_per_tile + 1):

                    fade_row = s_row_start + i

                    if fade_row >= shadow_rows:
                        break

                    below_tile_r = fade_row // blocks_per_tile

                    if not (0 <= below_tile_r < len(level)

                            and level[below_tile_r][col] in "PSRDM"):
                        break

                    fade_ratio = min(1.0, i / (max_depth * blocks_per_tile))

                    alpha = int(max_alpha * (fade_ratio ** shadow_intensity))

                    for dx in range(blocks_per_tile):

                        shadow_col = s_col_start + dx

                        if shadow_col >= shadow_cols:
                            continue

                        world_y = fade_row * SHADOW_RES

                        world_x = shadow_col * SHADOW_RES

                        tr = world_y // TILE_SIZE

                        tc = world_x // TILE_SIZE

                        ar = (world_y - SHADOW_RES) // TILE_SIZE

                        if (

                                0 <= tr < len(level)

                                and 0 <= tc < len(level[0])

                                and level[tr][tc] in "PSRDM"

                                and (ar < 0 or level[ar][tc] in "PSRDM")

                        ):
                            alpha_map[fade_row][shadow_col] = max(

                                alpha_map[fade_row][shadow_col], alpha

                            )

    for col in range(1, len(level[0]) - 1):
        for row in range(1, len(level) - 1):

            tile = level[row][col]

            tile_above = level[row - 1][col]

            tile_below = level[row + 1][col]

            tile_left = level[row][col - 1]

            tile_right = level[row][col + 1]

            if (

                    tile == " "

                    and tile_below in "PSRDM"

                    and tile_above in "PSRDM"

                    and tile_left in "PSRDM"

                    and tile_right in "PSRDM"

            ):

                s_col = col * blocks_per_tile

                s_row = row * blocks_per_tile

                for i in range(1, max_depth * blocks_per_tile + 1):

                    fade_row = s_row - i

                    if fade_row < 0:
                        break

                    fade_ratio = min(1.0, i / (max_depth * blocks_per_tile))

                    alpha = int(max_alpha * (fade_ratio ** shadow_intensity))

                    for dx in range(blocks_per_tile):

                        tile_check_row = (fade_row // blocks_per_tile)

                        tile_check_col = (s_col + dx) // blocks_per_tile

                        if (

                                0 <= tile_check_row < len(level)

                                and 0 <= tile_check_col < len(level[0])

                                and level[tile_check_row][tile_check_col] in "PSRDM"

                        ):
                            alpha_map[fade_row][s_col + dx] = max(alpha_map[fade_row][s_col + dx], alpha)

    blended_map = [[0 for _ in range(shadow_cols)] for _ in range(shadow_rows)]

    for row in range(shadow_rows):

        for col in range(shadow_cols):

            tr = row // blocks_per_tile

            tc = col // blocks_per_tile

            over_solid = (

                    0 <= tr < len(level)

                    and 0 <= tc < len(level[0])

                    and level[tr][tc] in "PSRDM"

            )

            in_cave = False

            if 1 <= tr < len(level) - 1 and 1 <= tc < len(level[0]) - 1:

                if level[tr][tc] == " ":

                    nbrs = (

                        level[tr + 1][tc], level[tr - 1][tc],

                        level[tr][tc + 1], level[tr][tc - 1]

                    )

                    if all(n in "PSRDM" for n in nbrs):
                        in_cave = True

            if not (over_solid or in_cave):
                blended_map[row][col] = 0

                continue

            neigh = [alpha_map[row][col]]

            if col > 0:
                neigh.append(alpha_map[row][col - 1])

            if col < shadow_cols - 1:
                neigh.append(alpha_map[row][col + 1])

            nz = [a for a in neigh if a > 0]

            blended_map[row][col] = int(sum(nz) / len(nz)) if nz else 0

    for col in range(shadow_cols):
        for row in range(1, shadow_rows):

            above = blended_map[row - 1][col]

            here = blended_map[row][col]

            if here < above:
                blended_map[row][col] = above

    tri_debug = False

    tri_x_shift = 3

    tri_y_shift = 8

    tri_w = 8

    tri_h = 8

    overlay_w, overlay_h = shadow_overlay.get_size()

    triangles = []

    blocked_cols = set()

    for row in range(shadow_rows):

        ext_cols = []

        for col in range(shadow_cols):

            alpha = blended_map[row][col]

            if alpha <= 0:
                continue

            x = col * SHADOW_RES

            y = row * SHADOW_RES

            pygame.draw.rect(

                shadow_overlay,

                (0, 0, 0, alpha),

                pygame.Rect(x, y, SHADOW_RES, SHADOW_RES),

            )

            tile_r = row // blocks_per_tile

            tile_c = col // blocks_per_tile

            right_is_air = (

                    tile_c == len(level[0]) - 1

                    or level[tile_r][tile_c + 1] not in "PSRDM"

            )

            if right_is_air:

                for off in (1, 2):
                    ex = x + off * SHADOW_RES

                    pygame.draw.rect(

                        shadow_overlay,

                        (0, 0, 0, alpha),

                        pygame.Rect(ex, y, SHADOW_RES, SHADOW_RES),

                    )

                ext_cols.append((col, alpha))

        if row % blocks_per_tile == (blocks_per_tile - 1):

            bottom_y = min((row + 1) * SHADOW_RES + tri_y_shift, overlay_h)

            top_y = max(bottom_y - tri_h, 0)

            tile_r = row // blocks_per_tile

            for col, alpha in ext_cols:

                tile_c = col // blocks_per_tile

                if tile_c in blocked_cols:
                    continue

                if level[tile_r][tile_c] == " ":
                    blocked_cols.add(tile_c)

                    continue

                x2 = col * SHADOW_RES + tri_x_shift

                x2 = max(0, min(x2, overlay_w - tri_w))

                pts = [

                    (x2, top_y),

                    (x2 + tri_w, top_y),

                    (x2, bottom_y),

                ]

                triangles.append((pts, alpha))

    for pts, alpha in triangles:
        color = (255, 0, 255, alpha) if tri_debug else (0, 0, 0, alpha)

        pygame.draw.polygon(shadow_overlay, color, pts)

    player = next(iter(players))

    camera.center_on(player.rect)

    def killPlayer():
        global magicPoints
        global lives

        playerObject = next(iter(players), None)

        if playerObject and getattr(playerObject, "shieldActive", False):
            return

        lives -= 1

        magicPoints = magicDefault

        if lives <= 0:
            gameOver()

        else:
            main()

    running = True

    while running:

        clock.tick(60)

        for e in pygame.event.get():

            if e.type == pygame.QUIT:
                sys.exit()

        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            sys.exit()

        """
        All of the player's interactions should be handled below
        """

        if coinCount >= 100:
            lives += 1

            coinCount = 0

        for player in players:

            player.frictional = True

            on_moving_platform = False

            for smartPlatform in smartPlatforms:
                if player.rect.colliderect(smartPlatform.rect):

                    if abs(player.rect.bottom - smartPlatform.rect.top) <= 6:
                        player.frictional = False

                        player.vel.x = smartPlatform.vel.x

                        on_moving_platform = True

                        break

            if not on_moving_platform:
                player.frictional = True

            for coin in coins:
                if coin.rect.colliderect(player.rect):
                    coinCount += 1

                    coin.kill()

                    sfx_collect.play()

                    scorecount += 10

            for smallAmmoPickup in smallAmmoPickups:
                if smallAmmoPickup.rect.colliderect(player.rect):
                    magicPoints += 25

                    sfx_collect.play()

                    smallAmmoPickup.kill()

            for bigAmmoPickup in bigAmmoPickups:
                if bigAmmoPickup.rect.colliderect(player.rect):
                    magicPoints += 50

                    sfx_collect.play()

                    bigAmmoPickup.kill()

            for blueKeyCard in blueKeyCards:
                if blueKeyCard.rect.colliderect(player.rect):
                    player.keys[0] = True

                    sfx_collect.play()

                    blueKeyCard.kill()

            for blueDoor in blueDoors:
                if player.keys[0]:
                    blueDoor.kill()

            for trophy in trophies:
                if trophy.rect.colliderect(player.rect):
                    running = False

                    victory()

            if pygame.mouse.get_pressed() == (True, False, False) and player.shotCooldown <= 0:

                if player.activeWeapon == 1 and magicPoints >= 1:

                    sfx_attack.play()

                    Bullet((player.rect.x + 8, player.rect.y + 16), player.direction,

                           not pygame.key.get_pressed()[pygame.K_w], not pygame.key.get_pressed()[pygame.K_s],

                           entities, bullets, playerWindBullets)

                    player.shotCooldown = 30

                    player.shooting = True

                    magicPoints -= 1

                elif player.activeWeapon == 2 and magicPoints >= 3:

                    sfx_attack.play()

                    LightningZap((player.rect.x + 8, player.rect.y + 16), player.direction,

                                 entities, bullets, playerLightningBullets)

                    player.shotCooldown = 100

                    player.shooting = True

                    magicPoints -= 3

                if player.activeWeapon == 3 and magicPoints >= 5:

                    sfx_attack.play()

                    SpiritBindBubble((player.rect.x + 8, player.rect.y + 16), player.direction,

                                     entities, bullets, playerSpiritBindBullets)

                    player.shotCooldown = 120

                    player.shooting = True

                    magicPoints -= 5

                elif player.activeWeapon == 4 and magicPoints >= 10:

                    sfx_attack.play()

                    RoughMagicAOE(player.rect.center, entities, playerkillables=playerKillables, entities=entities,

                                  blueKeyCards=blueKeyCards)

                    player.shotCooldown = 200

                    player.shooting = True

                    magicPoints -= 15

                elif player.activeWeapon == 6 and magicPoints >= 15 and not renunciationActive:

                    sfx_renounce.play()

                    RenunciationFlash(player.rect.center, entities)

                    renunciationCooldown = 600

                    renunciationActive = True

                    magicPoints -= 15

                    player.shotCooldown = 500

            for playerKiller in playerKillers:
                if playerKiller.rect.colliderect(

                        player.rect):
                    killPlayer()

        """
        Non player interactions
        """

        hits = pygame.sprite.groupcollide(bullets, platforms, True, False)

        for bottle in hits:
            if isinstance(bottle, Bottle):

                sfx_glass.play()

        for smartEnemy in smartEnemies:
            for smartEnemyTurnTrigger in smartEnemyTurnTriggers:
                if smartEnemy.rect.colliderect(smartEnemyTurnTrigger.rect):

                    if smartEnemy.direction == "left":

                        smartEnemy.vel.x *= -1

                        smartEnemy.direction = "right"

                    else:

                        smartEnemy.vel.x *= -1

                        smartEnemy.direction = "left"

        for b in bullets:
            if b not in playerWindBullets and b not in playerLightningBullets and b not in playerSpiritBindBullets:

                if b.rect.colliderect(player.rect):
                    killPlayer()

        for b in playerSpiritBindBullets:
            for enemy in playerKillables:
                if b.rect.colliderect(enemy.rect):

                    b.kill()

                    if hasattr(enemy, "stunned"):

                        enemy.stunned = 180

                    elif hasattr(enemy, "vel"):

                        enemy.vel.x = 0

        for b in playerWindBullets:
            for enemy in playerKillables:
                if b.rect.colliderect(enemy.rect):

                    b.kill()

                    if hasattr(enemy, "health"):

                        enemy.health -= 1

                        if enemy.health <= 0:

                            sfx_kill.play()

                            enemy.kill()

                            scorecount += 50

                            if isinstance(enemy, Alonso):
                                BlueKey(enemy.rect.center, entities, blueKeyCards)

                            enemy.kill()

                            scorecount += 25

                    else:

                        sfx_kill.play()

                        enemy.kill()

                        scorecount += 50

        for b in playerLightningBullets:
            for enemy in playerKillables:
                if b.rect.colliderect(enemy.rect):

                    b.kill()

                    if hasattr(enemy, "health"):

                        enemy.health -= 5

                        if enemy.health <= 0:

                            sfx_kill.play()

                            enemy.kill()

                            scorecount += 25

                            if isinstance(enemy, Alonso):
                                BlueKey(enemy.rect.center, entities, blueKeyCards)

                            enemy.kill()

                            scorecount += 25

                    else:

                        sfx_kill.play()

                        enemy.kill()

                        scorecount += 25

        camera.center_on(player.rect)

        if player.rect.top > level_h:

            lives -= 1

            if lives <= 0:

                gameOver()

                pygame.quit()

                sys.exit()

            else:

                main()

                return

        screen.fill((0, 0, 0))

        parallax_factor = 0.15

        cloud_scroll += 0.2

        bg_x = (-camera.offset.x * parallax_factor + cloud_scroll) % bg_width

        bg_y = (-camera.offset.y * parallax_factor) % bg_height

        screen.blit(bg_img, (bg_x - bg_width, bg_y - bg_height))

        screen.blit(bg_img, (bg_x, bg_y - bg_height))

        screen.blit(bg_img, (bg_x - bg_width, bg_y))

        screen.blit(bg_img, (bg_x, bg_y))

        screen.blit(background, (-camera.offset.x, -camera.offset.y))

        screen.blit(shadow_overlay, (-camera.offset.x, -camera.offset.y + (SHADOW_RES * 2)))

        for s in entities:
            on_screen = abs(s.rect.centerx - camera.offset.x - WIDTH // 2) <= (WIDTH // 2) + (TILE_SIZE * 4)

            if on_screen:
                s.update()

                if renunciationActive:
                    renunciationCooldown -= 1

                    for r in renunciationBlocked:
                        r.kill()

                    for enemy in playerKillables:
                        enemy_on_screen = abs(enemy.rect.centerx - camera.offset.x - WIDTH // 2) <= (WIDTH // 2) + (
                                    TILE_SIZE * 4)
                        if not enemy_on_screen:
                            continue

                        if isinstance(enemy, Alonso):
                            enemy.renunciationFrozen = 180
                        elif hasattr(enemy, "stunned"):
                            enemy.stunned = 360
                        elif hasattr(enemy, "vel"):
                            enemy.vel.x = 0

                    if renunciationCooldown <= 0:
                        renunciationActive = False

            else:
                if isinstance(s, (SpiritBindBubble, Bullet, LightningZap, Crown)):
                    s.kill()

        players.update()

        for s in entities:
            if camera.visible(s.rect):

                screen.blit(s.image, camera.to_screen(s.rect))

                if isinstance(s, (Alonso, Ariel, Caliban)) and hasattr(s, "health") and hasattr(s, "max_health"):

                    if s.health < s.max_health:
                        s.draw_health_bar(screen, camera)

        screen.blit(player.image, camera.to_screen(player.rect))

        if player.shieldActive:
            shield_rect = player.shieldImage.get_rect(center=camera.to_screen(player.rect).center)

            screen.blit(player.shieldImage, shield_rect)

        printHud(players)

        pygame.display.flip()


def callNextCutscene():
    global deflevel

    if deflevel == 1:

        cutscene("ACT I: THE STORM", """
            Prospero conjures a mighty tempest to wreck a royal ship.
            His plan: confront those who betrayed him, reclaim his power,
            and orchestrate a reckoning that will change the island forever.

            So dear the love my people bore me; nor set

            A mark so bloody on the business; but

            With colours fairer painted their foul ends.

            In few, they hurried us aboard a bark,

            Bore us some leagues to sea; where they prepared

            A rotten carcass of a boat, not rigg’d,

            Nor tackle, sail, nor mast; the very rats

            Instinctively have quit it: there they hoist us,

            To cry to the sea that roar’d to us; to sigh

            To the winds, whose pity, sighing back again...

            Sit still, and hear the last of our sea-sorrow.

            Here in this island we arrived; and here

            Have I, thy schoolmaster, made thee more profit

            Than other princesses can, that have more time

            For vainer hours, and tutors not so careful...

            - Prospero, Act 1, Scene 2.
            """)

    elif deflevel == 2:

        cutscene("ACT II: STRANGE LAND", """
                Congratulations on beating Act 1. You have unlocked your third ability: SPIRIT BIND.
                Press '3' to use SPIRIT BIND, and freeze an enemy in place for a short time! 
                (Not effective on very large enemies.)

                Shipwrecked nobles roam the island, bewildered and enchanted.
                Illusions cloud their senses. Power struggles ignite.
                The island reveals the rot beneath the courtly surface.

                Gonzalo dreams of a utopia free of kings and toil.
                Meanwhile, Antonio whispers treason again.

                I' the commonwealth I would by contraries
                Execute all things; for no kind of traffic
                Would I admit; no name of magistrate;
                Letters should not be known; riches, poverty,
                And use of service, none; contract, succession,
                Bourn, bound of land, tilth, vineyard, none...

                All men idle, all;
                And women too, but innocent and pure;
                No sovereignty...

                - Gonzalo, Act 2, Scene 1.
                """)

    elif deflevel == 3:

        cutscene("ACT III: THE PLOT THICKENS", """
            Congratulations on beating level 2.
            You have unlocked your fourth ability: ROUGH MAGIC.
            Press '4' to cast an explosive area-of-effect spell!

            Illusions tighten their grip. The nobles, starving and delirious,
            find a banquet — only for it to vanish at Ariel’s command.
            Caliban plots with Stephano to overthrow Prospero.

            You are three men of sin, whom Destiny—
            That hath to instrument this lower world
            And what is in’t—the never-surfeited sea
            Hath caused to belch up you...

            In their distractions: they are now in my power;
            And in these fits I leave them, while I visit
            Young Ferdinand...

            - Ariel & Prospero, Act 3, Scene 3.
            """)

    elif deflevel == 4:

        cutscene("ACT IV: MASQUES AND MONSTERS", """
            Congratulations on beating level 3.
            You have unlocked your fifth ability: SHIELD.
            Press '5' to protect yourself from harm, draining magic over time!

            Spirits dance at Prospero’s command. A masque unfolds —
            a vision of harmony, of blessing, of hope for Miranda’s future.
            But even dreams must end. Caliban’s treachery draws near.

            Our revels now are ended. These our actors,
            As I foretold you, were all spirits and
            Are melted into air, into thin air...

            And like the baseless fabric of this vision,
            The cloud-capp’d towers, the gorgeous palaces,
            The solemn temples, the great globe itself,
            Yea, all which it inherit, shall dissolve...

            - Prospero, Act 4, Scene 1.
        """)

    elif deflevel == 5:

        cutscene("ACT V: THE FINAL SPELL", """
            Congratulations on beating level 4.
            You have unlocked your final ability: RENUNCIATION.
            Press '6' to clear the battlefield of projectiles and stop all enemies from attacking for a few seconds!
            This is a powerful spell, so you too will be unable to cast any spells for a brief period.

            The time has come. The traitors are trapped, trembling.
            Ariel pleads for mercy on their behalf.
            Prospero stands at the edge of vengeance — and chooses virtue instead.

            He forgives. He frees. And he prepares to give up his magic forever.

            Though with their high wrongs I am struck to the quick,
            Yet with my nobler reason ’gainst my fury
            Do I take part: the rarer action is
            In virtue than in vengeance...

            But this rough magic
            I here abjure. And, when I have required
            Some heavenly music... I’ll break my staff,
            Bury it certain fathoms in the earth,
            And deeper than did ever plummet sound
            I’ll drown my book.

            - Prospero, Act 5, Scene 1.
        """)

    else:

        cutscene("", f"""
            Now my charms are all o’erthrown,

            And what strength I have’s mine own,

            Which is most faint: now, ’tis true,

            I must be here confined by you,

            Or sent to Naples. Let me not,

            Since I have my dukedom got,

            And pardon’d the deceiver, dwell

            In this bare island by your spell;

            But release me from my bands

            With the help of your good hands:

            Gentle breath of yours my sails

            Must fill, or else my project fails,

            Which was to please. Now I want

            Spirits to enforce, art to enchant;

            And my ending is despair,

            Unless I be relieved by prayer,

            Which pierces so, that it assaults

            Mercy itself, and frees all faults.

            As you from crimes would pardon’d be,

            Let your indulgence set me free.

            FINAL SCORE: {scorecount}
            """)

    if deflevel != 6:

        main()

    else:

        rollCredits()


if __name__ == "__main__":
    gameBegin()

    callNextCutscene()
