"""
Command-line interface for cnckit.

Provides simple CLI tools for queue management and job control.
"""

import sys


def main() -> int:
    """Main CLI entry point."""
    print("cnckit CLI - coming in Phase 1")
    print("Usage: cnckit <command> [options]")
    print()
    print("Commands:")
    print("  queue    Manage the job queue")
    print("  status   Show machine and queue status")
    print("  run      Start the scheduler")
    return 0


if __name__ == "__main__":
    sys.exit(main())
