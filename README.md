# SE-302-Project
# ExamTable Manager

**ExamTable Manager** is a desktop application designed to automate the complex process of scheduling university exams. By utilizing Constraint Satisfaction Problem (CSP) algorithms, it assigns courses to classrooms and time slots while preventing conflicts, respecting room capacities, and adhering to user-defined constraints.

---

## 📋 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [User Interface](#user-interface)
- [Project Architecture](#project-architecture)
- [Documentation & Planning](#documentation--planning)
- [Support](#support)

---

## 🚀 Overview

Scheduling exams is often a manual, error-prone process. ExamTable Manager streamlines this by allowing administrators to:
1. Import raw university data (Courses, Students, Rooms).
2. Define constraints (Time slots, Exam periods).
3. Automatically generate conflict-free schedules.
4. Export results for distribution.

---

## ✨ Key Features

### 📂 Data Management
* **CSV Import:** Seamlessly import `.csv` files for Classrooms, Attendance lists, Courses, and Students.
    * [Download Sample Import Files Here](#) *(Link to your sample files)*
* **Database Persistence:** Save progress to a local database and load from specific save slots.
* **Data Comparison:** Compare currently loaded data against saved versions to track changes.

### ⚙️ Scheduling Engine
* **Flexible Period Adjustment:** Set custom start dates, exam period duration, and daily slot configurations.
* **Constraint Handling:** Automatically manages room capacities and student conflicts.
* **Manual Overrides:** Remove specific time slots that are unavailable.

### 📊 Visualization & Reporting
* **Activity Log:** A running report of all user actions for audit purposes.
* **Multiple Schedule Views:**
    * **General Schedule:** High-level overview.
    * **Daily Plan:** Hour-by-hour breakdown.
    * **Student Based:** Individual schedules for students.
    * **Classroom Based:** Room utilization views.
    * **Exam Attendance:** Signature lists.

### 📤 Export
* Export generated schedules to **CSV** and **PDF** for easy printing and distribution.

---

## 💻 Prerequisites

* **Operating System:** Windows 10/11
* *(Optional: Add specific runtime requirements here, e.g., Java Runtime Environment 17, Python 3.9, or .NET Framework)*

---

## 🛠 Installation & Setup

1.  Download the latest release from the [Releases Page](#).
2.  Unzip the package to your desired location.
3.  Run `ExamTableManager.exe`.
4.  Ensure `examtable.db` is created in the application directory upon first launch.

---

## 📖 Usage Guide

1.  **Import Data:** Navigate to the **Data Panel** and upload your CSV files.
2.  **Configure Settings:** Set your Exam Calendar (Start date, duration, slot length) in the **Settings Panel**.
3.  **Generate:** Run the scheduler.
4.  **Review:** Use the **Schedule Panel** to check the Daily Plan or Classroom views.
5.  **Export:** Save your final schedule as a PDF.

---

## 🖥 User Interface

The application is divided into intuitive panels:

* **Settings & Data Panel:** Configuration and file imports.
* **Data Management:** Database save/load operations.
* **Exam Calendar Settings:** Time management.
* **Activity Log:** System status and history.
* **Schedule (Result) Panel:** The main visualization area containing:
    * General Schedule View
    * Daily Plan View
    * Student & Classroom Views
    * Exam Attendance Sheets

> **Screenshots:**
>
> *[Place Screenshot of Main Dashboard Here]*
>
> *[Place Screenshot of Generated Schedule Here]*

---

## 📂 Project Architecture

### File Structure
* **Database:** The system utilizes SQLite for lightweight, serverless data storage. The main file is `examtable.db`, located in the root directory.
* **Input Support:** Strictly typed `.csv` parsing for data ingestion.

---

## 📅 Documentation & Planning

We use Agile methodologies to track our progress.

* **Project Management:** [Trello Board](#) *(Link to your Trello)*
* **Milestone 1:** [Requirements Document](#) *(Link or relative path to file)*
* **Milestone 2:** [Design Document](#) *(Link or relative path to file)*

---

## 🆘 Support

For additional support, bug reports, or feature requests, please check the **Help Menu** within the application or contact the development team at:

* **Email:** your-email@example.com
* **Issues:** Please open a GitHub Issue for bug reports.