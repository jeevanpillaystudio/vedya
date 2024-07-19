"use client";

import { createContext, type ReactNode, useContext, useState } from "react";
import { DEFAULT_CONSTRUCTION_PLANE, DEFAULT_RESOLUTION } from "./_defaults";
import { type ConstructionPlane } from "../_lib/_enums";

export interface EngineSettings {
  resolution: number;
  constructionPlane: ConstructionPlane;
  setResolution: (resolution: number) => void;
  setConstructionPlane: (plane: ConstructionPlane) => void;
}

export const EngineContext = createContext<EngineSettings | undefined>(undefined);

export const useEngine = (): EngineSettings => {
  const context = useContext(EngineContext);
  if (!context) {
    throw new Error("useEngine must be used within an EngineProvider");
  }
  return context;
};

export type EngineProviderProps = {
  children: ReactNode;
  resolution?: number;
  constructionPlane?: ConstructionPlane;
};

export const EngineProvider = ({
  resolution: r = DEFAULT_RESOLUTION,
  constructionPlane: cp = DEFAULT_CONSTRUCTION_PLANE,
  children,
}: EngineProviderProps) => {
  const [resolution, setResolution] = useState<number>(r);
  const [constructionPlane, setConstructionPlane] = useState<ConstructionPlane>(cp);

  const updateResolution = (resolution: number) => setResolution(resolution);
  const updateConstructionPlane = (plane: ConstructionPlane) => setConstructionPlane(plane);

  return (
    <EngineContext.Provider
      value={{ resolution, constructionPlane, setResolution: updateResolution, setConstructionPlane: updateConstructionPlane }}
    >
      {children}
    </EngineContext.Provider>
  );
};
