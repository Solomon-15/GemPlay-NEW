# Валидация потока выполнения логики паузы

## Поток выполнения функции maintain_all_bots_active_bets()

### 1. Инициализация (каждые 5 секунд)
```
1. Загружаем список активных ботов: active_bots = await db.bots.find({"is_active": True, "bot_type": "REGULAR"})
2. Для каждого бота в списке:
```

### 2. Получение свежих данных бота
```
2.1. bot_id = bot_doc["id"]
2.2. fresh_bot_doc = await db.bots.find_one({"id": bot_id})  ✅ ИСПРАВЛЕНО
2.3. Если fresh_bot_doc None или неактивен → continue
2.4. cycle_games = fresh_bot_doc.get("cycle_games", 12)
```

### 3. Подсчет текущего состояния
```
3.1. current_active_bets = count WAITING games для bot_id
3.2. current_wins = fresh_bot_doc.get("current_cycle_wins", 0)
3.3. current_losses = fresh_bot_doc.get("current_cycle_losses", 0)
3.4. current_draws = fresh_bot_doc.get("current_cycle_draws", 0)
3.5. games_played = current_wins + current_losses + current_draws
3.6. cycle_completed = games_played >= cycle_games
```

### 4. Основная логика принятия решений

#### Ветка A: current_active_bets > 0
```
Действие: continue (ничего не делаем)
Логи: "Bot X: Y active bets, cycle progress: Z/W"
```

#### Ветка B: current_active_bets == 0 AND cycle_completed == True
```
B.1. last_cycle_completed_at = fresh_bot_doc.get("last_cycle_completed_at")
B.2. pause_between_cycles = fresh_bot_doc.get("pause_between_cycles", 5)

  Подветка B.1: last_cycle_completed_at == None
  ```
  Действие: Начать паузу
  1. cycle_completion_time = datetime.utcnow()
  2. UPDATE bots SET last_cycle_completed_at = cycle_completion_time WHERE id = bot_id
  3. continue (не создаем цикл)
  Логи: "🏁 Bot X: cycle completed, starting pause of Ys before next cycle"
  ```

  Подветка B.2: last_cycle_completed_at != None
  ```
  1. current_time = datetime.utcnow()
  2. time_since_completion = (current_time - last_cycle_completed_at).total_seconds()
  
    Подподветка B.2.1: time_since_completion < pause_between_cycles
    ```
    Действие: Пауза продолжается
    1. remaining_pause = pause_between_cycles - time_since_completion
    2. continue (не создаем цикл)
    Логи: "🕐 Bot X: pause in progress, Y.Ys remaining"
    ```
    
    Подподветка B.2.2: time_since_completion >= pause_between_cycles
    ```
    Действие: Создать новый цикл
    1. DELETE games WHERE creator_id = bot_id AND status = "COMPLETED"
    2. UPDATE bots SET current_cycle_wins=0, losses=0, draws=0, profit=0.0, UNSET last_cycle_completed_at
    3. updated_bot_doc = SELECT bot WHERE id = bot_id
    4. create_full_bot_cycle(updated_bot_doc)
    Логи: "✅ Bot X: pause completed, creating new cycle"
           "🗑️ Bot X: deleted Y completed games"
           "✅ Bot X created new cycle of Z bets"
    ```
  ```
```

#### Ветка C: current_active_bets == 0 AND cycle_completed == False AND games_played == 0
```
Действие: Создать первый цикл
1. create_full_bot_cycle(fresh_bot_doc)
Логи: "🎯 Bot X: starting initial cycle"
      "✅ Bot X created initial cycle of Y bets"
```

#### Ветка D: current_active_bets == 0 AND cycle_completed == False AND games_played > 0
```
Действие: Ничего не делаем (цикл в процессе, но нет активных ставок)
Логи: отсутствуют (нормальная ситуация)
```

## Проверка корректности логики

### ✅ Сценарий 1: Новый бот
```
Состояние: games_played = 0, current_active_bets = 0, cycle_completed = False
Ветка: C
Результат: Создается первый цикл ✅
```

### ✅ Сценарий 2: Цикл только что завершился
```
Состояние: games_played = 12, current_active_bets = 0, cycle_completed = True, last_cycle_completed_at = None
Ветка: B → B.1
Результат: Начинается пауза, цикл НЕ создается ✅
```

### ✅ Сценарий 3: Пауза активна
```
Состояние: games_played = 12, current_active_bets = 0, cycle_completed = True, 
           last_cycle_completed_at = 3 секунды назад, pause_between_cycles = 10
Ветка: B → B.2 → B.2.1
Результат: Пауза продолжается, цикл НЕ создается ✅
```

### ✅ Сценарий 4: Пауза завершена
```
Состояние: games_played = 12, current_active_bets = 0, cycle_completed = True,
           last_cycle_completed_at = 15 секунд назад, pause_between_cycles = 10
Ветка: B → B.2 → B.2.2
Результат: Сбрасывается статистика, создается новый цикл ✅
```

### ✅ Сценарий 5: После создания нового цикла (следующая итерация)
```
Состояние: games_played = 0 (сброшен), current_active_bets = 12 (новые ставки), cycle_completed = False
Ветка: A
Результат: Ничего не происходит (активные ставки есть) ✅
```

### ✅ Сценарий 6: Цикл в процессе
```
Состояние: games_played = 5, current_active_bets = 7, cycle_completed = False
Ветка: A  
Результат: Ничего не происходит ✅
```

## Критические исправления, которые были сделаны:

### 🔧 Исправление 1: Свежие данные бота
**Проблема:** Использовались кэшированные данные `bot_doc` из начального запроса
**Решение:** Добавлен `fresh_bot_doc = await db.bots.find_one({"id": bot_id})` для каждого бота

### 🔧 Исправление 2: Обновленные данные для create_full_bot_cycle
**Проблема:** После сброса статистики передавались старые данные в create_full_bot_cycle
**Решение:** Добавлен `updated_bot_doc = await db.bots.find_one({"id": bot_id})` после сброса

### 🔧 Исправление 3: Безопасное логирование
**Проблема:** Небезопасное обращение к `bot_doc['name']`
**Решение:** Заменено на `fresh_bot_doc.get('name', 'Unknown')`

## Оставшиеся потенциальные проблемы:

### ⚠️ Потенциальная проблема 1: Производительность
**Проблема:** Каждый бот делает дополнительный запрос к БД
**Оценка:** Не критично для небольшого количества ботов (<100)

### ⚠️ Потенциальная проблема 2: Race conditions
**Проблема:** Между получением fresh_bot_doc и обновлением может произойти изменение
**Оценка:** Маловероятно, так как функция выполняется последовательно

### ⚠️ Потенциальная проблема 3: Часовые пояса
**Проблема:** Использование datetime.utcnow() может вызвать проблемы при смене времени
**Оценка:** Не критично, так как используется относительное время

## Вывод: Логика корректна ✅

Поток выполнения теперь работает правильно:
1. Пауза срабатывает только после завершения цикла
2. Пауза активируется автоматически
3. Новый цикл создается только после завершения паузы
4. Нет дублирования или ложных срабатываний