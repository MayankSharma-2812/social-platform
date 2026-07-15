import os
import sys
import pandas as pd
import numpy as np

def analyze_growth(csv_path="post_history.csv", output_path="growth_analysis.txt"):
    """Reads post history from CSV, calculates growth metrics, identifies patterns, and writes a report."""
    print(f"[+] Starting growth analysis on {csv_path}...")
    
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
        
    # Ensure correct columns exist
    required_cols = ["timestamp", "post_id", "title", "url", "score", "num_comments", "upvote_ratio", "subreddit"]
    for col in required_cols:
        if col not in df.columns:
            print(f"[-] Error: Missing required column '{col}' in CSV.")
            sys.exit(1)
            
    # Parse timestamps and sort
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["post_id", "timestamp"])
    
    analysis_results = []
    
    # Group by post_id and process each post's history
    grouped = df.groupby("post_id")
    for post_id, group in grouped:
        # Sort group by timestamp just to be safe
        group = group.sort_values("timestamp")
        
        # Get basic info
        title = group.iloc[0]["title"]
        url = group.iloc[0]["url"]
        subreddit = group.iloc[0]["subreddit"]
        
        scores = group["score"].tolist()
        timestamps = group["timestamp"].tolist()
        num_comments_list = group["num_comments"].tolist()
        
        if len(scores) < 2:
            print(f"[-] Warning: Skipping post {post_id} due to insufficient snapshots ({len(scores)})")
            continue
            
        # 1. Absolute Growth
        initial_score = scores[0]
        final_score = scores[-1]
        abs_growth = final_score - initial_score
        
        # 2. Percentage Growth Rate
        if initial_score > 0:
            pct_growth = (abs_growth / initial_score) * 100
        else:
            pct_growth = abs_growth * 100.0  # fallback handling
            
        # 3. Acceleration
        # Midpoint index
        mid_idx = len(scores) // 2
        growth_first_half = scores[mid_idx] - scores[0]
        growth_second_half = scores[-1] - scores[mid_idx]
        acceleration = growth_second_half - growth_first_half
        
        # 4. Consistency
        # Difference at each step
        diffs = np.diff(scores)
        mean_diff = np.mean(diffs) if len(diffs) > 0 else 0
        std_diff = np.std(diffs) if len(diffs) > 0 else 0
        
        # Consistency score: closer to 1.0 means steady growth.
        # If std_diff is 0, consistency is 1.0.
        consistency = 1.0 / (1.0 + std_diff)
        
        # Pattern Identification
        pattern = "Unknown"
        if abs_growth <= 0:
            if all(s == initial_score for s in scores):
                pattern = "Flatliner"
            else:
                pattern = "Stagnant/Declining"
        else:
            # Check early peaking vs late acceleration
            first_half_pct = growth_first_half / abs_growth if abs_growth > 0 else 0
            second_half_pct = growth_second_half / abs_growth if abs_growth > 0 else 0
            
            if first_half_pct >= 0.70:
                pattern = "Early Peaker"
            elif second_half_pct >= 0.70:
                pattern = "Late Accelerator"
            elif consistency >= 0.50:
                pattern = "Steady Grower"
            else:
                pattern = "Fluctuating Grower"
                
        analysis_results.append({
            "post_id": post_id,
            "title": title,
            "url": url,
            "subreddit": subreddit,
            "initial_score": initial_score,
            "final_score": final_score,
            "abs_growth": abs_growth,
            "pct_growth": round(pct_growth, 2),
            "acceleration": acceleration,
            "consistency": round(consistency, 4),
            "pattern": pattern,
            "trajectory": scores,
            "final_comments": num_comments_list[-1]
        })
        
    if not analysis_results:
        print("[-] Error: No posts analyzed.")
        sys.exit(1)
        
    # Sort results by absolute growth descending
    analysis_results.sort(key=lambda x: x["abs_growth"], reverse=True)
    
    # Identify top performers
    fastest_grower = max(analysis_results, key=lambda x: x["abs_growth"])
    highest_pct_grower = max(analysis_results, key=lambda x: x["pct_growth"])
    # Filter out stagnant posts for consistency comparison
    growing_posts = [p for p in analysis_results if p["abs_growth"] > 0]
    most_consistent = max(growing_posts, key=lambda x: x["consistency"]) if growing_posts else analysis_results[0]
    
    # Count patterns
    pattern_counts = {}
    for p in analysis_results:
        pattern_counts[p["pattern"]] = pattern_counts.get(p["pattern"], 0) + 1
        
    # Build the report content
    report = []
    report.append("=" * 80)
    report.append("                      REDDIT POST GROWTH PATTERN REPORT")
    report.append("=" * 80)
    report.append(f"Subreddit Tracked: r/{analysis_results[0]['subreddit']}")
    report.append(f"Analysis Time:     {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Posts:       {len(analysis_results)}")
    report.append("-" * 80)
    
    report.append("\n### SUMMARY OF KEY FINDINGS")
    report.append(f"- **Fastest Absolute Growth**: '{fastest_grower['title']}' (+{fastest_grower['abs_growth']} upvotes)")
    report.append(f"- **Highest % Growth Rate**:  '{highest_pct_grower['title']}' (+{highest_pct_grower['pct_growth']}% growth)")
    report.append(f"- **Most Consistent Growth**:  '{most_consistent['title']}' (Consistency: {most_consistent['consistency']})")
    
    report.append("\n### GROWTH PATTERNS OBSERVED")
    for pat, count in pattern_counts.items():
        report.append(f"- {pat}: {count} post(s)")
        
    report.append("\n" + "=" * 80)
    report.append("### DETAILED POST METRICS (Ranked by Absolute Growth)")
    report.append("=" * 80)
    
    for idx, res in enumerate(analysis_results, 1):
        report.append(f"{idx}. Title: {res['title']}")
        report.append(f"   ID: {res['post_id']} | Subreddit: r/{res['subreddit']} | URL: {res['url']}")
        report.append(f"   Trajectory: {res['trajectory']}")
        report.append(f"   Metrics:")
        report.append(f"     - Initial Score:   {res['initial_score']}")
        report.append(f"     - Final Score:     {res['final_score']}")
        report.append(f"     - Absolute Growth: {res['abs_growth']}")
        report.append(f"     - Growth Rate (%): {res['pct_growth']}%")
        report.append(f"     - Acceleration:    {res['acceleration']} (first half: {res['trajectory'][mid_idx] - res['trajectory'][0]} -> second half: {res['trajectory'][-1] - res['trajectory'][mid_idx]})")
        report.append(f"     - Consistency:     {res['consistency']}")
        report.append(f"     - Classified As:   [{res['pattern']}]")
        report.append("-" * 80)
        
    report_text = "\n".join(report)
    
    # Write to output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    # Print to console
    print(report_text)
    print(f"\n[+] Analysis report successfully saved to {output_path}")

if __name__ == "__main__":
    analyze_growth()
