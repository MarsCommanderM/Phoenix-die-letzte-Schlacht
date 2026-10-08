from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "project"

def main():
    print(f"Phoenix project: {PROJECT}")
    print("Use the O3DE 26.05.0 CLI/Project Manager to register and configure this project.")
    print("This script intentionally does not guess a local O3DE installation path.")

if __name__ == "__main__":
    main()
