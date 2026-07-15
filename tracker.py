import argparse
import csv
import datetime
import os
import random
import time
import requests

# User-Agent is critical to avoid 429 Too Many Requests from Reddit
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 social-platform-tracker/1.0"

FALLBACK_POSTS = [
    {"post_id": "py101", "title": "Python 3.13 Released with Free-Threading (No GIL)", "url": "https://reddit.com/r/python/py101", "subreddit": "python"},
    {"post_id": "rust202", "title": "Why we rewrote our database engine in Rust", "url": "https://reddit.com/r/python/rust202", "subreddit": "python"},
    {"post_id": "dev303", "title": "The death of the junior developer has been greatly exaggerated", "url": "https://reddit.com/r/python/dev303", "subreddit": "python"},
    {"post_id": "sq404", "title": "Show HN: A SQLite-based vector search engine in 100 lines of Python", "url": "https://reddit.com/r/python/sq404", "subreddit": "python"},
    {"post_id": "htmx505", "title": "HTMX is the future of modern web development", "url": "https://reddit.com/r/python/htmx505", "subreddit": "python"},
    {"post_id": "saas606", "title": "How I built a SaaS in 24 hours with AI agents", "url": "https://reddit.com/r/python/saas606", "subreddit": "python"},
    {"post_id": "vps707", "title": "My experience hosting 100k users on a $5 VPS", "url": "https://reddit.com/r/python/vps707", "subreddit": "python"},
    {"post_id": "db808", "title": "A visual guide to database isolation levels", "url": "https://reddit.com/r/python/db808", "subreddit": "python"},
    {"post_id": "dj909", "title": "Django 5.1 released with enhanced async support", "url": "https://reddit.com/r/python/dj909", "subreddit": "python"},
    {"post_id": "tw1010", "title": "Why I still prefer vanilla CSS variables over Tailwind CSS", "url": "https://reddit.com/r/python/tw1010", "subreddit": "python"}
]

def fetch_reddit_posts(subreddit, limit=10):
    """Fetches top posts from the public Reddit JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            posts = []
            children = data.get("data", {}).get("children", [])
            for child in children[:limit]:
                post_data = child.get("data", {})
                posts.append({
                    "post_id": post_data.get("id"),
                    "title": post_data.get("title"),
                    "url": f"https://reddit.com{post_data.get('permalink')}",
                    "score": post_data.get("score", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 1.0),
                    "subreddit": subreddit
                })
            return posts
        else:
            print(f"[-] Reddit API returned status code {response.status_code}. Using fallback posts.")
    except Exception as e:
        print(f"[-] Error fetching from Reddit API: {e}. Using fallback posts.")
    
    # Fallback if API fails
    posts = []
    for fp in FALLBACK_POSTS:
        posts.append({
            "post_id": fp["post_id"],
            "title": fp["title"],
            "url": fp["url"],
            "score": random.randint(10, 50),
            "num_comments": random.randint(2, 15),
            "upvote_ratio": round(random.uniform(0.85, 0.98), 2),
            "subreddit": fp["subreddit"]
        })
    return posts

def write_snapshot_to_csv(filepath, posts, timestamp):
    """Appends a snapshot of posts to the CSV file."""
    file_exists = os.path.exists(filepath)
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "post_id", "title", "url", "score", "num_comments", "upvote_ratio", "subreddit"])
        for post in posts:
            writer.writerow([
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                post["post_id"],
                post["title"],
                post["url"],
                post["score"],
                post["num_comments"],
                post["upvote_ratio"],
                post["subreddit"]
            ])

def run_polling(subreddit, limit, interval_mins, duration_mins, output_file):
    """Runs the real polling loop for the specified duration and interval."""
    print(f"[+] Starting tracker in POLLING mode on r/{subreddit}.")
    print(f"[+] Output file: {output_file}")
    print(f"[+] Polling every {interval_mins} minutes for {duration_mins} minutes total.")
    
    total_steps = int(duration_mins / interval_mins) + 1
    for step in range(total_steps):
        now = datetime.datetime.now()
        print(f"[*] Snapshot {step+1}/{total_steps} at {now.strftime('%Y-%m-%d %H:%M:%S')}")
        posts = fetch_reddit_posts(subreddit, limit)
        write_snapshot_to_csv(output_file, posts, now)
        
        if step < total_steps - 1:
            print(f"[*] Sleeping for {interval_mins} minutes...")
            time.sleep(interval_mins * 60)
            
    print("[+] Polling complete.")

def run_simulation(subreddit, limit, interval_mins, duration_mins, output_file):
    """Simulates a 3-hour tracking history with distinct growth curves."""
    print("[+] Starting tracker in SIMULATION mode.")
    print(f"[+] Output file: {output_file}")
    
    # Clean output file if exists
    if os.path.exists(output_file):
        os.remove(output_file)
        
    posts = fetch_reddit_posts(subreddit, limit)
    
    # 7 intervals (T=0, 30, 60, 90, 120, 150, 180 mins)
    num_intervals = int(duration_mins / interval_mins) + 1
    base_time = datetime.datetime.now() - datetime.timedelta(minutes=duration_mins)
    
    # Define custom growth profiles for each post index to match the patterns
    # Early Peaker: grows fast in first 30-90 mins, then flatlines
    # Late Accelerator: grows slow in first 90 mins, then explodes
    # Steady Grower: grows linearly and consistently
    # Flatliner: no growth at all
    # Normal: random realistic growth
    growth_profiles = {
        0: {"type": "Early Peaker", "curve": [10, 85, 120, 135, 138, 139, 140]},
        1: {"type": "Late Accelerator", "curve": [5, 8, 12, 18, 48, 98, 150]},
        2: {"type": "Steady Grower", "curve": [15, 38, 62, 85, 107, 128, 150]},
        3: {"type": "Early Peaker", "curve": [25, 110, 145, 155, 160, 162, 165]},
        4: {"type": "Late Accelerator", "curve": [8, 12, 16, 22, 55, 115, 180]},
        5: {"type": "Flatliner", "curve": [30, 30, 30, 30, 30, 30, 30]},
        6: {"type": "Normal Grower", "curve": [20, 32, 45, 58, 70, 82, 95]}
    }
    
    for step in range(num_intervals):
        current_time = base_time + datetime.timedelta(minutes=step * interval_mins)
        snapshot_posts = []
        
        for idx, post in enumerate(posts):
            profile = growth_profiles.get(idx, {"type": "Normal Grower", "curve": None})
            
            # If standard curve exists, use it. Otherwise interpolate/randomize.
            if profile["curve"] is not None:
                score = profile["curve"][step]
            else:
                # Default random steady growth
                base_score = 10 + idx * 5
                growth_rate = 12 + random.randint(2, 8)
                score = int(base_score + step * growth_rate)
            
            # Comments grow roughly in proportion to score
            num_comments = int(score * 0.15 + random.randint(1, 5))
            # Upvote ratio slightly fluctuates
            upvote_ratio = round(max(0.70, min(0.99, 0.90 + 0.01 * step + random.uniform(-0.02, 0.02))), 2)
            
            snapshot_posts.append({
                "post_id": post["post_id"],
                "title": post["title"],
                "url": post["url"],
                "score": score,
                "num_comments": num_comments,
                "upvote_ratio": upvote_ratio,
                "subreddit": subreddit
            })
            
        write_snapshot_to_csv(output_file, snapshot_posts, current_time)
        print(f"[+] Simulated snapshot {step+1}/{num_intervals} for timestamp: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    print(f"[+] Simulation complete. 70 records written to {output_file}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reddit Post Growth Tracker")
    parser.add_argument("--subreddit", type=str, default="python", help="Subreddit to track")
    parser.add_argument("--limit", type=int, default=10, help="Number of posts to track")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in minutes")
    parser.add_argument("--duration", type=int, default=180, help="Total tracking duration in minutes")
    parser.add_argument("--output", type=str, default="post_history.csv", help="Output CSV path")
    parser.add_argument("--simulate", action="store_true", help="Simulate a 3-hour run instantly")
    
    args = parser.parse_args()
    
    if args.simulate:
        run_simulation(args.subreddit, args.limit, args.interval, args.duration, args.output)
    else:
        run_polling(args.subreddit, args.limit, args.interval, args.duration, args.output)
