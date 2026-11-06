import psutil
import matplotlib.pyplot as plt

def get_cpu_stats():
    """Returns current CPU statistics dictionary"""
    cpu_usage = psutil.cpu_percent(interval=None)
    physical_cores = psutil.cpu_count(logical=False)
    total_threads = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    
    stats = {
        "usage": cpu_usage,
        "physical_cores": physical_cores,
        "total_threads": total_threads,
        "current_freq": cpu_freq.current if cpu_freq else 0,
        "max_freq": cpu_freq.max if cpu_freq else 0
    }
    return stats

def check_cpu_alert(cpu_usage):
    """Checks for high CPU usage and returns alert status"""
    if cpu_usage > 85.0:
        return "[ALERT] Warning: High CPU usage detected!"
    return "[STATUS] CPU usage is normal."

def plot_live_cpu_history():
    """Opens the graph window first and updates live data second-by-second up to 60 seconds"""
    # Matplotlib ka interactive mode on karna taake graph live update ho sakay
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 4))
    
    times = []
    usages = []
    
    ax.set_title('Live CPU Usage History (60 Seconds)')
    ax.set_xlabel('Time (seconds)')
    ax.set_ylabel('CPU Usage (%)')
    ax.set_xlim(1, 60) # X-axis ko 60 seconds tak fix kar diya hai
    ax.set_ylim(0, 100) # Y-axis percentage 0 se 100 tak rahegi
    ax.grid(True)
    
    
    line, = ax.plot([], [], color='blue', linestyle='-', linewidth=1.5, marker='o', markersize=4)
    
    print("\nLive CPU graph window khul rahi hai, baraye meharbani wahan dekhein...")
    
    for i in range(1, 61):
        # fetching live cpu usage after every second 
        usage = psutil.cpu_percent(interval=1)
        times.append(i)
        usages.append(usage)
        
        # updating line data 
        line.set_xdata(times)
        line.set_ydata(usages)
        
        fig.canvas.draw()
        fig.canvas.flush_events()
        
        print(f"Time: {i}s | Live CPU Usage: {usage}%")
        
    plt.ioff() # Interactive mode off karna jab 60 seconds poore ho jayein
    plt.show()

if __name__ == "__main__":
    print("=== MEMBER 1: LIVE CPU MONITORING MODULE ===")
    
    # 1. Print current stats and alerts
    stats = get_cpu_stats()
    print(f"Current CPU Usage: {stats['usage']}%")
    print(f"Physical Cores: {stats['physical_cores']}")
    print(f"Total Threads: {stats['total_threads']}")
    print(f"Current Frequency: {stats['current_freq']:.2f} MHz")
    print(check_cpu_alert(stats['usage']))
    
    print("-" * 40)
    
    # 2. Run Live Animated Graph
    plot_live_cpu_history()