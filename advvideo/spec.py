"""Output format shared by the render and caption code."""
W, H = 480, 832               # the model's native vertical size, so nothing is upscaled
FPS = 30
DURATION = 15.0
CARD_SECONDS = 3.0            # the call-to-action ending occupies the last three seconds
K = W / 1080.0                # scale from the 1080-wide design the caption layout was drawn in
