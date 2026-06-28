# 🏴‍☠️ Treasure Runner - Web Edition

A browser-based dungeon crawler game where you navigate through rooms, collect treasures, and discover portals to new areas!

## 🎮 Play Online

**[Play Treasure Runner on GitHub Pages](https://codecraftsman2006.github.io/treasure-runner/)**

## Features

- 🗺️ **Multiple Rooms** - Explore interconnected dungeons
- 💎 **Treasure Collection** - Find and collect all treasures
- 🚪 **Portal System** - Use portals to travel between rooms
- 🎯 **Responsive Design** - Play on desktop, tablet, or mobile
- ⌨️ **Multiple Controls** - Keyboard (WASD/Arrows) or on-screen buttons

## How to Play

### Objective
Collect all treasures in the dungeon and escape!

### Controls
- **Arrow Keys** or **WASD** - Move your character (@)
- **">" Key** - Use a portal (stand on > and press)
- **"R" Key** - Reset the game

### Symbols
- `@` - Your character (Player)
- `#` - Wall (Impassable)
- `$` - Treasure (Collect these!)
- `>` - Portal (Use to travel between rooms)
- `.` - Empty floor

## Local Development

### Prerequisites
- Node.js 18+ 
- npm

### Setup

```bash
# Navigate to the web directory
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

The game will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

This creates an optimized build in the `dist/` folder.

## Architecture

### Frontend
- **React 18** - UI framework
- **Vite** - Modern build tool
- **CSS** - Custom styling

### Game Logic
- Pure JavaScript game engine
- State management for rooms, player, and treasures
- Real-time rendering and collision detection

### Deployment
- **GitHub Pages** - Automatic deployment on push to main
- **GitHub Actions** - Build pipeline configured in `.github/workflows/deploy.yml`

## Game Generation

The current version uses procedurally generated test rooms with:
- Random wall placement
- Pre-defined treasure locations
- Portal connections between rooms

Future versions can integrate the C-based backend for:
- Complex world generation
- Advanced puzzle mechanics
- Persistent save games

## Project Structure

```
treasure-runner/
├── web/                    # React web app
│   ├── src/
│   │   ├── App.jsx        # Main game component
│   │   ├── api.js         # API client (for future backend)
│   │   ├── components/    # Game UI components
│   │   └── index.css      # Styles
│   ├── package.json       # Dependencies
│   └── vite.config.js     # Vite configuration
├── .github/workflows/
│   └── deploy.yml         # GitHub Actions deployment
├── index.html             # Standalone single-file version
└── python/                # Python implementation
```

## Deployment

This project is automatically deployed to GitHub Pages via GitHub Actions. Every push to the `main` branch triggers:

1. **Build** - Runs `npm run build` to create optimized files
2. **Deploy** - Uploads the `dist/` folder to GitHub Pages

### Accessing the Deployed Game

The game is live at: `https://CodeCraftsman2006.github.io/treasure-runner/`

### Custom Domain (Optional)

To use a custom domain:
1. Go to repository Settings → Pages
2. Add your custom domain in the "Custom domain" field
3. Update DNS records pointing to GitHub Pages IP

## Future Enhancements

- [ ] Integrate C backend for complex worlds
- [ ] Add player progression system
- [ ] Implement level difficulty scaling
- [ ] Add sound effects and music
- [ ] Create level editor
- [ ] Add multiplayer support
- [ ] Implement achievements/leaderboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is part of a University of Guelph CIS*2750 assignment.

## Author

Created by Rajvansh Sandhu

---

**Enjoy the adventure! 🎮**
