import matplotlib.pyplot as plt


def visualize_bar_chart_to_image(x_list, y_list, output_file):

    # Define the background color
    blue_cobalt = "#004B73"  # Hex code for blue coban
    green_bar = "#00AA00"  # Green color for bars

    # Plotting the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(x_list, y_list, color=green_bar, alpha=0.8)

    # Set the background color
    plt.gca().set_facecolor(blue_cobalt)  # Change plot area background
    plt.gcf().set_facecolor(blue_cobalt)  # Change figure area background

    # Adding labels and title
    plt.xlabel("Frame Number", fontsize=12, color="white")  # White text for readability
    plt.ylabel("Count", fontsize=12, color="white")  # White text for readability
    plt.title(
        "People Count over Time", fontsize=14, color="white"
    )  # White text for readability
    plt.xticks(color="white", fontsize=10)
    plt.yticks(color="white", fontsize=10)

    # Save the chart as an image
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
