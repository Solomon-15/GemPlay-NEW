import React from 'react';
import { formatDateTimeDDMMYYYYHHMMSS } from '../utils/timeUtils';

const moveIconMap = {
  rock: '/Rock.svg',
  paper: '/Paper.svg',
  scissors: '/Scissors.svg'
};

const capitalize = (s) => (typeof s === 'string' && s.length ? s.charAt(0).toUpperCase() + s.slice(1) : s);

const parseOutcome = (notification) => {
  const payload = notification?.payload || {};
  if (payload.outcome) {
    const o = String(payload.outcome).toLowerCase();
    if (o.includes('win')) return 'win';
    if (o.includes('lose')) return 'lose';
    if (o.includes('draw')) return 'draw';
  }
  const msg = (notification?.message || '').toLowerCase();
  if (msg.includes('you won')) return 'win';
  if (msg.includes('you lost') || msg.includes('you lose')) return 'lose';
  if (msg.includes('draw')) return 'draw';
  return 'win';
};

const parseOpponent = (notification) => {
  const payload = notification?.payload || {};
  if (payload.opponent_name) return payload.opponent_name;
  const msg = notification?.message || '';
  if (msg.toLowerCase().includes('bot')) return 'Bot';
  return 'Opponent';
};


const parseMoves = (notification) => {
  const p = notification?.payload || {};
  const playerMove = (p.player_move || '').toString().toLowerCase();
  const opponentMove = (p.opponent_move || '').toString().toLowerCase();
  const valid = ['rock','paper','scissors'];
  return {
    player: valid.includes(playerMove) ? playerMove : null,
    opponent: valid.includes(opponentMove) ? opponentMove : null
  };
};

const parseBets = (notification) => {
  const p = notification?.payload || {};
  const player = typeof p.player_bet_gems === 'number' ? p.player_bet_gems : null;
  const opponent = typeof p.opponent_bet_gems === 'number' ? p.opponent_bet_gems : null;
  return { player, opponent };
};

const parseCommission = (notification) => {
  const p = notification?.payload || {};
  const isBotGame = !!p.is_bot_game;
  const isHumanBot = !!p.is_human_bot;
  const percent = typeof p.commission_percent === 'number' ? p.commission_percent : 3;
  // Базовая сумма для расчёта комиссии: USD если есть, иначе считаем 1:1 от Gems
  const baseUsd = typeof p.player_bet_usd === 'number' ? p.player_bet_usd : (typeof p.player_bet_gems === 'number' ? p.player_bet_gems : 0);
  const commissionAmountUsd = typeof p.commission_amount_usd === 'number' ? p.commission_amount_usd : (baseUsd * percent / 100);
  return { isBotGame, isHumanBot, percent, commissionAmountUsd };
};

const outcomeStyles = (outcome) => {
  switch (outcome) {
    case 'win':
      return { text: 'text-green-400', strong: 'text-green-400', badge: 'bg-green-600/20 text-green-300' };
    case 'lose':
      return { text: 'text-red-400', strong: 'text-red-400', badge: 'bg-red-600/20 text-red-300' };
    case 'draw':
      return { text: 'text-yellow-400', strong: 'text-yellow-400', badge: 'bg-yellow-600/20 text-yellow-300' };
    default:
      return { text: 'text-text-secondary', strong: 'text-accent-primary', badge: 'bg-surface-sidebar text-text-secondary' };
  }
};

const MoveIcon = ({ move }) => {
  if (!move) return null;
  const src = moveIconMap[move];
  if (!src) return null;
  return <img src={src} alt={capitalize(move)} className="w-5 h-5 sm:w-6 sm:h-6" />;
};

const MatchResultNotification = ({ notification, user }) => {
  const outcome = parseOutcome(notification);
  const styles = outcomeStyles(outcome);
  const opponent = parseOpponent(notification);
  const moves = parseMoves(notification);
  const bets = parseBets(notification);
  const { isBotGame, isHumanBot, percent: commissionPercent, commissionAmountUsd } = parseCommission(notification);

  // Показ комиссии: нет для обычных ботов; есть для игроков и Human‑ботов только при победе
  const showCommission = (outcome === 'win') && (!isBotGame || (isBotGame && isHumanBot)) && commissionAmountUsd > 0;

  const dateStr = formatDateTimeDDMMYYYYHHMMSS(notification.created_at, user?.timezone_offset);

  return (
    <div className="p-3">
      {/* 1 строка — Match Result */}
      <div className="text-white font-rajdhani font-bold text-sm sm:text-base">Match Result</div>

      {/* 2 строка — Outcome + Received */}
      <div className={`mt-1 text-xs sm:text-sm font-rajdhani font-bold ${styles.text}`}>
        {outcome === 'win' && `You won against ${opponent}!`}
        {outcome === 'lose' && `You lost against ${opponent}.`}
        {outcome === 'draw' && `Draw against ${opponent}.`}
        {(() => {
          const p = bets.player;
          const o = bets.opponent;
          if (outcome === 'win' && typeof p === 'number' && typeof o === 'number') {
            return (
              <span className="ml-1 text-text-secondary font-medium">
                Received: <span className={`font-extrabold ${styles.strong}`}>{p}/{o} Gems</span>
              </span>
            );
          }
          if (outcome === 'lose' || outcome === 'draw') {
            // Fallbacks for legacy payloads
            const legacy = notification?.payload || {};
            const value = typeof p === 'number'
              ? p
              : (typeof legacy.amount_lost === 'number' ? legacy.amount_lost
                : (typeof legacy.amount === 'number' ? legacy.amount : null));
            if (typeof value === 'number') {
              return (
                <span className="ml-1 text-text-secondary font-medium">
                  <span className={`font-extrabold ${styles.strong}`}>{value} Gems</span>
                </span>
              );
            }
          }
          return null;
        })()}
      </div>

      {/* 3 строка — Icons: player vs opponent */}
      {(moves.player || moves.opponent) && (
        <div className="mt-2 flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <MoveIcon move={moves.player} />
          </div>
          <span className="text-text-secondary text-xs font-rajdhani">vs</span>
          <div className="flex items-center space-x-1">
            <MoveIcon move={moves.opponent} />
          </div>
        </div>
      )}

      {/* 4 строка — Commission */}
      {showCommission && (
        <div className="mt-1 text-xs text-text-secondary font-rajdhani">({commissionPercent}% commission: ${commissionAmountUsd.toFixed(2)})</div>
      )}

      {/* 5 строка — дата и время */}
      <div className="mt-1 text-[11px] sm:text-xs text-gray-500 font-roboto">{dateStr}</div>
    </div>
  );
};

export default MatchResultNotification;