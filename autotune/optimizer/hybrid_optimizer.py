# optimizer/hybrid_optimizer.py
"""
Otimizador Híbrido: PSO + Pattern Search

Combina a exploração global do PSO com a busca local refinada do Pattern Search.

Estratégia:
1. PSO explora o espaço de busca (exploração global)
2. Pattern Search refina a melhor solução encontrada (busca local)
"""

import numpy as np
from .base_optimizer import BaseOptimizer
from .particle_swarm import ParticleSwarm
from .pattern_search import PatternSearch
from utils.logger import log


class HybridPSOPatternSearch(BaseOptimizer):
    """
    Otimizador Híbrido que combina PSO e Pattern Search.
    
    Fase 1: PSO para exploração global rápida
    Fase 2: Pattern Search para refinamento local preciso
    """
    
    def __init__(self, objective_function, x0,
                 # Parâmetros PSO
                 n_particles=30, w=0.7, c1=1.5, c2=1.5,
                 pso_max_iter=100,
                 # Parâmetros Pattern Search
                 delta=0.1, delta_min=1e-6, reduction_factor=0.5,
                 ps_max_iter=100,
                 # Outros
                 bounds=None, **kwargs):
        super().__init__(objective_function, x0, **kwargs)
        
        # Parâmetros PSO
        self.n_particles = n_particles
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.pso_max_iter = pso_max_iter
        
        # Parâmetros Pattern Search
        self.delta = delta
        self.delta_min = delta_min
        self.reduction_factor = reduction_factor
        self.ps_max_iter = ps_max_iter
        
        self.bounds = bounds
        if self.bounds is None:
            self.bounds = [(-10, 10)] * len(x0)
        
        self.history = {
            'pso': [],
            'pattern_search': [],
            'phases': []
        }
    
    def optimize(self):
        """Executa otimização híbrida PSO + Pattern Search."""
        n_dims = len(self.x0)
        
        log("="*70)
        log(f" HYBRID (PSO + PATTERN SEARCH) - INICIANDO")
        log("="*70)
        log(f"    Configuração:")
        log(f"      • Dimensões: {n_dims}")
        log(f"      • Limites: {self.bounds}")
        log(f"")
        log(f"    Estratégia em 2 Fases:")
        log(f"      1️  PSO: Exploração global ({self.pso_max_iter} iter)")
        log(f"      2️  Pattern Search: Refinamento local ({self.ps_max_iter} iter)")
        log("="*70)
        log("")
        
        # ============================================================
        # FASE 1: PSO - Exploração Global
        # ============================================================
        log(" FASE 1: PARTICLE SWARM OPTIMIZATION")
        log("   Objetivo: Exploração global do espaço de busca")
        log("-" * 60)
        
        pso = ParticleSwarm(
            objective_function=self.objective_function,
            x0=self.x0,
            n_particles=self.n_particles,
            w=self.w,
            c1=self.c1,
            c2=self.c2,
            bounds=self.bounds,
            max_iter=self.pso_max_iter,
            tol=self.tol
        )
        
        pso_best_x, pso_best_f, pso_history = pso.optimize()
        
        self.history['pso'] = pso_history
        self.history['phases'].append({
            'phase': 'PSO',
            'best_x': pso_best_x.copy(),
            'best_f': pso_best_f,
            'iterations': len(pso_history)
        })
        
        log("")
        log(" Fase PSO concluída!")
        log(f"   Melhor solução PSO: {pso_best_x}")
        log(f"   Fitness PSO: {pso_best_f:.10f}")
        log("")
        
        # ============================================================
        # FASE 2: Pattern Search - Refinamento Local
        # ============================================================
        log(" FASE 2: PATTERN SEARCH")
        log("   Objetivo: Refinamento local da melhor solução PSO")
        log("-" * 60)
        
        pattern_search = PatternSearch(
            objective_function=self.objective_function,
            x0=pso_best_x,  # Começa da melhor solução do PSO
            delta=self.delta,
            delta_min=self.delta_min,
            reduction_factor=self.reduction_factor,
            max_iter=self.ps_max_iter,
            tol=self.tol
        )
        
        ps_best_x, ps_best_f, ps_history = pattern_search.optimize()
        
        self.history['pattern_search'] = ps_history
        self.history['phases'].append({
            'phase': 'Pattern Search',
            'best_x': ps_best_x.copy(),
            'best_f': ps_best_f,
            'iterations': len(ps_history)
        })
        
        # ============================================================
        # Resultados Finais
        # ============================================================
        log("")
        log("="*70)
        log("HYBRID - OTIMIZACAO CONCLUIDA")
        log("="*70)
        
        improvement_pso = abs(pso_best_f - pso_history[0]['g_best_fitness'])  # Invertido
        improvement_ps = abs(ps_best_f - pso_best_f)  # Invertido
        total_improvement = abs(ps_best_f - pso_history[0]['g_best_fitness'])  # Invertido
        
        log(f"    Estatísticas por Fase:")
        log(f"       PSO:")
        log(f"         • Iterações: {len(pso_history)}")
        log(f"         • Fitness inicial: {pso_history[0]['g_best_fitness']:.10f}")
        log(f"         • Fitness final: {pso_best_f:.10f}")
        log(f"         • Melhoria: {improvement_pso:.10f}")
        log(f"")
        log(f"       Pattern Search:")
        log(f"         • Iterações: {len(ps_history)}")
        log(f"         • Fitness inicial: {pso_best_f:.10f}")
        log(f"         • Fitness final: {ps_best_f:.10f}")
        log(f"         • Melhoria: {improvement_ps:.10f}")
        log(f"")
        log(f"    Resultado Final:")
        log(f"      • Parâmetros: {ps_best_x}")
        log(f"      • Fitness: {ps_best_f:.10f}")
        log(f"      • Melhoria total: {total_improvement:.10f}")
        
        if improvement_ps > 0:
            refinement_pct = (improvement_ps / total_improvement * 100) if total_improvement > 0 else 0
            log(f"      • Contribuição do refinamento: {refinement_pct:.2f}%")
        
        log("="*70)
        
        return ps_best_x, ps_best_f, self.history


class AdaptiveHybrid(BaseOptimizer):
    """
    Versão adaptativa do híbrido que decide automaticamente
    quando alternar entre PSO e Pattern Search.
    """
    
    def __init__(self, objective_function, x0, bounds=None,
                 switch_threshold=1e-3, max_stagnation=10, **kwargs):
        super().__init__(objective_function, x0, **kwargs)
        
        self.bounds = bounds or [(-10, 10)] * len(x0)
        self.switch_threshold = switch_threshold
        self.max_stagnation = max_stagnation
        self.history = []
    
    def optimize(self):
        """
        Alterna automaticamente entre PSO e Pattern Search
        baseado na estagnação da busca.
        """
        log(f"Iniciando Hybrid Adaptativo")
        log(f"Alterna entre PSO e PS baseado na convergência")
        log("-" * 60)
        
        current_x = np.array(self.x0, dtype=float)
        current_f = self.objective_function(current_x)
        
        phase = "PSO"
        stagnation_count = 0
        total_iterations = 0
        
        while total_iterations < self.max_iter:
            if phase == "PSO":
                # Executa algumas iterações de PSO
                pso = ParticleSwarm(
                    objective_function=self.objective_function,
                    x0=current_x,
                    n_particles=20,
                    bounds=self.bounds,
                    max_iter=20,
                    tol=self.tol
                )
                new_x, new_f, _ = pso.optimize()
                
            else:  # Pattern Search
                ps = PatternSearch(
                    objective_function=self.objective_function,
                    x0=current_x,
                    delta=0.5,
                    max_iter=20,
                    tol=self.tol
                )
                new_x, new_f, _ = ps.optimize()
            
            # Verifica melhoria (MAXIMIZACAO)
            improvement = new_f - current_f  # Invertido
            
            if improvement < self.switch_threshold:
                stagnation_count += 1
            else:
                stagnation_count = 0
            
            current_x = new_x
            current_f = new_f
            total_iterations += 20
            
            # Alterna fase se estagnou
            if stagnation_count >= self.max_stagnation:
                phase = "Pattern Search" if phase == "PSO" else "PSO"
                log(f"Alternando para {phase}")
                stagnation_count = 0
            
            log(f"Iter {total_iterations}: f = {current_f:.6f} ({phase})")
            
            self.history.append({
                'iteration': total_iterations,
                'phase': phase,
                'x': current_x.copy(),
                'f': current_f
            })
        
        log(f"Híbrido Adaptativo concluído!")
        log(f"Melhor: {current_x}, f = {current_f:.6f}")
        
        return current_x, current_f, self.history