"""
Criador de gráficos e visualizações estatísticas para NDVI.
"""

from typing import Dict, List, Optional
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from ..config import NDVI_CLASSES


class ChartCreator:
    """Classe para criar gráficos e visualizações estatísticas."""

    @staticmethod
    def create_histogram(
        ndvi: np.ndarray,
        bins: int = 50,
        title: str = "Distribuição de NDVI",
    ) -> plt.Figure:
        """
        Cria histograma dos valores NDVI.

        Args:
            ndvi: Array com valores NDVI
            bins: Número de bins do histograma
            title: Título do gráfico

        Returns:
            Figura matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Remover NaN
        valid_ndvi = ndvi[~np.isnan(ndvi)]

        # Criar histograma
        counts, bins_edges, patches = ax.hist(
            valid_ndvi,
            bins=bins,
            range=(-1, 1),
            edgecolor="black",
            alpha=0.7,
        )

        # Colorir barras baseado em classes NDVI
        colors = {
            "water": "#d73027",
            "bare_soil": "#fc8d59",
            "sparse_vegetation": "#fee08b",
            "moderate_vegetation": "#d9ef8b",
            "dense_vegetation": "#1a9850",
        }

        class_ranges = list(NDVI_CLASSES.values())
        class_names = list(NDVI_CLASSES.keys())

        for patch, left_edge in zip(patches, bins_edges[:-1]):
            # Determinar a classe
            for i, (min_val, max_val) in enumerate(class_ranges):
                if min_val <= left_edge < max_val:
                    patch.set_facecolor(colors[class_names[i]])
                    break

        # Configurar eixos e título
        ax.set_xlabel("NDVI", fontsize=12)
        ax.set_ylabel("Frequência (pixels)", fontsize=12)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)

        # Adicionar estatísticas no gráfico
        mean_ndvi = np.mean(valid_ndvi)
        median_ndvi = np.median(valid_ndvi)
        ax.axvline(mean_ndvi, color="red", linestyle="--",
                   linewidth=2, label=f"Média: {mean_ndvi:.3f}")
        ax.axvline(median_ndvi, color="blue", linestyle="--",
                   linewidth=2, label=f"Mediana: {median_ndvi:.3f}")

        ax.legend()
        plt.tight_layout()

        return fig

    @staticmethod
    def create_class_pie_chart(
        class_stats: Dict[str, Dict],
        title: str = "Distribuição de Classes de Vegetação",
    ) -> plt.Figure:
        """
        Cria gráfico de pizza com distribuição de classes.

        Args:
            class_stats: Dicionário com estatísticas por classe
            title: Título do gráfico

        Returns:
            Figura matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Extrair dados
        labels = []
        sizes = []
        colors_map = {
            "water": "#d73027",
            "bare_soil": "#fc8d59",
            "sparse_vegetation": "#fee08b",
            "moderate_vegetation": "#d9ef8b",
            "dense_vegetation": "#1a9850",
        }
        colors = []

        labels_pt = {
            "water": "Água/Nuvens",
            "bare_soil": "Solo Exposto",
            "sparse_vegetation": "Vegetação Esparsa",
            "moderate_vegetation": "Vegetação Moderada",
            "dense_vegetation": "Vegetação Densa",
        }

        for class_name, stats in class_stats.items():
            if stats["percentage"] > 0:  # Incluir apenas classes com dados
                labels.append(labels_pt.get(class_name, class_name))
                sizes.append(stats["percentage"])
                colors.append(colors_map.get(class_name, "#cccccc"))

        # Criar gráfico de pizza
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            explode=[0.05] * len(sizes),
        )

        # Estilizar texto
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight("bold")

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(10)

        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
        plt.tight_layout()

        return fig

    @staticmethod
    def create_statistics_table(
        stats: Dict,
        class_stats: Dict[str, Dict],
    ) -> plt.Figure:
        """
        Cria tabela com estatísticas do NDVI.

        Args:
            stats: Estatísticas gerais
            class_stats: Estatísticas por classe

        Returns:
            Figura matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.axis("off")

        # Estatísticas gerais
        general_data = [
            ["Métrica", "Valor"],
            ["Média", f"{stats.get('mean', 0):.4f}"],
            ["Mediana", f"{stats.get('median', 0):.4f}"],
            ["Desvio Padrão", f"{stats.get('std', 0):.4f}"],
            ["Mínimo", f"{stats.get('min', 0):.4f}"],
            ["Máximo", f"{stats.get('max', 0):.4f}"],
            ["Pixels Válidos", f"{stats.get('valid_pixels', 0):,}"],
            ["Pixels Totais", f"{stats.get('total_pixels', 0):,}"],
        ]

        table1 = ax.table(
            cellText=general_data,
            cellLoc="left",
            loc="upper center",
            bbox=[0, 0.5, 0.45, 0.5],
        )
        table1.auto_set_font_size(False)
        table1.set_fontsize(10)
        table1.scale(1, 2)

        # Estilizar cabeçalho
        for i in range(2):
            table1[(0, i)].set_facecolor("#4CAF50")
            table1[(0, i)].set_text_props(weight="bold", color="white")

        # Estatísticas por classe
        labels_pt = {
            "water": "Água/Nuvens",
            "bare_soil": "Solo Exposto",
            "sparse_vegetation": "Vegetação Esparsa",
            "moderate_vegetation": "Vegetação Moderada",
            "dense_vegetation": "Vegetação Densa",
        }

        class_data = [["Classe", "Pixels", "Percentual"]]
        for class_name, stats in class_stats.items():
            class_data.append([
                labels_pt.get(class_name, class_name),
                f"{stats['pixel_count']:,}",
                f"{stats['percentage']:.2f}%",
            ])

        table2 = ax.table(
            cellText=class_data,
            cellLoc="left",
            loc="upper center",
            bbox=[0.55, 0.5, 0.45, 0.5],
        )
        table2.auto_set_font_size(False)
        table2.set_fontsize(10)
        table2.scale(1, 2)

        # Estilizar cabeçalho
        for i in range(3):
            table2[(0, i)].set_facecolor("#2196F3")
            table2[(0, i)].set_text_props(weight="bold", color="white")

        # Título
        ax.text(
            0.5, 0.95, "Estatísticas do NDVI",
            ha="center", va="top",
            fontsize=16, fontweight="bold",
            transform=ax.transAxes,
        )

        return fig

    @staticmethod
    def create_time_series_plot(
        dates: List[datetime],
        ndvi_values: List[float],
        title: str = "Série Temporal de NDVI",
    ) -> go.Figure:
        """
        Cria gráfico de série temporal interativo com Plotly.

        Args:
            dates: Lista de datas
            ndvi_values: Lista de valores médios de NDVI
            title: Título do gráfico

        Returns:
            Figura Plotly
        """
        fig = go.Figure()

        # Adicionar linha principal
        fig.add_trace(go.Scatter(
            x=dates,
            y=ndvi_values,
            mode="lines+markers",
            name="NDVI Médio",
            line=dict(color="#1a9850", width=3),
            marker=dict(size=8),
        ))

        # Adicionar faixas de referência
        fig.add_hrect(
            y0=-1, y1=0,
            fillcolor="red", opacity=0.1,
            annotation_text="Água/Nuvens", annotation_position="left",
        )
        fig.add_hrect(
            y0=0, y1=0.2,
            fillcolor="orange", opacity=0.1,
            annotation_text="Solo Exposto", annotation_position="left",
        )
        fig.add_hrect(
            y0=0.2, y1=0.4,
            fillcolor="yellow", opacity=0.1,
            annotation_text="Veg. Esparsa", annotation_position="left",
        )
        fig.add_hrect(
            y0=0.4, y1=0.6,
            fillcolor="lightgreen", opacity=0.1,
            annotation_text="Veg. Moderada", annotation_position="left",
        )
        fig.add_hrect(
            y0=0.6, y1=1,
            fillcolor="green", opacity=0.1,
            annotation_text="Veg. Densa", annotation_position="left",
        )

        # Configurar layout
        fig.update_layout(
            title=title,
            xaxis_title="Data",
            yaxis_title="NDVI",
            yaxis=dict(range=[-1, 1]),
            hovermode="x unified",
            template="plotly_white",
            height=500,
        )

        return fig

    @staticmethod
    def create_comparison_plot(
        ndvi_before: np.ndarray,
        ndvi_after: np.ndarray,
        date_before: str,
        date_after: str,
    ) -> plt.Figure:
        """
        Cria gráfico de comparação entre dois períodos.

        Args:
            ndvi_before: NDVI do primeiro período
            ndvi_after: NDVI do segundo período
            date_before: Data do primeiro período
            date_after: Data do segundo período

        Returns:
            Figura matplotlib
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Remover NaN
        valid_before = ndvi_before[~np.isnan(ndvi_before)]
        valid_after = ndvi_after[~np.isnan(ndvi_after)]

        # Histograma antes
        axes[0].hist(valid_before, bins=30, range=(-1, 1),
                     alpha=0.7, color="blue", edgecolor="black")
        axes[0].set_title(f"NDVI - {date_before}", fontweight="bold")
        axes[0].set_xlabel("NDVI")
        axes[0].set_ylabel("Frequência")
        axes[0].axvline(np.mean(valid_before), color="red",
                        linestyle="--", label=f"Média: {np.mean(valid_before):.3f}")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Histograma depois
        axes[1].hist(valid_after, bins=30, range=(-1, 1),
                     alpha=0.7, color="green", edgecolor="black")
        axes[1].set_title(f"NDVI - {date_after}", fontweight="bold")
        axes[1].set_xlabel("NDVI")
        axes[1].set_ylabel("Frequência")
        axes[1].axvline(np.mean(valid_after), color="red",
                        linestyle="--", label=f"Média: {np.mean(valid_after):.3f}")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        # Diferença (mudança)
        ndvi_diff = ndvi_after - ndvi_before
        valid_diff = ndvi_diff[~np.isnan(ndvi_diff)]

        axes[2].hist(valid_diff, bins=30, alpha=0.7,
                     color="purple", edgecolor="black")
        axes[2].set_title("Mudança de NDVI (Depois - Antes)",
                          fontweight="bold")
        axes[2].set_xlabel("Diferença de NDVI")
        axes[2].set_ylabel("Frequência")
        axes[2].axvline(0, color="black", linestyle="-", linewidth=2)
        axes[2].axvline(np.mean(valid_diff), color="red",
                        linestyle="--", label=f"Média: {np.mean(valid_diff):.3f}")
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig
