# Roadmap

This document outlines planned features and future expansion for the project.

## Foundation (Phase 0)

- [ ] Project structure and packaging setup
- [ ] Testing framework (pytest)
- [ ] Documentation tooling
- [ ] CI/CD pipeline for tests and docs

## Core Features (Phase 1)

- [ ] FIFO/LIFO job queues
- [ ] Job metadata (time, tool, priority)
- [ ] Scheduler with start/stop/pause controls
- [ ] Machine abstraction hiding LinuxCNC API complexity
- [ ] Event callbacks for job completion, errors, idle state

## Optional Integrations (Phase 2)

- [ ] REST API for remote monitoring (FastAPI)
- [ ] MQTT client for messaging and automation
- [ ] Websocket real-time status streaming
- [ ] Robot integration (ROS2, TCP commands)
- [ ] Simple web dashboard for queue & machine state

## Future Expansion (Phase 3+)

- [ ] Plugin system for user-contributed modules
- [ ] Industry tools (MQTT/OPC-UA, PLC handshakes)
- [ ] Multi-machine coordination
- [ ] Simulation mode for testing without hardware

## Guiding Principle

**Everything stays optional.** The core remains lean while integrations provide power when needed.
