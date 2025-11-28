"""
Modelo de Drone com gestão de bateria e autonomia
"""
from ..settings import Config

class Drone:
    """Representa um drone com lógica de autonomia e consumo de bateria"""
    
    def __init__(self):
        self.config = Config
        self.velocidade_padrao = Config.VELOCIDADE_MINIMA  # 36 km/h
        self.bateria_atual = self.calcular_autonomia(self.velocidade_padrao)
    
    def calcular_autonomia(self, velocidade):
        """
        Calcula autonomia em segundos baseada na velocidade usando a fórmula:
        A(v) = A₀ * (v₀ / v)² * fator_correção
        
        Onde:
        - A₀ = AUTONOMIA_REFERENCIA (5000s em lab)
        - v₀ = VELOCIDADE_REFERENCIA (36 km/h)
        - v = velocidade atual
        - fator_correção = FATOR_CORRECAO (0.93 para Curitiba)
        
        Args:
            velocidade: Velocidade em km/h
        
        Returns:
            float: Autonomia em segundos
        """
        if not self.velocidade_valida(velocidade):
            raise ValueError(f"Velocidade {velocidade} km/h inválida")
        
        fator = (Config.VELOCIDADE_REFERENCIA / velocidade) ** 2
        autonomia = Config.AUTONOMIA_REFERENCIA * fator * Config.FATOR_CORRECAO
        return autonomia
    
    def velocidade_valida(self, velocidade):
        """
        Verifica se velocidade está dentro das especificações.
        
        Args:
            velocidade: Velocidade em km/h
        
        Returns:
            bool: True se válida (entre 36-96 km/h e múltiplo de 4)
        """
        return (
            Config.VELOCIDADE_MINIMA <= velocidade <= Config.VELOCIDADE_MAXIMA
            and velocidade % 4 == 0
        )
    
    def get_velocidades_validas(self):
        """
        Retorna lista de todas as velocidades válidas.
        
        Returns:
            list: Velocidades de 36 a 96 km/h em incrementos de 4
        """
        return list(range(
            Config.VELOCIDADE_MINIMA,
            Config.VELOCIDADE_MAXIMA + 1,
            4
        ))
    
    def consumir_bateria(self, tempo_voo_segundos):
        """
        Consome bateria baseado no tempo de voo.
        
        Args:
            tempo_voo_segundos: Tempo em segundos
        
        Returns:
            bool: True se ainda há bateria, False se acabou
        """
        self.bateria_atual -= tempo_voo_segundos
        return self.bateria_atual >= 0
    
    def recarregar(self):
        """Recarrega bateria completamente para velocidade padrão"""
        self.bateria_atual = self.calcular_autonomia(self.velocidade_padrao)
    
    def get_bateria_porcentagem(self):
        """
        Retorna porcentagem de bateria restante.
        
        Returns:
            float: Porcentagem (0-100)
        """
        bateria_cheia = self.calcular_autonomia(self.velocidade_padrao)
        return (self.bateria_atual / bateria_cheia) * 100 if bateria_cheia > 0 else 0
    
    def __repr__(self):
        return f"Drone(bateria={self.get_bateria_porcentagem():.1f}%)"
