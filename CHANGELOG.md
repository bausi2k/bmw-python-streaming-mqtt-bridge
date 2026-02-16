# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-02-16
### Added
- **Multi-Car Support:** Neue Option `LOCAL_MQTT_APPEND_VIN` in der `.env`. Wenn aktiviert (`true`), wird die VIN an das MQTT-Basis-Topic angehängt (z.B. `home/bmw/live/<VIN>/...`). Dies ermöglicht den Betrieb mehrerer Container für unterschiedliche Fahrzeuge am selben Broker.


## [1.2.2] - 2025-02-14
### Added
- **GitHub Actions Workflow:** Automated build pipeline for Docker images.

## [1.2.0] - 2025-10-09
### Added
- **GitHub Actions Workflow:** Automated build pipeline for Docker images.
- **Multi-Arch Support:** Docker images are now built for `linux/amd64` (PC) and `linux/arm64` (Raspberry Pi).
- **GitHub Container Registry:** Images are now pushed to `ghcr.io` for easy access without manual builds.

### Changed
- **License:** Switched project license to **CC BY-NC-SA 4.0** (Non-Commercial).
- **Documentation:** Complete overhaul of `README.md` with bilingual support (English/German) and clearer installation instructions.
- **Installation:** Switched recommended installation method from local build to pre-built Docker image.

## [1.1.0] - 2025-10-09
### Added
- **Watchdog:** A background thread now monitors data traffic and restarts the connection if no data is received for 3 hours.
- **Token Refresh:** Added a dedicated thread to refresh OAuth2 tokens automatically before they expire.
- **Log Rotation:** Implemented `TimedRotatingFileHandler` to rotate logs daily and delete files older than 7 days.
- **Robustness:** Added connection retries for the local MQTT broker.
- **Startup:** Script now prints the version number on startup.

### Fixed
- Fixed an issue where the script would crash if `bmw_tokens.json` was missing (now triggers interactive login).
- Fixed a bug where the token refresh loop would not correctly update the client's internal state.

## [1.0.0] - 2025-10-03
### Added
- Initial Release.
- Basic connection to BMW CarData Streaming API.
- OAuth2 Device Code Flow authentication.
- Forwarding of vehicle data to local MQTT broker.
- Docker support via `Dockerfile` and `docker-compose.yml`.