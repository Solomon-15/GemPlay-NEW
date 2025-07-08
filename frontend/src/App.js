import React from "react";
import "./App.css";

const GemShowcase = () => {
  const gems = [
    { name: "Ruby", price: 1, color: "gem-ruby", file: "gem-red.svg" },
    { name: "Amber", price: 2, color: "gem-amber", file: "gem-orange.svg" },
    { name: "Topaz", price: 5, color: "gem-topaz", file: "gem-yellow.svg" },
    { name: "Emerald", price: 10, color: "gem-emerald", file: "gem-green.svg" },
    { name: "Aquamarine", price: 25, color: "gem-aquamarine", file: "gem-cyan.svg" },
    { name: "Sapphire", price: 50, color: "gem-sapphire", file: "gem-blue.svg" },
    { name: "Magic", price: 100, color: "gem-magic", file: "gem-purple.svg" }
  ];

  return (
    <div className="min-h-screen bg-gradient-primary p-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="font-russo text-4xl md:text-6xl text-accent-primary mb-4">
          GemPlay
        </h1>
        <p className="font-roboto text-xl text-text-secondary">
          PvP NFT Gem Battle Game
        </p>
      </div>

      {/* Gem Grid */}
      <div className="max-w-6xl mx-auto">
        <h2 className="font-russo text-3xl text-center mb-8 text-accent-secondary">
          Collectible Gems
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {gems.map((gem, index) => (
            <div
              key={index}
              className={`bg-surface-card border border-border-primary rounded-lg p-6 hover:bg-surface-hover transition-all duration-300 hover:shadow-gem hover:scale-105`}
            >
              {/* Gem Icon */}
              <div className="flex justify-center mb-4">
                <img
                  src={`/gems/${gem.file}`}
                  alt={gem.name}
                  className="w-20 h-20 object-contain"
                />
              </div>
              
              {/* Gem Info */}
              <div className="text-center">
                <h3 className="font-russo text-xl text-text-primary mb-2">
                  {gem.name}
                </h3>
                <div className="flex justify-center items-center space-x-4 mb-4">
                  <span className="font-roboto text-text-secondary">Price:</span>
                  <span className="font-rajdhani text-2xl font-bold text-accent-primary">
                    ${gem.price}
                  </span>
                </div>
                
                {/* Action Button */}
                <button className="w-full bg-gradient-accent hover:opacity-90 text-white font-rajdhani font-bold py-3 px-6 rounded-lg transition-all duration-300 hover:shadow-glow-primary">
                  VIEW
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center mt-16">
        <p className="font-roboto text-text-muted">
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
