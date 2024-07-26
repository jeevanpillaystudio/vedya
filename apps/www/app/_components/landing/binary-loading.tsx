import { useState, useEffect, useRef } from "react";
import { createNoise2D } from "simplex-noise";
import { cn } from "../../_react/css-utils";

const noise2D = createNoise2D();
const opacityNoise2D = createNoise2D();

interface CellData {
  value: string;
  opacity: number;
}

interface BinaryLoadingProps {
  duration: number;
  debug: boolean;
  isPlaying: boolean;
  restart: number;
}

const BinaryLoading: React.FC<BinaryLoadingProps> = ({ duration, debug, isPlaying, restart }) => {
  const [binaryString, setBinaryString] = useState("");
  const [debugInfo, setDebugInfo] = useState({ progress: 0, currentSize: 0 });
  const gridRef = useRef<(CellData | null)[][]>([]);
  const startTimeRef = useRef(Date.now());
  const frameCountRef = useRef(0);
  const animationRef = useRef<number | null>(null);

  const updateString = () => {
    const elapsedTime = Date.now() - startTimeRef.current;
    const progress = Math.min(elapsedTime / duration, 1);
    const initialSize = 4;
    const maxSize = Math.floor(Math.sqrt((window.innerWidth * window.innerHeight) / 20));
    const currentSize = Math.floor(initialSize + (maxSize - initialSize) * Math.pow(progress, 3));
    const noiseScale = 0.2;
    const opacityNoiseScale = 0.1;
    const opacitySpeed = 2;

    // Expand the grid if necessary
    while (gridRef.current.length < currentSize) {
      gridRef.current.push(new Array(currentSize).fill(null));
    }
    for (let i = 0; i < gridRef.current.length; i++) {
      while (gridRef.current[i]!.length < currentSize) {
        gridRef.current[i]!.push(null);
      }
    }

    const newString = Array(currentSize)
      .fill(0)
      .map((_, row) =>
        Array(currentSize)
          .fill(0)
          .map((_, col) => {
            if (gridRef.current[row]![col] === null) {
              let newValue: string;
              if (row === 0 || row === currentSize - 1 || col === 0 || col === currentSize - 1) {
                newValue = Math.random() > 0.5 ? "1" : "0";
              } else {
                const noiseValue = noise2D(col * noiseScale, row * noiseScale);
                newValue = noiseValue > 0.2 ? (Math.random() > 0.5 ? "1" : "0") : " ";
              }
              gridRef.current[row]![col] = { value: newValue, opacity: 1 };
            }

            // Update opacity for all cells
            const opacityNoiseValue = opacityNoise2D(
              col * opacityNoiseScale + progress * opacitySpeed,
              row * opacityNoiseScale + progress * opacitySpeed,
            );
            gridRef.current[row]![col]!.opacity = 0.3 + opacityNoiseValue * 0.7;

            return gridRef.current[row]![col];
          })
          .map((cell) => (cell ? `<span style="opacity: ${cell.opacity}">${cell.value}</span>` : " "))
          .join(" "),
      )
      .join("\n");

    setBinaryString(newString);
    setDebugInfo({ progress, currentSize });
    frameCountRef.current++;

    if (progress < 1 && isPlaying && !debug) {
      animationRef.current = requestAnimationFrame(updateString);
    }
  };

  useEffect(() => {
    // Reset everything when restart changes
    gridRef.current = [];
    startTimeRef.current = Date.now();
    frameCountRef.current = 0;
    setDebugInfo({ progress: 0, currentSize: 0 });

    if (isPlaying && !debug) {
      animationRef.current = requestAnimationFrame(updateString);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, debug, duration, restart]);

  const handleNextFrame = () => {
    updateString();
  };

  return (
    <div className={cn("fixed inset-0 flex flex-col items-center justify-center overflow-hidden bg-black text-white")}>
      <div className={cn("max-h-full max-w-full overflow-hidden break-all font-mono text-sm md:text-base lg:text-lg xl:text-xl")}>
        <pre className={cn("leading-none tracking-normal")} dangerouslySetInnerHTML={{ __html: binaryString }}></pre>
      </div>
      {debug && (
        <div className="mt-4 text-white">
          <button className="rounded bg-blue-500 px-4 py-2 font-bold text-white hover:bg-blue-700" onClick={handleNextFrame}>
            Next Frame
          </button>
          <div className="mt-2">
            Progress: {debugInfo.progress.toFixed(2)}
            <br />
            Current Size: {debugInfo.currentSize}
            <br />
            Frame Count: {frameCountRef.current}
          </div>
        </div>
      )}
    </div>
  );
};

export default BinaryLoading;
