import React from 'react';
import { useGems } from './GemsContext';
import { formatCurrencyWithSymbol } from '../utils/economy';

const GemsHeader = ({ user }) => {
  const { gemsDefinitions, loading } = useGems();

  const getGemData = (gemType) => {
    const gemData = gemsDefinitions.find(def => def.type === gemType);
    
    if (!gemData) return null;
    
    const totalQuantity = gemData.quantity || 0;
    const frozenQuantity = gemData.frozen_quantity || 0;
    const availableQuantity = totalQuantity - frozenQuantity;
    
    const availableValue = availableQuantity * gemData.price;
    const totalValue = totalQuantity * gemData.price;
    
    return {
      ...gemData,
      totalQuantity,
      frozenQuantity,
      availableQuantity,
      availableValue,
      totalValue,
      hasGems: totalQuantity > 0
    };
  };

  const GemBlock = ({ gemType }) => {
    const gemData = getGemData(gemType);
    
    if (!gemData) return null;
    
    const { name, icon, color, price, totalQuantity, frozenQuantity, availableQuantity, hasGems } = gemData;
    
    return (
      <div 
        className={`bg-surface-card rounded-lg p-3 text-center transition-all duration-300 ${
          hasGems ? 'hover:scale-105 hover:shadow-lg' : ''
        }`}
        style={{
          border: `1px solid ${color}${hasGems ? '60' : '20'}`,
          boxShadow: hasGems ? `0 0 8px ${color}20` : 'none'
        }}
      >
        {/* Gem Icon */}
        <div className="flex justify-center mb-2">
          <div className="w-12 h-12 flex items-center justify-center">
            <img
              src={icon}
              alt={name}
              className={`w-10 h-10 object-contain transition-all duration-300 ${
                hasGems ? 'brightness-100' : 'brightness-50 opacity-40'
              }`}
              style={{
                filter: hasGems ? `drop-shadow(0 0 6px ${color}60)` : 'grayscale(100%)'
              }}
            />
          </div>
        </div>
        
        {/* Gem Name */}
        <h3 className={`font-rajdhani text-sm font-bold mb-1 transition-colors duration-300 ${
          hasGems ? 'text-white' : 'text-gray-500'
        }`}>
          {name}
        </h3>
        
        {/* Gem Price */}
        <div className={`font-rajdhani text-lg font-bold mb-2 transition-colors duration-300`}
             style={{ color: hasGems ? color : '#6b7280' }}>
          {formatCurrencyWithSymbol(price)}
        </div>
        
        {/* Gem Status */}
        <div className="space-y-1">
          {hasGems ? (
            <>
              <div className="font-rajdhani text-xs text-green-400 font-medium">
                {availableQuantity} Available
              </div>
              {frozenQuantity > 0 && (
                <div className="font-rajdhani text-xs text-orange-400 font-medium">
                  {frozenQuantity} Frozen
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