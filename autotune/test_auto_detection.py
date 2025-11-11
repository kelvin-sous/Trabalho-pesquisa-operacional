# test_auto_detection.py
"""
Script para testar a detecção automática de parâmetros.
Cria programas fake com diferentes configurações e testa a detecção.
"""

import subprocess
import sys
import os
from pathlib import Path


def create_test_program(num_params, types, output_formula, filename):
    """
    Cria um programa de teste Python com número e tipos específicos de parâmetros.
    """
    type_hints = []
    conversions = []
    for i, t in enumerate(types):
        if t == "int":
            type_hints.append(f"[int]")
            conversions.append(f"    p{i} = int(sys.argv[{i+1}])")
        elif t == "float":
            type_hints.append(f"[float]")
            conversions.append(f"    p{i} = float(sys.argv[{i+1}])")
        else:
            type_hints.append(f"[string]")
            conversions.append(f"    p{i} = sys.argv[{i+1}]")
    
    # Monta o código
    params_list = " ".join([f"p{i}" for i in range(num_params)])
    
    code = f"""#!/usr/bin/env python3
import sys

def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Uso: {filename} {' '.join(type_hints)}")
        return
    
    if len(sys.argv) != {num_params + 1}:
        print("Erro: parâmetros inválidos", file=sys.stderr)
        sys.exit(1)
    
    try:
{chr(10).join(conversions)}
        result = {output_formula}
        print(result)
    except Exception as e:
        print(f"Erro: {{e}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
    
    # Salva o arquivo
    with open(filename, 'w') as f:
        f.write(code)
    
    # Torna executável (Linux/Mac)
    try:
        os.chmod(filename, 0o755)
    except:
        pass
    
    return filename


def test_detection(program_path, expected_params, expected_types):
    """
    Testa se a detecção automática funciona corretamente.
    """
    print(f"\n{'='*60}")
    print(f"Testando: {program_path}")
    print(f"Esperado: {expected_params} parâmetros, tipos: {expected_types}")
    print(f"{'='*60}")
    
    # Importa a função de detecção
    from objective.external_program import (
        detect_program_signature_smart,
        program_path as global_path
    )
    import objective.external_program as ext_prog
    
    # Define o caminho do programa
    ext_prog.program_path = program_path
    
    # Executa a detecção
    try:
        detected_types, detected_num = detect_program_signature_smart()
        
        # Verifica se está correto
        success = (detected_num == expected_params and 
                  detected_types == expected_types)
        
        if success:
            print(f"✅ SUCESSO! Detecção correta")
        else:
            print(f"❌ FALHA!")
            print(f"   Esperado: {expected_params} parâmetros, {expected_types}")
            print(f"   Detectado: {detected_num} parâmetros, {detected_types}")
        
        return success
        
    except Exception as e:
        print(f"❌ ERRO durante detecção: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("TESTE DE DETECÇÃO AUTOMÁTICA DE PARÂMETROS")
    print("="*60)
    
    # Cria diretório de testes
    test_dir = Path("test_programs")
    test_dir.mkdir(exist_ok=True)
    
    # Lista de testes
    tests = [
        {
            'name': 'test_2floats.py',
            'num_params': 2,
            'types': ['float', 'float'],
            'formula': '(p0 - 3)**2 + (p1 + 2)**2'
        },
        {
            'name': 'test_3floats.py',
            'num_params': 3,
            'types': ['float', 'float', 'float'],
            'formula': 'p0**2 + p1**2 + p2**2'
        },
        {
            'name': 'test_1int_1float.py',
            'num_params': 2,
            'types': ['int', 'float'],
            'formula': 'p0 * p1'
        },
        {
            'name': 'test_4floats.py',
            'num_params': 4,
            'types': ['float', 'float', 'float', 'float'],
            'formula': 'sum([p0**2, p1**2, p2**2, p3**2])'
        },
    ]
    
    results = []
    
    # Executa os testes
    for test in tests:
        print(f"\n🔧 Criando programa de teste: {test['name']}")
        
        program_path = test_dir / test['name']
        create_test_program(
            test['num_params'],
            test['types'],
            test['formula'],
            str(program_path)
        )
        
        print(f"✅ Programa criado: {program_path}")
        
        # Testa a detecção
        success = test_detection(
            str(program_path),
            test['num_params'],
            test['types']
        )
        
        results.append({
            'name': test['name'],
            'success': success
        })
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    for result in results:
        status = "✅ PASSOU" if result['success'] else "❌ FALHOU"
        print(f"{status} - {result['name']}")
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    
    print(f"\n📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  Alguns testes falharam. Revise a implementação.")


if __name__ == "__main__":
    main()