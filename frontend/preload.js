const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  sendMessage: (message) => ipcRenderer.invoke('send-message', message),
  onResponse: (callback) => ipcRenderer.on('response', callback),
  setMiniMode: (isMini) => ipcRenderer.invoke('set-mini-mode', isMini),
});
