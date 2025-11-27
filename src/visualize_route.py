"""
Script para visualizar a rota do drone em um gráfico
Gera um gráfico de dispersão mostrando os CEPs e a rota otimizada
"""
import matplotlib.pyplot as plt
import csv
import os

def plot_route(csv_path: str, output_path: str = None):
    """
    Plota a rota do drone a partir do arquivo CSV gerado
    
    Args:
        csv_path: Caminho para o arquivo flight_plan.csv
        output_path: Caminho para salvar a imagem (opcional)
    """
    # Ler o CSV
    lats_from = []
    lons_from = []
    lats_to = []
    lons_to = []
    ceps_from = []
    ceps_to = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lats_from.append(float(row['Latitude inicial']))
            lons_from.append(float(row['Longitude inicial']))
            lats_to.append(float(row['Latitude final']))
            lons_to.append(float(row['Longitude final']))
            ceps_from.append(row['CEP inicial'])
            ceps_to.append(row['CEP final'])
    
    # Criar figura
    plt.figure(figsize=(12, 10))
    
    # Plotar todos os pontos em azul
    all_lats = list(set(lats_from + lats_to))
    all_lons = list(set(lons_from + lons_to))
    plt.scatter(all_lons, all_lats, c='blue', s=50, alpha=0.6, zorder=2)
    
    # Plotar o ponto base (Unibrasil) em vermelho
    # CEP base: 82821020, lat=-25.408000, lon=-49.292000
    base_lat = -25.408000
    base_lon = -49.292000
    plt.scatter([base_lon], [base_lat], c='red', s=200, marker='o', 
                edgecolors='darkred', linewidths=2, zorder=5, label='Unibrasil (Base)')
    
    # Plotar as linhas da rota
    for i in range(len(lats_from)):
        plt.plot([lons_from[i], lons_to[i]], [lats_from[i], lats_to[i]], 
                'b-', alpha=0.3, linewidth=1, zorder=1)
    
    # Adicionar seta da primeira para a segunda posição para mostrar direção
    if len(lats_from) > 0:
        plt.annotate('', xy=(lons_to[0], lats_to[0]), 
                    xytext=(lons_from[0], lats_from[0]),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2),
                    zorder=3)
    
    # Configurar labels e título
    plt.xlabel('Longitude', fontsize=12)
    plt.ylabel('Latitude', fontsize=12)
    plt.title('Rota Otimizada do Drone - Curitiba\nAlgoritmo Genético', 
              fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    # Ajustar limites para melhor visualização
    margin = 0.01
    plt.xlim(min(all_lons) - margin, max(all_lons) + margin)
    plt.ylim(min(all_lats) - margin, max(all_lats) + margin)
    
    # Adicionar informações da rota
    info_text = f"Total de CEPs visitados: {len(set(ceps_from + ceps_to)) - 1}\n"
    info_text += f"Segmentos de voo: {len(lats_from)}"
    plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Salvar ou mostrar
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo em: {output_path}")
    else:
        plt.show()
    
    plt.close()


def main():
    """Função principal para gerar o gráfico da rota"""
    # Caminhos dos arquivos
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'outputs', 'flight_plan.csv')
    output_path = os.path.join(base_dir, 'outputs', 'route_visualization.png')
    
    if not os.path.exists(csv_path):
        print(f"Erro: Arquivo {csv_path} não encontrado!")
        print("Execute primeiro: python -m src.main")
        return
    
    print("Gerando visualização da rota...")
    
    # Salvar arquivo
    plot_route(csv_path, output_path)
    print(f"✅ Gráfico salvo em: {output_path}")
    
    # Mostrar também na tela
    print("\n📊 Abrindo visualização...")
    plot_route(csv_path, None)  # None = mostra na tela
    print("\n✅ Visualização concluída!")


if __name__ == '__main__':
    main()
