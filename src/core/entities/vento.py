"""
Modelo de gerenciamento de informações de vento
"""
from ...utils_custom.calculos import cardinal_para_angulo

class GerenciadorVento:
    """Gerencia previsão de vento para os 7 dias da missão"""
    
    def __init__(self):
        self.previsao = self._carregar_previsao()
    
    def _carregar_previsao(self):
        """Carrega tabela de previsão de vento conforme PDF"""
        return {
            1: {  # Dia 1
                '06h': {'velocidade': 17, 'direcao': 'ENE'},
                '09h': {'velocidade': 18, 'direcao': 'E'},
                '12h': {'velocidade': 19, 'direcao': 'E'},
                '15h': {'velocidade': 19, 'direcao': 'E'},
                '18h': {'velocidade': 20, 'direcao': 'E'},
                '21h': {'velocidade': 20, 'direcao': 'E'}
            },
            2: {  # Dia 2
                '06h': {'velocidade': 20, 'direcao': 'E'},
                '09h': {'velocidade': 19, 'direcao': 'E'},
                '12h': {'velocidade': 16, 'direcao': 'E'},
                '15h': {'velocidade': 19, 'direcao': 'E'},
                '18h': {'velocidade': 21, 'direcao': 'E'},
                '21h': {'velocidade': 21, 'direcao': 'E'}
            },
            3: {  # Dia 3
                '06h': {'velocidade': 15, 'direcao': 'ENE'},
                '09h': {'velocidade': 17, 'direcao': 'NE'},
                '12h': {'velocidade': 8, 'direcao': 'NE'},
                '15h': {'velocidade': 20, 'direcao': 'E'},
                '18h': {'velocidade': 16, 'direcao': 'E'},
                '21h': {'velocidade': 15, 'direcao': 'ENE'}
            },
            4: {  # Dia 4
                '06h': {'velocidade': 8, 'direcao': 'ENE'},
                '09h': {'velocidade': 11, 'direcao': 'ENE'},
                '12h': {'velocidade': 8, 'direcao': 'NE'},
                '15h': {'velocidade': 11, 'direcao': 'E'},
                '18h': {'velocidade': 11, 'direcao': 'E'},
                '21h': {'velocidade': 11, 'direcao': 'E'}
            },
            5: {  # Dia 5
                '06h': {'velocidade': 3, 'direcao': 'WSW'},
                '09h': {'velocidade': 3, 'direcao': 'WSW'},
                '12h': {'velocidade': 7, 'direcao': 'WSW'},
                '15h': {'velocidade': 7, 'direcao': 'SSW'},
                '18h': {'velocidade': 10, 'direcao': 'E'},
                '21h': {'velocidade': 11, 'direcao': 'E'}
            },
            6: {  # Dia 6
                '06h': {'velocidade': 4, 'direcao': 'NE'},
                '09h': {'velocidade': 5, 'direcao': 'ENE'},
                '12h': {'velocidade': 4, 'direcao': 'NE'},
                '15h': {'velocidade': 8, 'direcao': 'E'},
                '18h': {'velocidade': 15, 'direcao': 'E'},
                '21h': {'velocidade': 15, 'direcao': 'E'}
            },
            7: {  # Dia 7
                '06h': {'velocidade': 6, 'direcao': 'NE'},
                '09h': {'velocidade': 8, 'direcao': 'NE'},
                '12h': {'velocidade': 14, 'direcao': 'NE'},
                '15h': {'velocidade': 16, 'direcao': 'NE'},
                '18h': {'velocidade': 13, 'direcao': 'ENE'},
                '21h': {'velocidade': 10, 'direcao': 'ENE'}
            }
        }
    
    def get_vento(self, dia, hora_minutos):
        """
        Retorna informações de vento para dia e hora específicos.
        
        Args:
            dia: Número do dia (1-7)
            hora_minutos: Minutos desde meia-noite
        
        Returns:
            dict: {'velocidade': float, 'direcao': str, 'angulo': float}
        """
        if dia not in self.previsao:
            return {'velocidade': 0, 'direcao': 'N', 'angulo': 0}
        
        hora_str = self._hora_para_faixa(hora_minutos)
        vento_info = self.previsao[dia].get(hora_str, {'velocidade': 0, 'direcao': 'N'})
        
        # Converter direção cardinal para ângulo
        # Nota: a direção representa DE ONDE o vento vem (convenção meteorológica)
        # Para vetor velocidade, adicionamos 180° para direção PARA ONDE sopra
        angulo_origem = cardinal_para_angulo(vento_info['direcao'])
        angulo_destino = (angulo_origem + 180) % 360
        
        return {
            'velocidade': vento_info['velocidade'],
            'direcao': vento_info['direcao'],
            'angulo': angulo_destino
        }
    
    def _hora_para_faixa(self, hora_minutos):
        """Converte minutos do dia para faixa de horário da previsão"""
        horas = hora_minutos // 60
        if horas < 9:
            return '06h'
        elif horas < 12:
            return '09h'
        elif horas < 15:
            return '12h'
        elif horas < 18:
            return '15h'
        elif horas < 21:
            return '18h'
        else:
            return '21h'
    
    def __repr__(self):
        return f"GerenciadorVento({len(self.previsao)} dias de previsão)"
