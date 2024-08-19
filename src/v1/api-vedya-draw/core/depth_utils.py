class DepthRepeat:
    INCREMENT = 0
    DECREMENT = 1


def depth_repeat_iterator(
    depth_repeat: int,
    start_layer_offset: float,
    extrude_height: float,
    stroke_weight: float,
    direction=DepthRepeat.INCREMENT,
):
    """
    Generator that yields layer offset and stroke weight for each iteration.

    Parameters:
    - depth_repeat: Number of repetitions.
    - start_layer_offset: Initial offset for the first layer.
    - extrude_height: Height to extrude for each layer.
    - stroke_weight: Initial stroke weight.
    - direction: Direction of repetition (increment or decrement).

    Yields:
    - (layer_offset, stroke_weight): Tuple containing the current layer's offset and stroke weight.
    """
    for i in range(depth_repeat):
        # Calculate the layer offset
        layer_offset = start_layer_offset + extrude_height * i

        # Adjust stroke weight based on direction
        if direction == DepthRepeat.INCREMENT:
            sw = stroke_weight * (depth_repeat - i)
        elif direction == DepthRepeat.DECREMENT:
            sw = stroke_weight * (i + 1)

        yield layer_offset, sw
