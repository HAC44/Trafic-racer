from ursina import *

app = Ursina()

EditorCamera()  # <-- adds WASD + mouse orbit control

car = Entity(
    model='assets/car.glb',
    scale=0.03,
    origin_y=-1,  # Shift pivot up
    position=(0, 0, 0),
    collider='box',
    color=color.white
)

floor = Entity(model='plane', scale=40, color=color.gray, y=-1)

app.run()
