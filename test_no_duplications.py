#!/usr/bin/env python3
import asyncio
import math
from typing import List, Dict

# Тест на отсутствие конфликтов/дубликатов при генерации ставок цикла
# Условия: база 800, диапазон 1–100, N=16, ROI=10% (W% 39.60 / L% 32.40 / D% 28.00)

try:
	from backend.server_temp import generate_cycle_bets_natural_distribution
except Exception as e:
	print(f"❌ Не удалось импортировать генератор ставок: {e}")
	raise


async def run_once(run_id: int) -> bool:
	bot_id = f"test_bot_{run_id}"
	min_bet = 1
	max_bet = 100
	cycle_games = 16
	wins_count = 6
	losses_count = 6
	draws_count = 4
	wins_pct = 39.60
	losses_pct = 32.40
	draws_pct = 28.00

	bets = await generate_cycle_bets_natural_distribution(
		bot_id=bot_id,
		min_bet=min_bet,
		max_bet=max_bet,
		cycle_games=cycle_games,
		wins_count=wins_count,
		losses_count=losses_count,
		draws_count=draws_count,
		wins_percentage=wins_pct,
		losses_percentage=losses_pct,
		draws_percentage=draws_pct,
	)

	# Базовые проверки структуры
	assert isinstance(bets, list), "Результат генерации должен быть списком"
	assert len(bets) == cycle_games, f"Количество ставок должно быть {cycle_games}, а не {len(bets)}"

	# Проверка уникальности индексов (нет удвоения ставок)
	indices = [b.get("index") for b in bets]
	assert len(set(indices)) == cycle_games, "Обнаружены дубликаты индексов ставок (двойное создание)"
	assert min(indices) == 0 and max(indices) == cycle_games - 1, "Индексы ставок должны покрывать 0..N-1"

	# Группировка по исходу
	wins = [b for b in bets if b.get("result") == "win"]
	losses = [b for b in bets if b.get("result") == "loss"]
	draws = [b for b in bets if b.get("result") == "draw"]

	# Проверки баланса количества игр
	assert len(wins) == wins_count, f"Ожидалось {wins_count} побед, получено {len(wins)}"
	assert len(losses) == losses_count, f"Ожидалось {losses_count} поражений, получено {len(losses)}"
	assert len(draws) == draws_count, f"Ожидалось {draws_count} ничьих, получено {len(draws)}"

	# Суммы по категориям (в гемах)
	wins_sum = sum(int(b["amount"]) for b in wins)
	losses_sum = sum(int(b["amount"]) for b in losses)
	draws_sum = sum(int(b["amount"]) for b in draws)
	total_sum = wins_sum + losses_sum + draws_sum

	# База 800: ожидаем ровно 800 (масштабируемая база для 1–100, 16 игр)
	assert total_sum == 800, f"Общая сумма должна быть 800, а не {total_sum}"

	# Активный пул и прибыль
	active_pool = wins_sum + losses_sum
	profit = wins_sum - losses_sum
	roi_active = (profit / active_pool * 100) if active_pool > 0 else 0.0

	# Проверки финансовых формул
	assert active_pool == total_sum - draws_sum, "Активный пул должен быть W+L"
	# Допуск по ROI из-за целочисленности: ±0.2%
	assert abs(roi_active - 10.07) <= 0.2, f"ROI_active вне допуска: {roi_active:.2f}% (ожидалось около 10.07%)"

	print(f"✅ Прогон {run_id}: W={wins_sum}, L={losses_sum}, D={draws_sum}, Σ={total_sum}, Активный пул={active_pool}, Прибыль={profit}, ROI={roi_active:.2f}%")
	return True


async def main():
	print("🚀 Тест на отсутствие конфликтов/дубликатов (база 800, ROI 10%, N=16)")
	ok = True
	for i in range(1, 4):
		try:
			res = await run_once(i)
			ok = ok and res
		except AssertionError as e:
			print(f"❌ Прогон {i} не прошёл: {e}")
			ok = False
		except Exception as e:
			print(f"❌ Ошибка в прогоне {i}: {e}")
			ok = False
	
	if ok:
		print("\n🎉 Все 3 прогона прошли. Конфликтов/дубликатов не обнаружено.")
	else:
		print("\n⚠️ Обнаружены проблемы. Требуется анализ логики генерации/масштабирования.")


if __name__ == "__main__":
	asyncio.run(main())