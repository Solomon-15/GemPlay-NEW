import React from 'react';

const Loader = ({ size = 64, ariaLabel = 'Loading' }) => {
  return (
    <img
      src="/gems/gem-green.svg"
      alt={ariaLabel}
      width={size}
      height={size}
      className="spin-3s"
      style={{ width: size, height: size }}
    />
  );
};

export default Loader;