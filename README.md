# Kenneth Rosales — portfolio

Live: https://gamerbrosz833-ops.github.io/kenneth/

- `index.html` — the whole site (no build step). English by default, Spanish with the EN/ES toggle or `?lang=es`.
- `assets/` — intro film, poster, share image, favicon.
- `reel/` — HyperFrames source of the 12-second film. Sound: `python -I tools/score.py`; render: `npx hyperframes render . -o renders/reel.mp4`, then compress to `assets/reel.mp4`.
