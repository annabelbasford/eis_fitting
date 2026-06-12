import matplotlib.pyplot as plt

def save_fig(save_path, fig, axes, save_preferences):
    """
    save_path : pathlib class structured like
    .../fits/plots/sample_name/sample_name_{circuit_name}_nyquist.png"

    fig : see matplotlib
    axes : set of matplotlib axes
    save_to_png/csv : Boolean
    """

    save_to_png = save_preferences["png"]
    save_to_svg = save_preferences["svg"]
    transparent = save_preferences["transparent"]

    
    fig.tight_layout()

    if transparent:
        # transparent background
        fig.patch.set_alpha(0)
        # transparent plotting area for each figure
        for ax in axes:
            ax.patch.set_alpha(0)

    if save_to_png:
        file_path = save_path.with_suffix(".png")
        fig.savefig(file_path, format="png", transparent=transparent, dpi=300)
    if save_to_svg:
        file_path = save_path.with_suffix(".svg")
        fig.savefig(file_path, format="svg", transparent=transparent, dpi=300)

    plt.close(fig)