# Auto-generated runner for Hybrid
import sys
import os
import json
import numpy as np

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer.hybrid_optimizer import HybridPSOPatternSearch
from objective.external_program import run_external_program
from utils.logger import log
import objective.external_program as ext_prog

def main():
    # Carrega configuração
    with open(r"temp_optimization/config_hybrid.json", "r") as f:
        config = json.load(f)
    
    # Define variáveis globais do external_program
    ext_prog.program_path = config["program_path"]
    ext_prog.program_signature = config["signature"]
    ext_prog.num_params = config["num_params"]
    
    print("="*70)
    print(f"   OTIMIZAÇÃO: HYBRID")
    print("="*70)
    print()
    
    # Configurações específicas por algoritmo
    if "Hybrid" == "Pattern Search":
        optimizer = HybridPSOPatternSearch(
            objective_function=run_external_program,
            x0=config["x0"],
            delta=1.0,
            delta_min=1e-6,
            max_iter=config.get("max_iter", 200),
            tol=1e-6,
            reduction_factor=0.5
        )
    elif "Hybrid" == "Particle Swarm":
        optimizer = HybridPSOPatternSearch(
            objective_function=run_external_program,
            x0=config["x0"],
            n_particles=30,
            w=0.7,
            c1=1.5,
            c2=1.5,
            bounds=config.get("bounds"),
            max_iter=config.get("max_iter", 200),
            tol=1e-6
        )
    elif "Hybrid" == "Hybrid":
        optimizer = HybridPSOPatternSearch(
            objective_function=run_external_program,
            x0=config["x0"],
            n_particles=30,
            w=0.7,
            c1=1.5,
            c2=1.5,
            pso_max_iter=100,
            delta=0.1,
            delta_min=1e-6,
            ps_max_iter=100,
            bounds=config.get("bounds"),
            tol=1e-6
        )
    
    # Executa otimização
    try:
        result = optimizer.optimize()
        if len(result) == 3:
            best_x, best_f, history = result
        else:
            best_x, best_f = result
            history = None
        
        # Salva resultados
        results = {
            "algorithm": "Hybrid",
            "best_x": best_x.tolist() if hasattr(best_x, 'tolist') else list(best_x),
            "best_f": float(best_f),
            "iterations": len(history) if history else 0
        }
        
        result_file = r"temp_optimization/config_hybrid.json".replace("config", "result")
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "="*70)
        print(f"   HYBRID - OTIMIZAÇÃO CONCLUÍDA")
        print("="*70)
        log(f"")
        log(f" Melhor Solução Encontrada:")
        log(f"   Parâmetros: {best_x}")
        log(f"   Fitness: {best_f:.10f}")
        log(f"   Iterações: {len(history) if history else 0}")
        print("="*70)
        
        input("\nPressione Enter para fechar...")
        
    except Exception as e:
        log(f" Erro: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para fechar...")

if __name__ == "__main__":
    main()
