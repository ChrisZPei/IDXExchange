"""
Restore original Python 3.12 models from backup.

This script restores the original models from Models/backup_python312/
back to the Models/ directory, overwriting the converted Python 3.13 versions.
"""

from pathlib import Path
import shutil
import sys

# Define paths
models_dir = Path('Models')
backup_dir = models_dir / 'backup_python312'

# List of all model files
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

def restore_models():
    """Restore original models from backup."""
    if not backup_dir.exists():
        print(f"✗ Backup directory not found: {backup_dir}")
        print("   Cannot restore - no backup exists.")
        return False
    
    print(f"\n{'='*60}")
    print("Restoring Original Python 3.12 Models")
    print(f"{'='*60}\n")
    
    restored = []
    not_found = []
    
    for model_file in model_files:
        backup_path = backup_dir / model_file
        target_path = models_dir / model_file
        
        if backup_path.exists():
            shutil.copy2(backup_path, target_path)
            restored.append(model_file)
            print(f"✓ Restored: {model_file}")
        else:
            not_found.append(model_file)
            print(f"⚠ Not in backup: {model_file}")
    
    print(f"\n{'='*60}")
    print("Restore Summary")
    print(f"{'='*60}")
    print(f"✓ Restored: {len(restored)} models")
    if not_found:
        print(f"⚠ Not found in backup: {len(not_found)} models")
    
    return len(restored) > 0

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Model Restore Script")
    print("="*60)
    print("\nThis script will restore original Python 3.12 models from backup.")
    print("This will overwrite any converted Python 3.13 models.\n")
    
    response = input("Continue with restore? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\nRestore cancelled.")
        sys.exit(0)
    
    try:
        success = restore_models()
        if success:
            print("\n✓ Restore complete!")
            print("Original Python 3.12 models have been restored.")
        else:
            print("\n✗ Restore failed - no backups found.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nRestore interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

