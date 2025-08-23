#!/usr/bin/env python3
import asyncio
import aiohttp
import time

BACKEND_URL = "https://revenue-tracker-21.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

# Базовые настройки теста
MIN_BET = 1
MAX_BET = 100
CYCLE_GAMES = 16
WINS_COUNT = 6
LOSSES_COUNT = 6
DRAWS_COUNT = 4
WINS_PCT = 39.60
LOSSES_PCT = 32.40
DRAWS_PCT = 28.00
EXPECTED_TOTAL = 800
EXPECTED_ROI = 10.07  # ±0.2% допуска


async def login(session: aiohttp.ClientSession) -> str:
	async with session.post(f"{BACKEND_URL}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}) as resp:
		resp.raise_for_status()
		data = await resp.json()
		return data["access_token"]


async def create_bot(session: aiohttp.ClientSession, token: str, name: str) -> str:
	headers = {"Authorization": f"Bearer {token}"}
	payload = {
		"name": name,
		"min_bet_amount": MIN_BET,
		"max_bet_amount": MAX_BET,
		"wins_count": WINS_COUNT,
		"losses_count": LOSSES_COUNT,
		"draws_count": DRAWS_COUNT,
		"wins_percentage": WINS_PCT,
		"losses_percentage": LOSSES_PCT,
		"draws_percentage": DRAWS_PCT,
		"cycle_games": CYCLE_GAMES,
		"pause_between_cycles": 5
	}
	async with session.post(f"{BACKEND_URL}/admin/bots/create-regular", json=payload, headers=headers) as resp:
		resp.raise_for_status()
		data = await resp.json()
		return data.get("created_bot_id") or data.get("bot_id") or data.get("id")


async def recalc_bets(session: aiohttp.ClientSession, token: str, bot_id: str) -> None:
	headers = {"Authorization": f"Bearer {token}"}
	async with session.post(f"{BACKEND_URL}/admin/bots/{bot_id}/recalculate-bets", headers=headers) as resp:
		resp.raise_for_status()


async def get_cycle_bets(session: aiohttp.ClientSession, token: str, bot_id: str) -> dict:
	headers = {"Authorization": f"Bearer {token}"}
	async with session.get(f"{BACKEND_URL}/admin/bots/{bot_id}/cycle-bets", headers=headers) as resp:
		resp.raise_for_status()
		return await resp.json()


async def delete_bot(session: aiohttp.ClientSession, token: str, bot_id: str) -> None:
	headers = {"Authorization": f"Bearer {token}"}
	async with session.delete(f"{BACKEND_URL}/admin/bots/{bot_id}/delete", headers=headers, json={"reason": "test cleanup"}) as resp:
		# допускаем 404 если уже удалён
		if resp.status not in (200, 204, 404):
			raise RuntimeError(f"Delete failed: {resp.status}")


async def run_once(run_id: int) -> bool:
	async with aiohttp.ClientSession() as session:
		token = await login(session)
		name = f"DupCheckBot#{int(time.time())}_{run_id}"
		bot_id = await create_bot(session, token, name)
		assert bot_id, "Не удалось получить id созданного бота"

		# Форсируем генерацию ставок
		await recalc_bets(session, token, bot_id)
		# Дадим системе секунду на запись
		await asyncio.sleep(0.5)

		data = await get_cycle_bets(session, token, bot_id)
		bets = data.get("bets", [])
		sums = data.get("sums", {})

		# Базовые проверки количества ставок и уникальности id/index
		assert isinstance(bets, list) and len(bets) == CYCLE_GAMES, f"Ожидалось {CYCLE_GAMES} ставок, получено {len(bets)}"
		ids = [b.get("id") for b in bets if b.get("id")]
		assert len(set(ids)) == len(ids) == CYCLE_GAMES, "Найдены дубликаты ставок (id)"
		idxs = [b.get("index") for b in bets if b.get("index") is not None]
		if idxs:  # индекс может отсутствовать в API
			assert len(set(idxs)) == len(idxs), "Найдены дубликаты индексов"

		# Суммы по API
		wins_sum = int(sums.get("wins_sum", 0))
		losses_sum = int(sums.get("losses_sum", 0))
		draws_sum = int(sums.get("draws_sum", 0))
		total_sum = int(sums.get("total_sum", 0))
		active_pool = int(sums.get("active_pool", 0))
		profit = int(sums.get("profit", 0))
		roi_active = float(sums.get("roi_active", 0.0))

		# Проверки на удвоение и корректность
		assert total_sum == wins_sum + losses_sum + draws_sum, "total_sum != W+L+D"
		assert total_sum == EXPECTED_TOTAL, f"Ожидалась база {EXPECTED_TOTAL}, а не {total_sum}"
		assert active_pool == wins_sum + losses_sum, "active_pool != W+L"
		assert profit == wins_sum - losses_sum, "profit != W−L"
		assert abs(roi_active - EXPECTED_ROI) <= 0.2, f"ROI {roi_active}% вне допуска"

		print(f"✅ Прогон {run_id}: W={wins_sum}, L={losses_sum}, D={draws_sum}, Σ={total_sum}, Активный пул={active_pool}, Прибыль={profit}, ROI={roi_active:.2f}%")

		# Удаляем бота
		await delete_bot(session, token, bot_id)
		return True


async def main():
	print("🚀 HTTP‑тест на конфликты/дубликаты: база 800, ROI 10%, 16 игр")
	ok = True
	for i in range(1, 4):
		try:
			res = await run_once(i)
			ok = ok and res
		except AssertionError as e:
			print(f"❌ Прогон {i} не прошёл: {e}")
			ok = False
		except Exception as e:
			print(f"❌ Ошибка прогона {i}: {e}")
			ok = False
	
	if ok:
		print("\n🎉 Все 3 прогона прошли. Дубликатов и конфликтов не обнаружено.")
	else:
		print("\n⚠️ Обнаружены проблемы. Проверьте логи бэкенда и эндпоинты генерации.")


if __name__ == "__main__":
	asyncio.run(main())