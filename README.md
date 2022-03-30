# TechConf Registration Website

## Project Overview
The TechConf website allows attendees to register for an upcoming conference. Administrators can also view the list of attendees and notify all attendees via a personalized email message.

The application is currently working but the following pain points have triggered the need for migration to Azure:
 - The web application is not scalable to handle user load at peak
 - When the admin sends out notifications, it's currently taking a long time because it's looping through all attendees, resulting in some HTTP timeout exceptions
 - The current architecture is not cost-effective 

In this project, you are tasked to do the following:
- Migrate and deploy the pre-existing web app to an Azure App Service
- Migrate a PostgreSQL database backup to an Azure Postgres database instance
- Refactor the notification logic to an Azure Function via a service bus queue message

## Dependencies

You will need to install the following locally:
- [Postgres](https://www.postgresql.org/download/)
- [Visual Studio Code](https://code.visualstudio.com/download)
- [Azure Function tools V3](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Ccsharp%2Cbash#install-the-azure-functions-core-tools)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)
- [Azure Tools for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-node-azure-pack)

## Project Instructions

### Part 1: Create Azure Resources and Deploy Web App
1. Create a Resource group
2. Create an Azure Postgres Database single server
   - Add a new database `techconfdb`
   - Allow all IPs to connect to database server
   - Restore the database with the backup located in the data folder
3. Create a Service Bus resource with a `notificationqueue` that will be used to communicate between the web and the function
   - Open the web folder and update the following in the `config.py` file
      - `POSTGRES_URL`
      - `POSTGRES_USER`
      - `POSTGRES_PW`
      - `POSTGRES_DB`
      - `SERVICE_BUS_CONNECTION_STRING`
4. Create App Service plan
5. Create a storage account
6. Deploy the web app

### Part 2: Create and Publish Azure Function
1. Create an Azure Function in the `function` folder that is triggered by the service bus queue created in Part 1.

      **Note**: Skeleton code has been provided in the **README** file located in the `function` folder. You will need to copy/paste this code into the `__init.py__` file in the `function` folder.
      - The Azure Function should do the following:
         - Process the message which is the `notification_id`
         - Query the database using `psycopg2` library for the given notification to retrieve the subject and message
         - Query the database to retrieve a list of attendees (**email** and **first name**)
         - Loop through each attendee and send a personalized subject message
         - After the notification, update the notification status with the total number of attendees notified
2. Publish the Azure Function

### Part 3: Refactor `routes.py`
1. Refactor the post logic in `web/app/routes.py -> notification()` using servicebus `queue_client`:
   - The notification method on POST should save the notification object and queue the notification id for the function to pick it up
2. Re-deploy the web app to publish changes

## Monthly Cost Analysis
Complete a month cost analysis of each Azure resource to give an estimate total cost using the table below:

| Azure Resource                  | Service Tier | Cost                                                                        | Region    |
| ------------------------------- | ------------ | --------------------------------------------------------------------------- | --------- |
| *Azure Database for PostgreSQL* | B1ms         | $20.878/month                                                               | East Asia |
| *Azure Service Bus*             | Basic        | $0.05 per million operations                                                | East Asia |
| *Azure Web App*                 | B1 (Linux)   | $14.60/month                                                                | East Asia |
| *Azure Azure Function*          | Consumption  | Execution Time: $0.000016/GB-s (Free: 400,000 GB-s)                         | East Asia |
|                                 |              | Total Executions: $0.20 per million executions (Free: 1 million executions) | East Asia |
| Azure Cache for Redis           | C0           | $16.06/month                                                                | East Asia |

## Architecture Explanation

With sending background email functionality, it is quite small and independent and it is an event trigger. Our app can be running on demand, so Azure Function is suitable for this. Because with AF, we pay per call and do not pay anything when we do use. Execution Count and Execution Time are two concepts of the cost in AF.
Let assume that I start my function a 1 hour. There were 5000 executions and 700 million MB Function Execution Units consumed.
We have the 1-hour calculation:

   - Execution Count = 5000 * $0.20 / 1,000,000 = $0.0001
   - Execution Time = 700,000,000 / 1,024,000 * $16 / 1,000,000 = $0.0109375
   - 60 Min Total = Execution Count + Execution Time = $0.0110375

For the website, we can use Azure Web App or deploy on Azure Virtual Machine. VM is more expensive than Azure App Service to run, and also takes more time consuming of developers than App Sercice. For the current state of this app, I would refer Azure App Service.
If I start Azure Web App with 1 instance with B1 Tier for Linux: It will cost me $14.60/month. If I start Azure VM with 1 B1ms instance with for Ubuntu: It will cost me $21.316/month.
