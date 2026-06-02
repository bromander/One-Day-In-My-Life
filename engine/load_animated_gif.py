from pathlib import Path
from arcade import (
Texture,
TextureAnimationSprite,
TextureKeyframe,
TextureAnimation

)
from PIL import Image

def load_animated_gif(resource_name: str | Path, size_modif: float = 1.0) -> tuple[TextureAnimationSprite, (int, int)]:

    file_name = Path(resource_name)
    image_object = Image.open(file_name)

    if not getattr(image_object, "is_animated", False) or not (
        n_frames := getattr(image_object, "n_frames", 0)
    ):
        raise TypeError(f"The file {resource_name} is not an animated gif.")

    sprite = TextureAnimationSprite()
    keyframes = []
    for frame in range(n_frames):
        image_object.seek(frame)
        frame_duration = image_object.info["duration"]
        image = image_object.convert("RGBA")
        size_resiz = (int(image.size[0] * size_modif), int(image.size[1] * size_modif))
        image = image.resize(size_resiz, Image.Resampling.LANCZOS, reducing_gap=3.0)

        texture = Texture(image)
        texture.file_path = file_name
        # sprite.textures.append(texture)
        keyframes.append(TextureKeyframe(texture, frame_duration))
    original_size = tuple(image.size)

    animation = TextureAnimation(keyframes=keyframes)
    sprite.animation = animation
    return sprite, original_size