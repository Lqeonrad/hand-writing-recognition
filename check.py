import os
from PIL import Image

def check_images(folder):
    for filename in os.listdir(folder):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(folder, filename)
            try:
                img = Image.open(img_path)
                img.verify()  # 验证图像是否有效
                print(f"{filename} 是有效的图像文件。")
            except Exception as e:
                print(f"{filename} 不是有效的图像文件: {e}")

check_images('data/train/class1')