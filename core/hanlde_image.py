from dataclasses import dataclass
from PIL import Image
from typing import Dict, List, Tuple, Literal
import io
from PIL import ImageStat
from PIL import ImageOps  # 添加此行
from PIL import ImageDraw
ImageFormat = Literal['JPEG', 'PNG', 'WEBP']
WIDTH = int
HEIGHT = int

class ColorPalette:
    @dataclass    
    class Color:
        name: str
        color_hex: str

    def __init__(self, colors: List[Dict]):
        self.colors = [self.Color(color['name'], color['color']) for color in colors]

    def get_hex_from_name(self, name: str) -> str:
        """根据颜色名称获取十六进制颜色"""
        for color in self.colors:
            if color.name == name:
                return color.color_hex
        raise ValueError(f"Color {name} not found in palette")
        
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为RGB元组"""
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def closest_color(self, avg_color: Tuple[int, int, int]) -> Color:
        """找到与平均颜色最接近的色板颜色"""
        closest = None
        min_distance = float('inf')

        for color in self.colors:
            palette_color = self.hex_to_rgb(color.color_hex)
            # 使用简化的颜色差别公式计算距离
            rmean = (avg_color[0] + palette_color[0]) / 2
            rd = avg_color[0] - palette_color[0]
            gd = avg_color[1] - palette_color[1]
            bd = avg_color[2] - palette_color[2]
            distance = (((512 + rmean) * rd * rd) // 256) + 4 * gd * gd + (((767 - rmean) * bd * bd) // 256)

            if distance < min_distance:
                min_distance = distance
                closest = color

        return closest


def create_image_from_bytes(image_stream) -> Tuple[Image.Image, ImageFormat]:
    """
    Create an image object from a byte stream and determine its format.
    
    :param image_bytes: Byte stream of the image
    :return: Tuple of (Image object, format)
    """
    try:
        img = Image.open(image_stream)
        
        # 使用ImageOps.exif_transpose处理EXIF方向
        img = ImageOps.exif_transpose(img)

        img_format = img.format  # Get the image format
        return img, img_format  # Return both image and format
    except Exception as e:
        raise ValueError("Failed to create image from bytes: " + str(e))  # Handle errors


def resize_image(image: Image.Image, target_size: Tuple[WIDTH, HEIGHT], resample_method=Image.Resampling.BICUBIC):
    """
    Resize the image to the target size with a specified resampling method.
    
    :param image: The input image
    :param target_size: Tuple of (width, height) for the target size
    :param resample_method: Resampling method to use (default: BICUBIC)
    """
    resized_img = image.resize(target_size, resample=resample_method)
    return resized_img
    

def split_image_into_tiles(image: Image.Image, tile_shape: Tuple[WIDTH, HEIGHT], color_palette: ColorPalette) -> Tuple[List[ColorPalette.Color], Image.Image, Dict[str, int]]:
    """
    Splits the image into tiles, computes the average color of each tile,
    and maps it to the closest color in the palette to reduce noise.

    :param image: The input image.
    :param tile_shape: Tuple of (width, height) representing the size of each tile.
    :param color_palette: An instance of ColorPalette.
    :return: A tuple containing the list of tile colors, the resized image, and a dictionary of color counts.
    """
    tile_width, tile_height = tile_shape
    image_width, image_height = image.size

    # Calculate the number of tiles horizontally and vertically
    num_tiles_x = image_width // tile_width
    num_tiles_y = image_height // tile_height

    tiles = []
    color_counts = {}
    averaged_image = Image.new("RGB", (num_tiles_x, num_tiles_y))

    for y in range(num_tiles_y):
        for x in range(num_tiles_x):
            # Define the region for the current tile
            left = x * tile_width
            upper = y * tile_height
            right = left + tile_width
            lower = upper + tile_height

            tile = image.crop((left, upper, right, lower))

            # Compute the most frequently occurring color of the tile
            colors = list(tile.getdata())  # Get all pixel colors as a list
            most_frequent_color = max(set(colors), key=colors.count)  # Find the most common color
            avg_color = most_frequent_color  # Use the most frequent color

            # Find the closest color in the palette
            closest_color = color_palette.closest_color(avg_color)
            tiles.append(closest_color)

            # Update color count
            color_name = closest_color.name
            if color_name in color_counts:
                color_counts[color_name] += 1
            else:
                color_counts[color_name] = 1

            # Assign the closest color to the averaged_image
            averaged_image.putpixel((x, y), color_palette.hex_to_rgb(closest_color.color_hex))

    # Resize the averaged image to the original size using nearest neighbor to maintain uniform blocks
    resized_image = averaged_image.resize((image_width, image_height), Image.NEAREST)

    return tiles, resized_image, color_counts


def preview_tiles(tiles: List[ColorPalette.Color], 
                  tile_shape: Tuple[WIDTH, HEIGHT],
                  tile_image_size: Tuple[WIDTH, HEIGHT],
                  color_palette: ColorPalette) -> Image.Image:
    """
    根据色块颜色列表重新构建图像。
    
    :param tiles: 色块颜色列表
    :param tile_shape: tiles 对应的图像二维排列尺寸
    :param tile_image_size: 每个色块的图像尺寸
    :return: 重建的图像
    """
    # 计算图像的宽度和高度
    img_width = tile_shape[0] * tile_image_size[0]
    img_height = tile_shape[1] * tile_image_size[1]

    # 创建一个新的图像
    new_image = Image.new("RGB", (img_width, img_height))

    for index, color in enumerate(tiles):
        # 创建一个填充了最近色板颜色的色块
        colored_tile = Image.new("RGB", tile_image_size, color_palette.hex_to_rgb(color.color_hex))

        drawer = ImageDraw.Draw(colored_tile)
        drawer.text((5, 5), color.name, fill=(255, 255, 255))

        # 计算色块的放置位置
        x_position = (index % tile_shape[0]) * tile_image_size[0]
        y_position = (index // tile_shape[0]) * tile_image_size[1]
        new_image.paste(colored_tile, (x_position, y_position))

    return new_image

