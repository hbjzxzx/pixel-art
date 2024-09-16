import streamlit as st
import requests
import io
from core.palette import mardPalette
from core.hanlde_image import create_image_from_bytes, resize_image, split_image_into_tiles, preview_tiles

# Streamlit 页面标题
st.title("Image Tile Generator")

# 上传图像
image_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"])

# 输入目标大小和瓦片大小
target_size_width = st.number_input("Target Size Width", min_value=1, value=100)
target_size_height = st.number_input("Target Size Height", min_value=1, value=100)
tile_size_width = st.number_input("Tile Size Width", min_value=1, value=50)
tile_size_height = st.number_input("Tile Size Height", min_value=1, value=50)

# 选择调色板
palette = st.selectbox("Select Palette", options=["Palette 1", "Palette 2"])  # 示例调色板

# 提交按钮
if st.button("Generate Tiles"):
    if image_file is not None:
        try:
            # 读取图像数据
            image_data = image_file.getvalue()
            if image_data:  # Check if image_data is valid
                image, image_format = create_image_from_bytes(io.BytesIO(image_data))
                resized_image = resize_image(image, (target_size_width, target_size_height))
                
                tiles, tile_image, color_counts = split_image_into_tiles(resized_image, 
                                                                         (target_size_width // tile_size_width, target_size_height // tile_size_height), 
                                                                         mardPalette)
                preview_image = preview_tiles(tiles, 
                                              (tile_size_width, tile_size_height), 
                                              (50, 50), 
                                              mardPalette)
                preview_image.save("preview.png")

                # 显示结果
                st.image(resized_image, caption="Resized Image" )
                st.image(preview_image, caption="Preview Image")
                st.success("Tiles generated successfully!")

                # 显示颜色统计信息
                st.subheader("Color Counts")
                sorted_color_counts = sorted(color_counts.items(), key=lambda item: item[1], reverse=True)
                
                # 使用表格展示颜色统计信息
                color_table = "| Color Example | Color | Count |\n|---------------|-------|-------|\n"
                for color, count in sorted_color_counts:
                    color_table += f"| <div style='width: 20px; height: 20px; background-color: #{mardPalette.get_hex_from_name(color)};'></div> | {color} | {count} |\n"
                
                st.markdown(color_table, unsafe_allow_html=True)

            else:
                st.error("Invalid image data.")
        except ValueError as e:
            st.error(f"Failed to create image from bytes: {e}")
    else:
        st.error("Please upload an image.")