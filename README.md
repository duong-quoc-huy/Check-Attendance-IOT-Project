# check-attendance-iot

<h1> Guide to use </h1>

In order to use this project, go to <a href="https://aiven.io/"> Aiven </a>. You can use other live-service database as long as it free. In this porject you can use MySQL or PostgreSQL as long as you migrate it to live-service database. Finally, get the connection configuration and put into ".env".

In this project, we have used the PostgreSQL from Aiven. Which also provide a file called ca.pem, which is used for enhacing the security of connection. We have created a folder certs, which is used for storing ca.pem, replace the current empty ca.pem with correct ca.pem.