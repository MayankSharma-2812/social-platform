import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_visualization(csv_path="post_history.csv", output_path="score_trajectories.png"):
    """Reads post history from CSV and plots score trajectories, highlighting patterns of interest."""
    print(f"[+] Generating score trajectory visualization from {csv_path}...")
    
    if not os.path.exists(csv_path):
        print(f"[-] Error: Source file {csv_path} not found. Please run the tracker first.")
        sys.exit(1)
        
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[-] Error reading CSV file: {e}")
        sys.exit(1)
        
    if df.empty:
        print("[-] Error: CSV file is empty.")
        sys.exit(1)
        
    # Sort data by post and timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["post_id", "timestamp"])
    
    # Calculate elapsed minutes for each post
    df["elapsed_mins"] = 0
    grouped = df.groupby("post_id")
    
    post_trajectories = {}
    
    for post_id, group in grouped:
        group = group.sort_values("timestamp")
        start_time = group.iloc[0]["timestamp"]
        # Calculate minutes since start
        group["elapsed_mins"] = (group["timestamp"] - start_time).dt.total_seconds() / 60.0
        
        # Extract metadata
        title = group.iloc[0]["title"]
        scores = group["score"].tolist()
        elapsed = group["elapsed_mins"].tolist()
        
        # Calculate metrics for classification
        abs_growth = scores[-1] - scores[0]
        mid_idx = len(scores) // 2
        growth_first_half = scores[mid_idx] - scores[0]
        growth_second_half = scores[-1] - scores[mid_idx]
        
        # Pattern identification
        pattern = "Normal"
        if abs_growth <= 0:
            if all(s == scores[0] for s in scores):
                pattern = "Flatliner"
            else:
                pattern = "Stagnant"
        else:
            first_half_pct = growth_first_half / abs_growth
            second_half_pct = growth_second_half / abs_growth
            if first_half_pct >= 0.70:
                pattern = "Early Peaker"
            elif second_half_pct >= 0.70:
                pattern = "Late Accelerator"
                
        # Clean up title for labels
        short_title = title[:45] + "..." if len(title) > 45 else title
        
        post_trajectories[post_id] = {
            "title": short_title,
            "scores": scores,
            "elapsed": elapsed,
            "abs_growth": abs_growth,
            "pattern": pattern
        }
        
    if not post_trajectories:
        print("[-] Error: No trajectories found.")
        sys.exit(1)
        
    # Identify the fastest absolute grower
    fastest_post_id = max(post_trajectories, key=lambda k: post_trajectories[k]["abs_growth"])
    
    # Setup plotting style
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, ax = plt.subplots(figsize=(11, 7), dpi=150)
    
    # Track which categories we have plotted for the legend
    legend_handles = {}
    
    # Color scheme
    COLOR_FASTEST = "#FF4500"      # Bright Orange/Red (Reddit Red)
    COLOR_EARLY = "#1E90FF"        # Dodger Blue
    COLOR_LATE = "#2E8B57"         # Sea Green
    COLOR_DEFAULT = "#B0C4DE"      # Light Steel Blue with transparency
    
    # Plot in order of importance (draw default/gray lines first so they are in background)
    sorted_posts = sorted(post_trajectories.items(), key=lambda x: (
        x[0] == fastest_post_id,
        x[1]["pattern"] in ["Early Peaker", "Late Accelerator"],
        x[1]["abs_growth"]
    ))
    
    for post_id, data in sorted_posts:
        scores = data["scores"]
        elapsed = data["elapsed"]
        pattern = data["pattern"]
        title = data["title"]
        
        is_fastest = (post_id == fastest_post_id)
        
        if is_fastest:
            # Highlight Fastest Grower
            line, = ax.plot(elapsed, scores, color=COLOR_FASTEST, linewidth=3.5, 
                            marker="o", markersize=7, zorder=10, 
                            label=f"Fastest Growth (+{data['abs_growth']} upvotes)")
            legend_handles["Fastest Growth"] = line
            
            # Annotate Fastest Grower
            ax.annotate(f"Fastest Growth:\n{title}", 
                        xy=(elapsed[-1], scores[-1]), 
                        xytext=(elapsed[-1] - 45, scores[-1] + (max(scores)*0.02)),
                        arrowprops=dict(facecolor=COLOR_FASTEST, shrink=0.08, width=1.5, headwidth=6),
                        fontsize=9, color=COLOR_FASTEST, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=COLOR_FASTEST, alpha=0.9))
            
        elif pattern == "Early Peaker":
            # Highlight Early Peaker
            line, = ax.plot(elapsed, scores, color=COLOR_EARLY, linewidth=2.0, 
                            linestyle="--", marker="^", markersize=6, zorder=8)
            if "Early Peaker" not in legend_handles:
                legend_handles["Early Peaker"] = line
                
            # Annotate an Early Peaker (only one to avoid clutter)
            if "Early Peaker Annotated" not in legend_handles:
                ax.annotate("Early Peaker (Rapid start)", 
                            xy=(elapsed[2], scores[2]), 
                            xytext=(elapsed[2] - 20, scores[2] + (max(scores)*0.08)),
                            arrowprops=dict(facecolor=COLOR_EARLY, shrink=0.08, width=1, headwidth=5),
                            fontsize=8, color=COLOR_EARLY, fontweight="bold")
                legend_handles["Early Peaker Annotated"] = True
                
        elif pattern == "Late Accelerator":
            # Highlight Late Accelerator
            line, = ax.plot(elapsed, scores, color=COLOR_LATE, linewidth=2.0, 
                            linestyle=":", marker="s", markersize=6, zorder=8)
            if "Late Accelerator" not in legend_handles:
                legend_handles["Late Accelerator"] = line
                
            # Annotate a Late Accelerator
            if "Late Accelerator Annotated" not in legend_handles:
                ax.annotate("Late Accelerator (Surges late)", 
                            xy=(elapsed[-2], scores[-2]), 
                            xytext=(elapsed[-2] - 40, scores[-2] - (max(scores)*0.15)),
                            arrowprops=dict(facecolor=COLOR_LATE, shrink=0.08, width=1, headwidth=5),
                            fontsize=8, color=COLOR_LATE, fontweight="bold")
                legend_handles["Late Accelerator Annotated"] = True
                
        else:
            # Stagnant, normal, or flatline posts are faded out
            line, = ax.plot(elapsed, scores, color=COLOR_DEFAULT, linewidth=1.2, 
                            alpha=0.5, marker="x", markersize=4, zorder=2)
            if "Other Posts" not in legend_handles:
                legend_handles["Other Posts"] = line
                
    # Labels and Titles
    ax.set_title("Reddit Post Engagement Trajectories (3-Hour Window)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Time Elapsed (Minutes)", fontsize=11, fontweight="semibold", labelpad=10)
    ax.set_ylabel("Score (Upvote Count)", fontsize=11, fontweight="semibold", labelpad=10)
    
    # Force X-axis ticks to match 30-minute intervals
    ax.set_xticks(np.arange(0, 181, 30))
    ax.set_xlim(-5, 185)
    
    # Legend construction
    clean_handles = []
    clean_labels = []
    for label in ["Fastest Growth", "Early Peaker", "Late Accelerator", "Other Posts"]:
        if label in legend_handles:
            clean_handles.append(legend_handles[label])
            clean_labels.append(label)
            
    ax.legend(clean_handles, clean_labels, loc="upper left", frameon=True, shadow=True, facecolor="white", edgecolor="none")
    
    # Premium grid style
    ax.grid(True, linestyle="--", alpha=0.5, color="#D3D3D3")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    print(f"[+] Visualization successfully saved to {output_path}")

if __name__ == "__main__":
    generate_visualization()
