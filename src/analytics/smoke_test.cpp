#include <iostream>
#include <libpq-fe.h>
#include <cstdlib>
#include <string>

int main() {
	std::string connstr = 
		std::string("host=localhost dbname=griddb user=flask password=") +
	       	std::string(getenv("GRIDDB_PASSWORD"));

	PGconn* conn = PQconnectdb(connstr.c_str());

	if (PQstatus(conn) != CONNECTION_OK) {
		std::cerr << "Connection failed: " << PQerrorMessage(conn) << "\n";
		PQfinish(conn);
		return 1;
	}

	std::cout << "Connected. Server version: "
		  << PQserverVersion(conn) << "\n";

	PQfinish(conn);
	return 0;
}

