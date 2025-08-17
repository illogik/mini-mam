import React from 'react';

interface LoadingSpinnerProps {
  size?: number;
  color?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = React.memo(({ 
  size = 50, 
  color = 'white',
  className = ''
}) => {
  const spinnerStyle = {
    width: `${size}px`,
    height: `${size}px`,
    border: `4px solid rgba(255, 255, 255, 0.3)`,
    borderTop: `4px solid ${color}`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '20px',
    willChange: 'transform' as const,
    transform: 'translateZ(0)',
  };

  return (
    <div 
      className={`loading-spinner ${className}`}
      style={spinnerStyle}
    />
  );
});

export default LoadingSpinner; 