// timeserver.js
const express = require('express');
const os = require('os');
const app = express();
const cors = require('cors');
app.use(cors());

app.get('/time', (req, res) => {
  res.json({ serverTime: Date.now() }); // 返回毫秒级时间戳
});

const PORT = 80;

app.listen(PORT, () => {
  console.log(`Time server running on port ${PORT}`);
  console.log('Access URLs:');

    // 获取所有网络接口
  const interfaces = os.networkInterfaces();
  Object.keys(interfaces).forEach(name => {
    interfaces[name].forEach(iface => {
      if (iface.family === 'IPv4' && !iface.internal) {
        console.log(`- Network (${name}): http://${iface.address}/time`);
      }
    });
  });
  
  console.log('- Local: http://localhost/time');
});