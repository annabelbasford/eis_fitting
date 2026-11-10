import matplotlib.pyplot as plt
import warnings


class FigureSaver:
    def __init__(self, save_preferences: dict):
        self.save_preferences = save_preferences

    def save(self, save_path, fig, axes):
        save_to_png = self.save_preferences.get("png", True)
        save_to_svg = self.save_preferences.get("svg", False)
        transparent = self.save_preferences.get("transparent", False)
        dpi = self.save_preferences.get("dpi", 250)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Tight layout not applied.*")
            fig.tight_layout()

        if transparent:
            fig.patch.set_alpha(0)

            for ax in axes:
                ax.patch.set_alpha(0)

        if save_to_png:
            fig.savefig(
                save_path.parent / (save_path.name + ".png"),
                format="png",
                transparent=transparent,
                dpi=dpi,
                bbox_inches="tight",
            )

        if save_to_svg:
            fig.savefig(
                save_path.parent / (save_path.name + ".svg"),
                format="svg",
                transparent=transparent,
                dpi=dpi,
                bbox_inches="tight",
            )

        plt.close(fig)
