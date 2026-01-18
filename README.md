# Brutalist GitHub Stats Dashboard (rans0.github.io)

A personal dashboard with a **Brutalist Ink Splatter** aesthetic that displays GitHub statistics in real-time and automatically. This dashboard is designed to provide a dynamic and modern visualization of developer performance.

## 🚀 Key Features

- **Modular Architecture**: Uses a *dynamic section loader* system to separate HTML components (Header, Hero, Stats, Social, etc.) for easy management.
- **Fully Automated Stats**: Statistics are automatically updated daily using GitHub Actions and Python.
- **Dynamic Activity Flow**: A weekly bar chart that adjusts its height according to the actual number of commits in the last 7 days.
- **Responsive Design**: Optimized for both desktop and mobile devices with a touch of brutalist animation.

## 📊 Data & Automation

All numbers and charts on this dashboard are pulled directly from the GitHub GraphQL API using a Python script (`scripts/update_stats.py`).

| Data | Description | Automation Logic |
| :--- | :--- | :--- |
| **Total Commits** | Total lifetime commits of the profile. | Retrieved from `totalCommitContributions` across all years. |
| **Current Streak** | Number of consecutive days with commits. | Calculated from the contribution calendar (last 365 days). |
| **Total Repos** | Number of repositories owned. | Retrieved from `repositories.totalCount`. |
| **Stars & PRs** | Accumulated stars and Pull Requests. | Automatic summation from all repository metadata. |
| **Activity Flow** | Monday - Sunday bar chart. | Displays commit trends for the last 7 days proportionally. |
| **Lines Committed** | Estimated volume of code worked on. | Calculated using the formula: `(Disk Usage KB * 40) + (Commits * 100)`. |
| **AVG Monthly** | Average monthly contributions. | Total contributions this year divided by the current month. |

## 🛠 Tech Stack

- **Frontend**: HTML5, Vanilla CSS (Brutalist Style), Tailwind CSS.
- **Automation**: Python 3.x, GitHub Actions (Workflow).
- **API**: GitHub GraphQL API v4.
- **Hosting**: GitHub Pages.

## ⚙️ How to Run Locally

Since this project uses the `fetch` feature to load HTML modules, you cannot simply open the `index.html` file. You must use a local web server:

```bash
# Using Python
python3 -m http.server 8000
```
Then open `localhost:8000` in your browser.

## 🤖 Setting Up Automation (GitHub Actions)

To enable automatic updates every 12 AM (UTC/GMT+7):

1. Create a **Personal Access Token (PAT)** in your GitHub account with `repo` and `user` scopes.
2. Go to repository **Settings** > **Secrets and variables** > **Actions**.
3. Add a **New repository secret** named `GH_TOKEN` and fill it with your PAT token.
4. Ensure **Settings** > **Pages** > **Build and deployment** > Source is set to **"GitHub Actions"**.

---
*Built with code, logic, and a bit of chaos.* ✨
