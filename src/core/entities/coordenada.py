"""
Modelo de Coordenada geográfica
"""

class Coordenada:
    """Representa uma coordenada geográfica com CEP associado"""
    
    def __init__(self, cep, latitude, longitude):
        self.cep = str(cep)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
    
    def eh_unibrasil(self):
        """Verifica se é o CEP do Unibrasil (ponto inicial/final)"""
        return self.cep == "82821020"
    
    def __repr__(self):
        return f"Coordenada(CEP={self.cep}, lat={self.latitude:.4f}, lon={self.longitude:.4f})"
    
    def __eq__(self, other):
        if not isinstance(other, Coordenada):
            return False
        return self.cep == other.cep
    
    def __hash__(self):
        return hash(self.cep)
