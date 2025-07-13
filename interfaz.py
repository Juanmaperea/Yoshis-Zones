import pygame
import sys
import random
from enum import Enum
from typing import List, Tuple, Optional, Set
from algoritmo import GameLogic, Player, Difficulty


# Inicializar pygame
pygame.init()

# Constantes
BOARD_SIZE = 8
CELL_SIZE = 80
BOARD_WIDTH = BOARD_SIZE * CELL_SIZE
BOARD_HEIGHT = BOARD_SIZE * CELL_SIZE
SIDEBAR_WIDTH = 300
WINDOW_WIDTH = BOARD_WIDTH + SIDEBAR_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT + 100

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (240, 240, 240)
DARK_GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
LIGHT_GREEN = (144, 238, 144)
LIGHT_RED = (255, 182, 193)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
DARK_GREEN = (0, 200, 0)
DARK_RED = (200, 0, 0)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3

class YoshisZonesGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Yoshi's Zones")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.cell_owner = {}
        
        # Estado del juego
        self.game_state = GameState.MENU
        self.difficulty = Difficulty.BEGINNER
        self.current_player = Player.GREEN  # La máquina siempre inicia
        
        # Tablero y posiciones
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.green_yoshi_pos = None
        self.red_yoshi_pos = None
        
        # Zonas especiales (esquinas + casillas adyacentes)
        self.special_zones = self._create_special_zones()
        self.logic = GameLogic(self.difficulty, self.special_zones)
        self.painted_cells = set()
        
        # Control de zonas ganadas
        self.zone_winners = {}  # Diccionario: zona_index -> Player
        self.won_zones_cells = set()  # Casillas de zonas ya ganadas
        
        # Puntuación
        self.green_zones_won = 0
        self.red_zones_won = 0
        
        # Control de turno
        self.waiting_for_human = False
        self.game_over = False
        self.winner = None
        
        # Control de tiempo mejorado
        self.ai_move_timer = 0
        self.ai_move_delay = 1500  
        self.human_move_delay = 500 
        self.last_move_time = 0
        self.show_initial_positions = True
        
        # Historial de movimientos para evitar bucles
        self.move_history = []
        self.max_history = 6  
        
        # Mostrar movimientos válidos
        self.show_valid_moves = False
        self.valid_moves_for_display = []

        # Cargar imágenes de los Yoshis
        self.yoshi_green_img = pygame.image.load("./imagenes/yoshi_verde.png")
        self.yoshi_green_img = pygame.transform.scale(self.yoshi_green_img, (CELL_SIZE-10, CELL_SIZE-10))
        self.yoshi_red_img = pygame.image.load("./imagenes/yoshi_rojo.png")
        self.yoshi_red_img = pygame.transform.scale(self.yoshi_red_img, (CELL_SIZE-10, CELL_SIZE-10))

    def _create_special_zones(self) -> List[List[Tuple[int, int]]]:
        """Crea las 4 zonas especiales en las esquinas del tablero"""
        zones = []
        
        # Zona 1: Esquina superior izquierda
        zone1 = [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]
        zones.append(zone1)
        
        # Zona 2: Esquina superior derecha
        zone2 = [(0, 5), (0, 6), (0, 7), (1, 7), (2, 7)]
        zones.append(zone2)
        
        # Zona 3: Esquina inferior izquierda 
        zone3 = [(5, 0), (6, 0), (7, 0), (7, 1), (7, 2)]
        zones.append(zone3)
        
        # Zona 4: Esquina inferior derecha
        zone4 = [(7, 5), (7, 6), (7, 7), (6, 7), (5, 7)]
        zones.append(zone4)
        
        return zones

    def _is_in_special_zone(self, pos: Tuple[int, int]) -> bool:
        """Verifica si una posición está en alguna zona especial"""
        row, col = pos
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return False
        
        for zone in self.special_zones:
            if pos in zone:
                return True
        return False

    def _get_zone_index(self, pos: Tuple[int, int]) -> int:
        """Obtiene el índice de la zona especial donde está la posición"""
        for i, zone in enumerate(self.special_zones):
            if pos in zone:
                return i
        return -1

    def _is_zone_won(self, pos: Tuple[int, int]) -> bool:
        """Verifica si la posición está en una zona ya ganada"""
        zone_index = self._get_zone_index(pos)
        return zone_index in self.zone_winners

    def _get_valid_knight_moves(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Obtiene todos los movimientos válidos de caballo desde una posición"""
        row, col = pos
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        valid_moves = []
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE):
                new_pos = (new_row, new_col)
                
                # No permitir movimiento a casillas ya pintadas
                if new_pos in self.painted_cells:
                    continue
                
                # No permitir movimiento a zonas ya ganadas
                if self._is_zone_won(new_pos):
                    continue
                
                # No permitir que los Yoshis ocupen la misma posición
                other_yoshi_pos = self.red_yoshi_pos if pos == self.green_yoshi_pos else self.green_yoshi_pos
                if other_yoshi_pos and new_pos == other_yoshi_pos:
                    continue
                
                valid_moves.append(new_pos)
        
        return valid_moves

    def _place_yoshis_randomly(self):
        """Coloca los Yoshis en posiciones aleatorias válidas (NO en zonas especiales)"""
        available_positions = []
        
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                pos = (row, col)
                if not self._is_in_special_zone(pos):
                    available_positions.append(pos)
        
        if len(available_positions) < 2:
            raise ValueError(f"No hay suficientes posiciones válidas para colocar los Yoshis")
        
        selected_positions = random.sample(available_positions, 2)
        
        self.green_yoshi_pos = selected_positions[0]
        self.red_yoshi_pos = selected_positions[1]
        
        # Registrar la zona inicial de la IA para estrategia experta
        self.logic.set_initial_zone(self.green_yoshi_pos, self.special_zones)
        
        # Limpiar historial de movimientos
        self.move_history.clear()

    def _check_zone_completion(self, zone_index: int):
        """Verifica si una zona ha sido ganada por tener 3 casillas del mismo color"""
        zone = self.special_zones[zone_index]
        
        # Contar casillas por jugador
        green_count = 0
        red_count = 0
        
        for cell in zone:
            if cell in self.cell_owner:
                if self.cell_owner[cell] == Player.GREEN:
                    green_count += 1
                elif self.cell_owner[cell] == Player.RED:
                    red_count += 1
        
        # Verificar si algún jugador ha ganado la zona (3 casillas)
        if green_count >= 3 and zone_index not in self.zone_winners:
            self.zone_winners[zone_index] = Player.GREEN
            self._mark_zone_as_won(zone_index, Player.GREEN)
            self.green_zones_won += 1
        elif red_count >= 3 and zone_index not in self.zone_winners:
            self.zone_winners[zone_index] = Player.RED
            self._mark_zone_as_won(zone_index, Player.RED)
            self.red_zones_won += 1

    def _mark_zone_as_won(self, zone_index: int, winner: Player):
        """Marca toda la zona como ganada por el jugador especificado"""
        zone = self.special_zones[zone_index]
        
        # Marcar todas las casillas de la zona como pintadas y del color del ganador
        for cell in zone:
            self.painted_cells.add(cell)
            self.cell_owner[cell] = winner
            self.won_zones_cells.add(cell)

    def _check_zone_winners(self):
        """Verifica qué zonas han sido ganadas por tener 3 casillas del mismo color"""
        for i in range(len(self.special_zones)):
            if i not in self.zone_winners:  # Solo verificar zonas no ganadas
                self._check_zone_completion(i)

    def _is_game_over(self) -> bool:
        """Verifica si el juego ha terminado"""
        # El juego termina cuando todas las zonas especiales han sido ganadas
        # o cuando no hay más movimientos válidos
        return len(self.zone_winners) == len(self.special_zones)

    def _is_repetitive_move(self, new_pos: Tuple[int, int]) -> bool:
        """Verifica si el movimiento causaría una repetición excesiva"""
        if len(self.move_history) < 4:
            return False
        
        # Verificar patrones de movimiento repetitivo
        recent_moves = self.move_history[-4:]
        if recent_moves.count(new_pos) >= 2:
            return True
        
        return False

    def _make_move(self, new_pos: Tuple[int, int]):
        """Realiza un movimiento del jugador actual"""
        # Agregar al historial de movimientos
        self.move_history.append(new_pos)
        if len(self.move_history) > self.max_history:
            self.move_history.pop(0)
        
        if self.current_player == Player.GREEN:
            self.green_yoshi_pos = new_pos
        else:
            self.red_yoshi_pos = new_pos

        # Si la nueva posición está en una zona especial, la pintamos
        if self._is_in_special_zone(new_pos):
            self.painted_cells.add(new_pos)
            self.cell_owner[new_pos] = self.current_player
            
            # Verificar si se ganó la zona
            zone_index = self._get_zone_index(new_pos)
            if zone_index >= 0:
                self._check_zone_completion(zone_index)

        # Cambiar turno
        self.current_player = Player.RED if self.current_player == Player.GREEN else Player.GREEN
        
        # Actualizar tiempo del último movimiento
        self.last_move_time = pygame.time.get_ticks()

        # Verificar si el juego terminó
        if self._is_game_over():
            self.game_over = True
            if self.green_zones_won > self.red_zones_won:
                self.winner = Player.GREEN
            elif self.red_zones_won > self.green_zones_won:
                self.winner = Player.RED
            else:
                self.winner = None

    def _draw_menu(self):
        """Dibuja el menú principal"""
        self.screen.fill(WHITE)
        
        title = self.font.render("YOSHI'S ZONES", True, BLACK)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Botones de dificultad
        difficulties = [
            ("Principiante", Difficulty.BEGINNER),
            ("Amateur", Difficulty.AMATEUR),
            ("Experto", Difficulty.EXPERT)
        ]
        
        for i, (text, diff) in enumerate(difficulties):
            color = GREEN if diff == self.difficulty else LIGHT_GRAY
            pygame.draw.rect(self.screen, color, (WINDOW_WIDTH//2 - 150, 200 + i*60, 300, 50))
            text_surface = self.small_font.render(text, True, BLACK)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH//2, 225 + i*60))
            self.screen.blit(text_surface, text_rect)
        
        # Botón de inicio
        pygame.draw.rect(self.screen, BLUE, (WINDOW_WIDTH//2 - 100, 400, 200, 50))
        start_text = self.font.render("INICIAR", True, WHITE)
        start_rect = start_text.get_rect(center=(WINDOW_WIDTH//2, 425))
        self.screen.blit(start_text, start_rect)

    def _draw_board(self):
        """Dibuja el tablero de ajedrez con mejor visualización"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                
                # Color base del tablero (ajedrez)
                base_color = WHITE if (row + col) % 2 == 0 else LIGHT_GRAY
                
                # Determinar el color final de la celda
                pos = (row, col)
                zone_index = self._get_zone_index(pos)
                
                if zone_index >= 0:  # Es una zona especial
                    if zone_index in self.zone_winners:
                        # Zona ganada - colorear toda la zona del color del ganador
                        winner = self.zone_winners[zone_index]
                        if winner == Player.GREEN:
                            color = DARK_GREEN
                        else:
                            color = DARK_RED
                    elif pos in self.painted_cells:
                        # Casilla pintada en zona no ganada
                        owner = self.cell_owner.get(pos)
                        if owner == Player.GREEN:
                            color = LIGHT_GREEN
                        elif owner == Player.RED:
                            color = LIGHT_RED
                        else:
                            color = YELLOW
                    else:
                        # Zona especial disponible
                        color = YELLOW
                else:
                    # Casilla normal
                    color = base_color
                
                # Destacar movimientos válidos
                if pos in self.valid_moves_for_display:
                    color = ORANGE
                
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)
                
                # Agregar texto "GANADA" en zonas ganadas
                if zone_index >= 0 and zone_index in self.zone_winners:
                    text_color = WHITE if self.zone_winners[zone_index] == Player.GREEN else WHITE
                    won_text = self.small_font.render("GANADA", True, text_color)
                    text_rect = won_text.get_rect(center=(x + CELL_SIZE//2, y + CELL_SIZE//2))
                    self.screen.blit(won_text, text_rect)
        
        # Dibujar Yoshis
        if self.green_yoshi_pos:
            col, row = self.green_yoshi_pos[1], self.green_yoshi_pos[0]
            x = col * CELL_SIZE + 5
            y = row * CELL_SIZE + 5
            self.screen.blit(self.yoshi_green_img, (x, y))

        if self.red_yoshi_pos:
            col, row = self.red_yoshi_pos[1], self.red_yoshi_pos[0]
            x = col * CELL_SIZE + 5
            y = row * CELL_SIZE + 5
            self.screen.blit(self.yoshi_red_img, (x, y))

    def _draw_sidebar(self):
        """Dibuja la barra lateral con información del juego"""
        sidebar_x = BOARD_WIDTH
        pygame.draw.rect(self.screen, LIGHT_GRAY, (sidebar_x, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT))
        
        # Título
        title = self.font.render("INFORMACIÓN", True, BLACK)
        self.screen.blit(title, (sidebar_x + 10, 20))
        
        # Dificultad actual
        diff_text = f"Dificultad: {self.difficulty.name}"
        diff_surface = self.small_font.render(diff_text, True, BLACK)
        self.screen.blit(diff_surface, (sidebar_x + 10, 60))
        
        # Turno actual con información adicional
        if self.show_initial_positions:
            current = "Iniciando... (IA jugará en breve)"
        else:
            current_time = pygame.time.get_ticks()
            if self.current_player == Player.GREEN:
                remaining_time = max(0, self.ai_move_delay - (current_time - self.last_move_time)) // 1000
                current = f"IA (Verde) - {remaining_time}s"
            else:
                remaining_time = max(0, self.human_move_delay - (current_time - self.last_move_time)) // 1000
                current = f"Humano (Rojo) - {remaining_time}s"
        
        turn_text = f"Turno: {current}"
        turn_surface = self.small_font.render(turn_text, True, BLACK)
        self.screen.blit(turn_surface, (sidebar_x + 10, 90))
        
        # Mostrar posiciones actuales
        if self.green_yoshi_pos:
            green_pos_text = f"Verde en: {self.green_yoshi_pos}"
            green_pos_surface = self.small_font.render(green_pos_text, True, GREEN)
            self.screen.blit(green_pos_surface, (sidebar_x + 10, 120))
        
        if self.red_yoshi_pos:
            red_pos_text = f"Rojo en: {self.red_yoshi_pos}"
            red_pos_surface = self.small_font.render(red_pos_text, True, RED)
            self.screen.blit(red_pos_surface, (sidebar_x + 10, 145))
        
        # Puntuación
        score_text = "PUNTUACIÓN:"
        score_surface = self.small_font.render(score_text, True, BLACK)
        self.screen.blit(score_surface, (sidebar_x + 10, 180))
        
        green_score = f"Verde: {self.green_zones_won} zonas"
        green_surface = self.small_font.render(green_score, True, GREEN)
        self.screen.blit(green_surface, (sidebar_x + 10, 210))
        
        red_score = f"Rojo: {self.red_zones_won} zonas"
        red_surface = self.small_font.render(red_score, True, RED)
        self.screen.blit(red_surface, (sidebar_x + 10, 240))
        
        # Mostrar zonas ganadas específicas
        zones_won_text = "ZONAS GANADAS:"
        zones_surface = self.small_font.render(zones_won_text, True, BLACK)
        self.screen.blit(zones_surface, (sidebar_x + 10, 270))
        
        y_offset = 300
        zone_names = ["Sup. Izq.", "Sup. Der.", "Inf. Izq.", "Inf. Der."]
        for i, zone_name in enumerate(zone_names):
            if i in self.zone_winners:
                winner = self.zone_winners[i]
                color = GREEN if winner == Player.GREEN else RED
                winner_text = "Verde" if winner == Player.GREEN else "Rojo"
                zone_text = f"{zone_name}: {winner_text}"
            else:
                color = DARK_GRAY
                zone_text = f"{zone_name}: Disponible"
            
            zone_surface = self.small_font.render(zone_text, True, color)
            self.screen.blit(zone_surface, (sidebar_x + 10, y_offset + i*20))
        
        # Instrucciones mejoradas
        instructions = [
            "INSTRUCCIONES:",
            "- Los Yoshis se mueven como",
            "  caballos de ajedrez",
            "- Haz clic en una casilla",
            "  naranja (válida) para moverte",
            "- Gana una zona con 3 casillas",
            "- Zonas ganadas se colorean",
            "  completamente",
            "- No puedes moverte a zonas",
            "  ya ganadas"
        ]
        
        for i, instruction in enumerate(instructions):
            color = BLACK if i == 0 else DARK_GRAY
            font = self.small_font if i > 0 else self.small_font
            inst_surface = font.render(instruction, True, color)
            self.screen.blit(inst_surface, (sidebar_x + 10, 400 + i*22))

    def _draw_game_over(self):
        """Dibuja la pantalla de fin de juego"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if self.winner == Player.GREEN:
            message = "¡LA IA HA GANADO!"
            color = GREEN
        elif self.winner == Player.RED:
            message = "¡HAS GANADO!"
            color = RED
        else:
            message = "¡EMPATE!"
            color = BLUE
        
        text_surface = self.font.render(message, True, color)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        self.screen.blit(text_surface, text_rect)
        
        final_score = f"Verde: {self.green_zones_won} - Rojo: {self.red_zones_won}"
        score_surface = self.small_font.render(final_score, True, WHITE)
        score_rect = score_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
        self.screen.blit(score_surface, score_rect)
        
        pygame.draw.rect(self.screen, BLUE, (WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 50, 200, 50))
        menu_text = self.small_font.render("VOLVER AL MENÚ", True, WHITE)
        menu_rect = menu_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 75))
        self.screen.blit(menu_text, menu_rect)

    def _handle_click(self, pos: Tuple[int, int]):
        """Maneja los clics del mouse"""
        x, y = pos
        
        if self.game_state == GameState.MENU:
            if 200 <= y <= 250:
                self.difficulty = Difficulty.BEGINNER
                self.logic.difficulty = self.difficulty
            elif 260 <= y <= 310:
                self.difficulty = Difficulty.AMATEUR
                self.logic.difficulty = self.difficulty
            elif 320 <= y <= 370:
                self.difficulty = Difficulty.EXPERT
                self.logic.difficulty = self.difficulty
            elif 400 <= y <= 450 and WINDOW_WIDTH//2 - 100 <= x <= WINDOW_WIDTH//2 + 100:
                # Iniciar juego
                self.game_state = GameState.PLAYING
                self._place_yoshis_randomly()
                self.green_zones_won = 0
                self.red_zones_won = 0
                self.painted_cells.clear()
                self.cell_owner.clear()
                self.zone_winners.clear()
                self.won_zones_cells.clear()
                self.current_player = Player.GREEN
                self.game_over = False
                self.winner = None
                
                self.ai_move_timer = pygame.time.get_ticks()
                self.last_move_time = pygame.time.get_ticks()
                self.show_initial_positions = True
                self.show_valid_moves = False
                self.valid_moves_for_display.clear()
                
        elif self.game_state == GameState.PLAYING and not self.game_over:
            # Solo permitir clics del humano en su turno y después del delay
            current_time = pygame.time.get_ticks()
            if (self.current_player == Player.RED and x < BOARD_WIDTH and 
                current_time - self.last_move_time >= self.human_move_delay):
                
                col = x // CELL_SIZE
                row = y // CELL_SIZE
                
                if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                    valid_moves = self._get_valid_knight_moves(self.red_yoshi_pos)
                    if (row, col) in valid_moves:
                        self._make_move((row, col))
                        self.show_valid_moves = False
                        self.valid_moves_for_display.clear()
                        
        elif self.game_over:
            if (WINDOW_HEIGHT//2 + 50 <= y <= WINDOW_HEIGHT//2 + 100 and
                WINDOW_WIDTH//2 - 100 <= x <= WINDOW_WIDTH//2 + 100):
                self.game_state = GameState.MENU
                
    def update(self):
        """Actualiza la lógica del juego"""
        current_time = pygame.time.get_ticks()
        
        if (self.game_state == GameState.PLAYING and not self.game_over):
            
            # Turno de la IA
            if self.current_player == Player.GREEN:
                if self.show_initial_positions:
                    if current_time - self.ai_move_timer > self.ai_move_delay:
                        self.show_initial_positions = False
                        # Hacer el primer movimiento de la IA
                        ai_move = self.logic.get_ai_move(
                            self.green_yoshi_pos,
                            self.red_yoshi_pos,
                            self.painted_cells,
                            self.cell_owner,
                            self.move_history
                        )
                        if ai_move:
                            self._make_move(ai_move)
                else:
                    # Movimientos normales de la IA con delay
                    if current_time - self.last_move_time >= self.ai_move_delay:
                        ai_move = self.logic.get_ai_move(
                            self.green_yoshi_pos,
                            self.red_yoshi_pos,
                            self.painted_cells,
                            self.cell_owner,
                            self.move_history
                        )
                        if ai_move:
                            self._make_move(ai_move)
            
            # Turno del humano - mostrar movimientos válidos
            elif self.current_player == Player.RED:
                if current_time - self.last_move_time >= self.human_move_delay:
                    if not self.show_valid_moves:
                        self.show_valid_moves = True
                        self.valid_moves_for_display = self._get_valid_knight_moves(self.red_yoshi_pos)

    def draw(self):
        """Dibuja toda la interfaz"""
        if self.game_state == GameState.MENU:
            self._draw_menu()
        elif self.game_state == GameState.PLAYING:
            self.screen.fill(WHITE)
            self._draw_board()
            self._draw_sidebar()
            if self.game_over:
                self._draw_game_over()

    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_click(event.pos)
            
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# Ejecutar el juego
if __name__ == "__main__":
    game = YoshisZonesGame()
    game.run()