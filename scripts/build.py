from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["game", "editor", "server"], default="game")
    args = parser.parse_args()
    print(f"Build target requested: {args.target}")
    print("Run the configured O3DE build generated from the 26.05.0 engine.")

if __name__ == "__main__":
    main()
