# Roadmap

This document outlines planned features and development phases.

## Foundation (Phase 0) ✅

- [x] Project structure and packaging setup
- [x] Testing framework (pytest)
- [x] Documentation tooling (mkdocs)
- [x] CI/CD pipeline for tests and docs

## Core Features (Phase 1) ✅

- [x] FIFO/LIFO/priority job queues
- [x] Job metadata (status, timestamps, priority, tools)
- [x] Scheduler with start/stop/pause controls
- [x] Machine abstraction with simulation mode
- [x] Event system for job lifecycle callbacks
- [x] Configuration loader with defaults

## Optional Integrations (Phase 2) ✅

- [x] REST API for remote monitoring (FastAPI)
- [x] MQTT client for messaging and automation
- [x] WebSocket real-time status streaming
- [x] Robot integration (ROS2, TCP commands)
- [x] Simple web dashboard for queue & machine state

## Future Expansion (Phase 3+)

- [ ] Plugin system for user-contributed modules
- [ ] Industry protocols (OPC-UA, PLC handshakes)
- [ ] Multi-machine coordination

## Guiding Principle

**Everything stays optional.** The core remains lean while integrations provide power when needed.
