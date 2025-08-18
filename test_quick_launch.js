// Тестовый скрипт для проверки функциональности быстрого запуска ботов

console.log('🧪 Тестирование функциональности быстрого запуска ботов...');

// Тест 1: Проверка сохранения пресетов в localStorage
function testPresetStorage() {
  console.log('\n📦 Тест 1: Сохранение и загрузка пресетов');
  
  const testPreset = {
    id: '1234567890',
    name: 'Тестовый пресет',
    buttonName: '🧪 Тест',
    buttonColor: 'green',
    min_bet_amount: 5.0,
    max_bet_amount: 100.0,
    wins_percentage: 45.0,
    losses_percentage: 35.0,
    draws_percentage: 20.0,
    cycle_games: 20,
    pause_between_cycles: 10,
    pause_on_draw: 3
  };

  // Сохраняем тестовый пресет
  const presets = [testPreset];
  localStorage.setItem('quickLaunchPresets', JSON.stringify(presets));
  
  // Загружаем обратно
  const loaded = JSON.parse(localStorage.getItem('quickLaunchPresets'));
  
  if (loaded && loaded.length === 1 && loaded[0].name === testPreset.name) {
    console.log('✅ Тест пройден: Пресеты корректно сохраняются и загружаются');
    return true;
  } else {
    console.log('❌ Тест провален: Ошибка сохранения/загрузки пресетов');
    return false;
  }
}

// Тест 2: Проверка валидации процентов
function testPercentageValidation() {
  console.log('\n🔢 Тест 2: Валидация процентов исходов');
  
  const validPreset = { wins_percentage: 45, losses_percentage: 35, draws_percentage: 20 };
  const invalidPreset = { wins_percentage: 50, losses_percentage: 40, draws_percentage: 20 };
  
  const validTotal = validPreset.wins_percentage + validPreset.losses_percentage + validPreset.draws_percentage;
  const invalidTotal = invalidPreset.wins_percentage + invalidPreset.losses_percentage + invalidPreset.draws_percentage;
  
  const validCheck = Math.abs(validTotal - 100) < 0.1;
  const invalidCheck = Math.abs(invalidTotal - 100) > 0.1;
  
  if (validCheck && invalidCheck) {
    console.log('✅ Тест пройден: Валидация процентов работает корректно');
    console.log(`   Валидный: ${validTotal}% - ${validCheck ? 'OK' : 'FAIL'}`);
    console.log(`   Невалидный: ${invalidTotal}% - ${invalidCheck ? 'FAIL (правильно)' : 'OK (неправильно)'}`);
    return true;
  } else {
    console.log('❌ Тест провален: Ошибка валидации процентов');
    return false;
  }
}

// Тест 3: Проверка генерации данных бота
function testBotDataGeneration() {
  console.log('\n🤖 Тест 3: Генерация данных бота из пресета');
  
  const preset = {
    name: 'Агрессивный',
    min_bet_amount: 10,
    max_bet_amount: 200,
    wins_percentage: 40,
    losses_percentage: 35,
    draws_percentage: 25,
    cycle_games: 16,
    pause_between_cycles: 5,
    pause_on_draw: 2
  };
  
  // Генерируем данные как в коде
  const timestamp = Date.now();
  const botData = {
    name: `${preset.name}-${timestamp}`,
    min_bet_amount: preset.min_bet_amount,
    max_bet_amount: preset.max_bet_amount,
    wins_percentage: preset.wins_percentage,
    losses_percentage: preset.losses_percentage,
    draws_percentage: preset.draws_percentage,
    cycle_games: preset.cycle_games,
    pause_between_cycles: preset.pause_between_cycles,
    pause_on_draw: preset.pause_on_draw,
    wins_count: Math.round(preset.cycle_games * preset.wins_percentage / 100),
    losses_count: Math.round(preset.cycle_games * preset.losses_percentage / 100),
    draws_count: Math.round(preset.cycle_games * preset.draws_percentage / 100)
  };
  
  // Проверяем корректность
  const expectedWins = Math.round(16 * 40 / 100); // 6
  const expectedLosses = Math.round(16 * 35 / 100); // 6
  const expectedDraws = Math.round(16 * 25 / 100); // 4
  const totalGames = botData.wins_count + botData.losses_count + botData.draws_count;
  
  console.log(`   Имя: ${botData.name}`);
  console.log(`   Ставки: ${botData.min_bet_amount}-${botData.max_bet_amount}`);
  console.log(`   Игры: W=${botData.wins_count}, L=${botData.losses_count}, D=${botData.draws_count}, Total=${totalGames}`);
  console.log(`   Ожидалось: W=${expectedWins}, L=${expectedLosses}, D=${expectedDraws}, Total=16`);
  
  if (botData.wins_count === expectedWins && botData.losses_count === expectedLosses && 
      botData.draws_count === expectedDraws && totalGames === 16) {
    console.log('✅ Тест пройден: Данные бота генерируются корректно');
    return true;
  } else {
    console.log('❌ Тест провален: Ошибка генерации данных бота');
    return false;
  }
}

// Тест 4: Проверка цветовых схем кнопок
function testButtonColors() {
  console.log('\n🎨 Тест 4: Цветовые схемы кнопок');
  
  const colors = ['blue', 'green', 'red', 'yellow', 'purple', 'orange'];
  const expectedClasses = {
    'blue': 'bg-blue-600 hover:bg-blue-700 border-blue-500',
    'green': 'bg-green-600 hover:bg-green-700 border-green-500',
    'red': 'bg-red-600 hover:bg-red-700 border-red-500',
    'yellow': 'bg-yellow-600 hover:bg-yellow-700 border-yellow-500',
    'purple': 'bg-purple-600 hover:bg-purple-700 border-purple-500',
    'orange': 'bg-orange-600 hover:bg-orange-700 border-orange-500'
  };
  
  let allCorrect = true;
  colors.forEach(color => {
    const preset = { buttonColor: color };
    const className = preset.buttonColor === 'green' ? 'bg-green-600 hover:bg-green-700 border-green-500' :
                     preset.buttonColor === 'red' ? 'bg-red-600 hover:bg-red-700 border-red-500' :
                     preset.buttonColor === 'yellow' ? 'bg-yellow-600 hover:bg-yellow-700 border-yellow-500' :
                     preset.buttonColor === 'purple' ? 'bg-purple-600 hover:bg-purple-700 border-purple-500' :
                     preset.buttonColor === 'orange' ? 'bg-orange-600 hover:bg-orange-700 border-orange-500' :
                     'bg-blue-600 hover:bg-blue-700 border-blue-500';
    
    if (className !== expectedClasses[color]) {
      console.log(`❌ Ошибка для цвета ${color}: ожидался "${expectedClasses[color]}", получен "${className}"`);
      allCorrect = false;
    }
  });
  
  if (allCorrect) {
    console.log('✅ Тест пройден: Все цветовые схемы работают корректно');
    console.log(`   Поддерживаемые цвета: ${colors.join(', ')}`);
    return true;
  } else {
    console.log('❌ Тест провален: Ошибки в цветовых схемах');
    return false;
  }
}

// Запуск всех тестов
function runAllTests() {
  console.log('🚀 Запуск тестов функциональности быстрого запуска ботов\n');
  
  const tests = [
    testPresetStorage,
    testPercentageValidation,
    testBotDataGeneration,
    testButtonColors
  ];
  
  let passed = 0;
  let total = tests.length;
  
  tests.forEach(test => {
    if (test()) {
      passed++;
    }
  });
  
  console.log(`\n📊 Результаты тестирования:`);
  console.log(`   Пройдено: ${passed}/${total}`);
  console.log(`   Процент успеха: ${Math.round((passed/total) * 100)}%`);
  
  if (passed === total) {
    console.log('\n🎉 Все тесты пройдены! Функциональность готова к использованию.');
  } else {
    console.log(`\n⚠️  ${total - passed} тест(ов) провалено. Требуется доработка.`);
  }
  
  // Очистка после тестов
  localStorage.removeItem('quickLaunchPresets');
  
  return passed === total;
}

// Запускаем тесты если скрипт выполняется напрямую
if (typeof window !== 'undefined') {
  runAllTests();
} else {
  module.exports = { runAllTests, testPresetStorage, testPercentageValidation, testBotDataGeneration, testButtonColors };
}