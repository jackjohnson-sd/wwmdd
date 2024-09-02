import matplotlib.pyplot as plt
import numpy as np

class TextResizer:
    def __init__(self, texts, fig=None, minimal=4):
        if not fig:
            fig = plt.gcf()
        self.fig = fig
        self.texts = texts
        self.fontsizes = [t.get_fontsize() for t in self.texts]
        _, self.windowheight = fig.get_size_inches() * fig.dpi
        self.minimal = minimal

    def __call__(self, event=None):
        scale = event.height / self.windowheight
        for i in range(len(self.texts)):
            newsize = max(int(self.fontsizes[i] * scale), self.minimal)
            self.texts[i].set_fontsize(newsize)

def main():
    fig, ax = plt.subplots()
    texts = [
        ax.text(0.2, 0.2, 'Text2', fontsize=9),
        ax.text(0.3, 0.3, 'Text3', fontsize=7),
        ax.text(0.4, 0.4, 'Text4', fontsize=6),
        ax.text(0.5, 0.5, 'Text5', fontsize=5),
        ax.text(0.6, 0.6, 'Text6', fontsize=6),
        ax.text(0.7, 0.7, 'Text7', fontsize=7),
        ax.text(0.8, 0.8, 'Text8', fontsize=9)
        ]

    resizer = TextResizer(texts)
    cid = fig.canvas.mpl_connect('resize_event', resizer)

    plt.show()