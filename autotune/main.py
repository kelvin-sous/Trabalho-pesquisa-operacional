# main.py
"""
Script principal para executar o autotune com Pattern Search.
Detecção automática e inteligente de parâmetros do executável.
"""

import numpy as np
from optimizer.pattern_search import PatternSearch
from objective.external_program import (
    run_external_program, 
    select_program, 
    detect_program_signature_smart,
    get_program_info
)
from utils.logger import log


def main():
    print("="*60)
    log("🚀 AUTOTUNE COM PATTERN SEARCH")
    print("="*60 + "\n")
    
    # Passo 1: Selecionar o executável
    try:
        select_program()
    except FileNotFoundError as e:
        log(f"❌ Erro: {e}")
        return
    except Exception as e:
        log(f"❌ Erro ao selecionar programa: {e}")
        return
    
    # Passo 2: Detectar automaticamente a assinatura do programa
    try:
        signature, num_params = detect_program_signature_smart()
    except Exception as e:
        log(f"❌ Erro na detecção de assinatura: {e}")
        log("⚠️  Tentando usar configuração padrão: 2 floats")
        signature = ["float", "float"]
        num_params = 2
    
    # Validação: verifica se detectou corretamente
    if num_params == 0 or not signature:
        log("❌ Não foi possível detectar a assinatura do programa!")
        log("💡 Dica: Certifique-se que o programa:")
        log("   1. Aceita parâmetros na linha de comando")
        log("   2. Retorna um número como saída")
        log("   3. Não requer interação do usuário")
        return
    
    # Passo 3: Solicitar ponto inicial ao usuário (opcional)
    x0 = get_initial_point(num_params, signature)
    
    log(f"\n🎯 Configuração da Otimização:")
    log(f"   Ponto inicial: {x0}")
    log(f"   Número de parâmetros: {num_params}")
    log(f"   Tipos: {signature}")
    
    # Passo 4: Testar execução inicial
    log(f"\n🧪 Testando execução inicial...")
    try:
        f_initial = run_external_program(x0)
        log(f"✅ Teste bem-sucedido! f(x0) = {f_initial:.6f}")
    except Exception as e:
        log(f"❌ Erro no teste inicial: {e}")
        log("⚠️  O programa pode não estar funcionando corretamente")
        
        # Pergunta se deseja continuar
        response = input("\nDeseja continuar mesmo assim? (s/n): ").lower()
        if response != 's':
            log("❌ Otimização cancelada pelo usuário")
            return
    
    # Passo 5: Configurar o otimizador
    log(f"\n⚙️  Configurando Pattern Search...")
    
    optimizer = PatternSearch(
        objective_function=run_external_program,
        x0=x0,
        delta=1.0,           # Tamanho inicial do passo
        delta_min=1e-6,      # Passo mínimo antes de parar
        max_iter=200,        # Máximo de iterações (aumentado)
        tol=1e-6,            # Tolerância
        reduction_factor=0.5 # Fator de redução do delta
    )
    
    # Passo 6: Executar a otimização
    log(f"\n🔄 Iniciando otimização...\n")
    
    try:
        best_x, best_f, history = optimizer.optimize()
        
        # Passo 7: Exibir resultados finais
        display_results(best_x, best_f, history, signature)
        
        # Passo 8: Salvar resultados
        save_results(best_x, best_f, history, signature)
        
    except KeyboardInterrupt:
        log("\n⚠️  Otimização interrompida pelo usuário")
    except Exception as e:
        log(f"\n❌ Erro durante otimização: {e}")
        import traceback
        traceback.print_exc()


def get_initial_point(num_params, signature):
    """
    Solicita ou define o ponto inicial para a otimização.
    """
    log(f"\n📝 Definindo ponto inicial ({num_params} parâmetros)...")
    
    # Opção automática: começa do zero
    use_auto = input("Usar ponto inicial automático (zeros)? (s/n, padrão=s): ").lower()
    
    if use_auto in ['', 's', 'sim', 'y', 'yes']:
        x0 = [0.0] * num_params
        log(f"   → Usando zeros: {x0}")
    else:
        # Solicita valores manualmente
        x0 = []
        log("   Digite o valor para cada parâmetro:")
        for i, param_type in enumerate(signature):
            while True:
                try:
                    value_str = input(f"      Parâmetro {i+1} ({param_type}): ")
                    
                    if param_type == "int":
                        value = int(value_str)
                    elif param_type == "float":
                        value = float(value_str)
                    else:
                        value = value_str
                    
                    x0.append(value)
                    break
                except ValueError:
                    log(f"      ⚠️  Valor inválido para tipo {param_type}, tente novamente")
        
        log(f"   → Ponto inicial definido: {x0}")
    
    return x0


def display_results(best_x, best_f, history, signature):
    """Exibe os resultados da otimização de forma formatada."""
    print("\n" + "="*60)
    log("🏆 RESULTADOS FINAIS DA OTIMIZAÇÃO")
    print("="*60)
    
    log(f"\n📊 Estatísticas:")
    log(f"   Total de iterações: {len(history)}")
    
    # Conta avaliações
    total_evals = sum(1 for h in history if 'improved' in h)
    log(f"   Total de avaliações: {total_evals}")
    
    # Melhoria total
    f_initial = history[0]['f']
    improvement = f_initial - best_f
    improvement_pct = (improvement / abs(f_initial) * 100) if f_initial != 0 else 0
    
    log(f"   Valor inicial: {f_initial:.10f}")
    log(f"   Valor final: {best_f:.10f}")
    log(f"   Melhoria: {improvement:.10f} ({improvement_pct:.2f}%)")
    
    log(f"\n🎯 Melhor Solução Encontrada:")
    for i, (param_type, value) in enumerate(zip(signature, best_x)):
        if param_type == "int":
            log(f"   Parâmetro {i+1} ({param_type}): {int(value)}")
        elif param_type == "float":
            log(f"   Parâmetro {i+1} ({param_type}): {value:.10f}")
        else:
            log(f"   Parâmetro {i+1} ({param_type}): {value}")
    
    log(f"\n💎 Valor da Função Objetivo: {best_f:.10f}")
    
    print("="*60 + "\n")


def save_results(best_x, best_f, history, signature, filename="autotune_results.txt"):
    """Salva os resultados da otimização em um arquivo detalhado."""
    try:
        from datetime import datetime
        from objective.external_program import get_program_info
        
        program_info = get_program_info()
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write("="*70 + "\n")
            f.write("RESULTADOS DA OTIMIZAÇÃO - PATTERN SEARCH\n")
            f.write("="*70 + "\n\n")
            
            # Data e hora
            f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            # Informações do programa
            f.write("PROGRAMA OTIMIZADO:\n")
            f.write(f"  Caminho: {program_info['path']}\n")
            f.write(f"  Número de parâmetros: {program_info['num_params']}\n")
            f.write(f"  Tipos de parâmetros: {program_info['signature']}\n\n")
            
            # Melhor solução
            f.write("="*70 + "\n")
            f.write("MELHOR SOLUÇÃO ENCONTRADA:\n")
            f.write("="*70 + "\n")
            for i, (param_type, value) in enumerate(zip(signature, best_x)):
                if param_type == "int":
                    f.write(f"  Parâmetro {i+1} ({param_type}): {int(value)}\n")
                elif param_type == "float":
                    f.write(f"  Parâmetro {i+1} ({param_type}): {value:.15f}\n")
                else:
                    f.write(f"  Parâmetro {i+1} ({param_type}): {value}\n")
            
            f.write(f"\nValor da Função Objetivo: {best_f:.15f}\n\n")
            
            # Estatísticas
            f.write("="*70 + "\n")
            f.write("ESTATÍSTICAS DA OTIMIZAÇÃO:\n")
            f.write("="*70 + "\n")
            f.write(f"  Total de iterações: {len(history)}\n")
            
            improvements = sum(1 for h in history if h.get('improved', False))
            f.write(f"  Iterações com melhoria: {improvements}\n")
            f.write(f"  Iterações sem melhoria: {len(history) - improvements}\n")
            
            f_initial = history[0]['f']
            improvement = f_initial - best_f
            f.write(f"  Valor inicial: {f_initial:.15f}\n")
            f.write(f"  Valor final: {best_f:.15f}\n")
            f.write(f"  Melhoria total: {improvement:.15f}\n")
            
            if f_initial != 0:
                improvement_pct = (improvement / abs(f_initial) * 100)
                f.write(f"  Melhoria percentual: {improvement_pct:.2f}%\n")
            
            f.write(f"  Delta inicial: {history[0]['delta']:.6e}\n")
            f.write(f"  Delta final: {history[-1]['delta']:.6e}\n\n")
            
            # Histórico detalhado
            f.write("="*70 + "\n")
            f.write("HISTÓRICO DE CONVERGÊNCIA:\n")
            f.write("="*70 + "\n")
            f.write(f"{'Iter':<6} {'f(x)':<18} {'Delta':<12} {'Status':<10}\n")
            f.write("-"*70 + "\n")
            
            for h in history:
                status = "✓ Melhoria" if h.get('improved', False) else "✗ Sem melhoria"
                f.write(f"{h['iteration']:<6} {h['f']:<18.10e} {h['delta']:<12.6e} {status:<10}\n")
            
            f.write("\n" + "="*70 + "\n")
        
        log(f"💾 Resultados salvos em '{filename}'")
        
    except Exception as e:
        log(f"⚠️  Não foi possível salvar os resultados: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()