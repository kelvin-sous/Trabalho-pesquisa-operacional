# main.py
"""
Script principal para executar múltiplos otimizadores em paralelo.
Cada otimizador roda em seu próprio terminal/processo.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from objective.external_program import (
    select_program,
    detect_program_signature_smart,
    get_program_info
)
from utils.logger import log


def create_runner_script(algorithm_name, algorithm_class, config_file):
    """
    Cria um script Python temporário para executar um otimizador específico.
    """
    script_content = f'''# Auto-generated runner for {algorithm_name}
import sys
import os
import json
import numpy as np

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer.{algorithm_class.split(".")[0]} import {algorithm_class.split(".")[-1]}
from objective.external_program import run_external_program
from utils.logger import log
import objective.external_program as ext_prog

def main():
    # Carrega configuração
    with open("{config_file}", "r") as f:
        config = json.load(f)
    
    # Define variáveis globais do external_program
    ext_prog.program_path = config["program_path"]
    ext_prog.program_signature = config["signature"]
    ext_prog.num_params = config["num_params"]
    
    print("="*60)
    log(f"🚀 {algorithm_name}")
    print("="*60)
    
    # Configurações específicas por algoritmo
    if "{algorithm_name}" == "Pattern Search":
        optimizer = {algorithm_class.split(".")[-1]}(
            objective_function=run_external_program,
            x0=config["x0"],
            delta=1.0,
            delta_min=1e-6,
            max_iter=config.get("max_iter", 200),
            tol=1e-6,
            reduction_factor=0.5
        )
    elif "{algorithm_name}" == "Particle Swarm":
        optimizer = {algorithm_class.split(".")[-1]}(
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
    elif "{algorithm_name}" == "Hybrid":
        optimizer = {algorithm_class.split(".")[-1]}(
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
        results = {{
            "algorithm": "{algorithm_name}",
            "best_x": best_x.tolist() if hasattr(best_x, 'tolist') else list(best_x),
            "best_f": float(best_f),
            "iterations": len(history) if history else 0
        }}
        
        result_file = "{config_file}".replace("config", "result")
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print("\\n" + "="*60)
        log(f"✅ {algorithm_name} concluído!")
        log(f"   Melhor solução: {{best_x}}")
        log(f"   Melhor fitness: {{best_f:.10f}}")
        print("="*60)
        
        input("\\nPressione Enter para fechar...")
        
    except Exception as e:
        log(f"❌ Erro: {{e}}")
        import traceback
        traceback.print_exc()
        input("\\nPressione Enter para fechar...")

if __name__ == "__main__":
    main()
'''
    
    runner_file = f"temp_runner_{algorithm_name.lower().replace(' ', '_')}.py"
    with open(runner_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return runner_file


def open_terminal_with_script(script_path, algorithm_name):
    """
    Abre um novo terminal e executa o script.
    Funciona em Windows, Linux e Mac.
    """
    script_path = os.path.abspath(script_path)
    
    if sys.platform == "win32":
        # Windows
        cmd = f'start "Otimização: {algorithm_name}" cmd /k "python {script_path}"'
        subprocess.Popen(cmd, shell=True)
        
    elif sys.platform == "darwin":
        # macOS
        cmd = f'''
        osascript -e 'tell application "Terminal" to do script "cd {os.getcwd()} && python {script_path}"'
        '''
        subprocess.Popen(cmd, shell=True)
        
    else:
        # Linux
        terminals = ['gnome-terminal', 'konsole', 'xterm']
        for terminal in terminals:
            try:
                if terminal == 'gnome-terminal':
                    subprocess.Popen([terminal, '--title', f'Otimização: {algorithm_name}', '--', 'python3', script_path])
                elif terminal == 'konsole':
                    subprocess.Popen([terminal, '-e', f'python3 {script_path}'])
                else:
                    subprocess.Popen([terminal, '-e', f'python3 {script_path}'])
                break
            except FileNotFoundError:
                continue


def main():
    print("="*70)
    print("  🚀 SISTEMA DE OTIMIZAÇÃO MULTI-ALGORITMO")
    print("="*70)
    print()
    print("Este sistema executará 3 algoritmos em paralelo:")
    print("  1. 🎯 Pattern Search - Busca direta coordenada")
    print("  2. 🐦 Particle Swarm - Otimização por enxame")
    print("  3. 🔥 Hybrid (PSO + PS) - Exploração global + refinamento local")
    print()
    print("="*70)
    print()
    
    # Passo 1: Selecionar programa usando diálogo visual
    try:
        log("📂 Abrindo seletor de arquivos...")
        log("   Por favor, selecione o executável do programa para otimizar")
        print()
        
        # Chama select_program que abre o tkinter file dialog
        program_path = select_program()
        
        if not program_path:
            log("❌ Nenhum arquivo selecionado!")
            input("\nPressione Enter para sair...")
            return
            
        print()
        log(f"✅ Arquivo selecionado com sucesso!")
        log(f"   Caminho: {program_path}")
        
    except FileNotFoundError as e:
        log(f"❌ {e}")
        input("\nPressione Enter para sair...")
        return
    except Exception as e:
        log(f"❌ Erro ao selecionar programa: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        return
    
    # Passo 2: Detectar assinatura
    try:
        print()
        log("🔍 Detectando assinatura do programa...")
        log("   Analisando parâmetros e tipos...")
        print()
        
        signature, num_params = detect_program_signature_smart()
        
    except Exception as e:
        log(f"❌ Erro na detecção: {e}")
        log("⚠️  Usando configuração padrão: 2 floats")
        signature = ["float", "float"]
        num_params = 2
    
    if num_params == 0:
        log("❌ Não foi possível detectar a assinatura!")
        log("")
        log("💡 Certifique-se de que o programa:")
        log("   1. Aceita parâmetros na linha de comando")
        log("   2. Retorna um número como saída")
        log("   3. Não requer interação do usuário")
        input("\nPressione Enter para sair...")
        return
    
    # Passo 3: Mostrar informações detectadas
    print()
    print("="*70)
    log("✅ INFORMAÇÕES DO PROGRAMA DETECTADAS")
    print("="*70)
    log(f"   📄 Arquivo: {os.path.basename(program_path)}")
    log(f"   📊 Parâmetros: {num_params}")
    log(f"   🏷️  Tipos: {signature}")
    
    # Ponto inicial
    x0 = [0.0] * num_params
    log(f"   🎯 Ponto inicial: {x0}")
    
    # Define limites baseados nos tipos
    bounds = []
    for i, param_type in enumerate(signature):
        if param_type == "int":
            bounds.append((-10, 10))
        else:
            bounds.append((-10.0, 10.0))
    log(f"   📏 Limites: {bounds}")
    print("="*70)
    
    # Confirmação do usuário
    print()
    response = input("Deseja prosseguir com a otimização? (s/n): ").lower()
    if response not in ['s', 'sim', 'y', 'yes', '']:
        log("❌ Otimização cancelada pelo usuário")
        input("\nPressione Enter para sair...")
        return
    
    # Passo 4: Criar arquivos de configuração
    import json
    
    config = {
        "program_path": program_path,
        "signature": signature,
        "num_params": num_params,
        "x0": x0,
        "bounds": bounds,
        "max_iter": 200
    }
    
    algorithms = [
        ("Pattern Search", "pattern_search.PatternSearch"),
        ("Particle Swarm", "particle_swarm.ParticleSwarm"),
        ("Hybrid", "hybrid_optimizer.HybridPSOPatternSearch")
    ]
    
    # Criar pasta temporária
    temp_dir = Path("temp_optimization")
    temp_dir.mkdir(exist_ok=True)
    
    config_files = []
    runner_files = []
    
    print()
    log("⚙️  Preparando execução dos algoritmos...")
    
    for algo_name, algo_class in algorithms:
        # Cria arquivo de configuração
        config_file = temp_dir / f"config_{algo_name.lower().replace(' ', '_')}.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        config_files.append(config_file)
        
        # Cria script runner
        runner_file = create_runner_script(algo_name, algo_class, str(config_file))
        runner_files.append(runner_file)
        log(f"   ✓ {algo_name} configurado")
    
    # Passo 5: Abrir terminais
    print()
    print("="*70)
    log("🚀 INICIANDO OTIMIZAÇÕES")
    print("="*70)
    log("")
    log("Abrindo terminais para cada algoritmo...")
    log("Cada algoritmo executará independentemente.")
    print()
    time.sleep(1)
    
    for i, (algo_name, runner_file) in enumerate(zip([a[0] for a in algorithms], runner_files), 1):
        log(f"   {i}. Abrindo terminal: {algo_name}")
        open_terminal_with_script(runner_file, algo_name)
        time.sleep(0.8)  # Delay entre aberturas
    
    print()
    print("="*70)
    log("✅ Todos os algoritmos foram iniciados!")
    print("="*70)
    log("")
    log("ℹ️  Informações importantes:")
    log("   • Cada algoritmo está rodando em seu próprio terminal")
    log("   • Você pode acompanhar o progresso em cada janela")
    log("   • Os resultados serão salvos automaticamente")
    log("   • Aguarde a conclusão de todos os algoritmos")
    
    # Aguarda finalização
    print()
    input("⏳ Pressione Enter quando todos os algoritmos terminarem para ver a comparação...")
    
    # Passo 6: Coleta e compara resultados
    print("\n" + "="*70)
    log("📊 COMPARAÇÃO DE RESULTADOS")
    print("="*70)
    
    results = []
    for algo_name in [a[0] for a in algorithms]:
        result_file = temp_dir / f"result_{algo_name.lower().replace(' ', '_')}.json"
        
        if result_file.exists():
            try:
                with open(result_file, 'r') as f:
                    result = json.load(f)
                    results.append(result)
                    
                    print()
                    log(f"🎯 {result['algorithm']}:")
                    log(f"   Melhor solução: {result['best_x']}")
                    log(f"   Fitness: {result['best_f']:.10f}")
                    log(f"   Iterações: {result['iterations']}")
            except Exception as e:
                log(f"\n⚠️  {algo_name}: Erro ao ler resultado - {e}")
        else:
            log(f"\n⚠️  {algo_name}: Resultado não encontrado (ainda não terminou?)")
    
    # Encontra o melhor
    if results:
        best_result = min(results, key=lambda x: x['best_f'])
        
        print("\n" + "="*70)
        log("🏆 MELHOR ALGORITMO")
        print("="*70)
        log(f"   🥇 Algoritmo: {best_result['algorithm']}")
        log(f"   📍 Solução: {best_result['best_x']}")
        log(f"   💎 Fitness: {best_result['best_f']:.10f}")
        log(f"   🔄 Iterações: {best_result['iterations']}")
        print("="*70)
        
        # Estatísticas comparativas
        if len(results) > 1:
            print()
            log("📈 Estatísticas Comparativas:")
            
            fitness_values = [r['best_f'] for r in results]
            iterations = [r['iterations'] for r in results]
            
            log(f"   Melhor fitness: {min(fitness_values):.10f}")
            log(f"   Pior fitness: {max(fitness_values):.10f}")
            log(f"   Diferença: {max(fitness_values) - min(fitness_values):.10f}")
            log(f"   Média de iterações: {sum(iterations)/len(iterations):.0f}")
    else:
        log("\n⚠️  Nenhum resultado encontrado. Verifique se os algoritmos terminaram.")
    
    # Limpeza opcional
    print()
    cleanup = input("🗑️  Limpar arquivos temporários? (s/n): ").lower()
    if cleanup in ['s', 'sim', 'y', 'yes', '']:
        import shutil
        for runner_file in runner_files:
            try:
                os.remove(runner_file)
            except:
                pass
        try:
            shutil.rmtree(temp_dir)
            log("✅ Arquivos temporários removidos")
        except Exception as e:
            log(f"⚠️  Não foi possível remover todos os arquivos: {e}")
    else:
        log(f"ℹ️  Arquivos temporários mantidos em: {temp_dir}")
    
    print()
    log("✅ Execução concluída!")
    print()
    input("Pressione Enter para sair...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")