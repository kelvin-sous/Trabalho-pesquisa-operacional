# test_pattern_search.py
"""
Script para testar a implementação do Pattern Search
com funções conhecidas e visualização dos resultados.
"""

import numpy as np
import matplotlib.pyplot as plt
from optimizer.pattern_search import PatternSearch, PatternSearchWithPattern

# ============================================================
# Funções de Teste
# ============================================================

def sphere_function(x):
    """
    Função Esfera: f(x) = sum(xi^2)
    Ótimo global: x* = [0, 0, ...], f(x*) = 0
    """
    return np.sum(x**2)

def rosenbrock_function(x):
    """
    Função de Rosenbrock: f(x,y) = (1-x)^2 + 100(y-x^2)^2
    Ótimo global: x* = [1, 1], f(x*) = 0
    Difícil de otimizar devido ao vale estreito
    """
    return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

def quadratic_function(x):
    """
    Função quadrática simples: f(x,y) = (x-3)^2 + (y+2)^2
    Ótimo global: x* = [3, -2], f(x*) = 0
    (mesma do seu fake_program)
    """
    return (x[0] - 3)**2 + (x[1] + 2)**2

def rastrigin_function(x):
    """
    Função de Rastrigin (multimodal)
    Muito difícil devido aos múltiplos mínimos locais
    """
    A = 10
    n = len(x)
    return A * n + np.sum(x**2 - A * np.cos(2 * np.pi * x))

# ============================================================
# Função de Teste
# ============================================================

def test_function(func, name, x0, bounds=None):
    """Testa uma função de otimização."""
    print("\n" + "="*60)
    print(f"Testando: {name}")
    print("="*60)
    
    # Executa o Pattern Search
    optimizer = PatternSearch(
        objective_function=func,
        x0=x0,
        delta=1.0,
        delta_min=1e-6,
        max_iter=500,
        tol=1e-6
    )
    
    x_opt, f_opt, history = optimizer.optimize()
    
    print(f"\n📊 Resumo:")
    print(f"   Convergiu em {len(history)} iterações")
    print(f"   Solução: {x_opt}")
    print(f"   Valor: {f_opt:.10f}")
    
    return history

def plot_convergence(history, title="Convergência do Pattern Search"):
    """Plota a convergência do algoritmo."""
    iterations = [h['iteration'] for h in history]
    f_values = [h['f'] for h in history]
    deltas = [h['delta'] for h in history]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Gráfico do valor da função objetivo
    ax1.plot(iterations, f_values, 'b-o', linewidth=2, markersize=4)
    ax1.set_xlabel('Iteração')
    ax1.set_ylabel('f(x)')
    ax1.set_title(f'{title} - Valor da Função Objetivo')
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    
    # Gráfico do delta
    ax2.plot(iterations, deltas, 'r-o', linewidth=2, markersize=4)
    ax2.set_xlabel('Iteração')
    ax2.set_ylabel('Delta (tamanho do passo)')
    ax2.set_title('Evolução do Tamanho do Passo')
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig(f'convergence_{title.replace(" ", "_")}.png', dpi=150)
    print(f"✅ Gráfico salvo como 'convergence_{title.replace(' ', '_')}.png'")
    plt.show()

def plot_2d_trajectory(history, func, title="Trajetória"):
    """Plota a trajetória do algoritmo em 2D."""
    if len(history[0]['x']) != 2:
        print("⚠️  Visualização 2D disponível apenas para problemas bidimensionais")
        return
    
    x_hist = np.array([h['x'] for h in history])
    
    # Cria grid para o contorno
    x_min, x_max = x_hist[:, 0].min() - 2, x_hist[:, 0].max() + 2
    y_min, y_max = x_hist[:, 1].min() - 2, x_hist[:, 1].max() + 2
    
    x_grid = np.linspace(x_min, x_max, 100)
    y_grid = np.linspace(y_min, y_max, 100)
    X, Y = np.meshgrid(x_grid, y_grid)
    Z = np.zeros_like(X)
    
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            Z[i, j] = func([X[i, j], Y[i, j]])
    
    plt.figure(figsize=(10, 8))
    plt.contour(X, Y, Z, levels=20, alpha=0.6)
    plt.plot(x_hist[:, 0], x_hist[:, 1], 'r-o', linewidth=2, 
             markersize=6, label='Trajetória')
    plt.plot(x_hist[0, 0], x_hist[0, 1], 'go', markersize=12, 
             label='Início')
    plt.plot(x_hist[-1, 0], x_hist[-1, 1], 'r*', markersize=20, 
             label='Ótimo encontrado')
    
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f'trajectory_{title.replace(" ", "_")}.png', dpi=150)
    print(f"✅ Gráfico salvo como 'trajectory_{title.replace(' ', '_')}.png'")
    plt.show()

# ============================================================
# Testes Principais
# ============================================================

if __name__ == "__main__":
    print("🚀 Testando implementação do Pattern Search\n")
    
    # Teste 1: Função Quadrática (mesma do fake_program)
    print("\n" + "🎯 TESTE 1: Função Quadrática")
    history1 = test_function(
        quadratic_function,
        "Quadrática: (x-3)² + (y+2)²",
        x0=[0.0, 0.0]
    )
    plot_convergence(history1, "Quadrática")
    plot_2d_trajectory(history1, quadratic_function, "Quadrática")
    
    # Teste 2: Função de Rosenbrock
    print("\n" + "🎯 TESTE 2: Função de Rosenbrock")
    history2 = test_function(
        rosenbrock_function,
        "Rosenbrock",
        x0=[-1.0, -1.0]
    )
    plot_convergence(history2, "Rosenbrock")
    plot_2d_trajectory(history2, rosenbrock_function, "Rosenbrock")
    
    # Teste 3: Função Esfera (3D)
    print("\n" + "🎯 TESTE 3: Função Esfera (3D)")
    history3 = test_function(
        sphere_function,
        "Esfera 3D",
        x0=[5.0, -3.0, 2.0]
    )
    plot_convergence(history3, "Esfera 3D")
    
    print("\n" + "="*60)
    print("✅ Todos os testes concluídos!")
    print("="*60)