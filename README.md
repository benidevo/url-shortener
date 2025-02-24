# URL Shortener

A proof-of-concept project to explore microservices architecture and Kubernetes deployment using a URL shortening system.

## Project Overview

This project implements a distributed URL shortening system with geographic analytics capabilities using FastAPI and deployed on Kubernetes. It serves as a learning exercise for microservices orchestration with Kubernetes.

## Project Goals

- Implement a basic URL shortening service
- Create a separate analytics service
- Establish gRPC communication between services
- Deploy the system on Kubernetes
- Implement geographic tracking of URL usage

## Planned Architecture

- **Shortener Service**: Handles URL shortening operations
- **Analytics Service**: Processes click events and provides statistics
- **PostgreSQL Database**: Stores URL mappings and click data
- **Kubernetes**: Orchestrates the deployment of all components

## Tech Stack

- Python/FastAPI
- PostgreSQL
- gRPC
- Kubernetes

## Development Status

This project is currently in the initial setup phase.
