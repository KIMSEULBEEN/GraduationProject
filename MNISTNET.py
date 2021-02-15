from __future__ import print_function
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
import numpy as np

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

        self.load_model()

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output

    def load_model(self):
        self.load_state_dict(torch.load("mnist_cnn.pt"))
        self.eval()

    def test_image(self, image):
        def preprocess_image(image):
            height, width = image.shape
            block_size = width // 5 if (width // 5) % 2 == 1 else width // 5 + 1
            # print("block size: ", block_size)

            image_bin = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 151, 30)
            image_bin = cv2.bitwise_not(image_bin)
            cnt, labels, stats, centroids = cv2.connectedComponentsWithStats(image_bin)

            x_max, y_max, w_max, h_max, area_max = 0, 0, 0, 0, 0
            for i in range(1, cnt):
                (x, y, w, h, area) = stats[i]
                if (width * height / 2 > area > area_max):
                    x_max, y_max, w_max, h_max, area_max = x, y, w, h, area

                # cv2.rectangle(image, (x, y, w, h), 0)

            aspect_ratio = width / height  # 가로/세로 비율, 클 수록 가로가 길다

            # print(aspect_ratio)
            image_num = image_bin[y_max:y_max + h_max, x_max:x_max + w_max]
            image_num = cv2.copyMakeBorder(image_num, int(width * aspect_ratio / 5), int(width * aspect_ratio / 5)
                                           , int(height * aspect_ratio / 5), int(height * aspect_ratio / 5), cv2.BORDER_CONSTANT)
            height, width = image_num.shape

            aspect_num = width - height
            if (aspect_num > 0):
                image_num = cv2.copyMakeBorder(image_num, aspect_num // 2, aspect_num // 2, 0, 0, cv2.BORDER_CONSTANT)
            else:
                image_num = cv2.copyMakeBorder(image_num, 0, 0, abs(aspect_num // 2), abs(aspect_num // 2), cv2.BORDER_CONSTANT)
            image_num = cv2.resize(image_num, dsize=(28, 28), interpolation=cv2.INTER_AREA)
            return image_num
        image = preprocess_image(image)

        img_tensor = np.zeros([1, 1, 28, 28], dtype=np.double)
        img_tensor[0, 0, :, :] = image
        t = torch.from_numpy(img_tensor).float()
        pred = (int)(self(t).argmax(dim=1, keepdim=True)[0][0])
        print(pred)

def main():
    def set_args():
        # Training settings
        parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
        parser.add_argument('--no-cuda', action='store_true', default=True, help='disables CUDA training')
        parser.add_argument('--seed', type=int, default=1, metavar='S', help='random seed (default: 1)')
        args = parser.parse_args()

        use_cuda = not args.no_cuda and torch.cuda.is_available()
        torch.manual_seed(args.seed)
        device = torch.device("cuda" if use_cuda else "cpu")
        return device

    model = Net().to(set_args())

    capture = cv2.VideoCapture(2)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    while True:
        _, image = capture.read()
        cv2.imshow("image", image)
        key = cv2.waitKey(1)

        if key == ord('s') or key == ord('S'):
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            model.test_image(image)

    capture.release()
    cv2.destroyAllWindows()



if __name__ == '__main__':
    main()
