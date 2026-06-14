# Build Instructions

This project can be packaged into a standalone desktop app with PyInstaller.

## Install build dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-build.txt
```

## Build

```bash
pyinstaller tablora.spec
```

## Output

PyInstaller writes the standalone build to `dist/TabloraEditor/` on Windows and to `dist/TabloraEditor.app/` on macOS. Temporary build files go to `build/`.

## Notes

- The application title shown in the UI remains `Tablora Editor`.
- The build artifact name uses a filesystem-safe variant without a slash.
- On macOS, the current recommended standalone path is PyInstaller and the resulting app should be launched as the `.app` bundle, not by opening the inner executable directly.
