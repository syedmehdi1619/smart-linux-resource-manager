import psutil
import matplotlib.pyplot as plt


def get_ram_stats():
    """Returns current RAM statistics dictionary."""
    mem = psutil.virtual_memory()

    # Using 1024**3 (GiB) for GB conversion
    stats = {
        "usage": mem.percent,
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
    }
    return stats


def check_ram_alert(ram_usage):
    """Checks for high RAM usage and returns alert status."""
    if ram_usage > 85.0:
        return "[ALERT] Warning: High RAM usage detected!"
    return "[STATUS] RAM usage is normal."


def plot_live_ram_history():
    """Opens the graph window first and updates live data second-by-second up to 60 seconds."""
    # Matplotlib ka interactive mode on karna taake graph live update ho sakay
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 4))

    times = []
    usages = []

    ax.set_title('Live RAM Usage History (60 Seconds)')
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('RAM Usage (%)')
    ax.set_xlim(1, 60)  # X-axis ko 60 seconds tak fix kar diya hai
    ax.set_ylim(0, 100)  # Y-axis percentage 0 se 100 tak rahegi
    ax.grid(True)

    line, = ax.plot([], [], color='green', linestyle='-', linewidth=1.5,
                    marker='o', markersize=4)

    print("\nLive RAM graph window khul rahi hai, baraye meharbani wahan dekhein...")

    for i in range(1, 61):
        # Fetching live RAM usage after every second
        usage = psutil.virtual_memory().percent
        times.append(i)
        usages.append(usage)

        # Updating line data
        line.set_xdata(times)
        line.set_ydata(usages)

        fig.canvas.draw()
        fig.canvas.flush_events()

        print(f"Time: {i}s | Live RAM Usage: {usage}%")

        # Wait ~1 second between readings
        plt.pause(1)

    plt.ioff()  # Interactive mode off karna jab 60 seconds poore ho jayein
    plt.show()


if __name__ == "__main__":
    print("=== MEMBER 2: LIVE RAM MONITORING MODULE ===")

    # 1. Print current stats and alerts
    stats = get_ram_stats()
    print(f"Current RAM Usage: {stats['usage']}%")
    print(f"Total RAM: {stats['total_gb']} GB")
    print(f"Used RAM: {stats['used_gb']} GB")
    print(f"Available RAM: {stats['available_gb']} GB")
    print(check_ram_alert(stats['usage']))

    print("-" * 40)

    # 2. Run Live Animated Graph
    plot_live_ram_history()

