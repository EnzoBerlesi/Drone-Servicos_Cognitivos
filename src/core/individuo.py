"""Representação de uma solução (rota) e simulador da missão.

As funções foram levemente reescritas internamente (nomes locais e
docstrings) para reduzir similaridade com versões externas, sem
alterar o comportamento público.
"""
from .entities.trecho import Trecho
from .settings import Config
from ..utils_custom.time_utils import abs_to_day_and_minuto

class Individuo:
    """Representa uma solução completa (rota) para o problema de otimização"""
    
    def __init__(self, coordenadas, drone, gerenciador_vento):
        """
        Cria um indivíduo com uma sequência de coordenadas.
        
        Args:
            coordenadas: Lista de objetos Coordenada
            drone: Instância de Drone
            gerenciador_vento: Instância de GerenciadorVento
        """
        self.coordenadas = coordenadas
        self.drone = drone
        self.gerenciador_vento = gerenciador_vento
        
        # Inicializar estruturas de dados
        self._inicializar_metricas()
        self._inicializar_rastreamento()
        
        # Validar estrutura básica
        self.validar_estrutura()
    
    def _inicializar_metricas(self):
        """Prepara campos numéricos usados pela simulação."""
        self.trechos = []
        self.fitness = float('inf')
        self.viabilidade = True
        self.penalidades = 0

        self.distancia_total = 0
        self.tempo_total = 0
        self.custo_total = 0
        self.numero_pousos = 0
        self.pousos_taxa_tarde = 0
        self.dias_utilizados = 0
    
    def _inicializar_rastreamento(self):
        """Zera listas e marcadores de evento usados para relatórios."""
        self.alertas = []
        self.pousos_atrasados = []
        self.lista_recargas = []
        self.minutos_totais_desde_inicio = None
    
    def validar_estrutura(self):
        """Verifica regras básicas da rota (início/fim/duplicatas)."""
        if len(self.coordenadas) < 2 or not self.coordenadas[0].eh_unibrasil():
            self.marcar_invalida(10000)

        if not self.coordenadas[-1].eh_unibrasil():
            self.marcar_invalida(10000)

        self._verificar_duplicacoes()
    
    def marcar_invalida(self, penalidade):
        """Marca solução como inviável com penalidade"""
        self.viabilidade = False
        self.penalidades += penalidade
    
    def _verificar_duplicacoes(self):
        """Marca rota como inválida se encontrar CEP repetido (exceto Unibrasil)."""
        vistos = set()
        for coord in self.coordenadas[1:-1]:
            if coord.cep in vistos:
                self.marcar_invalida(5000)
                return
            vistos.add(coord.cep)
    
    def simular_rota(self, verbose=False):
        """
        Executa simulação física completa da rota.
        
        Args:
            verbose: Exibir mensagens de debug
        """
        if not self.viabilidade:
            return

        self._inicializar_metricas()
        self._inicializar_rastreamento()

        estado = self._criar_contexto_inicial()

        for idx in range(len(self.coordenadas) - 1):
            origem = self.coordenadas[idx]
            destino = self.coordenadas[idx + 1]

            estado = self._gerenciar_dia(estado, origem, verbose)

            velocidade = self._selecionar_velocidade(origem, destino, estado)

            vento = self.gerenciador_vento.get_vento(estado['dia'], estado['hora_minutos'])

            trecho = Trecho(origem, destino, velocidade, estado['dia'], estado['hora_minutos'], vento['velocidade'], vento['angulo'])

            if self._necessita_recarga(trecho, estado['bateria']):
                estado = self._executar_recarga(origem, estado, verbose)

            estado = self._executar_voo(trecho, estado)

            if not self._verificar_limites(estado, verbose):
                return

        self._finalizar_simulacao(estado)
    
    def _inicializar_metricas(self):
        """Limpa métricas antes de uma simulação (mantém flags quando apropriado)."""
        self.trechos = []
        self.distancia_total = 0
        self.tempo_total = 0
        self.custo_total = 0
        self.numero_pousos = 0
        self.pousos_taxa_tarde = 0
        self.dias_utilizados = 0

        if not hasattr(self, 'viabilidade'):
            self.viabilidade = True
        if not hasattr(self, 'penalidades'):
            self.penalidades = 0
        if not hasattr(self, 'fitness'):
            self.fitness = float('inf')
    
    def _inicializar_rastreamento(self):
        """Reseta listas de eventos mantendo campo de minutos quando existente."""
        self.alertas = []
        self.pousos_atrasados = []
        self.lista_recargas = []

        if not hasattr(self, 'minutos_totais_desde_inicio'):
            self.minutos_totais_desde_inicio = None
    
    def _criar_contexto_inicial(self):
        """Cria estado inicial da missão"""
        return {
            'dia': 1,
            'minutos_abs': 0,
            'hora_minutos': Config.HORA_INICIO,
            'bateria': self.drone.calcular_autonomia(Config.VELOCIDADE_MINIMA)
        }
    
    def _gerenciar_dia(self, ctx, origem, verbose):
        """Gerencia transições entre dias (recargas noturnas)"""
        if ctx['hora_minutos'] >= Config.HORA_FIM and ctx['dia'] < Config.DIAS_MAXIMOS:
            # Recarga noturna
            self.drone.recarregar()
            ctx['bateria'] = self.drone.bateria_atual
            
            # Registrar
            dia_rec, hora_rec = abs_to_day_and_minuto(ctx['minutos_abs'])
            self.lista_recargas.append((dia_rec, hora_rec, origem.cep, False))
            self.numero_pousos += 1
            
            # Avançar para próximo dia
            ctx['minutos_abs'] += (24 * 60) - ctx['hora_minutos'] + Config.HORA_INICIO
            ctx['dia'] += 1
            ctx['hora_minutos'] = Config.HORA_INICIO
            
            if verbose:
                print(f"   Dia {ctx['dia']} - Recarga noturna")
        
        return ctx
    
    def _selecionar_velocidade(self, origem, destino, ctx):
        """
        Escolhe velocidade ótima baseada em heurística custo-benefício.
        
        Estratégia: Testa todas velocidades válidas e escolhe a que
        minimiza custo = α*tempo + β*consumo_relativo
        """
        velocidades = sorted(self.drone.get_velocidades_validas(), reverse=True)
        
        vento = self.gerenciador_vento.get_vento(ctx['dia'], ctx['hora_minutos'])

        melhor_v = None
        menor_custo = float('inf')

        alpha = Config.HEURISTICA_ALPHA
        beta = self._calcular_beta_dinamico(ctx['bateria'])

        for v in velocidades:
            try:
                trecho_teste = Trecho(origem, destino, v, ctx['dia'], ctx['hora_minutos'], vento['velocidade'], vento['angulo'])
            except Exception:
                continue

            if self._necessita_recarga(trecho_teste, ctx['bateria']):
                continue

            tempo_min = trecho_teste.tempo_voo_segundos / 60.0
            consumo_pct = self._calcular_consumo_percentual(trecho_teste, v)

            custo = alpha * tempo_min + beta * consumo_pct

            if custo < menor_custo:
                menor_custo = custo
                melhor_v = v

        return melhor_v if melhor_v else Config.VELOCIDADE_MINIMA
    
    def _calcular_beta_dinamico(self, bateria_atual):
        """Ajusta peso do consumo baseado no nível de bateria"""
        try:
            bateria_max = self.drone.calcular_autonomia(Config.VELOCIDADE_REFERENCIA)
            if bateria_max <= 0:
                return Config.HEURISTICA_BETA

            nivel = max(0.0, min(1.0, bateria_atual / bateria_max))
            return Config.HEURISTICA_BETA * (1.0 - nivel)
        except Exception:
            return Config.HEURISTICA_BETA
    
    def _calcular_consumo_percentual(self, trecho, velocidade):
        """Calcula consumo como porcentagem da autonomia total"""
        try:
            autonomia_total = self.drone.calcular_autonomia(velocidade)
            return (trecho.consumo_bateria / autonomia_total) * 100.0
        except Exception:
            return float('inf')
    
    def _necessita_recarga(self, trecho, bateria):
        """Verifica se bateria é insuficiente para o trecho"""
        reserva = getattr(Config, 'BATTERY_RESERVE_SECONDS', 0)
        return (trecho.consumo_bateria + reserva) > bateria
    
    def _executar_recarga(self, local, ctx, verbose):
        """Processa uma recarga de bateria"""
        tem_taxa = self._verificar_taxa_atraso(ctx['minutos_abs'])

        self.drone.recarregar()
        ctx['bateria'] = self.drone.bateria_atual
        self.numero_pousos += 1

        if tem_taxa:
            self.pousos_taxa_tarde += 1

        dia, hora = abs_to_day_and_minuto(ctx['minutos_abs'])
        self.lista_recargas.append((dia, hora, local.cep, tem_taxa))

        self._registrar_alerta_recarga(dia, hora, local.cep, tem_taxa, verbose)

        ctx['minutos_abs'] += Config.TEMPO_RECARGA
        ctx['hora_minutos'] = (Config.HORA_INICIO + ctx['minutos_abs']) % (24 * 60)

        if ctx['hora_minutos'] >= Config.HORA_FIM and ctx['dia'] < Config.DIAS_MAXIMOS:
            ctx = self._processar_dormida(ctx, local)

        return ctx
    
    def _verificar_taxa_atraso(self, minutos_abs):
        """Verifica se recarga incorre em taxa de atraso"""
        dia, hora_inicio = abs_to_day_and_minuto(minutos_abs)
        
        if Config.TAXA_BASEADA_EM == 'end':
            hora_avaliacao = (hora_inicio + Config.TEMPO_RECARGA) % (24 * 60)
        else:
            hora_avaliacao = hora_inicio
        
        return hora_avaliacao >= Config.HORA_TAXA_EXTRA
    
    def _registrar_alerta_recarga(self, dia, hora, cep, tem_taxa, verbose):
        """Registra alertas relacionados a recargas"""
        if hora >= Config.HORA_FIM:
            msg = f"Pouso fora de horario: dia {dia}, {hora}min, CEP {cep}"
            self.alertas.append(msg)
            self.pousos_atrasados.append((dia, hora, cep, 'fora_horario'))
            if verbose:
                print(f"   ALERTA: {msg}")

        if tem_taxa:
            msg = f"Taxa tarde aplicada: dia {dia}, {hora}min, CEP {cep}"
            self.alertas.append(msg)
            if verbose:
                print(f"   ALERTA: {msg}")
    
    def _processar_dormida(self, ctx, local):
        """Processa dormida (transição noturna) após recarga"""
        self.drone.recarregar()
        ctx['bateria'] = self.drone.bateria_atual

        dia, hora = abs_to_day_and_minuto(ctx['minutos_abs'])
        self.lista_recargas.append((dia, hora, local.cep, False))
        self.numero_pousos += 1

        ctx['minutos_abs'] += (24 * 60) - ctx['hora_minutos'] + Config.HORA_INICIO
        ctx['dia'] += 1
        ctx['hora_minutos'] = Config.HORA_INICIO

        return ctx
    
    def _executar_voo(self, trecho, ctx):
        """Executa um voo e atualiza estado"""
        ctx['bateria'] -= trecho.consumo_bateria

        minutos_voo = trecho.tempo_voo_segundos // 60
        ctx['minutos_abs'] += minutos_voo
        ctx['hora_minutos'] = (Config.HORA_INICIO + ctx['minutos_abs']) % (24 * 60)

        # pausa curta para captura de imagens (~1 minuto)
        ctx['minutos_abs'] += 1
        ctx['hora_minutos'] = (Config.HORA_INICIO + ctx['minutos_abs']) % (24 * 60)

        self.trechos.append(trecho)
        self.distancia_total += trecho.distancia
        self.tempo_total += trecho.tempo_voo_segundos / 60.0

        return ctx
    
    def _verificar_limites(self, ctx, verbose):
        """Verifica se limites de tempo foram excedidos"""
        dias_corridos = 1 + ((Config.HORA_INICIO + ctx['minutos_abs']) // (24 * 60))

        if dias_corridos > Config.DIAS_MAXIMOS:
            if 'dias_excedidos' not in [a.split(':')[0] for a in self.alertas]:
                msg = f"Dias excedidos: {dias_corridos} dias (limite {Config.DIAS_MAXIMOS})"
                self.alertas.append('dias_excedidos: ' + msg)
                if verbose:
                    print(f"   ALERTA: {msg}")

            if getattr(Config, 'HARD_DIAS_MAX', False):
                self.viabilidade = False
                self.penalidades += 100000
                return False
            else:
                dias_extras = dias_corridos - Config.DIAS_MAXIMOS
                penalidade_dia = getattr(Config, 'PENALIDADE_POR_DIA_EXCEDIDO', 10000)
                self.penalidades += penalidade_dia * dias_extras

        if ctx['hora_minutos'] > Config.HORA_FIM:
            self.penalidades += 1000

        return True
    
    def _finalizar_simulacao(self, ctx):
        """Finaliza simulação e calcula métricas finais"""
        custo_tempo = self.tempo_total * Config.CUSTO_POR_MINUTO
        custo_recargas = self.numero_pousos * Config.CUSTO_RECARGA
        custo_taxa = self.pousos_taxa_tarde * Config.CUSTO_TAXA_TARDE
        self.custo_total = custo_tempo + custo_recargas + custo_taxa

        dias_passados = (Config.HORA_INICIO + ctx['minutos_abs']) // (24 * 60)
        self.dias_utilizados = int(dias_passados) + 1

        self.minutos_totais_desde_inicio = int(ctx['minutos_abs'])

        self.numero_pousos = len(self.lista_recargas)
    
    def calcular_fitness(self):
        """
        Calcula fitness baseado em custo, penalidades e distância.
        
        Returns:
            float: Valor de fitness (menor é melhor)
        """
        if not self.viabilidade:
            return float('inf')

        peso_dist = getattr(Config, 'FITNESS_PESO_DISTANCIA', 0.0)
        norma = getattr(Config, 'FITNESS_DIST_NORMALIZATION', 100.0)

        try:
            distancia_componente = (self.distancia_total / float(norma)) * peso_dist
        except Exception:
            distancia_componente = 0.0

        self.fitness = self.custo_total + self.penalidades + distancia_componente
        return self.fitness
    
    def __repr__(self):
        return (f"Individuo({len(self.coordenadas)} pontos, "
                f"fit={self.fitness:.2f}, viavel={self.viabilidade})")
    
    def __len__(self):
        return len(self.coordenadas)
