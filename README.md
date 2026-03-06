# GitHub Profile Analyzer

![Version](https://img.shields.io/badge/version-1.0.0-peach)
![Status](https://img.shields.io/badge/status-production--ready-success)
![Deployment](https://img.shields.io/badge/deployment-static--ready-brightgreen)
![API](https://img.shields.io/badge/API-GitHub%20REST-black)

---

## Tech Stack

![HTML5](https://img.shields.io/badge/HTML5-Markup-orange?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-styling-blue?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-logic-yellow?logo=javascript&logoColor=black)
![Chart.js](https://img.shields.io/badge/Chart.js-data%20visualization-red?logo=chartdotjs&logoColor=white)
![GitHub API](https://img.shields.io/badge/GitHub%20API-data%20source-black?logo=github)

---

## Overview

A modern, lightweight **developer analytics dashboard** that analyzes any GitHub profile and converts repository data into **clear insights, visual analytics, and developer metrics**.

The application runs entirely in the **browser with zero backend**, allowing instant analysis of GitHub profiles.

Simply open **index.html**, paste a GitHub profile, and generate a complete developer analytics report.

---

## Features

### Developer Profile Summary
Displays important GitHub profile information:

- Profile avatar  
- Username and bio  
- Followers and following  
- Public repositories  
- Account creation date  
- Direct profile link  

---

### Repository Insights
Automatic repository analysis including:

- Total repositories  
- Total forks  
- Most starred repository  
- Most recently updated repository  

---

### Programming Language Analytics

Analyzes languages used across repositories and displays them in a **clean pie chart visualization**.

---

### Developer Productivity Score

Custom scoring system:

Developer Score =  
(Stars × 2) + (Repositories × 3) + (Followers × 1)

Provides a quick indicator of **developer engagement and project popularity**.

---

### Repository Data Table

Clean tabular view displaying:

- Repository name  
- Programming language  
- Stars  
- Forks  
- Last updated date  

Each repository links directly to GitHub.

---

### Visual Analytics Dashboard

Interactive visualizations powered by **Chart.js** including:

- Language usage pie chart  
- Repository popularity bar chart  

---

## How to Use

1. Clone or download the repository.

2. Open the application by launching:

```
index.html
```

3. Enter a GitHub username or profile URL:

```
https://github.com/username
```

4. Click **Analyze**.

The dashboard will instantly generate a **complete GitHub profile report**.

---

## Project Structure

```
github-profile-analyzer
│
├── index.html
├── style.css
├── script.js
└── README.md
```

---

## GitHub API Endpoints Used

Profile Data

```
https://api.github.com/users/{username}
```

Repository Data

```
https://api.github.com/users/{username}/repos
```

Language Statistics

```
https://api.github.com/repos/{owner}/{repo}/languages
```

---

## Future Improvements

Potential upgrades:

- Contribution heatmap analytics  
- Repository quality scoring  
- Developer portfolio strength meter  
- AI developer profile summaries  
- Open-source contribution insights

## Disclaimer

This project is developed for educational and portfolio purposes.  
It uses publicly available data from the GitHub REST API and is not affiliated with or endorsed by GitHub.
