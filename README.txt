COMMANDS:

- Generate django model for an app
python ./manage.py graph_models inventorySAS --no-inheritance --arrow-shape normal -o inventorySAS_model.png

- Reset db
python ./manage.py reset_db

- Assign Schema steps:
1. Create ROLE

CREATE ROLE CompanyRole
LOGIN
PASSWORD 'Postgr@s321!';

2. Create Schema with authorization of the role
CREATE SCHEMA IF NOT EXISTS CompanyName AUTHORIZATION CompanyRole;

---------------------------------