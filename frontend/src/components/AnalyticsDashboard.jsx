import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { getAnalytics } from '../services/api';

const AnalyticsDashboard = ({ darkMode = false }) => {
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [period, setPeriod] = useState('month');

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAnalytics.getInsightsSummary();
      setAnalytics(data);
    } catch (error) {
      console.error('Error loading analytics:', error);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const moodColors = {
    Happy: '#10b981',
    Sad: '#3b82f6',
    Angry: '#ef4444',
    Calm: '#8b5cf6',
    Neutral: '#6b7280'
  };

  if (loading) {
    return (
      <div style={styles.container(darkMode)}>
        <div style={styles.loading}>Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container(darkMode)}>
        <div style={styles.error}>{error}</div>
        <button onClick={loadAnalytics} style={styles.retryButton}>Retry</button>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  const { summary, insights, mood_trends, consistency, peak_times, keywords, emotional_journey } = analytics;

  // Prepare data for charts
  const moodTrendData = mood_trends.periods.map((period, index) => ({
    period: new Date(period).toLocaleDateString(),
    Happy: mood_trends.moods.Happy[index],
    Sad: mood_trends.moods.Sad[index],
    Angry: mood_trends.moods.Angry[index],
    Calm: mood_trends.moods.Calm[index],
    Neutral: mood_trends.moods.Neutral[index]
  }));

  const peakHoursData = Object.entries(peak_times.by_hour).map(([hour, count]) => ({
    hour: `${hour}:00`,
    count
  }));

  const peakDaysData = Object.entries(peak_times.by_day).map(([day, count]) => ({
    day,
    count
  }));

  const keywordData = keywords.keywords.slice(0, 10);

  const renderOverviewTab = () => (
    <div style={styles.tabContent}>
      {/* Summary Cards */}
      <div style={styles.cardGrid}>
        <div style={styles.card(darkMode)}>
          <h3 style={styles.cardTitle}>Total Memories</h3>
          <div style={styles.cardValue}>{summary.total_memories}</div>
          <div style={styles.cardSubtext}>Life moments captured</div>
        </div>

        <div style={styles.card(darkMode)}>
          <h3 style={styles.cardTitle}>Consistency Score</h3>
          <div style={styles.cardValue}>{summary.consistency_score}%</div>
          <div style={styles.cardSubtext}>
            {consistency.current_streak} day streak
          </div>
        </div>

        <div style={styles.card(darkMode)}>
          <h3 style={styles.cardTitle}>Dominant Mood</h3>
          <div style={styles.cardValue}>
            <span style={{ color: moodColors[summary.dominant_mood] }}>
              {summary.dominant_mood}
            </span>
          </div>
          <div style={styles.cardSubtext}>Most frequent emotion</div>
        </div>

        <div style={styles.card(darkMode)}>
          <h3 style={styles.cardTitle}>Emotional Volatility</h3>
          <div style={styles.cardValue}>{summary.emotional_volatility.toFixed(2)}</div>
          <div style={styles.cardSubtext}>
            {summary.emotional_volatility < 0.5 ? 'Stable' : 'Variable'} emotions
          </div>
        </div>
      </div>

      {/* Insights */}
      <div style={styles.insightsSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Key Insights</h3>
        <ul style={styles.insightsList}>
          {insights.map((insight, index) => (
            <li key={index} style={styles.insightItem}>
              <span style={styles.insightBullet}>•</span>
              {insight}
            </li>
          ))}
        </ul>
      </div>

      {/* Mood Distribution Pie Chart */}
      <div style={styles.chartSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Mood Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={Object.entries(mood_trends.total_counts).map(([mood, count]) => ({
                name: mood,
                value: count
              }))}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {Object.entries(mood_trends.total_counts).map(([mood], index) => (
                <Cell key={`cell-${index}`} fill={moodColors[mood]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderMoodTab = () => (
    <div style={styles.tabContent}>
      {/* Mood Trends Line Chart */}
      <div style={styles.chartSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Mood Trends Over Time</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={moodTrendData}>
            <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
            <XAxis dataKey="period" stroke={darkMode ? '#9ca3af' : '#6b7280'} />
            <YAxis stroke={darkMode ? '#9ca3af' : '#6b7280'} />
            <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1f2937' : '#fff' }} />
            <Legend />
            {Object.keys(moodColors).map(mood => (
              <Line
                key={mood}
                type="monotone"
                dataKey={mood}
                stroke={moodColors[mood]}
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Emotional Journey */}
      <div style={styles.chartSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Emotional Journey</h3>
        <div style={styles.emotionalStats}>
          <div>
            <strong>Recent Trend:</strong> {emotional_journey.recent_trend}
          </div>
          <div>
            <strong>Mood Shifts:</strong> {emotional_journey.mood_shifts}
          </div>
          <div>
            <strong>Average Score:</strong> {emotional_journey.average_mood_score}
          </div>
        </div>
      </div>
    </div>
  );

  const renderActivityTab = () => (
    <div style={styles.tabContent}>
      {/* Peak Hours Bar Chart */}
      <div style={styles.chartSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Peak Activity Hours</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={peakHoursData}>
            <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
            <XAxis dataKey="hour" stroke={darkMode ? '#9ca3af' : '#6b7280'} />
            <YAxis stroke={darkMode ? '#9ca3af' : '#6b7280'} />
            <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1f2937' : '#fff' }} />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
        {peak_times.peak_hour_label && (
          <p style={styles.chartNote}>
            You're most active at {peak_times.peak_hour_label}
          </p>
        )}
      </div>

      {/* Peak Days Bar Chart */}
      <div style={styles.chartSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Activity by Day of Week</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={peakDaysData}>
            <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
            <XAxis dataKey="day" stroke={darkMode ? '#9ca3af' : '#6b7280'} />
            <YAxis stroke={darkMode ? '#9ca3af' : '#6b7280'} />
            <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1f2937' : '#fff' }} />
            <Bar dataKey="count" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
        {peak_times.peak_day && (
          <p style={styles.chartNote}>
            {peak_times.peak_day} is your most active day
          </p>
        )}
      </div>

      {/* Consistency Metrics */}
      <div style={styles.chartSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Journaling Consistency</h3>
        <div style={styles.consistencyGrid}>
          <div style={styles.consistencyCard(darkMode)}>
            <div style={styles.consistencyLabel}>Current Streak</div>
            <div style={styles.consistencyValue}>{consistency.current_streak} days</div>
          </div>
          <div style={styles.consistencyCard(darkMode)}>
            <div style={styles.consistencyLabel}>Longest Streak</div>
            <div style={styles.consistencyValue}>{consistency.longest_streak} days</div>
          </div>
          <div style={styles.consistencyCard(darkMode)}>
            <div style={styles.consistencyLabel}>Avg Per Day</div>
            <div style={styles.consistencyValue}>{consistency.avg_memories_per_day}</div>
          </div>
          <div style={styles.consistencyCard(darkMode)}>
            <div style={styles.consistencyLabel}>Active Days</div>
            <div style={styles.consistencyValue}>{consistency.total_days}/{consistency.days || 30}</div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderKeywordsTab = () => (
    <div style={styles.tabContent}>
      {/* Top Keywords */}
      <div style={styles.chartSection(darkMode)}>
        <h3 style={styles.sectionTitle}>Top Keywords</h3>
        <div style={styles.keywordCloud}>
          {keywordData.map((item, index) => (
            <span
              key={index}
              style={{
                ...styles.keyword,
                fontSize: `${Math.max(14, Math.min(30, item.count * 2))}px`,
                opacity: Math.max(0.6, Math.min(1, item.count / 10))
              }}
            >
              {item.word}
            </span>
          ))}
        </div>
      </div>

      {/* Topics Distribution */}
      {keywords.topics && keywords.topics.length > 0 && (
        <div style={styles.chartSection(darkMode)}>
          <h3 style={styles.sectionTitle}>Topics</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={keywords.topics}
              layout="horizontal"
            >
              <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? '#374151' : '#e5e7eb'} />
              <XAxis type="number" stroke={darkMode ? '#9ca3af' : '#6b7280'} />
              <YAxis type="category" dataKey="topic" stroke={darkMode ? '#9ca3af' : '#6b7280'} />
              <Tooltip contentStyle={{ backgroundColor: darkMode ? '#1f2937' : '#fff' }} />
              <Bar dataKey="count" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );

  return (
    <div style={styles.container(darkMode)}>
      <div style={styles.header}>
        <h2 style={styles.title}>Analytics Dashboard</h2>
        <div style={styles.periodSelector}>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            style={styles.select(darkMode)}
          >
            <option value="week">Past Week</option>
            <option value="month">Past Month</option>
            <option value="year">Past Year</option>
          </select>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={styles.tabNav}>
        {['overview', 'mood', 'activity', 'keywords'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={styles.tabButton(darkMode, activeTab === tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && renderOverviewTab()}
      {activeTab === 'mood' && renderMoodTab()}
      {activeTab === 'activity' && renderActivityTab()}
      {activeTab === 'keywords' && renderKeywordsTab()}
    </div>
  );
};

const styles = {
  container: (darkMode) => ({
    padding: '20px',
    backgroundColor: darkMode ? '#1f2937' : '#ffffff',
    color: darkMode ? '#e5e7eb' : '#1f2937',
    borderRadius: '12px',
    minHeight: '600px'
  }),
  loading: {
    textAlign: 'center',
    padding: '40px',
    fontSize: '18px'
  },
  error: {
    textAlign: 'center',
    padding: '40px',
    color: '#ef4444',
    fontSize: '18px'
  },
  retryButton: {
    display: 'block',
    margin: '20px auto',
    padding: '10px 20px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px'
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
    margin: 0
  },
  periodSelector: {
    display: 'flex',
    gap: '10px'
  },
  select: (darkMode) => ({
    padding: '8px 12px',
    borderRadius: '6px',
    border: `1px solid ${darkMode ? '#374151' : '#e5e7eb'}`,
    backgroundColor: darkMode ? '#374151' : '#fff',
    color: darkMode ? '#e5e7eb' : '#1f2937',
    fontSize: '14px',
    cursor: 'pointer'
  }),
  tabNav: {
    display: 'flex',
    gap: '10px',
    marginBottom: '30px',
    borderBottom: '2px solid #e5e7eb',
    paddingBottom: '10px'
  },
  tabButton: (darkMode, isActive) => ({
    padding: '10px 20px',
    backgroundColor: isActive ? '#3b82f6' : 'transparent',
    color: isActive ? '#fff' : darkMode ? '#9ca3af' : '#6b7280',
    border: 'none',
    borderRadius: '6px 6px 0 0',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: isActive ? 'bold' : 'normal',
    transition: 'all 0.2s ease'
  }),
  tabContent: {
    minHeight: '400px'
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px'
  },
  card: (darkMode) => ({
    padding: '20px',
    backgroundColor: darkMode ? '#374151' : '#f3f4f6',
    borderRadius: '8px',
    textAlign: 'center',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
  }),
  cardTitle: {
    fontSize: '14px',
    fontWeight: '500',
    marginBottom: '10px',
    opacity: 0.8
  },
  cardValue: {
    fontSize: '32px',
    fontWeight: 'bold',
    marginBottom: '5px'
  },
  cardSubtext: {
    fontSize: '12px',
    opacity: 0.6
  },
  insightsSection: (darkMode) => ({
    padding: '20px',
    backgroundColor: darkMode ? '#374151' : '#f9fafb',
    borderRadius: '8px',
    marginBottom: '30px'
  }),
  sectionTitle: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '15px'
  },
  insightsList: {
    listStyle: 'none',
    padding: 0,
    margin: 0
  },
  insightItem: {
    padding: '10px 0',
    borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
    display: 'flex',
    alignItems: 'flex-start'
  },
  insightBullet: {
    color: '#3b82f6',
    marginRight: '10px',
    fontSize: '20px'
  },
  chartSection: (darkMode) => ({
    marginBottom: '30px',
    padding: '20px',
    backgroundColor: darkMode ? '#374151' : '#f9fafb',
    borderRadius: '8px'
  }),
  chartNote: {
    textAlign: 'center',
    marginTop: '10px',
    fontSize: '14px',
    opacity: 0.7
  },
  emotionalStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginTop: '20px'
  },
  consistencyGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '15px',
    marginTop: '20px'
  },
  consistencyCard: (darkMode) => ({
    padding: '15px',
    backgroundColor: darkMode ? '#1f2937' : '#fff',
    borderRadius: '6px',
    textAlign: 'center',
    border: `1px solid ${darkMode ? '#4b5563' : '#e5e7eb'}`
  }),
  consistencyLabel: {
    fontSize: '12px',
    opacity: 0.7,
    marginBottom: '5px'
  },
  consistencyValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#3b82f6'
  },
  keywordCloud: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '15px',
    justifyContent: 'center',
    padding: '20px'
  },
  keyword: {
    display: 'inline-block',
    padding: '5px 15px',
    backgroundColor: '#3b82f6',
    color: 'white',
    borderRadius: '20px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'transform 0.2s ease',
    '&:hover': {
      transform: 'scale(1.1)'
    }
  }
};

export default AnalyticsDashboard;
