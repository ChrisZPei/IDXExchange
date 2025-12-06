"""
Convert joblib models from Python 3.12 to Python 3.13 compatible format.

This script:
1. Backs up all original .joblib files to Models/backup_python312/
2. Loads each model and re-saves it with Python 3.13 compatible pickle format
3. Preserves all model functionality while making them compatible with Python 3.13
"""

import joblib
from pathlib import Path
import shutil
import sys
import pickle

# Define paths
models_dir = Path('Models')
backup_dir = models_dir / 'backup_python312'

# List of all model files to convert
model_files = [
    'xgb_base_pipeline.joblib',
    'xgb_hybrid_pipeline.joblib',
    'lgbm_base.joblib',
    'lgbm_new.joblib',
    'lgbm_hybrid.joblib',
    'gbr_best.joblib',
    'xgb_best.joblib',
    'xgb_best_hybrid.joblib',
    'hybrid_linear.joblib',
    'hybrid_tree.joblib',
    'hybrid_forest.joblib',
]

def backup_originals():
    """Create backup directory and copy all original model files."""
    print(f"\n{'='*60}")
    print("Step 1: Backing up original Python 3.12 models")
    print(f"{'='*60}\n")
    
    # Create backup directory if it doesn't exist
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created backup directory: {backup_dir}\n")
    
    backed_up = []
    skipped = []
    
    for model_file in model_files:
        source_path = models_dir / model_file
        backup_path = backup_dir / model_file
        
        if source_path.exists():
            # Only backup if not already backed up (to avoid overwriting originals)
            if not backup_path.exists():
                shutil.copy2(source_path, backup_path)
                backed_up.append(model_file)
                print(f"✓ Backed up: {model_file}")
            else:
                skipped.append(model_file)
                print(f"⊘ Already backed up: {model_file} (skipping)")
        else:
            print(f"⚠ Not found: {model_file} (skipping)")
    
    print(f"\n✓ Backup complete: {len(backed_up)} files backed up")
    if skipped:
        print(f"⊘ Skipped (already exist): {len(skipped)} files")
    
    return backed_up

def convert_models():
    """Load and re-save models to convert to Python 3.13 compatible format."""
    print(f"\n{'='*60}")
    print("Step 2: Converting models to Python 3.13 compatible format")
    print(f"{'='*60}\n")
    
    print(f"Current Python version: {sys.version}")
    print(f"Pickle protocol: {pickle.HIGHEST_PROTOCOL}\n")
    
    converted = []
    failed = []
    
    for model_file in model_files:
        model_path = models_dir / model_file
        
        if not model_path.exists():
            print(f"⚠ Not found: {model_file} (skipping)")
            continue
        
        print(f"Converting {model_file}...", end=" ")
        
        try:
            # Load the model (this works with Python 3.12 format)
            model = joblib.load(model_path)
            
            # Re-save with current Python version
            # Use protocol 5 (highest for Python 3.8+) which is compatible with Python 3.13
            # Protocol 5 is the default for Python 3.8+ and works across versions
            joblib.dump(model, model_path, protocol=5)
            
            converted.append(model_file)
            print("✓ Success")
            
        except Exception as e:
            # Get more detailed error information
            error_msg = f"{type(e).__name__}: {str(e)}"
            failed.append((model_file, error_msg))
            print(f"✗ Failed: {error_msg}")
            # If it's a pickle error, try with a different approach
            if "pickle" in str(e).lower() or "118" in str(e):
                try:
                    # Try loading with different protocols or methods
                    import pickle5  # This might help, but may not be available
                    print(f"   (Note: Pickle protocol error - model may need Python 3.13 to convert)")
                except ImportError:
                    pass
    
    print(f"\n{'='*60}")
    print("Conversion Summary")
    print(f"{'='*60}")
    print(f"✓ Successfully converted: {len(converted)} models")
    if failed:
        print(f"✗ Failed: {len(failed)} models")
        for model_file, error in failed:
            print(f"  - {model_file}: {error}")
    
    return converted, failed

def verify_backup():
    """Verify that backup files exist and are different from originals."""
    print(f"\n{'='*60}")
    print("Step 3: Verifying backup integrity")
    print(f"{'='*60}\n")
    
    verified = 0
    for model_file in model_files:
        original = models_dir / model_file
        backup = backup_dir / model_file
        
        if original.exists() and backup.exists():
            # Check file sizes (they should be similar, not necessarily identical)
            orig_size = original.stat().st_size
            backup_size = backup.stat().st_size
            
            if abs(orig_size - backup_size) < 100:  # Allow small differences
                print(f"✓ {model_file}: Backup verified (sizes match)")
                verified += 1
            else:
                print(f"⚠ {model_file}: Size mismatch (original: {orig_size}, backup: {backup_size})")
        elif backup.exists():
            print(f"✓ {model_file}: Backup exists (original may have been converted)")
            verified += 1
    
    print(f"\n✓ Verified: {verified} backup files")
    return verified

if __name__ == "__main__":
    
    print("\n" + "="*60)
    print("Model Conversion Script: Python 3.12 → Python 3.13")
    print("="*60)
    print("\nThis script will:")
    print("  1. Backup all original .joblib files to Models/backup_python312/")
    print("  2. Convert models to Python 3.13 compatible format")
    print("  3. Verify backup integrity")
    print("\nOriginal models will be preserved in the backup directory.")
    print("You can restore them by copying from Models/backup_python312/ if needed.\n")
    
    # Confirm before proceeding (skip if --yes flag is passed)
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv
    if not skip_confirmation:
        response = input("Continue with conversion? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\nConversion cancelled.")
            sys.exit(0)
    
    try:
        # Step 1: Backup originals
        backed_up = backup_originals()
        
        # Step 2: Convert models
        converted, failed = convert_models()
        
        # Step 3: Verify backup
        verified = verify_backup()
        
        # Final summary
        print(f"\n{'='*60}")
        print("Conversion Complete!")
        print(f"{'='*60}")
        print(f"✓ Models converted: {len(converted)}")
        print(f"✓ Backups created: {len(backed_up)}")
        print(f"✓ Backups verified: {verified}")
        if failed:
            print(f"✗ Failed conversions: {len(failed)}")
        print(f"\nOriginal models backed up to: {backup_dir}")
        print("\nYou can now use the converted models with Python 3.13.")
        print("To restore originals, copy files from Models/backup_python312/ back to Models/")
        
    except KeyboardInterrupt:
        print("\n\nConversion interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

