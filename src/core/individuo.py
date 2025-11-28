"""
Modelo de Indivíduo (solução/rota completa) para o algoritmo genético
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
        """Inicializa todas as métricas do indivíduo"""
        self.trechos = []
        self.fitness = float('inf')
        self.viabilidade = True
        self.penalidades = 0
        
        # Métricas operacionais
        self.distancia_total = 0
        self.tempo_total = 0
        self.custo_total = 0
        self.numero_pousos = 0
        self.pousos_taxa_tarde = 0
        self.dias_utilizados = 0
    
    def _inicializar_rastreamento(self):
        """Inicializa estruturas de rastreamento de eventos"""
        self.alertas = []
        self.pousos_atrasados = []
        self.lista_recargas = []
        self.minutos_totais_desde_inicio = None
    
    def validar_estrutura(self):
        """Valida restrições estruturais da rota"""
        # Verificar início no Unibrasil
        if len(self.coordenadas) < 2 or not self.coordenadas[0].eh_unibrasil():
            self.marcar_invalida(10000)
        
        # Verificar fim no Unibrasil  
        if not self.coordenadas[-1].eh_unibrasil():
            self.marcar_invalida(10000)
        
        # Verificar duplicações (exceto Unibrasil)
        self._verificar_duplicacoes()
    
    def marcar_invalida(self, penalidade):
        """Marca solução como inviável com penalidade"""
        self.viabilidade = False
        self.penalidades += penalidade
    
    def _verificar_duplicacoes(self):
        """Verifica se há CEPs duplicados na rota"""
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
        
        # Reiniciar estado
        self._inicializar_metricas()
        self._inicializar_rastreamento()
        
        # Estado inicial da missão
        ctx = self._criar_contexto_inicial()
        
        # Processar cada segmento da rota
        for idx in range(len(self.coordenadas) - 1):
            origem = self.coordenadas[idx]
            destino = self.coordenadas[idx + 1]
            
            # Gerenciar transições de dia
            ctx = self._gerenciar_dia(ctx, origem, verbose)
            
            # Selecionar velocidade ideal
            velocidade = self._selecionar_velocidade(
                origem, destino, ctx
            )
            
            # Obter condições de vento
            vento = self.gerenciador_vento.get_vento(
                ctx['dia'], ctx['hora_minutos']
            )
            
            # Construir trecho
            trecho = Trecho(
                origem, destino, velocidade,
                ctx['dia'], ctx['hora_minutos'],
                vento['velocidade'], vento['angulo']
            )
            
            # Processar necessidade de recarga
            if self._necessita_recarga(trecho, ctx['bateria']):
                ctx = self._executar_recarga(
                    origem, ctx, verbose
                )
            
            # Executar voo
            ctx = self._executar_voo(trecho, ctx)
            
            # Verificar limites
            if not self._verificar_limites(ctx, verbose):
                return
        
        # Finalizar simulação
        self._finalizar_simulacao(ctx)
    
    def _inicializar_metricas(self):
        """Limpa métricas da simulação anterior"""
        self.trechos = []
        self.distancia_total = 0
        self.tempo_total = 0
        self.custo_total = 0
        self.numero_pousos = 0
        self.pousos_taxa_tarde = 0
        self.dias_utilizados = 0
        
        # Não resetar viabilidade e penalidades se já existirem
        if not hasattr(self, 'viabilidade'):
            self.viabilidade = True
        if not hasattr(self, 'penalidades'):
            self.penalidades = 0
        if not hasattr(self, 'fitness'):
            self.fitness = float('inf')
    
    def _inicializar_rastreamento(self):
        """Limpa rastreamento de eventos"""
        self.alertas = []
        self.pousos_atrasados = []
        self.lista_recargas = []
        
        # Não resetar se já existir
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
        velocidades = sorted(
            self.drone.get_velocidades_validas(),
            reverse=True
        )
        
        vento = self.gerenciador_vento.get_vento(ctx['dia'], ctx['hora_minutos'])
        
        melhor_v = None
        menor_custo = float('inf')
        
        # Parâmetros da heurística
        alpha = Config.HEURISTICA_ALPHA
        beta = self._calcular_beta_dinamico(ctx['bateria'])
        
        for v in velocidades:
            try:
                trecho_teste = Trecho(
                    origem, destino, v, ctx['dia'], ctx['hora_minutos'],
                    vento['velocidade'], vento['angulo']
                )
            except:
                continue
            
            # Pular velocidades que exigem recarga
            if self._necessita_recarga(trecho_teste, ctx['bateria']):
                continue
            
            # Calcular custo normalizado
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
            # Quanto menos bateria, maior o peso do consumo
            return Config.HEURISTICA_BETA * (1.0 - nivel)
        except:
            return Config.HEURISTICA_BETA
    
    def _calcular_consumo_percentual(self, trecho, velocidade):
        """Calcula consumo como porcentagem da autonomia total"""
        try:
            autonomia_total = self.drone.calcular_autonomia(velocidade)
            return (trecho.consumo_bateria / autonomia_total) * 100.0
        except:
            return float('inf')
    
    def _necessita_recarga(self, trecho, bateria):
        """Verifica se bateria é insuficiente para o trecho"""
        reserva = getattr(Config, 'BATTERY_RESERVE_SECONDS', 0)
        return (trecho.consumo_bateria + reserva) > bateria
    
    def _executar_recarga(self, local, ctx, verbose):
        """Processa uma recarga de bateria"""
        # Determinar se há taxa de atraso
        tem_taxa = self._verificar_taxa_atraso(ctx['minutos_abs'])
        
        # Recarregar
        self.drone.recarregar()
        ctx['bateria'] = self.drone.bateria_atual
        self.numero_pousos += 1
        
        if tem_taxa:
            self.pousos_taxa_tarde += 1
        
        # Registrar detalhes
        dia, hora = abs_to_day_and_minuto(ctx['minutos_abs'])
        self.lista_recargas.append((dia, hora, local.cep, tem_taxa))
        
        # Registrar alertas
        self._registrar_alerta_recarga(dia, hora, local.cep, tem_taxa, verbose)
        
        # Avançar tempo pela recarga
        ctx['minutos_abs'] += Config.TEMPO_RECARGA
        ctx['hora_minutos'] = (Config.HORA_INICIO + ctx['minutos_abs']) % (24 * 60)
        
        # Verificar se precisa dormir após recarga
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
        
        # Pular para próximo dia
        ctx['minutos_abs'] += (24 * 60) - ctx['hora_minutos'] + Config.HORA_INICIO
        ctx['dia'] += 1
        ctx['hora_minutos'] = Config.HORA_INICIO
        
        return ctx
    
    def _executar_voo(self, trecho, ctx):
        """Executa um voo e atualiza estado"""
        # Consumir bateria
        ctx['bateria'] -= trecho.consumo_bateria
        
        # Avançar tempo de voo
        minutos_voo = trecho.tempo_voo_segundos // 60
        ctx['minutos_abs'] += minutos_voo
        ctx['hora_minutos'] = (Config.HORA_INICIO + ctx['minutos_abs']) % (24 * 60)
        
        # Pausa para fotos (72s ≈ 1 min)
        ctx['minutos_abs'] += 1
        ctx['hora_minutos'] = (Config.HORA_INICIO + ctx['minutos_abs']) % (24 * 60)
        
        # Atualizar métricas
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
            
            # Aplicar política de penalidade
            if getattr(Config, 'HARD_DIAS_MAX', False):
                self.viabilidade = False
                self.penalidades += 100000
                return False
            else:
                dias_extras = dias_corridos - Config.DIAS_MAXIMOS
                penalidade_dia = getattr(Config, 'PENALIDADE_POR_DIA_EXCEDIDO', 10000)
                self.penalidades += penalidade_dia * dias_extras
        
        # Penalizar voos fora de horário
        if ctx['hora_minutos'] > Config.HORA_FIM:
            self.penalidades += 1000
        
        return True
    
    def _finalizar_simulacao(self, ctx):
        """Finaliza simulação e calcula métricas finais"""
        # Calcular custo total
        custo_tempo = self.tempo_total * Config.CUSTO_POR_MINUTO
        custo_recargas = self.numero_pousos * Config.CUSTO_RECARGA
        custo_taxa = self.pousos_taxa_tarde * Config.CUSTO_TAXA_TARDE
        self.custo_total = custo_tempo + custo_recargas + custo_taxa
        
        # Calcular dias utilizados
        dias_passados = (Config.HORA_INICIO + ctx['minutos_abs']) // (24 * 60)
        self.dias_utilizados = int(dias_passados) + 1
        
        # Guardar tempo total
        self.minutos_totais_desde_inicio = int(ctx['minutos_abs'])
        
        # Atualizar contador de pousos
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
