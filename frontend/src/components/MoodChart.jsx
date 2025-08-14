import React from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function MoodChart({ memories }) {
  const moodCounts = {};

  memories.forEach(mem => {
    const mood = mem.mood || 'Unknown';
    moodCounts[mood] = (moodCounts[mood] || 0) + 1;
  });

  const data = {
    labels: Object.keys(moodCounts),
    datasets: [
      {
        label: 'Mood Count',
        data: Object.values(moodCounts),
        backgroundColor: [
          '#a5f3fc', '#d8b4fe', '#fcd34d', '#fca5a5', '#bbf7d0', '#c7d2fe'
        ],
        borderRadius: 6,
      }
    ],
  };

  const options = {
    plugins: {
      legend: {
        labels: {
          color: '#334155',
          font: { size: 14, weight: 'bold' }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#475569' },
        grid: { display: false }
      },
      y: {
        beginAtZero: true,
        ticks: { color: '#475569' },
        grid: { color: '#e2e8f0' }
      }
    },
  };

  return (
    <div style={{ marginTop: 30, background: '#f9fafb', padding: 20, borderRadius: 12, boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
      <h3 style={{ marginBottom: 10, color: '#1e293b' }}>📊 Mood Analytics</h3>
      <Bar data={data} options={options} />
    </div>
  );
}

export default MoodChart;
