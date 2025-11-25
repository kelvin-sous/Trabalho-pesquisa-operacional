# optimizer/pattern_search.py
import numpy as np
from .base_optimizer import BaseOptimizer
from utils.logger import log

class PatternSearch(BaseOptimizer):
    """
    Implementação do método Pattern Search (Direct Search).
    
    O algoritmo funciona da seguinte forma:
    1. Parte de um ponto inicial x0
    2. Para cada dimensão, testa movimentos positivos e negativos
    3. Se encontrar uma melhoria, aceita o novo ponto
    4. Se não houver melhoria em nenhuma direção, reduz o tamanho do passo
    5. Para quando o passo fica menor que a tolerância
    """

    def __init__(self, objective_function, x0, delta=1.0, 
                 delta_min=1e-6, reduction_factor=0.5, **kwargs):
        super().__init__(objective_function, x0, **kwargs)
        self.delta = delta  # Tamanho inicial do passo
        self.delta_min = delta_min  # Passo mínimo antes de parar
        self.reduction_factor = reduction_factor  # Fator de redução do passo
        self.history = []  # Histórico de convergência

    def optimize(self):
        """Executa o algoritmo Pattern Search."""
        x = np.array(self.x0, dtype=float)
        n_dims = len(x)
        
        # Avalia o ponto inicial
        f_best = self.objective_function(x)
        self.history.append({'iteration': 0, 'x': x.copy(), 
                            'f': f_best, 'delta': self.delta})
        
        log("="*70)
        log(f" PATTERN SEARCH - INICIANDO")
        log("="*70)
        log(f"    Configuração:")
        log(f"      • Ponto inicial: {x}")
        log(f"      • Fitness inicial: f(x0) = {f_best:.6f}")
        log(f"      • Dimensões: {n_dims}")
        log(f"      • Delta inicial: {self.delta}")
        log(f"      • Max iterações: {self.max_iter}")
        log("="*70)

        delta = self.delta
        n_eval = 1  # Contador de avaliações da função objetivo

        for iteration in range(1, self.max_iter + 1):
            improved = False
            
            # Busca exploratória: testa cada dimensão
            for i in range(n_dims):
                if improved:
                    break  # Estratégia greedy: para assim que encontrar melhoria
                
                # Testa ambas as direções (+/-)
                for direction in [1, -1]:
                    x_new = np.copy(x)
                    x_new[i] += direction * delta
                    
                    # Avalia o novo ponto
                    f_new = self.objective_function(x_new)
                    n_eval += 1

                    # Se encontrou melhoria, aceita o novo ponto
                    if f_new > f_best:  # MAXIMIZAÇÃO: maior é melhor
                        improvement = f_new - f_best
                        log(f"✓ Iter {iteration}: Melhoria na dim {i} "
                            f"(direção {direction:+d})")
                        log(f"  x[{i}]: {x[i]:.6f} → {x_new[i]:.6f}")
                        log(f"  f: {f_best:.6f} → {f_new:.6f} "
                            f"(Δ = {improvement:.6f})")
                        
                        x = x_new
                        f_best = f_new
                        improved = True
                        
                        self.history.append({
                            'iteration': iteration,
                            'x': x.copy(),
                            'f': f_best,
                            'delta': delta,
                            'improved': True
                        })
                        break

            # Se não houve melhoria, reduz o tamanho do passo
            if not improved:
                delta *= self.reduction_factor
                log(f"✗ Iter {iteration}: Sem melhoria. "
                    f"Reduzindo delta: {delta/self.reduction_factor:.6f} → {delta:.6f}")
                
                self.history.append({
                    'iteration': iteration,
                    'x': x.copy(),
                    'f': f_best,
                    'delta': delta,
                    'improved': False
                })

            # Critério de parada: delta muito pequeno
            if delta < self.delta_min:
                log(f" Convergência atingida: delta ({delta:.2e}) < "
                    f"delta_min ({self.delta_min:.2e})")
                break

        # Resultados finais
        log("="*70)
        log(f" PATTERN SEARCH - OTIMIZAÇÃO CONCLUÍDA")
        log("="*70)
        log(f"    Estatísticas:")
        log(f"      • Iterações: {iteration}/{self.max_iter}")
        log(f"      • Avaliações da função: {n_eval}")
        log(f"      • Delta final: {delta:.2e}")
        log(f"")
        log(f"    Melhor Solução Encontrada:")
        log(f"      • Parâmetros: {x}")
        log(f"      • Fitness: f(x*) = {f_best:.10f}")
        log("="*70)

        return x, f_best, self.history


class PatternSearchWithPattern(BaseOptimizer):
    """
    Versão avançada do Pattern Search com movimento de padrão.
    
    Esta versão inclui um passo adicional de "movimento de padrão"
    que acelera a convergência quando uma direção promissora é encontrada.
    """

    def __init__(self, objective_function, x0, delta=1.0, 
                 alpha=2.0, **kwargs):
        super().__init__(objective_function, x0, **kwargs)
        self.delta = delta
        self.alpha = alpha  # Fator de aceleração do padrão

    def optimize(self):
        x = np.array(self.x0, dtype=float)
        f_best = self.objective_function(x)
        delta = self.delta
        
        log(f" Iniciando Pattern Search com Movimento de Padrão")
        log(f"   Ponto inicial: {x}, f(x0) = {f_best:.6f}")

        for iteration in range(1, self.max_iter + 1):
            x_old = np.copy(x)
            improved = False

            # Fase de busca exploratória
            for i in range(len(x)):
                if improved:
                    break
                
                for direction in [1, -1]:
                    x_new = np.copy(x)
                    x_new[i] += direction * delta
                    f_new = self.objective_function(x_new)

                    if f_new > f_best:  # MAXIMIZACAO
                        x, f_best = x_new, f_new
                        improved = True
                        break

            # Fase de movimento de padrão
            if improved:
                # Calcula o padrão de movimento
                pattern = x - x_old
                x_pattern = x + self.alpha * pattern
                f_pattern = self.objective_function(x_pattern)
                
                if f_pattern > f_best:  # MAXIMIZACAO
                    log(f"Iter {iteration}: Aceleração por padrão! "
                        f"f: {f_best:.6f} → {f_pattern:.6f}")
                    x, f_best = x_pattern, f_pattern
                else:
                    log(f"Iter {iteration}: Melhoria simples. f = {f_best:.6f}")
            else:
                delta *= 0.5
                log(f"✗ Iter {iteration}: Reduzindo delta → {delta:.6f}")

            if delta < self.tol:
                log(f"Convergência atingida")
                break

        log(f"Solução: {x}, f(x*) = {f_best:.6f}")
        return x, f_best