import pygame
import random
from blokus_classes.board import *
from utils import *
from player import *


class Game:
    def __init__(self, player_nb, argv):
        if player_nb != 2 and player_nb != 4:
            raise ValueError
        self.board = Board(player_nb)
        self.player_nb = player_nb
        self.players_script = [None for _ in range(player_nb)]
        self.players = []
        pygame.init()
        self.header_size = 100
        self.screen_width = 870 if self.player_nb == 2 else 1166
        self.screen_height = 450 + self.header_size if self.player_nb == 2 else 642 + self.header_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.text_font = pygame.font.SysFont('arial', 30)
        self.player_name = ["Player_1", "Player_2", "Player_3", "Player_4"]
        for i in range(self.player_nb):
            splitted = argv[2 + i].split('/')
            self.player_name[i] = splitted[-1].split('.')[0]
        self.players_color = [(0, 151, 230), (232, 65, 24), (76, 209, 55), (251, 197, 4)]
        self.set_colors()
        self.light_color = []

        for i in range(len(self.players_color)):
            self.light_color.append((self.players_color[i][0] + (255 - self.players_color[i][0]) * 60 / 100,
                                     self.players_color[i][1] + (255 - self.players_color[i][1]) * 60 / 100,
                                     self.players_color[i][2] + (255 - self.players_color[i][2]) * 60 / 100))
        self.start_ticks = pygame.time.get_ticks()
        pygame.display.set_caption('Blokus Tournament')

    def set_colors(self):
        colors = [(46, 204, 113), (52, 152, 219), (230, 126, 34), (155, 89, 182), (241, 196, 15), (231, 76, 60), (26, 188, 156)]
        random.seed()
        for i in range(4):
            value = random.randrange(len(colors) - i)
            self.players_color[i] = colors[value]
            colors.pop(value)

    def set_player_script(self, player_id, path):
        if player_id < 0 or player_id >= self.player_nb:
            raise ValueError
        self.players_script[player_id] = path

    async def run(self):
        for i in range(len(self.players_script)):
            if self.players_script[i] is None:
                raise ValueError
            self.players.append(Player(self.players_script[i]))
        for i in range(len(self.players)):
            player = self.players[i]
            await player.create()
            await player.write_stdin("START {}\n".format(self.board.size))
            await player.write_stdin("PLAYER {}\n".format(i))

        self.start_ticks = pygame.time.get_ticks()
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
            if self.board.check_end():
                self.display(win=True)
                continue
            while self.board.surrender[self.board.turn]:
                self.board.next_turn()
                self.start_ticks = pygame.time.get_ticks()
            await self.players[self.board.turn].write_stdin("PLAY\n")
            loop = True
            while loop:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        done = True
                try:
                    if (pygame.time.get_ticks() - self.start_ticks) / 1000 > 20:
                        raise ValueError("Timeout exception")
                    line = await asyncio.wait_for(self.players[self.board.turn].read_stdout(), 0.5)
                    if not line:
                        raise asyncio.TimeoutError
                    loop = await self.exec_cmd(line)
                except asyncio.TimeoutError:
                    pass
                except ValueError as e:
                    print(str(e), file=sys.stderr)
                    print(str(self.board), file=sys.stderr)
                    print('', file=sys.stderr)
                    print("GAME: FORCE SURRENDER FROM {}".format(self.players[self.board.turn].proc.pid), file=sys.stderr)
                    self.board.surrender[self.board.turn] = True
                    self.players[self.board.turn].terminate()
                    loop = False
                self.display()
        return

    def display(self, win=False):
        seconds = (pygame.time.get_ticks() - self.start_ticks) / 1000
        self.screen.fill((0, 0, 0))
        self.draw()
        if not win:
            text = self.text_font.render(
                "{0} turn, elapsed time: {1:.3f} / 20".format(self.player_name[self.board.turn], seconds if seconds < 20 else 20),
                True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen_width / 2, 30))
            self.screen.blit(text, text_rect)
        else:
            string = ""
            for i in range(self.player_nb):
                string += "{0}: {1}{2}".format(self.player_name[i], self.board.count_points(i),
                                                      "" if i == self.player_nb - 1 else " | ")
            text = self.text_font.render(string, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen_width / 2, 30))
            self.screen.blit(text, text_rect)
            winner = 0
            points = self.board.count_points(0)
            for i in range(1, self.board.player_nb):
                if self.board.count_points(i) > points:
                    points = self.board.count_points(i)
                    winner = i
            string = "Winner: {0}".format(self.player_name[winner])
            text = self.text_font.render(string, True, self.players_color[winner])
            text_rect = text.get_rect(center=(self.screen_width / 2, 60))
            self.screen.blit(text, text_rect)
        pygame.display.update()

    def draw(self):
        if self.player_nb == 2:
            self.draw_remaining_piece(0, 0, 68 + self.header_size)
            self.draw_remaining_piece(1, 660, 68 + self.header_size)
        else:
            self.draw_remaining_piece(0, 0, 0 + self.header_size)
            self.draw_remaining_piece(1, 904, 0 + self.header_size)
            self.draw_remaining_piece(2, 0, 380 + self.header_size)
            self.draw_remaining_piece(3, 904, 380 + self.header_size)

        self.draw_board(210 if self.player_nb == 2 else 262, 0 + self.header_size)

    def draw_remaining_piece(self, player_id, x, y):
        margin = 2
        x_off = 0 + margin
        y_off = 0 + margin
        line_length = 200 if self.player_nb == 2 else 250
        tile_size = 10

        text = self.text_font.render("{0}".format(self.player_name[player_id]), True, self.players_color[player_id])
        text_rect = text.get_rect(center=(x + 133 if self.player_nb == 4 else x + 107, y - 15))
        self.screen.blit(text, text_rect)

        for index in range(1, 25 if self.player_nb == 2 else 26):
            if any(piece.id == index for piece in self.board.player_pieces[player_id]):
                piece = first(piece for piece in self.board.player_pieces[player_id] if piece.id == index)
                for i in range(len(piece.shape)):
                    for j in range(len(piece.shape[i])):
                        pygame.draw.rect(self.screen,
                                         (self.light_color[player_id] if not self.board.surrender[player_id] else pygame.Color(
                                         190, 190, 190)) if piece.shape[i][j] == 'O' else (self.players_color[player_id]
                                        if not self.board.surrender[player_id] else pygame.Color(110, 110, 110)),
                                         pygame.Rect(x + x_off + j * tile_size, y + y_off + i * tile_size, tile_size,
                                                     tile_size))
            else:
                for i in range(5):
                    for j in range(5):
                        pygame.draw.rect(self.screen, self.light_color[player_id] if not self.board.surrender[player_id] else pygame.Color(190, 190, 190),
                                         pygame.Rect(x + x_off + j * tile_size, y + y_off + i * tile_size, tile_size,
                                                     tile_size))
            x_off += tile_size * 5 + margin
            if x_off >= line_length:
                y_off += tile_size * 5 + margin
                x_off = 0 + margin

    def draw_board(self, x, y):
        tile_size = 30
        tile_offset = 2

        for i in range(0, len(self.board.board)):
            for j in range(0, len(self.board.board[i])):
                pygame.draw.rect(self.screen, (100, 100, 100) if self.board.board[i][j] == 'O' else self.players_color[
                    int(self.board.board[i][j])], pygame.Rect(tile_offset + x + j * (tile_size + tile_offset),
                                                              tile_offset + y + i * (tile_size + tile_offset),
                                                              tile_size,
                                                              tile_size))
        for i in range(len(self.board.player_start_pos)):
            pos = self.board.player_start_pos[i]
            if self.board.board[pos[1]][pos[0]] == 'O':
                pygame.draw.rect(self.screen, self.light_color[i],
                                 pygame.Rect(tile_offset + x + pos[0] * (tile_size + tile_offset),
                                             tile_offset + y + pos[1] * (tile_size + tile_offset),
                                             tile_size,
                                             tile_size))

    async def exec_cmd(self, line):
        lines = line.strip('\n').split(' ')
        if lines[0] == "SURRENDER":
            if len(lines) != 1:
                raise ValueError("SURRENDER: Wrong args number")
            self.board.surrender[self.board.turn] = True
            await self.players[self.board.turn].write_stdin("DONE\n")
            self.players[self.board.turn].terminate()
            return False
        elif lines[0] == "PIECES":
            if len(lines) != 1:
                raise ValueError("PIECES: Wrong args number")
            string = ""
            for piece in self.board.player_pieces[self.board.turn]:
                string += str(piece.id) + "\n"
            await self.players[self.board.turn].write_stdin(string)
            await self.players[self.board.turn].write_stdin("DONE\n")
        elif lines[0] == "PIECE":
            if len(lines) != 2:
                raise ValueError("PIECE: Wrong args number")
            if int(lines[1]) < 1 or int(lines[1]) > 21:
                raise ValueError("PIECE: Wrong piece id value")
            exist = False
            for piece in self.board.player_pieces[self.board.turn]:
                if int(lines[1]) == piece.id:
                    await self.players[self.board.turn].write_stdin(str(piece))
                    exist = True
            if not exist:
                await self.players[self.board.turn].write_stdin("ALREADY PLACED\n")
            await self.players[self.board.turn].write_stdin("DONE\n")
        elif lines[0] == "BOARD":
            if len(lines) != 1:
                raise ValueError("BOARD: Wrong args number")
            await self.players[self.board.turn].write_stdin(str(self.board))
            await self.players[self.board.turn].write_stdin("DONE\n")
        elif lines[0] == "PLAY":
            if len(lines) != 5:
                raise ValueError("PLAY: Wrong args number")
            arg1 = int(lines[1])
            arg2 = int(lines[2])
            arg3 = int(lines[3])
            arg4 = int(lines[4])
            if arg1 < 1 or arg1 > 21:
                raise ValueError("PLAY: Wrong piece id value")
            if arg2 < 0 or arg2 > self.board.size - 1:
                raise ValueError("PLAY: Wrong x value")
            if arg3 < 0 or arg3 > self.board.size - 1:
                raise ValueError("PLAY: Wrong y value")
            if arg4 != 0 and arg4 != 90 and arg4 != 180 and arg4 != 270:
                raise ValueError("PLAY: Wrong rotation value")
            exist = False
            for piece in self.board.player_pieces[self.board.turn]:
                if arg1 == piece.id:
                    if arg4 == 90:
                        piece.rotate_right()
                    elif arg4 == 180:
                        piece.rotate_right()
                        piece.rotate_right()
                    elif arg4 == 270:
                        piece.rotate_left()
                    self.board.place_piece(self.board.turn, arg1, (arg2, arg3))
                    for i in range(len(self.players)):
                        if i != self.board.turn and not self.board.surrender[i]:
                            await self.players[i].write_stdin(
                                "PLAYED {0} {1} {2} {3} {4}\n".format(self.board.turn, arg1, arg2, arg3, arg4))
                    exist = True
            if not exist:
                await self.players[self.board.turn].write_stdin("ALREADY PLACED\n")
            await self.players[self.board.turn].write_stdin("DONE\n")
            self.board.next_turn()
            self.start_ticks = pygame.time.get_ticks()
            return False
        else:
            raise ValueError("UNKNOWN COMMAND")
        return True
