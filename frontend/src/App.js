import React from "react";
import "./App.css";

const GemShowcase = () => {
  const gems = [
    { 
      name: "Ruby", 
      price: 1, 
      borderColor: "#ff4444", 
      buttonColor: "#ff4444",
      bgColor: "#2a1d1d",
      glowColor: "#ff444440",
      file: "gem-red.svg" 
    },
    { 
      name: "Amber", 
      price: 2, 
      borderColor: "#ff8800", 
      buttonColor: "#ff8800",
      bgColor: "#2a2318",
      glowColor: "#ff880040",
      file: "gem-orange.svg" 
    },
    { 
      name: "Topaz", 
      price: 5, 
      borderColor: "#ffdd00", 
      buttonColor: "#ffdd00",
      bgColor: "#2a2a18",
      glowColor: "#ffdd0040",
      file: "gem-yellow.svg" 
    },
    { 
      name: "Emerald", 
      price: 10, 
      borderColor: "#00dd88", 
      buttonColor: "#00dd88",
      bgColor: "#182a20",
      glowColor: "#00dd8840",
      file: "gem-green.svg" 
    },
    { 
      name: "Aquamarine", 
      price: 25, 
      borderColor: "#00aaff", 
      buttonColor: "#00aaff",
      bgColor: "#18252a",
      glowColor: "#00aaff40",
      file: "gem-cyan.svg" 
    },
    { 
      name: "Sapphire", 
      price: 50, 
      borderColor: "#4466ff", 
      buttonColor: "#4466ff",
      bgColor: "#1d1f2a",
      glowColor: "#4466ff40",
      file: "gem-blue.svg" 
    },
    { 
      name: "Magic", 
      price: 100, 
      borderColor: "#aa44ff", 
      buttonColor: "#aa44ff",
      bgColor: "#251d2a",
      glowColor: "#aa44ff40",
      file: "gem-purple.svg" 
    }
  ];

  return (
    <div className="min-h-screen" style={{ 
      background: 'linear-gradient(135deg, #0a0a0f 0%, #151520 50%, #1a1a2e 100%)' 
    }}>
      {/* Header */}
      <div className="text-center py-12">
        <h1 className="font-russo text-5xl md:text-7xl text-white mb-4">
          GemPlay
        </h1>
        <p className="font-roboto text-xl text-gray-400">
          PvP NFT Gem Battle Game
        </p>
      </div>

      {/* Gem Grid */}
      <div className="max-w-7xl mx-auto px-8">
        <h2 className="font-russo text-4xl text-center mb-12 text-white">
          Collectible Gems
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {gems.map((gem, index) => (
            <div
              key={index}
              className="rounded-xl p-8 transition-all duration-300 hover:scale-105 hover:shadow-2xl group cursor-pointer"
              style={{
                backgroundColor: gem.bgColor,
                border: `1px solid ${gem.borderColor}`,
                boxShadow: `0 0 20px ${gem.borderColor}40`
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.border = `2px solid #23d364`;
                e.currentTarget.style.boxShadow = `0 0 30px #23d36440, 0 0 20px ${gem.borderColor}60`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.border = `1px solid ${gem.borderColor}`;
                e.currentTarget.style.boxShadow = `0 0 20px ${gem.borderColor}40`;
              }}
            >
              {/* Gem Icon */}
              <div className="flex justify-center mb-6">
                <div 
                  className="w-32 h-32 rounded-full flex items-center justify-center relative transition-all duration-300 group-hover:scale-110"
                  style={{
                    background: `radial-gradient(circle at 30% 30%, ${gem.borderColor}80, ${gem.borderColor}40, ${gem.borderColor}20)`,
                    boxShadow: `0 0 30px ${gem.glowColor}, inset 0 0 15px ${gem.glowColor}`
                  }}
                >
                  {/* Background glow */}
                  <div 
                    className="absolute inset-0 rounded-full animate-pulse transition-all duration-300 group-hover:scale-125"
                    style={{
                      background: `radial-gradient(circle, ${gem.glowColor}, transparent 70%)`,
                      filter: 'blur(8px)',
                      transform: 'scale(1.2)'
                    }}
                  ></div>
                  
                  <img
                    src={`/gems/${gem.file}`}
                    alt={gem.name}
                    className="w-28 h-28 object-contain drop-shadow-lg relative z-10 transition-all duration-300 group-hover:scale-110 group-hover:brightness-125"
                    style={{
                      filter: `drop-shadow(0 0 10px ${gem.glowColor})`
                    }}
                  />
                  
                  {/* Enhanced glow on hover */}
                  <div 
                    className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{
                      background: `radial-gradient(circle, ${gem.borderColor}60, transparent 60%)`,
                      filter: 'blur(15px)',
                      transform: 'scale(1.5)'
                    }}
                  ></div>
                </div>
              </div>
              
              {/* Gem Info */}
              <div className="text-center">
                <h3 className="font-russo text-2xl text-white mb-4 transition-all duration-300 group-hover:text-green-400">
                  {gem.name}
                </h3>
                
                {/* Price */}
                <div className="mb-6">
                  <span className="font-rajdhani text-4xl font-bold text-green-400 transition-all duration-300 group-hover:text-green-300 group-hover:text-5xl">
                    ${gem.price}
                  </span>
                </div>
                
                {/* Action Button */}
                <button 
                  className="w-full py-4 px-6 rounded-lg font-rajdhani font-bold text-lg text-white transition-all duration-300 hover:opacity-80 hover:scale-105 uppercase tracking-wider group-hover:shadow-lg"
                  style={{
                    backgroundColor: 'transparent',
                    border: `1px solid ${gem.buttonColor}`,
                    color: gem.buttonColor,
                    boxShadow: `0 0 15px ${gem.borderColor}30`
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.boxShadow = `0 0 25px ${gem.borderColor}50, 0 0 10px #23d36430`;
                    e.currentTarget.style.borderColor = '#23d364';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.boxShadow = `0 0 15px ${gem.borderColor}30`;
                    e.currentTarget.style.borderColor = gem.buttonColor;
                  }}
                >
                  VIEW
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-16">
        <p className="font-roboto text-gray-500">
          Powered by cutting-edge technology
        </p>
      </div>
    </div>
  );
};

function App() {
  return <GemShowcase />;
}

export default App;