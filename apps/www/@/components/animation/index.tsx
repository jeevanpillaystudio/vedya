import FrameProgressBar from "./frame-progress-bar";
import FrameControlPanel from "./frame-control-panel";

const AnimationControlPanel: React.FC = () => {
  return (
    <>
      <FrameProgressBar />
      <FrameControlPanel />
    </>
  );
};

export default AnimationControlPanel;
