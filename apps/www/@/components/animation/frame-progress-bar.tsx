import React from "react";
import { useFrameManagement } from "./frame/use-frame-management";
import { Progress } from "@/components/ui/progress";

const FrameProgressBar: React.FC = () => {
  const { currentFrame, totalFrames } = useFrameManagement();
  const progress = totalFrames > 0 ? (currentFrame / (totalFrames - 1)) * 100 : 0;

  return (
    <div className="fixed left-0 top-0 z-50 w-full bg-gray-200">
      <Progress value={progress} />
    </div>
  );
};

export default FrameProgressBar;
