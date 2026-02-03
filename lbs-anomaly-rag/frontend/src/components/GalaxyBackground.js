import React from 'react';

const GalaxyBackground = () => {
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        background: 'linear-gradient(180deg, #0a0a19 0%, #1a0a2e 50%, #0a0a19 100%)',
        backgroundImage: `
          radial-gradient(circle, rgba(124, 58, 237, 0.5) 2px, transparent 2px),
          radial-gradient(circle, rgba(192, 132, 252, 0.3) 1.5px, transparent 1.5px)
        `,
        backgroundSize: '60px 60px, 40px 40px',
        backgroundPosition: '0 0, 30px 30px',
        animation: 'dotGridMove 20s linear infinite',
      }}
    >
      <style>
        {`
          @keyframes dotGridMove {
            0% {
              background-position: 0 0, 30px 30px;
            }
            100% {
              background-position: 60px 60px, 90px 90px;
            }
          }
        `}
      </style>
    </div>
  );
};

export default GalaxyBackground;
