# Online Trivia Game

A real-time multiplayer trivia game supporting up to 100 players with admin controls.

## Features

- **Multiplayer Support**: Up to 100 concurrent players
- **Real-time Gameplay**: WebSocket-based real-time communication
- **Admin Panel**: Game creation, management, and control
- **3 Rounds**: 15 questions each, increasing point values
- **Voting System**: Players vote to eliminate incorrect answers
- **Score Tracking**: Automatic scoring and elimination at 10 points
- **Read-only Mode**: Eliminated players can still watch

## File Locations

All trivia game files are located in:
```
c:\Users\jamfog02\OneDrive - Robert Half\PythonFiles\trivia_game\
```

## Linux Installation

### 1. Copy Files to Linux Server
```bash
# Create directory
mkdir ~/trivia_game
cd ~/trivia_game

# Copy all files from Windows to this directory:
# - app.py (RDS version)
# - app_dynamodb.py (DynamoDB version) 
# - requirements.txt
# - setup_rds.py
# - setup_dynamodb.py
# - admin_game.html
# - templates/ folder with all HTML files
# - README.md
# - README_AWS.md
```

### 2. Install System Dependencies
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 3. Create Virtual Environment
```bash
python3 -m venv trivia_env
source trivia_env/bin/activate
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure AWS (for DynamoDB - Recommended)
```bash
# Install AWS CLI
sudo apt install awscli

# Configure credentials
aws configure
```

### 6. Setup Database
```bash
# For DynamoDB (Recommended)
python3 setup_dynamodb.py
python3 setup_questions.py

# OR for RDS (if preferred)
python3 setup_rds.py
```

### 7. Run the Application
```bash
# DynamoDB version (Recommended)
python3 app_dynamodb.py

# OR RDS version
python3 app.py
```

### 8. Access the Game
- Main page: http://your-server-ip:5000
- Admin login: http://your-server-ip:5000/admin

### 9. Production Deployment
```bash
# Install gunicorn
pip install gunicorn eventlet

# Run in production
gunicorn --worker-class eventlet -w 1 app_dynamodb:app --bind 0.0.0.0:5000
```

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`

## Game Rules

1. **3 Rounds** with 15 questions each
2. **30 seconds** per question
3. **Point System**:
   - Round 1: 1 point per vote
   - Round 2: 2 points per vote  
   - Round 3: 4 points per vote
4. **Maximum 4 points per round**
5. **Elimination at 10 total points**
6. **Read-only mode** for eliminated players

## How to Play

### For Administrators:
1. Login at `/admin`
2. Create a new game with name and password
3. Share game ID and password with players
4. Monitor players in the admin panel
5. Start the game when ready

### For Players:
1. Go to main page
2. Enter game ID, password, and your name
3. Wait in lobby for game to start
4. Answer questions within 30 seconds
5. Vote to eliminate incorrect players
6. Try to avoid elimination!

## Technical Details

- **Backend**: Flask + SocketIO
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript
- **Real-time**: WebSocket communication
- **Concurrent Games**: Multiple games can run simultaneously

## File Structure

```
trivia_game/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── trivia.db          # SQLite database (auto-created)
├── templates/         # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── game_lobby.html
│   └── game_play.html
└── admin_game.html    # Admin game control panel
```

## Complete File List to Copy

```
trivia_game/
├── app.py                    # RDS version
├── app_dynamodb.py          # DynamoDB version (recommended)
├── requirements.txt         # Python dependencies
├── setup_rds.py            # RDS setup script
├── setup_dynamodb.py       # DynamoDB setup script
├── setup_questions.py      # Question database setup
├── admin_game.html         # Admin control panel
├── README.md               # Basic documentation
├── README_AWS.md           # AWS setup guide
└── templates/              # HTML templates folder
    ├── base.html
    ├── index.html
    ├── admin_login.html
    ├── admin_dashboard.html
    ├── game_lobby.html
    └── game_play.html
```

## Database Schema

### DynamoDB Tables:
- **`trivia_admins`**: Admin user credentials
- **`trivia_questions`**: Runtime trivia questions (45+ questions)
- **`trivia_questions_source`**: Master question repository
- **`trivia_games`**: Game configurations and passwords

### Question Categories:
- Geography, Science, History, Literature, General Knowledge

The system automatically creates comprehensive questions and a default admin user on first run."# trivia_game" 
