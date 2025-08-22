#!/usr/bin/env python3
import json
import time
import urllib.request
import urllib.error

BACKEND_URL = "http://localhost:8000"

# Параметры теста (база 800)
CYCLE_GAMES = 16
EXPECTED_TOTAL = 800
EXPECTED_W = 317
EXPECTED_L = 259
EXPECTED_D = 224
EXPECTED_ACTIVE_POOL = 576
EXPECTED_PROFIT = 58
EXPECTED_ROI = 10.07  # допуск ±0.2%


def http_request(method: str, url: str, headers=None, payload=None):
	if headers is None:
		headers = {}
	data = None
	if payload is not None:
		data = json.dumps(payload).encode("utf-8")
		headers.setdefault("Content-Type", "application/json")
	req = urllib.request.Request(url, data=data, headers=headers, method=method)
	try:
		with urllib.request.urlopen(req, timeout=30) as resp:
			body = resp.read()
			if not body:
				return None
			return json.loads(body.decode("utf-8"))
	except urllib.error.HTTPError as e:
		try:
			msg = e.read().decode("utf-8")
		except Exception:
			msg = str(e)
		raise RuntimeError(f"HTTP {e.code} for {url}: {msg}")
	except urllib.error.URLError as e:
		raise RuntimeError(f"URL error for {url}: {e}")


def create_bot(name: str) -> str:
	payload = {"name": name}
	data = http_request("POST", f"{BACKEND_URL}/admin/bots/create", payload=payload)
	return data.get("bot", {}).get("id")


def get_cycle_bets(bot_id: str) -> dict:
	return http_request("GET", f"{BACKEND_URL}/admin/bots/{bot_id}/cycle-bets")


def run_once(run_id: int) -> bool:
	name = f"DupCheckBotLocal#{int(time.time())}_{run_id}"
	bot_id = create_bot(name)
	assert bot_id, "Не удалось получить id созданного бота"

	data = get_cycle_bets(bot_id)
	bets = data.get("bets", [])
	sums = data.get("sums", {})

	# Количество ставок и уникальные index (1..16 в mock)
	assert isinstance(bets, list) and len(bets) == CYCLE_GAMES, f"Ожидалось {CYCLE_GAMES} ставок, получено {len(bets)}"
	idxs = [b.get("index") for b in bets if b.get("index") is not None]
	assert len(set(idxs)) == len(idxs) == CYCLE_GAMES, "Найдены дубликаты индексов"
	assert min(idxs) == 1 and max(idxs) == CYCLE_GAMES, "Индексы должны покрывать 1..N"

	# Суммы
	wins_sum = int(sums.get("wins_sum", 0))
	losses_sum = int(sums.get("losses_sum", 0))
	draws_sum = int(sums.get("draws_sum", 0))
	total_sum = int(sums.get("total_sum", 0))
	active_pool = int(sums.get("active_pool", 0))
	profit = int(sums.get("profit", 0))
	roi_active = float(sums.get("roi_active", 0.0))

	assert total_sum == wins_sum + losses_sum + draws_sum, "total_sum != W+L+D"
	assert total_sum == EXPECTED_TOTAL, f"Ожидалась база {EXPECTED_TOTAL}, а не {total_sum}"
	assert (wins_sum, losses_sum, draws_sum) == (EXPECTED_W, EXPECTED_L, EXPECTED_D), "Суммы категорий не совпали с базой 800"
	assert active_pool == EXPECTED_ACTIVE_POOL, "active_pool != 576"
	assert profit == EXPECTED_PROFIT, "profit != 58"
	assert abs(roi_active - EXPECTED_ROI) <= 0.2, f"ROI {roi_active}% вне допуска"

	print(f"✅ Прогон {run_id}: W={wins_sum}, L={losses_sum}, D={draws_sum}, Σ={total_sum}, Активный пул={active_pool}, Прибыль={profit}, ROI={roi_active:.2f}%")
	return True


def main():
	print("🚀 Локальный HTTP‑тест на конфликты/дубликаты (mock): база 800, ROI 10%, 16 игр")
	ok = True
	for i in range(1, 4):
		try:
			res = run_once(i)
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
		print("\n⚠️ Обнаружены проблемы. Проверьте логи mock‑сервера.")


if __name__ == "__main__":
	main()