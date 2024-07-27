export interface CanvasSize {
    width: number;
    height: number;
}

export type UpdateFunction = (deltaTime: number, elapsedTime: number) => void;
export type RenderFunction = (ctx: CanvasRenderingContext2D, size: CanvasSize, elapsedTime: number) => void;

export interface AnimationState {
    startTime: number;
    lastFrameTime: number;
    frameCount: number;
}