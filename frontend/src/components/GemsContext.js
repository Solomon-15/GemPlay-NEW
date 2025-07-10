import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GemsContext = createContext();

export const useGems = () => {
  const context = useContext(GemsContext);
  if (!context) {
    throw new Error('useGems must be used within a GemsProvider');
  }
  return context;
};

export const GemsProvider = ({ children }) => {
  const [gemsData, setGemsData] = useState([]);
  const [gemsDefinitions, setGemsDefinitions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGemsData();
  }, []);

  const getDefaultGemDefinitions = () => [
    { type: 'Ruby', name: 'Ruby', price: 1, icon: '/gems/gem-red.svg', color: '#ef4444', quantity: 0, frozen_quantity: 0 },
    { type: 'Amber', name: 'Amber', price: 2, icon: '/gems/gem-orange.svg', color: '#f97316', quantity: 0, frozen_quantity: 0 },
    { type: 'Topaz', name: 'Topaz', price: 5, icon: '/gems/gem-yellow.svg', color: '#eab308', quantity: 0, frozen_quantity: 0 },
    { type: 'Emerald', name: 'Emerald', price: 10, icon: '/gems/gem-green.svg', color: '#22c55e', quantity: 0, frozen_quantity: 0 },
    { type: 'Aquamarine', name: 'Aquamarine', price: 25, icon: '/gems/gem-cyan.svg', color: '#06b6d4', quantity: 0, frozen_quantity: 0 },
    { type: 'Sapphire', name: 'Sapphire', price: 50, icon: '/gems/gem-blue.svg', color: '#3b82f6', quantity: 0, frozen_quantity: 0 },
    { type: 'Magic', name: 'Magic', price: 100, icon: '/gems/gem-purple.svg', color: '#a855f7', quantity: 0, frozen_quantity: 0 }
  ];

  const fetchGemsData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      if (!token) {
        setLoading(false);
        return;
      }

      // Fetch gem definitions (all gem types)
      const definitionsResponse = await axios.get(`${API}/gems/definitions`);
      const definitions = definitionsResponse.data || [];
      
      // Fetch user's gem inventory
      const inventoryResponse = await axios.get(`${API}/gems/inventory`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const userGems = inventoryResponse.data || [];
      
      // Create a map of user gems for easy lookup
      const userGemMap = {};
      userGems.forEach(gem => {
        userGemMap[gem.type] = {
          quantity: gem.quantity || 0,
          frozen_quantity: gem.frozen_quantity || 0
        };
      });
      
      // Combine definitions with user inventory data
      const combinedGems = definitions.map(def => ({
        type: def.type,
        name: def.name,
        price: def.price,
        color: def.color,
        icon: def.icon,
        rarity: def.rarity,
        quantity: userGemMap[def.type]?.quantity || 0,
        frozen_quantity: userGemMap[def.type]?.frozen_quantity || 0
      }));
      
      setGemsDefinitions(combinedGems);
      setGemsData(combinedGems);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching gems data:', error);
      // Fallback to default gem definitions if API fails
      setGemsDefinitions(getDefaultGemDefinitions());
      setLoading(false);
    }
  };

  const refreshGemsData = () => {
    fetchGemsData();
  };

  const getGemByType = (gemType) => {
    return gemsDefinitions.find(gem => gem.type === gemType || gem.name === gemType) || 
           getDefaultGemDefinitions().find(gem => gem.type === gemType || gem.name === gemType);
  };

  const getGemValue = (gemType) => {
    const gem = getGemByType(gemType);
    return gem ? gem.price : 0;
  };

  const getGemIcon = (gemType) => {
    const gem = getGemByType(gemType);
    return gem ? gem.icon : '/gems/gem-gray.svg';
  };

  const getSortedGems = (orderBy = 'price', order = 'asc') => {
    const sortedGems = [...gemsDefinitions].sort((a, b) => {
      if (order === 'asc') {
        return a[orderBy] - b[orderBy];
      } else {
        return b[orderBy] - a[orderBy];
      }
    });
    return sortedGems;
  };

  return (
    <GemsContext.Provider value={{
      gemsData,
      gemsDefinitions,
      loading,
      getGemByType,
      getGemValue,
      getGemIcon,
      getSortedGems,
      refreshGemsData
    }}>
      {children}
    </GemsContext.Provider>
  );
};

export default GemsContext;