from ursina import *
from random import choice, uniform, random
from ursina import lerp
import random as pyrandom

app = Ursina()

window.title = "Traffic Racer 3D"
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Camera settings
CAMERA_HEIGHT = 30
CAMERA_DISTANCE = 60
CAMERA_ANGLE = 30
camera.position = (0, CAMERA_HEIGHT, -CAMERA_DISTANCE)
camera.rotation_x = CAMERA_ANGLE

# Road and lane setup
road_width = 30
num_lanes = 7  # 7 lanes, centered
lane_gap = road_width / (num_lanes + 1)  # Slightly narrower lanes
lanes = [(-road_width/2) + lane_gap + i*lane_gap for i in range(num_lanes)]

# Load textures and model names
road_texture = load_texture('assets/road.png')
barrier_model_path = 'assets/road_barrier.glb'
player_model_path = 'assets/car.glb'
enemy_model_paths = [
    'assets/car.glb',
]

# Remove skybox for now
# sky = Sky(texture='assets/sky.jpg')

# Add a brighter directional light for proper shading
DirectionalLight(y=10, z=10, x=10, rotation=(45, -45, 45), color=color.white)
AmbientLight(color=color.rgba(255,255,255,100))

# Road segments (more for infinite look)
road_segments = []
road_length = 60
num_road_segments = 20
for i in range(num_road_segments):
    segment = Entity(
        model='cube',
        texture=road_texture,
        scale=(road_width, 1, road_length),
        position=(0, -1, i * road_length),
        collider=None,
        texture_scale=(1, 8)  # More frequent lane lines
    )
    road_segments.append(segment)

# Barriers (sync with road segments)
barrier_entities = []
barrier_spacing = 8
for i in range(num_road_segments):
    z_base = i * road_length
    for offset in range(0, road_length, barrier_spacing):
        left_barrier = Entity(
            model=barrier_model_path,
            scale=1.2,
            position=(-road_width/2, 0, z_base + offset),
            rotation_y=0,
            collider=None
        )
        right_barrier = duplicate(left_barrier, position=(road_width/2, 0, z_base + offset))
        barrier_entities.extend([left_barrier, right_barrier])

# Add grass ground background (covers the whole visible area)
grass = Entity(
    model='plane',
    scale=(120, 1, num_road_segments * road_length),
    position=(0, -1.5, 0),  # Start at z=0
    texture='assets/grass.png',
    texture_scale=(40, num_road_segments * 2),
    color=color.white
)

# Player car as a larger cube, free movement
player = Entity(
    model='cube',
    scale=(2.5, 1, 2),
    position=(0, 0.5, 0),  # Start at center
    color=color.yellow,
    collider='box'
)
player.speed = 5
player.max_speed = 12
player.min_speed = 3
player.base_speed = 5

# Score and speed display
score = 0
score_text = Text(f'Score: {score}', position=(-0.85, 0.45), scale=2, background=True)
speed_text = Text(f'Speed: {int(player.speed * 20)} km/h', position=(-0.85, 0.35), scale=2, background=True)

def update_speed_display():
    speed_text.text = f'Speed: {int(player.speed * 20)} km/h'

def update_score_display():
    score_text.text = f'Score: {score}'

# Enemy cars as larger cubes
class EnemyCar(Entity):
    def __init__(self, lane_x, z_pos):
        super().__init__(
            model='cube',
            scale=(2.5, 1, 2),
            position=(lane_x, 0.5, z_pos),
            collider='box',
            color=color.cyan
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
            update_score_display()
            self.overtaken = True

enemy_cars = []

def spawn_enemy():
    lane = choice(lanes)
    z = player.z + 100 + uniform(0, 50)
    car = EnemyCar(lane, z)
    enemy_cars.append(car)

enemy_timer = 0

# Lane snapping state
lane_change_cooldown = 0

# Add dense rows of trees along both sides of the road, well outside the barriers
barrier_offset = 2  # Distance from road edge to barrier
# Add extra offset to place trees further from the road
extra_tree_offset = 4
left_tree_x = -road_width/2 - barrier_offset - extra_tree_offset
right_tree_x = road_width/2 + barrier_offset + extra_tree_offset

tree_entities = []
for i in range(num_road_segments):
    z_base = i * road_length
    for z_offset in range(0, road_length, 2):  # High density: every 2 units
        # Left side
        tree_left = Entity(
            model='assets/tree_low.glb',
            scale=pyrandom.uniform(3.0, 4.0),
            position=(left_tree_x + pyrandom.uniform(-1, 1), 0, z_base + z_offset + pyrandom.uniform(-1, 1)),
            rotation_y=pyrandom.uniform(0, 360),
            color=color.white,
            collider=None
        )
        tree_entities.append(tree_left)
        # Right side
        tree_right = Entity(
            model='assets/tree_low.glb',
            scale=pyrandom.uniform(3.0, 4.0),
            position=(right_tree_x + pyrandom.uniform(-1, 1), 0, z_base + z_offset + pyrandom.uniform(-1, 1)),
            rotation_y=pyrandom.uniform(0, 360),
            color=color.white,
            collider=None
        )
        tree_entities.append(tree_right)


def update():
    global enemy_timer, score, player_lane_index, lane_change_cooldown
    # Smooth camera follow
    target_camera_pos = (0, CAMERA_HEIGHT, player.z - CAMERA_DISTANCE)
    camera.position = lerp(camera.position, target_camera_pos, 4 * time.dt)
    camera.rotation_x = CAMERA_ANGLE

    # Lane change cooldown logic
    lane_change_cooldown -= time.dt
    if lane_change_cooldown < 0:
        lane_change_cooldown = 0

    # Player movement (free between lanes, clamped to lane extremities)
    min_x = lanes[0]
    max_x = lanes[-1]
    if held_keys['a'] and player.x > min_x:
        player.x -= 5 * time.dt
        if player.x < min_x:
            player.x = min_x
    if held_keys['d'] and player.x < max_x:
        player.x += 5 * time.dt
        if player.x > max_x:
            player.x = max_x

    # Speed increase based on score
    speed_multiplier = 1 + (score // 100) * 0.5
    player.max_speed = player.base_speed * speed_multiplier
    # Braking
    if held_keys['s']:
        player.speed = max(player.min_speed, player.speed - 20 * time.dt)
    else:
        player.speed = min(player.max_speed, player.speed + 5 * time.dt)
    update_speed_display()
    # Scroll road segments
    for segment in road_segments:
        segment.z -= time.dt * player.speed
        if segment.z + road_length/2 < player.z - CAMERA_DISTANCE:
            segment.z += num_road_segments * road_length
    # Scroll barriers
    for barrier in barrier_entities:
        barrier.z -= time.dt * player.speed
        if barrier.z + barrier_spacing/2 < player.z - CAMERA_DISTANCE:
            barrier.z += num_road_segments * road_length
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
    # Move grass with the player
    grass.z = player.z

    # Scroll and recycle trees
    for tree in tree_entities:
        tree.z -= time.dt * player.speed
        if tree.z < player.z - CAMERA_DISTANCE - 60:
            tree.z = player.z + CAMERA_DISTANCE + num_road_segments * road_length * 0.5 + pyrandom.uniform(0, road_length)
            if tree.x < 0:
                tree.x = left_tree_x + pyrandom.uniform(-1, 1)
            else:
                tree.x = right_tree_x + pyrandom.uniform(-1, 1)
            tree.scale = pyrandom.uniform(3.0, 4.0)
            tree.rotation_y = pyrandom.uniform(0, 360)

app.run()
