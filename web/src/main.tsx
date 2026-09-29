import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider as ArcoConfigProvider } from '@arco-design/web-react';
import '@arco-design/web-react/dist/css/arco.css';
import 'reactflow/dist/style.css';
import './styles/global.css';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ArcoConfigProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ArcoConfigProvider>
  </React.StrictMode>,
);
