"""
Utilitários para leitura e escrita de arquivos
"""
import csv
from ..core.entities.coordenada import Coordenada

def carregar_coordenadas(caminho):
    """
    Carrega coordenadas de um arquivo CSV.
    
    Args:
        caminho: Caminho para o arquivo CSV
    
    Returns:
        list: Lista de objetos Coordenada
    """
    coordenadas = []
    try:
        with open(caminho, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for linha in reader:
                # Suportar ambos os formatos: lat/lon e latitude/longitude
                lat = linha.get('latitude') or linha.get('lat')
                lon = linha.get('longitude') or linha.get('lon')
                
                coord = Coordenada(
                    cep=linha['cep'],
                    latitude=float(lat),
                    longitude=float(lon)
                )
                coordenadas.append(coord)
        
        print(f"OK {len(coordenadas)} coordenadas carregadas")
        return coordenadas
    
    except FileNotFoundError:
        print(f"ERRO: Arquivo {caminho} nao encontrado")
        return []
    except Exception as e:
        print(f"ERRO ao carregar coordenadas: {e}")
        return []

def salvar_csv(dados, caminho, cabecalho=None):
    """
    Salva dados em arquivo CSV.
    
    Args:
        dados: Dados a serem salvos (lista de listas)
        caminho: Caminho do arquivo de saída
        cabecalho: Lista com nomes das colunas (opcional)
    
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        with open(caminho, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if cabecalho:
                writer.writerow(cabecalho)
            writer.writerows(dados)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar CSV: {e}")
        return False
