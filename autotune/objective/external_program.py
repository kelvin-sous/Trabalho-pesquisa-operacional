# objective/external_program.py - VERSÃO MELHORADA
import subprocess
import tkinter as tk
from tkinter import filedialog
import re
from utils.logger import log

program_path = None
program_signature = []
num_params = 0


def select_program():
    """Abre o explorador de arquivos para selecionar o executável."""
    global program_path

    root = tk.Tk()
    root.withdraw()
    program_path = filedialog.askopenfilename(
        title="Selecione o executável do programa do professor",
        filetypes=[("Executáveis", "*.exe"), ("Scripts Python", "*.py"), ("Todos os arquivos", "*.*")]
    )

    if not program_path:
        raise FileNotFoundError("Nenhum executável selecionado.")
    
    log(f"📂 Executável selecionado: {program_path}")
    return program_path


def parse_help_output_advanced(output):
    """
    Parser avançado para extrair informações da mensagem de ajuda.
    
    Exemplos que detecta:
    - "programa.exe x1 x2 x3 x4 x5 (valores inteiros de 1 a 100)"
    - "uso: programa [int] [float] [float]"
    - "parâmetros: 5 inteiros"
    """
    
    # Padrão 1: "x1 x2 x3 x4 x5" (conta os x's)
    x_pattern = re.findall(r'\bx\d+\b', output)
    if x_pattern:
        num = len(x_pattern)
        log(f"   ✓ Detectado {num} parâmetros pelo padrão 'x1 x2 x3...'")
        
        # Verifica o tipo
        if 'inteiro' in output.lower() or 'integer' in output.lower():
            types = ['int'] * num
            log(f"   ✓ Tipo: inteiro (detectado pela palavra 'inteiro')")
        elif 'float' in output.lower() or 'real' in output.lower():
            types = ['float'] * num
            log(f"   ✓ Tipo: float (detectado pela palavra 'float')")
        else:
            types = ['int'] * num  # Assume int como padrão
            log(f"   ⚠️  Tipo não especificado, assumindo 'int'")
        
        # Tenta detectar limites (1 a 100, etc)
        bounds_match = re.search(r'(\d+)\s*a\s*(\d+)', output)
        if bounds_match:
            min_val = int(bounds_match.group(1))
            max_val = int(bounds_match.group(2))
            log(f"   ✓ Limites detectados: {min_val} a {max_val}")
            bounds = [(min_val, max_val)] * num
        else:
            bounds = None
        
        return {
            'found': True,
            'num_params': num,
            'types': types,
            'bounds': bounds
        }
    
    # Padrão 2: "[int] [float] [string]"
    bracket_pattern = re.findall(r'\[(int|float|double|string|str|text)\]', output)
    if bracket_pattern:
        types = []
        for t in bracket_pattern:
            if t == 'int':
                types.append('int')
            elif t in ['float', 'double']:
                types.append('float')
            else:
                types.append('str')
        
        log(f"   ✓ Detectado {len(types)} parâmetros pelo padrão [tipo]")
        return {
            'found': True,
            'num_params': len(types),
            'types': types,
            'bounds': None
        }
    
    # Padrão 3: "N parâmetros" ou "N argumentos"
    num_match = re.search(r'(\d+)\s*(?:parâmetros|argumentos|params|args)', output.lower())
    if num_match:
        num = int(num_match.group(1))
        log(f"   ✓ Detectado {num} parâmetros pela descrição")
        
        # Tenta detectar tipo
        if 'inteiro' in output.lower() or 'integer' in output.lower():
            types = ['int'] * num
        elif 'float' in output.lower():
            types = ['float'] * num
        else:
            types = ['float'] * num  # Padrão
        
        return {
            'found': True,
            'num_params': num,
            'types': types,
            'bounds': None
        }
    
    return {'found': False, 'num_params': 0, 'types': [], 'bounds': None}


def try_get_help_info():
    """Tenta extrair informações usando --help ou similar."""
    global program_path
    
    help_attempts = [
        ["--help"],
        ["-h"],
        ["--usage"],
        ["-help"],
        []  # sem argumentos
    ]
    
    for args in help_attempts:
        try:
            cmd = [program_path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            output = (result.stdout + result.stderr)
            
            if output:
                log(f"   Tentativa com {args or '[sem args]'}: {len(output)} caracteres")
                log(f"   Mensagem: {output[:200]}")  # Mostra parte da mensagem
                
                # Usa o parser avançado
                parsed = parse_help_output_advanced(output)
                if parsed['found']:
                    return parsed
        except:
            continue
    
    return {'found': False, 'num_params': 0, 'types': [], 'bounds': None}


def test_program_with_params(params):
    """Testa o programa com um conjunto de parâmetros."""
    global program_path
    
    if program_path is None:
        raise ValueError("Programa não selecionado.")
    
    try:
        str_params = [str(p) for p in params]
        cmd = [program_path] + str_params
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode != 0:
            return False, output, error
        
        try:
            float(output)
            return True, output, error
        except ValueError:
            return False, output, error
            
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def detect_num_params_by_testing():
    """Detecta o número de parâmetros testando o programa."""
    global program_path
    
    log("🔍 Detectando número de parâmetros por tentativa e erro...")
    
    for n in range(1, 11):
        # Para inteiros, testa com valores de 1 a 100
        test_params = [50] * n  # Valor médio seguro
        
        success, output, error = test_program_with_params(test_params)
        
        if success:
            log(f"✅ Programa aceita {n} parâmetros")
            log(f"   Teste com {test_params} → Saída: {output}")
            return n, True
        else:
            log(f"❌ Teste com {n} parâmetros falhou")
            if error and len(error) < 100:
                log(f"   Erro: {error}")
    
    log("⚠️  Não foi possível detectar o número de parâmetros automaticamente")
    return None, False


def detect_param_types(num_params):
    """Detecta os tipos de cada parâmetro."""
    global program_path
    
    log(f"🔍 Detectando tipos dos {num_params} parâmetros...")
    
    types = []
    
    for i in range(num_params):
        base_params = [50] * num_params  # Valores base seguros
        
        # Teste com inteiro
        test_params_int = base_params.copy()
        test_params_int[i] = 10
        success_int, output_int, _ = test_program_with_params(test_params_int)
        
        # Teste com float
        test_params_float = base_params.copy()
        test_params_float[i] = 10.5
        success_float, output_float, _ = test_program_with_params(test_params_float)
        
        if success_int and not success_float:
            param_type = "int"
            log(f"   Parâmetro {i+1}: INT (rejeita decimais)")
        elif success_float:
            param_type = "float"
            log(f"   Parâmetro {i+1}: FLOAT (aceita decimais)")
        else:
            param_type = "int"  # Padrão para inteiro
            log(f"   Parâmetro {i+1}: INT (padrão)")
        
        types.append(param_type)
    
    return types


def detect_program_signature_smart():
    """Detecção automática inteligente da assinatura do programa."""
    global program_path, program_signature, num_params
    
    if program_path is None:
        select_program()
    
    log("="*60)
    log("🤖 DETECÇÃO AUTOMÁTICA DE ASSINATURA DO PROGRAMA")
    log("="*60)
    
    # Etapa 1: Tentar ler --help
    log("\n📖 Etapa 1: Tentando obter informações com --help...")
    help_info = try_get_help_info()
    
    if help_info['found']:
        log(f"✅ Informações encontradas via --help:")
        log(f"   Parâmetros: {help_info['num_params']}")
        log(f"   Tipos: {help_info['types']}")
        if help_info.get('bounds'):
            log(f"   Limites: {help_info['bounds']}")
        
        num_params = help_info['num_params']
        program_signature = help_info['types']
        bounds = help_info.get('bounds')
    else:
        # Etapa 2: Detecção por tentativa e erro
        log("\n🧪 Etapa 2: Detecção por tentativa e erro...")
        detected_num, success = detect_num_params_by_testing()
        
        if not success or detected_num is None:
            log("⚠️  Usando configuração padrão: 2 parâmetros float")
            num_params = 2
            program_signature = ["float", "float"]
            bounds = None
        else:
            num_params = detected_num
            log(f"\n🔬 Etapa 3: Detectando tipos dos {num_params} parâmetros...")
            program_signature = detect_param_types(num_params)
            bounds = None
    
    log("\n" + "="*60)
    log("✅ ASSINATURA DETECTADA:")
    log(f"   Número de parâmetros: {num_params}")
    log(f"   Tipos: {program_signature}")
    for i, t in enumerate(program_signature):
        log(f"      Parâmetro {i+1}: {t}")
    log("="*60 + "\n")
    
    return program_signature, num_params, bounds


def run_external_program(params):
    """Executa o programa com os parâmetros fornecidos."""
    global program_path, program_signature, num_params

    if program_path is None:
        select_program()

    if not program_signature or num_params == 0:
        detect_program_signature_smart()

    if len(params) != num_params:
        raise ValueError(
            f"Número incorreto de parâmetros! "
            f"Esperado: {num_params}, Recebido: {len(params)}"
        )

    # Converte parâmetros
    converted = []
    for p, t in zip(params, program_signature):
        if t == "int":
            converted.append(str(int(round(p))))  # Garante inteiro
        elif t == "float":
            converted.append(f"{float(p):.10f}")
        else:
            converted.append(str(p))

    cmd = [program_path] + converted
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"Programa retornou erro: {error_msg}")
        
        output = result.stdout.strip()
        
        try:
            value = float(output)
            return value
        except ValueError:
            raise ValueError(f"Saída inesperada (não é um número): '{output}'")
            
    except subprocess.TimeoutExpired:
        raise RuntimeError("Programa demorou muito para responder (timeout)")
    except Exception as e:
        raise RuntimeError(f"Erro ao executar programa: {e}")


def get_program_info():
    """Retorna informações sobre o programa detectado."""
    global program_path, program_signature, num_params
    
    return {
        'path': program_path,
        'num_params': num_params,
        'signature': program_signature,
        'detected': bool(program_signature)
    }