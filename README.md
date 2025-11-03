# Introduction
This project contains two applications: a FastAPI backend and a Streamlit frontend, designed to be run with Docker.

# Prerequisites
- Docker
- Docker Compose

# Getting Started

## Running with Docker

To build and run the applications, use the following command:

```bash
docker-compose up --build -d
```

This will start two services:

- `fastapi_app`: A FastAPI application running on port 8000.
- `streamlit_app`: A Streamlit application running on port 8501.

To view the logs for the services, you can use the following command:

```bash
docker-compose logs -f --tail 100
```

# Build and Test
TODO: Describe and show how to build your code and run the tests. 

# Contribute
TODO: Explain how other users and developers can contribute to make your code better. 

If you want to learn more about creating good readme files then refer the following [guidelines](https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops). You can also seek inspiration from the below readme files:
- [ASP.NET Core](https://github.com/aspnet/Home)
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [Chakra Core](https://github.com/Microsoft/ChakraCore)