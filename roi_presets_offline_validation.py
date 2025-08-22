#!/usr/bin/env python3
# -*- coding: utf-8 -*-

N_LIST = [6, 12, 16, 20, 26, 32, 40, 50]
ROI_LIST = list(range(2, 21))
DRAWS_PCT = 28.0
TOLERANCE = 0.2  # % по ROI из-за целочисленности


def half_up_round(x: float) -> int:
	from math import floor, ceil
	frac = x - int(floor(x))
	return int(ceil(x)) if frac >= 0.5 else int(floor(x))


def validate():
	all_ok = True
	for N in N_LIST:
		# масштаб от базы 800 (для 16 игр, 1–100)
		total = round(800 * (N / 16))
		for roi in ROI_LIST:
			active_share = 100.0 - DRAWS_PCT
			r = roi / 100.0
			w_pct = active_share * (1.0 + r) / 2.0
			l_pct = active_share - w_pct
			# Перевод процентов в суммы (half-up) и сведение к total
			w_raw = total * (w_pct / 100.0)
			l_raw = total * (l_pct / 100.0)
			d_raw = total * (DRAWS_PCT / 100.0)
			w = half_up_round(w_raw)
			l = half_up_round(l_raw)
			d = half_up_round(d_raw)
			# Корректируем до точной total (из-за сумм округлений)
			diff = total - (w + l + d)
			if diff != 0:
				# добавляем к наибольшей категории по модулю
				mx = max((w, 'w'), (l, 'l'), (d, 'd'))
				if mx[1] == 'w':
					w += diff
				elif mx[1] == 'l':
					l += diff
				else:
					d += diff
			active_pool = w + l
			profit = w - l
			roi_active = (profit / active_pool * 100.0) if active_pool > 0 else 0.0
			ok = abs(roi_active - roi) <= TOLERANCE
			if not ok:
				print(f"❌ N={N}, ROI={roi}% → W={w}, L={l}, D={d}, Σ={total}, ROI_active={roi_active:.2f}%")
				all_ok = False
	if all_ok:
		print("✅ Оффлайн‑валидация пресетов ROI 2–20% прошла для всех N. База 800, округление half‑up, формулы корректны.")


if __name__ == "__main__":
	validate()