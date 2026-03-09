---
title: Whisparr MacOS Installation
description: MacOS installation guide for Lidarr
tags:
  - installation
  - macos
  - mac
  - setup
  - guide
  - whisparr
---
# MacOS (OSX)

{#OSX}

!!! warning
    Whisparr is not compatible with OSX versions < 10.15 (Catalina) due to .NET incompatibilities.

1. Download the [MacOS App](https://whisparr.servarr.com/v1/update/nightly/updatefile?os=osx&runtime=netcore&arch=x64&installer=true) or  the [MacOS M1 App](https://whisparr.servarr.com/v1/update/nightly/updatefile?os=osx&runtime=netcore&arch=arm64&installer=true) depending on your system architecture.
1. Open the archive and drag the Whisparr icon to your Application folder.
1. Self-sign Whisparr `codesign --force --deep -s - /Applications/Whisparr.app && xattr -rd com.apple.quarantine /Applications/Whisparr.app`
1. Browse to <http://localhost:6969> to start using Whisparr
