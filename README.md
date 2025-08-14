# Lifelink

A sophisticated memory and journal application with AI capabilities, combining a React frontend with a Python/FastAPI backend.

## Project Structure

```
lifelink/
├── frontend/           # React + Vite frontend application
│   ├── src/           # React components and source code
│   ├── public/        # Static assets
│   └── ...            # Frontend configuration files
├── backend/           # Python FastAPI backend
│   ├── main.py        # FastAPI application
│   ├── models.py      # Data models
│   ├── config.py      # Configuration
│   └── ...            # Backend files
└── README.md          # This file
```

## Features

- **Memory Management**: Store and organize personal memories
- **AI-Powered Insights**: Analyze memories with AI for patterns and insights
- **Audio Transcription**: Convert audio recordings to text using Whisper
- **Semantic Search**: Find memories using natural language queries
- **Timeline Visualization**: View memories chronologically
- **Mood Tracking**: Track and visualize mood patterns over time
- **Advanced Search**: Complex filtering and search capabilities

## Technology Stack

### Frontend
- React 19.1.0 with Vite 7.0.4
- Material-UI for components
- Tailwind CSS for styling
- Chart.js for data visualization
- Axios for API communication

### Backend
- FastAPI with Python
- MongoDB for data storage
- OpenAI Whisper for audio transcription
- LangChain for AI features
- ChromaDB for vector search
- JWT authentication

## Getting Started

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

For more detailed information:
- Frontend documentation: [frontend/README.md](frontend/README.md)
- Backend setup: See backend directory

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
