# Changelog

## [0.2.0](https://github.com/jkkicks/cnckit/compare/v0.1.0...v0.2.0) (2025-11-30)


### Features

* **api:** add REST API integration with web dashboard ([445c8dd](https://github.com/jkkicks/cnckit/commit/445c8dd7fbbc00c0db408160330f3d43def94f51))
* **integrations:** add Phase 2 optional integrations ([dcfd2c7](https://github.com/jkkicks/cnckit/commit/dcfd2c702188b4f977989fbdf27af984c24b5a4b))
* **mqtt:** add MQTT pub/sub client integration ([0c8629f](https://github.com/jkkicks/cnckit/commit/0c8629f0b4968fa029673a90077e14f0dcf1c799))
* **robot:** add TCP and ROS2 robot interfaces ([cbc9ad1](https://github.com/jkkicks/cnckit/commit/cbc9ad15c24ba479c07ea1765f6482986fd57ca7))
* **websocket:** add WebSocket streaming server ([f75bd7c](https://github.com/jkkicks/cnckit/commit/f75bd7ca6d93e7bcba530b97f9ec1699aaf537c5))


### Bug Fixes

* add api init ([e2832d6](https://github.com/jkkicks/cnckit/commit/e2832d661f6fd2eb9e8e8a9aad23481cbfb575a0))
* add dashboard page and upate roadmap/toml ([1b8127a](https://github.com/jkkicks/cnckit/commit/1b8127abd585c799f1544c0d85c3eb7a74e203c6))
* **config:** correct pre_merge_checks key names in coderabbit config ([864c4d1](https://github.com/jkkicks/cnckit/commit/864c4d199dedaa16454b3be72dd99f5311cfa110))
* **config:** remove unsupported mypy from coderabbit tools ([73664a7](https://github.com/jkkicks/cnckit/commit/73664a7ec32ea6dd556822755c10852884b21086))
* remove unused ignore comment and update paho-mqtt version dependency ([9dc9a27](https://github.com/jkkicks/cnckit/commit/9dc9a272d3b05ba511456467183f05e0f119e8a6))


### Documentation

* **api:** add blank lines before fenced code blocks ([1547aa3](https://github.com/jkkicks/cnckit/commit/1547aa3beb17548c7a7ff6d3cc448efb2eb6f748))

## 0.1.0 (2025-11-29)

### Features

* Initial release of cnckit
* Core dependency-free layer with Machine, Job, JobQueue, Scheduler, and EventEmitter
* Automated releases with Release Please
* Publishing to PyPI and TestPyPI via GitHub Actions
