"""Classe que encapsula autonomia e consumo do drone."""
from ..settings import Config


class Drone:
    """Modelo simples do drone (autonomia, carregamento e velocidades)."""

    def __init__(self):
        self.config = Config
        self.velocidade_padrao = Config.VELOCIDADE_MINIMA
        self.bateria_atual = self.calcular_autonomia(self.velocidade_padrao)
    
    def calcular_autonomia(self, velocidade):
        """Retorna autonomia estimada (segundos) para uma velocidade dada."""
        if not self.velocidade_valida(velocidade):
            raise ValueError(f"Velocidade {velocidade} km/h inválida")

        fator = (Config.VELOCIDADE_REFERENCIA / velocidade) ** 2
        autonomia = Config.AUTONOMIA_REFERENCIA * fator * Config.FATOR_CORRECAO
        return autonomia
    
    def velocidade_valida(self, velocidade):
        """Valida se velocidade atende restrições (múltiplo de 4 entre limites)."""
        return (Config.VELOCIDADE_MINIMA <= velocidade <= Config.VELOCIDADE_MAXIMA and velocidade % 4 == 0)
    
    def get_velocidades_validas(self):
        """Lista todas as velocidades permitidas pelo drone."""
        return list(range(Config.VELOCIDADE_MINIMA, Config.VELOCIDADE_MAXIMA + 1, 4))
    
    def consumir_bateria(self, tempo_voo_segundos):
        """Subtrai tempo (s) da bateria atual; retorna se ainda há carga."""
        self.bateria_atual -= tempo_voo_segundos
        return self.bateria_atual >= 0
    
    def recarregar(self):
        """Restaura bateria ao nível máximo para a velocidade padrão."""
        self.bateria_atual = self.calcular_autonomia(self.velocidade_padrao)
    
    def get_bateria_porcentagem(self):
        bateria_cheia = self.calcular_autonomia(self.velocidade_padrao)
        return (self.bateria_atual / bateria_cheia) * 100 if bateria_cheia > 0 else 0
    
    def __repr__(self):
        return f"Drone(bateria={self.get_bateria_porcentagem():.1f}%)"
