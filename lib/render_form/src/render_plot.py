import numpy as np
import plotly.graph_objects as go


# @NOTE
#   - [ ] R, H are coupled with cylinder coordinate system...
def render_plot(coord_points: np.array, target_points: np.array, R, H) -> None:
    fig = go.Figure()

    # points of the coordinate system
    fig.add_trace(
        go.Scatter3d(
            x=coord_points[:, 0],
            y=coord_points[:, 1],
            z=coord_points[:, 2],
            mode="markers",
            marker=dict(size=3, color="red"),
            name="Rectangle",
        )
    )

    # points of the target system
    fig.add_trace(
        go.Scatter3d(
            x=target_points[:, 0],
            y=target_points[:, 1],
            z=target_points[:, 2],
            mode="markers",
            marker=dict(size=3, color="blue"),
            name="Circle",
        )
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-R - 1, R + 1]),
            yaxis=dict(range=[-R - 1, R + 1]),
            zaxis=dict(range=[0, H]),
            aspectmode="manual",
            aspectratio=dict(
                x=1, y=1, z=1
            ),  # for sphere: r.e zaxis=dict(range=[-R - 1, R + 1])
        ),
        title="Cylinder with Filled Circle",
    )

    fig.show()
