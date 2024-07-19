import { DEFAULT_CONSTRUCTION_PLANE, DEFAULT_RESOLUTION } from "./_components/_defaults";
import ThreeEngine from "./_components/three-engine";

export default function Home() {
  return (
    <main style={{ width: "100vw", height: "100vh" }}>
      <ThreeEngine resolution={DEFAULT_RESOLUTION} constructionPlane={DEFAULT_CONSTRUCTION_PLANE} name="three-engine" />
    </main>
  );
}
