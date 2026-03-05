import pygame
import math
import time


Points = []
Springs = []
Bodies = []

floor = 900

gravity = 1000


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, other):
        return Vector(self.x * other.x, self.y * other.y)

    def get_magnitude(self):
        return math.dist((0, 0), (self.x, self.y))

    def normalize(self):
        return Vector(self.x / self.get_magnitude(), self.y / self.get_magnitude())

    def dot_product(self, other):
        return (self.x * other.x) + (self.y * other.y)


def vector_to_tuple(vector: Vector):
    return (vector.x, vector.y)


class Rectangle:
    def __init__(self, top_left: Vector, top_right: Vector, bottom_left: Vector, bottom_right: Vector):
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right

    def is_colliding(self, position: Vector):
        if self.top_left.x > position.x > self.top_right.x:
            return True
            #if self.top_left.y > position.y > self.bottom_left.y:
            #    return True
            #else:
            #    return False
        else:
            return False


class Point:
    def __init__(self, position: Vector, mass: float):
        self.position = position
        self.velocity = Vector(0, 0)
        self.force = Vector(0, 0)
        self.mass = mass
        self.calculated_position = position
        self.tied_to_cursor = False
        Points.append(self)

    def update_forces(self):
        self.force = Vector(0, 0)
        self.force += get_spring_velocity(self)
        self.force += Vector(0, gravity * self.mass)
    
    def update_collisions(self):
        self.force += self.get_floor_collision_force()

    def apply_velocity(self, delta_time: float):
        self.velocity += Vector((self.force.x / self.mass) * delta_time, (self.force.y / self.mass) * delta_time)
        self.calculated_position += Vector(self.velocity.x * delta_time, self.velocity.y * delta_time)

    def get_floor_collision_force(self) -> "Vector":
        if self.position.y > floor:
            push_vector = Vector(0, self.position.y - floor)
            self.position -= push_vector
            bounce_vector_x = self.velocity.x - 2 * (self.velocity.dot_product(push_vector)) * push_vector.x
            bounce_vector_y = self.velocity.y - 2 * (self.velocity.dot_product(push_vector)) * push_vector.y
            return Vector(bounce_vector_x, bounce_vector_y)
        else:
            return Vector(0, 0)


def distance(a: Point, b: Point):
    return math.dist((a.position.x, a.position.y), (b.position.x, b.position.y))


class Spring:
    def __init__(self, a: Point, b: Point, stiffness: float, rest_length: float, damping_factor: float):
        self.a = a
        self.b = b
        self.stiffness = stiffness
        self.rest_length = rest_length
        self.damping_factor = damping_factor
        self.current_length = math.dist((a.position.x, a.position.y), (b.position.x, b.position.y))
        Springs.append(self)

    def calculate_spring_force(self) -> float:
        self.current_length = math.dist((self.a.position.x, self.a.position.y), (self.b.position.x, self.b.position.y))
        spring_force = (self.current_length - self.rest_length) * self.stiffness
        normalized_direction_vector = (self.b.position - self.a.position).normalize()
        velocity_difference = self.b.velocity - self.a.velocity
        damp_force = normalized_direction_vector.dot_product(velocity_difference) * self.damping_factor
        total_spring_force = spring_force + damp_force
        return total_spring_force


def get_spring_velocity(point: Point):
    force = Vector(0, 0)
    for spring in Springs:
        if spring.a == point:
            spring_force = spring.calculate_spring_force()
            normalized_direction = Vector(spring.b.position.x - spring.a.position.x, spring.b.position.y - spring.a.position.y).normalize()
            force += Vector(normalized_direction.x * spring_force, normalized_direction.y * spring_force)
        elif spring.b == point:
            spring_force = spring.calculate_spring_force()
            normalized_direction = Vector(spring.a.position.x - spring.b.position.x, spring.a.position.y - spring.b.position.y).normalize()
            force += Vector(normalized_direction.x * spring_force, normalized_direction.y * spring_force)
    return force


class SoftBody:
    def __init__(self, points: list, springs: list):
        self.points = points
        self.springs = springs
        Bodies.append(self)

    def get_bounding_box(self):
        minimum_vector = Vector(math.inf, math.inf)
        maximum_vector = Vector(-math.inf, -math.inf)
        for point in self.points:
            if point.position.x > maximum_vector.x:
                maximum_vector.x = point.position.x
            if point.position.y > maximum_vector.y:
                maximum_vector.y = point.position.y
            if point.position.x < minimum_vector.x:
                minimum_vector.x = point.position.x
            if point.position.y < minimum_vector.y:
                minimum_vector.y = point.position.y
        return Rectangle(
            Vector(minimum_vector.x, minimum_vector.y),
            Vector(maximum_vector.y, minimum_vector.y),
            Vector(minimum_vector.x, maximum_vector.y),
            Vector(maximum_vector.x, maximum_vector.y)
                         )


class Window:
    def __init__(self, size: Vector, colour: (int, int, int), caption: str, target_frame_rate=500):
        self.size = size
        self.colour = colour
        self.caption = caption
        self.surface = pygame.display.set_mode((size.x, size.y))
        self.surface.fill(colour)
        self.previous_time = time.time()
        self.target_frame_rate = target_frame_rate
        pygame.display.set_caption(caption)

    def clear(self):
        self.surface.fill(self.colour)

    def swap_buffers(self):
        pygame.display.flip()

    def get_delta_time(self):
        current_time = time.time()
        delta_time = current_time - self.previous_time
        self.previous_time = current_time
        return delta_time

    def set_caption(self):
        pygame.display.set_caption(self.caption)

    def draw_point(self, point: Point):
        surface = pygame.Surface((16, 16), pygame.SRCALPHA, 32)
        pygame.draw.circle(surface, (255, 0, 0), (8, 8), 8)
        self.surface.blit(surface, (point.position.x - 8, point.position.y - 8))

    def draw_spring(self, spring: Spring):
        if pygame.mouse.get_pressed(num_buttons=3)[0] == True:
            mouse_position = pygame.mouse.get_pos()
            mouse_position = Vector(mouse_position[0], mouse_position[1])
            if math.dist((mouse_position.x, mouse_position.y), (point.position.x, point.position.y)) <= 8:
                print("yesss")
                point.force += mouse_position - point.position
        pygame.draw.line(self.surface, (0, 0, 0), (spring.a.position.x, spring.a.position.y), (spring.b.position.x, spring.b.position.y), 4)


window = Window(Vector(2560, 1440), (255, 255, 255), "Ultimate Physics Simulator Softbody 2D")

test_a = Point(Vector(100, 100), 0.5)
test_b = Point(Vector(700, 100), 0.5)
test_c = Point(Vector(800, 600), 0.5)
test_d = Point(Vector(100, 600), 0.5)

test_spring_a = Spring(test_a, test_b, 20, distance(test_a, test_b) / 2, 1)
test_spring_b = Spring(test_a, test_c, 20, distance(test_a, test_c) / 2, 1)
test_spring_c = Spring(test_a, test_d, 20, distance(test_a, test_d) / 2, 1)
test_spring_d = Spring(test_b, test_c, 20, distance(test_b, test_c) / 2, 1)
test_spring_e = Spring(test_b, test_d, 20, distance(test_b, test_d) / 2, 1)
test_spring_f = Spring(test_c, test_d, 20, distance(test_c, test_d) / 2, 1)

body_aa = Point(Vector(700, 700), 0.5)
body_ab = Point(Vector(700, 725), 0.5)
body_ac = Point(Vector(700, 750), 0.5)
body_ad = Point(Vector(700, 775), 0.5)
body_ae = Point(Vector(700, 800), 0.5)

body_ba = Point(Vector(725, 700), 0.5)
body_bb = Point(Vector(725, 725), 0.5)
body_bc = Point(Vector(725, 750), 0.5)
body_bd = Point(Vector(725, 775), 0.5)
body_be = Point(Vector(725, 800), 0.5)

body_ca = Point(Vector(750, 700), 0.5)
body_cb = Point(Vector(750, 725), 0.5)
body_cc = Point(Vector(750, 750), 0.5)
body_cd = Point(Vector(750, 775), 0.5)
body_ce = Point(Vector(750, 800), 0.5)

body_da = Point(Vector(775, 700), 0.5)
body_db = Point(Vector(775, 725), 0.5)
body_dc = Point(Vector(775, 750), 0.5)
body_dd = Point(Vector(775, 775), 0.5)
body_de = Point(Vector(775, 800), 0.5)

body_ea = Point(Vector(800, 700), 0.5)
body_eb = Point(Vector(800, 725), 0.5)
body_ec = Point(Vector(800, 750), 0.5)
body_ed = Point(Vector(800, 775), 0.5)
body_ee = Point(Vector(800, 800), 0.5)

stiffness = 1000
damping_factor = 10

#floor_visual_a = Point(Vector(0, 900), 9999999999)
#floor_visual_b = Point(Vector(2000, 900), 9999999999)
#floor_visual_spring = Spring(floor_visual_a, floor_visual_b, 9999999999, distance(floor_visual_a, floor_visual_b), 9999999999)

for point_a in Points:
    for point_b in Points:
        if not point_a == point_b:
            if distance(point_a, point_b) < 50:
                new_spring = Spring(point_a, point_b, stiffness, distance(point_a, point_b), damping_factor)

test_body = SoftBody(
    [
        test_a,
        test_b,
        test_c,
        test_d
    ],

    [
        test_spring_a,
        test_spring_b,
        test_spring_c,
        test_spring_d,
        test_spring_e,
        test_spring_f
    ]
)

spring_point_a = Point(Vector(1100, 300), 1)
spring_point_b = Point(Vector(900, 300), 1)
spring_test = Spring(spring_point_a, spring_point_b, 10, distance(spring_point_a, spring_point_b) / 2, 0.8)



while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit(0)

    delta_time = window.get_delta_time()
    #print(1 / delta_time) 

    mouse_position = pygame.mouse.get_pos()
    mouse_position = Vector(mouse_position[0], mouse_position[1])

    if pygame.mouse.get_pressed(num_buttons=3)[0]:
        for point in Points:
            if math.dist((point.position.x, point.position.y), (mouse_position.x, mouse_position.y)) <= 8:
                point.tied_to_cursor = True
    else:
        for point in Points:
            point.tied_to_cursor = False

    for point in Points:
        point.update_forces()
    for point in Points:
        if point.tied_to_cursor:
            point.force += (mouse_position - point.position) * Vector(point.mass, point.mass) * Vector(100, 100)
    for point in Points:
        point.update_collisions()
    for point in Points:
        point.apply_velocity(delta_time)
    print(body_aa.position.x, body_aa.position.y)

        

    window.clear()
    for spring in Springs:
        window.draw_spring(spring)
    for point in Points:
        point.position = point.calculated_position
        window.draw_point(point)
    window.swap_buffers()
