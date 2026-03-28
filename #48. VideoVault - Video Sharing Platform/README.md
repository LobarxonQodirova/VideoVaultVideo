# VideoVault - Video Sharing Platform

A production-grade video sharing platform built with Django REST Framework and React, featuring video upload and transcoding, channels, playlists, comments, subscriptions, watch history, recommendations, trending, live streaming concepts, and a full creator studio.

## Architecture

```
+-------------------+       +-------------------+       +-------------------+
|   React Frontend  | <---> |   Nginx Reverse   | <---> |  Django REST API   |
|   (Port 3000)     |       |   Proxy (Port 80) |       |   (Port 8000)     |
+-------------------+       +-------------------+       +-------------------+
                                                                |
                        +-------------------+       +-------------------+
                        |   Redis           | <---> |   Celery Workers  |
                        |   (Cache/Broker)  |       |   (Transcoding)   |
                        +-------------------+       +-------------------+
                                                                |
                                                    +-------------------+
                                                    |   PostgreSQL      |
                                                    |   (Database)      |
                                                    +-------------------+
```

## Features

- **User Management**: Registration, authentication (JWT), profiles, avatars
- **Channels**: Create/manage channels, channel customization, subscriber counts
- **Video Upload**: Chunked uploads, multiple format support, thumbnail generation
- **Video Transcoding**: Celery-based async transcoding to multiple resolutions (360p, 480p, 720p, 1080p)
- **Playlists**: Create, edit, reorder, public/private/unlisted playlists
- **Comments**: Threaded comments with replies, likes, pinning
- **Interactions**: Like/dislike system on videos and comments
- **Subscriptions**: Subscribe to channels, subscription feed
- **Watch History**: Track viewing history, watch progress, resume playback
- **Watch Later**: Save videos for later viewing
- **Recommendations**: Content-based and collaborative filtering recommendation engine
- **Trending**: Algorithm-based trending page with time decay
- **Analytics**: View counts, watch time, audience retention, channel analytics
- **Creator Studio**: Dashboard for creators to manage content and view analytics
- **Content Moderation**: Report system, moderation queue
- **Search**: Full-text search across videos, channels, playlists
- **Live Streaming Concept**: Stream key management, live chat foundation

## Tech Stack

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Backend API     | Django 5.x + Django REST Framework  |
| Frontend        | React 18 + Redux Toolkit           |
| Database        | PostgreSQL 16                       |
| Cache/Broker    | Redis 7                             |
| Task Queue      | Celery 5.x                         |
| Reverse Proxy   | Nginx                               |
| Containerization| Docker + Docker Compose             |
| Authentication  | JWT (SimpleJWT)                     |
| Video Player    | Video.js                            |
| Charts          | Chart.js / react-chartjs-2          |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/your-username/videovault.git
cd videovault
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your preferred settings (defaults work for development).

4. Build and start the containers:
```bash
docker-compose up --build
```

5. Run database migrations:
```bash
docker-compose exec backend python manage.py migrate
```

6. Create a superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

7. Access the application:
   - Frontend: http://localhost
   - API: http://localhost/api/
   - Admin: http://localhost/admin/
   - API Docs: http://localhost/api/docs/

### Development Setup (without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend

```bash
cd frontend
npm install
npm start
```

#### Celery Worker

```bash
cd backend
celery -A config worker -l info
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Obtain JWT tokens
- `POST /api/auth/refresh/` - Refresh JWT token
- `GET  /api/auth/me/` - Current user profile

### Videos
- `GET    /api/videos/` - List videos (with filtering, search, ordering)
- `POST   /api/videos/` - Upload a new video
- `GET    /api/videos/{id}/` - Video details
- `PUT    /api/videos/{id}/` - Update video
- `DELETE /api/videos/{id}/` - Delete video
- `GET    /api/videos/trending/` - Trending videos
- `GET    /api/videos/feed/` - Subscription feed

### Channels
- `GET    /api/channels/` - List channels
- `POST   /api/channels/` - Create channel
- `GET    /api/channels/{handle}/` - Channel details
- `POST   /api/channels/{id}/subscribe/` - Subscribe/unsubscribe

### Playlists
- `GET    /api/playlists/` - List playlists
- `POST   /api/playlists/` - Create playlist
- `POST   /api/playlists/{id}/add_video/` - Add video to playlist
- `DELETE /api/playlists/{id}/remove_video/` - Remove video

### Interactions
- `POST   /api/interactions/like/` - Like a video
- `POST   /api/interactions/dislike/` - Dislike a video
- `GET    /api/interactions/comments/` - List comments
- `POST   /api/interactions/comments/` - Create comment

### Watch History
- `GET    /api/history/` - Watch history
- `POST   /api/history/progress/` - Update watch progress
- `GET    /api/history/watch-later/` - Watch later list

### Analytics
- `GET    /api/analytics/video/{id}/` - Video analytics
- `GET    /api/analytics/channel/{id}/` - Channel analytics

### Recommendations
- `GET    /api/recommendations/` - Personalized recommendations
- `GET    /api/recommendations/related/{video_id}/` - Related videos

## Project Structure

```
videovault/
├── backend/
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   ├── apps/
│   │   ├── accounts/
│   │   ├── videos/
│   │   ├── interactions/
│   │   ├── playlists/
│   │   ├── watch_history/
│   │   ├── recommendations/
│   │   ├── analytics/
│   │   └── reports/
│   ├── utils/
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/
│   │   ├── hooks/
│   │   └── styles/
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

## Environment Variables

See `.env.example` for all available configuration options.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License.
