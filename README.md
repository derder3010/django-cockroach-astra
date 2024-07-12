# Django Project with Django REST Framework, SimpleJWT, Cockroachlabs, Astra Cassandra, Redis, and R2 Cloudflare

This project is a Django application that utilizes Django REST Framework and SimpleJWT for authentication. It uses Cockroachlabs as the main database, Astra Cassandra as the secondary database, Redis for caching, and R2 Cloudflare for storage.

## Prerequisites

Ensure you have the following before setting up the project:

- Python 3.9+
- [Cockroachlabs account](https://www.cockroachlabs.com/get-started-cockroachdb/)
- [Astra account](https://astra.datastax.com/register)
- [Redis (Upstash) account](https://upstash.com/)
- [Cloudflare account](https://dash.cloudflare.com/sign-up)

## Installation

### Pre-Run Commands

1. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

2. Collect static files:

   ```bash
   python manage.py collectstatic
   ```

3. Make migrations for the Django models:

   ```bash
   python manage.py makemigrations
   ```

4. Apply the migrations to the main database:

   ```bash
   python manage.py migrate
   ```

5. Sync the schema to the Astra Cassandra database:
   ```bash
   python manage.py sync_cassandra
   ```

### Running the Server

Start the Django development server:

```bash
python manage.py runserver
```

**Docker Deployment**
You can also deploy the project using Docker and docker-compose with Nginx. Follow the steps below:

Build and start the containers:

```bash
docker compose up --build
```

The application should now be running and accessible at http://localhost.

### Configuration

**Database Settings**
Ensure you have set up your database configurations in the settings.py and .env file for Cockroachlabs and Astra Cassandra.

**Redis Configuration**
Configure Redis in your settings.py and .env file to use Upstash.

**Cloudflare R2 Configuration**
Set up Cloudflare R2 for storage in your settings.py and .env file.
