"""Class for Drone Deploy - Semantic Segmentation."""
import sys
import os
import numpy as np
import random
import torch
from .images2chips import run
from .utils import _urlretrieve, to_categorical

from PIL import Image
from torch.utils.data import Dataset


class DroneDeploy():
    """Drone Deploy Semantic Dataset.

    Args:
        root (string): Root directory of dataset.
        dataset_type (string, optional): Choose dataset type.
        download (bool, optional): If true, downloads the dataset from the internet and
            puts it in root directory. If dataset is already downloaded, it is not
            downloaded again.
        tensor_data (bool, optional): If true, raw dataset will converted to tensor data.
    """

    resources = {
        'dataset-sample': 'https://dl.dropboxusercontent.com/s/h8a8kev0rktf4kq/dataset-sample.tar.gz?dl=0',
        'dataset-medium': 'https://dl.dropboxusercontent.com/s/r0dj9mhyv4bgbme/dataset-medium.tar.gz?dl=0'
    }

    def __init__(self, root: str, dataset_type='dataset-sample', download: bool = False, tensor_data: bool = False):
        self.root = root
        self.dataset = dataset_type
        self.filename = f'{self.dataset}.tar.gz'

        if download and self._check_exists():
            print(f'zipfile "{self.filename}" already exists.')

        if download and not self._check_exists():
            self.download()

        if tensor_data:
            self.train_dataset, self.valid_dataset = self.load_dataset()

    def download(self):
        """Download a dataset, extract it and create the tiles."""
        print(f'Downloading "{self.dataset}"')
        self.root = os.path.expanduser(self.root)
        fpath = os.path.join(self.root, self.filename)
        _urlretrieve(self.resources[self.dataset], fpath)

        if not os.path.exists(self.dataset):
            print(f'Extracting "{self.filename}"')
            os.system(f'tar -xvf {self.filename}')
        else:
            print(f'Folder "{self.dataset}" already exists.')

        image_chips = f'{self.dataset}/image-chips'
        label_chips = f'{self.dataset}/label-chips'

        if not os.path.exists(image_chips) and not os.path.exists(label_chips):
            print("Creating chips")
            run(self.dataset)
        else:
            print(
                f'chip folders "{image_chips}" and "{label_chips}" already exist.')

    def _check_exists(self) -> bool:
        if self.dataset not in self.resources.keys():
            print(f"Unknown dataset {self.dataset}")
            print(f"Available dataset : {self.resources.keys()}")
            sys.exit(0)

        if os.path.exists(self.filename):
            return True
        else:
            return False

    def load_dataset(self):
        train_files = [
            f'{self.dataset}/image-chips/{fname}' for fname in load_lines(f'{self.dataset}/train.txt')]
        valid_files = [
            f'{self.dataset}/image-chips/{fname}' for fname in load_lines(f'{self.dataset}/valid.txt')]

        train_dataset = DroneDataset(self.dataset, train_files)
        valid_dataset = DroneDataset(self.dataset, valid_files)
        return train_dataset, valid_dataset


class DroneDataset(Dataset):
    def __init__(self, dataset, image_files):
        self.label_path = f'{dataset}/label-chips'
        self.image_path = f'{dataset}/image-chips'
        self.image_files = image_files
        random.shuffle(self.image_files)

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        image_file = self.image_files[idx]
        label_file = image_file.replace(self.image_path, self.label_path)

        image = load_img(image_file)
        label = mask_to_classes(load_img(label_file))

        tensor_image = torch.from_numpy(np.array(image))
        tensor_label = torch.from_numpy(np.array(label))
        return tensor_image, tensor_label

    def on_epoch_end(self):
        random.shuffle(self.image_files)


def load_lines(fname):
    with open(fname, 'r') as f:
        return [line.strip() for line in f.readlines()]


def load_img(fname):
    return np.array(Image.open(fname))


def mask_to_classes(mask):
    return to_categorical(mask[:, :, 0], 6)
