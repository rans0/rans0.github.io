import os
import re
import requests
from datetime import datetime, timedelta

# Constants
GITHUB_TOKEN = os.getenv('GH_TOKEN')

GRAPHQL_URL = 'https://api.github.com/graphql'
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def run_query(query, variables=None):
    response = requests.post(GRAPHQL_URL, json={'query': query, 'variables': variables}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with code {response.status_code}. {query}")

def fetch_github_data():
    # 1. Fetch Basic Info and First Batch of Repositories
    query = """
    query($cursor: String) {
      viewer {
        login
        createdAt
        repositories(first: 100, ownerAffiliations: OWNER, after: $cursor) {
          totalCount
          nodes {
            stargazerCount
            diskUsage
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
        pullRequests {
          totalCount
        }
        contributionsCollection {
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
    """
    
    result = run_query(query)
    viewer_data = result['data']['viewer']
    
    total_repos = viewer_data['repositories']['totalCount']
    total_stars = sum(repo['stargazerCount'] for repo in viewer_data['repositories']['nodes'])
    total_disk_kb = sum(repo['diskUsage'] for repo in viewer_data['repositories']['nodes'])
    total_prs = viewer_data['pullRequests']['totalCount']
    
    # Handle Repository Pagination
    has_next_page = viewer_data['repositories']['pageInfo']['hasNextPage']
    cursor = viewer_data['repositories']['pageInfo']['endCursor']
    
    while has_next_page:
        paginated_query = """
        query($cursor: String) {
          viewer {
            repositories(first: 100, ownerAffiliations: OWNER, after: $cursor) {
              nodes {
                stargazerCount
                diskUsage
              }
              pageInfo {
                hasNextPage
                endCursor
              }
            }
          }
        }
        """
        paginated_result = run_query(paginated_query, variables={"cursor": cursor})
        repo_nodes = paginated_result['data']['viewer']['repositories']['nodes']
        total_stars += sum(repo['stargazerCount'] for repo in repo_nodes)
        total_disk_kb += sum(repo['diskUsage'] for repo in repo_nodes)
        
        has_next_page = paginated_result['data']['viewer']['repositories']['pageInfo']['hasNextPage']
        cursor = paginated_result['data']['viewer']['repositories']['pageInfo']['endCursor']

    # 2. Calculate All-Time Commits
    start_year = datetime.strptime(viewer_data['createdAt'], '%Y-%m-%dT%H:%M:%SZ').year
    current_year = datetime.now().year
    total_commits = 0
    
    for year in range(start_year, current_year + 1):
        year_query = """
        query($from: DateTime, $to: DateTime) {
          viewer {
            contributionsCollection(from: $from, to: $to) {
              totalCommitContributions
            }
          }
        }
        """
        # Define time range for the year
        start_date = f"{year}-01-01T00:00:00Z"
        if year == current_year:
            end_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            end_date = f"{year}-12-31T23:59:59Z"
            
        year_result = run_query(year_query, variables={"from": start_date, "to": end_date})
        total_commits += year_result['data']['viewer']['contributionsCollection']['totalCommitContributions']

    # Extract last 7 days for Activity Flow (from the first query's collection)
    all_days = []
    for week in viewer_data['contributionsCollection']['contributionCalendar']['weeks']:
        for day in week['contributionDays']:
            all_days.append(day)
    
    all_days.sort(key=lambda x: x['date'])
    last_7_days = all_days[-7:]
    
    stats = {
        'total_repos': total_repos,
        'total_stars': total_stars,
        'total_prs': total_prs,
        'total_commits': total_commits,
        'current_streak': calculate_streak(viewer_data['contributionsCollection']['contributionCalendar']['weeks']),
        'weekly_activity': [day['contributionCount'] for day in last_7_days],
        'total_disk_kb': total_disk_kb,
        'total_contributions': viewer_data['contributionsCollection']['contributionCalendar']['totalContributions']
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

    print("Fetching comprehensive GitHub data...")
    try:
        stats = fetch_github_data()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print(f"Stats fetched: {stats}")

    # Estimate Lines: Disk usage (KB) * 40 lines/KB as a realistic proxy, plus commit weight
    estimated_lines = (stats['total_disk_kb'] * 40) + (stats['total_commits'] * 100)
    
    # Calculate average monthly contributions (this year so far)
    current_month = datetime.now().month
    avg_monthly = int(stats['total_contributions'] / current_month) if current_month > 0 else stats['total_contributions']

    # Prepare replacements for primary_stats.html
    primary_stats_replacements = {
        'total_commits': (r'(?s)(TOTAL_COMMITS\s*</p>.*?<p [^>]*class="[^"]*text-\[120px\][^"]*"[^>]*>)\s*.*?\s*(</p>)', rf'\g<1>{stats["total_commits"]:,}\g<2>'),
        'current_streak': (r'(?s)(Current_Streak\s*</p>\s*<p [^>]*class="[^"]*text-[56]xl[^"]*"[^>]*>)\s*.*?\s*(<span[^>]*>DAYS</span>\s*</p>)', rf'\g<1>{stats["current_streak"]}\g<2>'),
        'total_repos': (r'(?s)(Total_Repos\s*</p>\s*<p [^>]*class="[^"]*text-[56]xl[^"]*"[^>]*>)\s*.*?\s*(</p>)', rf'\g<1>{stats["total_repos"]}\g<2>')
    }

    # Prepare replacements for analytics.html
    max_act = max(stats['weekly_activity']) if max(stats['weekly_activity']) > 0 else 1
    scaled_heights = [int((val / max_act) * 90) or 5 for val in stats['weekly_activity']]
    
    analytics_replacements = {
        'total_stars': (r'(Stars: ).*?(\s*</h4>)', rf'\g<1>{format_number(stats["total_stars"])}\g<2>'),
        'total_prs': (r'(PRs: ).*?(\s*</h4>)', rf'\g<1>{stats["total_prs"]}\g<2>'),
        'total_lines': (r'(?s)(Total_Lines_Committed\s*</p>\s*</div>\s*<p [^>]*class="[^"]*text-[67]xl[^"]*"[^>]*>)\s*.*?\s*(</p>)', rf'\g<1>{format_number(estimated_lines)}+\g<2>'),
        'avg_monthly': (r'(?s)(<p [^>]*class="[^"]*text-[34]xl[^"]*"[^>]*>)\s*.*?\s*(</p>\s*<p [^>]*>Avg_Monthly</p>)', rf'\g<1>{avg_monthly}\g<2>')
    }
    
    # Update bars manually in analytics.html content
    try:
        with open('sections/analytics.html', 'r') as f:
            ana_content = f.read()
        
        grid_pattern = r'(<div class="grid grid-cols-7 gap-3 h-48 items-end px-2">)(.*?)(</div>)'
        match = re.search(grid_pattern, ana_content, re.DOTALL)
        if match:
            grid_start, grid_inner, grid_end = match.groups()
            bar_div_pattern = r'(<div class="[^"]*h-\[).*?(\%?\][^"]*")'
            
            bar_index = 0
            def bar_replacer(m):
                nonlocal bar_index
                if bar_index < len(scaled_heights):
                    h = scaled_heights[bar_index]
                    bar_index += 1
                    return f'{m.group(1)}{h}{m.group(2)}'
                return m.group(0)

            new_inner = re.sub(bar_div_pattern, bar_replacer, grid_inner)
            ana_content = ana_content.replace(grid_inner, new_inner)
            print(f"  [+] Updated Activity Flow bar chart with heights: {scaled_heights}")
            with open('sections/analytics.html', 'w') as f:
                f.write(ana_content)
    except FileNotFoundError:
        print("Warning: sections/analytics.html not found.")

    print("Updating HTML files...")
    update_html_file('sections/primary_stats.html', primary_stats_replacements)
    update_html_file('sections/analytics.html', analytics_replacements)
    print("Done!")

if __name__ == "__main__":
    main()
