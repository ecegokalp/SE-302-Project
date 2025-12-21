# ExamTable Manager

## Overview
ExamTable Manager is a desktop application designed to automate the process of scheduling university exam schedules. It uses a constraint satisfaction algorithm to assign courses to given classrooms and time slots while preventing student conflicts, respecting room capacities and other limitations given by the user.

## Prerequisites
* **Operating System:** Windows

## Features and Usage
* **Data import:** Users are able to import `.csv` files that include information about classrooms and capacities, Attendance lists, Courses and Students in correct formatting. You can access sample files below:
    * [Classrooms and Capacities List](docs/sampleData_AllClassroomsAndTheirCapacities.csv)
    * [Attendance Lists](docs/sampleData_AllAttendanceLists.csv)
    * [Course List](docs/sampleData_AllCourses.csv)
    * [Students List](docs/sampleData_AllStudents.csv)

* **Database actions:** Users are able to save their progress into a database and load from the database from specific slots. They can also compare currently loaded data with saved data to see differences between their files.
* **Exam Period Adjustment:** Users can pick a start date for their examination period and specify how long the exam period should last. They can also customize how many slots should exist in a day and how long a slot should be, and remove slots they don’t need.
* **Activity Log:** The program supplies the user with a report of all the actions they have executed.
* **Schedule View:** Users can view the generated schedules in multiple formats:
  * General Schedule: Shows the general plan.
  * Daily Plan: Shows the plan based on days.
  * Student Based: Shows the plan based on students.
  * Classroom Based: Shows the plan based on classrooms.
  * Exam Attendance: Shows the attendance status of students.
* **Export:** The user can export the generated schedule to CSV and PDF formats for easy distribution.

## User Interface
* SETTINGS & DATA PANEL
<img width="1509" height="950" alt="settings_data" src="https://github.com/user-attachments/assets/272b2bc1-8500-426a-b6a4-69985db7a31f" />

   * DATA MANAGEMENT (FILES & DATABASE)
<img width="852" height="216" alt="data_management" src="https://github.com/user-attachments/assets/8283ec37-ee31-4d66-a8e3-5762f317bfdb" />

   * EXAM CALENDAR SETTINGS
<img width="847" height="280" alt="slots" src="https://github.com/user-attachments/assets/4f4fee44-aa4c-4f47-955d-c686a76914bb" />

   * ACTIVITY LOG
<img width="591" height="511" alt="logs" src="https://github.com/user-attachments/assets/043ac9ed-9e49-4324-b841-0494a23a6b01" />

   * BUTTONS
<img width="429" height="70" alt="buttons" src="https://github.com/user-attachments/assets/5a95e3ac-abf9-4355-8537-22cffb0b0b53" />

* SCHEDULE (RESULT) PANEL
  * GENERAL SCHEDULE VIEW
  <img width="1510" height="947" alt="general" src="https://github.com/user-attachments/assets/ff16f107-5ef4-4c7c-837e-4606034cf530" />

  * DAILY PLAN VIEW
  <img width="1511" height="947" alt="daily" src="https://github.com/user-attachments/assets/de836174-a4ec-41e0-a45f-abd29825acc6" />

  * STUDENT BASED VIEW
  <img width="1511" height="949" alt="student" src="https://github.com/user-attachments/assets/831b0d20-c627-46fc-8c07-39554aecd9d6" />

  * CLASSROOM BASED VIEW
  <img width="1512" height="950" alt="class" src="https://github.com/user-attachments/assets/83bc4793-0518-4d33-a78e-830b5a48a0df" />

  * EXAM ATTENDANCE VIEW
  <img width="1511" height="949" alt="exam_attend" src="https://github.com/user-attachments/assets/8e1d7ef1-acb6-4e06-b953-e11f8bc74225" />


* HELP MENU
<img width="696" height="603" alt="Screenshot 2025-12-21 at 12 40 00" src="https://github.com/user-attachments/assets/57daaf39-76c5-4b3e-9bc6-6a7bfc90aee4" />


## File Structure
* **Database:** The system stores data in an SQLite database file (`examtable.db`)
* **Input Support:** The application supports importing data from .csv files that match specific patterns.

## Project Management
You can access our trello board [here](https://trello.com/b/2vd9H7P7)

### Milestone 1 - Requirements
You can access the requirements document [here](docs/Group-4_Requirements_Document.pdf)

### Milestone 2 - Design Document
You can access the design document [here](docs/Group-4_Design_Document.pdf)

## Help & Support
For additional support or information about the system, please contact the development team or refer to the help menu in the program.
