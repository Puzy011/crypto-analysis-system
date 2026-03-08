# 虚拟货币行情分析系统 - 前端

基于 Vue 3 + TypeScript + Element Plus 的现代化加密货币分析平台前端。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **构建工具**: Vite
- **图表库**: Lightweight Charts
- **HTTP 客户端**: Axios

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口定义
│   ├── components/       # 通用组件
│   ├── constants/        # 常量配置
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态管理
│   ├── styles/           # 全局样式
│   ├── utils/            # 工具函数
│   ├── views/            # 页面组件
│   ├── App.vue           # 根组件
│   └── main.ts           # 入口文件
├── .env.development      # 开发环境变量
├── .env.production       # 生产环境变量
├── index.html            # HTML 模板
├── package.json          # 依赖配置
├── tsconfig.json         # TypeScript 配置
└── vite.config.ts        # Vite 配置
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

### 类型检查

```bash
npm run type-check
```

## 功能模块

### 1. 市场行情
- 实时价格监控
- 多币种行情列表
- K线图表展示
- 多时间周期切换

### 2. AI 预测
- 基础预测模型
- 高级多模型预测
- 实时预测更新
- 预测结果可视化

### 3. 庄家分析
- 大单监控
- 资金流向分析
- 巨鲸操作识别
- 庄家阶段判断

### 4. 舆情分析
- 多源舆情采集
- 情感分析
- 实时舆情监控
- 主题建模

### 5. 技术分析
- 完整技术指标
- 多时间框架分析
- 回测系统
- 策略验证

### 6. 工具功能
- 自选币管理
- 价格预警设置
- 数据导出
- 个性化配置

## 开发规范

### 组件命名
- 使用 PascalCase 命名组件文件
- 组件名应该具有描述性

### 代码风格
- 使用 TypeScript 严格模式
- 遵循 Vue 3 Composition API 最佳实践
- 使用 ESLint 进行代码检查

### 提交规范
- feat: 新功能
- fix: 修复问题
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建/工具链更新

## 环境变量

### 开发环境 (.env.development)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=虚拟货币行情分析系统
```

### 生产环境 (.env.production)
```env
VITE_API_BASE_URL=
VITE_APP_TITLE=虚拟货币行情分析系统
```

## API 接口

所有 API 请求通过 `/api` 代理到后端服务器。

主要接口模块：
- `/api/market` - 市场行情
- `/api/prediction` - AI 预测
- `/api/whale` - 庄家分析
- `/api/sentiment` - 舆情分析
- `/api/complete-ta` - 技术分析
- `/api/enhanced-backtest` - 回测系统

## 常见问题

### 端口被占用
修改 `vite.config.ts` 中的 `server.port` 配置。

### API 请求失败
检查后端服务是否启动，确认 `.env` 文件中的 API 地址配置正确。

### 依赖安装失败
尝试清除缓存：
```bash
rm -rf node_modules package-lock.json
npm install
```

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 许可证

MIT License
