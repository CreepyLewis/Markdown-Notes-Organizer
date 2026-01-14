#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const NOTES_DIR = './notes';

// Ensure notes directory exists
if (!fs.existsSync(NOTES_DIR)) fs.mkdirSync(NOTES_DIR);

const command = process.argv[2];
const args = process.argv.slice(3);

switch(command) {
  case 'new':
    const title = args.join(' ');
    const filename = `${Date.now()}-${title.toLowerCase().replace(/\s+/g, '-')}.md`;
    const content = `# ${title}\n\nCreated: ${new Date().toLocaleString()}\n\n`;
    fs.writeFileSync(path.join(NOTES_DIR, filename), content);
    console.log(`✓ Created: ${filename}`);
    break;
    
  case 'list':
    const files = fs.readdirSync(NOTES_DIR);
    files.forEach(file => console.log(`• ${file}`));
    break;
    
  default:
    console.log(`
Usage: md-notes <command>
Commands:
  new <title>    Create new note
  list           List all notes
  search <term>  Search in notes
    `);
}
