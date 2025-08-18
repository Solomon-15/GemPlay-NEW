export const generatePeriodLabels = (period) => {
  const now = new Date();
  const labels = [];
  
  switch (period) {
    case 'day':
      for (let i = 23; i >= 0; i--) {
        const date = new Date(now);
        date.setHours(date.getHours() - i);
        labels.push(date.getHours().toString().padStart(2, '0') + ':00');
      }
      break;
      
    case 'week':
      for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric' }));
      }
      break;
      
    case 'month':
      for (let i = 3; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - (i * 7));
        labels.push(`${date.getDate()}.${(date.getMonth() + 1).toString().padStart(2, '0')}`);
      }
      break;
      
    case 'all':
      for (let i = 11; i >= 0; i--) {
        const date = new Date(now);
        date.setMonth(date.getMonth() - i);
        labels.push(date.toLocaleDateString('ru-RU', { month: 'short', year: '2-digit' }));
      }
      break;
      
    default:
      return ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
  }
  
  return labels;
};

export const generateMockChartData = (period, type, values) => {
  const labels = generatePeriodLabels(period);
  const dataLength = labels.length;
  
  if (!values) {
    values = Array.from({ length: dataLength }, () => Math.random() * 1000 + 100);
  }
  
  const colors = {
    blue: {
      background: 'rgba(74, 144, 226, 0.2)',
      border: 'rgba(74, 144, 226, 1)',
      point: 'rgba(74, 144, 226, 1)'
    },
    green: {
      background: 'rgba(34, 197, 94, 0.2)',
      border: 'rgba(34, 197, 94, 1)',
      point: 'rgba(34, 197, 94, 1)'
    },
    yellow: {
      background: 'rgba(251, 191, 36, 0.2)',
      border: 'rgba(251, 191, 36, 1)',
      point: 'rgba(251, 191, 36, 1)'
    },
    red: {
      background: 'rgba(239, 68, 68, 0.2)',
      border: 'rgba(239, 68, 68, 1)',
      point: 'rgba(239, 68, 68, 1)'
    },
    purple: {
      background: 'rgba(147, 51, 234, 0.2)',
      border: 'rgba(147, 51, 234, 1)',
      point: 'rgba(147, 51, 234, 1)'
    },
    orange: {
      background: 'rgba(249, 115, 22, 0.2)',
      border: 'rgba(249, 115, 22, 1)',
      point: 'rgba(249, 115, 22, 1)'
    }
  };
  
  return {
    labels,
    datasets: [{
      label: 'Доход',
      data: values,
      backgroundColor: colors[type]?.background || colors.blue.background,
      borderColor: colors[type]?.border || colors.blue.border,
      pointBackgroundColor: colors[type]?.point || colors.blue.point,
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
      borderWidth: 2,
      fill: true,
      tension: 0.4
    }]
  };
};

export const generateRevenueBreakdownData = (breakdownData) => {
  const colors = [
    'rgba(74, 144, 226, 0.8)',   // Комиссия от ставок
    'rgba(34, 197, 94, 0.8)',    // Доход от ботов
    'rgba(251, 191, 36, 0.8)',   // Комиссия от подарков
    'rgba(147, 51, 234, 0.8)',   // Дополнительные доходы
    'rgba(249, 115, 22, 0.8)',   // Прочие доходы
  ];
  
  const borderColors = [
    'rgba(74, 144, 226, 1)',
    'rgba(34, 197, 94, 1)',
    'rgba(251, 191, 36, 1)',
    'rgba(147, 51, 234, 1)',
    'rgba(249, 115, 22, 1)',
  ];
  
  return {
    labels: breakdownData.map(item => item.name || item.source),
    datasets: [{
      data: breakdownData.map(item => item.amount || 0),
      backgroundColor: colors.slice(0, breakdownData.length),
      borderColor: borderColors.slice(0, breakdownData.length),
      borderWidth: 2,
      hoverOffset: 4
    }]
  };
};

export const generateExpensesData = (period) => {
  const labels = generatePeriodLabels(period);
  const operationalData = labels.map(() => Math.random() * 200 + 50);
  const additionalData = labels.map(() => Math.random() * 100 + 20);
  
  return {
    labels,
    datasets: [
      {
        label: 'Операционные расходы',
        data: operationalData,
        backgroundColor: 'rgba(239, 68, 68, 0.6)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 2
      },
      {
        label: 'Дополнительные расходы',
        data: additionalData,
        backgroundColor: 'rgba(249, 115, 22, 0.6)',
        borderColor: 'rgba(249, 115, 22, 1)',
        borderWidth: 2
      }
    ]
  };
};

export const generateNetProfitData = (period) => {
  const labels = generatePeriodLabels(period);
  const revenueData = labels.map(() => Math.random() * 1000 + 500);
  const expensesData = labels.map((_, index) => revenueData[index] * 0.3 + Math.random() * 100);
  const netProfitData = labels.map((_, index) => revenueData[index] - expensesData[index]);
  
  return {
    labels,
    datasets: [
      {
        label: 'Доходы',
        data: revenueData,
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Расходы',
        data: expensesData,
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        borderColor: 'rgba(239, 68, 68, 1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Чистая прибыль',
        data: netProfitData,
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4
      }
    ]
  };
};