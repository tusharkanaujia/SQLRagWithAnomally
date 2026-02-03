import React, { useState, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  Table,
  Typography,
  Space,
  Alert,
  Tag,
  Spin,
  Row,
  Col,
  Divider,
  Collapse,
} from 'antd';
import {
  SearchOutlined,
  ThunderboltOutlined,
  CodeOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const QueryInterface = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [examples, setExamples] = useState([]);

  useEffect(() => {
    fetchExamples();
  }, []);

  const fetchExamples = async () => {
    try {
      const response = await axios.get('/examples');
      setExamples(response.data);
    } catch (error) {
      console.error('Error fetching examples:', error);
    }
  };

  const handleQuery = async () => {
    if (!question.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post('/query', {
        question: question,
        execute: true,
        limit: 100,
      });
      setResult(response.data);
    } catch (error) {
      console.error('Error executing query:', error);
      setResult({
        success: false,
        error: error.response?.data?.detail || error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuestion) => {
    setQuestion(exampleQuestion);
  };

  const getIntentColor = (intent) => {
    const colors = {
      ranking: 'blue',
      aggregation: 'green',
      time_series: 'purple',
      customer_analysis: 'orange',
      product_analysis: 'cyan',
      geographic: 'magenta',
      promotion: 'gold',
      general_query: 'default',
    };
    return colors[intent] || 'default';
  };

  const downloadCSV = () => {
    if (!result || !result.data) return;

    const headers = result.columns.join(',');
    const rows = result.data.map(row =>
      result.columns.map(col => JSON.stringify(row[col] || '')).join(',')
    );
    const csv = [headers, ...rows].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'query_results.csv';
    a.click();
  };

  const renderVisualization = () => {
    if (!result || !result.data || result.data.length === 0) return null;

    const chartSuggestion = result.chart_suggestion;
    if (!chartSuggestion) return null;

    const data = result.data;

    if (chartSuggestion.type === 'line') {
      return (
        <Card title="Visualization" style={{ marginTop: 16 }}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartSuggestion.x} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={chartSuggestion.y} stroke="#1890ff" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      );
    } else if (chartSuggestion.type === 'bar') {
      return (
        <Card title="Visualization" style={{ marginTop: 16 }}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={chartSuggestion.x} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={chartSuggestion.y} fill="#1890ff" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      );
    }

    return null;
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card>
            <Title level={4}>
              <SearchOutlined /> Ask a Question About Your Sales Data
            </Title>
            <Paragraph type="secondary">
              Type your question in natural language and get instant SQL queries and results
            </Paragraph>

            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Input.Search
                placeholder="e.g., What were the total sales in 2013?"
                size="large"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onSearch={handleQuery}
                enterButton={
                  <Button type="primary" loading={loading} icon={<SearchOutlined />}>
                    Query
                  </Button>
                }
              />

              <Collapse ghost>
                <Panel header="💡 Example Questions" key="examples">
                  <Space wrap>
                    {examples.slice(0, 6).map((example, index) => (
                      <Tag
                        key={index}
                        color={getIntentColor(example.intent)}
                        style={{ cursor: 'pointer', padding: '4px 12px' }}
                        onClick={() => handleExampleClick(example.question)}
                      >
                        {example.question}
                      </Tag>
                    ))}
                  </Space>
                </Panel>
              </Collapse>
            </Space>
          </Card>
        </Col>

        {loading && (
          <Col span={24}>
            <Card>
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin size="large" tip="Generating SQL query and fetching results..." />
              </div>
            </Card>
          </Col>
        )}

        {result && !loading && (
          <>
            <Col span={24}>
              <Card
                title={
                  <Space>
                    <CodeOutlined />
                    Generated SQL Query
                    <Tag color={getIntentColor(result.intent)}>{result.intent}</Tag>
                  </Space>
                }
                extra={
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={downloadCSV}
                    disabled={!result.success || !result.data?.length}
                  >
                    Export CSV
                  </Button>
                }
              >
                {result.success ? (
                  <>
                    <Alert
                      message={result.explanation}
                      type="info"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                    <pre
                      style={{
                        background: '#f5f5f5',
                        padding: 16,
                        borderRadius: 4,
                        overflow: 'auto',
                      }}
                    >
                      {result.sql}
                    </pre>
                  </>
                ) : (
                  <Alert
                    message="Query Failed"
                    description={result.error}
                    type="error"
                    showIcon
                  />
                )}
              </Card>
            </Col>

            {result.success && result.data && result.data.length > 0 && (
              <>
                <Col span={24}>
                  <Card
                    title={
                      <Space>
                        <ThunderboltOutlined />
                        Results ({result.row_count} rows)
                      </Space>
                    }
                  >
                    <Table
                      dataSource={result.data}
                      columns={result.columns.map((col) => ({
                        title: col,
                        dataIndex: col,
                        key: col,
                        ellipsis: true,
                        render: (text) => {
                          if (typeof text === 'number') {
                            return text.toLocaleString();
                          }
                          return text;
                        },
                      }))}
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (total) => `Total ${total} items`,
                      }}
                      scroll={{ x: true }}
                      size="small"
                    />
                  </Card>
                </Col>

                {renderVisualization()}
              </>
            )}

            {result.success && result.data && result.data.length === 0 && (
              <Col span={24}>
                <Alert
                  message="No Results"
                  description="The query executed successfully but returned no data."
                  type="warning"
                  showIcon
                />
              </Col>
            )}
          </>
        )}
      </Row>
    </div>
  );
};

export default QueryInterface;
