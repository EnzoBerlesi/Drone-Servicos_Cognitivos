"""
Exportador de resultados em formato CSV
"""
import os
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from ..core.settings import Config
from ..utils_custom.time_utils import formatar_hora_csv

class CSVExporter:
    """Exporta resultados da otimização em arquivos CSV"""
    
    def __init__(self, diretorio_saida="outputs"):
        """
        Inicializa exportador.
        
        Args:
            diretorio_saida: Diretório onde salvar os arquivos
        """
        self.diretorio_saida = diretorio_saida
        self._criar_diretorio()
    
    def _criar_diretorio(self):
        """Cria diretório de saída se não existir"""
        if not os.path.exists(self.diretorio_saida):
            os.makedirs(self.diretorio_saida)
    
    def exportar_rota_completa(self, individuo):
        """
        Exporta rota otimizada para CSV.
        
        Args:
            individuo: Melhor indivíduo encontrado
        
        Returns:
            str: Caminho do arquivo criado
        """
        caminho_completo = os.path.join(self.diretorio_saida, "flight_plan.csv")
        
        # Criar conjunto de recargas para identificar pousos
        recargas = set(
            (dia, cep, hora) 
            for (dia, hora, cep, taxa) in getattr(individuo, 'lista_recargas', [])
        )
        
        with open(caminho_completo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Cabeçalho conforme especificação
            writer.writerow([
                'CEP inicial', 'Latitude inicial', 'Longitude inicial',
                'Dia do vôo', 'Hora inicial', 'Velocidade',
                'CEP final', 'Latitude final', 'Longitude final',
                'Pouso', 'Hora final'
            ])
            
            # Escrever cada trecho
            for trecho in individuo.trechos:
                # Verificar se houve pouso neste trecho (recarga)
                matched = any(
                    r_cep == trecho.origem.cep and 
                    r_dia == trecho.dia and 
                    abs(r_hora - trecho.hora_partida) <= 3
                    for r_dia, r_cep, r_hora in recargas
                )
                pouso = "SIM" if matched else "NÃO"
                
                writer.writerow([
                    trecho.origem.cep,
                    f"{trecho.origem.latitude:.6f}",
                    f"{trecho.origem.longitude:.6f}",
                    trecho.dia,
                    formatar_hora_csv(trecho.hora_partida),
                    trecho.velocidade,
                    trecho.destino.cep,
                    f"{trecho.destino.latitude:.6f}",
                    f"{trecho.destino.longitude:.6f}",
                    pouso,
                    formatar_hora_csv(trecho.get_hora_chegada())
                ])
        
        print(f"OK Plano de voo salvo: {caminho_completo}")
        return caminho_completo
    
    def exportar_resumo(self, individuo, historico_metricas):
        """
        Exporta resumo da execução.
        
        Args:
            individuo: Melhor indivíduo
            historico_metricas: Histórico de métricas das gerações
        
        Returns:
            str: Caminho do arquivo criado
        """
        caminho_completo = os.path.join(self.diretorio_saida, "resumo_execucao.csv")
        
        with open(caminho_completo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['PARÂMETRO', 'VALOR'])
            
            # Informações básicas
            writer.writerow(['Data execução', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(['Total pontos', len(individuo.coordenadas)])
            writer.writerow(['Distância total (km)', f"{individuo.distancia_total:.2f}"])
            
            # Tempo total
            minutos_missao = getattr(individuo, 'minutos_totais_desde_inicio', None)
            if minutos_missao is None:
                num_recargas = len(getattr(individuo, 'lista_recargas', []))
                tempo_recargas_min = num_recargas * getattr(Config, 'TEMPO_RECARGA', 0)
                num_trechos = len(getattr(individuo, 'trechos', []))
                tempo_parada_min = (num_trechos * getattr(Config, 'TEMPO_PARADA', 0)) / 60.0
                minutos_missao = individuo.tempo_total + tempo_recargas_min + tempo_parada_min
            
            writer.writerow(['Tempo total missão (min)', f"{float(minutos_missao):.2f}"])
            
            # Custos
            custo_real = getattr(individuo, 'custo_total', 0)
            if custo_real > 0:
                writer.writerow(['Custo total (R$)', f"{custo_real:.2f}"])
            
            # Métricas operacionais
            num_recargas = len(getattr(individuo, 'lista_recargas', []))
            writer.writerow(['Número de pousos', num_recargas])
            writer.writerow(['Coordenadas visitadas', len(getattr(individuo, 'coordenadas', []))])
            writer.writerow(['Dias utilizados', individuo.dias_utilizados])
            writer.writerow(['Fitness final', f"{individuo.fitness:.2f}"])
            writer.writerow(['Viabilidade', 'SIM' if individuo.viabilidade else 'NÃO'])
            writer.writerow(['Penalidades totais', f"{getattr(individuo, 'penalidades', 0):.2f}"])
            writer.writerow(['Pousos taxa tarde', getattr(individuo, 'pousos_taxa_tarde', 0)])
            
            # Configurações utilizadas
            autonomia_segundos = individuo.drone.calcular_autonomia(36)
            autonomia_minutos = autonomia_segundos / 60.0
            writer.writerow(['Autonomia drone (min)', f"{autonomia_minutos:.1f}"])
            
            velocidade_media = 0
            if individuo.tempo_total > 0:
                velocidade_media = (individuo.distancia_total / (individuo.tempo_total / 60.0))
            writer.writerow(['Velocidade média (km/h)', f"{velocidade_media:.1f}"])
            
            # Alertas
            alertas_str = '; '.join(getattr(individuo, 'alertas', []))
            if alertas_str:
                writer.writerow(['Alertas', alertas_str])
        
        print(f"OK Resumo salvo: {caminho_completo}")
        
        # Tentar gerar gráfico de evolução
        if historico_metricas:
            self._gerar_grafico_evolucao(historico_metricas)
        
        return caminho_completo
    
    def _gerar_grafico_evolucao(self, historico_metricas):
        """Gera gráfico PNG da evolução do fitness"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            
            # Configurar estilo moderno
            plt.style.use('seaborn-v0_8-darkgrid')
            
            # Extrair dados do histórico
            geracoes = list(range(1, len(historico_metricas) + 1))
            melhor_fitness = [m.get('melhor_fitness', float('nan')) for m in historico_metricas]
            
            # Criar figura com fundo personalizado
            fig, ax = plt.subplots(1, 1, figsize=(12, 6))
            fig.patch.set_facecolor('#f8f9fa')
            ax.set_facecolor('#ffffff')
            
            # Plotar linha principal com gradiente
            line = ax.plot(geracoes, melhor_fitness, 
                          color='#2563eb', linewidth=2.5, 
                          marker='o', markersize=8, 
                          markerfacecolor='#3b82f6',
                          markeredgecolor='#1e40af',
                          markeredgewidth=1.5,
                          label='Evolução do Fitness',
                          zorder=3)
            
            # Adicionar área preenchida abaixo da linha
            ax.fill_between(geracoes, melhor_fitness, 
                           min(melhor_fitness) - (max(melhor_fitness) - min(melhor_fitness)) * 0.1,
                           alpha=0.2, color='#3b82f6', zorder=1)
            
            # Destacar melhor e pior geração
            melhor_idx = melhor_fitness.index(min(melhor_fitness))
            pior_idx = melhor_fitness.index(max(melhor_fitness))
            
            ax.scatter(geracoes[melhor_idx], melhor_fitness[melhor_idx], 
                      s=200, color='#10b981', marker='*', 
                      edgecolors='#065f46', linewidth=2,
                      label='Melhor solução', zorder=4)
            
            ax.scatter(geracoes[pior_idx], melhor_fitness[pior_idx], 
                      s=150, color='#ef4444', marker='v',
                      edgecolors='#991b1b', linewidth=1.5,
                      label='Pior solução', zorder=4)
            
            # Configurar eixos e labels
            ax.set_ylabel('Fitness (menor = melhor)', fontsize=12, fontweight='bold', color='#1f2937')
            ax.set_xlabel('Geração', fontsize=12, fontweight='bold', color='#1f2937')
            ax.set_title('Otimização por Algoritmo Genético + 2-opt\nUnibrasil Surveyor - Drone Route Optimizer',
                        fontsize=14, fontweight='bold', color='#111827', pad=20)
            
            # Grid mais sutil
            ax.grid(True, linestyle='--', alpha=0.3, color='#9ca3af', linewidth=0.8)
            ax.set_axisbelow(True)
            
            # Configurar ticks
            ax.tick_params(colors='#374151', which='both')
            
            # Adicionar legenda com estilo
            legend = ax.legend(loc='upper right', frameon=True, shadow=True,
                              fancybox=True, framealpha=0.95, fontsize=10)
            legend.get_frame().set_facecolor('#f3f4f6')
            legend.get_frame().set_edgecolor('#d1d5db')
            
            # Adicionar caixa de estatísticas
            stats_text = f'Melhoria: {((max(melhor_fitness) - min(melhor_fitness)) / max(melhor_fitness) * 100):.1f}%\n'
            stats_text += f'Fitness inicial: {melhor_fitness[0]:.2f}\n'
            stats_text += f'Fitness final: {melhor_fitness[-1]:.2f}'
            
            props = dict(boxstyle='round', facecolor='#fef3c7', alpha=0.8, edgecolor='#f59e0b', linewidth=2)
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props, family='monospace')
            
            plt.tight_layout()
            
            # Salvar gráfico
            caminho_fig = os.path.join(self.diretorio_saida, 'evolucao.png')
            plt.savefig(caminho_fig, dpi=150, bbox_inches='tight', facecolor='#f8f9fa')
            plt.close(fig)
            
            print(f"OK Grafico de evolucao salvo: {caminho_fig}")
            
        except ImportError:
            print("   AVISO: matplotlib nao encontrado - instale com 'pip install matplotlib'")
        except Exception as e:
            print(f"   AVISO: Erro ao gerar grafico: {e}")
    
    def gerar_mapa_rota(self, individuo):
        """
        Gera visualização da rota otimizada no mapa de Curitiba.
        
        Args:
            individuo: Melhor indivíduo encontrado
        
        Returns:
            str: Caminho do arquivo criado
        """
        try:
            # Coletar coordenadas da rota
            lats = []
            lons = []
            
            for trecho in individuo.trechos:
                lats.append(trecho.origem.latitude)
                lons.append(trecho.origem.longitude)
            
            # Adicionar última coordenada (destino final)
            if individuo.trechos:
                ultimo = individuo.trechos[-1]
                lats.append(ultimo.destino.latitude)
                lons.append(ultimo.destino.longitude)
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(14, 11))
            
            # Plotar rota completa (azul)
            ax.plot(lons, lats, 'o-', color='#3b82f6', markersize=5, 
                   linewidth=1.2, alpha=0.7, label='Rota otimizada', zorder=2)
            
            # Destacar Unibrasil (vermelho) - início e fim
            if lons and lats:
                ax.plot(lons[0], lats[0], 'o', color='#ef4444', markersize=18, 
                       label='Unibrasil (início/fim)', zorder=10, 
                       markeredgecolor='white', markeredgewidth=2)
            
            # Configurar eixos
            ax.set_xlabel('Longitude', fontsize=13, fontweight='bold')
            ax.set_ylabel('Latitude', fontsize=13, fontweight='bold')
            
            # Título com informações principais
            num_coords = len(individuo.coordenadas) if hasattr(individuo, 'coordenadas') else len(individuo.trechos) + 1
            titulo = (f'Rota Otimizada - {num_coords} CEPs em Curitiba\n'
                     f'Distância Total: {individuo.distancia_total:.2f} km | '
                     f'Tempo: {individuo.tempo_total/60:.0f} min | '
                     f'Dias: {individuo.dias_utilizados} | '
                     f'Recargas: {len(individuo.lista_recargas)} | '
                     f'Custo: R$ {individuo.custo_total:.2f}')
            ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
            
            # Grid e estilo
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax.set_facecolor('#f8f9fa')
            fig.patch.set_facecolor('white')
            
            # Legenda
            ax.legend(loc='upper right', fontsize=11, framealpha=0.95, 
                     edgecolor='gray', fancybox=True, shadow=True)
            
            # Ajustar limites para dar margem
            if lons and lats:
                lon_margin = (max(lons) - min(lons)) * 0.05
                lat_margin = (max(lats) - min(lats)) * 0.05
                ax.set_xlim(min(lons) - lon_margin, max(lons) + lon_margin)
                ax.set_ylim(min(lats) - lat_margin, max(lats) + lat_margin)
            
            plt.tight_layout()
            
            # Salvar
            caminho_mapa = os.path.join(self.diretorio_saida, 'mapa_rota.png')
            plt.savefig(caminho_mapa, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            print(f"OK Mapa da rota salvo: {caminho_mapa}")
            return caminho_mapa
            
        except ImportError:
            print("   AVISO: matplotlib nao encontrado - instale com 'pip install matplotlib'")
            return None
        except Exception as e:
            print(f"   AVISO: Erro ao gerar mapa da rota: {e}")
            return None
