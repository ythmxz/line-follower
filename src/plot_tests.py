#!/usr/bin/env python3
"""
plot_tests.py
=============
Gera gráficos a partir dos CSVs de teste do robô seguidor de linha.
Lê arquivos de logs/on_off/{success,fail}/ e (futuramente) logs/proportional/.

Uso:
    python plot_tests.py                     # processa todos os testes
    python plot_tests.py --controller on_off # apenas on_off
    python plot_tests.py --result success    # apenas testes bem-sucedidos
    python plot_tests.py --file <caminho>    # arquivo específico
    python plot_tests.py --summary           # apenas gráficos de resumo comparativo
    python plot_tests.py --save              # salva em logs/plots/ (não exibe)
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# ──────────────────────────────────────────────────────────────────────────────
# Configuração visual
# ──────────────────────────────────────────────────────────────────────────────
PALETTE = {
    "success": "#4ade80",
    "fail":    "#f87171",
    "left":    "#60a5fa",
    "right":   "#fb923c",
    "sensor":  "#a78bfa",
    "error":   "#f472b6",
    "speed":   "#34d399",
    "smooth":  "#fbbf24",
    "osc":     "#e879f9",
    "neutral": "#94a3b8",
}

DARK_BG    = "#0f172a"
PANEL_BG   = "#1e293b"
GRID_COLOR = "#334155"
TEXT_COLOR = "#e2e8f0"
ACCENT     = "#38bdf8"


def apply_dark_style():
    """Aplica estilo escuro global ao matplotlib."""
    plt.rcParams.update({
        "figure.facecolor":   DARK_BG,
        "axes.facecolor":     PANEL_BG,
        "axes.edgecolor":     GRID_COLOR,
        "axes.labelcolor":    TEXT_COLOR,
        "axes.titlecolor":    TEXT_COLOR,
        "axes.grid":          True,
        "grid.color":         GRID_COLOR,
        "grid.linewidth":     0.6,
        "grid.alpha":         0.7,
        "xtick.color":        TEXT_COLOR,
        "ytick.color":        TEXT_COLOR,
        "text.color":         TEXT_COLOR,
        "legend.facecolor":   PANEL_BG,
        "legend.edgecolor":   GRID_COLOR,
        "legend.labelcolor":  TEXT_COLOR,
        "lines.linewidth":    1.6,
        "font.family":        "sans-serif",
        "font.size":          10,
        "axes.titlesize":     12,
        "axes.labelsize":     10,
        "figure.titlesize":   14,
        "figure.titleweight": "bold",
    })


# ──────────────────────────────────────────────────────────────────────────────
# Paths e descoberta de arquivos
# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent

CONTROLLERS = {
    "on_off": {
        "success": ROOT / "logs" / "on_off" / "success",
        "fail":    ROOT / "logs" / "on_off" / "fail",
    },
    "proportional": {
        "success": ROOT / "logs" / "proportional" / "success",
        "fail":    ROOT / "logs" / "proportional" / "fail",
    },
}

OUTPUT_DIR = ROOT / "plots"


def find_test_csvs(controller=None, result=None):
    """Retorna lista de dicts {path, controller, result} para cada CSV de teste."""
    files = []
    for ctrl, paths in CONTROLLERS.items():
        if controller and ctrl != controller:
            continue
        for res, folder in paths.items():
            if result and res != result:
                continue
            if not folder.exists():
                continue
            for csv_path in sorted(folder.glob("*.csv")):
                files.append({"path": csv_path, "controller": ctrl, "result": res})
    return files


def load_csv(path):
    """Carrega CSV do teste, limpando espaços extras dos cabeçalhos."""
    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return df


def extract_timestamp(filename):
    """Extrai timestamp legível do nome do arquivo."""
    stem = Path(filename).stem
    parts = stem.split("_")
    for i, p in enumerate(parts):
        if len(p) == 4 and p.isdigit() and i + 5 < len(parts):
            date = f"{parts[i]}-{parts[i+1]}-{parts[i+2]}"
            time = f"{parts[i+3]}:{parts[i+4]}:{parts[i+5]}"
            return f"{date} {time}"
    return stem


# ──────────────────────────────────────────────────────────────────────────────
# Painel individual por arquivo
# ──────────────────────────────────────────────────────────────────────────────
def plot_single_test(info, save_dir=None, show=True):
    """Gera painel completo de 6 subgráficos para um único arquivo de teste."""
    df  = load_csv(info["path"])
    ts  = extract_timestamp(info["path"].name)
    res = info["result"]
    ctrl = info["controller"]
    color_res = PALETTE[res]

    apply_dark_style()

    fig = plt.figure(figsize=(16, 12), constrained_layout=True)
    fig.suptitle(
        f"[{ctrl.upper()}]  {ts}  —  {'✔ Sucesso' if res == 'success' else '✘ Falha'}",
        color=color_res, fontsize=14, fontweight="bold",
    )

    gs = gridspec.GridSpec(3, 2, figure=fig)
    t  = df.iloc[:, 0]  # Tempo (s)

    # ── 1. Velocidades dos motores ──────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(t, df["Velocidade Esq. (deg/s)"], color=PALETTE["left"],  label="Esquerda")
    ax1.plot(t, df["Velocidade Dir. (deg/s)"], color=PALETTE["right"], label="Direita", alpha=0.8)
    ax1.set_title("Velocidades dos Motores")
    ax1.set_ylabel("deg/s")
    ax1.legend(loc="upper right")
    ax1.axhline(0, color=GRID_COLOR, linewidth=0.8)

    # ── 2. Refletância e Erro ──────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(t, df["Refletância (%)"], color=PALETTE["sensor"], label="Refletância")
    ax2_r = ax2.twinx()
    ax2_r.plot(t, df["Erro (%)"], color=PALETTE["error"], label="Erro",
               linestyle="--", alpha=0.75)
    ax2_r.set_ylabel("Erro (%)", color=PALETTE["error"])
    ax2_r.tick_params(axis="y", labelcolor=PALETTE["error"])
    ax2.set_title("Sensor: Refletância e Erro")
    ax2.set_ylabel("Refletância (%)", color=PALETTE["sensor"])
    ax2.tick_params(axis="y", labelcolor=PALETTE["sensor"])
    legend_lines = [
        Line2D([0], [0], color=PALETTE["sensor"], label="Refletância"),
        Line2D([0], [0], color=PALETTE["error"],  label="Erro", linestyle="--"),
    ]
    ax2.legend(handles=legend_lines, loc="upper right")

    # ── 3. Velocidade Média ────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(t, df["Velocidade Média (m/s)"], color=PALETTE["speed"], alpha=0.6)
    window = max(5, len(df) // 30)
    rolling = df["Velocidade Média (m/s)"].rolling(window, center=True).mean()
    ax3.plot(t, rolling, color=ACCENT, linewidth=2.2,
             label=f"Média móvel (n={window})")
    ax3.set_title("Velocidade Média")
    ax3.set_ylabel("m/s")
    ax3.legend(loc="upper right")

    # ── 4. Distância percorrida ────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(t, df["Distância (m)"], color=color_res, linewidth=2)
    ax4.fill_between(t, df["Distância (m)"], alpha=0.2, color=color_res)
    ax4.set_title("Distância Percorrida")
    ax4.set_ylabel("m")

    # ── 5. Oscilação acumulada ─────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.plot(t, df["Oscilação"], color=PALETTE["osc"], linewidth=1.8)
    ax5.fill_between(t, df["Oscilação"], alpha=0.15, color=PALETTE["osc"])
    ax5.set_title("Oscilação Acumulada (Mudanças de Direção)")
    ax5.set_ylabel("Contagem")
    ax5.set_xlabel("Tempo (s)")

    # ── 6. Suavidade ───────────────────────────────────────────────────────
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.plot(t, df["Suavidade (deg/s)"], color=PALETTE["smooth"], linewidth=1, alpha=0.6)
    window_s = max(5, len(df) // 20)
    rolling_s = df["Suavidade (deg/s)"].rolling(window_s, center=True).mean()
    ax6.plot(t, rolling_s, color="#f59e0b", linewidth=2.2,
             label=f"Média móvel (n={window_s})")
    ax6.set_title("Suavidade (Variação de Velocidade dos Motores)")
    ax6.set_ylabel("deg/s")
    ax6.set_xlabel("Tempo (s)")
    ax6.legend(loc="upper right")

    # Rodapé com métricas rápidas
    total_time = float(t.max() - t.min())
    total_dist = float(df["Distância (m)"].max())
    avg_speed  = float(df["Velocidade Média (m/s)"].mean())
    total_osc  = float(df["Oscilação"].max())
    avg_smooth = float(df["Suavidade (deg/s)"].mean())
    stats_text = (
        f"Duração: {total_time:.1f}s  |  Distância: {total_dist:.2f}m  |  "
        f"Vel. Média: {avg_speed:.4f} m/s  |  Oscilações: {total_osc:.0f}  |  "
        f"Suavidade Média: {avg_smooth:.1f} deg/s"
    )
    fig.text(0.5, 0.005, stats_text, ha="center", fontsize=9,
             color=PALETTE["neutral"], style="italic")

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        fname = save_dir / (info["path"].stem + ".png")
        fig.savefig(fname, dpi=150, bbox_inches="tight")
        print(f"  Salvo: {fname}")

    if show:
        plt.show()
    else:
        plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# Resumo comparativo
# ──────────────────────────────────────────────────────────────────────────────
def compute_summary(files):
    """Extrai métricas-resumo de todos os arquivos."""
    rows = []
    for info in files:
        try:
            df = load_csv(info["path"])
            t = df.iloc[:, 0]
            rows.append({
                "arquivo":       info["path"].stem,
                "controller":    info["controller"],
                "resultado":     info["result"],
                "duracao_s":     float(t.max() - t.min()),
                "distancia_m":   float(df["Distância (m)"].max()),
                "vel_media_ms":  float(df["Velocidade Média (m/s)"].mean()),
                "vel_max_ms":    float(df["Velocidade Média (m/s)"].max()),
                "oscilacoes":    float(df["Oscilação"].max()),
                "osc_por_m":     float(df["Oscilação"].max()
                                       / max(df["Distância (m)"].max(), 1e-9)),
                "suavidade_med": float(df["Suavidade (deg/s)"].mean()),
                "erro_medio":    float(df["Erro (%)"].mean()),
                "erro_max":      float(df["Erro (%)"].max()),
            })
        except Exception as exc:
            print(f"  [AVISO] Erro ao processar {info['path'].name}: {exc}")
    return pd.DataFrame(rows)


def plot_summary(files, save_dir=None, show=True):
    """Gera figuras comparativas entre todos os testes."""
    summary = compute_summary(files)
    if summary.empty:
        print("Nenhum dado disponível para o resumo.")
        return

    apply_dark_style()

    colors_per_row = [
        PALETTE["success"] if r == "success" else PALETTE["fail"]
        for r in summary["resultado"]
    ]

    # ── Figura 1: Barras por métrica ─────────────────────────────────────────
    metrics = [
        ("distancia_m",   "Distância (m)",         "m"),
        ("duracao_s",     "Duração (s)",            "s"),
        ("vel_media_ms",  "Velocidade Média (m/s)", "m/s"),
        ("oscilacoes",    "Oscilações Totais",      "qtd"),
        ("osc_por_m",     "Oscilações por Metro",   "1/m"),
        ("suavidade_med", "Suavidade Média",        "deg/s"),
    ]

    fig1, axes = plt.subplots(2, 3, figsize=(18, 10), constrained_layout=True)
    fig1.suptitle("Resumo Comparativo — Todos os Testes", fontsize=15, fontweight="bold")

    for ax, (col, title, unit) in zip(axes.flat, metrics):
        vals = summary[col]
        labels = [s[-10:] for s in summary["arquivo"]]
        x = np.arange(len(vals))
        ax.bar(x, vals, color=colors_per_row, width=0.6,
               edgecolor=GRID_COLOR, linewidth=0.5)
        ax.set_title(title)
        ax.set_ylabel(unit)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
        for res, pal in [("success", PALETTE["success"]), ("fail", PALETTE["fail"])]:
            sub = summary[summary["resultado"] == res][col]
            if not sub.empty:
                ax.axhline(sub.mean(), color=pal, linestyle="--",
                           linewidth=1.2, alpha=0.8)

    legend_els = [
        Line2D([0], [0], color=PALETTE["success"], marker="s",
               linestyle="None", markersize=10, label="Sucesso"),
        Line2D([0], [0], color=PALETTE["fail"],    marker="s",
               linestyle="None", markersize=10, label="Falha"),
        Line2D([0], [0], color=PALETTE["success"], linestyle="--",
               label="Média Sucesso"),
        Line2D([0], [0], color=PALETTE["fail"],    linestyle="--",
               label="Média Falha"),
    ]
    fig1.legend(handles=legend_els, loc="lower center", ncol=4,
                bbox_to_anchor=(0.5, -0.03), framealpha=0.3)

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        fig1.savefig(save_dir / "summary_comparison.png", dpi=150, bbox_inches="tight")
        print(f"  Salvo: {save_dir / 'summary_comparison.png'}")

    # ── Figura 2: Box-plots success vs fail ────────────────────────────────
    box_metrics = [
        ("distancia_m",  "Distância (m)"),
        ("oscilacoes",   "Oscilações"),
        ("vel_media_ms", "Vel. Média (m/s)"),
        ("erro_medio",   "Erro Médio (%)"),
    ]
    success_df = summary[summary["resultado"] == "success"]
    fail_df    = summary[summary["resultado"] == "fail"]

    fig2, axes2 = plt.subplots(1, len(box_metrics), figsize=(16, 5),
                               constrained_layout=True)
    fig2.suptitle("Distribuição das Métricas: Sucesso vs Falha",
                  fontsize=14, fontweight="bold")

    for ax, (col, title) in zip(axes2, box_metrics):
        data_groups, group_labels = [], []
        if not success_df.empty:
            data_groups.append(success_df[col].dropna().tolist())
            group_labels.append("Sucesso")
        if not fail_df.empty:
            data_groups.append(fail_df[col].dropna().tolist())
            group_labels.append("Falha")
        if not data_groups:
            continue
        bp = ax.boxplot(data_groups, patch_artist=True, notch=False,
                        widths=0.5, showfliers=True)
        box_colors = [PALETTE["success"], PALETTE["fail"]][:len(data_groups)]
        for patch, color in zip(bp["boxes"], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        for whisker in bp["whiskers"]:
            whisker.set_color(TEXT_COLOR)
        for cap in bp["caps"]:
            cap.set_color(TEXT_COLOR)
        for median in bp["medians"]:
            median.set_color(ACCENT)
            median.set_linewidth(2)
        for flier in bp["fliers"]:
            flier.set(marker="o", color=PALETTE["neutral"], alpha=0.5, markersize=5)
        ax.set_title(title)
        ax.set_xticks(range(1, len(group_labels) + 1))
        ax.set_xticklabels(group_labels)

    if save_dir:
        fig2.savefig(save_dir / "summary_boxplot.png", dpi=150, bbox_inches="tight")
        print(f"  Salvo: {save_dir / 'summary_boxplot.png'}")

    # ── Figura 3: Scatter correlações ──────────────────────────────────────
    fig3, axes3 = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    fig3.suptitle("Correlações entre Métricas", fontsize=14, fontweight="bold")

    for res, pal in [("success", PALETTE["success"]), ("fail", PALETTE["fail"])]:
        sub = summary[summary["resultado"] == res]
        if sub.empty:
            continue
        axes3[0].scatter(sub["distancia_m"], sub["oscilacoes"],
                         color=pal, s=80, alpha=0.85,
                         edgecolors=DARK_BG, linewidths=0.5,
                         label=res.capitalize(), zorder=3)
        axes3[1].scatter(sub["vel_media_ms"], sub["suavidade_med"],
                         color=pal, s=80, alpha=0.85,
                         edgecolors=DARK_BG, linewidths=0.5,
                         label=res.capitalize(), zorder=3)

    axes3[0].set_xlabel("Distância (m)")
    axes3[0].set_ylabel("Oscilações")
    axes3[0].set_title("Distância vs Oscilações")
    axes3[0].legend()

    axes3[1].set_xlabel("Velocidade Média (m/s)")
    axes3[1].set_ylabel("Suavidade Média (deg/s)")
    axes3[1].set_title("Velocidade vs Suavidade")
    axes3[1].legend()

    if save_dir:
        fig3.savefig(save_dir / "summary_scatter.png", dpi=150, bbox_inches="tight")
        print(f"  Salvo: {save_dir / 'summary_scatter.png'}")

    if show:
        plt.show()
    else:
        plt.close("all")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Gera gráficos dos CSVs de teste do seguidor de linha.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--controller", choices=list(CONTROLLERS.keys()),
        help="Filtra por controlador (padrão: todos)",
    )
    parser.add_argument(
        "--result", choices=["success", "fail"],
        help="Filtra por resultado (padrão: ambos)",
    )
    parser.add_argument(
        "--file", type=Path, metavar="CAMINHO",
        help="Processa apenas este arquivo CSV específico",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Gera apenas os gráficos de resumo comparativo (sem os individuais)",
    )
    parser.add_argument(
        "--no-individual", action="store_true",
        help="Pula os gráficos individuais por arquivo",
    )
    parser.add_argument(
        "--save", action="store_true",
        help="Salva os gráficos em logs/plots/ em vez de exibir na tela",
    )
    parser.add_argument(
        "--show", action="store_true", default=False,
        help="Exibe na tela mesmo ao salvar (combina com --save)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    save_dir = OUTPUT_DIR if args.save else None
    show     = not args.save or args.show

    # Arquivo único especificado manualmente
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Erro: arquivo não encontrado: {path}", file=sys.stderr)
            sys.exit(1)
        ctrl = "on_off" if "on_off" in str(path) else "proportional"
        res  = "success" if "success" in str(path) else "fail"
        info = {"path": path, "controller": ctrl, "result": res}
        sub_save = (save_dir / ctrl / res) if save_dir else None
        plot_single_test(info, save_dir=sub_save, show=show)
        return

    # Descoberta automática
    files = find_test_csvs(controller=args.controller, result=args.result)
    if not files:
        print("Nenhum arquivo de teste encontrado com os filtros especificados.")
        sys.exit(0)

    print(f"Encontrados {len(files)} arquivo(s) de teste.\n")

    # Gráficos individuais
    if not args.summary and not args.no_individual:
        for info in files:
            print(f"  [{info['result']:7s}] {info['path'].name}")
            sub_save = (save_dir / info["controller"] / info["result"]) if save_dir else None
            plot_single_test(info, save_dir=sub_save, show=show)

    # Resumo comparativo
    if not args.no_individual or args.summary:
        print("\nGerando resumo comparativo...")
        sum_save = (save_dir / "summary") if save_dir else None
        plot_summary(files, save_dir=sum_save, show=show)

    print("\nConcluído.")


if __name__ == "__main__":
    main()
