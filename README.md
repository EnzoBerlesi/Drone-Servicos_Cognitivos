# Surveyor — Drone routing genetic algorithm

Projeto para o Trabalho 2 — UNIBRASIL Surveyor

Resumo
-------
Implementação em Python de um Algoritmo Genético (AG) para planejar o roteiro de um drone autônomo que deve fotografar uma lista de CEPs em Curitiba e retornar ao ponto inicial (CEP 82821020). O AG otimiza a ordem de visita e a programação respeitando restrições de autonomia, janelas de voo diurno (06:00–19:00), efeitos do vento, recargas e um prazo máximo de 7 dias.

Como usar
--------
Requisitos:
- Python 3.8+
- instalar dependências: `pip install -r requirements.txt`

Executar a versão de demo (gera `outputs/flight_plan.csv`):

```powershell
python -m src.main
```

Executar testes e verificar cobertura (local):

```powershell
pytest --maxfail=1 -q
# Para gerar relatório de cobertura (se tiver coverage instalada):
# coverage run -m pytest && coverage report -m
```

Assunções relevantes
--------------------
- A tabela real de ventos não foi fornecida pelo enunciado; incluímos uma tabela de exemplo em `data/wind_table.csv`. O AG usa essa tabela por dia/hora para calcular a componente do vento na direção do voo.
- Consumo de bateria: referência dada (36 km/h => 5000 s de autonomia) é tratada como autonomia em segundos, ajustada por fator 0.93 (Curitiba). A autonomia efetiva = 5000 * 0.93 = 4650 s.
- Consumo por parada: cada parada consome 72 s de autonomia (dec/acc/operacões). Paradas para recarga também consomem esses 72 s antes de recarregar.
- Tempo de recarga (para voltar a 100%): assumido 30 minutos (1800 s). Essa suposição está documentada e pode ser alterada em `src/utils.py`.
- Fotos só podem ser tiradas entre 06:00 e 19:00. Se chegada a um CEP ocorrer fora dessa janela, o leg é adiado até o próximo período de dia.

Arquivos principais
-------------------
- `src/ga.py` — Algoritmo Genético
- `src/drone.py` — Simulação do drone e geração das linhas do CSV
- `src/utils.py` — funções utilitárias (Haversine, velocidade com vento, manipulação de tempo)
- `src/main.py` — runner que carrega dados, executa o AG e escreve `outputs/flight_plan.csv`

Notas de avaliação
------------------
O repositório contém testes unitários em `tests/` — existem pelo menos 3 testes cobrindo Haversine, cálculo de consumo e validade de rota. A cobertura pode ser gerada localmente com `coverage`.

Contato
-------
Identificação dos integrantes: [Coloque aqui os nomes completos e RA/ID de cada integrante antes da entrega final]
