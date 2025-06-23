from enum import Enum
from typing import List, Tuple, Set, Dict, Optional
import random

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
        self.initial_zone = None
        self.initial_zone_index = None

    def set_initial_zone(self, green_pos: Tuple[int, int], special_zones: List[List[Tuple[int, int]]]):
        """Establece la zona inicial más cercana para la estrategia experta"""
        min_distance = float('inf')
        closest_zone = None
        closest_zone_index = None
        
        for i, zone in enumerate(special_zones):
            for cell in zone:
                distance = abs(green_pos[0] - cell[0]) + abs(green_pos[1] - cell[1])
                if distance < min_distance:
                    min_distance = distance
                    closest_zone = zone
                    closest_zone_index = i
        
        self.initial_zone = closest_zone
        self.initial_zone_index = closest_zone_index

    def get_ai_move(
        self,
        green_pos: Tuple[int, int],
        red_pos: Tuple[int, int],
        painted_cells: Set[Tuple[int, int]],
        cell_owner: Dict[Tuple[int, int], Player],
        move_history: List[Tuple[int, int]] = None
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
                    
                    #No permitir ocupar la misma posición que el oponente
                    if (new_row, new_col) != red_pos:
                        valid_moves.append((new_row, new_col))
            return valid_moves

        def is_repetitive_move(pos: Tuple[int, int], history: List[Tuple[int, int]]) -> bool:
            """Verifica si un movimiento causaría repetición excesiva"""
            if not history or len(history) < 4:
                return False
            
            # Contar cuántas veces aparece esta posición en el historial reciente
            recent_history = history[-4:]
            return recent_history.count(pos) >= 2

        def evaluate_position(green_pos, red_pos, painted_cells, cell_owner) -> float:
            """Función heurística mejorada con anti-bucles y estrategia experta"""
            score = 0.0
            
            # 1. Evaluar control de zonas (peso principal)
            for i, zone in enumerate(self.special_zones):
                green_count = sum(1 for cell in zone if cell in cell_owner and cell_owner[cell] == Player.GREEN)
                red_count = sum(1 for cell in zone if cell in cell_owner and cell_owner[cell] == Player.RED)
                
                # Bonificación por controlar zonas
                if green_count > red_count:
                    score += 10 * (green_count - red_count)
                elif red_count > green_count:
                    score -= 10 * (red_count - green_count)
                
                # Priorizar zona inicial si no está completamente perdida
                if (self.difficulty == Difficulty.EXPERT and 
                    self.initial_zone_index is not None and 
                    i == self.initial_zone_index):
                    
                    # Si aún podemos ganar esta zona, darle alta prioridad
                    if red_count < 3:
                        score += 15 * green_count

                # Bonificación por estar cerca de completar una zona
                if green_count == 4:
                    score += 25
                elif green_count == 3:
                    score += 15
                
                # Penalización si el oponente está cerca de completar
                if red_count == 4:
                    score -= 30
                elif red_count == 3:
                    score -= 20

            # 2. Evaluar proximidad a zonas no controladas
            for zone in self.special_zones:
                for cell in zone:
                    if cell not in painted_cells:
                        g_dist = abs(green_pos[0] - cell[0]) + abs(green_pos[1] - cell[1])
                        r_dist = abs(red_pos[0] - cell[0]) + abs(red_pos[1] - cell[1])
                        
                        # Bonificación por estar más cerca de celdas no pintadas
                        if g_dist < r_dist:
                            score += 3
                        elif r_dist < g_dist:
                            score -= 2

            # 3. Evaluar posición estratégica
            # Bonificación por posiciones centrales (más opciones de movimiento)
            center_distance = abs(green_pos[0] - 3.5) + abs(green_pos[1] - 3.5)
            score += (7 - center_distance) * 0.5

            # 4. Penalización por repetición de movimientos
            if move_history and is_repetitive_move(green_pos, move_history):
                score -= 20

            return score

        def minimax(g_pos, r_pos, painted, cell_owner, maximizing, depth_left, alpha=float('-inf'), beta=float('inf')):
            """Minimax con poda alfa-beta para mejor rendimiento"""
            if depth_left == 0:
                return evaluate_position(g_pos, r_pos, painted, cell_owner), None

            current_pos = g_pos if maximizing else r_pos
            valid_moves = get_valid_knight_moves(current_pos)

            if not valid_moves:
                return evaluate_position(g_pos, r_pos, painted, cell_owner), None

            best_move = None

            if maximizing:
                max_eval = float('-inf')
                
                # Ordenar movimientos para mejorar la poda alfa-beta
                def move_priority(move):
                    priority = 0
                    if is_in_special_zone(move):
                        priority += 100
                    if move_history and is_repetitive_move(move, move_history):
                        priority -= 50
                    return priority
                    
                valid_moves.sort(key=move_priority, reverse=True)
                
                for move in valid_moves:
                    new_painted = painted.copy()
                    new_owner = cell_owner.copy()

                    if is_in_special_zone(move):
                        new_painted.add(move)
                        new_owner[move] = Player.GREEN

                    eval_score, _ = minimax(move, r_pos, new_painted, new_owner, False, depth_left - 1, alpha, beta)
                    
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = move
                    
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                        
                return max_eval, best_move
            else:
                min_eval = float('inf')
                
                for move in valid_moves:
                    new_painted = painted.copy()
                    new_owner = cell_owner.copy()

                    if is_in_special_zone(move):
                        new_painted.add(move)
                        new_owner[move] = Player.RED

                    eval_score, _ = minimax(g_pos, move, new_painted, new_owner, True, depth_left - 1, alpha, beta)
                    
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = move
                    
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                        
                return min_eval, best_move

        # Obtener movimientos válidos
        valid_moves = get_valid_knight_moves(green_pos)
        
        if not valid_moves:
            return None

        # Filtrar movimientos repetitivos
        if move_history:
            non_repetitive_moves = [move for move in valid_moves if not is_repetitive_move(move, move_history)]
            if non_repetitive_moves:
                valid_moves = non_repetitive_moves

        # Si solo hay un movimiento válido, tomarlo directamente
        if len(valid_moves) == 1:
            return valid_moves[0]

        # Usar minimax para encontrar el mejor movimiento
        _, best_move = minimax(green_pos, red_pos, painted_cells, cell_owner, True, depth)
        
        # Fallback: si minimax no encuentra movimiento, tomar uno aleatorio
        if best_move is None:
            best_move = random.choice(valid_moves)
        
        return best_move