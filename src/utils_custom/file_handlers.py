"""Leitura/escrita simplificada de CSVs usados pelo projeto."""
import csv
from ..core.entities.coordenada import Coordenada


def carregar_coordenadas(caminho):
    """Lê um CSV e retorna objetos `Coordenada`.

    Aceita colunas `latitude`/`longitude` ou `lat`/`lon`.
    """
    resultado = []
    try:
        with open(caminho, 'r', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for linha in reader:
                lat = linha.get('latitude') or linha.get('lat')
                lon = linha.get('longitude') or linha.get('lon')

                coord = Coordenada(cep=linha['cep'], latitude=float(lat), longitude=float(lon))
                resultado.append(coord)

        print(f"OK {len(resultado)} coordenadas carregadas")
        return resultado

    except FileNotFoundError:
        print(f"ERRO: arquivo {caminho} não encontrado")
        return []
    except Exception as e:
        print(f"ERRO ao carregar coordenadas: {e}")
        return []


def salvar_csv(dados, caminho, cabecalho=None):
    """Grava `dados` em CSV; `dados` é uma lista de linhas (iteráveis)."""
    try:
        with open(caminho, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            if cabecalho:
                writer.writerow(cabecalho)
            writer.writerows(dados)
        return True
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")
        return False
