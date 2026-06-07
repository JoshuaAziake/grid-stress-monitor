#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <libpq-fe.h>

// Data structures mirroring the three database tables

struct Bus {
    int    bus_id;
    int    bus_type;
    double pd_mw;
    double base_kv;
};

struct Branch {
    int    fbus;
    int    tbus;
    double x_pu;
    double rate_a_mw;  // -1 means NULL (unconstrained)
    double ratio;
    int    status;
};

struct Generator {
    int    bus_id;
    double pg_mw;
    double pmax_mw;
    double pmin_mw;
    int    status;
};

void parse_case118(const std::string& filepath,
                   std::vector<Bus>& buses,
                   std::vector<Branch>& branches,
                   std::vector<Generator>& generators);

PGconn* connect_to_db();

void insert_buses(PGconn* conn, const std::vector<Bus>& buses);
void insert_branches(PGconn* conn, const std::vector<Branch>& branches);
void insert_generators(PGconn* conn, const std::vector<Generator>& generators);

int main() {
    std::vector<Bus>       buses;
    std::vector<Branch>    branches;
    std::vector<Generator> generators;

    parse_case118("/home/joshua/grid-stress-monitor/data/network/case118.m", buses, branches, generators);

    PGconn* conn = connect_to_db();

    insert_buses(conn, buses);
    insert_branches(conn, branches);
    insert_generators(conn, generators);

    PQfinish(conn);
    return 0;
}

void parse_case118(const std::string& filepath, std::vector<Bus>& buses, std::vector<Branch>& branches, std::vector<Generator>& generators) {
	
	std::ifstream infile(filepath);
	if (!infile.is_open()) {
        std::cerr << "Error: could not open " << filepath << "\n";
        return;
    }

    enum Section { NONE, BUS, GEN, BRANCH };
    Section current = NONE;

    std::string line;
    while (std::getline(infile, line)) {
        if (line.find("mpc.bus = [")    != std::string::npos) { current = BUS;    continue; }
        if (line.find("mpc.gen = [")    != std::string::npos) { current = GEN;    continue; }
        if (line.find("mpc.branch = [") != std::string::npos) { current = BRANCH; continue; }
        if (line.find("];")             != std::string::npos) { current = NONE;   continue; }

        if (line.empty() || line[0] == '%') continue;
        if (current == NONE) continue;

        std::istringstream ss(line);

        if (current == BUS) {
            Bus b;
            double dummy;
            ss >> b.bus_id >> b.bus_type >> b.pd_mw
               >> dummy >> dummy >> dummy >> dummy   // Qd, Gs, Bs, area
               >> dummy >> dummy                     // Vm, Va
               >> b.base_kv;
            buses.push_back(b);
        }
        else if (current == GEN) {
            Generator g;
            double dummy;
            ss >> g.bus_id >> g.pg_mw
               >> dummy >> dummy >> dummy            // Qg, Qmax, Qmin
               >> dummy >> dummy                     // Vg, mBase
               >> g.status >> g.pmax_mw >> g.pmin_mw;
            generators.push_back(g);
        }
        else if (current == BRANCH) {
            Branch br;
            double dummy;
            double rate_a;
            ss >> br.fbus >> br.tbus
               >> dummy                              // r
               >> br.x_pu
               >> dummy                              // b
               >> rate_a
               >> dummy >> dummy                     // rateB, rateC
               >> br.ratio
               >> dummy                              // angle
               >> br.status;
            br.rate_a_mw = (rate_a == 0.0) ? -1.0 : rate_a;
            branches.push_back(br);
        }
    }

    infile.close();
    std::cout << "Parsed: " << buses.size()      << " buses, "
                            << branches.size()   << " branches, "
                            << generators.size() << " generators\n";
}

PGconn* connect_to_db() {
    const char* user     = getenv("GRIDDB_USER");
    const char* password = getenv("GRIDDB_PASSWORD");

    if (!user || !password) {
        std::cerr << "Error: GRIDDB_USER and GRIDDB_PASSWORD must be set\n";
        exit(1);
    }

    std::string connstr =
        std::string("host=localhost dbname=griddb user=") + user +
        std::string(" password=") + password;

    PGconn* conn = PQconnectdb(connstr.c_str());
    if (PQstatus(conn) != CONNECTION_OK) {
        std::cerr << "Connection failed: " << PQerrorMessage(conn) << "\n";
        PQfinish(conn);
        exit(1);
    }
    return conn;
}

void insert_buses(PGconn* conn, const std::vector<Bus>& buses) {
    for (const auto& b : buses) {
        std::string sql =
            "INSERT INTO network.buses (bus_id, bus_type, pd_mw, base_kv) "
            "VALUES (" +
            std::to_string(b.bus_id)   + ", " +
            std::to_string(b.bus_type) + ", " +
            std::to_string(b.pd_mw)    + ", " +
            std::to_string(b.base_kv)  + ");";

        PGresult* res = PQexec(conn, sql.c_str());
        if (PQresultStatus(res) != PGRES_COMMAND_OK) {
            std::cerr << "insert_buses failed: " << PQerrorMessage(conn) << "\n";
            PQclear(res);
            PQfinish(conn);
            exit(1);
        }
        PQclear(res);
    }
    std::cout << "Inserted " << buses.size() << " buses\n";
}

void insert_branches(PGconn* conn, const std::vector<Branch>& branches) {
    for (const auto& br : branches) {
        std::string rate_a_str = (br.rate_a_mw < 0) ? "NULL" : std::to_string(br.rate_a_mw);

        std::string sql =
            "INSERT INTO network.branches (fbus, tbus, x_pu, rate_a_mw, ratio, status) "
            "VALUES (" +
            std::to_string(br.fbus)  + ", " +
            std::to_string(br.tbus)  + ", " +
            std::to_string(br.x_pu)  + ", " +
            rate_a_str               + ", " +
            std::to_string(br.ratio) + ", " +
            std::to_string(br.status) + ");";

        PGresult* res = PQexec(conn, sql.c_str());
        if (PQresultStatus(res) != PGRES_COMMAND_OK) {
            std::cerr << "insert_branches failed: " << PQerrorMessage(conn) << "\n";
            PQclear(res);
            PQfinish(conn);
            exit(1);
        }
        PQclear(res);
    }
    std::cout << "Inserted " << branches.size() << " branches\n";
}

void insert_generators(PGconn* conn, const std::vector<Generator>& generators) {
    for (const auto& g : generators) {
        std::string sql =
            "INSERT INTO network.generators (bus_id, pg_mw, pmax_mw, pmin_mw, status) "
            "VALUES (" +
            std::to_string(g.bus_id)  + ", " +
            std::to_string(g.pg_mw)   + ", " +
            std::to_string(g.pmax_mw) + ", " +
            std::to_string(g.pmin_mw) + ", " +
            std::to_string(g.status)  + ");";

        PGresult* res = PQexec(conn, sql.c_str());
        if (PQresultStatus(res) != PGRES_COMMAND_OK) {
            std::cerr << "insert_generators failed: " << PQerrorMessage(conn) << "\n";
            PQclear(res);
            PQfinish(conn);
            exit(1);
        }
        PQclear(res);
    }
    std::cout << "Inserted " << generators.size() << " generators\n";
}
