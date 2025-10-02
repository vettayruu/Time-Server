class TimeSync {
  constructor(serverUrl) {
    // 将 http:// 转换为 wss://，并添加端口
    this.serverUrl = serverUrl
      .replace('http://', 'wss://')
      .replace(':80', ':8443') // 更改端口
      + (serverUrl.includes(':') ? '' : ':8443'); // 如果没有端口则添加
    
    this.timeOffset = 0;
    this.isSynced = false;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    
    console.log(`WSS服务器地址: ${this.serverUrl}`);
  }

  async waitForInit() {
    try {
      await this.connectWebSocket();
      return true;
    } catch (error) {
      console.error('TimeSync 初始化失败:', error);
      return false;
    }
  }

  async connectWebSocket() {
    return new Promise((resolve, reject) => {
      try {
        // 对于Node.js环境，需要特殊处理自签名证书
        let wsOptions = {};
        
        if (typeof window === 'undefined') {
          // Node.js环境 - 忽略证书验证
          const WebSocket = require('ws');
          wsOptions = {
            rejectUnauthorized: false,
            checkServerIdentity: () => undefined
          };
          this.socket = new WebSocket(this.serverUrl, wsOptions);
        } else {
          // 浏览器环境
          this.socket = new WebSocket(this.serverUrl);
        }
        
        this.socket.onopen = () => {
          console.log('已连接到WSS时间服务器');
          this.reconnectAttempts = 0;
          this.socket.send(JSON.stringify({ command: 'getTime' }));
        };
        
        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.serverTime) {
              const now = Date.now();
              this.timeOffset = data.serverTime - now;
              this.isSynced = true;
              
              console.log(`安全时间同步完成, 偏移量: ${this.timeOffset}ms`);
              if (data.secure) {
                console.log('✓ 使用安全连接');
              }
              
              if (!this.resolved) {
                this.resolved = true;
                resolve(true);
              }
            }
          } catch (e) {
            console.error('解析服务器消息出错:', e);
          }
        };
        
        this.socket.onerror = (error) => {
          console.error('WSS WebSocket 错误:', error);
          if (!this.isSynced && !this.resolved) {
            reject(error);
          }
        };
        
        this.socket.onclose = (event) => {
          console.log('与WSS时间服务器断开连接，代码:', event.code);
          this.isSynced = false;
          
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connectWebSocket(), 5000);
          }
        };
        
        // 超时处理
        setTimeout(() => {
          if (!this.resolved) {
            this.resolved = true;
            reject(new Error('连接超时'));
          }
        }, 10000);
        
      } catch (error) {
        reject(error);
      }
    });
  }

  getServerTime() {
    return Date.now() + this.timeOffset;
  }
  
  async syncWithServer() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ command: 'getTime' }));
    } else {
      await this.connectWebSocket();
    }
  }
}

// 使用示例
async function main() {
  const timeSync = new TimeSync('http://192.168.197.52/time');
  
  const success = await timeSync.waitForInit();
  
  if (success) {
    console.log('=== WSS 同步完成，开始持续输出时间戳 ===');
    
    setInterval(() => {
      const timestamp = timeSync.getServerTime();
      const lastFive = timestamp.toString().slice(-5);
      const currentTime = new Date(timestamp).toLocaleTimeString();
      
      console.log(`[${currentTime}] WSS Timestamp: ${timestamp} | Last 5: ${lastFive}`);
    }, 1000);
  } else {
    console.log('WSS时间同步失败');
  }
}

// 如果是直接运行（不是被导入）
if (typeof window === 'undefined' && require.main === module) {
  main();
}

// export default TimeSync; // ES模块导出
module.exports = TimeSync; // CommonJS导出