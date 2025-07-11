# DreamRankr 🏆

*Encouraging friendly competition in sports clubs through ranking systems*

## What is DreamRankr?

Ever realized how little you and the others in your sports club actually play against each other? Well I noticed and wanted to encourage more friendly duels, as in my experience it's one of the best ways to improve your skills. So I created DreamRankr!

DreamRankr is a Flask web app that can host multiple ranking lists, where players can challenge each other to rise to the top and foster a more competitive, engaging club environment.

## Features

### 🎯 Ranking Systems

**By Position**
- Players can only challenge those with higher rankings
- Example: Player A (rank 4) can challenge Player B (rank 2), but not vice versa
- Winners move up exactly one rank, regardless of defender's position
- Maintains traditional ladder-style competition

**By Points**
- Rewards active participation and discourages rank camping
- Every match completion = 1 point
- Every match win = +1 additional point (2 total)
- Encourages high-ranked players to keep playing

### 🎮 Player Engagement

**Lifetime Leaderboard**
- Global player statistics across all rankings
- Prevents tunnel vision from single ranking systems
- Shows overall club performance and activity

### 🔧 Administration Tools

**Permission System**
- **Trainer permissions**: Full administrative access
- **Viewer permissions**: Read-only access to rankings and stats

**Management Features**
- Automatic ranking period endings
- Players saved independently of rankings for easy importing
- Support for players participating in multiple rankings simultaneously

### 🔒 Security & Legal Compliance

**Data Protection**
- Password protection for all app access
- Built-in privacy terms editor using EasyMDE
- Compliant with strict data protection regulations

### 🛠️ Development Features

**Logging System**
- Thorough application logging for debugging and monitoring

## Planned Features

- **📚 Documentation Hub**: Central location for club documents, equipment manuals, tournament plans
- **📢 Global Messaging**: Broadcast important announcements to all players
- **🏆 Tournament Rankings**: Support for tournament-style competitions
- **⚡ Command Line Tools**: Advanced log analysis utilities
- **🔌 API & ESP32 Client**: Hardware integration and third-party access

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript with AI-assisted UI design (probably a hot mess)
- **Editor**: EasyMDE for markdown editing


## Development Disclosure

As this was my first Flask and Python project, I used AI to learn about the framework and to help create the UI. Nearly all backend logic is human-made (whether that is a good thing is up to you 😊).

The goal was to create a functional, useful tool for sports clubs while learning modern web development practices.

---

*Built with ❤️ for sports clubs everywhere, encouraged by the Dream Team RE*
