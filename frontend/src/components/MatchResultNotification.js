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

const parseGemsReceived = (notification) => {
  const payload = notification?.payload || {};
  if (typeof payload.gems_received === 'number') return payload.gems_received;
  const msg = notification?.message || '';
  const match = msg.match(/Received:\s*(\d+)\s*Gems/i);
  if (match) return Number(match[1]);
  if (typeof payload.amount === 'number') return payload.amount;
  return null;
};

const parseMoves = (notification) => {
  const p = notification?.payload || {};
  const playerMove = (p.player_move || p.your_move || p.opponent_move_you || p.creator_move || '').toString().toLowerCase();
  const opponentMove = (p.opponent_move || p.their_move || p.creator_move_opponent || p.opponent || '').toString().toLowerCase();
  const valid = ['rock','paper','scissors'];
  return {
    player: valid.includes(playerMove) ? playerMove : null,
    opponent: valid.includes(opponentMove) ? opponentMove : null
  };
};

const parseCommission = (notification) => {
  const p = notification?.payload || {};
  const isBot = !!p.is_bot_game;
  let amount = null;
  let percent = p.commission_percent || 3;
  let paidByYou = p.commission_paid_by_you; // boolean | undefined

  if (typeof p.commission_amount === 'number') amount = p.commission_amount;

  if (amount === null) {
    const msg = notification?.message || '';
    const m = msg.match(/commission:\s*\$([0-9]+(?:\.[0-9]{1,2})?)/i);
    if (m) {
      amount = Number(m[1]);
    }
  }

  return { isBot, amount, percent, paidByYou };
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
  const gems = parseGemsReceived(notification);
  const moves = parseMoves(notification);
  const { isBot, amount: commissionAmount, percent: commissionPercent, paidByYou } = parseCommission(notification);

  // Show commission line only when: non-bot game AND commissionAmount > 0 AND paid by current user
  const showCommission = !isBot && typeof commissionAmount === 'number' && commissionAmount > 0 && paidByYou === true;

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
        {typeof gems === 'number' && (
          <span className="ml-1 text-text-secondary font-medium">
            Received: <span className={`font-extrabold ${styles.strong}`}>{gems} Gems</span>
          </span>
        )}
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
      {showCommission &amp;&amp; (
        <div className="mt-1 text-xs text-text-secondary font-rajdhani">({commissionPercent}% commission: ${commissionAmount.toFixed(2)})</div>
      )}

      {/* 5 строка — дата и время */}
      <div className="mt-1 text-[11px] sm:text-xs text-gray-500 font-roboto">{dateStr}</div>
    </div>
  );
};

export default MatchResultNotification;