#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const NOTES_DIR = path.join(process.env.HOME || process.env.USERPROFILE, '.md-notes');

// Ensure notes directory exists
if (!fs.existsSync(NOTES_DIR)) {
  fs.mkdirSync(NOTES_DIR, { recursive: true });
}

const command = process.argv[2];
const args = process.argv.slice(3);

const COMMANDS = {
  // Create new note with optional tags
  new: (titleParts) => {
    const title = titleParts.join(' ');
    if (!title) {
      console.log('Error: Please provide a title');
      console.log('Usage: md-notes new "Meeting Notes"');
      return;
    }
    
    const filename = `${Date.now()}-${title.toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, '-')}.md`;
    const tags = titleParts.filter(word => word.startsWith('#')).map(tag => tag.slice(1));
    const content = `# ${title}\n\nCreated: ${new Date().toISOString()}\nTags: ${tags.join(', ')}\n\n## Notes\n\n`;
    
    fs.writeFileSync(path.join(NOTES_DIR, filename), content);
    console.log(`✓ Created: ${filename} in ${NOTES_DIR}`);
  },
  
  // List all notes with options
  list: () => {
    const files = fs.readdirSync(NOTES_DIR);
    if (files.length === 0) {
      console.log('No notes found.');
      return;
    }
    
    console.log(`\n📝 Your Notes (${files.length}):\n`);
    files.forEach((file, index) => {
      const filePath = path.join(NOTES_DIR, file);
      const stats = fs.statSync(filePath);
      const content = fs.readFileSync(filePath, 'utf8');
      const firstLine = content.split('\n')[0].replace('# ', '');
      
      console.log(`${index + 1}. ${firstLine}`);
      console.log(`   📄 ${file} | 📅 ${stats.mtime.toLocaleDateString()}`);
      console.log();
    });
  },
  
  // Search notes by content
  search: (searchTerms) => {
    const term = searchTerms.join(' ').toLowerCase();
    if (!term) {
      console.log('Usage: md-notes search "keyword"');
      return;
    }
    
    const files = fs.readdirSync(NOTES_DIR);
    const results = [];
    
    files.forEach(file => {
      const content = fs.readFileSync(path.join(NOTES_DIR, file), 'utf8').toLowerCase();
      if (content.includes(term)) {
        results.push(file);
      }
    });
    
    if (results.length > 0) {
      console.log(`\n🔍 Found ${results.length} notes containing "${term}":\n`);
      results.forEach(file => console.log(`• ${file}`));
    } else {
      console.log(`No notes found containing "${term}"`);
    }
  },
  
  // Open note in default editor
  open: (filenameParts) => {
    const filename = filenameParts[0];
    if (!filename) {
      console.log('Usage: md-notes open <filename>');
      console.log('Tip: Use "md-notes list" to see all filenames');
      return;
    }
    
    const filePath = path.join(NOTES_DIR, filename);
    if (!fs.existsSync(filePath)) {
      console.log(`Error: Note "${filename}" not found`);
      return;
    }
    
    const { exec } = require('child_process');
    const editor = process.env.EDITOR || 'code'; // VS Code, can be 'nano', 'vim', etc.
    
    exec(`${editor} "${filePath}"`, (error) => {
      if (error) {
        console.log(`Opening with default editor...`);
        // Fallback to showing content
        const content = fs.readFileSync(filePath, 'utf8');
        console.log(content);
      }
    });
  },
  
  // Delete a note
  delete: (filenameParts) => {
    const filename = filenameParts[0];
    if (!filename) {
      console.log('Usage: md-notes delete <filename>');
      return;
    }
    
    const filePath = path.join(NOTES_DIR, filename);
    if (!fs.existsSync(filePath)) {
      console.log(`Error: Note "${filename}" not found`);
      return;
    }
    
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    rl.question(`Are you sure you want to delete "${filename}"? (y/N) `, (answer) => {
      if (answer.toLowerCase() === 'y') {
        fs.unlinkSync(filePath);
        console.log(`✓ Deleted: ${filename}`);
      } else {
        console.log('Deletion cancelled');
      }
      rl.close();
    });
  },
  
  // Display help
  help: () => {
    console.log(`
📝 MD Notes - Simple Note Manager

Usage: md-notes <command> [arguments]

Commands:
  new <title>          Create a new note
  list                 List all notes with details
  search <keyword>     Search notes by content
  open <filename>      Open note in editor
  delete <filename>    Delete a note
  help                 Show this help message

Examples:
  md-notes new "Meeting Notes #work #important"
  md-notes list
  md-notes search "project ideas"
  md-notes open 1234567890-meeting-notes.md
  md-notes delete old-note.md

Notes are stored in: ${NOTES_DIR}
    `);
  }
};

// Execute command
if (command && COMMANDS[command]) {
  COMMANDS[command](args);
} else {
  COMMANDS.help();
}
