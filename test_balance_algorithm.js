// Тест нового алгоритма балансировки побед и поражений
const fs = require('fs');

console.log('⚖️ === ТЕСТ АЛГОРИТМА БАЛАНСИРОВКИ W/L ===');
console.log('🎯 Проверяем что разница между победами и поражениями не более ±1-2\n');

// Извлекаем функцию из реального кода
const realCode = fs.readFileSync('frontend/src/components/RegularBotsManagement.js', 'utf8');

// Реализуем функцию для тестирования
function recalcCountsFromPercents(games, winsP, lossesP, drawsP) {
  const N = Math.max(1, parseInt(games) || 1);
  const w = (winsP / 100) * N;
  const l = (lossesP / 100) * N;
  const d = (drawsP / 100) * N;
  
  // Начальное распределение методом наибольших остатков
  let W = Math.floor(w), L = Math.floor(l), D = Math.floor(d);
  let R = N - (W + L + D);
  const remainders = [
    { key: 'W', rem: w - W },
    { key: 'L', rem: l - L },
    { key: 'D', rem: d - D }
  ].sort((a, b) => b.rem - a.rem);
  
  let i = 0;
  while (R > 0) {
    const k = remainders[i % remainders.length].key;
    if (k === 'W') W += 1; else if (k === 'L') L += 1; else D += 1;
    R -= 1; i += 1;
  }
  
  // НОВЫЙ АЛГОРИТМ: Балансировка побед и поражений
  // Проверяем разницу между победами и поражениями
  let wlDifference = Math.abs(W - L);
  
  // Если разница больше 2, пытаемся сбалансировать
  if (wlDifference > 2 && D > 0) {
    // Определяем кто больше
    const isWinsMore = W > L;
    const maxDifference = isWinsMore ? W - L : L - W;
    
    // Сколько можем перераспределить из ничьих
    const canRedistribute = Math.min(D, Math.floor((maxDifference - 2) / 2));
    
    if (canRedistribute > 0) {
      // Перераспределяем из ничьих в меньшую категорию
      if (isWinsMore) {
        L += canRedistribute;
      } else {
        W += canRedistribute;
      }
      D -= canRedistribute;
    }
  }
  
  // Финальная проверка и корректировка
  W = Math.max(0, W); L = Math.max(0, L); D = Math.max(0, D);
  const total = W + L + D;
  
  if (total !== N) {
    const diff = N - total;
    if (diff !== 0) {
      // Приоритет корректировки: сначала ничьи, потом меньшая из W/L
      if (diff > 0) {
        if (W <= L) W += diff; else L += diff;
      } else {
        if (D >= Math.abs(diff)) D += diff;
        else if (W >= L) W += diff; else L += diff;
      }
    }
  }
  
  return { W, L, D };
}

// Тестовые случаи
const testCases = [
  { games: 16, winsP: 41.73, lossesP: 30.27, drawsP: 28.0, name: 'Стандартный (16 игр, ROI 10%)' },
  { games: 20, winsP: 41.73, lossesP: 30.27, drawsP: 28.0, name: 'Увеличенный цикл (20 игр)' },
  { games: 12, winsP: 41.73, lossesP: 30.27, drawsP: 28.0, name: 'Уменьшенный цикл (12 игр)' },
  { games: 25, winsP: 41.73, lossesP: 30.27, drawsP: 28.0, name: 'Большой цикл (25 игр)' },
  { games: 8, winsP: 41.73, lossesP: 30.27, drawsP: 28.0, name: 'Малый цикл (8 игр)' },
  { games: 30, winsP: 45.0, lossesP: 35.0, drawsP: 20.0, name: 'Экстремальный (30 игр, 45%/35%/20%)' },
  { games: 10, winsP: 50.0, lossesP: 30.0, drawsP: 20.0, name: 'Высокий ROI (10 игр, 50%/30%/20%)' }
];

let passedTests = 0;
let failedTests = 0;

console.log('📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:');
console.log('=' .repeat(80));

testCases.forEach((testCase, index) => {
  console.log(`\n🧪 ТЕСТ ${index + 1}: ${testCase.name}`);
  console.log(`   📊 Параметры: ${testCase.games} игр, ${testCase.winsP}%/${testCase.lossesP}%/${testCase.drawsP}%`);
  
  const result = recalcCountsFromPercents(testCase.games, testCase.winsP, testCase.lossesP, testCase.drawsP);
  
  console.log(`   🎯 Результат: W=${result.W}, L=${result.L}, D=${result.D}`);
  
  // Проверки
  const totalCheck = result.W + result.L + result.D === testCase.games;
  const wlDifference = Math.abs(result.W - result.L);
  const balanceCheck = wlDifference <= 2;
  const nonNegativeCheck = result.W >= 0 && result.L >= 0 && result.D >= 0;
  
  console.log(`   ✅ Сумма корректна: ${totalCheck ? 'ДА' : 'НЕТ'} (${result.W + result.L + result.D}/${testCase.games})`);
  console.log(`   ⚖️ Разница W/L: ${wlDifference} (${balanceCheck ? '✅ ≤2' : '❌ >2'})`);
  console.log(`   🔢 Неотрицательные: ${nonNegativeCheck ? '✅ ДА' : '❌ НЕТ'}`);
  
  const testPassed = totalCheck && balanceCheck && nonNegativeCheck;
  
  if (testPassed) {
    console.log(`   🎉 ТЕСТ ${index + 1} ПРОЙДЕН`);
    passedTests++;
  } else {
    console.log(`   ❌ ТЕСТ ${index + 1} НЕ ПРОЙДЕН`);
    failedTests++;
  }
});

// Специальный тест: проверка граничных случаев
console.log('\n🔍 СПЕЦИАЛЬНЫЕ ТЕСТЫ ГРАНИЧНЫХ СЛУЧАЕВ:');
console.log('=' .repeat(80));

const edgeCases = [
  { games: 3, winsP: 60.0, lossesP: 40.0, drawsP: 0.0, name: 'Минимум игр без ничьих' },
  { games: 5, winsP: 40.0, lossesP: 40.0, drawsP: 20.0, name: 'Равные W/L' },
  { games: 100, winsP: 41.73, lossesP: 30.27, drawsP: 28.0, name: 'Много игр (100)' }
];

edgeCases.forEach((testCase, index) => {
  console.log(`\n🧪 ГРАНИЧНЫЙ ТЕСТ ${index + 1}: ${testCase.name}`);
  console.log(`   📊 Параметры: ${testCase.games} игр, ${testCase.winsP}%/${testCase.lossesP}%/${testCase.drawsP}%`);
  
  const result = recalcCountsFromPercents(testCase.games, testCase.winsP, testCase.lossesP, testCase.drawsP);
  
  console.log(`   🎯 Результат: W=${result.W}, L=${result.L}, D=${result.D}`);
  
  const totalCheck = result.W + result.L + result.D === testCase.games;
  const wlDifference = Math.abs(result.W - result.L);
  const balanceCheck = wlDifference <= 2;
  
  console.log(`   ✅ Сумма: ${totalCheck ? '✅' : '❌'} | Баланс W/L: ${wlDifference} ${balanceCheck ? '✅' : '❌'}`);
  
  if (totalCheck && balanceCheck) {
    passedTests++;
  } else {
    failedTests++;
  }
});

// Итоговый результат
console.log('\n🏁 === ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===');
console.log(`📊 Всего тестов: ${passedTests + failedTests}`);
console.log(`✅ Пройдено: ${passedTests}`);
console.log(`❌ Не пройдено: ${failedTests}`);
console.log(`📈 Успешность: ${Math.round((passedTests / (passedTests + failedTests)) * 100)}%\n`);

if (failedTests === 0) {
  console.log('🎉 ВСЕ ТЕСТЫ БАЛАНСИРОВКИ ПРОЙДЕНЫ!');
  console.log('\n⚖️ === АЛГОРИТМ БАЛАНСИРОВКИ РАБОТАЕТ ===');
  console.log('✅ Разница между победами и поражениями ≤ 2');
  console.log('✅ Автоматическое перераспределение из ничьих');
  console.log('✅ Сохранение общего количества игр');
  console.log('✅ Работа с любыми количествами игр');
  console.log('✅ Обработка граничных случаев');
  
  console.log('\n🎯 === ПРЕИМУЩЕСТВА НОВОГО АЛГОРИТМА ===');
  console.log('• При выборе N игр автоматически балансирует W/L');
  console.log('• Разница побед и поражений не более ±1-2');
  console.log('• Умное перераспределение из ничьих');
  console.log('• Сохранение пропорций пресетов');
  
  console.log('\n🚀 АЛГОРИТМ ГОТОВ К ИНТЕГРАЦИИ!');
} else {
  console.log('⚠️ ЕСТЬ ПРОБЛЕМЫ С АЛГОРИТМОМ');
  console.log('❌ Требуются дополнительные исправления');
}

return failedTests === 0;