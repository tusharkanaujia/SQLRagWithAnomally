import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Table,
  Tag,
  Spin,
  Alert,
  Tabs,
  Select,
  Space,
  Typography,
  Divider,
} from 'antd';
import {
  AlertOutlined,
  RiseOutlined,
  FallOutlined,
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ComposedChart,
} from 'recharts';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const AnomalyDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [allAnomalies, setAllAnomalies] = useState(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [dodData, setDodData] = useState(null);
  const [dodDimension, setDodDimension] = useState('ProductKey');
  const [dodMetric, setDodMetric] = useState('SalesAmount');
  const [dodThreshold, setDodThreshold] = useState(20);
  const [dodLoading, setDodLoading] = useState(false);

  useEffect(() => {
    fetchAllAnomalies();
  }, []);

  useEffect(() => {
    if (selectedTab === 'dayonday') {
      fetchDayOnDayAnomalies();
    }
  }, [selectedTab, dodDimension, dodMetric, dodThreshold]);

  const fetchAllAnomalies = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/anomalies/all');
      setAllAnomalies(response.data);
    } catch (error) {
      console.error('Error fetching anomalies:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDayOnDayAnomalies = async () => {
    setDodLoading(true);
    try {
      const response = await axios.get('/anomalies/day-on-day', {
        params: {
          dimension: dodDimension,
          metric: dodMetric,
          threshold_pct: dodThreshold,
          lookback_days: 30,
          top_n: 50
        }
      });
      setDodData(response.data);
    } catch (error) {
      console.error('Error fetching day-on-day anomalies:', error);
    } finally {
      setDodLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      high: 'red',
      medium: 'orange',
      low: 'yellow',
      critical: 'volcano',
    };
    return colors[severity] || 'default';
  };

  const getSeverityIcon = (severity) => {
    if (severity === 'high' || severity === 'critical') {
      return <WarningOutlined />;
    }
    return <AlertOutlined />;
  };

  const renderOverview = () => {
    if (!allAnomalies || !allAnomalies.summary) return null;

    const summary = allAnomalies.summary;
    const anomalyTypes = allAnomalies.anomaly_types || {};

    return (
      <div>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Total Anomalies Detected"
                value={summary.total_anomalies}
                prefix={<AlertOutlined />}
                valueStyle={{ color: summary.total_anomalies > 0 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Detection Methods"
                value={summary.detection_methods}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Time Series Anomalies"
                value={
                  (anomalyTypes.time_series_daily?.anomalies?.length || 0) +
                  (anomalyTypes.time_series_monthly?.anomalies?.length || 0)
                }
                prefix={<RiseOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Comparative Anomalies"
                value={
                  (anomalyTypes.comparative_yoy?.anomalies?.length || 0) +
                  (anomalyTypes.comparative_mom?.anomalies?.length || 0)
                }
                prefix={<FallOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Divider />

        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="Anomaly Distribution by Type">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart
                  data={Object.entries(anomalyTypes).map(([key, value]) => ({
                    name: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
                    count: value.anomalies?.length || 0,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#1890ff" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  const renderTimeSeries = () => {
    const dailyData = allAnomalies?.anomaly_types?.time_series_daily;
    const monthlyData = allAnomalies?.anomaly_types?.time_series_monthly;

    if (!dailyData && !monthlyData) return null;

    return (
      <div>
        <Row gutter={[16, 16]}>
          {/* Daily Time Series */}
          {dailyData && (
            <>
              <Col span={24}>
                <Card
                  title={`Daily Sales Trends (${dailyData.statistics?.granularity || 'daily'})`}
                  extra={
                    <Tag color={dailyData.anomalies.length > 0 ? 'red' : 'green'}>
                      {dailyData.anomalies.length} anomalies detected
                    </Tag>
                  }
                >
                  {dailyData.time_series_data && (
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={dailyData.time_series_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="TimePeriod" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="UpperBound"
                          stroke="#ffa940"
                          fill="#ffa940"
                          fillOpacity={0.2}
                        />
                        <Area
                          type="monotone"
                          dataKey="LowerBound"
                          stroke="#ffa940"
                          fill="#ffa940"
                          fillOpacity={0.2}
                        />
                        <Line
                          type="monotone"
                          dataKey="MetricValue"
                          stroke="#1890ff"
                          strokeWidth={2}
                          dot={(props) => {
                            const { cx, cy, payload } = props;
                            if (payload.IsAnomaly) {
                              return (
                                <circle cx={cx} cy={cy} r={5} fill="#cf1322" stroke="#fff" strokeWidth={2} />
                              );
                            }
                            return null;
                          }}
                        />
                        <Line type="monotone" dataKey="MA" stroke="#52c41a" strokeDasharray="5 5" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  )}
                </Card>
              </Col>

              <Col span={24}>
                <Card title="Daily Anomalies Details">
                  <Table
                    dataSource={dailyData.anomalies}
                    columns={[
                      {
                        title: 'Date',
                        dataIndex: 'time_period',
                        key: 'time_period',
                      },
                      {
                        title: 'Actual Value',
                        dataIndex: 'metric_value',
                        key: 'metric_value',
                        render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 2 }),
                      },
                      {
                        title: 'Expected Value',
                        dataIndex: 'expected_value',
                        key: 'expected_value',
                        render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 2 }),
                      },
                      {
                        title: 'Deviation',
                        dataIndex: 'deviation_pct',
                        key: 'deviation_pct',
                        render: (val) => (
                          <Tag color={val > 0 ? 'green' : 'red'}>
                            {val > 0 ? '+' : ''}
                            {val?.toFixed(1)}%
                          </Tag>
                        ),
                      },
                      {
                        title: 'Type',
                        dataIndex: 'type',
                        key: 'type',
                        render: (type) => (
                          <Tag color={type === 'spike' ? 'green' : 'red'}>
                            {type === 'spike' ? <RiseOutlined /> : <FallOutlined />} {type}
                          </Tag>
                        ),
                      },
                      {
                        title: 'Severity',
                        dataIndex: 'severity',
                        key: 'severity',
                        render: (severity) => (
                          <Tag color={getSeverityColor(severity)} icon={getSeverityIcon(severity)}>
                            {severity}
                          </Tag>
                        ),
                      },
                    ]}
                    pagination={{ pageSize: 5 }}
                    size="small"
                  />
                </Card>
              </Col>
            </>
          )}
        </Row>
      </div>
    );
  };

  const renderComparative = () => {
    const yoyData = allAnomalies?.anomaly_types?.comparative_yoy;
    const momData = allAnomalies?.anomaly_types?.comparative_mom;

    return (
      <div>
        <Row gutter={[16, 16]}>
          {/* Year over Year */}
          {yoyData && (
            <>
              <Col span={24}>
                <Card
                  title="Year-over-Year Comparison"
                  extra={
                    <Tag color={yoyData.anomalies.length > 0 ? 'red' : 'green'}>
                      {yoyData.anomalies.length} anomalies detected
                    </Tag>
                  }
                >
                  {yoyData.comparison_data && (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={yoyData.comparison_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="Period" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="CurrentValue" fill="#1890ff" name="Current" />
                        <Bar dataKey="PreviousValue" fill="#52c41a" name="Previous Year" />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </Card>
              </Col>

              <Col span={24}>
                <Card title="Year-over-Year Anomalies">
                  <Table
                    dataSource={yoyData.anomalies}
                    columns={[
                      { title: 'Period', dataIndex: 'period', key: 'period' },
                      {
                        title: 'Current',
                        dataIndex: 'current_value',
                        key: 'current_value',
                        render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                      },
                      {
                        title: 'Previous',
                        dataIndex: 'previous_value',
                        key: 'previous_value',
                        render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                      },
                      {
                        title: 'Change',
                        dataIndex: 'percent_change',
                        key: 'percent_change',
                        render: (val) => (
                          <Tag color={val > 0 ? 'green' : 'red'}>
                            {val > 0 ? '+' : ''}
                            {val?.toFixed(1)}%
                          </Tag>
                        ),
                      },
                      {
                        title: 'Type',
                        dataIndex: 'type',
                        key: 'type',
                        render: (type) => (
                          <Tag color={type === 'increase' ? 'green' : 'red'}>
                            {type === 'increase' ? <RiseOutlined /> : <FallOutlined />} {type}
                          </Tag>
                        ),
                      },
                      {
                        title: 'Severity',
                        dataIndex: 'severity',
                        key: 'severity',
                        render: (severity) => (
                          <Tag color={getSeverityColor(severity)}>{severity}</Tag>
                        ),
                      },
                    ]}
                    pagination={{ pageSize: 10 }}
                    size="small"
                  />
                </Card>
              </Col>
            </>
          )}
        </Row>
      </div>
    );
  };

  const renderStatistical = () => {
    const productData = allAnomalies?.anomaly_types?.statistical_products;
    const customerData = allAnomalies?.anomaly_types?.statistical_customers;

    return (
      <div>
        <Row gutter={[16, 16]}>
          {productData && (
            <Col span={24}>
              <Card
                title="Product Sales Anomalies (Z-Score Method)"
                extra={
                  <Tag color={productData.anomalies.length > 0 ? 'red' : 'green'}>
                    {productData.anomalies.length} anomalies detected
                  </Tag>
                }
              >
                <Table
                  dataSource={productData.anomalies}
                  columns={[
                    { title: 'Product', dataIndex: 'dimension_value', key: 'dimension_value' },
                    {
                      title: 'Sales Amount',
                      dataIndex: 'metric_value',
                      key: 'metric_value',
                      render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                    },
                    {
                      title: 'Z-Score',
                      dataIndex: 'zscore',
                      key: 'zscore',
                      render: (val) => (
                        <Tag color={Math.abs(val) > 4 ? 'red' : 'orange'}>{val?.toFixed(2)}</Tag>
                      ),
                    },
                    {
                      title: 'Deviation',
                      dataIndex: 'deviation',
                      key: 'deviation',
                      render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                    },
                    {
                      title: 'Severity',
                      dataIndex: 'severity',
                      key: 'severity',
                      render: (severity) => (
                        <Tag color={getSeverityColor(severity)}>{severity}</Tag>
                      ),
                    },
                  ]}
                  pagination={{ pageSize: 5 }}
                  size="small"
                />
              </Card>
            </Col>
          )}

          {customerData && (
            <Col span={24}>
              <Card
                title="Customer Purchase Anomalies (Isolation Forest)"
                extra={
                  <Tag color={customerData.anomalies.length > 0 ? 'red' : 'green'}>
                    {customerData.anomalies.length} anomalies detected
                  </Tag>
                }
              >
                <Table
                  dataSource={customerData.anomalies}
                  columns={[
                    { title: 'Customer', dataIndex: 'dimension_value', key: 'dimension_value' },
                    {
                      title: 'Purchase Amount',
                      dataIndex: 'metric_value',
                      key: 'metric_value',
                      render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                    },
                    {
                      title: 'Deviation',
                      dataIndex: 'deviation',
                      key: 'deviation',
                      render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                    },
                    {
                      title: 'Orders',
                      dataIndex: 'order_count',
                      key: 'order_count',
                    },
                    {
                      title: 'Severity',
                      dataIndex: 'severity',
                      key: 'severity',
                      render: (severity) => (
                        <Tag color={getSeverityColor(severity)}>{severity}</Tag>
                      ),
                    },
                  ]}
                  pagination={{ pageSize: 5 }}
                  size="small"
                />
              </Card>
            </Col>
          )}
        </Row>
      </div>
    );
  };

  const renderDayOnDay = () => {
    return (
      <div>
        <Card style={{ marginBottom: 16 }}>
          <Title level={5}>Configuration</Title>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Row gutter={16}>
              <Col span={6}>
                <Text strong>Dimension:</Text>
                <Select
                  value={dodDimension}
                  onChange={setDodDimension}
                  style={{ width: '100%', marginTop: 8 }}
                  options={[
                    { value: 'ProductKey', label: 'Product' },
                    { value: 'CustomerKey', label: 'Customer' },
                    { value: 'TerritoryKey', label: 'Territory' },
                    { value: 'PromotionKey', label: 'Promotion' }
                  ]}
                />
              </Col>
              <Col span={6}>
                <Text strong>Metric:</Text>
                <Select
                  value={dodMetric}
                  onChange={setDodMetric}
                  style={{ width: '100%', marginTop: 8 }}
                  options={[
                    { value: 'SalesAmount', label: 'Sales Amount' },
                    { value: 'OrderQuantity', label: 'Order Quantity' }
                  ]}
                />
              </Col>
              <Col span={6}>
                <Text strong>Threshold (%):</Text>
                <Select
                  value={dodThreshold}
                  onChange={setDodThreshold}
                  style={{ width: '100%', marginTop: 8 }}
                  options={[
                    { value: 10, label: '10%' },
                    { value: 20, label: '20%' },
                    { value: 30, label: '30%' },
                    { value: 50, label: '50%' }
                  ]}
                />
              </Col>
              <Col span={6}>
                <Text strong>&nbsp;</Text>
                <br />
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={fetchDayOnDayAnomalies}
                  loading={dodLoading}
                  style={{ marginTop: 8 }}
                >
                  Analyze
                </Button>
              </Col>
            </Row>
          </Space>
        </Card>

        {dodLoading ? (
          <Card>
            <div style={{ textAlign: 'center', padding: 40 }}>
              <Spin size="large" tip="Analyzing day-on-day changes..." />
            </div>
          </Card>
        ) : dodData ? (
          <div>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Total Anomalies"
                    value={dodData.statistics?.anomaly_count || 0}
                    prefix={<AlertOutlined />}
                    valueStyle={{ color: dodData.statistics?.anomaly_count > 0 ? '#cf1322' : '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Spikes"
                    value={dodData.statistics?.spike_count || 0}
                    prefix={<RiseOutlined />}
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Drops"
                    value={dodData.statistics?.drop_count || 0}
                    prefix={<FallOutlined />}
                    valueStyle={{ color: '#faad14' }}
                  />
                </Card>
              </Col>
            </Row>

            {/* Natural Language Summaries */}
            {dodData.anomalies && dodData.anomalies.length > 0 && (
              <Card
                style={{ marginTop: 16 }}
                title={
                  <span>
                    <AlertOutlined style={{ marginRight: 8 }} />
                    Anomaly Descriptions
                  </span>
                }
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {dodData.anomalies.slice(0, 5).map((anomaly, index) => (
                    <Alert
                      key={index}
                      message={
                        <span>
                          <Tag color={getSeverityColor(anomaly.severity)}>
                            {anomaly.severity.toUpperCase()}
                          </Tag>
                          {anomaly.dimension_name}
                        </span>
                      }
                      description={anomaly.description}
                      type={anomaly.severity === 'high' ? 'error' : anomaly.severity === 'medium' ? 'warning' : 'info'}
                      showIcon
                      icon={anomaly.type === 'spike' ? <RiseOutlined /> : <FallOutlined />}
                    />
                  ))}
                  {dodData.anomalies.length > 5 && (
                    <Text type="secondary" style={{ textAlign: 'center', display: 'block' }}>
                      Showing top 5 of {dodData.anomalies.length} anomalies. See table below for complete list.
                    </Text>
                  )}
                </Space>
              </Card>
            )}

            <Card style={{ marginTop: 16 }} title="Day-on-Day Anomalies">
              <Table
                dataSource={dodData.anomalies}
                columns={[
                  {
                    title: 'Date',
                    dataIndex: 'date',
                    key: 'date',
                    render: (date) => new Date(date).toLocaleDateString(),
                    sorter: (a, b) => new Date(b.date) - new Date(a.date),
                  },
                  {
                    title: dodDimension === 'ProductKey' ? 'Product' :
                           dodDimension === 'CustomerKey' ? 'Customer' :
                           dodDimension === 'TerritoryKey' ? 'Territory' : 'Promotion',
                    dataIndex: 'dimension_name',
                    key: 'dimension_name',
                    ellipsis: true,
                  },
                  {
                    title: 'Category',
                    dataIndex: 'category',
                    key: 'category',
                    render: (cat) => cat || '-',
                    ellipsis: true,
                  },
                  {
                    title: 'Current',
                    dataIndex: 'current_value',
                    key: 'current_value',
                    render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                    align: 'right',
                  },
                  {
                    title: 'Previous',
                    dataIndex: 'previous_value',
                    key: 'previous_value',
                    render: (val) => val?.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                    align: 'right',
                  },
                  {
                    title: 'Change',
                    dataIndex: 'percent_change',
                    key: 'percent_change',
                    render: (val, record) => (
                      <span style={{ color: val > 0 ? '#cf1322' : '#faad14' }}>
                        {val > 0 ? <RiseOutlined /> : <FallOutlined />} {Math.abs(val).toFixed(1)}%
                      </span>
                    ),
                    sorter: (a, b) => Math.abs(b.percent_change) - Math.abs(a.percent_change),
                    align: 'right',
                  },
                  {
                    title: 'Type',
                    dataIndex: 'type',
                    key: 'type',
                    render: (type) => (
                      <Tag color={type === 'spike' ? 'red' : 'orange'}>
                        {type}
                      </Tag>
                    ),
                    filters: [
                      { text: 'Spike', value: 'spike' },
                      { text: 'Drop', value: 'drop' },
                    ],
                    onFilter: (value, record) => record.type === value,
                  },
                  {
                    title: 'Severity',
                    dataIndex: 'severity',
                    key: 'severity',
                    render: (severity) => (
                      <Tag color={getSeverityColor(severity)} icon={getSeverityIcon(severity)}>
                        {severity}
                      </Tag>
                    ),
                    filters: [
                      { text: 'High', value: 'high' },
                      { text: 'Medium', value: 'medium' },
                      { text: 'Low', value: 'low' },
                    ],
                    onFilter: (value, record) => record.severity === value,
                  },
                ]}
                expandable={{
                  expandedRowRender: (record) => (
                    <div style={{ margin: 0, padding: '12px 24px', background: 'rgba(124, 58, 237, 0.05)' }}>
                      <Text strong>Description: </Text>
                      <Text>{record.description}</Text>
                    </div>
                  ),
                  rowExpandable: (record) => record.description !== undefined,
                }}
                pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `Total ${total} anomalies` }}
                scroll={{ x: true }}
                size="small"
              />
            </Card>

            {dodData.all_data && dodData.all_data.length > 0 && (
              <Card style={{ marginTop: 16 }} title="Trend Visualization">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dodData.all_data.slice(0, 50)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(124, 58, 237, 0.2)" />
                    <XAxis
                      dataKey="Date"
                      tick={{ fill: 'rgba(255, 255, 255, 0.65)' }}
                      tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                    />
                    <YAxis tick={{ fill: 'rgba(255, 255, 255, 0.65)' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(20, 20, 45, 0.95)',
                        border: '1px solid rgba(124, 58, 237, 0.3)',
                        borderRadius: '8px',
                      }}
                      labelFormatter={(val) => new Date(val).toLocaleDateString()}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="CurrentValue"
                      stroke="#7c3aed"
                      strokeWidth={2}
                      dot={{ fill: '#7c3aed', r: 3 }}
                      activeDot={{ r: 5 }}
                      name="Current Day"
                    />
                    <Line
                      type="monotone"
                      dataKey="PreviousValue"
                      stroke="#c084fc"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={{ fill: '#c084fc', r: 3 }}
                      name="Previous Day"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            )}
          </div>
        ) : (
          <Card>
            <Alert
              message="No Data"
              description="Click 'Analyze' to detect day-on-day anomalies"
              type="info"
              showIcon
            />
          </Card>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" tip="Analyzing sales data for anomalies..." />
        </div>
      </Card>
    );
  }

  return (
    <div>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={4}>
              <AlertOutlined /> Anomaly Detection Dashboard
            </Title>
            <Text type="secondary">
              Comprehensive anomaly detection using time series, statistical, and comparative methods
            </Text>
          </div>
          <Button icon={<ReloadOutlined />} onClick={fetchAllAnomalies} loading={loading}>
            Refresh
          </Button>
        </div>
      </Card>

      <div style={{ marginTop: 16 }}>
        {allAnomalies && allAnomalies.summary?.status === 'success' ? (
          <Tabs activeKey={selectedTab} onChange={setSelectedTab}>
            <TabPane tab="Overview" key="overview">
              {renderOverview()}
            </TabPane>
            <TabPane tab="Time Series" key="timeseries">
              {renderTimeSeries()}
            </TabPane>
            <TabPane tab="Comparative (YoY/MoM)" key="comparative">
              {renderComparative()}
            </TabPane>
            <TabPane tab="Statistical" key="statistical">
              {renderStatistical()}
            </TabPane>
            <TabPane tab="Day-on-Day" key="dayonday">
              {renderDayOnDay()}
            </TabPane>
          </Tabs>
        ) : (
          <Alert
            message="Error Loading Anomalies"
            description={allAnomalies?.summary?.error || 'Failed to load anomaly data'}
            type="error"
            showIcon
          />
        )}
      </div>
    </div>
  );
};

export default AnomalyDashboard;
