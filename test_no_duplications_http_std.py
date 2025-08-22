#!/usr/bin/env python3
import json
import time
import urllib.request
import urllib.error

BACKEND_URL = "https://fraction-calc.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@gemplay.com"
ADMIN_PASSWORD = "Admin123!"

# Параметры теста
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


def login() -> str:
	data = http_request(
		"POST",
		f"{BACKEND_URL}/auth/login",
		payload={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
	)
	return data["access_token"]


def create_bot(token: str, name: str) -> str:
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
		"pause_between_cycles": 5,
	}
	data = http_request("POST", f"{BACKEND_URL}/admin/bots/create-regular", headers, payload)
	return data.get("created_bot_id") or data.get("bot_id") or data.get("id")


def recalc_bets(token: str, bot_id: str) -> None:
	headers = {"Authorization": f"Bearer {token}"}
	http_request("POST", f"{BACKEND_URL}/admin/bots/{bot_id}/recalculate-bets", headers)


def get_cycle_bets(token: str, bot_id: str) -> dict:
	headers = {"Authorization": f"Bearer {token}"}
	return http_request("GET", f"{BACKEND_URL}/admin/bots/{bot_id}/cycle-bets", headers)


def delete_bot(token: str, bot_id: str) -> None:
	headers = {"Authorization": f"Bearer {token}"}
	try:
		http_request("DELETE", f"{BACKEND_URL}/admin/bots/{bot_id}/delete", headers, {"reason": "test cleanup"})
	except RuntimeError as e:
		# допускаем 404 как норму при повторном удалении
		if "HTTP 404" not in str(e):
			raise


def run_once(run_id: int) -> bool:
	token = login()
	name = f"DupCheckBot#{int(time.time())}_{run_id}"
	bot_id = create_bot(token, name)
	assert bot_id, "Не удалось получить id созданного бота"

	recalc_bets(token, bot_id)
	time.sleep(0.5)
	data = get_cycle_bets(token, bot_id)
	bets = data.get("bets", [])
	sums = data.get("sums", {})

	# Количество ставок и уникальные id
	assert isinstance(bets, list) and len(bets) == CYCLE_GAMES, f"Ожидалось {CYCLE_GAMES} ставок, получено {len(bets)}"
	ids = [b.get("id") for b in bets if b.get("id")]
	assert len(set(ids)) == len(ids) == CYCLE_GAMES, "Найдены дубликаты ставок (id)"
	idxs = [b.get("index") for b in bets if b.get("index") is not None]
	if idxs:
		assert len(set(idxs)) == len(idxs), "Найдены дубликаты индексов"

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
	assert active_pool == wins_sum + losses_sum, "active_pool != W+L"
	assert profit == wins_sum - losses_sum, "profit != W−L"
	assert abs(roi_active - EXPECTED_ROI) <= 0.2, f"ROI {roi_active}% вне допуска"

	print(f"✅ Прогон {run_id}: W={wins_sum}, L={losses_sum}, D={draws_sum}, Σ={total_sum}, Активный пул={active_pool}, Прибыль={profit}, ROI={roi_active:.2f}%")

	delete_bot(token, bot_id)
	return True


def main():
	print("🚀 HTTP‑тест на конфликты/дубликаты (urllib): база 800, ROI 10%, 16 игр")
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
		print("\n⚠️ Обнаружены проблемы. Проверьте логи бэкенда и эндпоинты генерации.")


if __name__ == "__main__":
	main()