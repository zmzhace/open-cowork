const { spawn } = require('child_process');
const path = require('path');

// Remove the problematic env var added by VS Code etc.
delete process.env.ELECTRON_RUN_AS_NODE;

// Spawn electron
const electronPath = require('electron');
const args = process.argv.slice(2);
args.unshift('.');

spawn(electronPath, args, {
  stdio: 'inherit',
  env: process.env
});
