"use client";

import React, { useMemo } from "react";
import { cn } from "@/lib/utils";
import { drawBinaryGrid } from "@/lib/draw/draw-binary-grid";
import { useAnimationSetup } from "@/components/animation/shared/use-animation-setup";

const BinaryLoading: React.FC = () => {
  const { canvasRef } = useAnimationSetup({ drawFn: drawBinaryGrid });
  const canvasStyle = useMemo(() => ({ height: "100%", width: "100%" }), []);
  return (
    <div className={cn("fixed inset-0 overflow-hidden bg-background")}>
      <canvas ref={canvasRef} style={canvasStyle} />
    </div>
  );
};

export default React.memo(BinaryLoading);
