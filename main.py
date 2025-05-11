from ursina import *
from ursina.shaders import unlit_shader
from random import choice, uniform, random
from ursina import lerp
import random as pyrandom
import json
import os

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
road_width = 28
num_lanes = 5
lane_margin = 4  # Margin on each side (adjust as needed)
usable_width = road_width - 3 * lane_margin
lane_gap = usable_width / (num_lanes - 1)
lanes = [(-usable_width/2) + i*lane_gap for i in range(num_lanes)]

# Load textures and model names
road_texture = load_texture('assets/roadTexture_01.png')
barrier_model_path = 'assets/road_barrier.glb'
player_model_path = 'assets/race.glb'
enemy_model_paths = [
    'assets/suv.glb',
    'assets/suv-luxury.glb',
    'assets/taxi.glb',
    'assets/truck.glb',
    'assets/van.glb',
]

# Add skybox
sky = Sky(texture='assets/sky.jpg')

# Add a brighter directional light for proper shading
# DirectionalLight(y=10, z=10, x=10, rotation=(45, -45, 45), color=color.white)
# AmbientLight(color=color.rgba(255,255,255,100))

# Road segments (more for infinite look)
road_segments = []
road_length = 120  # Make road tiles longer
num_road_segments = 10
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

# Re-enable the grass ground background (covers the whole visible area)
grass = Entity(
    model='plane',
    scale=(120, 1, num_road_segments * road_length),
    position=(0, -1.5, 0),  # Start at z=0
    texture='assets/roadTexture_25.png',
    texture_scale=(40, num_road_segments * 2),
    color=color.white
)

# Player car
player = Entity(
    model=player_model_path,
    scale=(1.5, 1.5, 1.5),
    position=(0, 0.5, 0),
    collider='box',
    rotation_y=180
)
player.speed = 5
player.max_speed = 12
player.min_speed = 3
player.base_speed = 5

print("The player texture is: ", player.texture)
print("The player model is: ", player.model)
print("The player color is: ", player.color)
# Score and speed display
score = 0
score_text = Text(f'Score: {score}', position=(-0.85, 0.45), scale=2, background=True)
speed_text = Text(f'Speed: {int(player.speed * 20)} km/h', position=(-0.85, 0.35), scale=2, background=True)

def update_speed_display():
    speed_text.text = f'Speed: {int(player.speed * 20)} km/h'

def update_score_display():
    score_text.text = f'Score: {score}'

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
current_state = MENU

# High score handling
def load_high_score():
    try:
        with open('high_score.json', 'r') as f:
            return json.load(f)['high_score']
    except:
        return 0

def save_high_score(score):
    with open('high_score.json', 'w') as f:
        json.dump({'high_score': score}, f)

high_score = load_high_score()

# UI Elements
def create_menu():
    global menu_entities
    menu_entities = []
    
    # Title
    title = Text('Traffic Racer 3D', position=(0, 0.3), scale=3, origin=(0, 0))
    menu_entities.append(title)
    
    # Start button
    start_button = Button(text='Start Game', position=(0, 0), scale=(0.3, 0.1))
    start_button.on_click = start_game
    menu_entities.append(start_button)
    
    # High score display
    high_score_text = Text(f'High Score: {high_score}', position=(0, -0.2), scale=2)
    menu_entities.append(high_score_text)

def create_game_over_screen():
    global game_over_entities
    # First destroy any existing game over entities
    hide_game_over()
    
    game_over_entities = []
    
    # Game Over text
    game_over_text = Text('Game Over!', position=(0, 0.3), scale=3, origin=(0, 0))
    game_over_entities.append(game_over_text)
    
    # Score display
    score_display = Text(f'Score: {score}', position=(0, 0.1), scale=2)
    game_over_entities.append(score_display)
    
    # High score display
    high_score_display = Text(f'High Score: {high_score}', position=(0, -0.1), scale=2)
    game_over_entities.append(high_score_display)
    
    # Try again button
    try_again_button = Button(text='Try Again', position=(0, -0.3), scale=(0.3, 0.1))
    try_again_button.on_click = restart_game
    game_over_entities.append(try_again_button)

def hide_menu():
    for entity in menu_entities:
        destroy(entity)

def hide_game_over():
    global game_over_entities
    if 'game_over_entities' in globals():
        for entity in game_over_entities:
            if entity:
                destroy(entity)
        game_over_entities = []

def start_game():
    global current_state, score, player, enemy_cars
    hide_menu()
    hide_game_over()  # Make sure to hide game over screen when starting
    current_state = PLAYING
    score = 0
    update_score_display()
    
    # Reset player position
    player.position = (0, 0.5, 0)
    player.speed = 5
    
    # Clear existing enemy cars
    for car in enemy_cars:
        destroy(car)
    enemy_cars.clear()

def game_over():
    global current_state, high_score
    current_state = GAME_OVER
    
    # Update high score if needed
    if score > high_score:
        high_score = score
        save_high_score(high_score)
    
    create_game_over_screen()

def restart_game():
    global current_state
    current_state = PLAYING
    hide_game_over()
    start_game()

# Initialize menu
create_menu()

# Enemy cars
class EnemyCar(Entity):
    def __init__(self, lane_x, z_pos):
        super().__init__(
            model=choice(enemy_model_paths),  # Random model for each enemy
            scale=(1.5, 1.5, 1.5),
            position=(lane_x, 0.5, z_pos),
            collider='box',
            rotation_y=180,
            shader=unlit_shader
        )
        self.speed = uniform(3, 6)
        self.overtaken = False

    def update(self):
        self.z -= time.dt * player.speed
        if self.intersects(player).hit:
            game_over()
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

# Define this first, before using it!
background_tree_textures = [
    'assets/foliagePack_004.png',
    'assets/foliagePack_005.png',
    'assets/foliagePack_006.png',
    'assets/foliagePack_007.png',
    'assets/foliagePack_008.png',
    'assets/foliagePack_009.png',
    'assets/foliagePack_010.png',
    'assets/foliagePack_011.png',
]

background_trees = []
num_background_trees = 40
background_tree_min_x = road_width / 2 + 2  # 2 units away from road edge
background_tree_max_x = 60  # How far from road center to place trees
visible_tree_range_behind = 100
visible_tree_range_ahead = 200
for _ in range(num_background_trees):
    side = choice([-1, 1])  # left or right
    x = side * uniform(background_tree_min_x, background_tree_max_x)
    z = uniform(0, 300)  # Initial z, will be repositioned in update
    texture = choice(background_tree_textures)
    tree = Entity(
        model='quad',
        texture=texture,
        position=(x, 0.5, z),
        scale=(4, 6, 1),  # Smaller trees
        double_sided=True,
        billboard=True,
        color=color.white
    )
    background_trees.append(tree)

num_trees_text = Text(f'Trees: {len(background_trees)}', position=(0.7, 0.45), scale=2, background=True)

def update():
    global enemy_timer, score, player_lane_index, lane_change_cooldown, current_state
    num_trees_text.text = f'Trees: {len(background_trees)}'
    
    if current_state == MENU:
        return
        
    if current_state == GAME_OVER:
        return
    
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
    
    # Move and recycle background trees
    for tree in background_trees:
        tree.z -= time.dt * player.speed
        if tree.z < player.z - visible_tree_range_behind:
            # Recycle tree to a new position ahead
            side = choice([-1, 1])
            x = side * uniform(background_tree_min_x, background_tree_max_x)
            z = player.z + visible_tree_range_ahead + uniform(0, 100)
            tree.x = x
            tree.z = z
            tree.texture = choice(background_tree_textures)
    
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
    # grass.z = player.z

app.run()
