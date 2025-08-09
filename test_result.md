backend:
  - task: "Regular Bots API Comprehensive Testing - Russian Review"
    implemented: true
    working: false
    file: "/app/backend/server.py"
    stuck_count: 1
    priority: "critical"
    needs_retesting: false
    status_history:
      - working: true
        agent: "testing"
        comment: "🎉 REGULAR BOTS API COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY! Conducted thorough testing of all Regular Bots API endpoints as specifically requested in the Russian review. CRITICAL SUCCESS RATE: 91.7% (11/12 tests passed). ALL MAJOR RUSSIAN REVIEW REQUIREMENTS VERIFIED: ✅ ..."
      - working: false
        agent: "testing"
        comment: "🚨 COMPREHENSIVE POST-LEGACY CLEANUP TESTING FAILED (33.3% success rate). CRITICAL ISSUES FOUND: 1) Legacy fields (win_percentage, creation_mode, profit_strategy) still present in bot details endpoint 2) Missing required fields (active_pool, display, current_cycle_wins/losses/draws, wins/losses/draws_percentage) 3) Old /reset-bets endpoint still exists (should be removed) 4) No metadata.intended_result in game bets 5) /recalculate-bets endpoint working but not creating proper metadata. PASSED: Bot creation without legacy fields, Anti-race conditions (12/12 active bets limit). FAILED: List structure, Bot details structure, Cycle recalculation metadata, Game completion logic. Legacy cleanup is INCOMPLETE."

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