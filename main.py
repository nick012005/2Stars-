from abc import ABC, abstractmethod
from enum import Enum
import random
import pygame
import os

pygame.init()

cell_sprites = pygame.sprite.Group()

# загрузка звуков
sound_dir = os.path.join(os.path.dirname(__file__), 'sounds')
bomb_sound = pygame.mixer.Sound(os.path.join(sound_dir, 'bomb.wav'))
bomb_sound2 = pygame.mixer.Sound(os.path.join(sound_dir, 'bomb2.wav'))
rook_sound = pygame.mixer.Sound(os.path.join(sound_dir, 'rook.mp3'))
# загрузка музыки
pygame.mixer.music.load(os.path.join(sound_dir, 'fon_music.mp3'))
pygame.mixer.music.set_volume(0.2)


class Direction(Enum):
    NONE = 0
    NOBODY = 1
    ORANGE = 2
    BLUE = 3


# загрузка изображений
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
    def __init__(self, x: int, y: int, direction: Direction, board):
        self.x = board.left + (board.cell_size + board.cell_distance) * x
        self.y = board.top + (board.cell_size + board.cell_distance) * y
        self.table_x = x
        self.table_y = y
        self.direction = direction
        self.board = board
        self.sprite = None

    def init_image(self, name):
        if self.sprite:
            cell_sprites.remove(self.sprite)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = load_image(f"{name[:-4].lower()}{self.direction.name}.png", color_key=-1)
        self.sprite.image = pygame.transform.scale(self.sprite.image, (self.board.cell_size, self.board.cell_size))
        self.sprite.rect = (self.x, self.y)
        cell_sprites.add(self.sprite)


# класс уничтожающейся клетки в режиме "Death"
class DeadCell(DefaultCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.init_image('deadCell')

    def init_image(self, name):
        if self.sprite:
            cell_sprites.remove(self.sprite)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = load_image(f"{name}.png", color_key=-1)
        self.sprite.image = pygame.transform.scale(self.sprite.image, (self.board.cell_size, self.board.cell_size))
        self.sprite.rect = (self.x, self.y)
        cell_sprites.add(self.sprite)


class EmptyCell(DefaultCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.init_image('EmptyCell')


# класс столиц
class CapitalCell(DefaultCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.init_image('CapitalCell')


class ClickableCell(DefaultCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.is_mouse_down = False
        self.board = board

    @abstractmethod
    def on_mouse_down(self, mouse_pos):
        pass

    @abstractmethod
    def on_mouse_up(self):
        pass


# класс, отвечающий за появление случайной клетки
class RandomCell(ClickableCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.init_image('RandomCell')

    def on_mouse_up(self):
        if not self.is_mouse_down:
            return None
        if self.board.current_direction != self.direction:
            return None
        current_variant = random.choice(all_cells[2:])
        self.board.table[self.table_y][self.table_x] = current_variant(self.table_x, self.table_y, self.direction,
                                                                       self.board)
        self.board.change_current_direction()

    def on_mouse_down(self, mouse_pos):
        self.is_mouse_down = True


# класс клетки бомбы
class BombCell(ClickableCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.init_image('BombCell')

    def on_mouse_up(self):
        if not self.is_mouse_down:
            return None
        if self.board.current_direction != self.direction:
            return None
        neighbors = [(self.table_x, self.table_y + 1), (self.table_x, self.table_y - 1),
                     (self.table_x + 1, self.table_y), (self.table_x - 1, self.table_y)]
        for neighbor in neighbors:
            neighbor_x, neighbor_y = neighbor
            if neighbor_x in range(self.board.side_size) and neighbor_y in range(self.board.side_size):
                if type(self.board.table[neighbor_y][neighbor_x]) == CapitalCell:
                    continue
                zv = random.randint(1, 2)
                if zv == 1:
                    bomb_sound.play()
                elif zv == 2:
                    bomb_sound2.play()
                self.board.table[neighbor_y][neighbor_x] = EmptyCell(neighbor_x, neighbor_y, self.direction, self.board)
        self.board.table[self.table_y][self.table_x] = EmptyCell(self.table_x, self.table_y, self.direction, self.board)
        self.board.change_current_direction()

    def on_mouse_down(self, mouse_pos):
        self.is_mouse_down = True


class ProtectedCell(DefaultCell):
    pass


# класс клетки башни
class TowerCell(ProtectedCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.init_image('TowerCell')


# класс клетки "Яндекс"
class YandexCell(ClickableCell, ProtectedCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.init_image('YandexCell')

    def on_mouse_up(self):
        if not self.is_mouse_down:
            return None
        if self.board.current_direction != self.direction:
            return None
        yandexed = []
        for row in self.board.table:
            for cell in row:
                if cell.direction == Direction.NOBODY or cell.direction == Direction.NONE:
                    neighbors = [(cell.table_x, cell.table_y + 1), (cell.table_x, cell.table_y - 1),
                                 (cell.table_x + 1, cell.table_y), (cell.table_x - 1, cell.table_y)]
                    rook_sound.play()
                    for neighbor in neighbors:
                        neighbor_x, neighbor_y = neighbor
                        if neighbor_x in range(self.board.side_size) and neighbor_y in range(self.board.side_size):
                            if self.board.table[neighbor_y][neighbor_x].direction == self.direction:
                                if type(cell) == CapitalCell:
                                    continue
                                yandexed.append((cell.table_x, cell.table_y))
        for coordinates in yandexed:
            x, y = coordinates
            self.board.table[y][x] = EmptyCell(x, y, self.direction, self.board)
        self.board.table[self.table_y][self.table_x] = EmptyCell(self.table_x, self.table_y, self.direction, self.board)
        self.board.change_current_direction()

    def on_mouse_down(self, mouse_pos):
        self.is_mouse_down = True


# класс, описывающий "изменяющюся клетку" в игре
class TurnCell(DefaultCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)

    @abstractmethod
    def on_turn_changed(self):
        pass


class ChangedCell(TurnCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        super().__init__(x, y, direction, board)
        self.mask_cell = random.choice(all_cells[1:])(self.table_x, self.table_y, self.direction, self.board)
        self.init_image('ChangedCell')

    def on_turn_changed(self):
        if self.board.current_direction != self.direction:
            return None
        self.mask_cell = random.choice(all_cells[2:])(self.table_x, self.table_y, self.direction, self.board)
        self.mask_cell.init_image(type(self.mask_cell).__name__)
        self.mask_image()

    def mask_image(self):
        if self.sprite:
            cell_sprites.remove(self.sprite)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = load_image(f"changed{self.direction.name}.png", color_key=-1)
        mask_size = self.board.cell_size // 3
        dist = self.board.cell_size // 1.7
        self.sprite.image = pygame.transform.scale(self.sprite.image, (mask_size, mask_size))
        self.sprite.rect = (self.x + dist, self.y + dist)
        cell_sprites.add(self.sprite)


all_cells = [ChangedCell, RandomCell, EmptyCell, TowerCell, BombCell, YandexCell]
all_cells_chances = [0.5, 0.3, 0, 0.3, 0.3, 0.6]
directions = [Direction.BLUE, Direction.ORANGE]
current_direction = Direction.ORANGE


# класс, отвечающий за добавление клетки на поле
class AddingCell(ClickableCell):
    def __init__(self, x: int, y: int, direction: Direction, board):
        self.is_draggable = False
        self.is_correct_coordinates = False
        self.draw_x = board.left + (board.cell_size + board.cell_distance) * x
        self.draw_y = board.top + (board.cell_size + board.cell_distance) * y
        self.diff_x = 0
        self.diff_y = 0
        super().__init__(x, y, direction, board)
        self.new_cell = random.choice(all_cells)
        self.init_image(self.new_cell.__name__)

    def init_image(self, name):
        if self.sprite:
            cell_sprites.remove(self.sprite)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = load_image(f"{name[:-4].lower()}{self.direction.name}.png", color_key=-1)
        self.sprite.image = pygame.transform.scale(self.sprite.image, (self.board.cell_size, self.board.cell_size))
        self.sprite.rect = (self.draw_x, self.draw_y)
        cell_sprites.add(self.sprite)

    def on_mouse_down(self, mouse_pos: tuple):
        self.diff_x = mouse_pos[0] - self.x
        self.diff_y = mouse_pos[1] - self.y
        self.is_draggable = True

    def on_mouse_up(self):
        self.draw_x = self.x
        self.draw_y = self.y
        self.is_draggable = False
        self.init_image(self.new_cell.__name__)

    def on_drag(self, mouse_position: tuple):
        if self.is_draggable:
            self.draw_x, self.draw_y = mouse_position[0] - self.diff_x, mouse_position[1] - self.diff_y
            self.init_image(self.new_cell.__name__)


# класс поля в стандартном режиме
class DefaultBoard:
    def __init__(self, side_size: int):
        self.side_size = side_size
        self.left, self.top, self.cell_distance, self.cell_size = self.set_board()
        side_range = range(self.side_size)
        self.table = [[EmptyCell(x, y, Direction.NOBODY, self) for x in side_range] for y in side_range]
        self.create_capitals(distance=3)
        self.added = [AddingCell(x + side_size + 2, 4, current_direction, self) for x in range(3)]
        self.current_direction = Direction.ORANGE
        self.winner = None

    def is_win(self):
        is_blue_capital_alive = False
        is_orange_capital_alive = False
        for row in self.table:
            for cell in row:
                if type(cell) == CapitalCell:
                    if cell.direction == Direction.BLUE:
                        is_blue_capital_alive = True
                    else:
                        is_orange_capital_alive = True
        if is_orange_capital_alive and is_blue_capital_alive:
            return None
        else:
            if is_orange_capital_alive:
                self.winner = Direction.ORANGE
            else:
                self.winner = Direction.BLUE
            return True

    def set_board(self):
        window_width = pygame.display.get_window_size()[0]
        window_height = pygame.display.get_window_size()[1]
        left = window_width // 20
        cell_distance = (window_width // 2 - left) // (self.side_size * 10)
        cell_size = (window_height - left) // self.side_size - cell_distance
        top = (window_height - (cell_size + cell_distance) * self.side_size) // 2
        return left, top, cell_distance, cell_size

    def change_current_direction(self):
        # функция изменения хода
        for row in self.table:
            for cell in row:
                if issubclass(type(cell), TurnCell):
                    cell.on_turn_changed()
        self.current_direction = directions[(directions.index(self.current_direction) + 1) % 2]
        self.added = [AddingCell(x, 4, self.current_direction, self)
                      for x in range(self.side_size + 2, self.side_size + 5)]

    def create_capitals(self, distance: int):
        first_x, second_x = random.choices(range(self.side_size), k=2)
        first_y, second_y = random.choices(range(self.side_size), k=2)
        if abs(first_x - second_x) > distance and abs(first_y - second_y) > distance:
            self.table[first_y][first_x] = CapitalCell(first_x, first_y, Direction.BLUE, self)
            self.table[second_y][second_x] = CapitalCell(second_x, second_y, Direction.ORANGE, self)
            return None
        self.create_capitals(distance)

    def is_cell_can_be_captured(self, x: int, y: int):
        if self.table[y][x].direction == self.current_direction and type(self.table[y][x]) != EmptyCell:
            return False
        if self.table[y][x].direction == directions[(directions.index(self.current_direction) + 1) % 2]:
            if issubclass(type(self.table[y][x]), ProtectedCell):
                return False
        neighbors = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
        for neighbor in neighbors:
            neighbor_x, neighbor_y = neighbor
            if neighbor_x in range(self.side_size) and neighbor_y in range(self.side_size):
                neighbor_cell = self.table[neighbor_y][neighbor_x]
                if neighbor_cell.direction == self.current_direction:
                    return True
        return False

    def add_new_cell(self, cell: AddingCell):
        for x in range(self.side_size):
            for y in range(self.side_size):
                table_cell = self.table[y][x]
                if self.is_cell_can_be_captured(x, y):
                    x_diff = abs(table_cell.x - cell.draw_x)
                    y_diff = abs(table_cell.y - cell.draw_y)
                    if x_diff < self.cell_size // 3 and y_diff < self.cell_size // 3:
                        self.table[y][x] = cell.new_cell(x, y, self.current_direction, self)
                        self.change_current_direction()

    def mouse_down_processing(self, mouse_position):
        for cell in self.added:
            x_range = range(cell.x, cell.x + self.cell_size)
            y_range = range(cell.y, cell.y + self.cell_size)
            if mouse_position[0] in x_range and mouse_position[1] in y_range:
                cell.on_mouse_down(mouse_position)
        for row in self.table:
            for cell in row:
                if issubclass(type(cell), ClickableCell):
                    x_range = range(cell.x, cell.x + self.cell_size)
                    y_range = range(cell.y, cell.y + self.cell_size)
                    if mouse_position[0] in x_range and mouse_position[1] in y_range:
                        cell.on_mouse_down(mouse_position)
                if type(cell) == ChangedCell:
                    if issubclass(type(cell.mask_cell), ClickableCell):
                        x_range = range(cell.x, cell.x + self.cell_size)
                        y_range = range(cell.y, cell.y + self.cell_size)
                        if mouse_position[0] in x_range and mouse_position[1] in y_range:
                            cell.mask_cell.on_mouse_down(mouse_position)

    def mouse_up_processing(self, mouse_position):
        for cell in self.added:
            if cell.is_draggable:
                self.add_new_cell(cell)
            cell.on_mouse_up()
        for row in self.table:
            for cell in row:
                if issubclass(type(cell), ClickableCell):
                    x_range = range(cell.x, cell.x + self.cell_size)
                    y_range = range(cell.y, cell.y + self.cell_size)
                    if mouse_position[0] in x_range and mouse_position[1] in y_range:
                        cell.on_mouse_up()
                if type(cell) == ChangedCell:
                    if issubclass(type(cell.mask_cell), ClickableCell):
                        x_range = range(cell.x, cell.x + self.cell_size)
                        y_range = range(cell.y, cell.y + self.cell_size)
                        if mouse_position[0] in x_range and mouse_position[1] in y_range:
                            cell.mask_cell.on_mouse_up()
        self.added[0].on_mouse_up()

    def on_mouse_motion(self, mouse_position):
        for cell in self.added:
            cell.on_drag(mouse_position)


# класс поля в режиме блитц
class BlitzBoard(DefaultBoard):
    def __init__(self, side_size: int):
        super().__init__(side_size)
        self.timer = 5

    def change_current_direction(self):
        for row in self.table:
            for cell in row:
                if issubclass(type(cell), TurnCell):
                    cell.on_turn_changed()
        self.current_direction = directions[(directions.index(self.current_direction) + 1) % 2]
        self.added = [AddingCell(x, 4, self.current_direction, self)
                      for x in range(self.side_size + 2, self.side_size + 5)]
        self.timer = 5


# класс поля в режиме "Death"
class DeadBoard(DefaultBoard):
    def change_current_direction(self):
        self.delete_cell()
        for row in self.table:
            for cell in row:
                if issubclass(type(cell), TurnCell):
                    cell.on_turn_changed()
        self.current_direction = directions[(directions.index(self.current_direction) + 1) % 2]
        self.added = [AddingCell(x, 4, self.current_direction, self)
                      for x in range(self.side_size + 2, self.side_size + 5)]

    def is_cell_can_be_captured(self, x: int, y: int):
        if type(self.table[y][x]) == DeadCell:
            return False
        if self.table[y][x].direction == directions[(directions.index(self.current_direction) + 1) % 2]:
            if issubclass(type(self.table[y][x]), ProtectedCell):
                return False
        neighbors = [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]
        for neighbor in neighbors:
            neighbor_x, neighbor_y = neighbor
            if neighbor_x in range(self.side_size) and neighbor_y in range(self.side_size):
                neighbor_cell = self.table[neighbor_y][neighbor_x]
                if neighbor_cell.direction == self.current_direction:
                    return True
        return False

    def add_new_cell(self, cell: AddingCell):
        for x in range(self.side_size):
            for y in range(self.side_size):
                table_cell = self.table[y][x]
                if self.is_cell_can_be_captured(x, y):
                    x_diff = abs(table_cell.x - cell.draw_x)
                    y_diff = abs(table_cell.y - cell.draw_y)
                    if x_diff < self.cell_size // 3 and y_diff < self.cell_size // 3:
                        self.table[y][x] = cell.new_cell(x, y, self.current_direction, self)
                        self.change_current_direction()

    def delete_cell(self):
        x, y = random.choices(range(self.side_size), k=2)
        if self.table[y][x].direction == Direction.NOBODY:
            self.table[y][x] = DeadCell(x, y, Direction.NONE, self)
            return None
        empties = 0
        for row in self.table:
            for cell in row:
                if cell.direction == Direction.NOBODY:
                    empties += 1
        if empties > 0:
            self.delete_cell()


all_game_modes = [DefaultBoard, DeadBoard, BlitzBoard]


# класс игрового менеджера и показа игры на ваш экран
class GameManager:
    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.start_sprites = pygame.sprite.Group()
        self.is_game_process = False
        self.board = None
        pygame.mixer.music.play(loops=-1)

    def start(self):
        x = self.screen.get_size()[0] // 3
        y = self.screen.get_size()[1] * 2 // 3
        shrift = pygame.font.SysFont('Times New Romans', 60)
        game_mode_id = 0
        while not self.is_game_process:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.pos[1] in range(y // 2, y // 2 + y // 3):
                        if event.pos[0] in range(int(x * 2.1), int(x * 2.1) + x // 2):
                            game_mode_id = (game_mode_id + 1) % len(all_game_modes)
                        elif event.pos[0] in range(int(x * 0.4), int(x * 0.4) + x // 2):
                            game_mode_id = (game_mode_id - 1) % len(all_game_modes)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_game_process = True
                        self.board = all_game_modes[game_mode_id](8)
                        self.play()
                        return None
            self.refresh_menu(game_mode_id)
            self.screen.fill(pygame.Color(27, 27, 27))
            self.start_sprites.draw(self.screen)
            self.screen.blit(shrift.render('[SPACE] - to start', True, (255, 255, 255)), (x * 1.2, y * 1.5 - 100))
            pygame.display.flip()

    def refresh_menu(self, mode_id):
        self.start_sprites = pygame.sprite.Group()
        x = self.screen.get_size()[0] // 3
        y = self.screen.get_size()[1] * 2 // 3
        if all_game_modes[mode_id] == DefaultBoard:
            name = 'standartGameMode.png'
        elif all_game_modes[mode_id] == DeadBoard:
            name = 'DeathGameMode.png'
        elif all_game_modes[mode_id] == BlitzBoard:
            name = 'BlitzGameMode.png'
        else:
            name = ''
        tower = pygame.sprite.Sprite()
        tower.image = load_image(name, color_key=-1)
        tower.image = pygame.transform.scale(tower.image, (x, y))
        tower.rect = (x, y // 8)
        self.start_sprites.add(tower)

        right = pygame.sprite.Sprite()
        right.image = load_image('rightButton.png', color_key=-1)
        right.image = pygame.transform.scale(right.image, (x // 2, y // 3))
        right.rect = (int(x * 2.1), y // 2)
        self.start_sprites.add(right)

        left = pygame.sprite.Sprite()
        left.image = load_image('leftButton.png', color_key=-1)
        left.image = pygame.transform.scale(left.image, (x // 2, y // 3))
        left.rect = (int(x * 0.4), y // 2)
        self.start_sprites.add(left)

    def play(self):
        clock = pygame.time.Clock()
        shrift = pygame.font.SysFont('Times New Romans', 200)
        shrift2 = pygame.font.SysFont('Times New Romans', 100)
        pygame.time.set_timer(pygame.USEREVENT, 1000)
        while self.is_game_process:
            if not self.board.is_win():
                self.manage_events()
                self.render()
            else:
                self.finish()
            if type(self.board) == BlitzBoard:
                if self.board.timer > 0:
                    text = str(self.board.timer).rjust(15)
                    self.screen.blit(shrift.render(text, True, (255, 255, 255)), (900, 200))
                elif self.board.timer == -2:
                    self.board.change_current_direction()
                else:
                    self.board.mouse_up_processing((0, 0))
                    text = 'Переход хода!'
                    self.screen.blit(shrift2.render(text, True, (255, 255, 255)), (1300, 200))
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

    def finish(self):
        self.is_game_process = False

    def render(self):
        self.screen.fill(pygame.Color(27, 27, 27))
        cell_sprites.draw(self.screen)

    def manage_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.finish()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.board.mouse_down_processing(event.pos)
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.board.mouse_up_processing(event.pos)
                    self.board.mouse_up_processing(event.pos)
            if event.type == pygame.MOUSEMOTION:
                self.board.on_mouse_motion(event.pos)
            if event.type == pygame.USEREVENT:
                if type(self.board) == BlitzBoard:
                    self.board.timer -= 1


game = GameManager()
game.start()
