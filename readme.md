# Cameron's PyGame Repo for Testing

## Current Version

v0.6.0

## Version Log

### v0.6.0 - 2026-06-22

- Added automated build and gameplay smoke tests with `unittest`.
- Tests cover source compilation, room building, major item pickup behavior, attack timing, minimap exploration, and save JSON shape.

### v0.5.0 - 2026-06-22

- Added explored-map rendering to the scroll-room minimap HUD.
- Minimap terrain now shows simplified real-world tile colors as the player explores.
- Save output now includes explored minimap tiles.

### v0.4.0 - 2026-06-22

- Added an Escape-key pause menu with save, exit, and resume options.
- Added the game version to the pause menu.
- Added JSON save output for the current room, player state, collected items, and locked exits.

### v0.3.1 - 2026-06-22

- Smoothed ghost/skull movement by preserving subpixel position between frames.

### v0.3.0 - 2026-06-22

- Added a fanfare animation for major item pickups.
- Added a generated fanfare sound for keys, swords, and sword upgrades.

### v0.2.0 - 2026-06-22

- Added a hand-anchored sword swing animation when attacking.
- Reduced the title splash transition to 2.5 seconds before gameplay.
- Added the game version to the title splash screen.

### v0.1.0 - Initial version

- Created the base Dungeons and Data pygame project.
