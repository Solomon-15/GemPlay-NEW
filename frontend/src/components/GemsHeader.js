import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GemsHeader = ({ user }) => {
  const [gemDefinitions, setGemDefinitions] = useState([]);
  const [userGems, setUserGems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGemsData();
  }, []);

  const fetchGemsData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch gem definitions
      const definitionsResponse = await axios.get(`${API}/gems/definitions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Fetch user's gem inventory
      const inventoryResponse = await axios.get(`${API}/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setGemDefinitions(definitionsResponse.data);
      setUserGems(inventoryResponse.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching gems data:', error);
      setLoading(false);
    }
  };

  const getGemData = (gemType) => {
    const definition = gemDefinitions.find(def => def.type === gemType);
    const userGem = userGems.find(gem => gem.type === gemType);
    
    if (!definition) return null;
    
    const totalQuantity = userGem ? userGem.quantity : 0;
    const frozenQuantity = userGem ? userGem.frozen_quantity : 0;
    const availableQuantity = totalQuantity - frozenQuantity;
    
    const availableValue = availableQuantity * definition.price;
    const totalValue = totalQuantity * definition.price;
    
    return {
      ...definition,
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
    
    const { name, icon, color, availableValue, totalValue, hasGems } = gemData;
    
    return (
      <div 
        className={`bg-surface-card rounded-lg p-3 text-center transition-all duration-300 ${
          hasGems ? 'hover:scale-105' : ''
        }`}
        style={{
          border: `1px solid ${color}${hasGems ? '60' : '20'}`,
          boxShadow: hasGems ? `0 0 8px ${color}20` : 'none'
        }}
      >
        {/* Gem Icon */}
        <div className="flex justify-center mb-2">
          <div className="w-8 h-8 flex items-center justify-center relative">
            <img
              src={`/gems/${icon}`}
              alt={name}
              className={`w-7 h-7 object-contain transition-all duration-300 ${
                hasGems ? 'brightness-100' : 'brightness-50 opacity-40'
              }`}
              style={{
                filter: hasGems ? `drop-shadow(0 0 4px ${color}40)` : 'grayscale(100%)'
              }}
            />
          </div>
        </div>
        
        {/* Gem Name */}
        <h3 className={`font-rajdhani text-xs mb-1 transition-colors duration-300 ${
          hasGems ? 'text-white' : 'text-gray-500'
        }`}>
          {name}
        </h3>
        
        {/* Gem Values */}
        <div className="space-y-1">
          <div className={`font-rajdhani text-sm font-bold transition-colors duration-300 ${
            hasGems ? 'text-green-400' : 'text-gray-600'
          }`}>
            ${availableValue.toFixed(2)}
          </div>
          <div className={`font-rajdhani text-xs transition-colors duration-300 ${
            hasGems ? 'text-text-secondary' : 'text-gray-700'
          }`}>
            / ${totalValue.toFixed(2)}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto mb-6">
        <div className="grid grid-cols-4 sm:grid-cols-7 gap-3">
          {[...Array(7)].map((_, index) => (
            <div key={index} className="bg-surface-card border border-accent-primary border-opacity-20 rounded-lg p-3 animate-pulse">
              <div className="w-8 h-8 bg-gray-600 rounded mx-auto mb-2"></div>
              <div className="w-12 h-3 bg-gray-600 rounded mx-auto mb-1"></div>
              <div className="w-10 h-3 bg-gray-600 rounded mx-auto mb-1"></div>
              <div className="w-8 h-3 bg-gray-600 rounded mx-auto"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto mb-6">
      {/* Desktop: 7 columns, Mobile: 4 columns (2 rows) */}
      <div className="grid grid-cols-4 sm:grid-cols-7 gap-3">
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