import React from 'react';
import {Composition, AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {registerRoot} from 'remotion';

const Scene = () => {
  const frame = useCurrentFrame();
  const y = interpolate(frame, [0, 45], [60, 0], {extrapolateRight: 'clamp'});
  const opacity = interpolate(frame, [0, 20], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{backgroundColor: '#0b1020', color: 'white', alignItems: 'center', justifyContent: 'center', fontFamily: 'Arial, sans-serif'}}>
      <div style={{fontSize: 84, fontWeight: 800, transform: `translateY(${y}px)`, opacity}}>ProofPath</div>
      <div style={{fontSize: 36, marginTop: 28, opacity}}>Research media verification</div>
    </AbsoluteFill>
  );
};

const Root = () => (
  <Composition id="Main" component={Scene} durationInFrames={90} fps={30} width={1920} height={1080} />
);

registerRoot(Root);
