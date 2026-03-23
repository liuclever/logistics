import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'tdesign-react';
import 'tdesign-react/es/style/index.css';
import App from './App';
import './styles/app.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ConfigProvider globalConfig={{ classPrefix: 't' }}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
);
