# GitHub Profile Analyzer

A clean, minimal, production-quality web application that analyzes any GitHub profile using the GitHub REST API. Built completely with frontend technologies, requiring no backend server.

## Features

- **Profile Summary**: Displays username, generic info, total followers, following, and public repositories.
- **Repository Highlights**: Highlights total repos, forks, most starred, and most recently updated repositories.
- **Programming Language Stats**: Extracts data from the GitHub API to showcase the most commonly used programming languages using a pie chart visualization.
- **Developer Productivity Score**: Unique scoring mechanism calculating developer capability based on repository count, stars, and followers.
- **Repository Data View**: Easy-to-read tabular format presenting popular and recent repositories.
- **Visual Analytics**: Interactive bar chart and pie chart using Chart.js.

## Screenshots

*(Placeholder: Add screenshots of the dashboard here)*

## How to use

1. Clone or download this project.
2. Open `index.html` directly in your web browser. No local server required!
3. Paste a GitHub profile URL or username into the input box and click **Analyze**.

## Tech Stack

- **HTML5**: Structured semantic layout.
- **Vanilla CSS**: Custom sleek CSS logic built around a unified UI design system (modern cards, soft shadows, custom variables).
- **Vanilla JavaScript**: ES6+ logic driving GitHub API fetching and DOM manipulation.
- **Chart.js**: Render charts cleanly from the client-side.

## GitHub API References Used

- Profile Info: `https://api.github.com/users/{username}`
- Repositories Info: `https://api.github.com/users/{username}/repos`
- Language Statistics: `https://api.github.com/repos/{owner}/{repo}/languages`

