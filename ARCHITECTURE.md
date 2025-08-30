# Trivia Game System Architecture

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Web Browser   │    │   Admin Panel   │
│   (Players)     │    │   (Players)     │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │         WebSocket    │         HTTP         │
          └──────────┬───────────┴──────────┬───────────┘
                     │                      │
              ┌──────▼──────────────────────▼──────┐
              │        Flask Application           │
              │      (Python + SocketIO)           │
              └──────┬───────────────────────┬─────┘
                     │                       │
                     ▼                       ▼
              ┌─────────────┐         ┌─────────────┐
              │  DynamoDB   │         │  In-Memory  │
              │  (Persist)  │         │ Game State  │
              └─────────────┘         └─────────────┘
```

## Component Architecture

### 1. Frontend Layer
- **Technology**: HTML5, CSS3, JavaScript, Socket.IO Client
- **Components**:
  - Player Interface (`game_lobby.html`, `game_play.html`)
  - Admin Interface (`admin_dashboard.html`, `admin_game.html`)
  - Authentication (`admin_login.html`)
- **Communication**: WebSocket for real-time, HTTP for REST APIs

### 2. Backend Layer
- **Technology**: Python Flask + Flask-SocketIO
- **Components**:
  - **Web Server**: Flask application server
  - **Real-time Engine**: SocketIO for WebSocket handling
  - **Game Logic**: Python classes and functions
  - **Session Management**: Flask sessions for admin auth

### 3. Data Layer
- **Persistent Storage**: AWS DynamoDB
  - `trivia_admins` - Admin credentials
  - `trivia_questions` - Question bank
  - `trivia_games` - Game configurations
- **In-Memory Storage**: Python dictionaries
  - Active game states
  - Player connections
  - Real-time game data

## Data Flow

### Game Creation Flow
```
Admin Dashboard → HTTP POST → Flask Route → DynamoDB Write → In-Memory State
```

### Player Join Flow
```
Player Browser → WebSocket Connect → Flask-SocketIO → Game State Update → Broadcast to Room
```

### Question Flow
```
Timer Trigger → Question Load → WebSocket Broadcast → Player Answers → Vote Processing → Next Question
```

## Scalability Architecture

### Current (Single Instance)
```
Load Balancer → Single Flask Instance → DynamoDB
```

### Scalable (Multi-Instance)
```
                    ┌─ Flask Instance 1 ─┐
Load Balancer ──────┼─ Flask Instance 2 ─┼─── DynamoDB
                    └─ Flask Instance N ─┘
                            │
                    ┌───────▼───────┐
                    │  Redis/ElastiCache │
                    │  (Session Store)   │
                    └───────────────────┘
```

## Security Architecture

### Authentication Flow
```
Admin Login → Password Hash → Session Cookie → Route Protection
```

### Game Access Control
```
Player Join → Game ID + Password → Room Assignment → Isolated Game State
```

## Deployment Architecture

### Development
```
Local Machine → Python Flask → Local DynamoDB/SQLite
```

### Production (AWS)
```
Internet → ALB → EC2/ECS → DynamoDB
                    │
                    ▼
              CloudWatch Logs
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | HTML/CSS/JS | User Interface |
| Real-time | Socket.IO | WebSocket Communication |
| Backend | Python Flask | Web Framework |
| Database | AWS DynamoDB | Data Persistence |
| Hosting | EC2/ECS | Application Server |
| Load Balancer | ALB | Traffic Distribution |
| Monitoring | CloudWatch | Logging & Metrics |

## Performance Characteristics

- **Concurrent Players**: Up to 100 per game
- **Response Time**: <100ms for game actions
- **Database**: Single-digit millisecond DynamoDB latency
- **Memory Usage**: ~50MB per active game
- **Network**: WebSocket for real-time, HTTP for admin

## Fault Tolerance

### Single Points of Failure
- Flask application instance
- DynamoDB region availability

### Mitigation Strategies
- Auto Scaling Groups for EC2
- DynamoDB Multi-AZ replication
- Application Load Balancer health checks
- CloudWatch monitoring and alerts

## Security Considerations

- **Data Encryption**: HTTPS/WSS in transit, DynamoDB encryption at rest
- **Authentication**: Session-based admin auth, game password protection
- **Network**: VPC security groups, private subnets for backend
- **Access Control**: IAM roles for AWS services, least privilege principle