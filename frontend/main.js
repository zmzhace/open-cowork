const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow = null;
let savedBounds = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load index.html
  mainWindow.loadFile('index.html');

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Handle mini mode toggle from renderer
ipcMain.handle('set-mini-mode', (event, isMini) => {
  if (!mainWindow) return;

  if (isMini) {
    // Save current window bounds before shrinking
    savedBounds = mainWindow.getBounds();
    
    // Get screen dimensions to position at bottom-right
    const { screen } = require('electron');
    const display = screen.getPrimaryDisplay();
    const { width: screenW, height: screenH } = display.workAreaSize;

    // Shrink to mini size, position at bottom-right
    mainWindow.setBounds({
      x: screenW - 350,
      y: screenH - 110,
      width: 340,
      height: 100,
    });
    mainWindow.setAlwaysOnTop(true, 'floating');
    mainWindow.setResizable(false);
  } else {
    // Restore original size
    if (savedBounds) {
      mainWindow.setBounds(savedBounds);
      savedBounds = null;
    }
    mainWindow.setAlwaysOnTop(false);
    mainWindow.setResizable(true);
  }
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
