const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let savedBounds = null;
let backendProcess = null;

function startBackend() {
  const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('--dev');
  
  // In both modes, we want to ensure the backend is running.
  // For simplicity in this demo, we assume the python environment is set up.
  const pythonPath = isDev 
    ? path.join(__dirname, '..', 'backend', 'venv', 'Scripts', 'python.exe')
    : path.join(process.resourcesPath, 'backend', 'venv', 'Scripts', 'python.exe');
  
  const mainPath = isDev
    ? path.join(__dirname, '..', 'backend', 'src', 'main.py')
    : path.join(process.resourcesPath, 'backend', 'src', 'main.py');

  console.log(`Starting backend at ${mainPath}`);
  
  backendProcess = spawn(pythonPath, ['-m', 'uvicorn', 'src.main:app', '--port', '8000'], {
    cwd: path.dirname(path.dirname(mainPath)),
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  backendProcess.stdout.on('data', (data) => {
    const output = data.toString();
    // Only log to terminal if it's likely writable to avoid EPIPE
    if (process.stdout.writable) {
      console.log(`Backend: ${output}`);
    }
  });

  backendProcess.stderr.on('data', (data) => {
    const output = data.toString();
    if (process.stderr.writable) {
      console.error(`Backend Error: ${output}`);
    }
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false,
    titleBarStyle: 'hidden',
    backgroundColor: '#fdfdfc',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Handle window controls
  ipcMain.on('window-control', (event, action) => {
    if (!mainWindow) return;
    if (action === 'minimize') mainWindow.minimize();
    else if (action === 'maximize') {
      if (mainWindow.isMaximized()) mainWindow.unmaximize();
      else mainWindow.maximize();
    }
    else if (action === 'close') mainWindow.close();
  });

  const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('--dev');

  if (isDev) {
    const url = 'http://localhost:5173';
    const loadWithRetry = () => {
      mainWindow.loadURL(url).catch(() => {
        console.log('Vite not ready, retrying in 500ms...');
        setTimeout(loadWithRetry, 500);
      });
    };
    loadWithRetry();
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile('dist/index.html');
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Handle mini mode toggle from renderer
ipcMain?.handle('set-mini-mode', (event, isMini) => {
  if (!mainWindow) return;

  if (isMini) {
    savedBounds = mainWindow.getBounds();
    const { screen } = require('electron');
    const display = screen.getPrimaryDisplay();
    const { width: screenW, height: screenH } = display.workAreaSize;

    mainWindow.setBounds({
      x: screenW - 370,
      y: screenH - 140,
      width: 360,
      height: 130,
    });
    mainWindow.setAlwaysOnTop(true, 'floating');
    mainWindow.setResizable(false);
  } else {
    if (savedBounds) {
      mainWindow.setBounds(savedBounds);
      savedBounds = null;
    }
    mainWindow.setAlwaysOnTop(false);
    mainWindow.setResizable(true);
  }
});

app.whenReady().then(() => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (backendProcess) backendProcess.kill();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

