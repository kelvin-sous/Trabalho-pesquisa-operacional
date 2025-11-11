# objective/external_program.py
import subprocess
import tkinter as tk
from tkinter import filedialog
import re
from utils.logger import log

program_path = None
program_signature = []  # lista de tipos de parâmetros detectados
num_params = 0  # número de parâmetros detectados


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


def test_program_with_params(params):
    """
    Testa o programa com um conjunto de parâmetros.
    Retorna (sucesso, output, erro).
    """
    global program_path
    
    if program_path is None:
        raise ValueError("Programa não selecionado.")
    
    try:
        # Converte todos os parâmetros para string
        str_params = [str(p) for p in params]
        cmd = [program_path] + str_params
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5  # timeout de 5 segundos
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        # Verifica se houve erro
        if result.returncode != 0:
            return False, output, error
        
        # Verifica se a saída parece válida (um número)
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
    """
    Detecta o número de parâmetros testando o programa com
    diferentes quantidades de parâmetros.
    """
    global program_path
    
    log("🔍 Detectando número de parâmetros por tentativa e erro...")
    
    # Testa de 1 até 10 parâmetros (ajuste se necessário)
    for n in range(1, 11):
        # Testa com valores 0.0 para todos os parâmetros
        test_params = [0.0] * n
        
        success, output, error = test_program_with_params(test_params)
        
        if success:
            log(f"✅ Programa aceita {n} parâmetros")
            log(f"   Teste com {test_params} → Saída: {output}")
            return n, True
        else:
            log(f"❌ Teste com {n} parâmetros falhou")
            if error:
                log(f"   Erro: {error}")
    
    log("⚠️  Não foi possível detectar o número de parâmetros automaticamente")
    return None, False


def detect_param_types(num_params):
    """
    Detecta os tipos de cada parâmetro testando com valores diferentes.
    Retorna uma lista de tipos: ['int', 'float', 'str', ...]
    """
    global program_path
    
    log(f"🔍 Detectando tipos dos {num_params} parâmetros...")
    
    types = []
    
    for i in range(num_params):
        # Testa se aceita inteiros vs floats
        # Cria parâmetros base (zeros)
        base_params = [0.0] * num_params
        
        # Teste 1: com inteiro
        test_params_int = base_params.copy()
        test_params_int[i] = 5
        success_int, output_int, _ = test_program_with_params(test_params_int)
        
        # Teste 2: com float
        test_params_float = base_params.copy()
        test_params_float[i] = 5.5
        success_float, output_float, _ = test_program_with_params(test_params_float)
        
        # Teste 3: com string (apenas para verificar se rejeita)
        test_params_str = base_params.copy()
        test_params_str[i] = "test"
        success_str, _, _ = test_program_with_params(test_params_str)
        
        # Determina o tipo baseado nos testes
        if success_str:
            param_type = "str"
            log(f"   Parâmetro {i+1}: STRING (aceita texto)")
        elif success_float and not success_int:
            param_type = "float"
            log(f"   Parâmetro {i+1}: FLOAT (requer decimais)")
        elif success_int and success_float:
            # Se aceita ambos, verifica se há diferença na saída
            try:
                val_int = float(output_int)
                val_float = float(output_float)
                if abs(val_int - val_float) < 1e-9:
                    param_type = "int"
                    log(f"   Parâmetro {i+1}: INT (int e float dão mesmo resultado)")
                else:
                    param_type = "float"
                    log(f"   Parâmetro {i+1}: FLOAT (diferença entre int e float)")
            except:
                param_type = "float"
                log(f"   Parâmetro {i+1}: FLOAT (padrão)")
        else:
            # Padrão: float
            param_type = "float"
            log(f"   Parâmetro {i+1}: FLOAT (padrão - não determinado)")
        
        types.append(param_type)
    
    return types


def detect_program_signature_smart():
    """
    Versão inteligente que detecta automaticamente:
    1. Número de parâmetros
    2. Tipo de cada parâmetro
    """
    global program_path, program_signature, num_params
    
    if program_path is None:
        select_program()
    
    log("="*60)
    log("🤖 DETECÇÃO AUTOMÁTICA DE ASSINATURA DO PROGRAMA")
    log("="*60)
    
    # Etapa 1: Tentar ler --help ou documentação
    log("\n📖 Etapa 1: Tentando obter informações com --help...")
    help_info = try_get_help_info()
    
    if help_info['found']:
        log(f"✅ Informações encontradas:")
        log(f"   Parâmetros: {help_info['num_params']}")
        log(f"   Tipos: {help_info['types']}")
        num_params = help_info['num_params']
        program_signature = help_info['types']
    else:
        # Etapa 2: Detecção por tentativa e erro
        log("\n🧪 Etapa 2: Detecção por tentativa e erro...")
        detected_num, success = detect_num_params_by_testing()
        
        if not success or detected_num is None:
            # Fallback: assume 2 floats
            log("⚠️  Usando configuração padrão: 2 parâmetros float")
            num_params = 2
            program_signature = ["float", "float"]
        else:
            num_params = detected_num
            # Etapa 3: Detectar tipos
            log(f"\n🔬 Etapa 3: Detectando tipos dos {num_params} parâmetros...")
            program_signature = detect_param_types(num_params)
    
    log("\n" + "="*60)
    log("✅ ASSINATURA DETECTADA:")
    log(f"   Número de parâmetros: {num_params}")
    log(f"   Tipos: {program_signature}")
    for i, t in enumerate(program_signature):
        log(f"      Parâmetro {i+1}: {t}")
    log("="*60 + "\n")
    
    return program_signature, num_params


def try_get_help_info():
    """
    Tenta extrair informações do programa usando --help, -h, ou sem argumentos.
    Retorna um dicionário com as informações encontradas.
    """
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
            output = (result.stdout + result.stderr).lower()
            
            if output:
                log(f"   Tentativa com {args or '[sem args]'}: {len(output)} caracteres")
                
                # Tenta parsear a saída
                parsed = parse_help_output(output)
                if parsed['found']:
                    return parsed
        except:
            continue
    
    return {'found': False, 'num_params': 0, 'types': []}


def parse_help_output(output):
    """
    Tenta extrair número e tipos de parâmetros da saída de ajuda.
    """
    # Padrão 1: "uso: programa [int] [float]"
    pattern1 = re.findall(r'\[(int|float|double|string|str|text)\]', output)
    if pattern1:
        types = []
        for t in pattern1:
            if t in ['int']:
                types.append('int')
            elif t in ['float', 'double']:
                types.append('float')
            elif t in ['string', 'str', 'text']:
                types.append('str')
        
        if types:
            return {'found': True, 'num_params': len(types), 'types': types}
    
    # Padrão 2: "parâmetros: 2" ou "parameters: 2"
    pattern2 = re.search(r'(?:parâmetros|parameters|params|args):\s*(\d+)', output)
    if pattern2:
        num = int(pattern2.group(1))
        # Assume float como padrão
        return {'found': True, 'num_params': num, 'types': ['float'] * num}
    
    # Padrão 3: conta ocorrências de tipos mencionados
    int_count = len(re.findall(r'\bint\b', output))
    float_count = len(re.findall(r'\b(?:float|double)\b', output))
    
    if int_count > 0 or float_count > 0:
        types = ['int'] * int_count + ['float'] * float_count
        if types:
            return {'found': True, 'num_params': len(types), 'types': types}
    
    return {'found': False, 'num_params': 0, 'types': []}


def run_external_program(params):
    """
    Executa o programa com os parâmetros fornecidos.
    Valida se a quantidade de parâmetros está correta.
    """
    global program_path, program_signature, num_params

    if program_path is None:
        select_program()

    # Se ainda não detectamos a assinatura, detecta agora
    if not program_signature or num_params == 0:
        detect_program_signature_smart()

    # Validação: verifica se o número de parâmetros está correto
    if len(params) != num_params:
        raise ValueError(
            f"Número incorreto de parâmetros! "
            f"Esperado: {num_params}, Recebido: {len(params)}"
        )

    # Converte cada parâmetro conforme o tipo esperado
    converted = []
    for p, t in zip(params, program_signature):
        if t == "int":
            converted.append(str(int(p)))
        elif t == "float":
            converted.append(f"{float(p):.10f}")
        else:  # texto ou outro tipo
            converted.append(str(p))

    # Monta o comando
    cmd = [program_path] + converted
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Verifica se houve erro
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"Programa retornou erro: {error_msg}")
        
        output = result.stdout.strip()
        
        # Tenta converter para float
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
    """
    Retorna informações sobre o programa detectado.
    Útil para debugging e logs.
    """
    global program_path, program_signature, num_params
    
    return {
        'path': program_path,
        'num_params': num_params,
        'signature': program_signature,
        'detected': bool(program_signature)
    }