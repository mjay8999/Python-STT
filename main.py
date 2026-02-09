"""
Main Launcher for Speech-to-Text Application
Provides easy access to both GUI and CLI modes
"""

import sys
import argparse


def main():
    """Main launcher"""
    parser = argparse.ArgumentParser(
        description="Local Speech-to-Text Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  gui  - Launch graphical user interface (default)
  cli  - Launch command-line interface
  
Examples:
  # Launch GUI (default)
  python main.py
  python main.py --mode gui
  
  # Launch CLI
  python main.py --mode cli --help
  python main.py --mode cli --mode record --duration 10
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['gui', 'cli'],
        default='gui',
        help='Application mode: gui or cli (default: gui)'
    )
    
    # Parse known args to allow CLI args to pass through
    args, remaining = parser.parse_known_args()
    
    if args.mode == 'gui':
        # Launch GUI
        try:
            from gui_app import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"Error importing GUI application: {e}")
            print("\nPlease ensure all dependencies are installed:")
            print("  pip install -r requirements.txt")
            sys.exit(1)
        except Exception as e:
            print(f"Error launching GUI: {e}")
            sys.exit(1)
    
    else:  # cli mode
        # Launch CLI with remaining arguments
        try:
            from cli_app import main as cli_main
            # Replace sys.argv with remaining args for CLI parser
            sys.argv = [sys.argv[0]] + remaining
            cli_main()
        except ImportError as e:
            print(f"Error importing CLI application: {e}")
            print("\nPlease ensure all dependencies are installed:")
            print("  pip install -r requirements.txt")
            sys.exit(1)
        except Exception as e:
            print(f"Error launching CLI: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
