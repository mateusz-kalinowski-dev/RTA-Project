# Reddit Sentiment Analysis - Monolithic Version

A monolithic application for real-time Reddit data collection and sentiment analysis.

## Project Structure

This project is designed with a clean, modular architecture that's easier to maintain:

```
backend/
  |- app.py              # Main application entry point
  |- config.py           # Configuration management
  |- database.py         # Database connection utilities
  |- routes/             # API routes and Socket.IO events
  |   |- api_routes.py   # REST API endpoints
  |   |- socket_routes.py # Real-time Socket.IO events
  |- services/           # Business logic components
  |   |- reddit_collector.py # Reddit data collection
  |   |- sentiment_analyzer.py # Sentiment analysis
  |- models/             # Data models and schemas
frontend/
  |- src/                # React application source
  |   |- App.js          # Main React component
  |   |- index.js        # React entry point
  |- public/             # Static assets
```

## Architecture

The project follows a modular monolithic architecture:

1. **Backend (Flask)**:
   - Uses Flask as the web framework with Flask-RESTful for API endpoints
   - Implements real-time updates with Socket.IO
   - Background job scheduling with APScheduler
   - MongoDB for data storage
   - Sentiment analysis with HuggingFace Transformers
   - Reddit data collection with PRAW

2. **Frontend (React)**:
   - React with Material-UI for modern UI components
   - Real-time data visualization with Chart.js
   - WebSocket communication with Socket.IO client

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Reddit API credentials (client ID and secret)

### Setting Up Reddit API Access
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create an app" at the bottom
3. Fill in the details:
   - Name: RTA Data Collector (or any name you prefer)
   - Type: Script
   - Description: Collects data for sentiment analysis
   - About URL: (Can be left blank)
   - Redirect URI: http://localhost:8000 (or any URL, as we won't be using OAuth)
4. Click "Create app"
5. Note your client ID (the string under the app name) and client secret

### Configuration
1. Copy `env.example` to `.env`
2. Fill in the Reddit API credentials
3. Customize the list of subreddits to monitor and other settings

### Running the Project

1. Set up environment variables:
   ```
   cp env.example .env
   ```
2. Edit the `.env` file with your Reddit API credentials
3. Build and start all services:
   ```
   docker-compose up -d
   ```
4. Access the dashboard at http://localhost:3000

## API Endpoints

- `GET /health` - Health check
- `POST /api/data` - Send data to the processing pipeline
- `GET /api/results` - Get the latest analyzed results (supports filtering)

## Development

### Architecture Benefits

This monolithic approach provides several advantages:
- Simpler deployment and development setup
- Easier to debug and trace execution flow
- Reduced network overhead between components
- Cleaner, more maintainable code structure
- Module separation for easier testing

### Adding New Features

To add new features:
1. Add new services in the `services` directory
2. Register new routes in the `routes` directory
3. Update the frontend to display the new data

### Customizing Reddit Data Collection

You can customize the Reddit data collection by changing the following environment variables:
- `SUBREDDITS_TO_MONITOR`: Comma-separated list of subreddits to monitor
- `REDDIT_POLLING_INTERVAL`: How often to poll Reddit API for new data (in seconds)

## License

This project is licensed under the MIT License 