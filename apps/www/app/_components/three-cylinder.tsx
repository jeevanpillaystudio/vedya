import React, { useRef } from 'react';
import { transformRectangleToCylinder } from '../_lib/transform';

interface Props {
  L: number;
  H: number;
  R: number;
  cylinderResolution: number;
}

const ThreeCylinder: React.FC<Props> = ({
    L,
    H,
    R,
    cylinderResolution,
  }) => {
    const pointsRef = useRef<any>();
    const cylinderPoints = transformRectangleToCylinder(L, H, R, cylinderResolution);
    return (
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={cylinderPoints.length / 3}
            array={cylinderPoints}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial size={0.01} color="red" />
      </points>
    );
  };
  
  
  
  

export default ThreeCylinder;
