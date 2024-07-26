"use client";

import { createContext, type ReactNode, useContext, useState } from "react";
import { type ConstructionPlane } from "./_lib/_enums";

export interface EngineCoreSettings {
  resolution: number;
  constructionPlane: ConstructionPlane;
}

export interface EngineSettings extends EngineCoreSettings {
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
} & EngineCoreSettings;

export const EngineProvider = ({ resolution: r, constructionPlane: cp, children }: EngineProviderProps) => {
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
