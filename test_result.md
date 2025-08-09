backend:
  - task: "Regular Bots API Comprehensive Testing - Russian Review"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "critical"
    needs_retesting: false
    status_history:
      - working: true
        agent: "testing"
        comment: "🎉 REGULAR BOTS API COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY! Conducted thorough testing of all Regular Bots API endpoints as specifically requested in the Russian review. CRITICAL SUCCESS RATE: 91.7% (11/12 tests passed). ALL MAJOR RUSSIAN REVIEW REQUIREMENTS VERIFIED: ✅ ..."

frontend:
  - task: "Legacy cleanup + Draw logic alignment (Implementation)"
    implemented: true
    working: pending
    file: "/app/backend/server.py, /app/frontend/src/components/RegularBotsManagement.js, /app/scripts/migrations/remove_legacy_fields.py"
    stuck_count: 0
    priority: "critical"
    needs_retesting: true
    status_history:
      - working: false
        agent: "main_agent"
        comment: "Удалены legacy поля win_percentage, creation_mode, profit_strategy из ключевых API (создание/обновление/списки), фронтенд очищен от отправки этих полей и обновлены вызовы на /recalculate-bets. Исправлена логика ничьих: ничьи входят в N игр цикла и замены не создаются. Внесены правки в расчёт суммы цикла и ROI Active, добавлен скрипт миграции для очистки старых полей. Требуется повторное тестирование бэкенда."