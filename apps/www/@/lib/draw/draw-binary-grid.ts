import { CanvasSize } from "@/lib/hooks/use-canvas-animation";
import { createNoise2D } from "simplex-noise";

const noise2D = createNoise2D();
const opacityNoise2D = createNoise2D();

export const drawBinaryGrid = (
  ctx: CanvasRenderingContext2D,
  size: CanvasSize,
  progress: number,
  deltaTime: number
) => {
  const currentSize = calculateCurrentSize(progress, size);
  const cellSize = Math.min(size.width / currentSize, size.height / currentSize);
  const noiseScale = 0.2;
  const opacityNoiseScale = 0.1;
  const opacitySpeed = 2;

  ctx.clearRect(0, 0, size.width, size.height);
  ctx.font = `${cellSize}px monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  for (let row = 0; row < currentSize; row++) {
    for (let col = 0; col < currentSize; col++) {
      const x = col * cellSize + cellSize / 2;
      const y = row * cellSize + cellSize / 2;

      let value: string;
      if (row === 0 || row === currentSize - 1 || col === 0 || col === currentSize - 1) {
        value = Math.random() > 0.5 ? "1" : "0";
      } else {
        const noiseValue = noise2D(col * noiseScale, row * noiseScale);
        value = noiseValue > 0.2 ? (Math.random() > 0.5 ? "1" : "0") : " ";
      }

      const opacityNoiseValue = opacityNoise2D(
        col * opacityNoiseScale + progress * opacitySpeed,
        row * opacityNoiseScale + progress * opacitySpeed,
      );
      const opacity = 0.3 + opacityNoiseValue * 0.7;

      ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
      ctx.fillText(value, x, y);
    }
  }

  return { currentSize };
};

const calculateCurrentSize = (progress: number, size: CanvasSize) => {
  const initialSize = 4;
  const maxSize = Math.floor(Math.sqrt((size.width * size.height) / 20));
  return Math.floor(initialSize + (maxSize - initialSize) * Math.pow(progress, 3));
};