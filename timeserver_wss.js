// timeserver.js - WSS version
const https = require('https');
const express = require('express');
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const os = require('os');
const cors = require('cors');

// Express app (保留 HTTP 端点作为备用)
const app = express();
app.use(cors());

// 传统 HTTP 端点 (可以与 WebSocket 并存)
app.get('/time', (req, res) => {
  res.json({ serverTime: Date.now() });
});

// SSL/TLS 配置
const sslOptions = {
  key: fs.readFileSync(path.join(__dirname, 'server-key.pem')),
  cert: fs.readFileSync(path.join(__dirname, 'server-cert.pem'))
};

// 创建 HTTPS 服务器
const server = https.createServer(sslOptions, app);

// 创建 WebSocket 服务器
const wss = new WebSocket.Server({ server });

// WebSocket 连接处理
wss.on('connection', (ws) => {
  console.log('客户端已连接到 WebSocket');
  
  // 连接时立即发送时间
  ws.send(JSON.stringify({ serverTime: Date.now() }));
  
  // 每秒发送时间更新
  const intervalId = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ serverTime: Date.now() }));
    }
  }, 1000);
  
  // 处理客户端消息
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());
      
      // 如果客户端发送 "getTime"，响应当前时间
      if (data.command === 'getTime') {
        ws.send(JSON.stringify({ serverTime: Date.now() }));
      }
    } catch (e) {
      console.error('解析 WebSocket 消息出错:', e);
    }
  });
  
  // 处理断开连接
  ws.on('close', () => {
    console.log('客户端已断开连接');
    clearInterval(intervalId);
  });
});

const PORT = 443; // 标准 HTTPS/WSS 端口

server.listen(PORT, () => {
  console.log(`时间服务器 (WSS) 运行在端口 ${PORT}`);
  console.log('访问 URL:');
  
  // 获取所有网络接口
  const interfaces = os.networkInterfaces();
  Object.keys(interfaces).forEach(name => {
    interfaces[name].forEach(iface => {
      if (iface.family === 'IPv4' && !iface.internal) {
        console.log(`- 网络 (${name}): https://${iface.address}/time`);
        console.log(`- WebSocket (${name}): wss://${iface.address}`);
      }
    });
  });
  
  console.log('- 本地 HTTP: https://localhost/time');
  console.log('- 本地 WebSocket: wss://localhost');
});