# -*- coding: utf-8 -*-
"""dl a3 t1

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gIRrK79SfNehoOcbw1sR4_Cmihrfs4I4
"""

from google.colab import drive
drive.mount('/content/drive')

"""# TASK 1"""

import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, transforms
from torch.utils.data.sampler import SubsetRandomSampler
import numpy as np
import matplotlib.pyplot as plt


class Dataloader(Dataset):
    def __init__(self, dataset, train=True, transform=None):
        self.dataset = dataset
        self.train = train
        self.transform = transform

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        image, label = self.dataset[idx]

        # Convert to tensor
        image = transforms.functional.to_tensor(image)

        # Transformations
        if self.transform:
            image = self.transform(image)
        # Normalize image
        image = transforms.functional.normalize(image, mean=(0.5,), std=(0.5,))
        # One-hot encoding thw label
        if self.train:
            one_hot_label = torch.zeros(10)
            one_hot_label[label] = 1
            return image, one_hot_label
        else:
            return image, label

def split_data_indices(dataset, split_size):
    num_data = len(dataset)
    indices = list(range(num_data))
    split = int(np.floor(split_size * num_data))
    np.random.shuffle(indices)
    selected_indices = indices[:split]
    return selected_indices

# Define transform for converting to tensor
data_transform = transforms.Compose([])  # No need for additional transforms

# Load MNIST dataset
train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=data_transform)
test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=data_transform)

# Select 10% of training and test data
train_indices = split_data_indices(train_dataset, split_size=0.10)
test_indices = split_data_indices(test_dataset, split_size=0.10)

# Create data samplers
train_sampler = SubsetRandomSampler(train_indices)
test_sampler = SubsetRandomSampler(test_indices)
# Use CustomMNISTDataset to apply further transformations
train_dataset = Dataloader(train_dataset, train=True, transform=data_transform)
test_dataset = Dataloader(test_dataset, train=False, transform=data_transform)

# Splitting training data to train and tes splits
def split_train_valid(train_dataset, validation_split=0.15):
    # Calculate the number of samples for validation set
    num_train_samples = len(train_dataset)
    num_val_samples = int(validation_split * num_train_samples)

    # Create indices for shuffling and splitting the dataset
    indices = list(range(num_train_samples))
    np.random.shuffle(indices)

    # Split indices into training and validation indices
    val_indices = indices[:num_val_samples]
    train_indices = indices[num_val_samples:]

    # Create samplers for training and validation sets
    train_sampler = SubsetRandomSampler(train_indices)
    val_sampler = SubsetRandomSampler(val_indices)

    # Create data loaders for training and validation sets
    train_loader = DataLoader(train_dataset, batch_size=64, sampler=train_sampler)
    val_loader = DataLoader(train_dataset, batch_size=64, sampler=val_sampler)

    return train_loader, val_loader


# Create data loaders with samplers
test_loader = DataLoader(test_dataset, batch_size=64, sampler=test_sampler)
train_loader, val_loader = split_train_valid(train_dataset)

# Example usage
for images, labels in train_loader:
    print(f'Images shape: {images.shape}')
    print(f'Labels shape: {labels.shape}')
    break  # Just to show one batch

import torch
import torch.nn as nn
import torch.nn.functional as F

class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()

        # First convolutional block
        self.conv1_1 = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
        self.conv1_2 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        # pooling
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Second convolutional block
        self.conv2_1 = nn.Conv2d(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        self.conv2_2 = nn.Conv2d(in_channels=128, out_channels=256, kernel_size=3, padding=1)
        # pooling
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        # 3 Fully connected layers
        self.fc1 = nn.Linear(256 * 7 * 7, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, 10)  # 10 output classes

    def forward(self, x):
        # First convolutional block
        x = F.relu(self.conv1_1(x))
        x = F.relu(self.conv1_2(x))
        x = self.pool1(x)

        # Second convolutional block
        x = F.relu(self.conv2_1(x))
        x = F.relu(self.conv2_2(x))
        x = self.pool2(x)

        # Flatten the output for fully connected layers
        x = torch.flatten(x, 1)

        # FC layers
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)

        return x

# Instantiate the model
model = CNNModel()
print(model)

def train(model, train_loader, val_loader, criterion, optimizer, num_epochs, lr_decay_patience=3):

    train_losses = []
    val_losses = []
    train_accuracies = []
    val_accuracies = []

    best_val_loss = np.inf
    patience = 0

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total_train += labels.size(0)
            correct_train += (predicted == torch.argmax(labels, 1)).sum().item()

        train_loss = running_loss / len(train_loader)
        train_accuracy = 100 * correct_train / total_train
        train_losses.append(train_loss)
        train_accuracies.append(train_accuracy)

        # Validation
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                total_val += labels.size(0)
                correct_val += (predicted == torch.argmax(labels, 1)).sum().item()

        val_loss /= len(val_loader)
        val_accuracy = 100 * correct_val / total_val
        val_losses.append(val_loss)
        val_accuracies.append(val_accuracy)

        print(f'Epoch [{epoch+1}/{num_epochs}], Train Loss: {train_loss:.4f}, Train Acc: {train_accuracy:.2f}%, Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.2f}%')

        # Early stopping and learning rate decay
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience = 0
        else:
            patience += 1
            if patience >= lr_decay_patience:
                for g in optimizer.param_groups:
                    g['lr'] *= 0.1

                patience = 0

    return model, train_losses, val_losses, train_accuracies, val_accuracies

def test(model, test_loader):
    model.eval()
    pred_labels = []
    true_labels = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            pred_labels.extend(predicted.tolist())
            true_labels.extend(torch.argmax(labels, 1).tolist())

    return pred_labels, true_labels

def plot_loss_accuracy(train_losses, val_losses, train_accuracies, val_accuracies):
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Loss Curves')
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(train_accuracies, label='Train Accuracy')
    plt.plot(val_accuracies, label='Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title('Accuracy Curves')
    plt.legend()

    plt.show()

def plot_confusion_matrix(y_true, y_pred, classes):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion Matrix')
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)

    fmt = 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.show()

def visualize_predictions(images, true_labels, predicted_labels, class_names):
    num_images = len(images)
    fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(12, 6))
    fig.subplots_adjust(hspace=0.6, wspace=0.3)
    for i, ax in enumerate(axes.flat):
        if i < num_images:
            ax.imshow(images[i], cmap='binary')
            if true_labels[i] == predicted_labels[i]:
                ax.set_title(f'True: {class_names[true_labels[i]]}\nPred: {class_names[predicted_labels[i]]}', color='green')
            else:
                ax.set_title(f'True: {class_names[true_labels[i]]}\nPred: {class_names[predicted_labels[i]]}', color='red')
        ax.axis('off')
    plt.show()

import torch.optim as optim
# Training the model
model.train()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.1)
epochs=5
trained_model, train_losses, val_losses, train_accuracies, val_accuracies = train(model, train_loader, val_loader, criterion, optimizer, num_epochs=epochs)

# Plotting loss and accuracy curves
plot_loss_accuracy(train_losses, val_losses, train_accuracies, val_accuracies)

# Testing the model
predictions, true_labels = test(trained_model, test_loader)

import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image

def save_model(model, filepath):
    torch.save(model.state_dict(), filepath)
    print("Model saved successfully.")

def load_model(model_class, filepath):
    model = model_class()
    model.load_state_dict(torch.load(filepath))
    print("Model loaded successfully.")
    return model

def test(model, test_loader):
    model.eval()
    predictions = []
    true_labels = []

    with torch.no_grad():
        for images, labels in test_loader:
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            predictions.extend(predicted.tolist())
            true_labels.extend(labels.tolist())

    return predictions, true_labels

def runtime_testing(model, image_path, transform):
    model.eval()
    image = Image.open(image_path).convert('L')  # Convert to grayscale
    image = transform(image).unsqueeze(0)  # Add batch dimension
    output = model(image)
    prediction = torch.argmax(F.softmax(output, dim=1), dim=1).item()
    return prediction

# Save the model
save_model(model, '/content/drive/MyDrive/deep learning a3 data/task1')

# Load the model
loaded_model = load_model(CNNModel, '/content/drive/MyDrive/deep learning a3 data/task1')

# Test the model
predictions, true_labels = test(loaded_model, test_loader)

# Runtime testing
image_path = '/content/drive/MyDrive/deep learning a3 data/mnist/dla3_test/test/1.png'  # Replace with the path to your input image
predicted_label = runtime_testing(loaded_model, image_path, transform)
print("Predicted label:", predicted_label)

# Assuming `test_model` function returns predictions and true labels
predictions, true_labels = test(loaded_model, test_loader)

# Calculating metrics
accuracy = accuracy_score(true_labels, predictions)
f1 = f1_score(true_labels, predictions, average='macro')

print(f'Test Accuracy: {accuracy:.2f}')
print(f'F1 Score: {f1:.2f}')

def visualize_metrics(accuracy, f1):
    # Plotting accuracy and F1 score
    plt.figure(figsize=(8, 5))
    plt.bar(['Accuracy', 'F1 Score'], [accuracy, f1], color=['blue', 'green'])
    plt.xlabel('Metrics')
    plt.ylabel('Score')
    plt.title('Accuracy and F1 Score')
    plt.ylim(0, 1)  # Set y-axis limit from 0 to 1
    plt.show()

# Plot accuracy and F1 score
visualize_metrics(accuracy, f1)

# Plotting confusion matrix
class_names = [str(i) for i in range(10)]
plot_confusion_matrix(true_labels, predictions, class_names)

def visualize_predictions(images, true_labels, predicted_labels, class_names):
    # Display 5 accurate predictions
    accurate_indices = [i for i in range(len(true_labels)) if true_labels[i] == predicted_labels[i]]

    fig, axes = plt.subplots(2, 5, figsize=(12, 6))
    fig.subplots_adjust(hspace=0.6, wspace=0.3)

    for i in range(5):
        ax = axes[0, i]
        ax.imshow(images[accurate_indices[i]], cmap='binary')
        ax.set_title(f'True: {class_names[true_labels[accurate_indices[i]]]}\nPred: {class_names[predicted_labels[accurate_indices[i]]]}')
        ax.axis('off')

    # Display 5 wrong predictions
    wrong_indices = [i for i in range(len(true_labels)) if true_labels[i] != predicted_labels[i]]

    for i in range(5):
        ax = axes[1, i]
        ax.imshow(images[wrong_indices[i]], cmap='binary')
        ax.set_title(f'True: {class_names[true_labels[wrong_indices[i]]]}\nPred: {class_names[predicted_labels[wrong_indices[i]]]}')
        ax.axis('off')

    plt.show()

# Extract a subset of data from the test dataset
num_images_to_visualize = 10  # Number of images to visualize
images_to_visualize = []
true_labels_to_visualize = []
predicted_labels_to_visualize = []

# Get a subset of data from the test loader
for i, (images, labels) in enumerate(test_loader):
    images_to_visualize.extend(images.numpy())
    true_labels_to_visualize.extend(labels.numpy())
    predicted_labels_to_visualize.extend(predictions[i * len(images):(i + 1) * len(images)])

    if len(images_to_visualize) >= num_images_to_visualize:
        break

# Reshape images to (28, 28)
images_to_visualize = [image.reshape(28, 28) for image in images_to_visualize]

# Call visualize_predictions function
class_names = [str(i) for i in range(10)]
visualize_predictions(images_to_visualize, true_labels_to_visualize, predicted_labels_to_visualize, class_names)