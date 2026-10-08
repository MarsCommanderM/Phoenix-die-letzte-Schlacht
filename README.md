# Phoenix — O3DE 26.05.0 Starter Repository

This repository is the implementation baseline for the Phoenix technical design.

## Baseline
- O3DE: 26.05.0
- Renderer: Atom / RPI / RHI
- Physics: PhysX
- Animation: EMotionFX
- Multiplayer: O3DE Multiplayer / AzNetworking
- Build: O3DE CMake / CLI
- Primary target: Windows

## Important
The `engine/o3de/` directory is intentionally not included. Register your local O3DE 26.05.0 engine separately.

`project/Code/enabled_gems.cmake` is O3DE-managed. Use the O3DE CLI to enable/disable Gems.

## Configure
1. Register the Phoenix project with O3DE.
2. Register the external Phoenix Gems if needed.
3. Enable the required O3DE Gems.
4. Configure and build using O3DE CLI / Project Manager.

The source tree is intentionally conservative: generated AutoComponent C++ and processed asset products are not committed.
