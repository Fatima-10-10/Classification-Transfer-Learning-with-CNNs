# -*- coding: utf-8 -*-
"""dla3 t2 p2

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1M-x5JSVx1ZfGzMo3zZxacHl5Oc6x7kMK
"""



from google.colab import drive
drive.mount('/content/drive')

import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image


class Dataloader(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.classes = sorted(os.listdir(root_dir))  # Get class labels from directory names
        self.class_to_label = {cls: i for i, cls in enumerate(self.classes)}  # Assign label to each class
        self.file_paths = self.get_file_paths()

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        image_path = self.file_paths[idx]
        image = Image.open(image_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        # Extract class label from the parent directory name
        label = self.class_to_label[os.path.basename(os.path.dirname(image_path))]

        return image, label

    def get_file_paths(self):
        file_paths = []
        for cls in self.classes:
            class_dir = os.path.join(self.root_dir, cls)
            files = os.listdir(class_dir)
            file_paths.extend([os.path.join(class_dir, file) for file in files])
        return file_paths


def split(root_dir, train_split=0.7, test_split=0.15, val_split=0.15):
    # Get list of all image file paths
    all_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".bmp") or file.endswith(".jpg") or file.endswith(".png"):  # Adjust file extensions as needed
                all_files.append(os.path.join(root, file))

    # Shuffle the file paths
    np.random.shuffle(all_files)

    # Calculate split sizes
    num_files = len(all_files)
    train_size = int(train_split * num_files)
    test_size = int(test_split * num_files)
    val_size = num_files - train_size - test_size

    # Split the file paths
    train_files = all_files[:train_size]
    test_files = all_files[train_size:train_size + test_size]
    val_files = all_files[train_size + test_size:]

    return train_files, test_files, val_files


root_dir = '/content/drive/MyDrive/deep learning a3 data/image_classification'
train_files, test_files, val_files = split(root_dir)

print("Number of training images:", len(train_files))
print("Number of test images:", len(test_files))
print("Number of validation images:", len(val_files))

# Define transforms for data augmentation and normalization
data_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Create custom datasets
train_dataset = Dataloader(root_dir, transform=data_transform)
test_dataset = Dataloader(root_dir, transform=data_transform)
val_dataset = Dataloader(root_dir, transform=data_transform)

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

# Example usage
for images, labels in train_loader:
    print(f'Images shape: {images.shape}')
    print(f'Labels shape: {labels.shape}')
    break

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, f1_score
import seaborn as sns

# Load pre-trained VGG16 model
vgg16 = models.vgg16(pretrained=True)

# Freeze layers
for param in vgg16.parameters():
    param.requires_grad = False

# Modify the last layer for 7 classes
num_features = vgg16.classifier[6].in_features
vgg16.classifier[6] = nn.Linear(num_features, 7)

# Define loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(vgg16.parameters(), lr=0.001, momentum=0.9)

# Move model to appropriate device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
vgg16.to(device)

def train(model, train_loader, val_loader, criterion, optimizer, num_epochs):
    train_loss_history = []
    train_acc_history = []
    val_loss_history = []
    val_acc_history = []

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            total_train += labels.size(0)
            correct_train += (predicted == labels).sum().item()

        train_loss = running_loss / len(train_loader)
        train_acc = correct_train / total_train

        val_loss, val_acc = evaluate(model, val_loader, criterion)

        train_loss_history.append(train_loss)
        train_acc_history.append(train_acc)
        val_loss_history.append(val_loss)
        val_acc_history.append(val_acc)

        print(f'Epoch [{epoch + 1}/{num_epochs}], '
              f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, '
              f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}')

    return train_loss_history, train_acc_history, val_loss_history, val_acc_history

def evaluate(model, loader, criterion):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    loss = running_loss / len(loader)
    acc = correct / total

    return loss, acc

def plot_curves(train_loss, train_acc, val_loss, val_acc):
    epochs = range(1, len(train_loss) + 1)

    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(epochs, train_loss, label='Train')
    plt.plot(epochs, val_loss, label='Validation')
    plt.title('Loss Curves')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(epochs, train_acc, label='Train')
    plt.plot(epochs, val_acc, label='Validation')
    plt.title('Accuracy Curves')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()

    plt.tight_layout()
    plt.show()

def test(model, loader):
    model.eval()
    correct = 0
    total = 0
    y_true = []
    y_pred = []

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)

            outputs = model(images)
            _, predicted = torch.max(outputs, 1)

            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())

    accuracy = correct / total
    cm = confusion_matrix(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='macro')

    return accuracy, cm, f1

# Train the model
num_epochs = 10
train_loss_history, train_acc_history, val_loss_history, val_acc_history = train(vgg16, train_loader, val_loader, criterion, optimizer, num_epochs)

# Plot loss and accuracy curves
plot_curves(train_loss_history, train_acc_history, val_loss_history, val_acc_history)

# Test the model
test_accuracy, confusion_matrix, f1_score = test(vgg16, test_loader)
print(f'Test Accuracy: {test_accuracy:.4f}')
print(f'F1 Score: {f1_score:.4f}')

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(confusion_matrix, annot=True, fmt='d', cmap='Blues')
plt.xlabel('Predicted Labels')
plt.ylabel('True Labels')
plt.title('Confusion Matrix')
plt.show()

