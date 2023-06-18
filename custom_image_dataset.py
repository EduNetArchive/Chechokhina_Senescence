# -*- coding: utf-8 -*-
"""Custom_Image_Dataset.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tNEbNohl_Sja_DWstuF7tLMsQnjXOBlb
"""

import os
import pandas as pd
import torchvision
from torch.utils.data import Dataset
from torchvision.io import read_image
from torchvision.ops import masks_to_boxes
from torchvision import transforms

class CustomImageDataset(Dataset):
    def __init__(self, annotations_file, img_dir, mask_dir, transform=None, target_transform=None):
        self.img_labels = pd.read_csv(annotations_file)
        self.img_dir = img_dir
        self.mask_dir = mask_dir
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.img_labels)

    def __getitem__(self, idx):
        label = self.img_labels.iloc[idx]['Class']
        img_path = os.path.join(self.img_dir + self.img_labels.iloc[idx]['File'])
        mask_path = os.path.join(self.img_dir + self.img_labels.iloc[idx]['Mask'])

        image =  Image.open(img_path)
        image = np.array(image)/65535
        image = (image - mean_train)/std_train
        image_torch = torch.from_numpy(image)
        image_torch = image_torch.unsqueeze(0)

        masks = np.load(mask_path)
        mask = np.ma.masked_values(masks, self.img_labels.iloc[idx]['Cell number']).mask
        torch_mask = torch.unsqueeze(torch.from_numpy(mask), 0)
        boxes = masks_to_boxes(torch_mask)

        mean_x = int((boxes[0][0]+boxes[0][2])/2)
        mean_y = int((boxes[0][1]+boxes[0][3])/2)

        len_x = int((-boxes[0][0]+boxes[0][2]))
        len_y = int((-boxes[0][1]+boxes[0][3]))

        masked_cell = (image*mask)

        box_cell = torch.from_numpy(masked_cell[int(boxes[0][1]):int(boxes[0][3]),
                                        int(boxes[0][0]):int(boxes[0][2])])

        box_size_x = int(-boxes[0][0])+int(boxes[0][2])
        box_size_y = int(-boxes[0][1])+int(boxes[0][3])

        x_size, y_size = 380, 380

        if box_size_x>x_size:
            box_cell = box_cell[:, box_size_x//2 - x_size//2: box_size_x//2+(x_size-x_size//2)]
            box_size_y, box_size_x= box_cell.shape[0], box_cell.shape[1]
        if box_size_y>y_size:
            box_cell = box_cell[box_size_y//2 - y_size//2: box_size_y//2+(y_size-y_size//2), :]
            box_size_y, box_size_x = box_cell.shape[0], box_cell.shape[1]

        final_image = torch.zeros((x_size, y_size))
        final_image[y_size//2-box_size_y//2: y_size//2+(box_size_y-box_size_y//2),
                      x_size//2-box_size_x//2: x_size//2+(box_size_x-box_size_x//2)] = box_cell
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)

        return final_image.unsqueeze(0), label