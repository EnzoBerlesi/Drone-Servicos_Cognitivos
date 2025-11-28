"""
Modelo de Trecho entre duas coordenadas
"""
from ..settings import Config
from ...utils_custom.calculos import (
    distancia_haversine, 
    calcular_direcao,
    calcular_velocidade_efetiva
)

class Trecho:
    """Representa um trecho de voo entre duas coordenadas"""
    
    def __init__(self, origem, destino, velocidade, dia, hora_partida, vento_velocidade, vento_angulo):
        """
        Cria um trecho de voo com todos os cálculos automáticos.
        
        Args:
            origem: Objeto Coordenada de partida
            destino: Objeto Coordenada de chegada
            velocidade: Velocidade do drone em km/h
            dia: Dia do voo (1-7)
            hora_partida: Minutos desde meia-noite
            vento_velocidade: Velocidade do vento em km/h
            vento_angulo: Ângulo do vento em graus (PARA ONDE sopra)
        """
        self.origem = origem
        self.destino = destino
        self.velocidade = int(velocidade)
        self.dia = dia
        self.hora_partida = int(hora_partida)
        self.vento_velocidade = vento_velocidade
        self.vento_angulo = vento_angulo
        
        # Calcular métricas automaticamente
        self._calcular_metricas()
    
    def _calcular_metricas(self):
        """Calcula distância, direção, velocidade efetiva e tempo de voo"""
        # Distância em km
        self.distancia = distancia_haversine(
            self.origem.latitude, self.origem.longitude,
            self.destino.latitude, self.destino.longitude
        )
        
        # Direção do voo em graus
        self.direcao_voo = calcular_direcao(
            self.origem.latitude, self.origem.longitude,
            self.destino.latitude, self.destino.longitude
        )
        
        # Velocidade efetiva considerando vento (soma vetorial)
        self.velocidade_efetiva = calcular_velocidade_efetiva(
            self.velocidade, 
            self.direcao_voo,
            self.vento_velocidade, 
            self.vento_angulo
        )
        
        # Tempo de voo em segundos (arredondado para cima)
        tempo_horas = self.distancia / max(0.001, self.velocidade_efetiva)
        self.tempo_voo_segundos = int(tempo_horas * 3600) + 1
        
        # Consumo de bateria = tempo de voo
        self.consumo_bateria = self.tempo_voo_segundos
        
        # Custo será calculado durante simulação
        self.custo = 0
    
    def get_hora_chegada(self):
        """
        Retorna hora de chegada em minutos desde meia-noite.
        
        Returns:
            int: Minutos desde 00:00
        """
        return self.hora_partida + (self.tempo_voo_segundos // 60)
    
    def precisa_recarregar(self, bateria_atual):
        """
        Verifica se é necessário recarregar antes deste trecho.
        Considera reserva de segurança configurada.
        
        Args:
            bateria_atual: Bateria disponível em segundos
        
        Returns:
            bool: True se precisa recarregar
        """
        reserva = getattr(Config, 'BATTERY_RESERVE_SECONDS', 0)
        return (self.consumo_bateria + reserva) > bateria_atual
    
    def __repr__(self):
        return (f"Trecho({self.origem.cep}→{self.destino.cep}: "
                f"{self.distancia:.1f}km, v={self.velocidade}km/h, "
                f"t={self.tempo_voo_segundos}s)")
