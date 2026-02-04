from PIL import Image as Im, ImageDraw as Imd

im = Im.new('RGBA', (512, 512), (0, 0, 0, 0))
mask = Im.new('L', (512, 512), 0)
mask_d = Imd.Draw(mask)

for i in range(128):
    r = i+64
    mask_d.ellipse((256-r, 256-r, 256+r, 256+r), outline=255-2*i, width=2)
mask_d.ellipse((256-64, 256-64, 256+64, 256+64), fill=255)

_parameters_get_shader = None
_buffer_shader = None
_parameters_get_mask = None
_buffer_mask = None


def _get_imNmask(radius: int):
    global _parameters_get_mask, _buffer_mask
    if _parameters_get_mask == radius:
        return _buffer_mask
    _parameters_get_mask = radius
    _buffer_mask = im.resize((2*radius, 2*radius)), \
        mask.resize((2*radius, 2*radius))
    return _buffer_mask


def get_shader(width: int, height: int, lightSources: list):
    "lightSources:list[( tuple[2], radius )], return PIL.Image"
    global _parameters_get_shader, _buffer_shader
    if _parameters_get_shader == (width, height, lightSources):
        return _buffer_shader
    _parameters_get_shader = (width, height, lightSources)
    _buffer_shader = Im.new('RGBA', (width, height), (0, 0, 0, 255))
    for (position, radius) in lightSources:
        _buf_im, _buf_mk = _get_imNmask(radius)
        _buffer_shader.paste(_buf_im, (position[0]-radius, position[1]-radius,
                                       position[0]+radius, position[1]+radius), _buf_mk)
    return _buffer_shader


def shade(target: Im.Image, lightSources: list, cover_origin=True):
    "lightSources:list[( position:tuple[2], radius )], return PIL.Image"
    if not cover_origin:
        target = target.copy()
    shader = get_shader(*target.size, lightSources)
    target.paste(shader, (0, 0), shader.getchannel('A'))
    return target


def main():
    demo = Im.open("2222.jpg").convert('RGBA')
    shade(demo, [((demo.width//2, demo.height//2), 700)])
    demo.show()


if __name__ == "__main__":
    main()
