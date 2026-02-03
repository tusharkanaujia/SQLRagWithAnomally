import React, { useState } from 'react';
import { Layout, Menu, Typography, ConfigProvider, theme } from 'antd';
import {
  RobotOutlined,
  AlertOutlined,
  SearchOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import QueryInterface from './components/QueryInterface';
import AnomalyDashboard from './components/AnomalyDashboard';
import GalaxyBackground from './components/GalaxyBackground';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

function App() {
  const [selectedMenu, setSelectedMenu] = useState('query');
  const [isDarkMode] = useState(true); // Always dark mode for AI theme

  const menuItems = [
    {
      key: 'query',
      icon: <SearchOutlined />,
      label: 'SQL Query',
    },
    {
      key: 'anomalies',
      icon: <AlertOutlined />,
      label: 'Anomaly Detection',
    },
    {
      key: 'analytics',
      icon: <BarChartOutlined />,
      label: 'Analytics',
    },
  ];

  const renderContent = () => {
    switch (selectedMenu) {
      case 'query':
        return <QueryInterface />;
      case 'anomalies':
        return <AnomalyDashboard />;
      case 'analytics':
        return <div style={{ padding: 24 }}>Analytics Dashboard (Coming Soon)</div>;
      default:
        return <QueryInterface />;
    }
  };

  return (
    <>
      <GalaxyBackground />
      <ConfigProvider
        theme={{
          algorithm: theme.darkAlgorithm,
          token: {
            colorPrimary: '#7c3aed',
            colorBgContainer: 'rgba(15, 15, 35, 0.85)',
            colorBgElevated: 'rgba(20, 20, 45, 0.9)',
            colorBorder: 'rgba(124, 58, 237, 0.3)',
            colorText: 'rgba(255, 255, 255, 0.95)',
            colorTextSecondary: 'rgba(255, 255, 255, 0.65)',
            borderRadius: 12,
            fontSize: 14,
          },
        }}
      >
        <Layout style={{ minHeight: '100vh', background: 'transparent', position: 'relative', zIndex: 1 }}>
          <Sider
            breakpoint="lg"
            collapsedWidth="0"
            style={{
              background: 'rgba(15, 15, 35, 0.85)',
              backdropFilter: 'blur(20px)',
              borderRight: '1px solid rgba(124, 58, 237, 0.2)',
              boxShadow: '0 8px 32px rgba(124, 58, 237, 0.15)',
            }}
          >
            <div
              className="logo-container"
              style={{
                height: 64,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 22,
                fontWeight: 700,
                background: 'linear-gradient(135deg, #7c3aed 0%, #c084fc 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                letterSpacing: '1px',
              }}
            >
              <RobotOutlined style={{ marginRight: 10, fontSize: 28, color: '#7c3aed' }} />
              <span style={{ color: '#fff' }}>AI Sales RAG</span>
            </div>
            <Menu
              theme="dark"
              mode="inline"
              selectedKeys={[selectedMenu]}
              items={menuItems}
              onClick={({ key }) => setSelectedMenu(key)}
              style={{
                background: 'transparent',
                borderRight: 'none',
              }}
              className="galaxy-menu"
            />
          </Sider>
          <Layout style={{ background: 'transparent' }}>
            <Header
              style={{
                padding: '0 32px',
                background: 'rgba(15, 15, 35, 0.7)',
                backdropFilter: 'blur(20px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid rgba(124, 58, 237, 0.2)',
                boxShadow: '0 4px 24px rgba(124, 58, 237, 0.1)',
              }}
            >
              <Title
                level={3}
                style={{
                  margin: 0,
                  background: 'linear-gradient(135deg, #ffffff 0%, #c084fc 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  fontWeight: 700,
                  letterSpacing: '0.5px',
                }}
              >
                🚀 AI-Powered Sales Intelligence
              </Title>
            </Header>
            <Content
              style={{
                margin: '24px 16px',
                padding: 0,
                background: 'transparent',
                minHeight: 280,
              }}
            >
              {renderContent()}
            </Content>
          </Layout>
        </Layout>
      </ConfigProvider>
    </>
  );
}

export default App;
