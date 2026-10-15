# RockTube Downloader

**RockTube Downloader 2.2.1** is a Windows desktop video downloader built by Mr.Sulim.Inc.

## Windows downloads

Download the installer or portable ZIP from the **2.2.1 release** on the GitHub Releases page.

- **Installer:** run `RockTube-Downloader-Setup-2.2.1.exe`.
- **Portable:** extract `RockTube-Downloader-2.2.1-Windows-Portable.zip` to a folder and launch `RockTube Downloader.exe` from the extracted `RockTube Downloader` folder.

The portable package includes the application runtime and bundled FFmpeg tools.

## Source and build

- `main.py` — application source
- `RockTube Downloader.spec` — PyInstaller build configuration
- `RockTube-Downloader-2.2.1.iss` — Inno Setup installer script
- `rocktube.ico` and `rocktube_logo.png` — application assets

Build prerequisites include a compatible Python environment, the dependencies required by the application, PyInstaller, FFmpeg binaries in the expected build location, and Inno Setup 6 for creating the installer.

Review the build configuration before producing a new release. Generated executables and release archives are distributed through GitHub Releases rather than committed to the source repository.

## Version

Current release candidate: **2.2.1**

## Publisher

Mr.Sulim.Inc
