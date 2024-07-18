# Plot some data

import matplotlib.pyplot as plt

def main():
    import matplotlib.pyplot as plt

    # Create a figure and multiple subplots 
    # the plot created by following statement creates 3 rows of 3, 10 X 10 squares (until resized)
    fig, axs = plt.subplots(3, 3, figsize=(10, 10))

    # Add text to each subplot
    texts = []
    for i, ax in enumerate(axs.flat):
        text = ax.text(0.5, 0.5, f'Subplot {i+1}', transform=ax.transAxes, fontsize=12, ha='center')
        texts.append(text)

    # Function to update text size based on figure size
    def update_text_size(event):
        for text in texts:
            new_fontsize = fig.get_size_inches()[0] * 1.5  # Adjust the factor as needed
            text.set_fontsize(new_fontsize)
        fig.canvas.draw_idle()

    # Connect the resize event to the update function
    fig.canvas.mpl_connect('resize_event', update_text_size)

    # Show the plot
    plt.show()