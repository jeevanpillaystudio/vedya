import { DEFAULT_CONSTRUCTION_PLANE, DEFAULT_RESOLUTION } from "./_components/_defaults";
import ThreeEngine from "./_components/three-engine";
import { cn } from "./_react/css-utils";

export default function Home() {
  return (
    <main className={cn("h-screen w-screen bg-white")}>
      <ThreeEngine resolution={DEFAULT_RESOLUTION} constructionPlane={DEFAULT_CONSTRUCTION_PLANE} name="three-engine" />
    </main>
  );
}
