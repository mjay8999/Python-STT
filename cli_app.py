"""
Command-Line Interface for Speech-to-Text
Simple CLI for quick transcription tasks
"""

import argparse
import sys
import config
from audio_handler import AudioHandler
from stt_engine import STTEngine


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Local Speech-to-Text CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record 10 seconds and transcribe
  python cli_app.py --mode record --duration 10
  
  # Transcribe an audio file
  python cli_app.py --mode file --input audio.mp3
  
  # Use specific model and language
  python cli_app.py --mode record --model small --language en --duration 5
  
  # Save transcription to custom location
  python cli_app.py --mode file --input audio.wav --output my_transcription.txt
        """
    )
    
    # Mode selection
    parser.add_argument(
        '--mode',
        type=str,
        choices=['record', 'file'],
        required=True,
        help='Operation mode: record from microphone or transcribe file'
    )
    
    # Input/Output
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Input audio file path (required for file mode)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output transcription file path (optional, auto-generated if not provided)'
    )
    
    # Recording options
    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=config.DEFAULT_DURATION,
        help=f'Recording duration in seconds (default: {config.DEFAULT_DURATION})'
    )
    
    # Model options
    parser.add_argument(
        '--model', '-m',
        type=str,
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        default=config.DEFAULT_MODEL,
        help=f'Whisper model size (default: {config.DEFAULT_MODEL})'
    )
    
    parser.add_argument(
        '--language', '-l',
        type=str,
        default=None,
        help='Language code (e.g., en, es, fr) or auto-detect if not specified'
    )
    
    parser.add_argument(
        '--task', '-t',
        type=str,
        choices=['transcribe', 'translate'],
        default=config.TASK,
        help=f'Task: transcribe or translate to English (default: {config.TASK})'
    )
    
    # Device options
    parser.add_argument(
        '--device',
        type=str,
        choices=['auto', 'cpu', 'cuda'],
        default='auto',
        help='Device to run model on (default: auto)'
    )
    
    # Additional options
    parser.add_argument(
        '--no-save-audio',
        action='store_true',
        help='Do not save recorded audio file'
    )
    
    parser.add_argument(
        '--no-save-transcription',
        action='store_true',
        help='Do not save transcription to file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'file' and not args.input:
        parser.error("--input is required when using file mode")
    
    # Initialize components
    print("\n" + "=" * 60)
    print("Local Speech-to-Text CLI")
    print("=" * 60 + "\n")
    
    audio_handler = AudioHandler(
        sample_rate=config.SAMPLE_RATE,
        channels=config.CHANNELS
    )
    
    stt_engine = STTEngine(
        model_name=args.model,
        device=args.device
    )
    
    # Load model
    print(f"Loading {args.model} model...")
    stt_engine.load_model()
    print()
    
    result = None
    audio_path = None
    
    try:
        if args.mode == 'record':
            # Record mode
            print(f"Recording for {args.duration} seconds...")
            print("Speak now!\n")
            
            audio_data = audio_handler.record_audio(duration=args.duration)
            
            # Save audio if not disabled
            if not args.no_save_audio:
                audio_path = audio_handler.save_audio(
                    audio_data,
                    output_dir=config.RECORDINGS_DIR
                )
                print()
            
            # Transcribe
            print("Transcribing...")
            result = stt_engine.transcribe_audio_data(
                audio_data,
                sample_rate=config.SAMPLE_RATE,
                language=args.language,
                task=args.task
            )
            
        else:  # file mode
            # Transcribe file
            audio_path = args.input
            result = stt_engine.transcribe_file(
                audio_path,
                language=args.language,
                task=args.task
            )
        
        # Display result
        print("\n" + "=" * 60)
        print("TRANSCRIPTION RESULT")
        print("=" * 60)
        print(f"\nLanguage: {result['language']}")
        print(f"\nText:\n{result['text']}\n")
        
        # Display segments if verbose
        if args.verbose and result['segments']:
            print("=" * 60)
            print("DETAILED SEGMENTS")
            print("=" * 60 + "\n")
            
            for segment in result['segments']:
                start = format_timestamp(segment['start'])
                end = format_timestamp(segment['end'])
                print(f"[{start} -> {end}] {segment['text']}")
            print()
        
        # Save transcription if not disabled
        if not args.no_save_transcription:
            output_path = stt_engine.save_transcription(
                result,
                filename=args.output,
                output_dir=config.OUTPUT_DIR
            )
            print()
        
        print("=" * 60)
        print("COMPLETED SUCCESSFULLY")
        print("=" * 60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def format_timestamp(seconds):
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    main()
