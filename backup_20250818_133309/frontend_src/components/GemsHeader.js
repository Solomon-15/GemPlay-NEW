import { useGems } from './GemsContext';
import { formatCurrencyWithSymbol } from '../utils/economy';

const GemsHeader = ({ user }) => {
  const { gemsData, loading } = useGems();

  const GemBlock = ({ gemType }) => {
    const gemData = gemsData.find(gem => gem.type === gemType);
    
    if (!gemData) return null;
    
    const { 
      name, 
      icon, 
      color, 
      price, 
      quantity, 
      frozen_quantity, 
      available_quantity, 
      has_gems,
      has_available 
    } = gemData;
    
    return (
      <div 
        className={`bg-surface-card rounded-lg p-3 text-center transition-all duration-300 ${
          has_gems ? 'hover:scale-105 hover:shadow-lg' : ''
        }`}
        style={{
          border: `1px solid ${color}${has_gems ? '60' : '20'}`,
          boxShadow: has_gems ? `0 0 8px ${color}20` : 'none'
        }}
      >
        {/* Gem Icon */}
        <div className="flex justify-center mb-2">
          <div className="w-12 h-12 flex items-center justify-center">
            <img
              src={icon}
              alt={name}
              className={`w-10 h-10 object-contain transition-all duration-300 ${
                has_gems ? 'brightness-100' : 'brightness-50 opacity-40'
              }`}
              style={{
                filter: has_gems ? `drop-shadow(0 0 6px ${color}60)` : 'grayscale(100%)'
              }}
            />
          </div>
        </div>
        
        {/* Gem Name */}
        <h3 className={`font-rajdhani text-sm font-bold mb-1 transition-colors duration-300 ${
          has_gems ? 'text-white' : 'text-gray-500'
        }`}>
          {name}
        </h3>
        
        {/* Gem Price */}
        <div className={`font-rajdhani text-lg font-bold mb-2 transition-colors duration-300`}
             style={{ color: has_gems ? color : '#6b7280' }}>
          {formatCurrencyWithSymbol(price)}
        </div>
        
        {/* Gem Status - SOURCE OF TRUTH: Inventory */}
        <div className="space-y-1">
          {has_gems ? (
            <>
              <div className="font-rajdhani text-xs text-green-400 font-medium">
                {available_quantity} Available
              </div>
              {frozen_quantity > 0 && (
                <div className="font-rajdhani text-xs text-orange-400 font-medium">
                  {frozen_quantity} Frozen
                </div>
              )}
            </>
          ) : (
            <div className="font-rajdhani text-xs text-gray-600">
              0 Owned
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto mb-6">
        <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {[...Array(7)].map((_, index) => (
            <div key={index} className="bg-surface-card border border-accent-primary border-opacity-20 rounded-lg p-3 animate-pulse">
              <div className="w-12 h-12 bg-gray-600 rounded-full mx-auto mb-2"></div>
              <div className="w-16 h-3 bg-gray-600 rounded mx-auto mb-2"></div>
              <div className="w-12 h-4 bg-gray-600 rounded mx-auto mb-2"></div>
              <div className="w-14 h-3 bg-gray-600 rounded mx-auto"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto mb-6">
      {/* Desktop: 7 columns, Tablet: 4 columns, Mobile: 3 columns */}
      <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <GemBlock gemType="Ruby" />
        <GemBlock gemType="Amber" />
        <GemBlock gemType="Topaz" />
        <GemBlock gemType="Emerald" />
        <GemBlock gemType="Aquamarine" />
        <GemBlock gemType="Sapphire" />
        <GemBlock gemType="Magic" />
      </div>
    </div>
  );
};

export default GemsHeader;