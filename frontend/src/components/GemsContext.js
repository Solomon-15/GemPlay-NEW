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

  const getGemColor = (gemType) => {
    const colorMap = {
      'Ruby': 'red',
      'Amber': 'orange', 
      'Topaz': 'yellow',
      'Emerald': 'green',
      'Aquamarine': 'cyan',
      'Sapphire': 'blue',
      'Magic': 'purple'
    };
    return colorMap[gemType] || 'gray';
  };

  const getGemTailwindColor = (gemType) => {
    const colorMap = {
      'Ruby': 'text-red-500',
      'Amber': 'text-orange-500',
      'Topaz': 'text-yellow-500', 
      'Emerald': 'text-green-500',
      'Aquamarine': 'text-cyan-500',
      'Sapphire': 'text-blue-500',
      'Magic': 'text-purple-500'
    };
    return colorMap[gemType] || 'text-gray-500';
  };

  const getDefaultGemDefinitions = () => [
    { name: 'Ruby', value: 1, icon: '/gems/gem-red.svg', color: 'text-red-500' },
    { name: 'Amber', value: 2, icon: '/gems/gem-orange.svg', color: 'text-orange-500' },
    { name: 'Topaz', value: 5, icon: '/gems/gem-yellow.svg', color: 'text-yellow-500' },
    { name: 'Emerald', value: 10, icon: '/gems/gem-green.svg', color: 'text-green-500' },
    { name: 'Aquamarine', value: 25, icon: '/gems/gem-cyan.svg', color: 'text-cyan-500' },
    { name: 'Sapphire', value: 50, icon: '/gems/gem-blue.svg', color: 'text-blue-500' },
    { name: 'Magic', value: 100, icon: '/gems/gem-purple.svg', color: 'text-purple-500' }
  ];

  const getGemByType = (gemType) => {
    return gemsDefinitions.find(gem => gem.name === gemType) || 
           getDefaultGemDefinitions().find(gem => gem.name === gemType);
  };

  const getGemValue = (gemType) => {
    const gem = getGemByType(gemType);
    return gem ? gem.value : 0;
  };

  const getGemIcon = (gemType) => {
    const gem = getGemByType(gemType);
    return gem ? gem.icon : '/gems/gem-gray.svg';
  };

  const getSortedGems = (orderBy = 'value', order = 'asc') => {
    const sortedGems = [...gemsDefinitions].sort((a, b) => {
      if (order === 'asc') {
        return a[orderBy] - b[orderBy];
      } else {
        return b[orderBy] - a[orderBy];
      }
    });
    return sortedGems;
  };

  const refreshGemsData = () => {
    fetchGemsData();
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