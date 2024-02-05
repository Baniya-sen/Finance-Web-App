# Finance Website

Welcome to the Finance Website project! This web application provides various finance-related functionalities, making it easier for users to manage their financial activities effectively.
View deployed app: [Here](https://financestocks.pythonanywhere.com/)

### Home Page
![Home Page](https://github.com/Baniya-sen/Finance-Web-App/assets/144620117/bd14586a-e8f3-475c-85c3-9af5b8aafab0)

## Description

The Finance Website is a Flask-based web application designed to offer users a comprehensive platform for managing their finances. Flask, a lightweight and flexible web framework for Python, is utilized to streamline the development process, enabling rapid prototyping and easy scalability.

## Features

### Stock Tracking
Stay informed about your favorite stocks with real-time price updates. Track the performance of individual stocks or create custom watchlists to monitor multiple stocks simultaneously.

### Portfolio Management
Effortlessly manage your investment portfolio with our intuitive portfolio management tools. Keep track of your holdings, analyze performance metrics, and make informed investment decisions.

### Financial News Aggregation
Stay ahead of the curve with our curated financial news section. Get access to the latest news articles, market insights, and expert analysis to help you stay informed about the financial markets.

## Technologies Used

- **Flask**: Flask is a lightweight and flexible web framework for Python. It provides the foundation for building web applications with ease, enabling rapid development and easy scalability.
  
- **Flask-Session**: Flask-Session is an extension for Flask that adds support for server-side sessions. It allows us to store user session data securely.

- **requests**: The requests library is used for making HTTP requests in Python. We leverage it to fetch real-time stock prices and financial news from external APIs.

- **pytz**: pytz is a Python library for working with time zones. It enables us to handle date and time data effectively, ensuring accurate time zone conversions and display.

## Usage

1. Install dependencies listed in the `requirements.txt` file:
   ```cmd
   pip install -r requirements.txt
   ```
in the command window.
  
2. Run the Flask application:
   Add ```Python
         if __name__ == "__main__:
                 app.run(debug=True)"```
   in a development environment.

You can also access the deployed website through your web browser at the provided URL:
   `https://financestocks.pythonanywhere.com` just register with a username and password.

## Screenshots

### Login Page
![Login Page](https://github.com/Baniya-sen/Finance-Web-App/assets/144620117/a3d5d041-a1f4-4666-83f1-ce85b322b81a)

### Stock Tracking
![buy](https://github.com/Baniya-sen/Finance-Web-App/assets/144620117/927aaacc-0181-4e87-9af0-350cab67a3bf)

### History
![history](https://github.com/Baniya-sen/Finance-Web-App/assets/144620117/c45aa72d-a3fd-46ea-9f8c-7a6ab4cc4ed2)
