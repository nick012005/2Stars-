from abc import ABC, abstractmethod
from enum import Enum
import random
import pygame
import os

pygame.init()
cell_sprites = pygame.sprite.Group()


class Direction(Enum):
    NOBODY = 0
    ORANGE = 1
    BLUE = 2


def load_image(name, color_key=0):
    full_name = os.path.join('images', name)
    try:
        image = pygame.image.load(full_name)
    except pygame.error as message:
        raise SystemExit(message)
    if color_key == -1:
        color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


class DefaultCell(ABC):
    def __init__(self, x: int, y: int, direction: Direction, cell_size: int, cell_distance: int, left: int, top: int):
        self.direction = direction
        self.x = left + (cell_size + cell_distance) * x
        self.y = top + (cell_size + cell_distance) * y
        self.sprite = None
        self.cell_size = cell_size
        self.init_image()

    @abstractmethod
    def init_image(self):
        pass


class EmptyCell(DefaultCell):
    def init_image(self):
        if self.sprite:
            cell_sprites.remove(self.sprite)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = load_image(f"empty{self.direction.name}.png", color_key=-1)
        self.sprite.image = pygame.transform.scale(self.sprite.image, (self.cell_size, self.cell_size))
        self.sprite.rect = (self.x, self.y)
        cell_sprites.add(self.sprite)


class CapitalCell(DefaultCell):
    def init_image(self):
        if self.sprite:
            cell_sprites.remove(self.sprite)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = load_image(f"capital{self.direction.name}.png", color_key=-1)
        self.sprite.image = pygame.transform.scale(self.sprite.image, (self.cell_size, self.cell_size))
        self.sprite.rect = (self.x, self.y)
        cell_sprites.add(self.sprite)


class ClickableCell(DefaultCell):
    @abstractmethod
    def init_image(self):
        pass

    @abstractmethod
    def on_mouse_down(self, mouse_pos):
        pass

    @abstractmethod
    def on_mouse_up(self):
        pass


class DraggableCell(ClickableCell):
    def __init__(self, x: int, y: int, direction: Direction, cell_size: int, cell_distance: int, left: int, top: int):
        self.is_draggable = False
        self.is_correct_coordinates = False
        self.draw_x = left + (cell_size + cell_distance) * x
        self.draw_y = top + (cell_size + cell_distance) * y
        self.diff_x = 0
        self.diff_y = 0
        super().__init__(x, y, direction, cell_size, cell_distance, left, top)

    @abstractmethod
    def init_image(self):
        pass

    def on_mouse_down(self, mouse_pos: tuple):
        self.diff_x = mouse_pos[0] - self.x
        self.diff_y = mouse_pos[1] - self.y
        self.is_draggable = True

    def on_mouse_up(self):
        self.draw_x = self.x
        self.draw_y = self.y
        self.is_draggable = False
        self.init_image()

    def on_drag(self, mouse_position: tuple):
        if self.is_draggable:
            self.draw_x, self.draw_y = mouse_position[0] - self.diff_x, mouse_position[1] - self.diff_y
            self.init_image()


all_cells = [EmptyCell]


class AddingCell(DraggableCell):
    def __init__(self, x: int, y: int, direction: Direction, cell_size: int, cell_distance: int, left: int, top: int):
        self.new_cell = all_cells[random.randint(0, len(all_cells)) - 1]
        super().__init__(x, y, direction, cell_size, cell_distance, left, top)
        self.init_image()

    def init_image(self):
        if self.sprite:
            cell_sprites.remove(self.sprite)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = load_image(f"{self.new_cell.__name__[:-4].lower()}{self.direction.name}.png", color_key=-1)
        self.sprite.image = pygame.transform.scale(self.sprite.image, (self.cell_size, self.cell_size))
        self.sprite.rect = (self.draw_x, self.draw_y)
        cell_sprites.add(self.sprite)


class Board:
    def __init__(self, side_size: int):
        self.current_direction = Direction.ORANGE
        self.side_size = side_size
        self.left = pygame.display.get_window_size()[0] // 20
        self.cell_distance = (pygame.display.get_window_size()[0] // 2 - self.left) // (self.side_size * 10)
        self.cell_size = (pygame.display.get_window_size()[1] - self.left) // self.side_size - self.cell_distance
        self.top = (pygame.display.get_window_size()[1] - (self.cell_size + self.cell_distance) * self.side_size) // 2
        self.table = [[EmptyCell(x, y, Direction.NOBODY, self.cell_size, self.cell_distance, self.left, self.top)
                       for x in range(self.side_size)] for y in range(self.side_size)]
        self.added = [AddingCell(x, 6, self.current_direction, self.cell_size, self.cell_distance, self.left, self.top)
                      for x in range(self.side_size + 2, self.side_size + 5)]
        self.first_capital_coordinates = None
        self.second_capital_coordinates = None

    def change_current_direction(self):
        directions = [Direction.NOBODY, Direction.BLUE, Direction.ORANGE]

        self.current_direction = directions[directions.index(self.current_direction) % 2 + 1]
        self.added = [AddingCell(x, 6, self.current_direction, self.cell_size, self.cell_distance, self.left, self.top)
                      for x in range(self.side_size + 2, self.side_size + 5)]

    def create_capitals(self):
        first_x, first_y = self.first_capital_coordinates
        second_x, second_y = self.second_capital_coordinates
        self.table[first_y][first_x] = CapitalCell(first_x, first_y, Direction.ORANGE,
                                                   self.cell_size, self.cell_distance, self.left, self.top)
        self.table[second_y][second_x] = CapitalCell(second_x, second_y, Direction.BLUE,
                                                     self.cell_size, self.cell_distance, self.left, self.top)

    def generate_capitals_coordinates(self, distance: int):
        first_x, second_x = random.choices(range(self.side_size), k=2)
        first_y, second_y = random.choices(range(self.side_size), k=2)
        if abs(first_x - second_x) > distance and abs(first_y - second_y) > distance:
            self.first_capital_coordinates = (first_x, first_y)
            self.second_capital_coordinates = (second_x, second_y)
            return None
        self.generate_capitals_coordinates(distance)

    def is_cell_can_be_captured(self, x: int, y: int):
        neighbors = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
        for neighbor in neighbors:
            neighbor_x, neighbor_y = neighbor
            if neighbor_x in range(self.side_size) and neighbor_y in range(self.side_size):
                neighbor_cell = self.table[neighbor_y][neighbor_x]
                if neighbor_cell.direction == self.current_direction:
                    return True
        return False

    def is_cell_alive(self, x: int, y: int):
        neighbors = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
        for neighbor in neighbors:
            neighbor_x, neighbor_y = neighbor
            if neighbor_x in range(self.side_size) and neighbor_y in range(self.side_size):
                neighbor_cell = self.table[neighbor_y][neighbor_x]
                if type(neighbor_cell) == CapitalCell:
                    return True
                else:
                    self.is_cell_alive(neighbor_x, neighbor_y)
        return False

    def add_new_cell(self, cell: AddingCell):
        for x in range(self.side_size):
            for y in range(self.side_size):
                table_cell = self.table[y][x]
                if self.is_cell_can_be_captured(x, y):
                    x_diff = abs(table_cell.x - cell.draw_x)
                    y_diff = abs(table_cell.y - cell.draw_y)
                    if x_diff < self.cell_size // 3 and y_diff < self.cell_size // 3:
                        self.table[y][x] = cell.new_cell(x, y, cell.direction, self.cell_size,
                                                         self.cell_distance, self.left, self.top)
                        self.change_current_direction()


class GameManager(Board):
    def __init__(self, side_size: int):
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        super().__init__(side_size)
        self.is_game_process = False
        self.clock = pygame.time.Clock()
        self.fps = 60

    def initialize(self):
        self.generate_capitals_coordinates(distance=3)
        self.create_capitals()

    def start(self):
        self.is_game_process = True
        self.initialize()
        self.play()

    def play(self):
        while self.is_game_process:
            self.manage_events()
            self.render()
        pygame.quit()

    def finish(self):
        self.is_game_process = False

    def render(self):
        self.screen.fill(pygame.Color(27, 27, 27))
        cell_sprites.draw(self.screen)
        pygame.display.flip()

    def manage_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.finish()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for cell in self.added:
                        x_range = range(cell.x, cell.x + self.cell_size)
                        y_range = range(cell.y, cell.y + self.cell_size)
                        if event.pos[0] in x_range and event.pos[1] in y_range:
                            cell.on_mouse_down(event.pos)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    for cell in self.added:
                        self.add_new_cell(cell)
                        cell.on_mouse_up()
            if event.type == pygame.MOUSEMOTION:
                for cell in self.added:
                    cell.on_drag(event.pos)


GAME = GameManager(side_size=8)
GAME.start()
