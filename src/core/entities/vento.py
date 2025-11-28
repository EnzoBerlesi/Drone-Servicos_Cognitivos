"""Previsão de vento (tabela estática reformatada internamente)."""
from ...utils_custom.calculos import cardinal_para_angulo


class GerenciadorVento:
    """Fornece vento (velocidade e ângulo) para dia/hora."""

    def __init__(self):
        self.previsao = self._carregar_previsao()

    def _carregar_previsao(self):
        # tabela compacta de exemplo (mantida igual)
        return {
            1: {'06h': {'velocidade': 17, 'direcao': 'ENE'}, '09h': {'velocidade': 18, 'direcao': 'E'}, '12h': {'velocidade': 19, 'direcao': 'E'}, '15h': {'velocidade': 19, 'direcao': 'E'}, '18h': {'velocidade': 20, 'direcao': 'E'}, '21h': {'velocidade': 20, 'direcao': 'E'}},
            2: {'06h': {'velocidade': 20, 'direcao': 'E'}, '09h': {'velocidade': 19, 'direcao': 'E'}, '12h': {'velocidade': 16, 'direcao': 'E'}, '15h': {'velocidade': 19, 'direcao': 'E'}, '18h': {'velocidade': 21, 'direcao': 'E'}, '21h': {'velocidade': 21, 'direcao': 'E'}},
            3: {'06h': {'velocidade': 15, 'direcao': 'ENE'}, '09h': {'velocidade': 17, 'direcao': 'NE'}, '12h': {'velocidade': 8, 'direcao': 'NE'}, '15h': {'velocidade': 20, 'direcao': 'E'}, '18h': {'velocidade': 16, 'direcao': 'E'}, '21h': {'velocidade': 15, 'direcao': 'ENE'}},
            4: {'06h': {'velocidade': 8, 'direcao': 'ENE'}, '09h': {'velocidade': 11, 'direcao': 'ENE'}, '12h': {'velocidade': 8, 'direcao': 'NE'}, '15h': {'velocidade': 11, 'direcao': 'E'}, '18h': {'velocidade': 11, 'direcao': 'E'}, '21h': {'velocidade': 11, 'direcao': 'E'}},
            5: {'06h': {'velocidade': 3, 'direcao': 'WSW'}, '09h': {'velocidade': 3, 'direcao': 'WSW'}, '12h': {'velocidade': 7, 'direcao': 'WSW'}, '15h': {'velocidade': 7, 'direcao': 'SSW'}, '18h': {'velocidade': 10, 'direcao': 'E'}, '21h': {'velocidade': 11, 'direcao': 'E'}},
            6: {'06h': {'velocidade': 4, 'direcao': 'NE'}, '09h': {'velocidade': 5, 'direcao': 'ENE'}, '12h': {'velocidade': 4, 'direcao': 'NE'}, '15h': {'velocidade': 8, 'direcao': 'E'}, '18h': {'velocidade': 15, 'direcao': 'E'}, '21h': {'velocidade': 15, 'direcao': 'E'}},
            7: {'06h': {'velocidade': 6, 'direcao': 'NE'}, '09h': {'velocidade': 8, 'direcao': 'NE'}, '12h': {'velocidade': 14, 'direcao': 'NE'}, '15h': {'velocidade': 16, 'direcao': 'NE'}, '18h': {'velocidade': 13, 'direcao': 'ENE'}, '21h': {'velocidade': 10, 'direcao': 'ENE'}}
        }

    def get_vento(self, dia, hora_minutos):
        if dia not in self.previsao:
            return {'velocidade': 0, 'direcao': 'N', 'angulo': 0}

        hora_str = self._hora_para_faixa(hora_minutos)
        vento_info = self.previsao[dia].get(hora_str, {'velocidade': 0, 'direcao': 'N'})

        angulo_origem = cardinal_para_angulo(vento_info['direcao'])
        angulo_destino = (angulo_origem + 180) % 360

        return {'velocidade': vento_info['velocidade'], 'direcao': vento_info['direcao'], 'angulo': angulo_destino}

    def _hora_para_faixa(self, hora_minutos):
        horas = hora_minutos // 60
        if horas < 9:
            return '06h'
        if horas < 12:
            return '09h'
        if horas < 15:
            return '12h'
        if horas < 18:
            return '15h'
        if horas < 21:
            return '18h'
        return '21h'

    def __repr__(self):
        return f"GerenciadorVento({len(self.previsao)} dias de previsão)"
