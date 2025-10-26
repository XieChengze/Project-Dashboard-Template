# Explanation

Mongo refers to the folder for the MongoDB database
Postgres refers to the folder for the PostgreSQL database
Both contain dump files

However, when I was conducting tests by importing the database file, an error occurred. Postgres error: 'utf-8' codec can't decode byte 0xd6 at position 61: invalid continuation byte
I have no idea how this problem occurred. 
I used the content in the PPT. As follows,
show server_encoding;
show client_encoding; 
SELECT pg_encoding_to_char(encoding)
FROM pg_database WHERE datname = current_database();
The results are all in UTF8.
I used the methods in the PPT and tried various encoding formats, but still couldn't solve the problem.
I then tried to recreate a database with the encoding format of UTF8 in pgAdmin4, backed up the data, and imported it into the new database. I used the new database for testing and found that there were still UTF8 encoding parsing errors.
I tried many methods but still couldn't solve the problem.
Therefore, in order to prevent any potential issues, I have provided the DDL and DML statements for PostgreSQL. If there are problems with the dump file, DMD1.sql can be used as a substitute for db.dump for testing and evaluation.

"mongodb-sensor_data" is a JSON file of MongoDB.
