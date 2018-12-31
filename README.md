# Pharmacy Stock App


## About

This is the second project for the Udacity Full Stack Nanodegree. The Pharmacy Stock App consists of developing an application that provides a list of Medications within a variety of pharmacies, as well as provide a user registration and authentication system. This project uses persistent data storage to create a RESTful web application that allows users to perform Create, Read, Update, and Delete operations.

A user does not need to be logged in in order to read the pharmacies or items uploaded. However, users who created an item are the only users allowed to update or delete the item that they created.

This program uses third-party auth with Google. Some of the technologies used to build this application include Flask, Bootsrap, Jinja2, and SQLite.


## Skills used for this project
- Python
- HTML
- CSS
- Bootstrap
- Flask
- Jinja2
- SQLAchemy
- OAuth
- Google Login

## Some things you might need
- [Vagrant](https://www.vagrantup.com/)
- [Udacity Vagrantfile](https://github.com/udacity/fullstack-nanodegree-vm)
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

## Getting Started

- Install Vagrant and VirtualBox
- Clone the Vagrantfile from the Udacity Repo
- Clone this repo into the `catlog/` directory found in the Vagrant directory
- Run `vagrant up` to run the virtual machine, then `vagrant ssh` to login to the VM
- run application with `python application.py` from within its directory
- go to `http://localhost:5000/pharmacies/` to access the application
- *if first time running, you must add a pharmacy before adding a medication
