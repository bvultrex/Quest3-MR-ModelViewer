# PROJECT STATE

**Project:** Quest3 MR Model Viewer  
**Target:** Meta Quest 3 / Quest 3S standalone  
**Current milestone:** v0.1 hardware bring-up  
**Date:** 2026-09-16

## Current architecture

- Native Android + C++ OpenXR for the first hardware-validation milestone.
- Meta OpenXR SDK v85 `XrPassthroughOcclusion` is used as the reference implementation.
- GitHub Actions builds a debug-signed ARM64 APK.
- CI validates APK signature, package name, application label and SHA-256 checksum.

## v0.1 acceptance criteria

- APK builds in GitHub Actions.
- APK installs and launches on Quest 3 standalone.
- Passthrough is visible.
- Environment Depth permission/API initializes.
- Real geometry can occlude virtual sample geometry.

## Next milestone

v0.2 replaces sample content with the first custom Model Viewer shell and adds GLB/glTF import plus object manipulation.
