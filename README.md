# 🚁 UNIBRASIL Surveyor - Sistema de Otimização de Rotas de Drone

Sistema inteligente de otimização de rotas para drone autônomo utilizando Algoritmo Genético.

## 📋 Descrição

Sistema completo em Python para planejamento otimizado de rotas de drone para fotografar 374 locais em Curitiba, retornando à base UNIBRASIL (CEP 82821020). Implementa Algoritmo Genético com otimização local 2-opt, considerando:

- ✅ **Autonomia dinâmica**: A(v) = 5000 × (36/v)² × 0.93 minutos
- ✅ **Efeito de vento vetorial**: Interpolação de tabela 7 dias × 6 horários
- ✅ **Janela operacional**: 06:00-19:00 diariamente
- ✅ **Prazo máximo**: 7 dias
- ✅ **Gestão de custos**: R$80 por recarga + R$80 taxa tardia (após 18:00)
- ✅ **Velocidades válidas**: 36-72 km/h (múltiplos de 4)

## 🚀 Instalação e Execução

### Pré-requisitos
- Python 3.13+ (compatível com 3.8+)
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

**1. Executar sistema completo:**
```bash
python src/main.py
```

**Saídas geradas:**
- `outputs/flight_plan.csv` - Plano de voo detalhado (375 trechos)
- `outputs/resumo_execucao.csv` - Resumo da execução
- `outputs/evolucao.png` - Gráfico de evolução do AG

**2. Executar testes (100% passando):**
```bash
pytest tests/ -v
```

**3. Ver cobertura de código:**
```bash
pytest tests/ --cov=src --cov-report=html
```
Relatório: `htmlcov/index.html`

## 📁 Estrutura do Projeto

```
Drone-Servicos_Cognitivos/
├── src/
│   ├── main.py                      # Ponto de entrada do sistema
│   ├── core/
│   │   ├── entities/
│   │   │   ├── drone.py            # Modelo do drone
│   │   │   └── vento.py            # Gerenciador de vento
│   │   ├── individuo.py            # Indivíduo do AG
│   │   ├── populacao.py            # População do AG
│   │   └── settings.py             # Configurações centralizadas
│   ├── algorithms/
│   │   ├── fitness.py              # Cálculo de fitness
│   │   └── genetico.py             # Algoritmo Genético
│   ├── models/
│   │   ├── coordenada.py           # Modelo de coordenada
│   │   └── trecho.py               # Modelo de trecho de voo
│   ├── simulation/
│   │   └── csv_exporter.py         # Exportação de resultados
│   └── utils_custom/
│       ├── calculos.py             # Funções matemáticas
│       └── file_handlers.py        # Manipulação de arquivos
├── data/
│   └── coordenadas.csv             # 374 coordenadas + base
├── tests/
│   ├── test_drone.py               # Testes do drone
│   ├── test_ga.py                  # Testes do AG
│   ├── test_pdf_specifications.py  # Testes das especificações
│   ├── test_user_requested.py      # Testes customizados
│   └── ...                         # 40 testes no total
├── outputs/
│   ├── flight_plan.csv
│   ├── resumo_execucao.csv
│   └── evolucao.png
├── requirements.txt
├── pytest.ini
└── README.md
```

## 🧬 Algoritmo Genético

### Parâmetros de Execução
- **População**: 50 indivíduos
- **Gerações**: 10
- **Taxa de Elite**: 10% (5 melhores preservados)
- **Taxa de Mutação**: 2% (adaptativa)
- **Taxa de Crossover**: 80%

### Operadores Genéticos
- **Crossover**: Order Crossover (OX)
- **Mutação**: Swap adaptativa
- **Seleção**: Torneio (elitismo garantido)
- **Otimização local**: 2-opt (1000 iterações)

### Função de Fitness
Maximiza a eficiência considerando:
- Tempo total de missão
- Número de recargas
- Custos operacionais
- Viabilidade da solução

## 📊 Resultados Típicos

```
✅ Solução otimizada:
   - Distância total: ~1600 km
   - Tempo total: ~1400 min (~23h)
   - Dias utilizados: 2-3
   - Pousos para recarga: 18-20
   - Custo total: R$ 1600-1760
   - Coordenadas visitadas: 375
```

## 📝 Formato de Saída

`flight_plan.csv` com colunas:
```
cep_origem, lat_origem, lon_origem, dia, hora_inicio, 
velocidade, cep_destino, lat_destino, lon_destino, 
pousou, hora_fim
```

## 🧪 Testes

**40 testes unitários (100% passando)**
- ✅ Testes de autonomia e velocidades
- ✅ Testes de efeito vetorial do vento
- ✅ Testes de custos e taxas
- ✅ Testes de integração do AG
- ✅ Validação completa das especificações do PDF

**Cobertura de código: 61%**

## 🔧 Desenvolvimento

### Executar em modo de desenvolvimento:
```bash
# Ambiente virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Executar sistema
python src/main.py

# Executar testes
pytest tests/ -v

# Cobertura
pytest tests/ --cov=src --cov-report=term-missing
```

## 👥 Autores

- Bernardo Rodrigues RA:2023100357 
- Enzo Berlesi RA:2023102306
- Henrique Bicudo RA:2023103607
- João Godoy RA:2023100923

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos - UNIBRASIL 2025