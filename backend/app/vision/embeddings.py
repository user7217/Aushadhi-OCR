from typing import Optional

# Placeholder stub for visual similarity
# Return a percentage similarity 0-100 (float) or None if disabled/unavailable.

def image_similarity_score(rgb_image) -> Optional[float]:
    """
    Compute visual similarity of the uploaded image to a canonical reference set
    for the matched product. This is a stub and returns None to indicate the
    visual check is disabled until a model/index is configured.

    Implement later:
    - Load a vision embedding model (e.g., CLIP).
    - Compute embedding for rgb_image.
    - Compare against a reference embedding bank for the predicted product.
    - Return cosine similarity * 100 as a float.
    """
    return None
