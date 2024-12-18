import os
import struct
import pickle
import threading

import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


# 处理单个gnt文件获取图像与标签
def read_from_gnt_dir(gnt_dir):
    def one_file(f):
        header_size = 10
        while True:
            header = np.fromfile(f, dtype='uint8', count=header_size)
            if not header.size:
                break
            sample_size = header[0] + (header[1] << 8) + (header[2] << 16) + (header[3] << 24)
            label = header[5] + (header[4] << 8)
            width = header[6] + (header[7] << 8)
            height = header[8] + (header[9] << 8)
            if header_size + width * height != sample_size:
                break
            image = np.fromfile(f, dtype='uint8', count=width * height).reshape((height, width))
            yield image, label

    for file_name in os.listdir(gnt_dir):
        if file_name.endswith('.gnt'):
            file_path = os.path.join(gnt_dir, file_name)
            with open(file_path, 'rb') as f:
                for image, label in one_file(f):
                    yield image, label


def gnt_to_img(gnt_dir, img_dir):
    def save_img(label, image, counter):
        label = struct.pack('>H', label).decode('gb2312')
        img = Image.fromarray(image)
        dir_name = os.path.join(img_dir, '%0.5d' % char_dict[label])
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        img.convert('RGB').save(dir_name + '/' + str(counter) + '.png')
        print("thread: {}, counter=".format(threading.current_thread().name), counter)

    counter = 0
    thread_pool = ThreadPoolExecutor(4)  # 定义4个线程执行此任务
    for image, label in read_from_gnt_dir(gnt_dir=gnt_dir):
        thread_pool.submit(save_img, label, image, counter)
        counter += 1
    thread_pool.shutdown()


def new_func(train_img_dir):
    os.mkdir(train_img_dir)

if __name__ == "__main__":
    # 路径
    data_dir = r'./data'
    train_gnt_dir = os.path.join(data_dir, 'HWDB1.1trn_gnt')
    test_gnt_dir = os.path.join(data_dir, 'HWDB1.1tst_gnt')
    train_img_dir = os.path.join(data_dir, 'train')
    test_img_dir = os.path.join(data_dir, 'test')

    # 使用 os.makedirs 确保路径存在
    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(test_img_dir, exist_ok=True)
    # 获取字符集合
    if not os.path.exists('char_dict'):
        char_set = set()
        for _, tagcode in read_from_gnt_dir(gnt_dir=test_gnt_dir):
            tagcode_unicode = struct.pack('>H', tagcode).decode('gb2312')
            char_set.add(tagcode_unicode)
        char_list = list(char_set)
        char_dict = dict(zip(sorted(char_list), range(len(char_list))))
        print(len(char_dict))
        print("char_dict=", char_dict)

        with open('char_dict', 'wb') as f:
            pickle.dump(char_dict, f)
    else:
        with open('char_dict', 'rb') as f:
            char_dict = pickle.load(f)
    #创建线程
    train_thread = threading.Thread(target=gnt_to_img, args=(train_gnt_dir, train_img_dir))
    test_thread = threading.Thread(target=gnt_to_img, args=(test_gnt_dir, test_img_dir))
    # 启动线程
    train_thread.start()
    test_thread.start()
    # 等待线程完成
    train_thread.join()
    test_thread.join()
