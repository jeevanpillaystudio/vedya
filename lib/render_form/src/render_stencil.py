import numpy as np
import cv2


def render_2d_stencil(img_path: str) -> None:
    # Load the image
    image = cv2.imread(img_path)

    # Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply GaussianBlur to reduce noise and improve edge detection
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

    # Detect edges using the Canny edge detection algorithm
    edges = cv2.Canny(blurred_image, threshold1=100, threshold2=180)

    # Use morphological operations to improve edge connectivity
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    adaptive_thresh = cv2.adaptiveThreshold(
        gray_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=5,
        C=12,
    )
    stencil = cv2.bitwise_not(adaptive_thresh)

    # Find contours based on the edges detected
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contours on the stencil image
    cv2.drawContours(stencil, contours, -1, (255, 255, 255), 1)

    # Invert the stencil image to match the typical stencil look (white on black)
    stencil = cv2.bitwise_not(stencil)

    # Save or display the resulting stencil
    # cv2.imwrite("stencil_output.png", stencil) # @TODO dont save for now
    cv2.imshow("Stencil", stencil)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
