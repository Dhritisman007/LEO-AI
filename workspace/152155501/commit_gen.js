const readline = require('readline');
const fs = require('fs');
const path = require('path');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const configPath = path.join(process.cwd(), 'commit_config.json');
const defaultConfig = { types: ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore'], prefix: '' };

const config = fs.existsSync(configPath) ? JSON.parse(fs.readFileSync(configPath)) : defaultConfig;

console.log('--- Git Commit Message Generator ---');

rl.question(`Select type (${config.types.join('|')}): `, (type) => {
  rl.question('Enter short description: ', (desc) => {
    const message = `${config.prefix}${type}: ${desc}`;
    console.log(`\nGenerated Message:\n${message}`);
    
    rl.question('Commit now? (y/n): ', (answer) => {
      if (answer.toLowerCase() === 'y') {
        const { execSync } = require('child_process');
        try {
          execSync(`git commit -m "${message}"`);
          console.log('Successfully committed.');
        } catch (e) {
          console.error('Failed to commit. Ensure you are in a git repo.');
        }
      }
      rl.close();
    });
  });
});