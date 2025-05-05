from ursina import *
from random import choice, uniform

app = Ursina()

window.title = "Traffic Racer 3D"
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

camera.position = (0, 40, -60)
camera.rotation_x = 30

lanes = [-6, -2, 2, 6]

# Load textures
road_texture = load_texture('assets/waterTile43.png')  # road texture
tree_texture = load_texture('assets/tree.png')          # your tree image

# Road segments
road_segments = []
for i in range(3):
    segment = Entity(
        model='cube',
        texture=road_texture,
        scale=(30, 1, 100),
        position=(0, -1, i * 100),
        collider=None
    )
    road_segments.append(segment)

# Tree scenery segments (billboard-style)
tree_rows_left = []
tree_rows_right = []

for i in range(3):
    for offset in range(-45, 50, 15):
        left_tree = Entity(
            model='quad',
            texture=tree_texture,
            scale=(5, 10),
            position=(-15, 5, i * 100 + offset),
            billboard=True
        )
        right_tree = Entity(
            model='quad',
            texture=tree_texture,
            scale=(5, 10),
            position=(15, 5, i * 100 + offset),
            billboard=True
        )
        tree_rows_left.append(left_tree)
        tree_rows_right.append(right_tree)

# Player car
player = Entity(model='cube', color=color.azure, scale=(2, 1, 4), position=(0, 0, -10), collider='box')
player.speed = 5
player.max_speed = 12
player.min_speed = 3

score = 0
score_text = Text(f'Score: {score}', position=(-0.85, 0.45), scale=2, background=True)

class EnemyCar(Entity):
    def __init__(self, lane_x, z_pos):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(2, 1, 4),
            position=(lane_x, 0, z_pos),
            collider='box'
        )
        self.speed = uniform(3, 6)
        self.overtaken = False

    def update(self):
        self.z -= time.dt * player.speed

        if self.intersects(player).hit:
            print("Collision! Game Over.")
            application.quit()

        global score
        if not self.overtaken and self.z < player.z:
            score += 10
            score_text.text = f"Score: {score}"
            self.overtaken = True

enemy_cars = []

def spawn_enemy():
    lane = choice(lanes)
    z = player.z + 100 + uniform(0, 50)
    car = EnemyCar(lane, z)
    enemy_cars.append(car)

enemy_timer = 0

def update():
    global enemy_timer

    # Player movement
    if held_keys['a'] and player.x > min(lanes):
        player.x -= 5 * time.dt
    if held_keys['d'] and player.x < max(lanes):
        player.x += 5 * time.dt

    # Braking
    if held_keys['s']:
        player.speed = max(player.min_speed, player.speed - 20 * time.dt)
    else:
        player.speed = min(player.max_speed, player.speed + 5 * time.dt)

    # Scroll road and wrap segments
    for segment in road_segments:
        segment.z -= time.dt * player.speed
        if segment.z + 50 < player.z:
            segment.z += 300

    # Scroll trees and wrap
    for tree in tree_rows_left + tree_rows_right:
        tree.z -= time.dt * player.speed
        if tree.z < player.z - 50:
            tree.z += 300

    # Enemies
    enemy_timer += time.dt
    if enemy_timer > 1.5:
        spawn_enemy()
        enemy_timer = 0

    for car in enemy_cars:
        car.update()

    for car in enemy_cars[:]:
        if car.z < player.z - 20:
            destroy(car)
            enemy_cars.remove(car)

app.run()