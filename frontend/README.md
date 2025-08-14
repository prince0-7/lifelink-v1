# Lifelink Frontend

This directory contains the frontend application for Lifelink, built with React and Vite.

## Directory Structure

```
frontend/
├── public/              # Static assets
│   └── vite.svg        # Vite logo
├── src/                # Source code
│   ├── ai/             # AI-related modules
│   │   └── AIManager.js (AI integration manager)
│   ├── assets/         # Images and static resources
│   │   └── react.svg   # React logo
│   ├── components/     # React components
│   │   ├── AdvancedSearch.jsx (188 lines) - Advanced search functionality
│   │   ├── AISettings.jsx (219 lines) - AI configuration interface
│   │   ├── MemoryCard.jsx (80 lines) - Memory display component
│   │   ├── MemoryInsights.jsx (265 lines) - Memory analysis and insights
│   │   ├── MemoryTimeline.jsx (137 lines) - Timeline visualization
│   │   └── MoodChart.jsx (52 lines) - Mood tracking charts
│   ├── services/       # API and external services
│   │   └── api.js      # API client for backend communication
│   ├── App.jsx         # Main application component (695 lines)
│   ├── App.css         # Application styles
│   ├── main.jsx        # Application entry point
│   └── index.css       # Global styles
├── node_modules/       # Dependencies
├── .gitignore          # Git ignore file
├── eslint.config.js    # ESLint configuration
├── index.html          # HTML entry point
├── package.json        # Project dependencies and scripts
├── package-lock.json   # Dependency lock file
└── vite.config.js      # Vite configuration

```

## Technology Stack

- **Framework**: React 19.1.0
- **Build Tool**: Vite 7.0.4
- **UI Library**: Material-UI (MUI) 7.2.0
- **Styling**: 
  - Tailwind CSS 4.1.11
  - Emotion (for styled components)
- **Charts**: Chart.js 4.5.0 with react-chartjs-2
- **HTTP Client**: Axios 1.11.0
- **Development Tools**:
  - ESLint for linting
  - PostCSS with Autoprefixer

## Component Classification

### Core Components
- **App.jsx**: Main application container, manages routing and global state

### Memory Management Components
- **MemoryCard.jsx**: Individual memory display component
- **MemoryTimeline.jsx**: Chronological visualization of memories
- **MemoryInsights.jsx**: Analytics and insights from memory data

### Feature Components
- **AdvancedSearch.jsx**: Complex search functionality for memories
- **AISettings.jsx**: Configuration interface for AI features
- **MoodChart.jsx**: Data visualization for mood tracking

### Service Layer
- **api.js**: Centralized API client for backend communication
- **AIManager.js**: AI feature integration and management

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Development

To start the frontend development server:

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:5173` (default Vite port).
