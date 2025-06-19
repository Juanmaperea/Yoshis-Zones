from enum import Enum
from typing import List, Tuple, Set, Dict, Optional

class Player(Enum):
    GREEN = 1
    RED = 2

class Difficulty(Enum):
    BEGINNER = 2
    AMATEUR = 4
    EXPERT = 6

class GameLogic:
    def __init__(self, difficulty: Difficulty, special_zones: List[List[Tuple[int, int]]]):
        self.difficulty = difficulty
        self.special_zones = special_zones

    def get_ai_move(
        self,
        green_pos: Tuple[int, int],
        red_pos: Tuple[int, int],
        painted_cells: Set[Tuple[int, int]],
        cell_owner: Dict[Tuple[int, int], Player]
    ) -> Optional[Tuple[int, int]]:
        depth = self.difficulty.value

        def is_in_special_zone(pos: Tuple[int, int]) -> bool:
            for zone in self.special_zones:
                if pos in zone:
                    return True
            return False

        def get_valid_knight_moves(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
            row, col = pos
            knight_moves = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            valid_moves = []
            for dr, dc in knight_moves:
                new_row, new_col = row + dr, col + dc
                if (0 <= new_row < 8 and 0 <= new_col < 8 and
                    (new_row, new_col) not in painted_cells):
                    valid_moves.append((new_row, new_col))
            return valid_moves
        
        
        
        
        """
        IMPLEMENTA AQUÍ TU FUNCIÓN HEURÍSTICA
        
        Esta función debe evaluar qué tan buena es una posición para el jugador verde (IA).
        
        Considera factores como:
        - Proximidad a zonas especiales no controladas
        - Control actual de zonas especiales
        - Bloqueo de movimientos del oponente
        - Posiciones centrales vs periféricas
        
        Retorna un valor float donde:
        - Valores positivos favorecen al jugador verde
        - Valores negativos favorecen al jugador rojo
        """
        def evaluate_position(green_pos, red_pos, painted_cells, cell_owner) -> float:
            score = 0.0
            for zone in self.special_zones:
                green_count = 0
                red_count = 0
                for cell in zone:
                    if cell in cell_owner:
                        if cell_owner[cell] == Player.GREEN:
                            green_count += 1
                        elif cell_owner[cell] == Player.RED:
                            red_count += 1
                if green_count > red_count:
                    score += 1
                elif red_count > green_count:
                    score -= 1

            for zone in self.special_zones:
                for cell in zone:
                    if cell not in painted_cells:
                        g_dist = abs(green_pos[0] - cell[0]) + abs(green_pos[1] - cell[1])
                        r_dist = abs(red_pos[0] - cell[0]) + abs(red_pos[1] - cell[1])
                        score += (r_dist - g_dist) * 0.05

            return score
        
        

        # ================================================================


        """
        IMPLEMENTA AQUÍ EL ALGORITMO MINIMAX
        
        Esta función debe:
        1. Implementar el algoritmo minimax con la profundidad según la dificultad:
           - BEGINNER: profundidad 2
           - AMATEUR: profundidad 4
           - EXPERT: profundidad 6
        
        2. Usar una función heurística que evalúe:
           - Control de zonas especiales
           - Posiciones estratégicas
           - Bloqueo del oponente
        
        3. Retornar la mejor jugada como tupla (fila, columna)
        
        Parámetros disponibles:
        - self.green_yoshi_pos: posición actual del Yoshi verde (IA)
        - self.red_yoshi_pos: posición actual del Yoshi rojo (humano)
        - self.special_zones: lista de zonas especiales
        - self.painted_cells: conjunto de celdas ya pintadas
        - self.difficulty.value: profundidad del árbol (2, 4, o 6)
        """

        def minimax(g_pos, r_pos, painted, cell_owner, maximizing, depth_left):
            if depth_left == 0:
                return evaluate_position(g_pos, r_pos, painted, cell_owner), None

            current_pos = g_pos if maximizing else r_pos
            valid_moves = get_valid_knight_moves(current_pos)

            if not valid_moves:
                return evaluate_position(g_pos, r_pos, painted, cell_owner), None

            best_value = float('-inf') if maximizing else float('inf')
            best_move = None

            for move in valid_moves:
                new_painted = painted.copy()
                new_owner = cell_owner.copy()

                if is_in_special_zone(move):
                    new_painted.add(move)
                    new_owner[move] = Player.GREEN if maximizing else Player.RED

                if maximizing:
                    val, _ = minimax(move, r_pos, new_painted, new_owner, False, depth_left - 1)
                    if val > best_value:
                        best_value = val
                        best_move = move
                else:
                    val, _ = minimax(g_pos, move, new_painted, new_owner, True, depth_left - 1)
                    if val < best_value:
                        best_value = val
                        best_move = move

            return best_value, best_move

        _, best = minimax(green_pos, red_pos, painted_cells, cell_owner, True, depth)
        return best