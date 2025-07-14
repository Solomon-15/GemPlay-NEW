import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const ProfitChart = ({ type, data, options = {}, title }) => {
  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20,
          color: '#e2e8f0',
          font: {
            family: 'Rajdhani',
            size: 12,
            weight: 'bold'
          }
        }
      },
      title: {
        display: !!title,
        text: title,
        color: '#e2e8f0',
        font: {
          family: 'Rajdhani',
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#e2e8f0',
        bodyColor: '#e2e8f0',
        borderColor: '#4a90e2',
        borderWidth: 1,
        titleFont: {
          family: 'Rajdhani',
          weight: 'bold'
        },
        bodyFont: {
          family: 'Rajdhani'
        }
      }
    },
    scales: type !== 'doughnut' ? {
      x: {
        grid: {
          color: 'rgba(74, 144, 226, 0.1)'
        },
        ticks: {
          color: '#a0a0a0',
          font: {
            family: 'Rajdhani',
            size: 11
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(74, 144, 226, 0.1)'
        },
        ticks: {
          color: '#a0a0a0',
          font: {
            family: 'Rajdhani',
            size: 11
          },
          callback: function(value) {
            return '$' + value.toFixed(2);
          }
        }
      }
    } : undefined,
    ...options
  };

  const chartProps = {
    data,
    options: defaultOptions
  };

  const renderChart = () => {
    switch (type) {
      case 'line':
        return <Line {...chartProps} />;
      case 'bar':
        return <Bar {...chartProps} />;
      case 'doughnut':
        return <Doughnut {...chartProps} />;
      default:
        return <Line {...chartProps} />;
    }
  };

  return (
    <div className="w-full h-64 p-4">
      {renderChart()}
    </div>
  );
};

export default ProfitChart;