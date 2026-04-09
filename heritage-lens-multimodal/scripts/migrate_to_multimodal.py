#!/usr/bin/env python3
"""
Migration script to add multimodal capabilities to existing deployment
Adds optional multimodal section to existing config while preserving original settings
"""

import yaml
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def backup_config(config_path: Path) -> Path:
    """Create backup of existing configuration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"settings.yaml.backup.{timestamp}"
    shutil.copy2(config_path, backup_path)
    print(f"  ✓ Backup created: {backup_path.name}")
    return backup_path


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load existing configuration"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def save_config(config_path: Path, config: Dict[str, Any]):
    """Save configuration to file"""
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def add_multimodal_section(config: Dict[str, Any], enable: bool = False) -> Dict[str, Any]:
    """
    Add multimodal section to config if not present

    Args:
        config: Existing configuration dict
        enable: Whether to enable multimodal features by default

    Returns:
        Updated configuration dict
    """
    if "multimodal" in config:
        print("  ℹ️  Multimodal section already exists")
        return config

    # Add multimodal section with all feature flags
    config["multimodal"] = {
        "enabled": enable,  # Default: disabled (preserve original behavior)
        "vision": {
            "enabled": enable,
            "model": "clip-ViT-B-32",
            "image_collection": "heritage_lens_images"
        },
        "data_pipeline": {
            "extract_images_from_pdf": enable
        },
        "ui": {
            "show_images": enable,
            "max_display_images": 3
        }
    }

    return config


def add_fallback_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Add fallback behavior settings"""
    if "fallback" not in config:
        config["fallback"] = {
            "text_only_on_vision_failure": True,
            "cache_failed_vision_calls": True,
            "log_vision_errors": True
        }
    return config


def migrate_configuration(
    config_path: str = "config/settings.yaml",
    enable: bool = False,
    dry_run: bool = False
) -> bool:
    """
    Migrate configuration to add multimodal capabilities

    Args:
        config_path: Path to configuration file
        enable: Whether to enable multimodal features
        dry_run: If True, only show what would change

    Returns:
        True if migration successful
    """
    config_full_path = Path(config_path)
    if not config_full_path.is_absolute():
        config_full_path = Path.home() / "heritage-lens-multimodal" / config_path

    print(f"Migrating configuration: {config_full_path}")

    # Check if file exists
    if not config_full_path.exists():
        print(f"❌ Configuration file not found: {config_full_path}")
        return False

    # Load existing config
    try:
        config = load_config(config_full_path)
        print(f"  ✓ Loaded existing configuration")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    # Create backup
    if not dry_run:
        backup_config(config_full_path)

    # Add multimodal section
    config = add_multimodal_section(config, enable=enable)

    # Add fallback settings
    config = add_fallback_settings(config)

    # Save updated config
    if dry_run:
        print("\n🔍 Dry run - would add the following section:")
        print(yaml.dump({"multimodal": config["multimodal"]}, default_flow_style=False))
    else:
        try:
            save_config(config_full_path, config)
            print(f"  ✓ Configuration updated successfully")
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False

    return True


def main():
    """Main entry point for migration script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate Heritage Lens configuration to support multimodal features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add multimodal section (disabled by default)
  python scripts/migrate_to_multimodal.py

  # Add and enable multimodal features
  python scripts/migrate_to_multimodal.py --enable

  # Preview changes without applying
  python scripts/migrate_to_multimodal.py --dry-run

  # Custom config path
  python scripts/migrate_to_multimodal.py --config /path/to/settings.yaml
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/settings.yaml",
        help="Path to configuration file (default: config/settings.yaml)"
    )

    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable multimodal features (default: disabled)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Heritage Lens - Multimodal Configuration Migration")
    print("=" * 70)
    print()

    if args.enable:
        print("Mode: Enable multimodal features")
    else:
        print("Mode: Add multimodal section (disabled)")
        print("      Use --enable to activate features")
    print()

    success = migrate_configuration(
        config_path=args.config,
        enable=args.enable,
        dry_run=args.dry_run
    )

    print()
    if success:
        print("=" * 70)
        print("Migration Complete")
        print("=" * 70)

        if args.dry_run:
            print("\nThis was a dry run. Run without --dry-run to apply changes.")
        else:
            print("\nNext steps:")
            if not args.enable:
                print("  1. Multimodal features are DISABLED by default")
                print("     To enable, run: python scripts/migrate_to_multimodal.py --enable")
            else:
                print("  1. Multimodal features are now ENABLED")
                print("  2. Install optional dependencies:")
                print("     pip install sentence-transformers Pillow PyMuPDF")
            print("  3. Restart the Heritage Lens agent")
            print("  4. Test with: python verify_setup.py")

        return 0
    else:
        print("=" * 70)
        print("Migration Failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())
