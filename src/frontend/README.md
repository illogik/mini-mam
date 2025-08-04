# Mini-MAM Frontend

A React TypeScript application that integrates with the Mini-MAM microservices architecture, specifically the Search and Assets services.

## Features

- **Search Page**: Search through assets with real-time suggestions
- **Assets Page**: Browse, create, edit, and delete assets
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean and intuitive user interface
- **Error Handling**: Comprehensive error handling and user feedback

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Running Mini-MAM microservices (see main README.md)

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will open in your browser at `http://localhost:3000`.

### Environment Variables

Create a `.env` file in the frontend directory to configure the API URL:

```
REACT_APP_API_URL=http://localhost:80
```

If not set, the default API URL is `http://localhost:80` (nginx proxy).

### Access URLs

- **Frontend**: `http://localhost:80/` (served from root)
- **API Gateway**: `http://localhost:80/api/` (all API endpoints)
- **Assets API**: `http://localhost:80/api/assets/`
- **Files API**: `http://localhost:80/api/files/`
- **Search API**: `http://localhost:80/api/search/`
- **Transcode API**: `http://localhost:80/api/transcode/`

## Usage

### Search Page

- Enter search terms in the search box
- Get real-time search suggestions as you type
- View search results with relevance scores
- Filter results by type and other criteria

### Assets Page

- Browse assets in a responsive grid layout
- Create new assets with the "Add Asset" button
- Edit existing assets by clicking the "Edit" button
- Delete assets with confirmation dialog
- Navigate through pages of assets

## API Integration

The frontend communicates with the following microservices:

- **Search Service**: `/search/` - Search functionality and suggestions
- **Assets Service**: `/assets/` - Asset management (CRUD operations)

All requests go through the nginx reverse proxy on port 80.

## Available Scripts

- `npm start` - Start the development server
- `npm run build` - Build the app for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (not recommended)

## Project Structure

```
src/
├── components/          # React components
│   ├── Header.tsx      # Navigation header
│   ├── SearchPage.tsx  # Search functionality
│   ├── AssetsPage.tsx  # Asset management
│   └── *.css          # Component styles
├── services/           # API services
│   └── api.ts         # API client and services
├── types/             # TypeScript type definitions
│   └── api.ts         # API response types
├── App.tsx            # Main application component
└── App.css            # Global styles
```

## Development

The application uses:
- **React 18** with TypeScript
- **Axios** for HTTP requests
- **CSS** for styling (no external UI libraries)
- **Modern ES6+** features

## Troubleshooting

1. **CORS Issues**: Ensure the microservices are running and nginx is properly configured
2. **API Connection**: Check that the `REACT_APP_API_URL` environment variable is correct
3. **Build Issues**: Clear node_modules and reinstall dependencies

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test thoroughly before submitting changes
4. Update documentation as needed
