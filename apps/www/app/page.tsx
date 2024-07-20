import { DEFAULT_CONSTRUCTION_PLANE, DEFAULT_RESOLUTION } from "./_components/_defaults";
import ThreeEngine from "./_components/three-engine";

export default function Home() {
  return (
    <main className="h-screen w-screen bg-white">
      <ThreeEngine resolution={DEFAULT_RESOLUTION} constructionPlane={DEFAULT_CONSTRUCTION_PLANE} name="three-engine" />
    </main>
  );
}
