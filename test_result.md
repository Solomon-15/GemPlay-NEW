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
      - working: false
        agent: "testing"
        comment: "🚨 COMPREHENSIVE POST-LEGACY CLEANUP TESTING FAILED (33.3% success rate). CRITICAL ISSUES FOUND: 1) Legacy fields (win_percentage, creation_mode, profit_strategy) still present in bot details endpoint 2) Missing required fields (active_pool, display, current_cycle_wins/losses/draws, wins/losses/draws_percentage) 3) Old /reset-bets endpoint still exists (should be removed) 4) No metadata.intended_result in game bets 5) /recalculate-bets endpoint working but not creating proper metadata. PASSED: Bot creation without legacy fields, Anti-race conditions (12/12 active bets limit). FAILED: List structure, Bot details structure, Cycle recalculation metadata, Game completion logic. Legacy cleanup is INCOMPLETE."
      - working: true
        agent: "testing"
        comment: "✅ RUSSIAN REVIEW REPEAT TEST 2 SUCCESSFUL! Tested /admin/bots/regular/list endpoint after legacy cleanup and flat fields addition. PERFECT COMPLIANCE ACHIEVED: ❌ NO legacy fields found (win_percentage, creation_mode, profit_strategy completely removed), ✅ ALL required fields present (cycle_total_amount, active_pool, cycle_total_display), ✅ Field validations passed (active_pool calculation correct), ✅ cycle_total_info.display field present. Analyzed 3 regular bots, all showing proper structure. SUCCESS RATE: 100% (1/1 tests passed). Legacy cleanup is COMPLETE for Regular Bots List API."

frontend:
  - task: "Legacy cleanup + Draw logic alignment (Implementation)"
    implemented: true
    working: false
    file: "/app/backend/server.py, /app/frontend/src/components/RegularBotsManagement.js, /app/scripts/migrations/remove_legacy_fields.py"
    stuck_count: 1
    priority: "critical"
    needs_retesting: true
    status_history:
      - working: false
        agent: "main_agent"
        comment: "Удалены legacy поля win_percentage, creation_mode, profit_strategy из ключевых API (создание/обновление/списки), фронтенд очищен от отправки этих полей и обновлены вызовы на /recalculate-bets. Исправлена логика ничьих: ничьи входят в N игр цикла и замены не создаются. Внесены правки в расчёт суммы цикла и ROI Active, добавлен скрипт миграции для очистки старых полей. Требуется повторное тестирование бэкенда."
      - working: false
        agent: "testing"
        comment: "Backend testing reveals LEGACY CLEANUP IS INCOMPLETE. Critical backend issues found: 1) Bot details endpoint (/admin/bots/{id}) still returns legacy fields win_percentage, creation_mode, profit_strategy 2) Missing required fields in list endpoint: active_pool, display 3) Missing W/L/D count fields in details endpoint 4) Old /reset-bets endpoint still exists and functional 5) No metadata.intended_result in game bets. Frontend cleanup may be complete but backend API responses still contain legacy data. REQUIRES IMMEDIATE BACKEND FIXES."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "Legacy cleanup + Draw logic alignment (Implementation)"
  stuck_tasks:
    - "Regular Bots API Comprehensive Testing - Russian Review"
  test_all: false
  test_priority: "critical_first"

agent_communication:
  - agent: "main_agent"
    message: "Удалены legacy поля win_percentage, creation_mode, profit_strategy из ключевых API (создание/обновление/списки), фронтенд очищен от отправки этих полей и обновлены вызовы на /recalculate-bets. Исправлена логика ничьих: ничьи входят в N игр цикла и замены не создаются. Внесены правки в расчёт суммы цикла и ROI Active, добавлен скрипт миграции для очистки старых полей. Требуется повторное тестирование бэкенда."
  - agent: "testing"
    message: "🚨 CRITICAL BACKEND TESTING RESULTS: Legacy cleanup is INCOMPLETE. Comprehensive testing of 6 Russian review requirements shows 33.3% success rate (2/6 passed). MAJOR ISSUES: 1) Bot details API still returns legacy fields (win_percentage, creation_mode, profit_strategy) 2) Missing required fields in list/details APIs (active_pool, display, W/L/D counts/percentages) 3) Old /reset-bets endpoint still exists (should be removed) 4) No metadata.intended_result in game bets 5) Cycle recalculation not creating proper metadata. WORKING: Bot creation without legacy fields, Anti-race conditions. REQUIRES IMMEDIATE BACKEND API FIXES before system is functional."