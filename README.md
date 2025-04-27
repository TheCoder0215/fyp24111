# ProfileBlocks

ProfileBlocks is a blockchain-based platform for secure education credentials built with Django and Ethereum smart contracts. This project enables secure issuance, management, and verification of digital academic certificates using a modular backend and smart contracts deployed on the Ethereum Sepolia testnet.

---

## Table of Contents

- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create and Activate Virtual Environment](#2-create-and-activate-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Setup Environment Variables](#4-setup-environment-variables)
  - [5. Database Setup](#5-database-setup)
  - [6. Run the Development Server](#6-run-the-development-server)
- [Project Structure](#project-structure)
- [Additional Notes](#additional-notes)
- [Contact](#contact)

---

## Getting Started

Follow the instructions below to set up your local environment, run the server, and start developing or testing.

### 1. Clone the Repository

```bash
git clone https://github.com/TheCoder0215/fyp24111
cd profileblocks_v2
```

---

### 2. Create and Activate Virtual Environment

It is highly recommended to use a Python virtual environment to manage dependencies and keep your system clean.

Create a virtual environment named `venv`:

```bash
python3 -m venv venv
```

Activate the virtual environment:

- **macOS/Linux:**

  ```bash
  source venv/bin/activate
  ```

- **Windows (PowerShell):**

  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

- **Windows (Command Prompt):**

  ```cmd
  .\venv\Scripts\activate.bat
  ```

---

### 3. Install Dependencies

Upgrade `pip` first, then install the required packages from `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Setup Environment Variables

A `.env` file is included in the project root directory. This file contains essential environment variables such as blockchain RPC URLs and other configuration.
For validated personnels who wish to test using the projects Metamask Account, please contact u3578912@connect.hku.hk to obtain the `CONTRACT_OWNER_PRIVATE_KEY`.

- **Do not commit your `.env` file to public repos.**
- Review and update any placeholders or sensitive data in the `.env` as necessary.

---

### 5. Database Setup

The project includes a pre-populated SQLite database file `db.sqlite3` with testing data.

- If you want to apply migrations (for schema updates or if starting fresh), run:

  ```bash
  python manage.py migrate
  ```

- To create a superuser for Django admin access:

  ```bash
  python manage.py createsuperuser
  ```

---

### 6. Run the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

By default, the server will be accessible at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## Project Structure

```
profileblocks_v2/
├─ accounts/              # User authentication, key management, services, tests
├─ blockchain/            # Ethereum smart contract interaction services and tests
├─ certificates/          # Certificate issuance, management, templates, and templatetags
├─ institutions/          # Institution models and services
├─ profiles/              # Student profile management, services, templates
├─ static/                # Static files (CSS, JS)
├─ verification/          # Verification portal templates and tests
├─ manage.py              # Django management script
.env                      # Environment variables file (sensitive)
db.sqlite3                # SQLite database with testing data
requirements.txt          # Python dependencies
smart_contracts/          # Solidity contracts and Hardhat scripts/tests
```

---

## Additional Notes

- **Blockchain Integration:**  
  The backend interacts with Ethereum Sepolia testnet smart contracts using Web3.py. Ensure your `.env` contains correct RPC endpoints and private keys.

- **Security:**  
  Sensitive data is managed via `.env` and never committed to version control. The system uses role-based access control and cryptographic verification.

- **Frontend:**  
  Uses Django templates with Bootstrap 5 for responsive UI.

- **Testing Data:**  
  The included `db.sqlite3` contains sample data for quick testing and development.

---

## Contact

For questions, issues, or contributions, please contact u3578912@connect.hku.hk or refer to the project documentation.

---
