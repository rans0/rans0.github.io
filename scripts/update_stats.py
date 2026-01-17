import os
import re
import requests
from datetime import datetime, timedelta

# Constants
GITHUB_TOKEN = os.getenv('GH_TOKEN')
USERNAME = 'rans0'

GRAPHQL_URL = 'https://api.github.com/graphql'
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def run_query(query):
    response = requests.post(GRAPHQL_URL, json={'query': query}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with code {response.status_code}. {query}")

def fetch_github_data():
    query = """
    {
      user(login: "%s") {
        repositories(first: 100, ownerAffiliations: OWNER) {
          totalCount
          nodes {
            stargazerCount
            diskUsage
          }
        }
        pullRequests {
          totalCount
        }
        contributionsCollection {
          totalCommitContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """ % USERNAME
    
    result = run_query(query)
    user_data = result['data']['user']
    
    # Extract last 7 days for Activity Flow
    all_days = []
    for week in user_data['contributionsCollection']['contributionCalendar']['weeks']:
        for day in week['contributionDays']:
            all_days.append(day)
    
    all_days.sort(key=lambda x: x['date'])
    last_7_days = all_days[-7:]
    
    stats = {
        'total_repos': user_data['repositories']['totalCount'],
        'total_stars': sum(repo['stargazerCount'] for repo in user_data['repositories']['nodes']),
        'total_prs': user_data['pullRequests']['totalCount'],
        'total_commits': user_data['contributionsCollection']['totalCommitContributions'],
        'current_streak': calculate_streak(user_data['contributionsCollection']['contributionCalendar']['weeks']),
        'weekly_activity': [day['contributionCount'] for day in last_7_days],
        'total_disk_kb': sum(repo['diskUsage'] for repo in user_data['repositories']['nodes'])
    }
    return stats

def calculate_streak(weeks):
    days = []
    for week in weeks:
        for day in week['contributionDays']:
            days.append(day)
    
    days.sort(key=lambda x: x['date'], reverse=True)
    
    current_streak = 0
    today = datetime.now().date()
    
    for i, day in enumerate(days):
        date = datetime.strptime(day['date'], '%Y-%m-%d').date()
        count = day['contributionCount']
        
        if date == today and count == 0:
            continue
            
        if count > 0:
            current_streak += 1
        else:
            if date < today:
                break
                
    return current_streak

def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)

def update_html_file(file_path, replacements):
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    modified = False
    for name, (pattern, value) in replacements.items():
        new_content, count = re.subn(pattern, value, content)
        if count > 0:
            print(f"  [+] Updated {name}: {count} match(es) replaced.")
            content = new_content
            modified = True
        else:
            print(f"  [-] Failed to update {name}: No matches found for pattern.")

    if modified:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Successfully updated {file_path}")
    else:
        print(f"No changes made to {file_path}")

def main():
    if not GITHUB_TOKEN:
        print("Error: GH_TOKEN not found in environment variables.")
        return

    print(f"Fetching data for {USERNAME}...")
    try:
        stats = fetch_github_data()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print(f"Stats fetched: {stats}")

    # Estimate Lines: Disk usage (KB) * 50 lines/KB as a realistic proxy, plus commit weight
    estimated_lines = (stats['total_disk_kb'] * 40) + (stats['total_commits'] * 100)

    # Prepare replacements for primary_stats.html
    primary_stats_replacements = {
        'total_commits': (r'(TOTAL_COMMITS</p>.*?<p class="text-\[120px\][^>]*>).*?(</p>)', rf'\g<1>{stats["total_commits"]:,}\g<2>'),
        'current_streak': (r'(Current_Streak</p>\s*<p class="text-6xl font-black leading-none">).*?(<span class="text-2xl ml-1">DAYS</span></p>)', rf'\g<1>{stats["current_streak"]}\g<2>'),
        'total_repos': (r'(Total_Repos</p>\s*<p class="text-6xl font-black leading-none">).*?(</p>)', rf'\g<1>{stats["total_repos"]}\g<2>')
    }

    # Prepare replacements for analytics.html
    # Scale activity bars: Max activity in the week sets 90% height
    max_act = max(stats['weekly_activity']) if max(stats['weekly_activity']) > 0 else 1
    scaled_heights = [int((val / max_act) * 90) or 5 for val in stats['weekly_activity']]
    
    analytics_replacements = {
        'total_stars': (r'(Stars: ).*?(</h4>)', rf'\g<1>{format_number(stats["total_stars"])}\g<2>'),
        'total_prs': (r'(PRs: ).*?(</h4>)', rf'\g<1>{stats["total_prs"]}\g<2>'),
        'total_lines': (r'(Total_Lines_Committed</p>\s*</div>\s*<p class="text-7xl[^>]*>).*?(</p>)', rf'\g<1>{format_number(estimated_lines)}+\g<2>')
    }
    
    # Add bars replacements (M, T, W, T, F, S, S)
    # We'll use a specific replacement for the activity flow grid children
    # This is slightly more complex with regex, let's find the grid and replace the h-[] classes
    
    with open('sections/analytics.html', 'r') as f:
        ana_content = f.read()
    
    # Find the activity flow grid
    grid_pattern = r'(<div class="grid grid-cols-7 gap-3 h-48 items-end px-2">)(.*?)(</div>)'
    match = re.search(grid_pattern, ana_content, re.DOTALL)
    if match:
        grid_start, grid_inner, grid_end = match.groups()
        # Find all divs with h-[] classes inside the grid
        bar_pattern = r'(<div class="[^"]*h-\[).*?(\%?\][^"]*")'
        bars = re.findall(bar_pattern, grid_inner)
        
        new_inner = grid_inner
        for i, val in enumerate(scaled_heights):
            if i < len(bars):
                # Replace the i-th bar's height
                # Using a targeted replace for the i-th occurrence is tricky with regex, 
                # let's do it sequentially
                target = bars[i][0] + r'.*?' + bars[i][1]
                new_inner = re.sub(target, f'{bars[i][0]}{val}{bars[i][1]}', new_inner, count=1)
        
        ana_content = ana_content.replace(grid_inner, new_inner)
        with open('sections/analytics.html', 'w') as f:
            f.write(ana_content)
        print("  [+] Updated Activity Flow bar chart.")

    print("Updating HTML files...")
    update_html_file('sections/primary_stats.html', primary_stats_replacements)
    update_html_file('sections/analytics.html', analytics_replacements)
    print("Done!")

if __name__ == "__main__":
    main()
