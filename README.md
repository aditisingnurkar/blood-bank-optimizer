# HEMATIX – Blood Bank Allocation System

## Overview

HEMATIX is a Python desktop application that automates blood allocation by matching hospital requests with available blood units based on distance, blood unit expiry, and request priority. It features a live inventory dashboard, visual analytics, and a donation portal for efficient blood bank management.

---

## Features

* Imports and validates blood bank, hospital, inventory, and request data from CSV files.
* Calculates the nearest blood bank using the Haversine distance formula.
* Allocates blood units based on proximity and expiry date.
* Prioritizes hospital requests by urgency.
* Supports complete, partial, and failed allocations.
* Live inventory dashboard with allocation details and summary statistics.
* Interactive charts for blood availability, demand trends, and inventory distribution.
* Donation portal with appointment booking, donor registration, photo capture, and nearby donation camps.
* Automatically maintains allocation and donation logs.

---

## Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/18b196d2-041c-4030-9aa7-0afccdea046c" width="48%">
  <img src="https://github.com/user-attachments/assets/0e2361ef-6e6a-48fa-91a3-b3b7c9d8397a" width="48%">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/de251f89-b852-4616-acc1-58484699a353" width="48%">
  <img src="https://github.com/user-attachments/assets/f200e095-cc39-47f9-82a5-81e73923cf7d" width="48%">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/9bc2a677-f973-4419-b7a2-7e97f00d2a41" width="48%">
  <img src="https://github.com/user-attachments/assets/68fd6fe4-a068-41d0-b48c-95d2e1305f2b" width="48%">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/7adcc955-be55-440c-9d53-b3432bda14a4" width="48%">
  <img src="https://github.com/user-attachments/assets/4b6a1050-e915-4249-b48a-22e6ac38f8cd" width="48%">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/cb62cf64-63a9-4d90-ae4d-066b0f45c343" width="48%">
  <img src="https://github.com/user-attachments/assets/c235b2e7-8865-4bf1-8b3d-a01c9731cf6a" width="48%">
</p>

---

## Tech Stack

* Python
* Tkinter
* Pandas
* NumPy
* Matplotlib
* Seaborn
* OpenCV
* Pillow (PIL)

---

## How to Run

Generate the distance matrix:

```bash
python -m src.distance_matrix
```

Run the application:

```bash
python -m src.main
```

---

## Requirements

Install the required dependencies:

```bash
pip install pandas numpy matplotlib seaborn pillow opencv-python
```
