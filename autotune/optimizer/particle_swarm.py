# optimizer/particle_swarm.py
"""
Implementação do Particle Swarm Optimization (PSO).

PSO é um algoritmo de otimização inspirado no comportamento social de
bandos de pássaros ou cardumes de peixes. Cada partícula representa uma
solução candidata que se move pelo espaço de busca influenciada por:
1. Sua própria melhor posição histórica (memória cognitiva)
2. A melhor posição encontrada pelo enxame (memória social)
"""

import numpy as np
from .base_optimizer import BaseOptimizer
from utils.logger import log


class ParticleSwarm(BaseOptimizer):
    """
    Implementação do Particle Swarm Optimization (PSO).
    
    Parâmetros:
    - n_particles: Número de partículas no enxame
    - w: Peso de inércia (controla velocidade anterior)
    - c1: Coeficiente cognitivo (atração para melhor pessoal)
    - c2: Coeficiente social (atração para melhor global)
    - bounds: Limites do espaço de busca [(min, max), ...]
    """
    
    def __init__(self, objective_function, x0, 
                 n_particles=30, w=0.7, c1=1.5, c2=1.5,
                 bounds=None, **kwargs):
        super().__init__(objective_function, x0, **kwargs)
        
        self.n_particles = n_particles
        self.w = w  # Inércia
        self.c1 = c1  # Coeficiente cognitivo
        self.c2 = c2  # Coeficiente social
        self.bounds = bounds
        self.history = []
        
        # Define limites padrão se não fornecidos
        if self.bounds is None:
            # Usa limites baseados no ponto inicial
            self.bounds = [(-10, 10)] * len(x0)
    
    def optimize(self):
        """Executa o algoritmo PSO."""
        n_dims = len(self.x0)
        
        log("="*70)
        log(f" PARTICLE SWARM - INICIANDO")
        log("="*70)
        log(f"    Configuração:")
        log(f"      • Número de partículas: {self.n_particles}")
        log(f"      • Dimensões: {n_dims}")
        log(f"      • Parâmetros: w={self.w}, c1={self.c1}, c2={self.c2}")
        log(f"      • Limites: {self.bounds}")
        log(f"      • Max iterações: {self.max_iter}")
        log("="*70)
        
        # Inicializa posições das partículas (distribuição uniforme nos limites)
        positions = np.zeros((self.n_particles, n_dims))
        for i in range(n_dims):
            low, high = self.bounds[i]
            positions[:, i] = np.random.uniform(low, high, self.n_particles)
        
        # Inicializa velocidades (pequenas)
        velocities = np.zeros((self.n_particles, n_dims))
        for i in range(n_dims):
            low, high = self.bounds[i]
            range_size = high - low
            velocities[:, i] = np.random.uniform(
                -range_size * 0.1, 
                range_size * 0.1, 
                self.n_particles
            )
        
        # Avalia todas as partículas iniciais
        fitness = np.array([self.objective_function(p) for p in positions])
        
        # Melhor posição pessoal de cada partícula
        p_best = positions.copy()
        p_best_fitness = fitness.copy()
        
        # Melhor posição global (MAXIMIZAÇÃO: maior é melhor)
        g_best_idx = np.argmax(fitness)  # Mudado de argmin para argmax
        g_best = positions[g_best_idx].copy()
        g_best_fitness = fitness[g_best_idx]
        
        log(f"    Inicialização completa")
        log(f"      • Fitness inicial: {g_best_fitness:.6f}")
        log(f"      • Posição inicial: {g_best}")
        
        # Histórico
        self.history.append({
            'iteration': 0,
            'g_best': g_best.copy(),
            'g_best_fitness': g_best_fitness,
            'mean_fitness': np.mean(fitness),
            'std_fitness': np.std(fitness)
        })
        
        n_eval = self.n_particles  # Contador de avaliações
        
        # Loop principal
        for iteration in range(1, self.max_iter + 1):
            # Para cada partícula
            for i in range(self.n_particles):
                # Componentes aleatórios
                r1 = np.random.random(n_dims)
                r2 = np.random.random(n_dims)
                
                # Atualiza velocidade
                # v = w*v + c1*r1*(p_best - x) + c2*r2*(g_best - x)
                cognitive = self.c1 * r1 * (p_best[i] - positions[i])
                social = self.c2 * r2 * (g_best - positions[i])
                velocities[i] = self.w * velocities[i] + cognitive + social
                
                # Limita velocidade (evita explosão)
                for j in range(n_dims):
                    low, high = self.bounds[j]
                    v_max = (high - low) * 0.2  # 20% do range
                    velocities[i, j] = np.clip(velocities[i, j], -v_max, v_max)
                
                # Atualiza posição
                positions[i] = positions[i] + velocities[i]
                
                # Aplica limites de posição
                for j in range(n_dims):
                    low, high = self.bounds[j]
                    positions[i, j] = np.clip(positions[i, j], low, high)
                
                # Avalia nova posição
                fitness[i] = self.objective_function(positions[i])
                n_eval += 1
                
                # Atualiza melhor pessoal (MAXIMIZAÇÃO)
                if fitness[i] > p_best_fitness[i]:  # Mudado de < para >
                    p_best[i] = positions[i].copy()
                    p_best_fitness[i] = fitness[i]
                    
                    # Atualiza melhor global
                    if fitness[i] > g_best_fitness:  # Mudado de < para >
                        improvement = fitness[i] - g_best_fitness
                        g_best = positions[i].copy()
                        g_best_fitness = fitness[i]
                        
                        log(f"✓ Iter {iteration}: Nova melhor solução!")
                        log(f"  Partícula {i}: f = {g_best_fitness:.6f}")
                        log(f"  Posição: {g_best}")
                        log(f"  Melhoria: {improvement:.6f}")
            
            # Estatísticas da iteração
            mean_fitness = np.mean(fitness)
            std_fitness = np.std(fitness)
            
            # Log a cada 10 iterações ou se houver melhoria significativa
            if iteration % 10 == 0:
                log(f" Iter {iteration}: g_best = {g_best_fitness:.6f}, "
                    f"mean = {mean_fitness:.6f}, std = {std_fitness:.6f}")
            
            # Salva histórico
            self.history.append({
                'iteration': iteration,
                'g_best': g_best.copy(),
                'g_best_fitness': g_best_fitness,
                'mean_fitness': mean_fitness,
                'std_fitness': std_fitness,
                'positions': positions.copy(),
                'velocities': velocities.copy()
            })
            
            # Critério de convergência: desvio padrão muito pequeno
            if std_fitness < self.tol:
                log(f" Convergência atingida: std ({std_fitness:.2e}) < tol ({self.tol:.2e})")
                break
        
        # Resultados finais
        log("="*70)
        log(f" PARTICLE SWARM - OTIMIZAÇÃO CONCLUÍDA")
        log("="*70)
        log(f"    Estatísticas:")
        log(f"      • Iterações: {iteration}/{self.max_iter}")
        log(f"      • Avaliações da função: {n_eval}")
        log(f"")
        log(f"    Melhor Solução Encontrada:")
        log(f"      • Parâmetros: {g_best}")
        log(f"      • Fitness: {g_best_fitness:.10f}")
        log("="*70)
        
        return g_best, g_best_fitness, self.history


class AdaptivePSO(BaseOptimizer):
    """
    Versão adaptativa do PSO com peso de inércia decrescente.
    
    O peso de inércia começa alto (exploração) e diminui com o tempo
    (intensificação), melhorando a convergência.
    """
    
    def __init__(self, objective_function, x0, 
                 n_particles=30, w_max=0.9, w_min=0.4,
                 c1=2.0, c2=2.0, bounds=None, **kwargs):
        super().__init__(objective_function, x0, **kwargs)
        
        self.n_particles = n_particles
        self.w_max = w_max
        self.w_min = w_min
        self.c1 = c1
        self.c2 = c2
        self.bounds = bounds
        self.history = []
        
        if self.bounds is None:
            self.bounds = [(-10, 10)] * len(x0)
    
    def optimize(self):
        """Executa PSO com inércia adaptativa."""
        n_dims = len(self.x0)
        
        log(f" Iniciando Adaptive PSO")
        log(f"   Partículas: {self.n_particles}, Dimensões: {n_dims}")
        log(f"   w: {self.w_max} → {self.w_min} (adaptativo)")
        log("-" * 60)
        
        # Inicialização (igual ao PSO básico)
        positions = np.zeros((self.n_particles, n_dims))
        for i in range(n_dims):
            low, high = self.bounds[i]
            positions[:, i] = np.random.uniform(low, high, self.n_particles)
        
        velocities = np.zeros((self.n_particles, n_dims))
        for i in range(n_dims):
            low, high = self.bounds[i]
            range_size = high - low
            velocities[:, i] = np.random.uniform(
                -range_size * 0.1, 
                range_size * 0.1, 
                self.n_particles
            )
        
        fitness = np.array([self.objective_function(p) for p in positions])
        p_best = positions.copy()
        p_best_fitness = fitness.copy()
        
        g_best_idx = np.argmin(fitness)
        g_best = positions[g_best_idx].copy()
        g_best_fitness = fitness[g_best_idx]
        
        log(f" Melhor fitness inicial: {g_best_fitness:.6f}")
        
        self.history.append({
            'iteration': 0,
            'g_best': g_best.copy(),
            'g_best_fitness': g_best_fitness,
            'w': self.w_max
        })
        
        # Loop principal com inércia adaptativa
        for iteration in range(1, self.max_iter + 1):
            # Calcula peso de inércia decrescente linearmente
            w = self.w_max - (self.w_max - self.w_min) * iteration / self.max_iter
            
            for i in range(self.n_particles):
                r1 = np.random.random(n_dims)
                r2 = np.random.random(n_dims)
                
                cognitive = self.c1 * r1 * (p_best[i] - positions[i])
                social = self.c2 * r2 * (g_best - positions[i])
                velocities[i] = w * velocities[i] + cognitive + social
                
                # Limita velocidade
                for j in range(n_dims):
                    low, high = self.bounds[j]
                    v_max = (high - low) * 0.2
                    velocities[i, j] = np.clip(velocities[i, j], -v_max, v_max)
                
                positions[i] = positions[i] + velocities[i]
                
                # Limites de posição
                for j in range(n_dims):
                    low, high = self.bounds[j]
                    positions[i, j] = np.clip(positions[i, j], low, high)
                
                fitness[i] = self.objective_function(positions[i])
                
                if fitness[i] > p_best_fitness[i]:  # MAXIMIZAÇÃO
                    p_best[i] = positions[i].copy()
                    p_best_fitness[i] = fitness[i]
                    
                    if fitness[i] > g_best_fitness:  # MAXIMIZAÇÃO
                        improvement = fitness[i] - g_best_fitness
                        g_best = positions[i].copy()
                        g_best_fitness = fitness[i]
                        log(f"✓ Iter {iteration}: f = {g_best_fitness:.6f} "
                            f"(w={w:.3f}, melhoria={improvement:.6f})")
            
            if iteration % 10 == 0:
                log(f"📊 Iter {iteration}: g_best = {g_best_fitness:.6f}, w = {w:.3f}")
            
            self.history.append({
                'iteration': iteration,
                'g_best': g_best.copy(),
                'g_best_fitness': g_best_fitness,
                'w': w
            })
            
            if np.std(fitness) < self.tol:
                log(f" Convergência atingida em {iteration} iterações")
                break
        
        log("-" * 60)
        log(f" Adaptive PSO concluído!")
        log(f"   Melhor solução: {g_best}")
        log(f"   Melhor fitness: {g_best_fitness:.6f}")
        
        return g_best, g_best_fitness, self.history