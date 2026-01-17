import os
import re
import requests
from datetime import datetime, timedelta

# Constants
GITHUB_TOKEN = os.getenv('GH_TOKEN')
USERNAME = 'rans0'  # Hardcoded as per implementation plan context

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
    
    stats = {
        'total_repos': user_data['repositories']['totalCount'],
        'total_stars': sum(repo['stargazerCount'] for repo in user_data['repositories']['nodes']),
        'total_prs': user_data['pullRequests']['totalCount'],
        'total_commits': user_data['contributionsCollection']['totalCommitContributions'],
        'current_streak': calculate_streak(user_data['contributionsCollection']['contributionCalendar']['weeks'])
    }
    return stats

def calculate_streak(weeks):
    # Flatten days and sort by date descending
    days = []
    for week in weeks:
        for day in week['contributionDays']:
            days.append(day)
    
    days.sort(key=lambda x: x['date'], reverse=True)
    
    current_streak = 0
    today = datetime.now().date()
    # Find start point (skip today if no commits yet, but checking yesterday)
    
    for i, day in enumerate(days):
        date = datetime.strptime(day['date'], '%Y-%m-%d').date()
        count = day['contributionCount']
        
        # If it's today and count is 0, we don't break yet, just look at previous days
        if date == today and count == 0:
            continue
            
        if count > 0:
            current_streak += 1
        else:
            # If we miss a day (and it's not today), the streak is broken
            if date < today:
                break
                
    return current_streak

def format_number(num):
    if num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)

def update_html_file(file_path, replacements):
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        content = f.read()

    for pattern, value in replacements.items():
        content = re.sub(pattern, value, content)

    with open(file_path, 'w') as f:
        f.write(content)

def main():
    if not GITHUB_TOKEN:
        print("Error: GH_TOKEN not found in environment variables.")
        return

    print(f"Fetching data for {USERNAME}...")
    stats = fetch_github_data()
    print(f"Stats fetched: {stats}")

    # Prepare replacements for primary_stats.html
    # 1. Total Commits
    # 2. Current Streak
    # 3. Total Repos
    primary_stats_replacements = {
        r'(<p class="text-\[120px\][^>]*>).*?(</p>)': rf'\1{stats["total_commits"]:,}\2',
        r'(<p class="text-6xl font-black leading-none">).*?(<span class="text-2xl ml-1">DAYS</span></p>)': rf'\1{stats["current_streak"]}\2',
        r'(<p class="text-6xl font-black leading-none">)(?!\d+\s*<span).*?(</p>)': rf'\1{stats["total_repos"]}\2'
    }

    # Prepare replacements for analytics.html
    # 1. Stars
    # 2. PRs
    analytics_replacements = {
        r'(<h4 class="text-2xl font-black uppercase leading-tight">Stars: ).*?(</h4>)': rf'\1{format_number(stats["total_stars"])}\2',
        r'(<h4 class="text-2xl font-black uppercase leading-tight">PRs: ).*?(</h4>)': rf'\1{stats["total_prs"]}\2'
    }

    print("Updating HTML files...")
    update_html_file('sections/primary_stats.html', primary_stats_replacements)
    update_html_file('sections/analytics.html', analytics_replacements)
    print("Done!")

if __name__ == "__main__":
    main()
