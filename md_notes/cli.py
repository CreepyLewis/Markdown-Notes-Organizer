#!/usr/bin/env python3
"""
MD Notes - Simple Markdown Note Manager
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import click

NOTES_DIR = Path.home() / ".md-notes"
CONFIG_FILE = NOTES_DIR / "config.json"

def ensure_notes_dir():
    """Create notes directory if it doesn't exist."""
    NOTES_DIR.mkdir(exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps({"tags": [], "notes_count": 0}))

def get_next_id() -> int:
    """Get next note ID."""
    ensure_notes_dir()
    config = json.loads(CONFIG_FILE.read_text())
    config["notes_count"] += 1
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    return config["notes_count"]

def extract_tags(text: str) -> List[str]:
    """Extract tags from text (words starting with #)."""
    import re
    return re.findall(r'#(\w+)', text)

@click.group()
def cli():
    """MD Notes - Simple Markdown Note Manager"""
    ensure_notes_dir()

@cli.command()
@click.argument("title", nargs=-1, required=True)
@click.option("--content", "-c", help="Note content")
def new(title, content):
    """Create a new note."""
    title_text = " ".join(title)
    note_id = get_next_id()
    
    # Extract tags
    tags = extract_tags(title_text)
    title_clean = title_text.replace("#", "")
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{title_clean[:30].replace(' ', '-')}.md"
    filepath = NOTES_DIR / filename
    
    # Prepare content
    note_content = f"""# {title_clean}

Created: {datetime.now().isoformat()}
ID: {note_id}
Tags: {', '.join(tags) if tags else 'none'}

## Content

{content if content else 'Start writing here...'}
"""
    
    # Write file
    filepath.write_text(note_content)
    
    click.echo(f"✅ Created note: {filename}")
    click.echo(f"   Location: {filepath}")
    if tags:
        click.echo(f"   Tags: {', '.join(tags)}")

@cli.command()
@click.option("--tags", "-t", help="Filter by tags (comma-separated)")
@click.option("--recent", "-r", type=int, help="Show N most recent notes")
def list(tags, recent):
    """List all notes."""
    notes = []
    
    for filepath in NOTES_DIR.glob("*.md"):
        content = filepath.read_text()
        lines = content.split("\n")
        
        note_info = {
            "file": filepath.name,
            "title": lines[0].replace("# ", "") if lines else "Untitled",
            "created": lines[1].replace("Created: ", "") if len(lines) > 1 else "",
            "id": lines[2].replace("ID: ", "") if len(lines) > 2 else "",
            "tags": lines[3].replace("Tags: ", "") if len(lines) > 3 else "",
            "size": filepath.stat().st_size,
            "modified": datetime.fromtimestamp(filepath.stat().st_mtime),
        }
        notes.append(note_info)
    
    # Filter by tags
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        notes = [n for n in notes if any(tag in n["tags"] for tag in tag_list)]
    
    # Sort by modified date
    notes.sort(key=lambda x: x["modified"], reverse=True)
    
    # Limit if --recent specified
    if recent:
        notes = notes[:recent]
    
    # Display
    if not notes:
        click.echo("No notes found.")
        return
    
    click.echo(f"\n📝 Found {len(notes)} notes:\n")
    
    for i, note in enumerate(notes, 1):
        tags_display = f" [{note['tags']}]" if note["tags"] not in ["none", ""] else ""
        click.echo(f"{i:2d}. {note['title'][:40]:40} {tags_display}")
        click.echo(f"    📄 {note['file']}")
        click.echo(f"    📅 {note['modified'].strftime('%Y-%m-%d %H:%M')}")
        click.echo()

@cli.command()
@click.argument("query", required=True)
@click.option("--tag-only", "-T", is_flag=True, help="Search only in tags")
def search(query, tag_only):
    """Search notes by content or tags."""
    results = []
    
    for filepath in NOTES_DIR.glob("*.md"):
        content = filepath.read_text()
        
        if tag_only:
            # Search in tags line
            lines = content.split("\n")
            tags_line = lines[3] if len(lines) > 3 else ""
            if query.lower() in tags_line.lower():
                results.append(filepath)
        else:
            # Search in entire content
            if query.lower() in content.lower():
                results.append(filepath)
    
    if results:
        click.echo(f"\n🔍 Found {len(results)} notes:\n")
        for filepath in results:
            title = filepath.read_text().split("\n")[0].replace("# ", "")
            click.echo(f"• {title}")
            click.echo(f"  {filepath.name}")
            click.echo()
    else:
        click.echo(f"No notes found for: '{query}'")

@cli.command()
@click.argument("pattern")
def open_note(pattern):
    """Open a note by ID, filename, or search pattern."""
    # Try to find by ID first
    for filepath in NOTES_DIR.glob("*.md"):
        content = filepath.read_text()
        lines = content.split("\n")
        if len(lines) > 2 and lines[2] == f"ID: {pattern}":
            _open_editor(filepath)
            return
    
    # Try by filename
    filepath = NOTES_DIR / pattern
    if filepath.exists():
        _open_editor(filepath)
        return
    
    # Try by partial filename
    matches = list(NOTES_DIR.glob(f"*{pattern}*.md"))
    if len(matches) == 1:
        _open_editor(matches[0])
        return
    elif len(matches) > 1:
        click.echo(f"Multiple matches found:")
        for match in matches:
            click.echo(f"  • {match.name}")
        return
    
    click.echo(f"Note not found: {pattern}")

def _open_editor(filepath: Path):
    """Open file in default editor."""
    import subprocess
    import platform
    
    editor = os.environ.get("EDITOR", "code" if platform.system() != "Windows" else "notepad")
    
    try:
        subprocess.run([editor, str(filepath)])
        click.echo(f"Opened: {filepath.name}")
    except FileNotFoundError:
        # Fallback to showing content
        click.echo(filepath.read_text())

@cli.command()
@click.argument("pattern")
@click.confirmation_option(prompt="Are you sure you want to delete this note?")
def delete(pattern):
    """Delete a note by ID or filename."""
    # Similar search logic as open_note
    for filepath in NOTES_DIR.glob("*.md"):
        content = filepath.read_text()
        lines = content.split("\n")
        if len(lines) > 2 and lines[2] == f"ID: {pattern}":
            filepath.unlink()
            click.echo(f"✅ Deleted: {filepath.name}")
            return
    
    filepath = NOTES_DIR / pattern
    if filepath.exists():
        filepath.unlink()
        click.echo(f"✅ Deleted: {filepath.name}")
        return
    
    click.echo(f"Note not found: {pattern}")

@cli.command()
def stats():
    """Show statistics about your notes."""
    note_files = list(NOTES_DIR.glob("*.md"))
    total_notes = len(note_files)
    
    if total_notes == 0:
        click.echo("No notes found.")
        return
    
    # Calculate stats
    total_size = sum(f.stat().st_size for f in note_files)
    oldest = min(note_files, key=lambda f: f.stat().st_mtime)
    newest = max(note_files, key=lambda f: f.stat().st_mtime)
    
    # Count tags
    all_tags = []
    for filepath in note_files:
        content = filepath.read_text()
        lines = content.split("\n")
        if len(lines) > 3:
            tags_line = lines[3].replace("Tags: ", "")
            if tags_line != "none":
                all_tags.extend(tag.strip() for tag in tags_line.split(","))
    
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Display
    click.echo("\n📊 Notes Statistics\n")
    click.echo(f"Total notes: {total_notes}")
    click.echo(f"Total size: {total_size / 1024:.1f} KB")
    click.echo(f"Oldest note: {oldest.name} ({datetime.fromtimestamp(oldest.stat().st_mtime).strftime('%Y-%m-%d')})")
    click.echo(f"Newest note: {newest.name} ({datetime.fromtimestamp(newest.stat().st_mtime).strftime('%Y-%m-%d')})")
    
    if tag_counts:
        click.echo(f"\nTags ({len(tag_counts)} unique):")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            click.echo(f"  #{tag}: {count} notes")

def main():
    """Entry point for the CLI."""
    cli()

if __name__ == "__main__":
    main()
