# Drone Route Optimization - Trabalho 2 UNIBRASIL

Algoritmo Genético para otimização de rotas de drone em Curitiba.

## 📋 Descrição

Implementação em Python de um Algoritmo Genético (AG) para planejar o roteiro ótimo de um drone autônomo que deve fotografar uma lista de CEPs em Curitiba e retornar à base (CEP 82821020). O AG otimiza a ordem de visita, velocidades e horários respeitando:

- ✅ Autonomia variável com velocidade: A(v) = 5000 × (36/v)² × 0.93
- ✅ Efeito de vento com soma vetorial
- ✅ Janela operacional: 06:00-19:00 
- ✅ Prazo máximo: 7 dias
- ✅ Custos: R$80 por pouso + R$80 adicional após 17:00

## 🚀 Instalação e Execução

### Pré-requisitos
- Python 3.8+
- pip

### Instalação

```bash
# Clone o repositório
git clone https://github.com/EnzoBerlesi/Drone-Servicos_Cognitivos.git
cd Drone-Servicos_Cognitivos

# Instale as dependências
pip install -r requirements.txt
```

### Execução

**1. Gerar solução otimizada (CSV):**
```bash
python -m src.main
```

Saída: `outputs/flight_plan.csv`

**2. Visualizar rota no gráfico:**
```bash
python -m src.visualize_route
```

Saída: `outputs/route_visualization.png` + janela interativa

**3. Executar testes:**
```bash
python -m pytest -v
```

**4. Ver cobertura de código:**
```bash
python -m pytest --cov=src --cov-report=html
```

Relatório: `htmlcov/index.html`

## 📁 Estrutura do Projeto

```
Drone-Servicos_Cognitivos/
├── src/
│   ├── __init__.py
│   ├── main.py              # Script principal
│   ├── ga.py                # Algoritmo Genético
│   ├── drone.py             # Simulador do drone
│   ├── utils.py             # Funções utilitárias
│   └── visualize_route.py   # Geração de gráficos
├── data/
│   ├── ceps.csv             # Coordenadas dos CEPs
│   └── wind_table.csv       # Dados de vento (7 dias × 5 horários)
├── tests/
│   ├── conftest.py
│   ├── test_drone.py
│   ├── test_ga.py
│   ├── test_utils.py
│   ├── test_pdf_specifications.py
│   └── ...
├── outputs/
│   ├── flight_plan.csv      # Solução gerada
│   └── route_visualization.png
├── requirements.txt
└── README.md
```

## 🧬 Algoritmo Genético

**Parâmetros:**
- População: 50 indivíduos
- Gerações: 200
- Elite: 2 (preservados)
- Mutação: 15%

**Operadores:**
- Crossover: Order Crossover (OX) + Uniform
- Seleção: Torneio (tournament)
- Fitness: `1 / (1 + tempo + pousos×3600 + custo×100)`

## 📊 Formato de Saída

CSV com 11 colunas:
```
CEP inicial, Latitude inicial, Longitude inicial, Dia do voo, Hora inicial, 
Velocidade, CEP final, Latitude final, Longitude final, Pouso, Hora final
```

## 🧪 Testes

**49 testes unitários e de integração**
- Cobertura: 87%
- Valida todas as especificações do PDF

## 📦 Deploy

Para fazer deploy em outro ambiente:

```bash
# 1. Clone o repositório
git clone https://github.com/EnzoBerlesi/Drone-Servicos_Cognitivos.git
cd Drone-Servicos_Cognitivos

# 2. Crie ambiente virtual (opcional mas recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Execute
python -m src.main
python -m src.visualize_route
python -m pytest -v
```

## 👥 Autores

- Enzo Berlesi
- [Adicionar outros membros da equipe]

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos - UNIBRASIL 2025
- Se quiser que o runner (`src/main.py`) aceite matrícula ou outros parâmetros, posso adicionar argumentos de linha de comando.

Estrutura principal
-------------------
- `src/ga.py` — Algoritmo Genético (população, crossover, mutação, fitness)
- `src/drone.py` — Simulador: `DroneSimulator`, `FlightSegment` e geração do CSV
- `src/utils.py` — utilitários (haversine, vento, janelas de tempo, constantes)
- `src/visualize_route.py` — geração de gráfico de visualização da rota
- `data/` — `ceps.csv` e `wind_table.csv` (dados de entrada)
- `tests/` — suíte de testes (unitários e integrais)
- `outputs/` — `flight_plan.csv` (solução) e `route_visualization.png` (gráfico)

Próximos passos que posso implementar
------------------------------------
- Adicionar argumentos CLI a `src/main.py` (por exemplo `--matricula`).
- Incluir GitHub Actions para rodar testes automaticamente em PRs.
- Acrescentar mais testes específicos (CSV header validado a partir da execução de `main`, regras detalhadas de matrícula, quantização estrita em todas fases).

Contato
-------
Coloque aqui os nomes do(s) integrante(s) antes da entrega final.
