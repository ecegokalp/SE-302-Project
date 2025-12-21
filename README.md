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
  * General Schedule:
  * Daily Plan:
  * Student Based:
  * Classroom Based:
  * Exam Attendance:
* **Export:** The user can export the generated schedule to CSV and PDF formats for easy distribution.

## User Interface
* SETTINGS & DATA PANEL
    * DATA MANAGEMENT (FILES & DATABASE)
    * EXAM CALENDAR SETTINGS
    * ACTIVITY LOG
    * BUTTONS
* SCHEDULE (RESULT) PANEL
  * GENERAL SCHEDULE VIEW
  * DAILY PLAN VIEW
  * STUDENT BASED VIEW
  * CLASSROOM BASED VIEW
  * EXAM ATTENDANCE VIEW
* HELP MENU

//TBA: SON HALINDE SSLER KOYULACAK

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