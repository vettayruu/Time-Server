class TimeSync {
  constructor(serverUrl) {
    this.serverUrl = serverUrl;
    this.timeOffset = 0;
    this.syncWithServer();
    setInterval(() => this.syncWithServer(), 60000); // 每分钟同步一次
  }
  async syncWithServer() {
    try {
      const start = Date.now();
      const res = await fetch(this.serverUrl);
      const end = Date.now();
      const { serverTime } = await res.json();
      const networkDelay = (end - start) / 2;
      this.timeOffset = serverTime - (end - networkDelay);
      console.log('TimeSync: offset(ms)=', this.timeOffset);
    } catch (e) {
      console.warn('TimeSync failed:', e);
    }
  }
  getServerTime() {
    return Date.now() + this.timeOffset;
  }
}

// 修改为使用本地服务器地址
// const timeSync = new TimeSync('http://localhost/time'); 
const timeSync = new TimeSync('http://192.168.197.52/time'); 

console.log('Current server time:', new Date(timeSync.getServerTime()).toLocaleString());
console.log('Current server timestamp:', timeSync.getServerTime());