import torch
import torch.nn
from tqdm import tqdm


class TextCNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        modules = []
        for i in [2, 3, 4]:
            module = torch.nn.Sequential(
                torch.nn.Conv1d(in_channels=200, out_channels=100, kernel_size=i),
                torch.nn.ReLU(),
                torch.nn.MaxPool1d(kernel_size=625 - i + 1)
            )
            modules.append(module)
        self.modules = torch.nn.ModuleList(modules=modules)
        self.out = torch.nn.Linear(in_features=3 * 100, out_features=2)

    def forward(self, x):
        x_list = [conv(x) for conv in self.modules]
        x = torch.cat(x_list, 1)
