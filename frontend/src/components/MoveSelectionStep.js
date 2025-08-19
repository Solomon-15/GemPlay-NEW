import { formatGemValue } from '../utils/economy';

const MoveSelectionStep = ({
  targetAmount,
  totalGemValue,
  selectedMove,
  onSelectedMoveChange,
  showCountdown = false
}) => {

  const moves = [
    { id: 'rock', name: 'Rock', icon: '/Rock.svg' },
    { id: 'paper', name: 'Paper', icon: '/Paper.svg' },
    { id: 'scissors', name: 'Scissors', icon: '/Scissors.svg' }
  ];

  const handleMoveSelect = (moveId) => {
    if (onSelectedMoveChange) {
      onSelectedMoveChange(moveId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-white font-rajdhani text-xl mb-2">Choose Your Move</h3>
        <div className="text-green-400 font-rajdhani text-6xl font-bold">
          {(totalGemValue)}
        </div>
      </div>

      {/* Move Selection */}
      <div className="grid grid-cols-3 gap-4">
        {moves.map(move => (
          <button
            key={move.id}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleMoveSelect(move.id);
            }}
            className={`p-6 rounded-lg border-2 transition-all duration-300 ${
              showCountdown 
                ? 'pointer-events-none' 
                : 'hover:scale-105'
            } ${
              selectedMove === move.id
                ? 'border-accent-primary bg-accent-primary bg-opacity-20'
                : `border-border-primary ${showCountdown ? '' : 'hover:border-accent-primary'}`
            }`}
          >
            <div className="flex flex-col items-center space-y-2">
              <img src={move.icon} alt={move.name} className="w-24 h-24" />
              <span className="text-white font-rajdhani font-bold">{move.name}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Selected Move Confirmation */}
      {selectedMove && (
        <div className="text-center">
          <div className="inline-block bg-accent-primary bg-opacity-20 border border-accent-primary rounded-lg px-4 py-2">
            <span className="text-accent-primary font-rajdhani font-bold">
              Selected: {moves.find(m => m.id === selectedMove)?.name}
            </span>
          </div>
        </div>
      )}


      {/* Instructions */}
      <div className="bg-blue-900 bg-opacity-20 border border-blue-600 rounded-lg p-4">
        <div className="text-blue-400 font-rajdhani font-bold mb-2">
          ⚡ Battle Rules
        </div>
        <ul className="text-blue-300 text-sm space-y-1">
          <li>• Rock beats Scissors</li>
          <li>• Paper beats Rock</li>
          <li>• Scissors beats Paper</li>
          <li>• Winner takes all gems</li>
        </ul>
      </div>
    </div>
  );
};

export default MoveSelectionStep;