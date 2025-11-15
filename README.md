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

# Surveyor — Planejamento de rotas de drone (Trabalho 2)

Projeto para o Trabalho 2 — AG que gera um plano de voo para um drone fotografar uma lista de CEPs e retornar à base.

Visão rápida
------------
- O AG otimiza a ordem de visita, velocidades por trecho e horário de início.
- O simulador modela autonomia (em segundos), custos de parada, recargas e janela diária de operação (06:00–19:00).
- Gera um CSV (`outputs/flight_plan.csv`) com o plano de voo seguindo o formato do enunciado.

Instalação e execução (Windows / PowerShell)
-------------------------------------------
1. Ative a virtualenv do projeto (se existir `.venv`):

```powershell
& "C:/Users/enzol/OneDrive/Área de Trabalho/Drone/.venv/Scripts/Activate.ps1"
```

2. Instale dependências (caso necessário):

```powershell
& "C:/Users/enzol/OneDrive/Área de Trabalho/Drone/.venv/Scripts/python.exe" -m pip install -r requirements.txt
```

3. Rodar os testes:

```powershell
& "C:/Users/enzol/OneDrive/Área de Trabalho/Drone/.venv/Scripts/python.exe" -m pytest -q
```

4. Gerar um `flight_plan.csv` (modo demo):

```powershell
& "C:/Users/enzol/OneDrive/Área de Trabalho/Drone/.venv/Scripts/python.exe" -m src.main
```

Formato de saída (CSV)
----------------------
O CSV de saída segue o cabeçalho exigido no enunciado (ordem e rótulos):

`CEP inicial, Latitude inicial, Longitude inicial, Dia do voo, Hora inicial, Velocidade, CEP final, Latitude final, Longitude final, Pouso, Hora final`

Comportamentos importantes
-------------------------
- Velocidades geradas pelo AG são quantizadas em múltiplos de 4 km/h (4..96).
- Regras específicas de matrícula (ex.: matrícula iniciada por '2') são consideradas pelo simulador quando informado.
- Se quiser que o runner (`src/main.py`) aceite matrícula ou outros parâmetros, posso adicionar argumentos de linha de comando.

Estrutura principal
-------------------
- `src/ga.py` — Algoritmo Genético (população, crossover, mutação, fitness)
- `src/drone.py` — Simulador: `DroneSimulator`, `FlightSegment` e geração do CSV
- `src/utils.py` — utilitários (haversine, vento, janelas de tempo, constantes)
- `data/` — `ceps.csv` e `wind_table.csv` (dados de entrada)
- `tests/` — suíte de testes (unitários e integrais)

Próximos passos que posso implementar
------------------------------------
- Adicionar argumentos CLI a `src/main.py` (por exemplo `--matricula`).
- Incluir GitHub Actions para rodar testes automaticamente em PRs.
- Acrescentar mais testes específicos (CSV header validado a partir da execução de `main`, regras detalhadas de matrícula, quantização estrita em todas fases).

Contato
-------
Coloque aqui os nomes do(s) integrante(s) antes da entrega final.
