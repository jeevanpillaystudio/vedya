# from . import plot_cylinder_with_filled_circle, plot_sphere_with_filled_circle, create_cylinder_scad_model
import numpy as np
import cv2

def main() -> None:
    # Load the image
    image = cv2.imread('lib/img-to-stencil/public/roman-soldier-cc.png')

    # Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply GaussianBlur to reduce noise and improve edge detection
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

    # Detect edges using the Canny edge detection algorithm
    edges = cv2.Canny(blurred_image, threshold1=60, threshold2=150)

    # Invert the edges to create a stencil effect
    stencil = cv2.bitwise_not(edges)

    # Optional: Apply a threshold to make the stencil more distinct
    _, stencil = cv2.threshold(stencil, 127, 255, cv2.THRESH_BINARY)

    # Save or display the resulting stencil
    cv2.imwrite('lib/img-to-stencil/public/stencil_output.png', stencil)
    cv2.imshow('Stencil', stencil)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
