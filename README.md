# Explanation

When conducting tests by importing database files, errors will occur. Postgres error: 'utf-8' codec can't decode byte 0xd6 at position 61: invalid continuation byte.
I used the content in the ppt. 
show server_encoding;
show client_encoding;
SELECT pg_encoding_to_char(encoding)
FROM pg_database WHERE datname = current_database();
The results are all in utf8.
I used the method in the ppt and tried various encoding formats, but still couldn't solve the problem.
I then tried to recreate a database with the encoding format of utf8 in pgAdmin4, backed up the data, and imported it into the new database. I used the new database for testing and found that there were still utf8 encoding parsing errors.
I tried many methods but still couldn't solve the problem. Therefore, I provided my PostgreSQL DDL and DML statements(DMD1.sql) to replace the db.dump file for testing and evaluation.

"mongodb-sensor_data" is a JSON file of MongoDB.